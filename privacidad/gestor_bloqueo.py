# gestor_bloqueo.py
# Usa adblock (motor Rust de Brave) para bloquear anuncios y rastreadores.

import os
import hashlib
import json
import threading
import time

try:
    import adblock  # motor Rust de Brave
except ImportError:
    # La app sigue arrancando (solo sin bloqueo) y avisa en cargar_listas().
    adblock = None


from rutas import RUTA_DATOS, RUTA_LISTAS


CARPETA_LISTAS = RUTA_LISTAS
RUTA_WHITELIST = os.path.join(RUTA_DATOS, "whitelist.json")
# Motor ya compilado: cargarlo es ~3 veces más rápido que recompilar.
RUTA_CACHE = os.path.join(RUTA_DATOS, "cache_adblock.bin")
RUTA_CACHE_INFO = os.path.join(RUTA_DATOS, "cache_adblock.json")
# Súbelo si cambia el formato del caché o la forma de compilar las reglas.
VERSION_CACHE = 1


def _log(mensaje):
    """print tolerante: no rompe si stdout no existe (pythonw) ni admite
    el texto (consola cp1252 al redirigir la salida a un archivo)."""
    try:
        print(mensaje)
    except (UnicodeEncodeError, OSError, AttributeError):
        pass


class GestorBloqueo:

    def __init__(self):
        self.engine = None
        self.whitelist = self._cargar_whitelist()
        # Estado de la carga: 'listo' = ya se intentó (haya reglas o no).
        self.listo = False
        self.reglas = 0
        self.segundos = 0.0
        self.error = ""
        self._candado = threading.Lock()
        self.cargar_listas()

    # ---------- WHITELIST ----------

    def _cargar_whitelist(self):
        if not os.path.exists(RUTA_WHITELIST):
            return set()
        try:
            with open(RUTA_WHITELIST, "r", encoding="utf-8") as f:
                datos = json.load(f)
                if isinstance(datos, list):
                    return set(datos)
        except (json.JSONDecodeError, OSError):
            pass
        return set()

    def _guardar_whitelist(self):
        try:
            carpeta = os.path.dirname(RUTA_WHITELIST)
            if carpeta:
                os.makedirs(carpeta, exist_ok=True)
            with open(RUTA_WHITELIST, "w", encoding="utf-8") as f:
                json.dump(sorted(self.whitelist), f, indent=2)
        except OSError:
            pass

    # ---------- CARGA DE LISTAS ----------

    def cargar_listas(self):
        """Carga todas las reglas de la carpeta 'listas/' en el motor.

        Bloquea ~2,4 s: para el arranque se usa cargar_en_segundo_plano().
        """
        with self._candado:
            self._cargar_listas_sin_candado()

    def _cargar_listas_sin_candado(self):
        inicio = time.perf_counter()
        self.listo = False
        self.error = ""
        self.reglas = 0
        self.engine = None

        if adblock is None:
            self.error = ("Falta la dependencia 'adblock'. Instálala con: "
                          r"venv\Scripts\pip install -r requirements.txt")
            _log(self.error)
            self._terminar_carga(inicio)
            return

        if not os.path.isdir(CARPETA_LISTAS):
            self.error = "No existe la carpeta 'listas/'. Sin reglas cargadas."
            _log(self.error)
            self._terminar_carga(inicio)
            return

        huella, total_reglas = self._huella_listas()
        if total_reglas == 0:
            self.error = "No se encontraron reglas en 'listas/'."
            _log(self.error)
            self._terminar_carga(inicio)
            return

        # 1. Camino rápido: motor ya compilado con estas mismas listas.
        if self._cache_valido(huella):
            motor = self._motor_desde_cache()
            if motor is not None:
                self.engine = motor
                self.reglas = total_reglas
                self._terminar_carga(inicio)
                _log("Motor adblock cargado desde caché: ~%d reglas (%.2fs)"
                     % (total_reglas, self.segundos))
                return

        # 2. Camino normal: compilar las reglas (y guardar el resultado).
        filter_set = adblock.FilterSet()
        for nombre in sorted(os.listdir(CARPETA_LISTAS)):
            if not nombre.endswith(".txt"):
                continue
            ruta = os.path.join(CARPETA_LISTAS, nombre)
            try:
                with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
                    filter_set.add_filter_list(f.read())
            except OSError:
                pass

        # El segundo argumento (True) activa las optimizaciones.
        self.engine = adblock.Engine(filter_set, True)
        self.reglas = total_reglas
        self._guardar_cache(huella)
        self._terminar_carga(inicio)
        _log("Motor adblock compilado: ~%d reglas (%.1fs)"
             % (total_reglas, self.segundos))

    def _huella_listas(self):
        """Firma de las listas (contenido + versión) y total de líneas.

        Leer los 3,4 MB tarda ~10 ms: mucho menos que recompilar 135k reglas.
        """
        resumen = hashlib.sha256()
        resumen.update(("v%d" % VERSION_CACHE).encode())
        total = 0
        for nombre in sorted(os.listdir(CARPETA_LISTAS)):
            if not nombre.endswith(".txt"):
                continue
            ruta = os.path.join(CARPETA_LISTAS, nombre)
            try:
                with open(ruta, "rb") as f:
                    datos = f.read()
            except OSError:
                continue
            resumen.update(nombre.encode("utf-8"))
            resumen.update(datos)
            total += datos.count(b"\n")
        return resumen.hexdigest(), total

    def _cache_valido(self, huella):
        try:
            with open(RUTA_CACHE_INFO, "r", encoding="utf-8") as f:
                info = json.load(f)
        except (OSError, json.JSONDecodeError):
            return False
        return (isinstance(info, dict)
                and info.get("huella") == huella
                and os.path.isfile(RUTA_CACHE))

    def _verificar_cache_integridad(self):
        """Verifica la integridad del archivo de caché binario comparando su SHA-256.
        
        Returns:
            True si el hash coincide, False si el archivo no existe, está corrupto
            o no hay hash guardado.
        """
        try:
            with open(RUTA_CACHE_INFO, "r", encoding="utf-8") as f:
                info = json.load(f)
        except (OSError, json.JSONDecodeError):
            return False
        
        hash_guardado = info.get("cache_sha256")
        if not hash_guardado:
            return False
        
        try:
            import hashlib
            with open(RUTA_CACHE, "rb") as f:
                datos = f.read()
            hash_calculado = hashlib.sha256(datos).hexdigest()
            return hash_calculado == hash_guardado
        except (OSError, Exception):
            return False

    def _motor_desde_cache(self):
        """Motor deserializado, o None si el caché está roto o corrupto."""
        # Primero verificar integridad del archivo binario
        if not self._verificar_cache_integridad():
            return None
        
        try:
            motor = adblock.Engine(adblock.FilterSet(), True)
            motor.deserialize_from_file(RUTA_CACHE)
            return motor
        except Exception:
            # Caché corrupto o de otra versión: se recompila.
            return None

    def _guardar_cache(self, huella):
        """Guarda el motor compilado con su hash SHA-256 para verificación posterior."""
        try:
            os.makedirs(os.path.dirname(RUTA_CACHE), exist_ok=True)
            temporal = RUTA_CACHE + ".tmp"
            self.engine.serialize_to_file(temporal)
            
            # Calcular hash del archivo temporal antes de moverlo
            import hashlib
            with open(temporal, "rb") as f:
                datos = f.read()
            cache_sha256 = hashlib.sha256(datos).hexdigest()
            
            os.replace(temporal, RUTA_CACHE)
            with open(RUTA_CACHE_INFO, "w", encoding="utf-8") as f:
                json.dump({
                    "huella": huella, 
                    "version": VERSION_CACHE,
                    "cache_sha256": cache_sha256
                }, f)
        except Exception:
            pass

    def _terminar_carga(self, inicio):
        self.segundos = time.perf_counter() - inicio
        self.listo = True

    # ---------- COMPROBACIÓN ----------

    def debe_bloquear(self, url, source_url="", resource_type="other"):
        """Pregunta al motor de Brave si una URL debe bloquearse."""
        if self.engine is None or not url:
            return False

        # Whitelist del usuario.
        if self._en_whitelist(source_url):
            return False

        try:
            resultado = self.engine.check_network_urls(
                url=url,
                source_url=source_url,
                request_type=resource_type,
            )
            # resultado.matched = True si alguna regla coincide.
            # resultado.exception = None si NO es una excepción.
            # Si matched=True y exception=None -> BLOQUEAR.
            if resultado.matched and resultado.exception is None:
                return True
            return False
        except Exception:
            return False

    def _en_whitelist(self, source_url):
        if not source_url:
            return False
        try:
            from urllib.parse import urlparse
            host = urlparse(source_url).hostname or ""
            return self._coincide_whitelist(host)
        except Exception:
            return False

    def _coincide_whitelist(self, host):
        """True si el host es un dominio de la whitelist o un subdominio suyo
        (www.sitio.com cuenta como sitio.com)."""
        return any(host == d or host.endswith("." + d) for d in self.whitelist)

    # ---------- WHITELIST PÚBLICA ----------

    def añadir_a_whitelist(self, dominio):
        self.whitelist.add(dominio)
        self._guardar_whitelist()

    def quitar_de_whitelist(self, dominio):
        # Quitamos todas las entradas que hacían que este host estuviera
        # permitido (por ejemplo 'sitio.com' si estamos en 'www.sitio.com').
        self.whitelist = {
            d for d in self.whitelist
            if not (dominio == d or dominio.endswith("." + d))
        }
        self._guardar_whitelist()

    def esta_en_whitelist(self, dominio):
        return self._coincide_whitelist(dominio)
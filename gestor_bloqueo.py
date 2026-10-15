# gestor_bloqueo.py
# Usa adblock (motor Rust de Brave) para bloquear anuncios y rastreadores.

import os
import json
import adblock  # <-- ahora usamos 'adblock', no 'braveblock'


DIR = os.path.dirname(__file__)
CARPETA_LISTAS = os.path.join(DIR, "listas")
RUTA_WHITELIST = os.path.join(DIR, "whitelist.json")


class GestorBloqueo:

    def __init__(self):
        self.engine = None
        self.whitelist = self._cargar_whitelist()
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
            with open(RUTA_WHITELIST, "w", encoding="utf-8") as f:
                json.dump(sorted(self.whitelist), f, indent=2)
        except OSError:
            pass

    # ---------- CARGA DE LISTAS ----------

    def cargar_listas(self):
        """Carga todas las reglas de la carpeta 'listas/' en el motor."""
        if not os.path.isdir(CARPETA_LISTAS):
            print("⚠️ No existe la carpeta 'listas/'. Sin reglas cargadas.")
            self.engine = None
            return

        # 1. Crear el FilterSet (el "conjunto de filtros").
        filter_set = adblock.FilterSet()

        # 2. Leer todos los archivos .txt y añadirlos al FilterSet.
        total_reglas = 0
        for nombre in os.listdir(CARPETA_LISTAS):
            if not nombre.endswith(".txt"):
                continue
            ruta = os.path.join(CARPETA_LISTAS, nombre)
            try:
                with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
                    contenido = f.read()
                    filter_set.add_filter_list(contenido)
                    total_reglas += contenido.count("\n")
            except OSError:
                pass

        if total_reglas == 0:
            print("⚠️ No se encontraron reglas en 'listas/'.")
            self.engine = None
            return

        # 3. Crear el Engine a partir del FilterSet.
        #    El segundo argumento (True) activa las optimizaciones.
        self.engine = adblock.Engine(filter_set, True)
        print(f"✅ Motor adblock cargado con ~{total_reglas} líneas de reglas")

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
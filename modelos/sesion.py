# sesion.py
# Guarda las pestañas abiertas para restaurarlas en el siguiente arranque.
#
# Formato de datos/sesion.json:
#   {
#     "version": 1,
#     "activa": 0,
#     "pestanas": [
#       {"url": "https://ejemplo.com", "titulo": "Ejemplo", "fijada": false},
#       {"nueva": true, "fijada": false}
#     ]
#   }
#
# Reglas:
#   - Solo se guardan páginas http/https. La página de inicio (data:) y
#     about:blank se anotan como pestaña nueva.
#   - Tope de 30 pestañas para no volver el arranque eterno.
#   - Un archivo corrupto o de otra versión se ignora sin romper el arranque.

import json
import os

from rutas import RUTA_DATOS


RUTA = os.path.join(RUTA_DATOS, "sesion.json")
VERSION = 1
MAX_PESTANAS = 30
ESQUEMAS = ("http", "https")


def normalizar_entrada(entrada):
    """Devuelve una entrada limpia o None si no sirve."""
    if not isinstance(entrada, dict):
        return None

    fijada = entrada.get("fijada") is True

    if entrada.get("nueva") is True:
        return {"nueva": True, "fijada": fijada}

    url = entrada.get("url")
    if not isinstance(url, str):
        return None
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        return None

    titulo = entrada.get("titulo")
    if not isinstance(titulo, str):
        titulo = ""
    return {"url": url, "titulo": titulo, "fijada": fijada}


def ordenar_fijadas(entradas, activa=0):
    """Pone las fijadas primero, conservando el orden relativo.

    Devuelve (entradas_ordenadas, indice_activo_remapeado). Sirve para
    restaurar sesiones escritas a mano o por versiones anteriores, donde una
    fijada podía quedar en medio.
    """
    orden = sorted(
        range(len(entradas)),
        key=lambda i: (not entradas[i].get("fijada"), i),
    )
    ordenadas = [entradas[i] for i in orden]
    if 0 <= activa < len(orden):
        activa = orden.index(activa)
    else:
        activa = 0
    return ordenadas, activa


class Sesion:

    def __init__(self, ruta=RUTA):
        self.ruta = ruta
        self.datos = self._cargar()

    # ---------- lectura ----------

    def _vacia(self):
        return {"version": VERSION, "activa": 0, "pestanas": []}

    def _cargar(self):
        if self.ruta is None or not os.path.exists(self.ruta):
            return self._vacia()
        try:
            with open(self.ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[Sesion] archivo ilegible, empiezo vacío: {e}")
            return self._vacia()

        if not isinstance(datos, dict) or datos.get("version") != VERSION:
            return self._vacia()

        entradas = []
        for bruta in datos.get("pestanas") or []:
            limpia = normalizar_entrada(bruta)
            if limpia is not None:
                entradas.append(limpia)
            if len(entradas) >= MAX_PESTANAS:
                break

        activa = datos.get("activa")
        if not isinstance(activa, int) or isinstance(activa, bool):
            activa = 0
        if entradas:
            activa = max(0, min(activa, len(entradas) - 1))
        else:
            activa = 0

        return {"version": VERSION, "activa": activa, "pestanas": entradas}

    def pestanas(self):
        return list(self.datos["pestanas"])

    def activa(self):
        return self.datos.get("activa", 0)

    def vacia(self):
        return not self.datos["pestanas"]

    # ---------- escritura ----------

    def guardar(self, pestanas, activa=0):
        """Guarda la lista (ya limpia) y el índice activo."""
        limpias = []
        for bruta in pestanas or []:
            limpia = normalizar_entrada(bruta)
            if limpia is not None:
                limpias.append(limpia)
            if len(limpias) >= MAX_PESTANAS:
                break

        if limpias:
            activa = max(0, min(int(activa or 0), len(limpias) - 1))
        else:
            activa = 0

        self.datos = {
            "version": VERSION,
            "activa": activa,
            "pestanas": limpias,
        }
        self._escribir()

    def borrar(self):
        """Olvida la sesión (al desactivar la restauración)."""
        self.datos = self._vacia()
        self._escribir()

    def _escribir(self):
        if self.ruta is None:
            return
        try:
            carpeta = os.path.dirname(self.ruta)
            if carpeta:
                os.makedirs(carpeta, exist_ok=True)
            with open(self.ruta, "w", encoding="utf-8") as f:
                json.dump(self.datos, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"[Sesion] no se pudo guardar: {e}")

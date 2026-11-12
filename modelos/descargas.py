# descargas.py
# Modelo de descargas. Guarda el historial en descargas.json.

import os
from datetime import datetime

from .modelo_json import ModeloJSON
from rutas import RUTA_DATOS


RUTA = os.path.join(RUTA_DATOS, "descargas.json")
MAX_ENTRADAS = 200

# Estados finales posibles de una descarga.
ESTADOS_FINALES = ("completada", "cancelada", "interrumpida")


def puede_reintentar(entrada):
    """True si la descarga se puede volver a lanzar abriendo su URL.

    Qt no permite reanudar una descarga cuya petición ya murió, así que el
    "reintento" es volver a pedir el archivo desde el principio.
    """
    if not entrada:
        return False
    if entrada.get("estado") not in ("interrumpida", "cancelada"):
        return False
    url = (entrada.get("url") or "").strip()
    return url.startswith(("http://", "https://"))


class Descargas(ModeloJSON):

    def __init__(self, ruta=RUTA):
        super().__init__(ruta)

    def _normalizar(self, entradas):
        # Si el programa se cerró a mitad de una descarga, esa descarga
        # ya no existe: la marcamos como interrumpida.
        for e in entradas:
            if e.get("estado") == "en curso":
                e["estado"] = "interrumpida"
        return entradas

    def añadir(self, nombre, ruta, url, tamano, estado="completada"):
        entrada = {
            "nombre": nombre,
            "ruta": ruta,
            "url": url,
            "tamano": tamano,
            "estado": estado,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.entradas.insert(0, entrada)
        del self.entradas[MAX_ENTRADAS:]
        self.guardar()
        return entrada
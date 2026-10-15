# descargas.py
# Modelo de descargas. Guarda el historial en descargas.json.

import os
from datetime import datetime

from modelo_json import ModeloJSON


RUTA = os.path.join(os.path.dirname(__file__), "descargas.json")
MAX_ENTRADAS = 200


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
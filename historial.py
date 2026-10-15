# historial.py
# Gestor del historial: añade, consulta y borra las visitas.

import os
from datetime import datetime

from modelo_json import ModeloJSON


RUTA = os.path.join(os.path.dirname(__file__), "historial.json")
MAX_ENTRADAS = 500  # tope para no llenar el disco


class Historial(ModeloJSON):

    def __init__(self, ruta=RUTA):
        super().__init__(ruta)

    def añadir(self, titulo, url):
        """Añade una visita y guarda al momento. Ignora URLs internas
        y repeticiones seguidas de la misma URL."""
        if not url or url.startswith(("about:", "data:", "file:")):
            return
        if self.entradas and self.entradas[0].get("url") == url:
            return

        self.entradas.insert(0, {
            "titulo": titulo or url,
            "url": url,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        del self.entradas[MAX_ENTRADAS:]
        self.guardar()

    def recientes(self, n=20):
        return self.entradas[:n]

    def buscar(self, texto):
        """Entradas que contienen el texto en el título o en la URL."""
        texto = texto.lower().strip()
        if not texto:
            return list(self.entradas)
        return [
            e for e in self.entradas
            if texto in e.get("titulo", "").lower()
            or texto in e.get("url", "").lower()
        ]

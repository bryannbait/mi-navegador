# favoritos.py
# Modelo de favoritos. No sabe nada de la interfaz.

import os
from datetime import datetime

from modelo_json import ModeloJSON


RUTA = os.path.join(os.path.dirname(__file__), "favoritos.json")


class Favoritos(ModeloJSON):

    def __init__(self, ruta=RUTA):
        super().__init__(ruta)

    def existe(self, url):
        return any(e.get("url") == url for e in self.entradas)

    def añadir(self, titulo, url):
        if not url or url.startswith(("about:", "data:", "file:")):
            return
        if self.existe(url):
            return
        self.entradas.append({
            "titulo": titulo or url,
            "url": url,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        self.guardar()

    def eliminar(self, url):
        antes = len(self.entradas)
        self.entradas = [e for e in self.entradas if e.get("url") != url]
        if len(self.entradas) != antes:
            self.guardar()

    def renombrar(self, url, nuevo_titulo):
        for e in self.entradas:
            if e.get("url") == url:
                e["titulo"] = nuevo_titulo
                self.guardar()
                return

    def buscar(self, texto):
        texto = texto.lower().strip()
        if not texto:
            return list(self.entradas)
        return [
            e for e in self.entradas
            if texto in e.get("titulo", "").lower()
            or texto in e.get("url", "").lower()
        ]
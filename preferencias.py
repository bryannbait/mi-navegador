# preferencias.py
# Guarda y carga preferencias del navegador en preferencias.json.

import json
import os


RUTA = os.path.join(os.path.dirname(__file__), "preferencias.json")


class Preferencias:

    def __init__(self, ruta=RUTA):
        self.ruta = ruta
        self.datos = self._cargar()

    def _cargar(self):
        por_defecto = {
            "motor_busqueda": "duckduckgo",
            "mostrar_barra_favoritos": True,
        }
        if not os.path.exists(self.ruta):
            return por_defecto
        try:
            with open(self.ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)
                if isinstance(datos, dict):
                    # Rellenamos claves nuevas si faltan.
                    for k, v in por_defecto.items():
                        datos.setdefault(k, v)
                    return datos
        except (json.JSONDecodeError, OSError):
            pass
        return por_defecto

    def guardar(self):
        try:
            with open(self.ruta, "w", encoding="utf-8") as f:
                json.dump(self.datos, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def get(self, clave, por_defecto=None):
        return self.datos.get(clave, por_defecto)

    def set(self, clave, valor):
        self.datos[clave] = valor
        self.guardar()
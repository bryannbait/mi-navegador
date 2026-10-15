# modelo_json.py
# Base para los modelos que guardan una lista de diccionarios en un JSON
# (historial, favoritos, descargas). No sabe nada de la interfaz.

import json
import os


class ModeloJSON:
    """
    ruta=None -> modelo solo en memoria (no toca el disco).
    Las subclases pueden sobrescribir _normalizar() para ajustar
    las entradas justo después de cargarlas.
    """

    def __init__(self, ruta):
        self.ruta = ruta
        self.entradas = self._cargar()

    def _cargar(self):
        if self.ruta is None or not os.path.exists(self.ruta):
            return []
        try:
            with open(self.ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[{type(self).__name__}] archivo ilegible, empiezo vacío: {e}")
            return []
        if not isinstance(datos, list):
            return []
        return self._normalizar([e for e in datos if isinstance(e, dict)])

    def _normalizar(self, entradas):
        """Hook: ajusta las entradas al cargar. Por defecto no cambia nada."""
        return entradas

    def guardar(self):
        if self.ruta is None:
            return
        try:
            with open(self.ruta, "w", encoding="utf-8") as f:
                json.dump(self.entradas, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"[{type(self).__name__}] no se pudo guardar: {e}")

    def todos(self):
        return list(self.entradas)

    def borrar_todo(self):
        self.entradas = []
        self.guardar()
# zoom.py
# Guarda el factor de zoom por sitio (host), para recordarlo entre sesiones.
#
# Formato de datos/zoom.json:
#   {"ejemplo.com": 1.25, "wikipedia.org": 1.5}
#
# Reglas:
#   - Rango 50 %..200 % en pasos de 10 % (factores 0.5..2.0 con un decimal).
#   - La clave es el host SIN puerto: localhost:8000 y localhost:8765
#     comparten el mismo zoom.
#   - Incógnito: ruta=None, solo en memoria, nunca escribe.
#   - Un archivo corrupto se ignora sin romper el arranque.

import json
import os

from rutas import RUTA_DATOS


RUTA = os.path.join(RUTA_DATOS, "zoom.json")

MIN_FACTOR = 0.5     # 50 %
MAX_FACTOR = 2.0     # 200 %
PASO = 0.1           # 10 %
FACTOR_DEFECTO = 1.0


def _redondear_paso(factor):
    """Ajusta al múltiplo de 10 % más cercano, con un decimal."""
    return round(round(factor / PASO) * PASO, 1)


def _limitar(factor):
    return max(MIN_FACTOR, min(MAX_FACTOR, factor))


def pasar_a_puntos(factor):
    """Factor (1.25) -> puntos Qt (125)."""
    return round(factor * 100)


def pasar_a_factor(puntos):
    """Puntos Qt (125) -> factor (1.25). Solo limita, no fuerza el paso."""
    return _limitar(round(puntos / 100, 2))


def host_de(url):
    """Host sin puerto, para que distintos puertos compartan zoom."""
    if url is None:
        return ""
    return (url.host() or "").strip().lower()


class Zoom:

    def __init__(self, ruta=RUTA):
        self.ruta = ruta
        self.datos = self._cargar()

    # ---------- lectura ----------

    def _cargar(self):
        if self.ruta is None or not os.path.exists(self.ruta):
            return {}
        try:
            with open(self.ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)
        except (json.JSONDecodeError, OSError):
            print("[Zoom] archivo ilegible, empiezo vacío")
            return {}
        if not isinstance(datos, dict):
            return {}
        resultado = {}
        for clave, valor in datos.items():
            if not isinstance(clave, str) or not clave:
                continue
            try:
                factor = float(valor)
            except (TypeError, ValueError):
                continue
            factor = _limitar(_redondear_paso(factor))
            if factor > 0:
                resultado[clave] = factor
        return resultado

    def obtener(self, host):
        """Factor guardado para el host, o 1.0 si no hay ninguno."""
        if not host:
            return FACTOR_DEFECTO
        return self.datos.get(host, FACTOR_DEFECTO)

    # ---------- escritura ----------

    def establecer(self, host, factor, guardar=True):
        """Guarda el factor para el host (clamp + paso de 10 %)."""
        if not host:
            return
        factor = _limitar(_redondear_paso(factor))
        self.datos[host] = factor
        if guardar and self.ruta is not None:
            self._escribir()

    def restablecer(self, host, guardar=True):
        """Borra el zoom guardado del host (vuelve a 1.0)."""
        if host in self.datos:
            del self.datos[host]
            if guardar and self.ruta is not None:
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
        except OSError:
            print("[Zoom] no se pudo guardar")

    # ---------- helpers ----------

    def ajuste(self, factor, mas=True):
        """Sube o baja un paso desde el factor, dentro de los límites."""
        if mas:
            return _limitar(_redondear_paso(factor + PASO))
        return _limitar(_redondear_paso(factor - PASO))

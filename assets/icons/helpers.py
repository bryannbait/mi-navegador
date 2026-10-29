# assets/icons/helpers.py
# Carga iconos SVG desde la carpeta assets/icons/ y los tiñe del color pedido.

import os
from functools import lru_cache

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QGuiApplication, QIcon, QPainter, QPixmap, QColor

try:
    from PyQt6.QtSvg import QSvgRenderer
except ImportError:          # por si la instalación no trae QtSvg
    QSvgRenderer = None


DIR_ICONOS = os.path.dirname(os.path.abspath(__file__))


def ruta_icono(nombre):
    """Ruta completa del SVG (con barras normales, para usarla en estilos QSS)."""
    return os.path.join(DIR_ICONOS, f"{nombre}.svg").replace("\\", "/")


@lru_cache(maxsize=None)
def icono(nombre, color="#e8e8f2", tamano=18):
    """
    Devuelve un QIcon del SVG `nombre` (sin extensión, ej: "arrow-left")
    teñido de `color`. Se dibuja a la resolución real de la pantalla para que
    se vea nítido también en pantallas con escala (125 %, 150 %...).
    El resultado se guarda en caché: pedir el mismo icono otra vez es gratis.
    """
    ruta = os.path.join(DIR_ICONOS, f"{nombre}.svg")
    if not os.path.exists(ruta):
        return QIcon()

    pantalla = QGuiApplication.primaryScreen()
    dpr = pantalla.devicePixelRatio() if pantalla else 1.0
    lado = int(tamano * dpr)

    pixmap = QPixmap(lado, lado)
    pixmap.fill(Qt.GlobalColor.transparent)
    pixmap.setDevicePixelRatio(dpr)

    zona = QRectF(0, 0, tamano, tamano)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    if QSvgRenderer is not None:
        # Dibujo vectorial a la resolución final (nítido).
        render = QSvgRenderer(ruta)
        if not render.isValid():
            painter.end()
            return QIcon()
        render.render(painter, zona)
    else:
        # Plan B: cargar como imagen y escalar.
        base = QPixmap(ruta)
        if base.isNull():
            painter.end()
            return QIcon()
        painter.drawPixmap(zona.toRect(), base)

    # Teñir: SourceIn deja solo el color donde el SVG ha dibujado algo.
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(zona, QColor(color))
    painter.end()

    return QIcon(pixmap)

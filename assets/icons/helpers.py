# assets/icons/helpers.py
# Carga iconos SVG desde la carpeta assets/icons/.

import os
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt, QSize


DIR_ICONOS = os.path.dirname(os.path.abspath(__file__))


def icono(nombre, color="#cdd6f4", tamano=18):
    """
    Carga un icono SVG y lo tiñe del color indicado.
    `nombre` es el nombre del archivo sin extensión (ej: "arrow-left").
    """
    ruta = os.path.join(DIR_ICONOS, f"{nombre}.svg")
    if not os.path.exists(ruta):
        return QIcon()

    # Cargamos el SVG como pixmap.
    pixmap = QPixmap(ruta)
    if pixmap.isNull():
        return QIcon()

    # Lo teñimos (los SVG de Lucide son monocromos).
    pixmap = pixmap.scaled(
        tamano, tamano,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )

    pintado = QPixmap(pixmap.size())
    pintado.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pintado)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pintado.rect(), QColor(color))
    painter.end()

    return QIcon(pintado)
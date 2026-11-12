# rutas.py
# Rutas absolutas del proyecto, centralizadas.
# Así los modelos y el bloqueador no dependen de en qué carpeta vivan.

import os

RAIZ = os.path.dirname(os.path.abspath(__file__))

RUTA_DATOS = os.path.join(RAIZ, "datos")
RUTA_LISTAS = os.path.join(RAIZ, "listas")
RUTA_ASSETS = os.path.join(RAIZ, "assets")

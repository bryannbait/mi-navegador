# main.py
# Punto de entrada del navegador.

import sys

from PyQt6.QtWidgets import QApplication

from gestor_bloqueo import GestorBloqueo
from historial import Historial
from favoritos import Favoritos
from descargas import Descargas
from preferencias import Preferencias
from navegador import MiNavegador, configurar_perfil, hoja_de_estilos
import config


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(config.NOMBRE)
    app.setStyleSheet(hoja_de_estilos())

    # Modelos reales: solo los usa la ventana normal.
    prefs = Preferencias()
    historial = Historial()
    favoritos = Favoritos()
    descargas = Descargas()
    gestor = GestorBloqueo()

    # Perfil normal con su interceptor de bloqueo.
    configurar_perfil(gestor)

    ventana = MiNavegador(gestor, prefs, historial, favoritos, descargas)
    ventana.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

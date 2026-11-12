# main.py
# Punto de entrada del navegador.

import os
import subprocess
import sys

try:
    from PyQt6.QtWidgets import QApplication
except ImportError:
    # Este proyecto usa su propio entorno virtual (venv). Si alguien lo
    # arranca con el Python del sistema ("python main.py"), lo relanzamos
    # con el intérprete correcto en vez de fallar con ModuleNotFoundError.
    RAIZ = os.path.dirname(os.path.abspath(__file__))
    VENV = os.path.join(RAIZ, "venv", "Scripts", "python.exe")
    if (os.path.isfile(VENV)
            and os.path.normcase(os.path.abspath(sys.executable))
            != os.path.normcase(os.path.abspath(VENV))):
        # subprocess entrecomilla bien la ruta aunque tenga espacios
        # ("Projecto Navegador"); os.execv en Windows no lo hace.
        sys.exit(subprocess.call(
            [VENV, os.path.abspath(__file__), *sys.argv[1:]]
        ))

    print("No encuentro PyQt6 en este Python.")
    print("Usa el lanzador del proyecto: iniciar.bat")
    print(r"O ejecuta: venv\Scripts\python.exe main.py")
    sys.exit(1)

from privacidad.gestor_bloqueo import GestorBloqueo
from modelos.historial import Historial
from modelos.favoritos import Favoritos
from modelos.descargas import Descargas
from modelos.preferencias import Preferencias
from navegador import MiNavegador, configurar_perfil
from estilos import aplicar_tema
import config


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(config.NOMBRE)
    aplicar_tema(app)

    # Modelos reales: solo los usa la ventana normal.
    prefs = Preferencias()
    historial = Historial()
    favoritos = Favoritos()
    descargas = Descargas()
    gestor = GestorBloqueo()

    # Perfil normal con su interceptor de bloqueo.
    configurar_perfil(gestor, prefs.get("anti_fingerprint", config.ANTI_FINGERPRINT))

    ventana = MiNavegador(gestor, prefs, historial, favoritos, descargas)
    ventana.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

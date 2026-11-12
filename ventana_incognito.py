# ventana_incognito.py
# Ventana incógnita. Usa perfil off-the-record y modelos SOLO en memoria:
# no lee ni escribe tu historial, favoritos ni descargas reales.

from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtWidgets import QApplication

from privacidad import anti_fingerprint
import config
from privacidad.bloqueador import Bloqueador
from navegador import MiNavegador
from puente_vim import crear_script_vim
from historial import Historial
from favoritos import Favoritos
from descargas import Descargas


class VentanaIncognito(MiNavegador):

    def __init__(self, gestor, prefs):
        # Perfil aislado (todo vive en RAM).
        perfil_inc = QWebEngineProfile()
        anti_fingerprint.preparar_perfil(
            perfil_inc, prefs.get("anti_fingerprint", config.ANTI_FINGERPRINT)
        )

        # Detector Vim para este perfil.
        perfil_inc.scripts().insert(crear_script_vim())

        # Interceptor propio (su propio contador del escudo).
        interceptor_inc = Bloqueador(
            gestor,
            privacidad=anti_fingerprint.esta_activo(perfil_inc),
            ua=perfil_inc.httpUserAgent(),
        )
        perfil_inc.setUrlRequestInterceptor(interceptor_inc)

        # Modelos vacíos y sin ruta: nada de esto toca el disco, y esta
        # ventana no puede ver ni borrar tus datos reales.
        super().__init__(
            gestor, prefs,
            Historial(ruta=None), Favoritos(ruta=None), Descargas(ruta=None),
            perfil_web=perfil_inc,
            interceptor_propio=interceptor_inc,
            es_incognito=True,
        )

        # El perfil debe morir DESPUÉS de las páginas que lo usan: al ser
        # hijo de la ventana, Qt lo destruye el último.
        perfil_inc.setParent(self)

        self.setWindowTitle(f"{config.NOMBRE} — Modo incógnito")
        self.resize(1200, 800)

    def closeEvent(self, event):
        # Soltamos el interceptor antes de que Python lo borre.
        self.perfil_web.setUrlRequestInterceptor(None)
        app = QApplication.instance()
        if hasattr(app, "_ventanas_incognito") and self in app._ventanas_incognito:
            app._ventanas_incognito.remove(self)
        super().closeEvent(event)

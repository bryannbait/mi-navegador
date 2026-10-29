# ventana_incognito.py
# Ventana incógnita. Usa perfil off-the-record, sin acceso a modelos reales.

from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtWidgets import QApplication

from bloqueador import Bloqueador
from navegador import MiNavegador
from puente_vim import crear_script_vim


class VentanaIncognito(MiNavegador):

    def __init__(self, gestor, prefs, historial, favoritos, descargas):
        # Perfil aislado.
        perfil_inc = QWebEngineProfile()
        perfil_inc.setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

        # Detector Vim para este perfil.
        perfil_inc.scripts().insert(crear_script_vim())

        # Interceptor propio.
        interceptor_inc = Bloqueador(gestor)
        perfil_inc.setUrlRequestInterceptor(interceptor_inc)

        # Conectar descargas del perfil incógnito.
        from navegador import _on_download_requested
        perfil_inc.downloadRequested.connect(_on_download_requested)

        # Llamar al padre con los modelos compartidos (aunque incógnito no
        # los usa para guardar, los necesita para construir la UI).
        super().__init__(
            gestor, prefs, historial, favoritos, descargas,
            perfil_web=perfil_inc,
            interceptor_propio=interceptor_inc,
            es_incognito=True,
        )

        self.setWindowTitle("🕵️  Mi Navegador — Modo Incógnito")
        self.resize(1200, 800)

        # Avisar al interceptor de esta ventana (para el escudo por pestaña).
        interceptor_inc.navegador = self

        # Registrar en la lista global.
        app = QApplication.instance()
        if not hasattr(app, "_ventanas_navegador"):
            app._ventanas_navegador = []
        app._ventanas_navegador.append(self)

    def closeEvent(self, event):
        app = QApplication.instance()
        if hasattr(app, "_ventanas_incognito") and self in app._ventanas_incognito:
            app._ventanas_incognito.remove(self)
        if hasattr(app, "_ventanas_navegador") and self in app._ventanas_navegador:
            app._ventanas_navegador.remove(self)
        super().closeEvent(event)
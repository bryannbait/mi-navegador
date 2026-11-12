# bloqueador.py
# Interceptor de red. Usa GestorBloqueo para decidir y cuenta bloqueos.

from PyQt6.QtWebEngineCore import (
    QWebEngineUrlRequestInterceptor,
    QWebEngineUrlRequestInfo,
)

import config
from . import anti_fingerprint


# Mapeo de tipos de PyQt6 -> strings que espera adblock (estilo Brave/AdBlock).
# Referencia: QWebEngineUrlRequestInfo.ResourceType
_MAPA_TIPOS = {
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeMainFrame:          "document",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeSubFrame:           "subdocument",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeStylesheet:         "stylesheet",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeScript:             "script",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeImage:              "image",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeFontResource:       "font",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeSubResource:        "other",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeObject:             "object",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeMedia:              "media",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeWorker:             "other",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeSharedWorker:       "other",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypePrefetch:           "other",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeFavicon:            "image",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeXhr:                "xhr",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypePing:               "ping",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeServiceWorker:      "other",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeCspReport:          "csp_report",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypePluginResource:     "object",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeNavigationPreloadMainFrame: "document",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeNavigationPreloadSubFrame:  "subdocument",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeUnknown:            "other",
}


def _tipo_legible(info):
    """Convierte el ResourceType de PyQt6 al string que espera adblock."""
    try:
        tipo_qt = info.resourceType()
        return _MAPA_TIPOS.get(tipo_qt, "other")
    except Exception:
        return "other"


class Bloqueador(QWebEngineUrlRequestInterceptor):
    """
    Interceptor que consulta al GestorBloqueo y mantiene un contador
    de bloqueos por pestaña.
    """

    def __init__(self, gestor, privacidad=True, ua=None, parent=None):
        super().__init__(parent)
        self.gestor = gestor
        self.contadores = {}
        self.navegador = None
        self.privacidad = privacidad
        # Sec-CH-UA coherente con el UA y con navigator.userAgentData.
        self.sec_ch_ua = anti_fingerprint.cabecera_client_hints(ua) if ua else None

    def set_privacidad(self, activo):
        """El interruptor del escudo cambia también las cabeceras."""
        self.privacidad = activo

    def registrar_pestana(self, pestana_id):
        self.contadores[pestana_id] = {"total": 0, "por_tipo": {}}

    def olvidar_pestana(self, pestana_id):
        self.contadores.pop(pestana_id, None)

    def contador_actual(self, pestana_id):
        return self.contadores.get(pestana_id, {"total": 0, "por_tipo": {}})

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        tipo = _tipo_legible(info)

        # Nivel 10: cabeceras de privacidad.
        if self.privacidad:
            try:
                # Global Privacy Control: "no vendas ni compartas mis datos".
                if config.FP_ENVIAR_GPC:
                    info.setHttpHeader(b"Sec-GPC", b"1")
                # Solo tiene sentido en HTTPS (los Client Hints son secure-only).
                if self.sec_ch_ua and info.requestUrl().scheme() == "https":
                    info.setHttpHeader(b"sec-ch-ua", self.sec_ch_ua)
            except Exception:
                pass

        source_url = ""
        try:
            source_url = info.firstPartyUrl().toString()
        except Exception:
            pass

        if self.gestor.debe_bloquear(url, source_url, tipo):
            info.block(True)

            if self.navegador is not None:
                # La pestaña que hizo la petición (no tiene por qué ser la
                # que está a la vista en este momento).
                pid = self.navegador.id_pestana_de(info.firstPartyUrl())
                if pid in self.contadores:
                    c = self.contadores[pid]
                    c["total"] += 1
                    c["por_tipo"][tipo] = c["por_tipo"].get(tipo, 0) + 1
                    # Refresca el escudo, pero sin repintar en cada petición.
                    self.navegador.actualizar_escudo_pronto()
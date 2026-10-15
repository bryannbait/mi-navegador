# puente_vim.py
# Puente JS <-> Python para saber si el foco está en un input de la web.
# Usa console.log como canal (rápido, sin setup de QWebChannel).

from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineScript


PREFIJO = "VIM_INPUT_"


JS_DETECTOR = r"""
(function() {
    if (window.__vimInstalado) return;
    window.__vimInstalado = true;

    function esInput(el) {
        if (!el) return false;
        var tag = el.tagName ? el.tagName.toLowerCase() : '';
        if (tag === 'input' || tag === 'textarea' || tag === 'select') return true;
        if (el.isContentEditable) return true;
        return false;
    }

    function notificar(activo) {
        try { console.log("VIM_INPUT_" + (activo ? "1" : "0")); } catch (e) {}
    }

    document.addEventListener('focusin', function(e) {
        if (esInput(e.target)) notificar(true);
    }, true);

    document.addEventListener('focusout', function(e) {
        if (esInput(e.target)) notificar(false);
    }, true);

    // Estado inicial: SOLO lo manda el documento principal. Si lo mandaran
    // también los iframes (anuncios, widgets...), al cargar uno mientras
    // escribes se apagaría el flag y las teclas dispararían atajos Vim.
    if (window.self === window.top) {
        notificar(esInput(document.activeElement));
    }
})();
"""


class PaginaVim(QWebEnginePage):
    """QWebEnginePage que escucha los mensajes VIM_INPUT_ y mantiene el estado."""

    def __init__(self, perfil=None, parent=None):
        if perfil is not None:
            super().__init__(perfil, parent)
        else:
            super().__init__(parent)
        self.input_activo = False

    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        # Filtro rápido: solo procesamos nuestros mensajes.
        if message.startswith(PREFIJO):
            self.input_activo = message.endswith("1")
            return
        # El resto de mensajes los ignoramos.


def crear_script_vim():
    """Devuelve un QWebEngineScript listo para registrar en un perfil."""
    script = QWebEngineScript()
    script.setName("vim_detector")
    script.setSourceCode(JS_DETECTOR)
    script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
    script.setWorldId(QWebEngineScript.ScriptWorldId.ApplicationWorld)
    script.setRunsOnSubFrames(True)
    return script
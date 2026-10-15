# atajos_vim.py
# Atajos estilo Vim. El modo INSERT/NORMAL se decide automáticamente
# según si el foco está en un input de la web (vía puente_vim.py).

import json

from PyQt6.QtCore import QObject, QEvent, Qt, QTimer
from PyQt6.QtWidgets import QApplication, QLabel


class IndicadorModo(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        # Que el cartel no robe el foco a la ventana del navegador.
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #181825;
                color: #89b4fa;
                border: 1px solid #89b4fa;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def mostrar(self, texto, ms=1200):
        self.setText(texto)
        self.adjustSize()
        pantalla = QApplication.primaryScreen().availableGeometry()
        x = pantalla.right() - self.width() - 20
        y = pantalla.bottom() - self.height() - 20
        self.move(x, y)
        self.show()
        self.raise_()
        self._timer.start(ms)


class VimKeys(QObject):

    def __init__(self, ventana):
        super().__init__()
        self.ventana = ventana
        self.indicador = IndicadorModo()
        self.buffer = ""
        self.en_comando = False

        QApplication.instance().installEventFilter(self)

    def desinstalar(self):
        """Quita el filtro de la aplicación. Llamar al cerrar la ventana."""
        QApplication.instance().removeEventFilter(self)
        self.indicador.hide()

    # ---------- FILTRO ----------

    def eventFilter(self, obj, event):
        if event.type() != QEvent.Type.KeyPress:
            return False

        # El filtro es de toda la aplicación y cada ventana tiene el suyo.
        # Solo actuamos si la ventana activa es la NUESTRA; si no, la tecla
        # de la ventana normal la procesaría el incógnito (y al revés), o
        # un panel como Descargas haría scroll en la página.
        activa = QApplication.activeWindow()
        if activa is not self.ventana and activa is not self.indicador:
            return False

        # Si el foco está en un QLineEdit de la UI (barra de direcciones,
        # diálogos, etc.), las teclas van al widget. No interceptamos.
        foco = QApplication.focusWidget()
        if self._foco_es_input(foco):
            return False

        # Si hay un diálogo modal, no interceptamos.
        if QApplication.activeModalWidget() is not None:
            return False

        tecla = event.key()
        texto = event.text()
        modificadores = event.modifiers()

        # Ctrl/Alt: dejar pasar atajos globales.
        if modificadores & (
            Qt.KeyboardModifier.ControlModifier
            | Qt.KeyboardModifier.AltModifier
        ):
            return False

        # ---------- ¿Foco en input de la web? ----------
        view = self.ventana.pestana_actual()
        if view is not None:
            page = view.page()
            input_activo = getattr(page, "input_activo", False)
            if input_activo:
                # Esc: difuminar el input y volver a comandos.
                if tecla == Qt.Key.Key_Escape:
                    view.page().runJavaScript(
                        "if (document.activeElement) document.activeElement.blur();"
                    )
                    return True
                # Todo lo demás va a la web.
                return False

        # ---------- Modo comando (: y /) ----------
        if self.en_comando:
            return self._manejar_comando(tecla, texto)

        if texto == ":":
            self.en_comando = True
            self.buffer = ":"
            self.indicador.mostrar(":", 5000)
            return True
        if texto == "/":
            self.en_comando = True
            self.buffer = "/"
            self.indicador.mostrar("/", 5000)
            return True

        return self._manejar_normal(tecla, texto)

    # ---------- MODO NORMAL ----------

    def _manejar_normal(self, tecla, texto):
        v = self.ventana
        view = v.pestana_actual()
        if view is None:
            return False

        # Shift, Ctrl... solos no traen texto: no deben cancelar la 'g'.
        if not texto:
            return False

        # 'gg': primero miramos si ya había una 'g' pendiente.
        if texto == "g":
            if self.buffer == "g":
                self.buffer = ""
                view.page().runJavaScript("window.scrollTo(0, 0);")
            else:
                self.buffer = "g"
            return True

        # Cualquier otra tecla cancela la 'g' pendiente.
        self.buffer = ""

        def scroll(dy):
            view.page().runJavaScript(f"window.scrollBy(0, {dy});")

        if texto == "j":
            scroll(80); return True
        if texto == "k":
            scroll(-80); return True

        if texto == "d":
            view.page().runJavaScript(
                "window.scrollBy(0, window.innerHeight / 2);"
            )
            return True
        if texto == "u":
            view.page().runJavaScript(
                "window.scrollBy(0, -window.innerHeight / 2);"
            )
            return True

        if texto == "G":
            view.page().runJavaScript(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            return True

        if texto == "f":
            v.atras_actual(); return True
        if texto == "F":
            v.adelante_actual(); return True

        if texto == "r":
            v.recargar_o_detener(); return True

        if texto == "t":
            v.nueva_pestana(); return True
        if texto == "x":
            v.cerrar_pestana_actual(); return True

        if texto == "J":
            v.siguiente_pestana(); return True
        if texto == "K":
            v.pestana_anterior(); return True

        if texto == "H":
            v.inicio_actual(); return True

        if texto == "?":
            self._mostrar_ayuda()
            return True

        # 'i' fuerza INSERT manualmente: hace foco en el primer input.
        if texto == "i":
            view.page().runJavaScript("""
                (function() {
                    var el = document.querySelector(
                        'input:not([type=hidden]), textarea, [contenteditable=true]'
                    );
                    if (el) el.focus();
                })();
            """)
            self.indicador.mostrar("-- INSERT --", 800)
            return True

        return False

    # ---------- MODO COMANDO ----------

    def _manejar_comando(self, tecla, texto):
        if tecla in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._ejecutar_comando()
            self.en_comando = False
            self.buffer = ""
            return True

        if tecla == Qt.Key.Key_Escape:
            self.en_comando = False
            self.buffer = ""
            self.indicador.mostrar("-- cancelado --", 700)
            return True

        if tecla == Qt.Key.Key_Backspace:
            if len(self.buffer) > 1:
                self.buffer = self.buffer[:-1]
            self.indicador.mostrar(self.buffer, 5000)
            return True

        if texto and texto.isprintable():
            self.buffer += texto
            self.indicador.mostrar(self.buffer, 5000)
            return True

        return False

    def _ejecutar_comando(self):
        v = self.ventana

        if self.buffer.startswith("/"):
            termino = self.buffer[1:]
            if termino:
                view = v.pestana_actual()
                if view:
                    js = f"window.find({json.dumps(termino)});"
                    view.page().runJavaScript(js)
                self.indicador.mostrar(f"Buscar: {termino}", 1200)
            return

        cmd = self.buffer[1:].strip()
        cmd_lower = cmd.lower()

        if cmd_lower in ("t", "tab", "tabnew"):
            v.nueva_pestana()
            self.indicador.mostrar("Nueva pestaña", 800)
        elif cmd_lower in ("w", "wq", "q", "quit"):
            v.cerrar_pestana_actual()
            self.indicador.mostrar("Cerrando pestaña", 800)
        elif cmd_lower in ("qa", "quitall"):
            v.close()
        elif cmd_lower in ("h", "help"):
            self._mostrar_ayuda()
        elif cmd_lower in ("hist", "history"):
            v._abrir_ventana_historial()
        elif cmd_lower in ("fav", "favoritos", "bookmarks"):
            v._abrir_ventana_favoritos()
        elif cmd_lower in ("inc", "incognito"):
            v.abrir_incognito()
        elif cmd_lower in ("top", "home"):
            v.inicio_actual()
        elif cmd_lower.startswith("open "):
            destino = cmd[5:].strip()
            if destino:
                v.barra.setText(destino)
                v.navegar()
        else:
            self.indicador.mostrar(f"Comando desconocido: {self.buffer}", 1500)

    # ---------- UTILIDADES ----------

    def _foco_es_input(self, widget):
        if widget is None:
            return False
        clase = widget.metaObject().className()
        return clase in (
            "QLineEdit", "QTextEdit", "QPlainTextEdit",
            "QComboBox", "QSpinBox", "QDoubleSpinBox",
        )

    def _mostrar_ayuda(self):
        ayuda = (
            "j k: scroll   |   d/u: media página   |   gg / G: arriba/abajo\n"
            "f / F: atrás/adelante   |   r: recargar   |   i: foco al primer input\n"
            "t: nueva pestaña   |   x: cerrar   |   J / K: cambiar pestaña\n"
            "H: inicio   |   /: buscar   |   :t :w :q :help :inc :open URL"
        )
        self.indicador.mostrar(ayuda, 6000)
# barra_busqueda.py
# Barra para buscar texto dentro de la página (Ctrl+F).
# Solo emite señales: la ventana decide en qué pestaña buscar.

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget
)

import config
from assets.icons.helpers import icono


class BarraBusqueda(QWidget):

    buscar = pyqtSignal(str, bool)   # (texto, hacia_atras)
    cerrada = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("barra_busqueda")

        self.campo = QLineEdit()
        self.campo.setObjectName("campo_busqueda")
        self.campo.setPlaceholderText("Buscar en la página...")
        self.campo.setClearButtonEnabled(True)
        self.campo.textChanged.connect(self._al_escribir)
        self.campo.installEventFilter(self)

        self.lbl_resultado = QLabel("")
        self.lbl_resultado.setObjectName("resultado_busqueda")
        self.lbl_resultado.setMinimumWidth(96)
        self.lbl_resultado.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.btn_anterior = self._boton("chevron-up", "Anterior (Mayús+Enter)",
                                        self.anterior)
        self.btn_siguiente = self._boton("chevron-down", "Siguiente (Enter)",
                                         self.siguiente)
        self.btn_cerrar = self._boton("x", "Cerrar (Esc)", self.cerrar)

        fila = QHBoxLayout(self)
        fila.setContentsMargins(8, 2, 8, 6)
        fila.setSpacing(4)
        fila.addWidget(QLabel("Buscar"))
        fila.addWidget(self.campo, 1)
        fila.addWidget(self.lbl_resultado)
        fila.addWidget(self.btn_anterior)
        fila.addWidget(self.btn_siguiente)
        fila.addWidget(self.btn_cerrar)

        self.hide()

    # ---------- construcción ----------

    def _boton(self, nombre, tooltip, slot):
        b = QPushButton()
        b.setObjectName("btn_busqueda")
        b.setIcon(icono(nombre, config.COLOR_TEXTO_SUAVE, 16))
        b.setToolTip(tooltip)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setFixedSize(26, 26)
        b.clicked.connect(slot)
        return b

    # ---------- estado ----------

    def esta_abierta(self):
        return not self.isHidden()

    def texto(self):
        return self.campo.text()

    def abrir(self):
        """Muestra la barra y pone el foco en el campo, sin borrar lo escrito."""
        self.show()
        self.campo.setFocus()
        self.campo.selectAll()
        if self.campo.text():
            self.buscar.emit(self.campo.text(), False)

    def cerrar(self):
        if not self.esta_abierta():
            return
        self.hide()
        self.campo.clear()
        self.lbl_resultado.setText("")
        self.cerrada.emit()

    # ---------- búsqueda ----------

    def siguiente(self):
        self._emitir(False)

    def anterior(self):
        self._emitir(True)

    def _emitir(self, atras):
        if not self.esta_abierta():
            return
        self.buscar.emit(self.campo.text(), atras)

    def _al_escribir(self, texto):
        # Al borrar el campo se quita el resaltado.
        self.buscar.emit(texto, False)

    def mostrar_resultado(self, actual, total):
        if total <= 0:
            self.lbl_resultado.setText("Sin resultados")
            self.lbl_resultado.setStyleSheet(
                "color: " + config.COLOR_AVISO + "; font-size: 11px;"
            )
        else:
            self.lbl_resultado.setText(f"{actual} de {total}")
            self.lbl_resultado.setStyleSheet(
                "color: " + config.COLOR_TEXTO_SUAVE + "; font-size: 11px;"
            )

    def limpiar_resultado(self):
        self.lbl_resultado.setText("")

    # ---------- teclado ----------

    def eventFilter(self, obj, evento):
        if obj is self.campo and evento.type() == evento.Type.KeyPress:
            tecla = evento.key()
            if tecla == Qt.Key.Key_Escape:
                self.cerrar()
                return True
            if tecla in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                atras = bool(
                    evento.modifiers() & Qt.KeyboardModifier.ShiftModifier
                )
                self._emitir(atras)
                return True
        return super().eventFilter(obj, evento)

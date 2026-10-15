# ventana_historial.py
# Ventana con la lista completa del historial, buscador y botón de borrar.

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QLabel
)
from PyQt6.QtCore import Qt
import config


class VentanaHistorial(QDialog):
    """
    Muestra el historial completo. Al hacer doble clic en una entrada,
    emite la URL seleccionada en `self.url_seleccionada` y se cierra.
    """

    def __init__(self, historial, parent=None):
        super().__init__(parent)
        self.historial = historial
        self.url_seleccionada = None  # aquí guardaremos la URL elegida

        self.setWindowTitle("Historial")
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        # --- Buscador ---
        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText("Buscar en el historial...")
        self.buscador.textChanged.connect(self._refrescar)
        layout.addWidget(self.buscador)

        # --- Lista ---
        self.lista = QListWidget()
        self.lista.itemDoubleClicked.connect(self._abrir_seleccion)
        layout.addWidget(self.lista)

        # --- Barra inferior ---
        abajo = QHBoxLayout()
        self.info = QLabel("")
        abajo.addWidget(self.info)
        abajo.addStretch()

        btn_borrar = QPushButton("Borrar todo")
        btn_borrar.clicked.connect(self._borrar_todo)
        abajo.addWidget(btn_borrar)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.close)
        abajo.addWidget(btn_cerrar)

        layout.addLayout(abajo)

        self._refrescar()

    def _refrescar(self):
        """Rellena la lista según el texto del buscador."""
        self.lista.clear()
        entradas = self.historial.buscar(self.buscador.text())

        for e in entradas:
            texto = f"{e.get('fecha','')}  ·  {e.get('titulo','')}\n{e.get('url','')}"
            item = QListWidgetItem(texto)
            item.setData(Qt.ItemDataRole.UserRole, e.get("url", ""))
            self.lista.addItem(item)

        self.info.setText(f"{len(entradas)} entradas")

    def _abrir_seleccion(self, item):
        url = item.data(Qt.ItemDataRole.UserRole)
        if url:
            self.url_seleccionada = url
            self.accept()  # cierra el diálogo con "aceptado"

    def _borrar_todo(self):
        self.historial.borrar_todo()
        self._refrescar()
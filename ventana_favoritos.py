# ventana_favoritos.py
# Ventana gestora de favoritos: buscar, renombrar, eliminar, abrir.

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QLabel, QInputDialog
)
from PyQt6.QtCore import Qt
import config


class VentanaFavoritos(QDialog):

    def __init__(self, favoritos, parent=None):
        super().__init__(parent)
        self.favoritos = favoritos
        self.url_seleccionada = None

        self.setWindowTitle("Favoritos")
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText("Buscar en favoritos...")
        self.buscador.textChanged.connect(self._refrescar)
        layout.addWidget(self.buscador)

        self.lista = QListWidget()
        self.lista.itemDoubleClicked.connect(self._abrir_seleccion)
        layout.addWidget(self.lista)

        abajo = QHBoxLayout()
        self.info = QLabel("")
        abajo.addWidget(self.info)
        abajo.addStretch()

        btn_renombrar = QPushButton("Renombrar")
        btn_renombrar.clicked.connect(self._renombrar)
        abajo.addWidget(btn_renombrar)

        btn_eliminar = QPushButton("Eliminar")
        btn_eliminar.clicked.connect(self._eliminar)
        abajo.addWidget(btn_eliminar)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.close)
        abajo.addWidget(btn_cerrar)

        layout.addLayout(abajo)
        self._refrescar()

    def _refrescar(self):
        self.lista.clear()
        entradas = self.favoritos.buscar(self.buscador.text())
        for e in entradas:
            texto = f"{e.get('titulo','')}\n{e.get('url','')}"
            item = QListWidgetItem(texto)
            item.setData(Qt.ItemDataRole.UserRole, e.get("url", ""))
            self.lista.addItem(item)
        self.info.setText(f"{len(entradas)} favoritos")

    def _url_actual(self):
        item = self.lista.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _abrir_seleccion(self, item):
        url = item.data(Qt.ItemDataRole.UserRole)
        if url:
            self.url_seleccionada = url
            self.accept()

    def _renombrar(self):
        url = self._url_actual()
        if not url:
            return
        actual = ""
        for e in self.favoritos.todos():
            if e.get("url") == url:
                actual = e.get("titulo", "")
                break
        nuevo, ok = QInputDialog.getText(
            self, "Renombrar favorito", "Nuevo nombre:", text=actual
        )
        if ok and nuevo.strip():
            self.favoritos.renombrar(url, nuevo.strip())
            self._refrescar()

    def _eliminar(self):
        url = self._url_actual()
        if not url:
            return
        self.favoritos.eliminar(url)
        self._refrescar()
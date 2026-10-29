# pestanas.py
# Pestañas con la barra (las "píldoras") separada de las páginas.
# Así la barra de pestañas puede ir arriba del todo, en la fila de la
# ventana, y las páginas debajo. Tiene la misma interfaz que QTabWidget
# (addTab, widget, indexOf...), así que el resto del programa no cambia.

from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtWidgets import QStackedWidget, QTabBar


class Pestanas(QObject):

    currentChanged = pyqtSignal(int)
    tabCloseRequested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.barra = QTabBar()
        self.barra.setObjectName("pestanas")
        self.barra.setTabsClosable(True)
        self.barra.setMovable(True)
        self.barra.setExpanding(False)
        self.barra.setDrawBase(False)
        self.barra.setUsesScrollButtons(True)
        self.barra.setElideMode(Qt.TextElideMode.ElideRight)
        self.barra.setDocumentMode(True)
        self.barra.setChangeCurrentOnDrag(True)

        self.paginas = QStackedWidget()

        # Lista paralela a las pestañas (mismo orden que la barra).
        self._paginas = []

        self.barra.currentChanged.connect(self._on_current_changed)
        self.barra.tabCloseRequested.connect(self.tabCloseRequested)
        self.barra.tabMoved.connect(self._on_moved)

    # ---------- interfaz tipo QTabWidget ----------

    def addTab(self, widget, texto=""):
        self.paginas.addWidget(widget)
        # La lista va ANTES que la barra: addTab dispara currentChanged
        # y los que escuchan ya necesitan encontrar la página.
        self._paginas.append(widget)
        return self.barra.addTab(texto)

    def removeTab(self, idx):
        if not 0 <= idx < len(self._paginas):
            return
        widget = self._paginas.pop(idx)
        self.paginas.removeWidget(widget)
        self.barra.removeTab(idx)

    def count(self):
        return len(self._paginas)

    def widget(self, idx):
        if 0 <= idx < len(self._paginas):
            return self._paginas[idx]
        return None

    def indexOf(self, widget):
        try:
            return self._paginas.index(widget)
        except ValueError:
            return -1

    def currentIndex(self):
        return self.barra.currentIndex()

    def currentWidget(self):
        return self.widget(self.barra.currentIndex())

    def setCurrentIndex(self, idx):
        self.barra.setCurrentIndex(idx)

    def setCurrentWidget(self, widget):
        self.setCurrentIndex(self.indexOf(widget))

    def setTabText(self, idx, texto):
        self.barra.setTabText(idx, texto)

    def tabText(self, idx):
        return self.barra.tabText(idx)

    def setTabToolTip(self, idx, texto):
        self.barra.setTabToolTip(idx, texto)

    def setTabIcon(self, idx, icono):
        self.barra.setTabIcon(idx, icono)

    def tabIcon(self, idx):
        return self.barra.tabIcon(idx)

    # ---------- internos ----------

    def _on_current_changed(self, idx):
        pagina = self.widget(idx)
        if pagina is not None:
            self.paginas.setCurrentWidget(pagina)
        self.currentChanged.emit(idx)

    def _on_moved(self, desde, hasta):
        self._paginas.insert(hasta, self._paginas.pop(desde))

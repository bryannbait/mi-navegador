# ventana_descargas.py
# Panel de descargas con progreso, pausa/reanudar, cancelar, abrir.

import os
import config

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QScrollArea, QWidget, QMessageBox
)
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest


def _legible(n):
    """Convierte bytes a un texto corto: 1536 -> '1.5 KB'."""
    n = float(n)
    for unidad in ("B", "KB", "MB", "GB"):
        if n < 1024 or unidad == "GB":
            return f"{n:.0f} {unidad}" if unidad == "B" else f"{n:.1f} {unidad}"
        n /= 1024


class FilaDescarga(QWidget):
    """Una fila por descarga con progreso y botones."""

    def __init__(self, download, entrada, parent=None):
        super().__init__(parent)
        self.download = download      # None si es una descarga del historial
        self.entrada = entrada        # dict del modelo Descargas
        self.panel = parent           # VentanaDescargas (tiene .gestor)
        self._terminada = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)

        # Nombre
        self.lbl_nombre = QLabel(entrada.get("nombre", "archivo"))
        self.lbl_nombre.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.lbl_nombre)

        # Progreso (0..1000 = décimas de %; así no hay límite de tamaño:
        # QProgressBar usa enteros de 32 bits y un archivo de 3 GB no cabe).
        self.barra = QProgressBar()
        self.barra.setRange(0, 1000)
        self.barra.setTextVisible(True)
        self.barra.setFormat("%p%")
        layout.addWidget(self.barra)

        # Estado
        self.lbl_estado = QLabel("Iniciando…")
        self.lbl_estado.setStyleSheet("color: " + config.COLOR_TEXTO_SUAVE + "; font-size: 11px;")
        layout.addWidget(self.lbl_estado)

        # Botones
        botones = QHBoxLayout()

        self.btn_pausa = QPushButton("Pausar")
        self.btn_pausa.clicked.connect(self._pausar_reanudar)
        botones.addWidget(self.btn_pausa)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self._cancelar)
        botones.addWidget(self.btn_cancelar)

        self.btn_carpeta = QPushButton("Abrir carpeta")
        self.btn_carpeta.clicked.connect(self._abrir_carpeta)
        self.btn_carpeta.setEnabled(False)
        botones.addWidget(self.btn_carpeta)

        self.btn_abrir = QPushButton("Abrir")
        self.btn_abrir.clicked.connect(self._abrir_archivo)
        self.btn_abrir.setEnabled(False)
        botones.addWidget(self.btn_abrir)

        botones.addStretch()
        layout.addLayout(botones)

        if download is not None:
            # Descarga en vivo: escuchamos sus señales.
            download.receivedBytesChanged.connect(self._on_progreso)
            download.totalBytesChanged.connect(self._on_progreso)
            download.stateChanged.connect(self._on_estado)
        else:
            # Fila del historial: no hay descarga viva, solo mostramos el
            # resultado guardado (y desactivamos Pausar/Cancelar).
            estado = entrada.get("estado", "completada")
            if estado not in ("completada", "cancelada", "interrumpida"):
                estado = "interrumpida"
            self._terminar(estado, guardar=False)

    # ---------- EVENTOS ----------

    def _on_progreso(self):
        if self._terminada:
            return
        recibidos = self.download.receivedBytes()
        total = self.download.totalBytes()
        if total > 0:
            self.barra.setRange(0, 1000)
            self.barra.setValue(int(recibidos * 1000 / total))
            self.lbl_estado.setText(
                f"Descargando…  {_legible(recibidos)} / {_legible(total)}"
            )
        else:
            # El servidor no dijo el tamaño: barra animada sin porcentaje.
            self.barra.setRange(0, 0)
            self.lbl_estado.setText(f"Descargando…  {_legible(recibidos)}")

    def _on_estado(self, estado):
        S = QWebEngineDownloadRequest.DownloadState
        if estado == S.DownloadCompleted:
            self._terminar("completada")
        elif estado == S.DownloadCancelled:
            self._terminar("cancelada")
        elif estado == S.DownloadInterrupted:
            self._terminar("interrumpida")

    def _terminar(self, estado, guardar=True):
        """Deja la fila en un estado final y lo anota en el modelo."""
        if self._terminada:
            return
        self._terminada = True

        # Tamaño final y estado, en el modelo (y a disco).
        self.entrada["estado"] = estado
        if self.download is not None:
            total = self.download.totalBytes()
            self.entrada["tamano"] = (
                total if total > 0 else self.download.receivedBytes()
            )
        if guardar and self.panel is not None:
            self.panel.gestor.guardar()

        self.btn_pausa.setEnabled(False)
        self.btn_cancelar.setEnabled(False)
        hecha = estado == "completada"
        self.btn_carpeta.setEnabled(hecha)
        self.btn_abrir.setEnabled(hecha)

        self.barra.setRange(0, 1000)
        self.barra.setValue(1000 if hecha else self.barra.value())

        tamano = self.entrada.get("tamano") or 0
        detalle = f" · {_legible(tamano)}" if tamano > 0 else ""
        fecha = self.entrada.get("fecha", "")
        if fecha:
            detalle += f" · {fecha}"
        textos = {
            "completada": "✅ Completada",
            "cancelada": "❌ Cancelada",
            "interrumpida": "⚠️ Interrumpida",
        }
        self.lbl_estado.setText(textos[estado] + detalle)

    # ---------- ACCIONES ----------

    def _pausar_reanudar(self):
        if self.download is None:
            return
        if self.download.isPaused():
            self.download.resume()
            self.btn_pausa.setText("Pausar")
            self.lbl_estado.setText("Descargando…")
        else:
            self.download.pause()
            self.btn_pausa.setText("Reanudar")
            self.lbl_estado.setText("⏸ Pausada")

    def _cancelar(self):
        # Al cancelar, la descarga emite stateChanged y _on_estado hace el resto.
        if self.download is not None:
            self.download.cancel()

    def _abrir_carpeta(self):
        ruta = self.entrada.get("ruta", "")
        if not ruta:
            return
        carpeta = os.path.dirname(ruta)
        if os.path.isdir(carpeta):
            QDesktopServices.openUrl(QUrl.fromLocalFile(carpeta))

    def _abrir_archivo(self):
        ruta = self.entrada.get("ruta", "")
        if ruta and os.path.isfile(ruta):
            QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))
        else:
            QMessageBox.warning(self, "Archivo", "El archivo ya no está en esa ruta.")


class VentanaDescargas(QDialog):
    """Panel con la lista de descargas activas e históricas."""

    def __init__(self, gestor_descargas, parent=None):
        super().__init__(parent)
        self.gestor = gestor_descargas
        self.filas = {}  # id(download) -> FilaDescarga

        self.setWindowTitle("Descargas")
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        # Cabecera
        cabecera = QLabel(f"Descargas  ({len(self.gestor.todos())} en historial)")
        cabecera.setStyleSheet("font-size: 14px; font-weight: bold; padding: 4px;")
        layout.addWidget(cabecera)
        self.cabecera = cabecera

        # Área scrollable
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; }")
        self.contenedor = QWidget()
        self.layout_filas = QVBoxLayout(self.contenedor)
        self.layout_filas.setSpacing(6)
        self.layout_filas.addStretch()
        self.scroll.setWidget(self.contenedor)
        layout.addWidget(self.scroll)

        # Botones inferiores
        abajo = QHBoxLayout()
        abajo.addStretch()

        btn_limpiar = QPushButton("Borrar historial")
        btn_limpiar.clicked.connect(self._borrar_historial)
        abajo.addWidget(btn_limpiar)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.close)
        abajo.addWidget(btn_cerrar)

        layout.addLayout(abajo)

        # Cargar el historial previo (sin descarga viva). Vamos de la más
        # antigua a la más nueva porque cada fila nueva se pone ARRIBA.
        for entrada in reversed(self.gestor.todos()):
            self.añadir_descarga(None, entrada)

    def añadir_descarga(self, download, entrada):
        fila = FilaDescarga(download, entrada, self)
        if download is not None:
            self.filas[id(download)] = fila
        # Las más nuevas arriba.
        self.layout_filas.insertWidget(0, fila)
        self.cabecera.setText(f"Descargas  ({len(self.gestor.todos())} en historial)")

    def _borrar_historial(self):
        self.gestor.borrar_todo()
        # Recargar la vista.
        while self.layout_filas.count() > 1:
            item = self.layout_filas.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.filas.clear()
        self.cabecera.setText("Descargas  (0 en historial)")

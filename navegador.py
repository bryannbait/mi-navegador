# navegador.py
# Clase MiNavegador y helpers. Importar desde main.py o ventana_incognito.py.

import os
import json
from urllib.parse import quote, urlparse

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLineEdit, QToolBar, QPushButton,
    QProgressBar, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy,
    QMenu, QInputDialog, QCompleter, QFileDialog
)
from PyQt6.QtCore import QUrl, Qt, QStringListModel, QTimer, QSize
from PyQt6.QtGui import QAction, QKeySequence, QPalette, QColor, QIcon
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile, QWebEngineSettings
)

from bloqueador import Bloqueador
from ventana_historial import VentanaHistorial
from ventana_favoritos import VentanaFavoritos
from ventana_descargas import VentanaDescargas
from atajos_vim import VimKeys
from puente_vim import PaginaVim, crear_script_vim
from pestanas import Pestanas
import pagina_inicio
from assets.icons.helpers import icono, ruta_icono
import motores
import config


# ---------- VARIABLES GLOBALES ----------

interceptor = None   # interceptor del perfil normal (lo crea configurar_perfil)


def url_a_texto(qurl):
    """URL como texto para GUARDAR (historial, favoritos). Los espacios van
    como %20 para que la URL siga siendo válida al volver a abrirla."""
    return qurl.toString(QUrl.ComponentFormattingOption.EncodeSpaces)


def configurar_perfil(gestor):
    global interceptor
    perfil = QWebEngineProfile.defaultProfile()
    perfil.setHttpUserAgent(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    perfil.setHttpCacheMaximumSize(50 * 1024 * 1024)
    interceptor = Bloqueador(gestor)
    perfil.setUrlRequestInterceptor(interceptor)

    # Detector Vim para inputs.
    perfil.scripts().insert(crear_script_vim())

    ajustes = perfil.settings()
    ajustes.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
    ajustes.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
    ajustes.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
    return perfil


def hoja_de_estilos():
    t = config
    cerrar = ruta_icono("tab-close")
    cerrar_hover = ruta_icono("tab-close-hover")
    return f"""
    QMainWindow {{ background-color: {t.COLOR_FONDO}; }}
    QWidget {{ color: {t.COLOR_TEXTO}; }}
    QToolTip {{
        background-color: {t.COLOR_SUPERFICIE_2}; color: {t.COLOR_TEXTO};
        border: 1px solid {t.COLOR_BORDE}; border-radius: 6px; padding: 4px 8px;
    }}

    /* ---- cabecera: pestañas + navegación ---- */
    QFrame#chrome {{
        background-color: {t.COLOR_TOOLBAR};
        border-bottom: 1px solid {t.COLOR_BORDE};
    }}
    QFrame#chrome[incognito="true"] {{ background-color: {t.COLOR_INCOGNITO}; }}

    QTabBar#pestanas {{ background: transparent; }}
    QTabBar#pestanas::tab {{
        background: transparent; color: {t.COLOR_TEXTO_SUAVE};
        height: 30px; padding: 0 10px 0 12px; margin: 3px 2px 3px 2px;
        border-radius: 10px; min-width: 110px; max-width: 220px; font-size: 12px;
    }}
    QTabBar#pestanas::tab:selected {{
        background-color: {t.COLOR_SUPERFICIE}; color: {t.COLOR_TEXTO};
    }}
    QTabBar#pestanas::tab:hover:!selected {{
        background-color: {t.COLOR_SUPERFICIE_2}; color: {t.COLOR_TEXTO};
    }}
    QTabBar#pestanas::close-button {{
        image: url("{cerrar}"); subcontrol-position: right;
        border-radius: 7px; padding: 2px; margin-right: 2px;
    }}
    QTabBar#pestanas::close-button:hover {{
        image: url("{cerrar_hover}"); background-color: {t.COLOR_ACENTO_FUERTE};
    }}
    QTabBar#pestanas QToolButton {{ background: transparent; border: none; }}

    /* ---- botones ---- */
    QPushButton {{
        background-color: {t.COLOR_SUPERFICIE}; color: {t.COLOR_TEXTO};
        border: 1px solid {t.COLOR_BORDE}; border-radius: 8px; padding: 6px 14px;
    }}
    QPushButton:hover {{ background-color: {t.COLOR_SUPERFICIE_2}; }}
    QPushButton:pressed {{ background-color: {t.COLOR_ACENTO_FUERTE}; color: white; }}
    QPushButton:disabled {{ color: {t.COLOR_TEXTO_SUAVE}; }}
    QPushButton:default {{ border-color: {t.COLOR_ACENTO}; }}

    QPushButton#btn_icono {{
        background: transparent; border: none; border-radius: 17px;
        padding: 0; min-width: 34px; max-width: 34px; min-height: 34px; max-height: 34px;
    }}
    QPushButton#btn_icono:hover {{ background-color: {t.COLOR_SUPERFICIE_2}; }}
    QPushButton#btn_icono:pressed {{ background-color: {t.COLOR_ACENTO_FUERTE}; }}

    QPushButton#btn_motor {{
        background-color: {t.COLOR_SUPERFICIE}; border: none; border-radius: 17px;
        padding: 0; min-width: 34px; max-width: 34px; min-height: 34px; max-height: 34px;
        font-size: 15px;
    }}
    QPushButton#btn_motor:hover {{ background-color: {t.COLOR_SUPERFICIE_2}; }}

    QPushButton#escudo_activo, QPushButton#escudo_inactivo {{
        background-color: {t.COLOR_SUPERFICIE}; border: none; border-radius: 17px;
        min-height: 34px; max-height: 34px; padding: 0 12px;
        font-size: 12px; font-weight: bold;
    }}
    QPushButton#escudo_activo {{ color: {t.COLOR_OK}; }}
    QPushButton#escudo_inactivo {{ color: {t.COLOR_TEXTO_SUAVE}; }}
    QPushButton#escudo_activo:hover, QPushButton#escudo_inactivo:hover {{
        background-color: {t.COLOR_SUPERFICIE_2};
    }}

    /* ---- barra de direcciones ---- */
    QLineEdit {{
        background-color: {t.COLOR_SUPERFICIE}; color: {t.COLOR_TEXTO};
        border: 1px solid {t.COLOR_BORDE}; border-radius: 8px; padding: 6px 10px;
        selection-background-color: {t.COLOR_ACENTO}; selection-color: white;
    }}
    QLineEdit:focus {{ border: 1px solid {t.COLOR_ACENTO}; }}
    QLineEdit#barra_direcciones {{
        border: 1px solid transparent; border-radius: 17px;
        min-height: 32px; padding: 0 8px; font-size: 13px;
    }}
    QLineEdit#barra_direcciones:hover {{ border-color: {t.COLOR_BORDE}; }}
    QLineEdit#barra_direcciones:focus {{ border: 1px solid {t.COLOR_ACENTO}; }}

    /* ---- favoritos ---- */
    QToolBar#barra_favoritos {{
        background: transparent; border: none; padding: 0 8px 6px 8px; spacing: 4px;
    }}
    QToolBar#barra_favoritos QPushButton {{
        background: transparent; border: none; border-radius: 12px;
        padding: 4px 10px; font-size: 12px; color: {t.COLOR_TEXTO_SUAVE};
    }}
    QToolBar#barra_favoritos QPushButton:hover {{
        background-color: {t.COLOR_SUPERFICIE_2}; color: {t.COLOR_TEXTO};
    }}

    /* ---- progreso ---- */
    QProgressBar {{
        background-color: {t.COLOR_SUPERFICIE_2}; border: none; border-radius: 4px;
        text-align: center; color: {t.COLOR_TEXTO};
    }}
    QProgressBar::chunk {{
        border-radius: 4px;
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {t.COLOR_ACENTO_FUERTE}, stop:1 {t.COLOR_ACENTO_SUAVE});
    }}
    QProgressBar#progreso_carga {{
        background: transparent; border-radius: 0;
        min-height: 2px; max-height: 2px;
    }}
    QProgressBar#progreso_carga::chunk {{ border-radius: 0; }}

    /* ---- menús ---- */
    QMenu {{
        background-color: {t.COLOR_SUPERFICIE}; color: {t.COLOR_TEXTO};
        border: 1px solid {t.COLOR_BORDE}; border-radius: 10px; padding: 6px;
    }}
    QMenu::item {{ padding: 7px 28px 7px 14px; border-radius: 6px; }}
    QMenu::item:selected {{ background-color: {t.COLOR_ACENTO}; color: white; }}
    QMenu::item:disabled {{ color: {t.COLOR_TEXTO_SUAVE}; background: transparent; }}
    QMenu::separator {{ height: 1px; background-color: {t.COLOR_BORDE}; margin: 6px 8px; }}

    /* ---- diálogos y listas ---- */
    QDialog, QMessageBox, QInputDialog {{ background-color: {t.COLOR_FONDO}; }}
    QLabel {{ background: transparent; }}
    QListWidget, QTableWidget, QTreeWidget {{
        background-color: {t.COLOR_SUPERFICIE}; color: {t.COLOR_TEXTO};
        border: 1px solid {t.COLOR_BORDE}; border-radius: 10px; padding: 4px; outline: none;
    }}
    QListWidget::item {{ padding: 7px 8px; border-radius: 6px; }}
    QListWidget::item:hover {{ background-color: {t.COLOR_SUPERFICIE_2}; }}
    QListWidget::item:selected {{ background-color: {t.COLOR_ACENTO}; color: white; }}
    QScrollArea {{ background: transparent; border: none; }}

    QCompleter QAbstractItemView, QListView {{
        background-color: {t.COLOR_SUPERFICIE}; color: {t.COLOR_TEXTO};
        border: 1px solid {t.COLOR_BORDE}; selection-background-color: {t.COLOR_ACENTO};
        selection-color: white; padding: 4px; outline: none;
    }}

    QStatusBar {{
        background-color: {t.COLOR_TOOLBAR}; color: {t.COLOR_TEXTO_SUAVE};
        border-top: 1px solid {t.COLOR_BORDE};
    }}
    QStatusBar::item {{ border: none; }}

    /* ---- barras de desplazamiento ---- */
    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
    QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
    QScrollBar::handle:vertical {{
        background: {t.COLOR_SUPERFICIE_2}; border-radius: 3px; min-height: 30px;
    }}
    QScrollBar::handle:horizontal {{
        background: {t.COLOR_SUPERFICIE_2}; border-radius: 3px; min-width: 30px;
    }}
    QScrollBar::handle:hover {{ background: {t.COLOR_ACENTO}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
    """


def aplicar_tema(app):
    """Fusion + paleta oscura + hoja de estilos. Llamar una vez tras crear QApplication."""
    t = config
    app.setStyle("Fusion")   # base uniforme en todos los sistemas (sin esquinas claras)
    p = QPalette()
    roles = {
        QPalette.ColorRole.Window: t.COLOR_FONDO,
        QPalette.ColorRole.WindowText: t.COLOR_TEXTO,
        QPalette.ColorRole.Base: t.COLOR_SUPERFICIE,
        QPalette.ColorRole.AlternateBase: t.COLOR_TOOLBAR,
        QPalette.ColorRole.Text: t.COLOR_TEXTO,
        QPalette.ColorRole.Button: t.COLOR_SUPERFICIE,
        QPalette.ColorRole.ButtonText: t.COLOR_TEXTO,
        QPalette.ColorRole.BrightText: "#ffffff",
        QPalette.ColorRole.Highlight: t.COLOR_ACENTO,
        QPalette.ColorRole.HighlightedText: "#ffffff",
        QPalette.ColorRole.ToolTipBase: t.COLOR_SUPERFICIE_2,
        QPalette.ColorRole.ToolTipText: t.COLOR_TEXTO,
        QPalette.ColorRole.PlaceholderText: t.COLOR_TEXTO_SUAVE,
        QPalette.ColorRole.Link: t.COLOR_ACENTO_SUAVE,
    }
    for rol, col in roles.items():
        p.setColor(rol, QColor(col))
    for rol in (QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText,
                QPalette.ColorRole.WindowText):
        p.setColor(QPalette.ColorGroup.Disabled, rol, QColor(t.COLOR_TEXTO_SUAVE))
    app.setPalette(p)
    app.setStyleSheet(hoja_de_estilos())


# ---------- VENTANA PRINCIPAL ----------

class MiNavegador(QMainWindow):

    def __init__(self, gestor, prefs, historial, favoritos, descargas,
                 perfil_web=None, interceptor_propio=None, es_incognito=False):
        super().__init__()

        self.gestor = gestor
        self.prefs = prefs

        # Modelos compartidos (pasados por constructor).
        self.historial = historial
        self.favoritos = favoritos
        self.descargas = descargas

        # Modo incógnito.
        self.es_incognito = es_incognito
        self.perfil_web = perfil_web
        self.interceptor_actual = (
            interceptor_propio if interceptor_propio is not None else interceptor
        )

        self.motor_actual = prefs.get(
            "motor_busqueda", motores.motor_por_defecto()
        )

        # Las descargas del perfil de ESTA ventana (normal o incógnito)
        # las gestiona esta ventana, con SUS modelos.
        self._panel_descargas = None
        perfil = (perfil_web if perfil_web is not None
                  else QWebEngineProfile.defaultProfile())
        perfil.downloadRequested.connect(self._descarga_solicitada)

        self.setWindowTitle(f"{config.NOMBRE} {config.VERSION}")
        self.resize(1200, 800)

        # --- Red para sugerencias ---
        self.net = QNetworkAccessManager(self)
        self.reply_sugerencias = None

        # --- Barra de direcciones (píldora con candado y estrella dentro) ---
        self.barra = QLineEdit()
        self.barra.setObjectName("barra_direcciones")
        self.barra.setPlaceholderText(
            "Busca o escribe una dirección...  (!g, !w para atajos)"
        )
        self.barra.returnPressed.connect(self.navegar)
        self.barra.textEdited.connect(self._pedir_sugerencias)

        self.accion_candado = self.barra.addAction(
            icono("search", config.COLOR_TEXTO_SUAVE, 16),
            QLineEdit.ActionPosition.LeadingPosition)
        self.accion_estrella = self.barra.addAction(
            icono("star", config.COLOR_TEXTO_SUAVE, 18),
            QLineEdit.ActionPosition.TrailingPosition)
        self.accion_estrella.setToolTip("Añadir a favoritos (Ctrl+D)")
        self.accion_estrella.triggered.connect(self._toggle_favorito)

        # --- Autocompletado ---
        self.modelo_sugerencias = QStringListModel([], self)
        self.completer = QCompleter(self.modelo_sugerencias, self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.barra.setCompleter(self.completer)

        # --- Pestañas (la barra va arriba, las páginas debajo) ---
        self.tabs = Pestanas(self)
        self.tabs.barra.setIconSize(QSize(16, 16))
        self.tabs.tabCloseRequested.connect(self.cerrar_pestana)
        self.tabs.currentChanged.connect(self.cambio_de_pestana)

        self.btn_nueva = self._boton_icono("plus", "Nueva pestaña (Ctrl+T)",
                                           lambda: self.nueva_pestana())

        # --- Fila 1: pestañas ---
        fila_tabs = QHBoxLayout()
        fila_tabs.setContentsMargins(8, 4, 8, 0)
        fila_tabs.setSpacing(4)
        if self.es_incognito:
            marca = QPushButton()
            marca.setObjectName("btn_icono")
            marca.setIcon(icono("eye-off", config.COLOR_ACENTO_SUAVE, 18))
            marca.setIconSize(QSize(18, 18))
            marca.setToolTip("Modo incógnito")
            marca.setEnabled(False)
            fila_tabs.addWidget(marca)
        fila_tabs.addWidget(self.tabs.barra)
        fila_tabs.addWidget(self.btn_nueva)
        fila_tabs.addStretch(1)

        # --- Fila 2: navegación ---
        self.btn_atras = self._boton_icono("arrow-left", "Atrás (Alt+←)", self.atras_actual)
        self.btn_adelante = self._boton_icono("arrow-right", "Adelante (Alt+→)", self.adelante_actual)
        self.btn_recargar = self._boton_icono("rotate-cw", "Recargar (F5)", self.recargar_o_detener)
        btn_inicio = self._boton_icono("home", "Inicio (Alt+Inicio)", self.inicio_actual)

        self.btn_motor = QPushButton()
        self.btn_motor.setObjectName("btn_motor")
        self.btn_motor.clicked.connect(self._mostrar_menu_motores)
        self._actualizar_icono_motor()

        self.btn_escudo = QPushButton(" 0")
        self.btn_escudo.setObjectName("escudo_inactivo")
        self.btn_escudo.setIcon(icono("shield", config.COLOR_TEXTO_SUAVE, 16))
        self.btn_escudo.setIconSize(QSize(16, 16))
        self.btn_escudo.setToolTip("Bloqueador de anuncios")
        self.btn_escudo.clicked.connect(self._mostrar_menu_escudo)

        btn_fav = self._boton_icono("bookmark", "Gestionar favoritos (Ctrl+Shift+O)",
                                    self._abrir_ventana_favoritos)
        self.btn_historial = self._boton_icono("clock", "Historial", self._mostrar_menu_historial)
        btn_inc = self._boton_icono("eye-off", "Nueva ventana de incógnito (Ctrl+Shift+N)",
                                    self.abrir_incognito)
        btn_desc = self._boton_icono("download", "Descargas (Ctrl+J)", self.abrir_panel_descargas)

        fila_nav = QHBoxLayout()
        fila_nav.setContentsMargins(8, 4, 8, 6)
        fila_nav.setSpacing(4)
        for w in (self.btn_atras, self.btn_adelante, self.btn_recargar, btn_inicio,
                  self.btn_motor):
            fila_nav.addWidget(w)
        fila_nav.addWidget(self.barra, 1)
        for w in (self.btn_escudo, btn_fav, self.btn_historial, btn_inc, btn_desc):
            fila_nav.addWidget(w)

        # --- Fila 3: marcadores ---
        self.barra_fav = QToolBar("Favoritos")
        self.barra_fav.setObjectName("barra_favoritos")
        self.barra_fav.setMovable(False)

        # --- Cabecera (un solo bloque con el color del tema) ---
        self.chrome = QFrame()
        self.chrome.setObjectName("chrome")
        self.chrome.setProperty("incognito", self.es_incognito)
        caja = QVBoxLayout(self.chrome)
        caja.setContentsMargins(0, 0, 0, 0)
        caja.setSpacing(0)
        caja.addLayout(fila_tabs)
        caja.addLayout(fila_nav)
        caja.addWidget(self.barra_fav)

        # --- Progreso (2 px; reserva su hueco para que la página no salte) ---
        self.progreso = QProgressBar()
        self.progreso.setObjectName("progreso_carga")
        self.progreso.setTextVisible(False)
        self.progreso.setFixedHeight(2)
        pol = self.progreso.sizePolicy()
        pol.setRetainSizeWhenHidden(True)
        self.progreso.setSizePolicy(pol)
        self.progreso.hide()

        # --- Layout general ---
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.chrome)
        layout.addWidget(self.progreso)
        layout.addWidget(self.tabs.paginas, 1)
        self.setCentralWidget(contenedor)

        # El interceptor necesita saber a qué ventana avisar (escudo).
        if self.interceptor_actual is not None:
            self.interceptor_actual.navegador = self

        # Refresca el escudo como mucho cada 150 ms, no en cada petición.
        self._timer_escudo = QTimer(self)
        self._timer_escudo.setSingleShot(True)
        self._timer_escudo.setInterval(150)
        self._timer_escudo.timeout.connect(self.actualizar_escudo)

        # Vim.
        self.vim = VimKeys(self)

        self._crear_atajos()
        self._refrescar_barra_favoritos()
        self.nueva_pestana()

    # ---------- AYUDAS DE INTERFAZ ----------

    def _boton_icono(self, nombre, tooltip, slot):
        """Botón redondo de 34x34 con un icono."""
        b = QPushButton()
        b.setObjectName("btn_icono")
        b.setIcon(icono(nombre, config.COLOR_TEXTO, 18))
        b.setIconSize(QSize(18, 18))
        b.setToolTip(tooltip)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.clicked.connect(slot)
        return b

    def _html_inicio(self):
        favs = [] if self.es_incognito else self.favoritos.todos()
        return pagina_inicio.generar_html(
            favs, motores.obtener(self.motor_actual)["nombre"], self.es_incognito)

    @staticmethod
    def _es_url_vacia(qurl):
        """La página de inicio propia (data:) o about:blank no muestran dirección."""
        return qurl.scheme() in ("data", "about", "")

    def _texto_url(self, qurl):
        return "" if self._es_url_vacia(qurl) else qurl.toString()

    def _actualizar_candado(self, qurl):
        esq = qurl.scheme()
        if esq == "https":
            self.accion_candado.setIcon(icono("lock", config.COLOR_OK, 16))
            self.accion_candado.setToolTip("Conexión segura")
        elif esq == "http":
            self.accion_candado.setIcon(icono("triangle-alert", config.COLOR_AVISO, 16))
            self.accion_candado.setToolTip("Conexión no segura")
        else:
            self.accion_candado.setIcon(icono("search", config.COLOR_TEXTO_SUAVE, 16))
            self.accion_candado.setToolTip("")

    def _actualizar_navegacion(self):
        """Activa/desactiva atrás y adelante según el historial de la pestaña."""
        v = self.pestana_actual()
        hist = v.history() if v is not None else None
        self.btn_atras.setEnabled(bool(hist and hist.canGoBack()))
        self.btn_adelante.setEnabled(bool(hist and hist.canGoForward()))

    def _poner_icono_recargar(self, cargando):
        if cargando:
            self.btn_recargar.setIcon(icono("x", config.COLOR_TEXTO, 18))
            self.btn_recargar.setToolTip("Detener (Esc)")
        else:
            self.btn_recargar.setIcon(icono("rotate-cw", config.COLOR_TEXTO, 18))
            self.btn_recargar.setToolTip("Recargar (F5)")

    def _on_icon_changed(self, ic):
        view = self.sender()
        idx = self.tabs.indexOf(view)
        if idx != -1:
            self.tabs.setTabIcon(idx, ic if not ic.isNull() else self._icono_pestana(view))

    def _icono_pestana(self, view):
        return icono("home" if self._es_url_vacia(view.url()) else "globe",
                     config.COLOR_TEXTO_SUAVE, 16)

    def _buscar_desde_inicio(self, texto):
        """El usuario buscó desde la página de inicio: lo tratamos como si lo
        hubiera escrito en la barra de direcciones."""
        view = self.sender().parent() if self.sender() is not None else None

        def hacer():
            if view is not None and self.tabs.indexOf(view) != -1:
                self.tabs.setCurrentWidget(view)
            self.barra.setText(texto)
            self.navegar()

        # Diferido: esta señal sale de dentro de acceptNavigationRequest y
        # navegar a otra página en pleno aviso de navegación cierra Qt de golpe.
        QTimer.singleShot(0, hacer)

    # ---------- ABRIR INCÓGNITO ----------

    def abrir_incognito(self):
        """Abre una nueva ventana en modo incógnito."""
        from ventana_incognito import VentanaIncognito

        app = QApplication.instance()
        if not hasattr(app, "_ventanas_incognito"):
            app._ventanas_incognito = []

        v = VentanaIncognito(self.gestor, self.prefs)
        app._ventanas_incognito.append(v)
        v.show()

    # ---------- DESCARGAS ----------

    def _descarga_solicitada(self, download):
        """Una web lanzó una descarga en el perfil de esta ventana."""
        nombre_sugerido = download.downloadFileName()
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar archivo como", nombre_sugerido
        )
        if not ruta:
            download.cancel()
            return

        download.setDownloadDirectory(os.path.dirname(ruta))
        download.setDownloadFileName(os.path.basename(ruta))
        download.accept()

        # self.descargas es el modelo real en la ventana normal y uno solo
        # en memoria en incógnito, así que aquí no hace falta distinguir.
        entrada = self.descargas.añadir(
            nombre=os.path.basename(ruta),
            ruta=ruta,
            url=url_a_texto(download.url()),
            tamano=download.totalBytes(),
            estado="en curso",
        )
        self._obtener_panel_descargas().añadir_descarga(download, entrada)
        self._notificar_descarga(nombre_sugerido, ruta)

    def _obtener_panel_descargas(self):
        # Sin ventana padre: así no se destruye si se cierra otra ventana.
        if self._panel_descargas is None:
            self._panel_descargas = VentanaDescargas(self.descargas)
        return self._panel_descargas

    def abrir_panel_descargas(self):
        panel = self._obtener_panel_descargas()
        panel.show()
        panel.raise_()
        panel.activateWindow()

    def _notificar_descarga(self, nombre, ruta):
        self.statusBar().showMessage(
            f"📥 Descargando: {nombre}  →  {ruta}", 5000
        )

    # ---------- MOTOR DE BÚSQUEDA ----------

    def _actualizar_icono_motor(self):
        motor = motores.obtener(self.motor_actual)
        self.btn_motor.setText(motor["icono"])
        self.btn_motor.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_motor.setToolTip(f"Motor: {motor['nombre']} (clic para cambiar)")

    def _mostrar_menu_motores(self):
        menu = QMenu(self)
        for clave, m in motores.MOTORES.items():
            texto = f"{m['icono']}  {m['nombre']}    ({m['bang']})"
            if clave == self.motor_actual:
                texto = "● " + texto
            accion = menu.addAction(texto)
            accion.triggered.connect(
                lambda _=False, c=clave: self._cambiar_motor(c, self._ctrl_pulsado())
            )

        menu.addSeparator()
        ayuda = menu.addAction("Clic: cambiar motor  ·  Ctrl+Clic: ir a la home")
        ayuda.setEnabled(False)

        pos = self.btn_motor.mapToGlobal(self.btn_motor.rect().bottomLeft())
        menu.exec(pos)

    def _cambiar_motor(self, clave, ir_a_home=False):
        self.motor_actual = clave
        self.prefs.set("motor_busqueda", clave)
        self._actualizar_icono_motor()

        if ir_a_home:
            motor = motores.obtener(clave)
            url_home = motor.get("url_home")
            if url_home:
                view = self.pestana_actual()
                if view:
                    view.setUrl(QUrl(url_home))

    # ---------- SUGERENCIAS ----------

    def _pedir_sugerencias(self, texto):
        texto = texto.strip()
        if not texto or texto.startswith("!"):
            self.modelo_sugerencias.setStringList([])
            return

        motor = motores.obtener(self.motor_actual)
        plantilla = motor.get("url_sugerencias")
        if not plantilla:
            self.modelo_sugerencias.setStringList([])
            return

        url = plantilla.format(q=quote(texto))

        if self.reply_sugerencias is not None:
            try:
                self.reply_sugerencias.abort()
            except Exception:
                pass

        peticion = QNetworkRequest(QUrl(url))
        self.reply_sugerencias = self.net.get(peticion)
        self.reply_sugerencias.finished.connect(self._on_sugerencias)

    def _on_sugerencias(self):
        reply = self.sender()
        if reply is None:
            return
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                self.modelo_sugerencias.setStringList([])
                return
            datos = bytes(reply.readAll()).decode("utf-8", errors="ignore")
        except Exception:
            return
        finally:
            reply.deleteLater()
            if self.reply_sugerencias is reply:
                self.reply_sugerencias = None

        sugerencias = self._parsear_sugerencias(datos)
        self.modelo_sugerencias.setStringList(sugerencias[:8])

    def _parsear_sugerencias(self, datos):
        try:
            data = json.loads(datos)
        except json.JSONDecodeError:
            return []

        if isinstance(data, list) and data and isinstance(data[0], dict):
            return [d.get("phrase", "") for d in data if d.get("phrase")]

        if isinstance(data, list) and len(data) >= 2 and isinstance(data[1], list):
            return [s for s in data[1] if isinstance(s, str)]

        return []

    # ---------- NAVEGACIÓN ----------

    def navegar(self):
        view = self.pestana_actual()
        if view is None:
            return

        texto = self.barra.text().strip()
        if not texto:
            return

        plantilla, consulta = motores.buscar_bang(texto)
        if plantilla:
            url = plantilla.format(q=quote(consulta))
            view.setUrl(QUrl(url))
            return

        if texto.startswith(("http://", "https://")):
            view.setUrl(QUrl(texto))
            return

        if "." in texto and " " not in texto:
            view.setUrl(QUrl("https://" + texto))
            return

        motor = motores.obtener(self.motor_actual)
        url = motor["url_busqueda"].format(q=quote(texto))
        view.setUrl(QUrl(url))

    def recargar_o_detener(self):
        view = self.pestana_actual()
        if view is None:
            return
        if self.progreso.isVisible() and self.progreso.value() < 100:
            view.stop()
        else:
            view.reload()

    def atras_actual(self):
        v = self.pestana_actual()
        if v:
            v.back()

    def adelante_actual(self):
        v = self.pestana_actual()
        if v:
            v.forward()

    def inicio_actual(self):
        """Muestra la página de inicio propia en la pestaña actual."""
        v = self.pestana_actual()
        if v:
            v.setHtml(self._html_inicio())
            v.setFocus()

    def enfocar_barra(self):
        self.barra.setFocus()
        self.barra.selectAll()

    # ---------- ESCUDO ----------

    def id_pestana_activa(self):
        v = self.pestana_actual()
        return id(v) if v else None

    def id_pestana_de(self, qurl):
        """Id de la pestaña que está mostrando esa URL (la 'first party' de
        una petición). Si ninguna coincide, devolvemos la activa."""
        def sin_fragmento(u):
            return u.adjusted(QUrl.UrlFormattingOption.RemoveFragment).toString()

        objetivo = sin_fragmento(qurl)
        activa = self.pestana_actual()
        # Primero la activa, luego las demás.
        orden = [activa] if activa is not None else []
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if w is not activa:
                orden.append(w)
        for v in orden:
            if sin_fragmento(v.url()) == objetivo:
                return id(v)
        return id(activa) if activa is not None else None

    def actualizar_escudo_pronto(self):
        """Pide refrescar el escudo; si ya hay uno pendiente, no hace nada."""
        if not self._timer_escudo.isActive():
            self._timer_escudo.start()

    def actualizar_escudo(self):
        if self.interceptor_actual is None:
            return
        pid = self.id_pestana_activa()
        if pid is None:
            return
        c = self.interceptor_actual.contador_actual(pid)
        activo = c["total"] > 0
        self.btn_escudo.setText(f" {c['total']}")
        self.btn_escudo.setIcon(icono(
            "shield", config.COLOR_OK if activo else config.COLOR_TEXTO_SUAVE, 16))
        self.btn_escudo.setObjectName("escudo_activo" if activo else "escudo_inactivo")
        self.btn_escudo.style().unpolish(self.btn_escudo)
        self.btn_escudo.style().polish(self.btn_escudo)

    def _mostrar_menu_escudo(self):
        view = self.pestana_actual()
        if view is None:
            return
        pid = self.id_pestana_activa()
        c = (self.interceptor_actual.contador_actual(pid)
             if self.interceptor_actual else {"total": 0, "por_tipo": {}})

        menu = QMenu(self)
        a = menu.addAction(f"Bloqueados: {c['total']}")
        a.setEnabled(False)
        menu.addSeparator()

        tipos = c.get("por_tipo", {})
        if tipos:
            nombres = {
                "script": "Scripts", "image": "Imágenes",
                "stylesheet": "Estilos", "subdocument": "Iframes",
                "document": "Páginas", "xhr": "XHR", "media": "Medios",
                "font": "Fuentes", "ping": "Pings", "object": "Objetos",
                "other": "Otros",
            }
            for tipo, cantidad in sorted(tipos.items(), key=lambda x: -x[1]):
                acc = menu.addAction(f"{nombres.get(tipo, tipo.capitalize())}: {cantidad}")
                acc.setEnabled(False)
        else:
            acc = menu.addAction("(Sin bloqueos en esta página)")
            acc.setEnabled(False)

        menu.addSeparator()
        host = urlparse(view.url().toString()).hostname or ""
        if host:
            if self.gestor.esta_en_whitelist(host):
                acc = menu.addAction(f"✅ Bloqueo desactivado en {host}")
                acc.setEnabled(False)
                acc2 = menu.addAction("Reactivar bloqueo en este sitio")
                acc2.triggered.connect(lambda: self._quitar_whitelist(host))
            else:
                acc = menu.addAction(f"Desactivar bloqueo en {host}")
                acc.triggered.connect(lambda: self._añadir_whitelist(host))

        menu.addSeparator()
        acc = menu.addAction("Recargar reglas de bloqueo")
        acc.triggered.connect(self._recargar_reglas)

        pos = self.btn_escudo.mapToGlobal(self.btn_escudo.rect().bottomLeft())
        menu.exec(pos)

    def _añadir_whitelist(self, host):
        self.gestor.añadir_a_whitelist(host)
        self.actualizar_escudo()

    def _quitar_whitelist(self, host):
        self.gestor.quitar_de_whitelist(host)
        self.actualizar_escudo()

    def _recargar_reglas(self):
        self.gestor.cargar_listas()
        self.actualizar_escudo()

    # ---------- FAVORITOS ----------

    def _toggle_favorito(self):
        view = self.pestana_actual()
        if view is None:
            return
        url = url_a_texto(view.url())
        if not url or url.startswith(("about:", "data:", "file:")):
            return
        if self.favoritos.existe(url):
            self.favoritos.eliminar(url)
        else:
            titulo = view.title() or url
            nuevo, ok = QInputDialog.getText(
                self, "Añadir a favoritos", "Nombre:", text=titulo
            )
            if ok and nuevo.strip():
                self.favoritos.añadir(nuevo.strip(), url)
        self._refrescar_favoritos()

    def _refrescar_favoritos(self):
        self._actualizar_estrella()
        self._refrescar_barra_favoritos()

    def _actualizar_estrella(self):
        view = self.pestana_actual()
        if view is None:
            return
        if self.es_incognito:
            self.accion_estrella.setIcon(icono("star", config.COLOR_TEXTO_SUAVE, 18))
            self.accion_estrella.setToolTip("Favoritos no disponibles en incógnito")
            return
        url = url_a_texto(view.url())
        if self.favoritos.existe(url):
            self.accion_estrella.setIcon(icono("star-filled", config.COLOR_AVISO, 18))
            self.accion_estrella.setToolTip("Quitar de favoritos (Ctrl+D)")
        else:
            self.accion_estrella.setIcon(icono("star", config.COLOR_TEXTO_SUAVE, 18))
            self.accion_estrella.setToolTip("Añadir a favoritos (Ctrl+D)")

    def _refrescar_barra_favoritos(self):
        self.barra_fav.clear()
        if self.es_incognito:
            lbl = QPushButton("Modo incógnito: sin favoritos")
            lbl.setEnabled(False)
            self.barra_fav.addWidget(lbl)
            return
        favoritos = self.favoritos.todos()
        if not favoritos:
            lbl = QPushButton("Sin favoritos: pulsa la estrella o Ctrl+D")
            lbl.setEnabled(False)
            self.barra_fav.addWidget(lbl)
            return
        for f in favoritos:
            titulo = f.get("titulo", f.get("url", ""))
            corto = titulo if len(titulo) <= 22 else titulo[:21] + "…"
            url = f.get("url", "")
            btn = QPushButton(corto)
            btn.setToolTip(url)
            btn.clicked.connect(lambda _=False, u=url: self._abrir_en_actual(u))
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                lambda pos, u=url, b=btn: self._menu_contextual_favorito(u, b, pos)
            )
            self.barra_fav.addWidget(btn)

    def _menu_contextual_favorito(self, url, boton, pos):
        menu = QMenu(self)
        acc = menu.addAction("Abrir en pestaña actual")
        acc.triggered.connect(lambda: self._abrir_en_actual(url))
        acc = menu.addAction("Abrir en pestaña nueva")
        acc.triggered.connect(lambda: self.nueva_pestana(url))
        menu.addSeparator()
        acc = menu.addAction("Renombrar…")
        acc.triggered.connect(lambda: self._renombrar_favorito(url))
        acc = menu.addAction("Eliminar")
        acc.triggered.connect(lambda: self._eliminar_favorito(url))
        menu.exec(boton.mapToGlobal(pos))

    def _renombrar_favorito(self, url):
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
            self._refrescar_favoritos()

    def _eliminar_favorito(self, url):
        self.favoritos.eliminar(url)
        self._refrescar_favoritos()

    def _abrir_ventana_favoritos(self):
        dlg = VentanaFavoritos(self.favoritos, self)
        if dlg.exec() and dlg.url_seleccionada:
            self._abrir_en_actual(dlg.url_seleccionada)
        self._refrescar_favoritos()

    # ---------- HISTORIAL ----------

    def _mostrar_menu_historial(self):
        menu = QMenu(self)
        recientes = self.historial.recientes(20)
        if not recientes:
            a = menu.addAction("(Sin historial)")
            a.setEnabled(False)
        else:
            for e in recientes:
                titulo = e.get("titulo", e.get("url", ""))
                corto = titulo if len(titulo) <= 60 else titulo[:57] + "…"
                a = menu.addAction(corto)
                a.setToolTip(e.get("url", ""))
                a.triggered.connect(
                    lambda _=False, url=e.get("url", ""): self._abrir_en_actual(url)
                )
        menu.addSeparator()
        a = menu.addAction("Ver todo el historial…")
        a.triggered.connect(self._abrir_ventana_historial)
        if not self.es_incognito:
            a = menu.addAction("Borrar historial")
            a.triggered.connect(lambda: self.historial.borrar_todo())
        pos = self.btn_historial.mapToGlobal(self.btn_historial.rect().bottomLeft())
        menu.exec(pos)

    def _abrir_en_actual(self, url):
        v = self.pestana_actual()
        if v and url:
            v.setUrl(QUrl(url))

    def _abrir_ventana_historial(self):
        dlg = VentanaHistorial(self.historial, self)
        if dlg.exec() and dlg.url_seleccionada:
            self._abrir_en_actual(dlg.url_seleccionada)

    def closeEvent(self, event):
        # Quitar el filtro de teclas de esta ventana y cerrar su panel
        # (si se quedara abierto, la aplicación no terminaría).
        self.vim.desinstalar()
        if self._panel_descargas is not None:
            self._panel_descargas.close()
        if not self.es_incognito:
            self.historial.guardar()
            self.favoritos.guardar()
            self.descargas.guardar()
            self.prefs.guardar()
        super().closeEvent(event)

    # ---------- PESTAÑAS ----------

    def pestana_actual(self):
        return self.tabs.currentWidget()

    def nueva_pestana(self, url=None):
        view = QWebEngineView()

        perfil = (self.perfil_web if self.perfil_web is not None
                  else QWebEngineProfile.defaultProfile())

        page = PaginaVim(perfil, view)
        page.busqueda_pedida.connect(self._buscar_desde_inicio)
        view.setPage(page)

        view.urlChanged.connect(self._on_url_changed)
        view.titleChanged.connect(self._on_title_changed)
        view.iconChanged.connect(self._on_icon_changed)
        view.loadStarted.connect(self._on_load_started)
        view.loadProgress.connect(self._on_load_progress)
        view.loadFinished.connect(self._on_load_finished)

        if self.interceptor_actual is not None:
            self.interceptor_actual.registrar_pestana(id(view))

        idx = self.tabs.addTab(view, "Nueva pestaña")
        self.tabs.setTabIcon(idx, icono("home", config.COLOR_TEXTO_SUAVE, 16))
        self.tabs.setCurrentIndex(idx)
        if url:
            view.setUrl(QUrl(url))
        else:
            view.setHtml(self._html_inicio())
            view.setFocus()
        return view

    def cerrar_pestana(self, idx):
        widget = self.tabs.widget(idx)
        if widget is not None and self.interceptor_actual is not None:
            self.interceptor_actual.olvidar_pestana(id(widget))
        self.tabs.removeTab(idx)
        if widget is not None:
            widget.deleteLater()
        if self.tabs.count() == 0:
            self.close()

    def cerrar_pestana_actual(self):
        idx = self.tabs.currentIndex()
        if idx != -1:
            self.cerrar_pestana(idx)

    def cambio_de_pestana(self, idx):
        view = self.tabs.widget(idx)
        if view is None:
            return
        self.barra.setText(self._texto_url(view.url()))
        self._actualizar_candado(view.url())
        titulo = view.title() or "Nueva pestaña"
        self.setWindowTitle(f"{titulo} — {config.NOMBRE}")
        self.progreso.hide()
        self._poner_icono_recargar(False)
        self._actualizar_estrella()
        self._actualizar_navegacion()
        self.actualizar_escudo()

    # ---------- SEÑALES ----------

    def _es_actual(self):
        return self.sender() is self.pestana_actual()

    def _on_url_changed(self, qurl):
        if self._es_actual():
            self.barra.setText(self._texto_url(qurl))
            self._actualizar_candado(qurl)
            self._actualizar_estrella()
            self._actualizar_navegacion()

    def _on_title_changed(self, titulo):
        view = self.sender()
        idx = self.tabs.indexOf(view)
        if idx != -1:
            corto = titulo if len(titulo) <= 22 else titulo[:21] + "…"
            self.tabs.setTabText(idx, corto or "Nueva pestaña")
            self.tabs.setTabToolTip(idx, titulo)
        if self._es_actual():
            self.setWindowTitle(f"{titulo} — {config.NOMBRE}")

    def _on_load_started(self):
        if self._es_actual():
            self.progreso.setValue(0)
            self.progreso.show()
            self._poner_icono_recargar(True)

    def _on_load_progress(self, valor):
        if self._es_actual():
            self.progreso.setValue(valor)

    def _on_load_finished(self, ok):
        # Sin favicon propio: icono genérico (no dejar el de la página anterior).
        origen = self.sender()
        if isinstance(origen, QWebEngineView) and origen.icon().isNull():
            idx = self.tabs.indexOf(origen)
            if idx != -1:
                self.tabs.setTabIcon(idx, self._icono_pestana(origen))
        if self._es_actual():
            self.progreso.hide()
            self._poner_icono_recargar(False)
            self._actualizar_estrella()
            self._actualizar_navegacion()
            self.actualizar_escudo()

        if ok and not self.es_incognito:
            view = self.sender()
            # La página de inicio propia (data:) no es historial.
            if isinstance(view, QWebEngineView) and not self._es_url_vacia(view.url()):
                self.historial.añadir(view.title(), url_a_texto(view.url()))

    # ---------- TECLADO ----------

    def _ctrl_pulsado(self):
        """True si Ctrl está pulsado ahora mismo (aunque el foco esté en la web)."""
        mods = QApplication.keyboardModifiers()
        return bool(mods & Qt.KeyboardModifier.ControlModifier)

    # ---------- ATAJOS ----------

    def _crear_atajos(self):
        atajos = [
            ("Ctrl+L", self.enfocar_barra),
            ("Ctrl+K", self.enfocar_barra),
            ("Ctrl+T", lambda: self.nueva_pestana()),
            ("Ctrl+W", self.cerrar_pestana_actual),
            ("Ctrl+Shift+N", self.abrir_incognito),
            ("Ctrl+J", self.abrir_panel_descargas),
            ("Ctrl+Tab", self.siguiente_pestana),
            ("Ctrl+Shift+Tab", self.pestana_anterior),
            ("Ctrl+H", self._abrir_ventana_historial),
            ("Ctrl+D", self._toggle_favorito),
            ("Ctrl+Shift+O", self._abrir_ventana_favoritos),
            ("F5", self.recargar_o_detener),
            ("Ctrl+R", self.recargar_o_detener),
            ("Esc", self.detener_actual),
            ("Alt+Left", self.atras_actual),
            ("Alt+Right", self.adelante_actual),
            ("Alt+Home", self.inicio_actual),
        ]
        for sec, fn in atajos:
            acc = QAction(self)
            acc.setShortcut(QKeySequence(sec))
            acc.triggered.connect(fn)
            self.addAction(acc)

        self.accion_ver_fav = QAction(self)
        self.accion_ver_fav.setCheckable(True)
        self.accion_ver_fav.setChecked(
            self.prefs.get("mostrar_barra_favoritos", True)
        )
        self.accion_ver_fav.setShortcut(QKeySequence("Ctrl+Shift+B"))
        self.accion_ver_fav.toggled.connect(self._toggle_barra_favoritos)
        self.addAction(self.accion_ver_fav)
        self.barra_fav.setVisible(self.accion_ver_fav.isChecked())

    def _toggle_barra_favoritos(self, visible):
        self.barra_fav.setVisible(visible)
        self.prefs.set("mostrar_barra_favoritos", visible)

    def siguiente_pestana(self):
        n = self.tabs.count()
        if n > 1:
            self.tabs.setCurrentIndex((self.tabs.currentIndex() + 1) % n)

    def pestana_anterior(self):
        n = self.tabs.count()
        if n > 1:
            self.tabs.setCurrentIndex((self.tabs.currentIndex() - 1) % n)

    def detener_actual(self):
        v = self.pestana_actual()
        if v:
            v.stop()
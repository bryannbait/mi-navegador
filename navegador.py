# navegador.py
# Clase MiNavegador y helpers. Importar desde main.py o ventana_incognito.py.

import os
import json
from urllib.parse import quote, urlparse

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLineEdit, QToolBar, QPushButton,
    QProgressBar, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QMenu, QInputDialog, QCompleter, QFileDialog, QLabel
)
from PyQt6.QtCore import QUrl, Qt, QStringListModel, QSize
from PyQt6.QtGui import QAction, QKeySequence, QIcon
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings

from bloqueador import Bloqueador
from historial import Historial
from ventana_historial import VentanaHistorial
from favoritos import Favoritos
from ventana_favoritos import VentanaFavoritos
from descargas import Descargas
from ventana_descargas import VentanaDescargas
from atajos_vim import VimKeys
from puente_vim import PaginaVim, crear_script_vim
import motores
import config
from assets.icons.helpers import icono


# ---------- VARIABLES GLOBALES ----------

gestor_bloqueo = None
interceptor = None
ventana_descargas_global = None


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

    # Descargas.
    perfil.downloadRequested.connect(_on_download_requested)

    ajustes = perfil.settings()
    ajustes.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
    ajustes.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
    ajustes.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
    return perfil


def _on_download_requested(download):
    """Se llama cuando una web lanza una descarga."""
    nombre_sugerido = download.downloadFileName()
    ruta, _ = QFileDialog.getSaveFileName(
        None, "Guardar archivo como", nombre_sugerido
    )
    if not ruta:
        download.cancel()
        return

    download.setDownloadDirectory(os.path.dirname(ruta))
    download.setDownloadFileName(os.path.basename(ruta))
    download.accept()

    # Registrar en el modelo compartido de descargas.
    app = QApplication.instance()
    gestor_desc = getattr(app, "_gestor_descargas_global", None)
    if gestor_desc is not None:
        entrada = gestor_desc.añadir(
            nombre=os.path.basename(ruta),
            ruta=ruta,
            url=download.url().toString(),
            tamano=download.totalBytes(),
            estado="en curso",
        )
        # Avisar al panel si está abierto.
        if ventana_descargas_global is not None:
            ventana_descargas_global.añadir_descarga(download, entrada)

    # Avisar a todas las ventanas.
    for v in getattr(app, "_ventanas_navegador", []):
        v._notificar_descarga(nombre_sugerido, ruta)


def hoja_de_estilos():
    return f"""
    QMainWindow {{ background-color: {config.COLOR_FONDO}; }}

    QToolBar {{
        background-color: {config.COLOR_TOOLBAR};
        border: none;
        padding: 6px;
        spacing: 4px;
    }}
    QToolBar#barra_favoritos {{
        background-color: {config.COLOR_FONDO};
        border-bottom: 1px solid {config.COLOR_TOOLBAR};
        padding: 3px 6px;
        spacing: 2px;
    }}
    QToolBar#barra_favoritos QPushButton {{
        padding: 3px 8px;
        font-size: 12px;
        border-radius: 4px;
    }}

    QPushButton {{
        background-color: transparent;
        color: {config.COLOR_TEXTO};
        border: none;
        border-radius: 6px;
        padding: 4px 6px;
        font-size: 13px;
        min-width: 28px;
    }}
    QPushButton:hover {{ background-color: {config.COLOR_BOTON_HOVER}; }}
    QPushButton:pressed {{
        background-color: {config.COLOR_ACENTO};
        color: {config.COLOR_FONDO};
    }}

    QPushButton#escudo_activo {{ color: #a6e3a1; }}
    QPushButton#escudo_inactivo {{ color: #f38ba8; }}

    QPushButton#btn_motor {{
        font-size: 16px;
        padding: 4px 8px;
        border-radius: 8px;
        min-width: 0px;
    }}

    QLineEdit {{
        background-color: {config.COLOR_BARRA_FONDO};
        color: {config.COLOR_BARRA_TEXTO};
        border: 1px solid transparent;
        border-radius: 12px;
        padding: 6px 12px;
        font-size: 13px;
        selection-background-color: {config.COLOR_ACENTO};
        selection-color: {config.COLOR_FONDO};
    }}
    QLineEdit:focus {{ border: 1px solid {config.COLOR_ACENTO}; }}

    QProgressBar {{
        background-color: {config.COLOR_TOOLBAR};
        border: none;
        height: 3px;
    }}
    QProgressBar::chunk {{ background-color: {config.COLOR_ACENTO}; }}

    QTabWidget::pane {{
        border: none;
        background-color: {config.COLOR_FONDO};
    }}
    QTabBar {{ background-color: {config.COLOR_TOOLBAR}; }}
    QTabBar::tab {{
        background-color: {config.COLOR_TOOLBAR};
        color: {config.COLOR_TEXTO};
        padding: 8px 14px;
        margin-right: 2px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        min-width: 100px;
        max-width: 220px;
        font-size: 12px;
    }}
    QTabBar::tab:selected {{
        background-color: {config.COLOR_BARRA_FONDO};
        color: {config.COLOR_ACENTO};
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {config.COLOR_BOTON_HOVER};
    }}

    QMenu {{
        background-color: {config.COLOR_TOOLBAR};
        color: {config.COLOR_TEXTO};
        border: 1px solid {config.COLOR_BOTON_HOVER};
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 24px 6px 12px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {config.COLOR_ACENTO};
        color: {config.COLOR_FONDO};
    }}
    QMenu::item:disabled {{ color: #6c7086; }}
    QMenu::separator {{
        height: 1px;
        background-color: {config.COLOR_BOTON_HOVER};
        margin: 4px 8px;
    }}

    QDialog {{
        background-color: {config.COLOR_FONDO};
        color: {config.COLOR_TEXTO};
    }}
    QLabel {{ color: {config.COLOR_TEXTO}; }}
    QListWidget {{
        background-color: {config.COLOR_BARRA_FONDO};
        color: {config.COLOR_BARRA_TEXTO};
        border: none;
        border-radius: 8px;
        padding: 4px;
    }}
    QListWidget::item {{
        padding: 6px 8px;
        border-radius: 4px;
    }}
    QListWidget::item:selected {{
        background-color: {config.COLOR_ACENTO};
        color: {config.COLOR_FONDO};
    }}

    QCompleter QAbstractItemView {{
        background-color: {config.COLOR_TOOLBAR};
        color: {config.COLOR_TEXTO};
        border: 1px solid {config.COLOR_BOTON_HOVER};
        selection-background-color: {config.COLOR_ACENTO};
        selection-color: {config.COLOR_FONDO};
        padding: 4px;
        outline: none;
    }}
    """


# ---------- VENTANA PRINCIPAL ----------

class MiNavegador(QMainWindow):

    def __init__(self, gestor, prefs, historial, favoritos, descargas,
                 perfil_web=None, interceptor_propio=None, es_incognito=False):
        super().__init__()

        self.gestor = gestor
        self.prefs = prefs

        # Modelos compartidos
        self.historial = historial
        self.favoritos = favoritos
        self.descargas = descargas

        # Modo incógnito
        self.es_incognito = es_incognito
        self.perfil_web = perfil_web
        self.interceptor_actual = (
            interceptor_propio if interceptor_propio is not None else interceptor
        )

        self.motor_actual = prefs.get(
            "motor_busqueda", motores.motor_por_defecto()
        )

        self.setWindowTitle(f"{config.NOMBRE} {config.VERSION}")
        self.resize(1200, 800)

        # Red para sugerencias
        self.net = QNetworkAccessManager(self)
        self.reply_sugerencias = None

        # --- Barra de direcciones y candado ---
        self.barra = QLineEdit()
        self.barra.setPlaceholderText("Busca o escribe una dirección... (!g, !w para atajos)")
        self.barra.returnPressed.connect(self.navegar)
        self.barra.textEdited.connect(self._pedir_sugerencias)

        self.lbl_candado = QLabel("🔒")
        self.lbl_candado.setToolTip("Conexión segura")
        self.lbl_candado.setStyleSheet("QLabel { color: #a6e3a1; padding: 0 4px 0 8px; font-size: 14px; }")

        # Autocompletado
        self.modelo_sugerencias = QStringListModel([], self)
        self.completer = QCompleter(self.modelo_sugerencias, self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.barra.setCompleter(self.completer)

        # --- Barra de herramientas ---
        toolbar = QToolBar("Navegación")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Atrás
        self.btn_atras = QPushButton()
        self.btn_atras.setIcon(icono("arrow-left"))
        self.btn_atras.setIconSize(QSize(18, 18))
        self.btn_atras.setToolTip("Atrás (Alt+←)")
        self.btn_atras.clicked.connect(self.atras_actual)
        toolbar.addWidget(self.btn_atras)

        # Adelante
        self.btn_adelante = QPushButton()
        self.btn_adelante.setIcon(icono("arrow-right"))
        self.btn_adelante.setIconSize(QSize(18, 18))
        self.btn_adelante.setToolTip("Adelante (Alt+→)")
        self.btn_adelante.clicked.connect(self.adelante_actual)
        toolbar.addWidget(self.btn_adelante)

        # Recargar
        self.btn_recargar = QPushButton()
        self.btn_recargar.setIcon(icono("rotate-cw"))
        self.btn_recargar.setIconSize(QSize(18, 18))
        self.btn_recargar.setToolTip("Recargar (F5)")
        self.btn_recargar.clicked.connect(self.recargar_o_detener)
        toolbar.addWidget(self.btn_recargar)

        # Inicio
        btn_inicio = QPushButton()
        btn_inicio.setIcon(icono("home"))
        btn_inicio.setIconSize(QSize(18, 18))
        btn_inicio.setToolTip("Inicio (Alt+Inicio)")
        btn_inicio.clicked.connect(self.inicio_actual)
        toolbar.addWidget(btn_inicio)

        # Motor (con emoji)
        self.btn_motor = QPushButton()
        self.btn_motor.setObjectName("btn_motor")
        self.btn_motor.setToolTip("Elegir motor de búsqueda")
        self.btn_motor.clicked.connect(self._mostrar_menu_motores)
        toolbar.addWidget(self.btn_motor)
        self._actualizar_icono_motor()

        # Contenedor candado + barra
        contenedor_barra = QWidget()
        layout_barra = QHBoxLayout(contenedor_barra)
        layout_barra.setContentsMargins(0, 0, 0, 0)
        layout_barra.setSpacing(0)
        layout_barra.addWidget(self.lbl_candado)
        layout_barra.addWidget(self.barra)
        toolbar.addWidget(contenedor_barra)

        # Escudo
        self.btn_escudo = QPushButton()
        self.btn_escudo.setIcon(icono("shield", color="#a6e3a1"))
        self.btn_escudo.setIconSize(QSize(18, 18))
        self.btn_escudo.setText(" 0")
        self.btn_escudo.setToolTip("Bloqueador de anuncios")
        self.btn_escudo.clicked.connect(self._mostrar_menu_escudo)
        self.btn_escudo.setObjectName("escudo_activo")
        toolbar.addWidget(self.btn_escudo)

        # Estrella
        self.btn_estrella = QPushButton()
        self.btn_estrella.setIcon(icono("star"))
        self.btn_estrella.setIconSize(QSize(18, 18))
        self.btn_estrella.setToolTip("Añadir a favoritos (Ctrl+D)")
        self.btn_estrella.clicked.connect(self._toggle_favorito)
        toolbar.addWidget(self.btn_estrella)

        # Marcadores
        btn_fav = QPushButton()
        btn_fav.setIcon(icono("bookmark"))
        btn_fav.setIconSize(QSize(18, 18))
        btn_fav.setToolTip("Gestionar favoritos (Ctrl+Shift+O)")
        btn_fav.clicked.connect(self._abrir_ventana_favoritos)
        toolbar.addWidget(btn_fav)

        # Historial
        self.btn_historial = QPushButton()
        self.btn_historial.setIcon(icono("clock"))
        self.btn_historial.setIconSize(QSize(18, 18))
        self.btn_historial.setToolTip("Historial")
        self.btn_historial.clicked.connect(self._mostrar_menu_historial)
        toolbar.addWidget(self.btn_historial)

        # Incógnito
        btn_inc = QPushButton()
        btn_inc.setIcon(icono("eye-off"))
        btn_inc.setIconSize(QSize(18, 18))
        btn_inc.setToolTip("Nueva ventana de incógnito (Ctrl+Shift+N)")
        btn_inc.clicked.connect(self.abrir_incognito)
        toolbar.addWidget(btn_inc)

        # Descargas
        btn_desc = QPushButton()
        btn_desc.setIcon(icono("download"))
        btn_desc.setIconSize(QSize(18, 18))
        btn_desc.setToolTip("Descargas (Ctrl+J)")
        btn_desc.clicked.connect(self.abrir_panel_descargas)
        toolbar.addWidget(btn_desc)

        # --- Barra de marcadores ---
        self.addToolBarBreak()
        self.barra_fav = QToolBar("Favoritos")
        self.barra_fav.setObjectName("barra_favoritos")
        self.barra_fav.setMovable(False)
        self.addToolBar(self.barra_fav)

        # --- Pestañas ---
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.setElideMode(Qt.TextElideMode.ElideRight)
        self.tabs.tabCloseRequested.connect(self.cerrar_pestana)
        self.tabs.currentChanged.connect(self.cambio_de_pestana)

        btn_nueva = QPushButton("+")
        btn_nueva.setToolTip("Nueva pestaña (Ctrl+T)")
        btn_nueva.clicked.connect(lambda: self.nueva_pestana())
        self.tabs.setCornerWidget(btn_nueva, Qt.Corner.TopRightCorner)

        # --- Progreso ---
        self.progreso = QProgressBar()
        self.progreso.setTextVisible(False)
        self.progreso.setFixedHeight(3)
        self.progreso.hide()

        # --- Layout ---
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.progreso)
        layout.addWidget(self.tabs)
        self.setCentralWidget(contenedor)

        if self.interceptor_actual is not None and not self.es_incognito:
            self.interceptor_actual.navegador = self

        self._ctrl_pulsado = False
        self.vim = VimKeys(self)

        self._crear_atajos()
        self._refrescar_barra_favoritos()
        self.nueva_pestana()

    # ---------- ABRIR INCÓGNITO ----------

    def abrir_incognito(self):
        from ventana_incognito import VentanaIncognito
        app = QApplication.instance()
        if not hasattr(app, "_ventanas_incognito"):
            app._ventanas_incognito = []
        v = VentanaIncognito(self.gestor, self.prefs, self.historial, self.favoritos, self.descargas)
        app._ventanas_incognito.append(v)
        v.show()

    # ---------- DESCARGA ----------

    def _notificar_descarga(self, nombre, ruta):
        try:
            self.statusBar().showMessage(f"📥 Descargando: {nombre}  →  {ruta}", 5000)
        except Exception:
            pass

    def abrir_panel_descargas(self):
        global ventana_descargas_global
        if ventana_descargas_global is None:
            ventana_descargas_global = VentanaDescargas(self.descargas, self)
        ventana_descargas_global.show()
        ventana_descargas_global.raise_()
        ventana_descargas_global.activateWindow()

    # ---------- MOTOR DE BÚSQUEDA ----------

    def _actualizar_icono_motor(self):
        motor = motores.obtener(self.motor_actual)
        self.btn_motor.setText(motor["icono"])
        self.btn_motor.setToolTip(f"Motor: {motor['nombre']} (clic para cambiar)")

    def _mostrar_menu_motores(self):
        menu = QMenu(self)
        for clave, m in motores.MOTORES.items():
            texto = f"{m['icono']}  {m['nombre']}    ({m['bang']})"
            if clave == self.motor_actual:
                texto = "● " + texto
            accion = menu.addAction(texto)
            accion.triggered.connect(lambda _=False, c=clave: self._cambiar_motor(c, self._ctrl_pulsado))

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
            try: self.reply_sugerencias.abort()
            except Exception: pass
        peticion = QNetworkRequest(QUrl(url))
        self.reply_sugerencias = self.net.get(peticion)
        self.reply_sugerencias.finished.connect(self._on_sugerencias)

    def _on_sugerencias(self):
        reply = self.sender()
        if reply is None: return
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
        if view is None: return
        texto = self.barra.text().strip()
        if not texto: return

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
        if view is None: return
        if self.progreso.isVisible() and self.progreso.value() < 100:
            view.stop()
        else:
            view.reload()

    def atras_actual(self):
        v = self.pestana_actual()
        if v: v.back()

    def adelante_actual(self):
        v = self.pestana_actual()
        if v: v.forward()

    def inicio_actual(self):
        v = self.pestana_actual()
        if v: v.setUrl(QUrl(config.HOME))

    def enfocar_barra(self):
        self.barra.setFocus()
        self.barra.selectAll()

    # ---------- CANDADO HTTPS ----------

    def _actualizar_candado(self, qurl):
        esquema = qurl.scheme().lower()
        if esquema == "https":
            self.lbl_candado.setText("🔒")
            self.lbl_candado.setToolTip("Conexión segura (HTTPS)")
            self.lbl_candado.setStyleSheet("QLabel { color: #a6e3a1; padding: 0 4px 0 8px; font-size: 14px; }")
        elif esquema == "http":
            self.lbl_candado.setText("⚠️")
            self.lbl_candado.setToolTip("Conexión NO segura (HTTP)")
            self.lbl_candado.setStyleSheet("QLabel { color: #f9e2af; padding: 0 4px 0 8px; font-size: 14px; }")
        else:
            self.lbl_candado.setText("")
            self.lbl_candado.setToolTip("")

    # ---------- ESCUDO ----------

    def id_pestana_activa(self):
        v = self.pestana_actual()
        return id(v) if v else None

    def actualizar_escudo(self):
        if self.interceptor_actual is None: return
        pid = self.id_pestana_activa()
        if pid is None: return
        c = self.interceptor_actual.contador_actual(pid)
        total = c["total"]
        self.btn_escudo.setText(f" {total}")

        if total > 0:
            self.btn_escudo.setIcon(icono("shield", color="#a6e3a1"))
            self.btn_escudo.setObjectName("escudo_activo")
        else:
            self.btn_escudo.setIcon(icono("shield", color="#6c7086"))
            self.btn_escudo.setObjectName("escudo_inactivo")

        self.btn_escudo.style().unpolish(self.btn_escudo)
        self.btn_escudo.style().polish(self.btn_escudo)

    def _mostrar_menu_escudo(self):
        view = self.pestana_actual()
        if view is None: return
        pid = self.id_pestana_activa()
        c = (self.interceptor_actual.contador_actual(pid) if self.interceptor_actual else {"total": 0, "por_tipo": {}})

        menu = QMenu(self)
        a = menu.addAction(f"Bloqueados: {c['total']}")
        a.setEnabled(False)
        menu.addSeparator()

        tipos = c.get("por_tipo", {})
        if tipos:
            nombres = {"script": "Scripts", "image": "Imágenes", "stylesheet": "Estilos", "subframe": "Iframes", "xhr": "XHR", "media": "Medios", "font": "Fuentes", "other": "Otros"}
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
        if view is None: return
        url = view.url().toString()
        if not url or url.startswith(("about:", "data:", "file:")): return
        if self.favoritos.existe(url):
            self.favoritos.eliminar(url)
        else:
            titulo = view.title() or url
            nuevo, ok = QInputDialog.getText(self, "Añadir a favoritos", "Nombre:", text=titulo)
            if ok and nuevo.strip():
                self.favoritos.añadir(nuevo.strip(), url)
        self._refrescar_favoritos()

    def _refrescar_favoritos(self):
        self._actualizar_estrella()
        self._refrescar_barra_favoritos()

    def _actualizar_estrella(self):
        view = self.pestana_actual()
        if view is None: return
        if self.es_incognito:
            self.btn_estrella.setIcon(icono("star"))
            self.btn_estrella.setToolTip("Favoritos no disponibles en incógnito")
            return
        url = view.url().toString()
        if self.favoritos.existe(url):
            self.btn_estrella.setIcon(icono("star", color="#f9e2af"))
            self.btn_estrella.setToolTip("Quitar de favoritos (Ctrl+D)")
        else:
            self.btn_estrella.setIcon(icono("star"))
            self.btn_estrella.setToolTip("Añadir a favoritos (Ctrl+D)")

    def _refrescar_barra_favoritos(self):
        self.barra_fav.clear()
        if self.es_incognito:
            lbl = QPushButton("(Modo incógnito: sin favoritos)")
            lbl.setEnabled(False)
            self.barra_fav.addWidget(lbl)
            return
        favoritos = self.favoritos.todos()
        if not favoritos:
            lbl = QPushButton("(Sin favoritos — pulsa ☆ o Ctrl+D)")
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
            btn.customContextMenuRequested.connect(lambda pos, u=url, b=btn: self._menu_contextual_favorito(u, b, pos))
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
        nuevo, ok = QInputDialog.getText(self, "Renombrar favorito", "Nuevo nombre:", text=actual)
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
                a.triggered.connect(lambda _=False, url=e.get("url", ""): self._abrir_en_actual(url))
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
        if v and url: v.setUrl(QUrl(url))

    def _abrir_ventana_historial(self):
        dlg = VentanaHistorial(self.historial, self)
        if dlg.exec() and dlg.url_seleccionada:
            self._abrir_en_actual(dlg.url_seleccionada)

    def closeEvent(self, event):
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
        perfil = (self.perfil_web if self.perfil_web is not None else QWebEngineProfile.defaultProfile())
        page = PaginaVim(perfil, view)
        view.setPage(page)

        view.urlChanged.connect(self._on_url_changed)
        view.titleChanged.connect(self._on_title_changed)
        view.iconUrlChanged.connect(self._on_icon_changed)
        view.loadStarted.connect(self._on_load_started)
        view.loadProgress.connect(self._on_load_progress)
        view.loadFinished.connect(self._on_load_finished)

        idx = self.tabs.addTab(view, "Nueva pestaña")
        self.tabs.setCurrentIndex(idx)

        # Si no hay URL, cargamos nuestra nueva pestaña personalizada
        if url is None:
            ruta_html = os.path.join(os.path.dirname(__file__), "assets", "nueva_pestana.html")
            view.setUrl(QUrl.fromLocalFile(ruta_html))
        else:
            view.setUrl(QUrl(url))

        if self.interceptor_actual is not None:
            self.interceptor_actual.registrar_pestana(id(view))
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
        if view is None: return
        self.barra.setText(view.url().toString())
        self._actualizar_candado(view.url())
        titulo = view.title() or "Nueva pestaña"
        self.setWindowTitle(f"{titulo} — {config.NOMBRE}")
        self.progreso.hide()
        self.btn_recargar.setIcon(icono("rotate-cw"))
        self.btn_recargar.setToolTip("Recargar (F5)")
        self._actualizar_estrella()
        self.actualizar_escudo()

    # ---------- SEÑALES ----------

    def _es_actual(self):
        return self.sender() is self.pestana_actual()

    def _on_url_changed(self, qurl):
        if self._es_actual():
            self.barra.setText(qurl.toString())
            self._actualizar_estrella()
            self._actualizar_candado(qurl)

    def _on_title_changed(self, titulo):
        view = self.sender()
        idx = self.tabs.indexOf(view)
        if idx != -1:
            corto = titulo if len(titulo) <= 22 else titulo[:21] + "…"
            self.tabs.setTabText(idx, corto or "Nueva pestaña")
            self.tabs.setTabToolTip(idx, titulo)
        if self._es_actual():
            self.setWindowTitle(f"{titulo} — {config.NOMBRE}")

    def _on_icon_changed(self, icon_url):
        view = self.sender()
        if not isinstance(view, QWebEngineView): return
        idx = self.tabs.indexOf(view)
        if idx == -1: return

        if icon_url.isValid() and not icon_url.isEmpty():
            icono_pestana = QIcon(icon_url.toString())
            self.tabs.setTabIcon(idx, icono_pestana)

    def _on_load_started(self):
        if self._es_actual():
            self.progreso.setValue(0)
            self.progreso.show()
            self.btn_recargar.setIcon(icono("x"))
            self.btn_recargar.setToolTip("Detener (Esc)")

    def _on_load_progress(self, valor):
        if self._es_actual():
            self.progreso.setValue(valor)

    def _on_load_finished(self, ok):
        if self._es_actual():
            self.progreso.hide()
            self.btn_recargar.setIcon(icono("rotate-cw"))
            self.btn_recargar.setToolTip("Recargar (F5)")
            self._actualizar_estrella()
            self.actualizar_escudo()

        view = self.sender()
        if not isinstance(view, QWebEngineView):
            return

        # Si es nuestra nueva pestaña, inyectamos datos
        url_actual = view.url().toString()
        if url_actual.endswith("nueva_pestana.html"):
            motor = motores.obtener(self.motor_actual)
            url_motor = motor["url_busqueda"].split("{q}")[0] # Tomamos solo la base
            
            # Enviamos el motor
            view.page().runJavaScript(f"actualizarMotor('{url_motor}');")
            
            # Enviamos los favoritos
            favs = self.favoritos.todos()
            view.page().runJavaScript(f"cargarFavoritos({json.dumps(favs)});")

        # Guardar historial (excepto si es incógnito o es la nueva pestaña)
        if ok and not self.es_incognito and not url_actual.endswith("nueva_pestana.html"):
            self.historial.añadir(view.title(), url_actual)

    # ---------- TECLADO ----------

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Control:
            self._ctrl_pulsado = True
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Control:
            self._ctrl_pulsado = False
        super().keyReleaseEvent(event)

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
        self.accion_ver_fav.setChecked(self.prefs.get("mostrar_barra_favoritos", True))
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
        if v: v.stop()
# navegador.py
# Clase MiNavegador y helpers. Importar desde main.py o ventana_incognito.py.

import os
import json
import time
from urllib.parse import quote, urlparse

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLineEdit, QToolBar, QPushButton,
    QProgressBar, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QMenu, QInputDialog, QCompleter, QFileDialog
)
from PyQt6.QtCore import QUrl, Qt, QStringListModel, QTimer, QSize
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile, QWebEngineSettings, QWebEnginePage
)

from privacidad.bloqueador import Bloqueador
from privacidad import anti_fingerprint
from interfaz.puente_vim import PaginaVim, crear_script_vim
from interfaz.pestanas import Pestanas
from interfaz import pagina_inicio
from assets.icons.helpers import icono
from modelos import motores
from modelos import busqueda
from modelos.sesion import Sesion, ordenar_fijadas
from modelos.zoom import (
    Zoom, host_de, FACTOR_DEFECTO, pasar_a_puntos,
)
import config


# ---------- VARIABLES GLOBALES ----------

_perfil_normal = None  # perfil persistente compartido por la ventana normal


def perfil_persistente():
    """Perfil compartido de la ventana normal, con cookies en disco.

    El perfil por defecto de QtWebEngine es "off the record": no guarda
    cookies ni caché, así que cada arranque parecía un navegador recién
    instalado. Los buscadores (Google sobre todo) respondían con CAPTCHA en
    cada búsqueda. Un perfil con nombre sí persiste, como en cualquier
    navegador. El incógnito NO usa esto: tiene su propio perfil en memoria.
    """
    global _perfil_normal
    if _perfil_normal is None:
        _perfil_normal = QWebEngineProfile("MiNavegador")
        _perfil_normal.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
    return _perfil_normal


def url_a_texto(qurl):
    """URL como texto para GUARDAR (historial, favoritos). Los espacios van
    como %20 para que la URL siga siendo válida al volver a abrirla."""
    return qurl.toString(QUrl.ComponentFormattingOption.EncodeSpaces)


def configurar_perfil(gestor, anti_fingerprint_activo=None):
    """Configura el perfil normal y devuelve (perfil, interceptor).

    Cada llamada crea su propio Bloqueador; no hay estado global compartido.
    """
    perfil = perfil_persistente()
    anti_fingerprint.preparar_perfil(perfil, anti_fingerprint_activo)
    perfil.setHttpCacheMaximumSize(50 * 1024 * 1024)
    interceptor = Bloqueador(
        gestor,
        privacidad=anti_fingerprint.esta_activo(perfil),
        ua=perfil.httpUserAgent(),
    )
    perfil.setUrlRequestInterceptor(interceptor)

    # Detector Vim para inputs.
    perfil.scripts().insert(crear_script_vim())

    ajustes = perfil.settings()
    ajustes.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
    ajustes.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
    ajustes.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)

    # --- Rendimiento: aceleración de hardware y renderizado ---
    ajustes.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
    ajustes.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
    ajustes.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
    ajustes.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)

    return perfil, interceptor


# ---------- VENTANA PRINCIPAL ----------

class MiNavegador(QMainWindow):

    def __init__(self, gestor, prefs, historial, favoritos, descargas,
                 perfil_web=None, interceptor_propio=None, es_incognito=False,
                 sesion=None, zoom=None):
        super().__init__()

        self.gestor = gestor
        self.prefs = prefs

        # Modelos compartidos (pasados por constructor).
        self.historial = historial
        self.favoritos = favoritos
        self.descargas = descargas

        # Sesión: en incógnito nunca toca el disco (ruta=None).
        if sesion is not None:
            self.sesion = sesion
        elif es_incognito:
            self.sesion = Sesion(None)
        else:
            self.sesion = Sesion()

        # Zoom por sitio: en incógnito solo vive en memoria.
        if zoom is not None:
            self.zoom = zoom
        elif es_incognito:
            self.zoom = Zoom(None)
        else:
            self.zoom = Zoom()

        # Modo incógnito.
        self.es_incognito = es_incognito
        self.perfil_web = perfil_web
        # Si no se pasa interceptor_propio, se crea uno nuevo (para ventana normal).
        # En incógnito siempre se pasa uno propio desde ventana_incognito.py.
        self.interceptor_actual = interceptor_propio

        self.motor_actual = prefs.get(
            "motor_busqueda", motores.motor_por_defecto()
        )

        # Si no hay interceptor propio (ventana normal), creamos uno para este perfil.
        if self.interceptor_actual is None:
            from privacidad.bloqueador import Bloqueador
            perfil_para_interceptor = (perfil_web if perfil_web is not None
                                       else perfil_persistente())
            self.interceptor_actual = Bloqueador(
                gestor,
                privacidad=anti_fingerprint.esta_activo(perfil_para_interceptor),
                ua=perfil_para_interceptor.httpUserAgent(),
            )
            perfil_para_interceptor.setUrlRequestInterceptor(self.interceptor_actual)

        # Las descargas del perfil de ESTA ventana (normal o incógnito)
        # las gestiona esta ventana, con SUS modelos.
        self._panel_descargas = None

        # Pestañas cerradas recientes (Ctrl+Shift+T). Solo en memoria.
        self._cerradas = []
        # Restauración diferida: marcadores en espera de crear su vista.
        self._diferidas = {}
        self._restaurando = False
        # Zoom: hosts cuyo zoom tocó el usuario en esta sesión (se respetan)
        # y host previo de cada vista (para detectar cambio de sitio).
        self._zoom_tocado_sesion = set()
        self._zoom_host_por_view = {}
        # Modo lectura: estado por vista (bool). No se persiste.
        self._lectura_por_view = {}
        perfil = (perfil_web if perfil_web is not None
                  else perfil_persistente())
        perfil.downloadRequested.connect(self._descarga_solicitada)

        self.setWindowTitle(f"{config.NOMBRE} {config.VERSION}")
        self.resize(1200, 800)

        # --- Red para sugerencias ---
        self.net = QNetworkAccessManager(self)
        self.reply_sugerencias = None

        # --- Motor de búsqueda: si el elegido no responde, se usa el respaldo ---
        # Claves de los motores que han fallado en esta sesión (no se persiste).
        self._motores_caidos = set()
        self._respaldo_hecho = set()
        # Motores que pidieron CAPTCHA: no se usan hasta que pase la espera.
        self._reto_hasta = {}
        self._reto_visto = set()
        self._reply_motor = None
        self._motor_comprobado = 0.0

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
        self.tabs.barra.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabs.barra.customContextMenuRequested.connect(
            self._menu_contexto_pestana)

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
        self.btn_lectura = self._boton_icono("book-open", "Modo lectura (Ctrl+Alt+R)",
                                             self.alternar_lectura)
        self.btn_lectura.setCheckable(True)
        self.btn_lectura.setChecked(False)

        # --- Menú hamburguesa (Nivel 11 B5) ---
        self.btn_menu = self._boton_icono("menu", "Menú (sesión, lectura, zoom, privacidad)",
                                          self._abrir_menu_hamburguesa)
        self.menu_hamburguesa = QMenu(self)
        self._construir_menu_hamburguesa()

        fila_nav = QHBoxLayout()
        fila_nav.setContentsMargins(8, 4, 8, 6)
        fila_nav.setSpacing(4)
        for w in (self.btn_atras, self.btn_adelante, self.btn_recargar, btn_inicio,
                  self.btn_motor):
            fila_nav.addWidget(w)
        fila_nav.addWidget(self.barra, 1)
        for w in (self.btn_escudo, btn_fav, self.btn_historial, btn_inc, btn_desc,
                  self.btn_lectura, self.btn_menu):
            fila_nav.addWidget(w)

        # --- Fila 3: marcadores ---
        self.barra_fav = QToolBar("Favoritos")
        self.barra_fav.setObjectName("barra_favoritos")
        self.barra_fav.setMovable(False)

        # --- Buscar en la página (Ctrl+F) ---
        from interfaz.barra_busqueda import BarraBusqueda
        self.busqueda = BarraBusqueda(self)
        self.busqueda.buscar.connect(self._buscar_en_pagina)
        self.busqueda.cerrada.connect(self._limpiar_busqueda)

        # --- Cabecera (un solo bloque con el color del tema) ---
        self.chrome = QFrame()
        self.chrome.setObjectName("chrome")
        self.chrome.setProperty("incognito", self.es_incognito)
        caja = QVBoxLayout(self.chrome)
        caja.setContentsMargins(0, 0, 0, 0)
        caja.setSpacing(0)
        caja.addLayout(fila_tabs)
        caja.addLayout(fila_nav)
        caja.addWidget(self.busqueda)
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
        from interfaz.atajos_vim import VimKeys
        self.vim = VimKeys(self)

        self._crear_atajos()
        self._refrescar_barra_favoritos()

        # Al abrir: restaurar la sesión anterior (si está activada) o una
        # pestaña nueva. En incógnito siempre se empieza de cero.
        if (not self.es_incognito
                and self.prefs.get("restaurar_sesion", True)
                and not self.sesion.vacia()):
            self._restaurar_sesion()
        else:
            self.nueva_pestana()

        # Comprobar en segundo plano si el motor de búsqueda responde. En
        # incógnito no hace falta: no se guarda ningún estado de esta sonda.
        if not self.es_incognito:
            # Warmup inmediato: lanzar la sonda y la precarga en cuanto el loop
            # de eventos esté libre, no esperar 1,5 s.
            QTimer.singleShot(0, self._comprobar_motor)

    # ---------- MOTOR DE BÚSQUEDA: DISPONIBILIDAD ----------

    def _motor_efectivo(self):
        """Clave del motor que se usará ahora mismo (respaldo si hace falta)."""
        return busqueda.elegir(self.motor_actual, self._caidos_ahora())

    def _caidos_ahora(self):
        """Motores no utilizables: los caídos y los que están en espera por
        haber pedido CAPTCHA (la espera se limpia sola al expirar)."""
        ahora = time.monotonic()
        for clave, hasta in list(self._reto_hasta.items()):
            if hasta <= ahora:
                del self._reto_hasta[clave]
        return set(self._motores_caidos) | set(self._reto_hasta)

    def _usando_respaldo(self):
        return self._motor_efectivo() != self.motor_actual

    def _comprobar_motor(self, clave=None):
        """Pregunta al motor si responde. Si no, lo marca como caído.

        Se lanza al arrancar, al cambiar de motor y de vez en cuando. Nunca
        bloquea la interfaz: la respuesta llega por señal. Cualquier fallo de
        esta comprobación (red rara, servidor que rechaza HEAD) se ignora: es
        solo un diagnóstico, no debe tumbar el navegador.
        """
        try:
            clave = clave or self.motor_actual
            if self._reply_motor is not None:
                return
            motor = motores.obtener(clave)
            url = motor.get("url_home") or motor["url_busqueda"].format(q="")

            peticion = QNetworkRequest(QUrl(url))
            # Sin caché: interesa saber si la red llega, no lo que hubiera
            # guardado de antes.
            peticion.setAttribute(
                QNetworkRequest.Attribute.CacheLoadControlAttribute,
                QNetworkRequest.CacheLoadControl.AlwaysNetwork)
            peticion.setTransferTimeout(6000)
            self._reply_motor = self.net.head(peticion)
            self._reply_motor.finished.connect(
                lambda r=None, c=clave: self._on_motor_comprobado(
                    c, r or self._reply_motor)
            )
        except Exception:
            self._reply_motor = None
            self._motor_comprobado = time.monotonic()

    def _on_motor_comprobado(self, clave, reply):
        self._reply_motor = None
        self._motor_comprobado = time.monotonic()
        try:
            responde = self._motor_responde(reply)
        except Exception:
            responde = True  # ante la duda, no cambiar de motor
        finally:
            if reply is not None:
                reply.deleteLater()

        if responde:
            if clave in self._motores_caidos:
                self._motores_caidos.discard(clave)
                self._actualizar_icono_motor()
                self._refrescar_inicios()
                print(f"[Búsqueda] {busqueda.nombre(clave)} responde de nuevo.",
                      flush=True)
            return

        if clave not in self._motores_caidos:
            self._motores_caidos.add(clave)
            if clave == self.motor_actual:
                self._actualizar_icono_motor()
                self.statusBar().showMessage(
                    f"{busqueda.nombre(clave)} no responde en tu red. "
                    f"Las búsquedas usarán {busqueda.nombre(self._motor_efectivo())}.",
                    8000)
                self._refrescar_inicios()
                # Aviso legible en la consola: los errores de red de Chromium
                # quedan silenciados (ver config.CHROMIUM_FLAGS).
                print(f"[Búsqueda] {busqueda.nombre(clave)} no responde en tu "
                      f"red; las búsquedas usarán "
                      f"{busqueda.nombre(self._motor_efectivo())}.", flush=True)

    def _precargar_motor(self, clave):
        """Carga la home del motor en una vista oculta para calentar la conexión.

        Esto hace que la primera búsqueda del usuario sea instantánea porque:
        - DNS ya resuelto
        - TCP/TLS handshake ya hecho
        - Socket pool de Chromium caliente
        - Posible HSTS/HPKP cacheado

        La vista se destruye sola al terminar (deleteLater).
        NOTA: Actualmente no se usa (desactivada por causar efectos laterales).
        """
        motor = motores.obtener(clave)
        url_home = motor.get("url_home")
        if not url_home:
            return

        # Evitar precargas duplicadas simultáneas
        if getattr(self, f"_precarga_{clave}", None) is not None:
            return

        view = QWebEngineView()
        # No mostrar, no añadir a pestañas, sin foco
        view.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        view.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        view.resize(1, 1)
        view.move(-10000, -10000)

        # Usar el mismo perfil que las pestañas reales
        perfil = (self.perfil_web if self.perfil_web is not None
                  else perfil_persistente())
        page = PaginaVim(perfil, view)
        view.setPage(page)

        def _fin(ok):
            # Limpiar referencia para permitir otra precarga futura
            setattr(self, f"_precarga_{clave}", None)
            view.deleteLater()
            if ok:
                print(f"[Búsqueda] {busqueda.nombre(clave)} precargado.", flush=True)

        setattr(self, f"_precarga_{clave}", view)
        view.loadFinished.connect(_fin)
        view.setUrl(QUrl(url_home))

    @staticmethod
    def _motor_responde(reply):
        """True si la petición llegó a un servidor, aunque responda un error."""
        if reply.error() == QNetworkReply.NetworkError.NoError:
            return True
        # Un 4xx/5xx significa que el dominio SÍ responde (p. ej. un 405
        # porque el servidor no acepta HEAD).
        estado = reply.attribute(
            QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        return bool(estado)

    def _refrescar_inicios(self):
        """Rehace las páginas de inicio abiertas con el motor que toca ahora."""
        for i in range(self.tabs.count()):
            view = self.tabs.widget(i)
            if not isinstance(view, QWebEngineView):
                continue
            if self._es_url_vacia(view.url()):
                view.setHtml(self._html_inicio())

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
            favs, busqueda.nombre(self._motor_efectivo()), self.es_incognito)

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
        hist = v.history() if isinstance(v, QWebEngineView) else None
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
        if idx == -1:
            return
        nuevo = ic if not ic.isNull() else self._icono_pestana(view)
        if self.es_fijada(idx):
            # La pestaña fijada muestra el pin; el favicon se guarda para
            # devolverlo si se desfija.
            datos = dict(self.tabs.tabData(idx) or {})
            datos["icono"] = nuevo
            self.tabs.setTabData(idx, datos)
            return
        self.tabs.setTabIcon(idx, nuevo)

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
        from interfaz.ventana_incognito import VentanaIncognito

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
            from interfaz.ventana_descargas import VentanaDescargas
            self._panel_descargas = VentanaDescargas(
                self.descargas, abrir_url=self._abrir_en_pestana_nueva
            )
        return self._panel_descargas

    def _abrir_en_pestana_nueva(self, url):
        self.nueva_pestana(url)

    def abrir_panel_descargas(self):
        panel = self._obtener_panel_descargas()
        panel.show()
        panel.raise_()
        panel.activateWindow()

    def _notificar_descarga(self, nombre, ruta):
        self.statusBar().showMessage(
            f"Descargando: {nombre}  →  {ruta}", 5000
        )

    # ---------- MOTOR DE BÚSQUEDA ----------

    def _actualizar_icono_motor(self):
        motor = motores.obtener(self.motor_actual)
        self.btn_motor.setText(motor["icono"])
        self.btn_motor.setCursor(Qt.CursorShape.PointingHandCursor)
        if self._usando_respaldo():
            self.btn_motor.setToolTip(
                f"Motor: {motor['nombre']} (no responde en tu red)"
                f"  ·  usando {busqueda.nombre(self._motor_efectivo())}"
                "  ·  clic para cambiar")
        else:
            self.btn_motor.setToolTip(
                f"Motor: {motor['nombre']} (clic para cambiar)")

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
        # Elección explícita del usuario: se respeta aunque ese motor hubiera
        # pedido CAPTCHA hace un momento (quizá quiera resolverlo).
        self._reto_hasta.pop(clave, None)
        # Motor recién elegido: puede que ahora sí responda (o que no).
        self._motor_comprobado = 0.0
        self._comprobar_motor(clave)

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
            qurl = QUrl(texto)
            if qurl.isValid() and qurl.scheme() in ("http", "https"):
                view.setUrl(qurl)
            else:
                self.statusBar().showMessage("URL inválida", 3000)
            return

        # Heurística: parece un dominio (tiene punto, sin espacios, no es IP sola).
        # Validamos con QUrl para evitar javascript:, data:, file:, etc.
        if "." in texto and " " not in texto and not texto.replace(".", "").isdigit():
            qurl = QUrl("https://" + texto)
            if qurl.isValid() and qurl.scheme() in ("http", "https"):
                view.setUrl(qurl)
            else:
                self.statusBar().showMessage("Dirección inválida", 3000)
            return

        # Si el motor elegido no responde (red que corta ese dominio), se busca
        # con el de respaldo y se avisa. La comprobación se refresca cada 5
        # minutos para que se recupere solo cuando la red lo permita.
        if time.monotonic() - self._motor_comprobado > 300:
            self._comprobar_motor()

        url, clave = busqueda.url_busqueda(
            self.motor_actual, texto, self._caidos_ahora())
        if clave != self.motor_actual:
            self.statusBar().showMessage(
                f"{busqueda.nombre(self.motor_actual)} no está disponible: "
                f"buscando en {busqueda.nombre(clave)}...", 5000)
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

        # --- Nivel 10: anti-fingerprinting ---
        menu.addSeparator()
        activo = anti_fingerprint.esta_activo(self._perfil_actual())
        titulo = menu.addAction(
            "Huella digital: " + ("protegida" if activo else "expuesta")
        )
        titulo.setEnabled(False)
        acc = menu.addAction("Proteger contra fingerprinting")
        acc.setCheckable(True)
        acc.setChecked(activo)
        acc.triggered.connect(
            lambda _=False, a=acc: self._cambiar_anti_fingerprint(a.isChecked())
        )

        acc = menu.addAction("Comprobar mi huella (página local)")
        acc.triggered.connect(self.abrir_privacidad)

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

    # ---------- PRIVACIDAD (Nivel 10) ----------

    def _perfil_actual(self):
        return (self.perfil_web if self.perfil_web is not None
                else perfil_persistente())

    def abrir_privacidad(self):
        """Abre la página local que muestra lo que una web ve de nosotros."""
        from interfaz import pagina_privacidad
        activo = anti_fingerprint.esta_activo(self._perfil_actual())
        view = self.nueva_pestana()
        view.setHtml(pagina_privacidad.generar_html(activo))
        idx = self.tabs.indexOf(view)
        if idx != -1:
            self.tabs.setTabText(idx, "Privacidad")

    def _cambiar_anti_fingerprint(self, activo):
        """Activa/desactiva la protección en el perfil de esta ventana.

        Los scripts de un perfil se aplican al cargar cada página, así que
        el cambio se nota al recargar (no hace falta reiniciar el navegador).
        """
        anti_fingerprint.aplicar(self._perfil_actual(), activo)
        if self.interceptor_actual is not None:
            self.interceptor_actual.set_privacidad(activo)
        self.prefs.set("anti_fingerprint", activo)
        aviso = ("Anti-fingerprinting activado" if activo
                 else "Anti-fingerprinting desactivado")
        self.statusBar().showMessage(
            f"{aviso}: recarga la página para aplicarlo", 5000
        )

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
        if not isinstance(view, QWebEngineView):
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
        from interfaz.ventana_favoritos import VentanaFavoritos
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
        from interfaz.ventana_historial import VentanaHistorial
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
            if self.prefs.get("restaurar_sesion", True):
                self._guardar_sesion()
            else:
                self.sesion.borrar()
            self.historial.guardar()
            self.favoritos.guardar()
            self.descargas.guardar()
            self.prefs.guardar()
        super().closeEvent(event)

    # ---------- PESTAÑAS ----------

    def pestana_actual(self):
        # Si la pestaña activa venía de la sesión y aún no tiene vista, se
        # crea ahora: quien pregunta espera una QWebEngineView de verdad.
        if not self._restaurando:
            self._materializar(self.tabs.currentIndex())
        return self.tabs.currentWidget()

    def nueva_pestana(self, url=None):
        view = self._crear_vista()

        idx = self.tabs.addTab(view, "Nueva pestaña")
        self.tabs.setTabIcon(idx, icono("home", config.COLOR_TEXTO_SUAVE, 16))
        self.tabs.setCurrentIndex(idx)
        if url:
            view.setUrl(QUrl(url))
        else:
            view.setHtml(self._html_inicio())
            view.setFocus()
        return view

    def _crear_vista(self):
        """Crea una pestaña de verdad (QWebEngineView) con sus señales."""
        view = QWebEngineView()

        perfil = (self.perfil_web if self.perfil_web is not None
                  else perfil_persistente())

        page = PaginaVim(perfil, view)
        page.busqueda_pedida.connect(self._buscar_desde_inicio)
        page.findTextFinished.connect(self._on_busqueda_terminada)
        view.setPage(page)

        view.urlChanged.connect(self._on_url_changed)
        view.titleChanged.connect(self._on_title_changed)
        view.iconChanged.connect(self._on_icon_changed)
        view.loadStarted.connect(self._on_load_started)
        view.loadProgress.connect(self._on_load_progress)
        view.loadFinished.connect(self._on_load_finished)

        if self.interceptor_actual is not None:
            self.interceptor_actual.registrar_pestana(id(view))
        return view

    def cerrar_pestana(self, idx):
        widget = self.tabs.widget(idx)
        es_vista = isinstance(widget, QWebEngineView)
        if es_vista:
            self._anotar_cerrada(widget.url(), self.es_fijada(idx))
            if self.interceptor_actual is not None:
                self.interceptor_actual.olvidar_pestana(id(widget))
        if widget is not None:
            self._diferidas.pop(id(widget), None)
            self._zoom_host_por_view.pop(id(widget), None)
            self._lectura_por_view.pop(id(widget), None)
        self.tabs.removeTab(idx)
        if widget is not None:
            widget.deleteLater()
        if self.tabs.count() == 0:
            self.close()

    def _anotar_cerrada(self, qurl, fijada=False):
        """Guarda la URL para poder reabrirla con Ctrl+Shift+T.

        Las páginas internas (inicio, about:) no se reabren: no hay nada que
        restaurar. Se recuerda también si estaba fijada.
        """
        if self._es_url_vacia(qurl) or qurl.scheme() not in ("http", "https", "file"):
            return
        self._cerradas.append((url_a_texto(qurl), bool(fijada)))
        del self._cerradas[:-10]     # como mucho las 10 últimas

    def reabrir_pestana_cerrada(self):
        if not self._cerradas:
            return
        url, fijada = self._cerradas.pop()
        view = self.nueva_pestana(url)
        if fijada:
            self._aplicar_fijada(self.tabs.indexOf(view), True)

    def ir_a_pestana(self, idx):
        """Ctrl+1..8 → esa pestaña; Ctrl+9 → la última (idx -1)."""
        total = self.tabs.count()
        if total == 0:
            return
        if idx < 0:
            idx = total - 1
        if 0 <= idx < total:
            self.tabs.setCurrentIndex(idx)

    # ---------- PESTAÑAS FIJADAS ----------

    def es_fijada(self, idx):
        datos = self.tabs.tabData(idx)
        return bool(datos and datos.get("fijada"))

    def alternar_fijada(self, idx=None):
        """Ctrl+Shift+P: fija o desfija la pestaña actual (o la indicada)."""
        if idx is None:
            idx = self.tabs.currentIndex()
        if idx < 0:
            return
        self._aplicar_fijada(idx, not self.es_fijada(idx))

    def _aplicar_fijada(self, idx, fijada):
        if not 0 <= idx < self.tabs.count():
            return
        datos = dict(self.tabs.tabData(idx) or {})
        datos["fijada"] = bool(fijada)
        self.tabs.setTabData(idx, datos)

        vista = self.tabs.widget(idx)
        if fijada:
            # Guardamos el favicon para devolverlo al desfijar; el icono de
            # la pestaña pasa a ser el pin.
            favicon = (vista.icon()
                       if isinstance(vista, QWebEngineView) else None)
            if favicon is not None and not favicon.isNull():
                datos["icono"] = favicon
                self.tabs.setTabData(idx, datos)
            self.tabs.setTabIcon(idx, self._icono_pin())
        else:
            favorito = datos.pop("icono", None)
            self.tabs.setTabData(idx, datos)
            if favorito is not None and not favorito.isNull():
                self.tabs.setTabIcon(idx, favorito)
            elif isinstance(vista, QWebEngineView):
                self.tabs.setTabIcon(idx, self._icono_pestana(vista))
            else:
                self.tabs.setTabIcon(
                    idx, icono("home", config.COLOR_TEXTO_SUAVE, 16))

        # Las fijadas van siempre a la izquierda. El destino es el final del
        # bloque de fijadas (sin contarse a sí misma).
        destino = sum(
            1 for i in range(self.tabs.count())
            if i != idx and self.es_fijada(i)
        )
        if destino != idx:
            actual = self.tabs.currentWidget()
            self.tabs.moveTab(idx, destino)
            if actual is not None:
                self.tabs.setCurrentWidget(actual)

    def _icono_pin(self):
        return icono("pin", config.COLOR_ACENTO_SUAVE, 16)

    def _menu_contexto_pestana(self, pos):
        idx = self.tabs.barra.tabAt(pos)
        if idx < 0:
            return
        menu = QMenu(self)
        acc = menu.addAction(
            "Desfijar pestaña" if self.es_fijada(idx) else "Fijar pestaña"
        )
        acc.triggered.connect(lambda: self.alternar_fijada(idx))
        acc = menu.addAction("Cerrar pestaña")
        acc.triggered.connect(lambda: self.cerrar_pestana(idx))
        menu.addSeparator()
        acc = menu.addAction("Reabrir pestaña cerrada")
        acc.setEnabled(bool(self._cerradas))
        acc.triggered.connect(self.reabrir_pestana_cerrada)
        menu.exec(self.tabs.barra.mapToGlobal(pos))

    def cerrar_ventana(self):
        self.close()

    def alternar_pantalla_completa(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    # ---------- SESIÓN ----------

    def _estado_sesion(self):
        """Pestañas que hay ahora y cuál está activa, listas para guardar."""
        pestanas = []
        activa = 0
        actual = self.tabs.currentIndex()
        for i in range(self.tabs.count()):
            view = self.tabs.widget(i)
            if view is None:
                continue
            diferida = self._diferidas.get(id(view))
            if diferida is not None:
                # Pestaña restaurada que aún no se ha abierto: se guarda tal
                # cual estaba, sin crear la vista.
                entrada = dict(diferida)
                entrada["fijada"] = self.es_fijada(i)
                pestanas.append(entrada)
            elif (not isinstance(view, QWebEngineView)
                    or self._es_url_vacia(view.url())
                    or view.url().scheme() not in ("http", "https")):
                # La página de inicio propia no se restaura: se abre nueva.
                pestanas.append({"nueva": True, "fijada": self.es_fijada(i)})
            else:
                pestanas.append({
                    "url": url_a_texto(view.url()),
                    "titulo": view.title(),
                    "fijada": self.es_fijada(i),
                })
            if i == actual:
                activa = len(pestanas) - 1
        return pestanas, activa

    def _guardar_sesion(self):
        pestanas, activa = self._estado_sesion()
        self.sesion.guardar(pestanas, activa)

    def _restaurar_sesion(self):
        """Reabre las pestañas guardadas SIN cargar ninguna URL aún.

        Todas las pestañas empiezan como marcadores ligeros (QWidget).
        La vista real (QWebEngineView) y la carga de la URL se hacen
        solo cuando la pestaña recibe el foco por primera vez.
        """
        entradas = self.sesion.pestanas()
        if not entradas:
            self.nueva_pestana()
            return

        entradas, activa = ordenar_fijadas(entradas, self.sesion.activa())
        self._restaurando = True
        try:
            for i, entrada in enumerate(entradas):
                marcador = QWidget()
                self.tabs.addTab(marcador, self._titulo_entrada(entrada))
                self.tabs.setTabIcon(
                    i, icono("home", config.COLOR_TEXTO_SUAVE, 16))
                self._aplicar_fijada_silenciosa(i, entrada)
                self._diferidas[id(marcador)] = entrada
        finally:
            self._restaurando = False

        if self.tabs.count() == 0:
            self.nueva_pestana()
            return
        idx = activa
        if 0 <= idx < self.tabs.count():
            self.tabs.setCurrentIndex(idx)
            # Materializar la pestaña activa AHORA (ya no estamos restaurando)
            self._materializar(idx)

    def _aplicar_fijada_silenciosa(self, idx, entrada):
        """Marca la pestaña como fijada sin reordenar (ya viene ordenada)."""
        if not entrada.get("fijada"):
            return
        self.tabs.setTabData(idx, {"fijada": True})
        self.tabs.setTabIcon(idx, self._icono_pin())

    @staticmethod
    def _titulo_entrada(entrada):
        if entrada.get("nueva"):
            return "Nueva pestaña"
        return (entrada.get("titulo") or entrada.get("url") or "Nueva pestaña")

    def _cargar_entrada(self, view, entrada):
        if entrada.get("nueva"):
            view.setHtml(self._html_inicio())
        else:
            view.setUrl(QUrl(entrada.get("url")))
            self.tabs.setTabIcon(
                self.tabs.indexOf(view),
                icono("home", config.COLOR_TEXTO_SUAVE, 16))

    def _materializar(self, idx):
        """Crea la vista real de una pestaña restaurada que estaba en espera."""
        marcador = self.tabs.widget(idx)
        if marcador is None:
            return
        entrada = self._diferidas.pop(id(marcador), None)
        if entrada is None:
            return
        view = self._crear_vista()
        self.tabs.reemplazar_pagina(idx, view)
        self._cargar_entrada(view, entrada)
        self._aplicar_fijada_silenciosa(idx, entrada)
        self._lectura_por_view[id(view)] = False

    # ---------- ZOOM POR SITIO ----------

    def _zoom_host_de(self, view):
        if not isinstance(view, QWebEngineView):
            return ""
        return host_de(view.url())

    def _zoom_aplicar(self, view, factor):
        if not isinstance(view, QWebEngineView):
            return
        try:
            view.setZoomFactor(factor)
        except Exception:
            pass

    def _zoom_aplicar_vista(self, view):
        """Aplica el zoom guardado del host de `view`, salvo que el usuario
        ya haya tocado el zoom en esta sesión (ese se respeta)."""
        host = self._zoom_host_de(view)
        if not host or host in self._zoom_tocado_sesion:
            return
        factor = self.zoom.obtener(host)
        self._zoom_aplicar(view, factor)

    def _zoom_mostrar(self, factor):
        self.statusBar().showMessage(f"Zoom: {pasar_a_puntos(factor)} %", 2000)

    def zoom_mas(self):
        self._zoom_cambiar(mas=True)

    def zoom_menos(self):
        self._zoom_cambiar(mas=False)

    def zoom_reset(self):
        self._zoom_cambiar(reset=True)

    def _zoom_cambiar(self, mas=False, reset=False):
        view = self.pestana_actual()
        host = self._zoom_host_de(view)
        if not host:
            return
        if reset:
            self.zoom.restablecer(host)
            factor = FACTOR_DEFECTO
        else:
            actual = view.zoomFactor() if isinstance(view, QWebEngineView) else 1.0
            factor = self.zoom.ajuste(actual, mas=mas)
            self.zoom.establecer(host, factor)
        self._zoom_tocado_sesion.add(host)
        self._zoom_aplicar(view, factor)
        self._zoom_mostrar(factor)

    # ---------- MODO LECTURA ----------

    def _js_activar_lectura(self):
        """JS inline que busca el artículo y lo muestra en un overlay."""
        from interfaz.modo_lectura import generar_css, JS_BUSCAR_ARTICULO, js_literal
        css = js_literal(generar_css())
        return (
            "(function(){"
            "var ID='mn-lector';"
            "if(document.getElementById(ID)) return 'ya-activo';"
            + JS_BUSCAR_ARTICULO
            + "var a=_encontrar();"
            + "if(!a) return 'sin-articulo';"
            + "var c=a.cloneNode(true);"
            + "var o=document.createElement('div');"
            + "o.id=ID;"
            + "var btn=document.createElement('button');"
            + "btn.id='mn-lector-salir';"
            + "btn.textContent='Salir';"
            + "btn.onclick=function(){var x=document.getElementById(ID);"
            + " if(x) x.remove();};"
            + "o.appendChild(btn);"
            + "var cont=document.createElement('div');"
            + "cont.id='mn-lector-contenido';"
            + "cont.appendChild(c);"
            + "o.appendChild(cont);"
            + "document.body.appendChild(o);"
            + "var s=document.createElement('style');"
            + "s.textContent=" + css + ";"
            + "document.head.insertBefore(s, document.head.firstChild);"
            + "return 'ok';"
            + "})()"
        )

    def _js_desactivar_lectura(self):
        return ("(function(){"
                 "var o=document.getElementById('mn-lector');"
                 "if(o) o.remove();"
                 "return 'ok';"
                 "})()")

    def alternar_lectura(self):
        view = self.pestana_actual()
        if not isinstance(view, QWebEngineView):
            return
        vid = id(view)
        # Consulta el estado real en el DOM (el boton Salir del overlay puede
        # haberlo desactivado sin pasar por Python).
        view.page().runJavaScript(
            "!!document.getElementById('mn-lector')",
            lambda res, vid=vid, view=view: self._alternar_después(
                vid, res, view))

    def _alternar_después(self, vid, tiene_overlay, view):
        if tiene_overlay:
            view.page().runJavaScript(
                self._js_desactivar_lectura(),
                lambda res, vid=vid: self._despues_lectura(vid, False, None))
        else:
            view.page().runJavaScript(
                self._js_activar_lectura(),
                lambda res, vid=vid: self._despues_lectura(
                    vid, res == "ok", res))

    def _despues_lectura(self, vid, activo, resultado):
        self._lectura_por_view[vid] = bool(activo)
        if not activo and resultado == "sin-articulo":
            view = self.tabs.widget(self.tabs.currentIndex())
            if view is not None and id(view) == vid:
                self.statusBar().showMessage(
                    "No se detectó un artículo en esta página", 3000)
        self._actualizar_boton_lectura()

    def esta_en_lectura(self, view=None):
        if view is None:
            view = self.pestana_actual()
        if not isinstance(view, QWebEngineView):
            return False
        return bool(self._lectura_por_view.get(id(view), False))

    def _actualizar_boton_lectura(self):
        activa = self.esta_en_lectura()
        self.btn_lectura.setChecked(activa)
        if activa:
            self.btn_lectura.setObjectName("btn_lectura_activo")
            self.btn_lectura.setToolTip("Salir del modo lectura (Ctrl+Alt+R)")
        else:
            self.btn_lectura.setObjectName("btn_lectura")
            self.btn_lectura.setToolTip("Modo lectura (Ctrl+Alt+R)")
        self.btn_lectura.style().unpolish(self.btn_lectura)
        self.btn_lectura.style().polish(self.btn_lectura)
        self.btn_lectura.update()

    # ---------- MENÚ HAMBURGUESA (Nivel 11 B5) ----------

    def _construir_menu_hamburguesa(self):
        m = self.menu_hamburguesa
        self.act_restaurar = m.addAction("Restaurar sesión al iniciar")
        self.act_restaurar.setCheckable(True)
        self.act_restaurar.setChecked(
            bool(self.prefs.get("restaurar_sesion", True)))
        self.act_restaurar.triggered.connect(self._toggle_restaurar_sesion)

        m.addSeparator()
        self.act_lectura = m.addAction("Modo lectura (Ctrl+Alt+R)")
        self.act_lectura.setCheckable(True)
        self.act_lectura.triggered.connect(self.alternar_lectura)

        m.addSeparator()
        m.addAction("Zoom: Acercar (Ctrl+=)", self.zoom_mas)
        m.addAction("Zoom: Alejar (Ctrl+-)", self.zoom_menos)
        m.addAction("Zoom: Restablecer (Ctrl+0)", self.zoom_reset)

        m.addSeparator()
        m.addAction("Comprobar privacidad (página local)", self.abrir_privacidad)

    def _abrir_menu_hamburguesa(self):
        self.act_restaurar.setChecked(
            bool(self.prefs.get("restaurar_sesion", True)))
        self.act_lectura.setChecked(self.esta_en_lectura())
        pos = self.btn_menu.mapToGlobal(self.btn_menu.rect().bottomLeft())
        self.menu_hamburguesa.exec(pos)

    def _toggle_restaurar_sesion(self, checked):
        self.prefs.set("restaurar_sesion", bool(checked))
        self.prefs.guardar()

    # ---------- BUSCAR EN LA PÁGINA ----------

    def abrir_busqueda(self):
        self.busqueda.abrir()

    def _buscar_en_pagina(self, texto, atras=False):
        view = self.pestana_actual()
        if not isinstance(view, QWebEngineView):
            return
        if not texto:
            view.page().findText("")
            self.busqueda.limpiar_resultado()
            return
        banderas = (QWebEnginePage.FindFlag.FindBackward if atras
                    else QWebEnginePage.FindFlag(0))
        view.page().findText(texto, banderas)

    def _limpiar_busqueda(self):
        view = self.pestana_actual()
        if isinstance(view, QWebEngineView):
            view.page().findText("")

    def _on_busqueda_terminada(self, resultado):
        if not self.busqueda.esta_abierta():
            return
        if not self.busqueda.texto():
            self.busqueda.limpiar_resultado()
            return
        self.busqueda.mostrar_resultado(
            resultado.activeMatch(), resultado.numberOfMatches()
        )

    def cerrar_pestana_actual(self):
        idx = self.tabs.currentIndex()
        if idx != -1:
            self.cerrar_pestana(idx)

    def cambio_de_pestana(self, idx):
        # Durante la restauración las pestañas aún son marcadores vacíos; no
        # hay nada que mostrar ni que crear hasta que el usuario las abra.
        if self._restaurando:
            return
        self._materializar(idx)
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
        # Zoom del sitio de esta pestaña (respeta lo elegido en la sesión).
        self._zoom_aplicar_vista(view)
        # La búsqueda abierta sigue en la pestaña nueva.
        if self.busqueda.esta_abierta() and self.busqueda.texto():
            self._buscar_en_pagina(self.busqueda.texto())

    # ---------- SEÑALES ----------

    def _es_actual(self):
        return self.sender() is self.pestana_actual()

    def _on_url_changed(self, qurl):
        if self._es_actual():
            self.barra.setText(self._texto_url(qurl))
            self._actualizar_candado(qurl)
            self._actualizar_estrella()
            self._actualizar_navegacion()

        # Cambio de sitio: aplico el zoom guardado del nuevo host.
        view = self.sender()
        if isinstance(view, QWebEngineView):
            host = host_de(qurl)
            previo = self._zoom_host_por_view.get(id(view))
            if host and previo != host:
                self._zoom_host_por_view[id(view)] = host
                if (not self.es_incognito
                        and host not in self._zoom_tocado_sesion):
                    self._zoom_aplicar_vista(view)

        # Nueva URL: sale del modo lectura de la página anterior.
        if isinstance(view, QWebEngineView):
            self._lectura_por_view[id(view)] = False

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
                self._zoom_aplicar_vista(view)

        # Primero el CAPTCHA: la página de verificación suele llegar con un
        # código HTTP de error (429), así que "no cargó" y "es un reto" pueden
        # ser el mismo evento. Detectarlo antes evita el mensaje equivocado.
        if not self._revisar_reto(self.sender()) and not ok:
            self._reintentar_con_respaldo(self.sender())

    def _revisar_reto(self, view):
        """Detecta la página de CAPTCHA de un motor y busca en el siguiente.

        Google responde /sorry/index a QtWebEngine: el dominio funciona pero no
        da resultados. En vez de dejarte atrapado en el reto, repetimos tu
        búsqueda en el motor siguiente (y no volvemos a molestar a ese motor
        durante un rato). Devuelve True si era un reto y ya se actuó.
        """
        try:
            return self._revisar_reto_seguro(view)
        except Exception:
            return False

    def _revisar_reto_seguro(self, view):
        if not isinstance(view, QWebEngineView):
            return False
        qurl = view.url()
        clave = busqueda.es_reto(qurl.host(), qurl.path())
        if clave is None:
            return False

        marca = (id(view), qurl.toString())
        if marca in self._reto_visto:
            return True
        self._reto_visto.add(marca)

        self._reto_hasta[clave] = time.monotonic() + config.MOTOR_ESPERA_MINUTOS * 60
        self._actualizar_icono_motor()

        consulta = busqueda.consulta_de_reto(qurl.query())
        destino = busqueda.elegir(clave, self._caidos_ahora())
        if destino == clave:
            self.statusBar().showMessage(
                f"{busqueda.nombre(clave)} pide una verificación (CAPTCHA).",
                8000)
            return True

        url = None
        if consulta:
            url, _ = busqueda.url_busqueda(destino, consulta)
        if not url:
            url = motores.obtener(destino).get("url_home")
        if not url:
            return True

        self.statusBar().showMessage(
            f"{busqueda.nombre(clave)} pide CAPTCHA: buscando en "
            f"{busqueda.nombre(destino)}.", 8000)
        print(f"[Búsqueda] {busqueda.nombre(clave)} pide CAPTCHA; "
              f"buscando en {busqueda.nombre(destino)}.", flush=True)
        QTimer.singleShot(0, lambda: view.setUrl(QUrl(url)))

    def _reintentar_con_respaldo(self, view):
        """Si falló la carga de una URL del motor de búsqueda, reintenta la
        misma búsqueda con el motor de respaldo.

        Cubre el caso de que la sonda inicial dijera que el motor va bien y la
        red lo corte después (o un corte intermitente).
        """
        try:
            self._reintentar_con_respaldo_seguro(view)
        except Exception:
            # Nunca dejar que un fallo al reintentar cierre la ventana.
            pass

    def _reintentar_con_respaldo_seguro(self, view):
        if not isinstance(view, QWebEngineView):
            return
        qurl = view.url()
        clave = busqueda.clave_por_host(qurl.host())
        if clave is None:
            return

        # Una sola reintento por pestaña y URL: si el respaldo también falla,
        # no nos quedamos en un bucle de recargas.
        marca = (id(view), qurl.toString())
        if marca in self._respaldo_hecho:
            return

        # Ojo: no basta con mirar self._motores_caidos. Puede que la sonda ya
        # haya marcado el motor como caído mientras esta pestaña cargaba; en
        # ese caso también hay que reintentar.
        # Si el motor está en espera por CAPTCHA, el reto ya se atendió:
        # repetir el aviso de "no responde" solo confunde.
        if clave in self._reto_hasta:
            return

        caidos = self._caidos_ahora() | {clave}
        destino = busqueda.elegir(clave, caidos)
        if destino == clave:
            return

        self._respaldo_hecho.add(marca)
        self._motores_caidos.add(clave)

        consulta = busqueda.consulta_de_reto(qurl.query())
        motor = motores.obtener(destino)
        if consulta:
            url, _ = busqueda.url_busqueda(destino, consulta)
        else:
            url = motor.get("url_home")

        self._actualizar_icono_motor()
        if not url:
            return

        self.statusBar().showMessage(
            f"{busqueda.nombre(clave)} no responde en tu red: "
            f"seguimos con {busqueda.nombre(destino)}.", 8000)
        print(f"[Búsqueda] {busqueda.nombre(clave)} no responde; "
              f"reintentando con {busqueda.nombre(destino)}.", flush=True)

        # Diferido: navegar en pleno manejo de loadFinished es frágil.
        QTimer.singleShot(0, lambda: view.setUrl(QUrl(url)))

    # ---------- TECLADO ----------

    def _ctrl_pulsado(self):
        """True si Ctrl está pulsado ahora mismo (aunque el foco esté en la web)."""
        mods = QApplication.keyboardModifiers()
        return bool(mods & Qt.KeyboardModifier.ControlModifier)

    # ---------- ATAJOS ----------

    def _crear_atajos(self):
        from interfaz.atajos_tabla import ATAJOS_GLOBALES
        for atajo in ATAJOS_GLOBALES:
            secuencia, metodo = atajo[0], atajo[1]
            argumento = atajo[2] if len(atajo) > 2 else None
            acc = QAction(self)
            acc.setShortcut(QKeySequence(secuencia))
            acc.triggered.connect(self._lanzar(metodo, argumento))
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

    def _lanzar(self, nombre, argumento=None):
        """Devuelve una función sin argumentos para conectar a QAction.

        Hace falta el envoltorio: `triggered` manda un bool y algunos métodos
        (como ir_a_pestana) recibirían ese bool como si fuera su parámetro.
        """
        metodo = getattr(self, nombre)
        if argumento is None:
            return lambda: metodo()
        return lambda: metodo(argumento)

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
        # Si la barra de búsqueda está abierta, Esc la cierra primero.
        if self.busqueda.esta_abierta():
            self.busqueda.cerrar()
            return
        v = self.pestana_actual()
        if isinstance(v, QWebEngineView):
            v.stop()
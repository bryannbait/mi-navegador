# estilos.py
# Hoja de estilos QSS y paleta oscura del navegador.
# La usa main.py (aplicar_tema); no depende de la ventana.

from PyQt6.QtGui import QPalette, QColor

from assets.icons.helpers import ruta_icono
import config


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

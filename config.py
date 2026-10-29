# config.py
# Aquí centralizamos los ajustes para no tocar el código cada vez.

# --- Identidad ---
NOMBRE = "MiNavegador"
VERSION = "1.2"

# --- Página de inicio del motor (Ctrl+clic en el botón del motor) ---
HOME = "https://duckduckgo.com"

# --- Paleta del tema: oscuro sobrio + acento violeta ---
# Cambia COLOR_ACENTO* y todo el navegador cambia de color de acento.
COLOR_FONDO         = "#0e0e13"   # fondo general (detrás de las páginas)
COLOR_TOOLBAR       = "#15151c"   # barras superiores
COLOR_SUPERFICIE    = "#1e1e28"   # barra de direcciones, pestaña activa, menús
COLOR_SUPERFICIE_2  = "#2a2a38"   # al pasar el ratón por encima
COLOR_BORDE         = "#2f2f40"   # bordes finos
COLOR_TEXTO         = "#e8e8f2"   # texto principal
COLOR_TEXTO_SUAVE   = "#9b9bb4"   # texto secundario, iconos apagados
COLOR_ACENTO        = "#8b5cf6"   # acento (foco, selección, progreso)
COLOR_ACENTO_SUAVE  = "#a78bfa"   # acento claro (detalles, degradados)
COLOR_ACENTO_FUERTE = "#7c3aed"   # acento oscuro (botón pulsado)
COLOR_OK            = "#4ade80"   # verde: conexión segura, bloqueos
COLOR_AVISO         = "#facc15"   # amarillo: favorito, conexión no segura
COLOR_PELIGRO       = "#f87171"   # rojo: errores
COLOR_INCOGNITO     = "#1a1230"   # fondo de las barras en modo incógnito

# --- Nombres antiguos (por si algún archivo los sigue usando) ---
COLOR_BARRA_FONDO = COLOR_SUPERFICIE
COLOR_BARRA_TEXTO = COLOR_TEXTO
COLOR_BOTON_HOVER = COLOR_SUPERFICIE_2

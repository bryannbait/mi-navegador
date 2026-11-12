# config.py
# Aquí centralizamos los ajustes para no tocar el código cada vez.

# --- Identidad ---
NOMBRE = "MiNavegador"
VERSION = "1.4"

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

# --- Privacidad / anti-fingerprinting (Nivel 10) ---
# Se puede activar o desactivar en caliente desde el menú del escudo.
ANTI_FINGERPRINT = True

# Idioma que ve la web y que mandamos en Accept-Language (deben coincidir).
FP_IDIOMAS = ["es-MX", "es", "en-US", "en"]
FP_ACCEPT_LANGUAGE = "es-MX,es;q=0.9,en-US;q=0.8,en;q=0.7"

# Valores genéricos que sustituyen a los reales de tu equipo.
FP_NUCLEOS = 8          # navigator.hardwareConcurrency
FP_MEMORIA_GB = 8       # navigator.deviceMemory

# Ruido determinista en canvas/WebGL: rompe la huella sin verse a simple vista.
FP_RUIDO_CANVAS = True

# Manda la cabecera Sec-GPC: 1 (Global Privacy Control, "no vendas mis datos").
FP_ENVIAR_GPC = True

# User-Agent que se anuncia a las webs. Si es None, se usa el de QtWebEngine
# limpiado (sin el token QtWebEngine). Poner uno realista de Chrome en Windows
# ayuda a evitar CAPTCHAs en sitios que bloquean navegadores poco comunes.
UA_PERSONALIZADO = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)

# --- Rendimiento: Chromium / QtWebEngine ---
# Flags que se aplican al motor antes de crear la ventana.
# Ayudan a la reproducción de vídeo y al renderizado de páginas pesadas.
CHROMIUM_FLAGS = [
    "--enable-gpu-rasterization",
    "--enable-native-gpu-memory-buffers",
    "--disable-background-timer-throttling",
]

# --- Motor de búsqueda de respaldo ---
# Si el motor elegido no responde (red que corta ese dominio, caída del
# servicio...), las búsquedas se hacen con este en vez de fallar. Se avisa en
# la barra de estado. Pon None para desactivar el respaldo.
MOTOR_RESPALDO = "duckduckgo"

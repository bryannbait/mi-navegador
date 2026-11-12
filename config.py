# config.py
# Aquí centralizamos los ajustes para no tocar el código cada vez.

# --- Identidad ---
NOMBRE = "MiNavegador"
VERSION = "1.4"

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
# Medidos en este equipo: --disable-extensions da ~30 % menos en MiNavegador()
# y --disable-background-networking ~46 % menos en show().
# Ver pruebas/bench_flags.py para la metodología.
CHROMIUM_FLAGS = [
    "--enable-gpu-rasterization",
    "--enable-native-gpu-memory-buffers",
    "--disable-background-timer-throttling",
    "--disable-extensions",
    "--disable-component-extensions-with-background-pages",
    "--disable-default-apps",
    "--disable-background-networking",
    "--renderer-process-limit=2",
    # Solo errores fatales en la consola. Los fallos de red esperados (por
    # ejemplo un motor de búsqueda bloqueado por la red) ya se explican con
    # nuestro propio mensaje; el ruido de Chromium solo asusta.
    "--log-level=3",
]

# --- Motores de búsqueda: orden de preferencia ---
# El primero es el principal. Si no responde (red que corta el dominio, caída
# del servicio...) o devuelve una página de verificación (CAPTCHA), se pasa al
# siguiente. Se avisa en la barra de estado.
# Orden actual: 1.º Brave Search, 2.º Google, 3.º DuckDuckGo (red de seguridad).
MOTORES_RESPALDO = ["google", "duckduckgo"]

# Minutos que se deja de usar un motor que pidió CAPTCHA antes de reintentarlo.
MOTOR_ESPERA_MINUTOS = 20

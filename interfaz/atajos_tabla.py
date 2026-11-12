# atajos_tabla.py
# Tabla única de atajos globales de la ventana.
#
# Vive aparte de navegador.py para que las pruebas puedan comprobar que no
# hay combinaciones repetidas sin crear un QApplication ni una ventana.
#
# Formato de cada entrada: (secuencia, método, [argumento]).
# El método se busca en MiNavegador con getattr().

ATAJOS_GLOBALES = [
    # Dirección y búsqueda
    ("Ctrl+L", "enfocar_barra"),
    ("Ctrl+K", "enfocar_barra"),
    ("Ctrl+F", "abrir_busqueda"),

    # Pestañas
    ("Ctrl+T", "nueva_pestana"),
    ("Ctrl+W", "cerrar_pestana_actual"),
    ("Ctrl+Shift+T", "reabrir_pestana_cerrada"),
    ("Ctrl+Shift+P", "alternar_fijada"),
    ("Ctrl+Tab", "siguiente_pestana"),
    ("Ctrl+Shift+Tab", "pestana_anterior"),
    ("Ctrl+PgDown", "siguiente_pestana"),
    ("Ctrl+PgUp", "pestana_anterior"),

    # Ventanas
    ("Ctrl+Shift+N", "abrir_incognito"),
    ("Ctrl+Shift+W", "cerrar_ventana"),
    ("F11", "alternar_pantalla_completa"),

    # Paneles
    ("Ctrl+J", "abrir_panel_descargas"),
    ("Ctrl+H", "_abrir_ventana_historial"),
    ("Ctrl+Shift+O", "_abrir_ventana_favoritos"),
    ("Ctrl+D", "_toggle_favorito"),

    # Navegación
    ("F5", "recargar_o_detener"),
    ("Ctrl+R", "recargar_o_detener"),
    ("Ctrl+=", "zoom_mas"),
    ("Ctrl+-", "zoom_menos"),
    ("Ctrl+0", "zoom_reset"),
    ("Ctrl+Alt+R", "alternar_lectura"),
    ("Esc", "detener_actual"),
    ("Alt+Left", "atras_actual"),
    ("Alt+Right", "adelante_actual"),
    ("Alt+Home", "inicio_actual"),
]

# Ctrl+1..8 van a esa pestaña; Ctrl+9 a la última (como en Chrome).
for _numero in range(1, 9):
    ATAJOS_GLOBALES.append((f"Ctrl+{_numero}", "ir_a_pestana", _numero - 1))
ATAJOS_GLOBALES.append(("Ctrl+9", "ir_a_pestana", -1))

# ---------- NORMALIZACIÓN (sin Qt) ----------

_ORDEN_MODIFICADORES = ("Ctrl", "Alt", "Shift", "Meta")

_ALIAS_MODIFICADOR = {
    "ctrl": "Ctrl", "control": "Ctrl", "ctl": "Ctrl",
    "alt": "Alt",
    "shift": "Shift", "mayus": "Shift", "mayús": "Shift",
    "meta": "Meta", "win": "Meta", "super": "Meta", "cmd": "Meta",
}

_ALIAS_TECLA = {
    "esc": "Esc", "escape": "Esc",
    "intro": "Return", "enter": "Return", "return": "Return",
    "del": "Delete", "delete": "Delete", "supr": "Delete",
    "pgdown": "PgDown", "avpag": "PgDown", "pagedown": "PgDown",
    "pgup": "PgUp", "repag": "PgUp", "pageup": "PgUp",
    "inicio": "Home", "home": "Home",
    "fin": "End", "end": "End",
    "espacio": "Space", "space": "Space",
    "izquierda": "Left", "derecha": "Right",
    "arriba": "Up", "abajo": "Down",
}


def _tecla_canonica(tecla):
    """Una letra sola se escribe en mayúscula; los símbolos se dejan igual."""
    if len(tecla) == 1 and tecla.isalpha():
        return tecla.upper()
    return tecla


def normalizar(secuencia):
    """Devuelve la secuencia en forma canónica, para comparar atajos.

    Ordena los modificadores y unifica alias (Control -> Ctrl, Sup -> Delete).
    No importa Qt a propósito: es una función de texto pura.
    """
    modificadores = set()
    tecla = ""

    for parte in secuencia.split("+"):
        if not parte.strip():
            # "Ctrl++" se parte en ["Ctrl", "", ""]: el hueco es la tecla "+".
            tecla = "+"
            continue
        clave = parte.strip().lower()
        if clave in _ALIAS_MODIFICADOR:
            modificadores.add(_ALIAS_MODIFICADOR[clave])
        else:
            tecla = _ALIAS_TECLA.get(clave) or _tecla_canonica(parte.strip())

    ordenados = [m for m in _ORDEN_MODIFICADORES if m in modificadores]
    if not ordenados:
        return tecla
    return "+".join(ordenados + [tecla])


def secuencias():
    """Lista de secuencias normalizadas, en orden de la tabla."""
    return [normalizar(sec) for sec, *_ in ATAJOS_GLOBALES]


def colisiones():
    """Devuelve {secuencia: [métodos]} solo para las repetidas."""
    vistas = {}
    for secuencia, metodo, *_ in ATAJOS_GLOBALES:
        vistas.setdefault(normalizar(secuencia), []).append(metodo)
    return {s: m for s, m in vistas.items() if len(m) > 1}

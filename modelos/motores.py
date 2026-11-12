# motores.py
# Catálogo de motores de búsqueda y atajos (bangs).


# Cada motor tiene:
#   nombre          -> para mostrar en el menú
#   icono           -> un emoji que lo representa (lo ponemos en el botón)
#   url_busqueda    -> plantilla; {q} se reemplaza por la consulta URL-encoded
#   url_sugerencias -> plantilla para autocompletado; None si no hay API pública
#   bang            -> atajo corto (se escribe al inicio de la barra)
MOTORES = {
    "duckduckgo": {
        "nombre": "DuckDuckGo",
        "icono": "🦆",
        "url_busqueda": "https://duckduckgo.com/?q={q}",
        "url_sugerencias": "https://duckduckgo.com/ac/?q={q}&type=list",
        "url_home": "https://duckduckgo.com",
        "bang": "!ddg",
    },
    "brave": {
        "nombre": "Brave Search",
        "icono": "🦁",
        "url_busqueda": "https://search.brave.com/search?q={q}",
        "url_sugerencias": None,
        "url_home": "https://search.brave.com",
        "bang": "!b",
    },
    "startpage": {
        "nombre": "Startpage",
        "icono": "🛡️",
        "url_busqueda": "https://www.startpage.com/sp/search?query={q}",
        "url_sugerencias": None,
        "url_home": "https://www.startpage.com",
        "bang": "!s",
    },
    "google": {
        "nombre": "Google",
        "icono": "🔍",
        "url_busqueda": "https://www.google.com/search?q={q}",
        "url_sugerencias": "https://suggestqueries.google.com/complete/search?client=firefox&q={q}",
        "url_home": "https://www.google.com",
        "bang": "!g",
    },
    "ecosia": {
        "nombre": "Ecosia",
        "icono": "🌳",
        "url_busqueda": "https://www.ecosia.org/search?q={q}",
        "url_sugerencias": None,
        "url_home": "https://www.ecosia.org",
        "bang": "!e",
    },
    "bing": {
        "nombre": "Bing",
        "icono": "🅱️",
        "url_busqueda": "https://www.bing.com/search?q={q}",
        "url_sugerencias": None,
        "url_home": "https://www.bing.com",
        "bang": "!bi",
    },
    "wikipedia": {
        "nombre": "Wikipedia",
        "icono": "📚",
        "url_busqueda": "https://es.wikipedia.org/w/index.php?search={q}",
        "url_sugerencias": "https://es.wikipedia.org/w/api.php?action=opensearch&format=json&limit=8&search={q}",
        "url_home": "https://es.wikipedia.org",
        "bang": "!w",
    },
}

# Bangs "extra" que no tienen motor en el menú, pero sirven para saltar
# rápidamente a un sitio. No se pueden elegir como motor principal.
BANGS_EXTRA = {
    "!yt": "https://www.youtube.com/results?search_query={q}",
    "!gh": "https://github.com/search?q={q}",
    "!so": "https://stackoverflow.com/search?q={q}",
    "!mdn": "https://developer.mozilla.org/es/search?q={q}",
    "!npm": "https://www.npmjs.com/search?q={q}",
    "!pypi": "https://pypi.org/search/?q={q}",
}


def buscar_bang(texto):
    """
    Si el texto empieza por un bang conocido, devuelve:
        (url_plantilla, consulta_restante)
    Si no, devuelve (None, None).
    """
    if not texto.startswith("!"):
        return None, None

    partes = texto.split(maxsplit=1)
    if len(partes) < 2:
        return None, None

    posible_bang = partes[0].lower()
    consulta = partes[1]

    # ¿Es un motor del menú?
    for motor in MOTORES.values():
        if motor["bang"] == posible_bang:
            return motor["url_busqueda"], consulta

    # ¿Es un bang extra?
    if posible_bang in BANGS_EXTRA:
        return BANGS_EXTRA[posible_bang], consulta

    return None, None


def motor_por_defecto():
    return "duckduckgo"


def obtener(clave):
    """Devuelve el dict del motor o el de por defecto si no existe."""
    return MOTORES.get(clave, MOTORES[motor_por_defecto()])
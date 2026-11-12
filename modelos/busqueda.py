# busqueda.py
# Elige con qué motor se hace una búsqueda cuando el elegido no responde.
#
# Hay redes (y algunos proveedores) que cortan un dominio concreto: la
# conexión se reinicia en pleno saludo TLS y ningún navegador puede cargarlo
# (le pasa igual a Brave, Chrome o al nuestro). En vez de dejar la búsqueda
# muerta, se usa el motor de respaldo de config y se avisa en la barra de
# estado.
#
# Este módulo es lógica pura (sin Qt) para poder probarlo sin abrir ventanas.

from urllib.parse import parse_qs, quote

import config
from modelos import motores


def nombre(clave):
    """Nombre visible de un motor (o la propia clave si no existe)."""
    motor = motores.MOTORES.get(clave)
    return motor["nombre"] if motor else str(clave)


def elegir(motor_actual, caidos):
    """Clave del motor que se usará de verdad.

    Si el elegido está caído se recorre config.MOTORES_RESPALDO en orden. Si
    ninguno sirve se devuelve el original: es mejor intentarlo que no buscar.
    """
    if motor_actual not in caidos:
        return motor_actual

    for respaldo in config.MOTORES_RESPALDO:
        if respaldo != motor_actual and respaldo not in caidos:
            return respaldo
    return motor_actual


def url_busqueda(motor_actual, consulta, caidos=()):
    """Devuelve (url, clave_usada) para buscar la consulta."""
    clave = elegir(motor_actual, caidos)
    url = motores.obtener(clave)["url_busqueda"].format(q=quote(consulta))
    return url, clave


def host_de(plantilla):
    """Host de una plantilla de URL ('https://x.com/?q={q}' -> 'x.com')."""
    resto = plantilla.split("://", 1)[-1]
    return resto.split("/", 1)[0].split("?", 1)[0].lower()


def clave_por_host(host, catalogo=None):
    """Qué motor corresponde a ese host, o None si es un sitio cualquiera."""
    host = (host or "").lower()
    if not host:
        return None
    for clave, motor in (catalogo or motores.MOTORES).items():
        for campo in ("url_home", "url_busqueda", "url_sugerencias"):
            plantilla = motor.get(campo)
            if plantilla and host_de(plantilla) == host:
                return clave
    return None


def consulta_de(query):
    """Saca el término buscado de la query de una URL de resultados."""
    valores = parse_qs((query or "").lstrip("?"))
    for campo in ("q", "query"):
        if valores.get(campo):
            return valores[campo][0]
    return ""


# Rutas donde un motor pone su página de "demuestra que no eres un robot".
PATRONES_RETO = {
    "google": ("/sorry", "enablejs"),
}


def es_reto(host, ruta, catalogo=None):
    """Clave del motor si esa URL es su página de verificación (CAPTCHA).

    Google redirige a /sorry/index cuando desconfía del navegador. No es un
    fallo de red: el dominio responde, pero no da resultados. Se aceptan los
    subdominios del motor (www.google.com, consent.google.com...).
    """
    host = (host or "").lower()
    ruta = (ruta or "").lower()
    if not host:
        return None

    catalogo = catalogo or motores.MOTORES
    for clave, patrones in PATRONES_RETO.items():
        motor = catalogo.get(clave)
        if not motor:
            continue
        base = host_de(motor["url_busqueda"])
        if base.startswith("www."):
            base = base[4:]
        if host != base and not host.endswith("." + base):
            continue
        for patron in patrones:
            if patron in ruta:
                return clave
    return None


def consulta_de_reto(query):
    """Consulta original escondida en el parámetro continue= del reto.

    Google manda /sorry/index?continue=https://www.google.com/search?q=youtube
    para poder devolverte a los resultados una vez resuelto el captcha.
    """
    valores = parse_qs((query or "").lstrip("?"))
    for destino in valores.get("continue", []):
        partes = destino.split("?", 1)
        if len(partes) == 2:
            consulta = consulta_de(partes[1])
            if consulta:
                return consulta
    return consulta_de(query)

# pagina_inicio.py
# Página de inicio propia (la que se ve al abrir una pestaña nueva).
# Es HTML sencillo generado aquí: sin recursos externos, sin trackers.
# La búsqueda se envía a Python con una dirección especial (ver
# puente_vim.PaginaVim) y es el navegador quien decide a qué motor ir.

import html
from datetime import datetime

import config

# Dirección "inventada" que PaginaVim intercepta (el .invalid nunca existe).
PREFIJO_BUSQUEDA = "https://buscar.minavegador.invalid/"

_CSS = """
*{box-sizing:border-box;margin:0}
html,body{height:100%}
html{background:%(fondo)s}
body{background:radial-gradient(1200px 600px at 50% -10%,%(fondo2)s 0%,transparent 70%);
 color:%(texto)s;font-family:"Segoe UI",system-ui,-apple-system,Roboto,sans-serif;
 display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px}
.hora{font-size:84px;font-weight:200;letter-spacing:-2px;line-height:1}
.fecha{color:%(suave)s;font-size:15px;margin-top:8px}
.fecha::first-letter{text-transform:uppercase}
.saludo{font-size:20px;margin:28px 0 18px;color:%(texto)s}
.saludo b{color:%(acento_suave)s;font-weight:600}
form{width:min(620px,92vw)}
.caja{display:flex;align-items:center;gap:12px;background:%(superficie)s;
 border:1px solid %(borde)s;border-radius:999px;padding:0 22px;height:54px;
 transition:border-color .15s,box-shadow .15s}
.caja:focus-within{border-color:%(acento)s;box-shadow:0 0 0 4px %(acento_halo)s}
.caja svg{flex:none;stroke:%(suave)s}
input{flex:1;background:none;border:0;outline:0;color:%(texto)s;font-size:16px;font-family:inherit}
input::placeholder{color:%(suave)s}
.accesos{display:flex;flex-wrap:wrap;justify-content:center;gap:14px;margin-top:44px;max-width:720px}
.acceso{width:92px;text-decoration:none;color:%(texto)s;text-align:center;font-size:12px}
.icono{width:56px;height:56px;margin:0 auto 8px;border-radius:16px;background:%(superficie)s;
 border:1px solid %(borde)s;display:flex;align-items:center;justify-content:center;
 font-size:22px;font-weight:600;transition:transform .12s,border-color .12s,background .12s}
.acceso:hover .icono{transform:translateY(-3px);border-color:%(acento)s;background:%(superficie2)s}
.acceso span{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:%(suave)s}
.vacio{margin-top:44px;color:%(suave)s;font-size:13px}
.pie{position:fixed;bottom:16px;color:%(suave)s;font-size:12px;opacity:.7}
.inc{display:inline-block;margin-bottom:18px;padding:6px 14px;border-radius:999px;
 background:%(acento_halo)s;color:%(acento_suave)s;font-size:13px}
"""

_ICONO_LUPA = (
    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/>'
    '<path d="m21 21-4.3-4.3"/></svg>'
)

_JS = """
var DIAS=['domingo','lunes','martes','miércoles','jueves','viernes','sábado'];
var MESES=['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
function p(n){return n<10?'0'+n:''+n}
function reloj(){var d=new Date();
 document.getElementById('hora').textContent=p(d.getHours())+':'+p(d.getMinutes());
 document.getElementById('fecha').textContent=DIAS[d.getDay()]+', '+d.getDate()+' de '+MESES[d.getMonth()];}
reloj();setInterval(reloj,10000);
document.getElementById('f').addEventListener('submit',function(e){
 e.preventDefault();var q=document.getElementById('q').value.trim();
 if(q)location.href='%(prefijo)s?q='+encodeURIComponent(q);});
document.getElementById('q').focus();
"""


def _saludo():
    h = datetime.now().hour
    if h < 6:
        return "Buenas noches"
    if h < 13:
        return "Buenos días"
    if h < 20:
        return "Buenas tardes"
    return "Buenas noches"


def _inicial(titulo, url):
    for c in (titulo or url or "?"):
        if c.isalnum():
            return c.upper()
    return "?"


def generar_html(favoritos, motor_nombre, incognito=False):
    """HTML de la página de inicio. `favoritos`: lista de dicts titulo/url."""
    c = config
    colores = {
        "fondo": c.COLOR_INCOGNITO if incognito else c.COLOR_FONDO,
        "fondo2": c.COLOR_ACENTO_FUERTE + "33",
        "superficie": c.COLOR_SUPERFICIE, "superficie2": c.COLOR_SUPERFICIE_2,
        "borde": c.COLOR_BORDE, "texto": c.COLOR_TEXTO, "suave": c.COLOR_TEXTO_SUAVE,
        "acento": c.COLOR_ACENTO, "acento_suave": c.COLOR_ACENTO_SUAVE,
        "acento_halo": c.COLOR_ACENTO + "33",
    }
    css = _CSS
    for k, v in colores.items():
        css = css.replace("%(" + k + ")s", v)

    if incognito:
        cuerpo_extra = '<div class="inc">Navegación privada</div>'
        accesos = ('<p class="vacio">En incógnito no se guardan favoritos, '
                   'historial ni descargas.</p>')
    else:
        cuerpo_extra = ""
        tiles = []
        for f in favoritos[:8]:
            url = f.get("url", "")
            if not url.startswith(("http://", "https://")):
                continue
            titulo = f.get("titulo") or url
            tiles.append(
                '<a class="acceso" href="%s" title="%s"><div class="icono">%s</div>'
                '<span>%s</span></a>' % (
                    html.escape(url, quote=True), html.escape(url, quote=True),
                    html.escape(_inicial(titulo, url)), html.escape(titulo))
            )
        if tiles:
            accesos = '<div class="accesos">' + "".join(tiles) + "</div>"
        else:
            accesos = ('<p class="vacio">Aún no tienes favoritos. '
                       'Pulsa ☆ en la barra (o Ctrl+D) y aparecerán aquí.</p>')

    js = _JS.replace("%(prefijo)s", PREFIJO_BUSQUEDA)
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        "<title>Nueva pestaña</title><style>" + css + "</style></head><body>"
        + cuerpo_extra +
        '<div class="hora" id="hora">--:--</div><div class="fecha" id="fecha"></div>'
        '<div class="saludo"><b>' + _saludo() + '</b></div>'
        '<form id="f" autocomplete="off"><div class="caja">' + _ICONO_LUPA +
        '<input id="q" type="text" placeholder="Buscar con ' + html.escape(motor_nombre) +
        ' o escribir una dirección"></div></form>' + accesos +
        '<div class="pie">' + html.escape(c.NOMBRE) + " " + html.escape(c.VERSION) + "</div>"
        "<script>" + js + "</script></body></html>"
    )

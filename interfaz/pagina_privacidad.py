# pagina_privacidad.py
# Página local de diagnóstico de privacidad (Nivel 10).
#
# Se genera aquí, sin red: la propia página lee lo que la web puede ver y lo
# pinta en una tabla. Sirve para comparar con el escudo activado y desactivado
# (desactivarlo en el menú del escudo y recargar).

import config


_CABECERA = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>Privacidad · __NOMBRE__</title>
<style>
  :root { color-scheme: dark; }
  body {
    background: __FONDO__; color: __TEXTO__; margin: 0; padding: 40px 24px;
    font-family: "Segoe UI", system-ui, sans-serif;
  }
  main { max-width: 760px; margin: 0 auto; }
  h1 { font-size: 22px; margin: 0 0 6px 0; }
  .sub { color: __SUAVE__; font-size: 13px; margin-bottom: 22px; }
  .estado {
    display: inline-block; padding: 4px 12px; border-radius: 999px;
    font-size: 13px; font-weight: 600; margin-bottom: 22px;
    color: __ESTADO_COLOR__; border: 1px solid __ESTADO_COLOR__;
  }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid __BORDE__; }
  th { color: __SUAVE__; font-weight: 600; width: 45%; }
  td { font-family: ui-monospace, Consolas, monospace; word-break: break-word; }
  .nota {
    margin-top: 24px; padding: 14px 16px; border-radius: 10px;
    background: __SUPERFICIE__; color: __SUAVE__; font-size: 12px;
    line-height: 1.6;
  }
  button {
    margin-top: 20px; padding: 8px 16px; border-radius: 8px; cursor: pointer;
    border: 1px solid __BORDE__; background: __SUPERFICIE__; color: __TEXTO__;
  }
</style></head>
<body><main>
  <h1>Qué ve una web de ti</h1>
  <div class="sub">Página local: no se envía nada a ninguna red.</div>
  <div class="estado">Huella: __ESTADO__</div>
  <table><tbody id="tabla"></tbody></table>
  <button onclick="location.reload()">Recargar</button>
  <div class="nota">
    Si el escudo está activo, los valores deben ser genéricos: 8 núcleos,
    8 GB de memoria, 1920×1080, idioma es-MX y un canvas distinto en cada
    arranque del navegador. Desactívalo en el menú del escudo y recarga para
    ver la diferencia. Lo que no se puede ocultar desde la página (zona
    horaria, fuentes y algunas lecturas de WebGL) aparece tal cual.
  </div>
</main>
<script>
(function () {
  const filas = [];
  function fila(nombre, valor) {
    filas.push([nombre, String(valor)]);
  }

  function hash(texto) {
    let h = 2166136261;
    for (let i = 0; i < texto.length; i++) {
      h ^= texto.charCodeAt(i);
      h = Math.imul(h, 16777619) >>> 0;
    }
    return h.toString(16);
  }

  function huellaCanvas() {
    const c = document.createElement("canvas");
    c.width = 240; c.height = 60;
    const ctx = c.getContext("2d");
    if (!ctx) return "sin canvas";
    ctx.textBaseline = "top";
    ctx.font = "16px Arial";
    ctx.fillStyle = "#f60";
    ctx.fillRect(10, 10, 100, 30);
    ctx.fillStyle = "#069";
    ctx.fillText("huella de prueba 123", 12, 14);
    return hash(c.toDataURL());
  }

  function tarjetaGrafica() {
    const c = document.createElement("canvas");
    const gl = c.getContext("webgl") || c.getContext("experimental-webgl");
    if (!gl) return "sin WebGL";
    const ext = gl.getExtension("WEBGL_debug_renderer_info");
    const proveedor = gl.getParameter(
      ext ? ext.UNMASKED_VENDOR_WEBGL : gl.VENDOR);
    const modelo = gl.getParameter(
      ext ? ext.UNMASKED_RENDERER_WEBGL : gl.RENDERER);
    return proveedor + " · " + modelo;
  }

  fila("navigator.userAgent", navigator.userAgent);
  fila("navigator.platform", navigator.platform);
  fila("navigator.vendor", navigator.vendor);
  fila("Idioma", navigator.language);
  fila("Idiomas", (navigator.languages || []).join(", "));
  fila("Núcleos (hardwareConcurrency)", navigator.hardwareConcurrency);
  fila("Memoria GB (deviceMemory)",
       navigator.deviceMemory === undefined ? "no disponible"
                                            : navigator.deviceMemory);
  fila("Puntos táctiles (maxTouchPoints)", navigator.maxTouchPoints);
  fila("WebDriver", navigator.webdriver);
  fila("GPC (globalPrivacyControl)",
       navigator.globalPrivacyControl === undefined
         ? "no disponible" : navigator.globalPrivacyControl);
  fila("Do Not Track", navigator.doNotTrack);
  fila("Marcas (userAgentData)",
       navigator.userAgentData && navigator.userAgentData.brands
         ? navigator.userAgentData.brands
             .map(function (b) { return b.brand + " " + b.version; })
             .join(", ")
         : "no disponible");
  fila("Plataforma (userAgentData)",
       navigator.userAgentData ? navigator.userAgentData.platform
                               : "no disponible");
  fila("Pantalla", screen.width + " × " + screen.height);
  fila("Área disponible", screen.availWidth + " × " + screen.availHeight);
  fila("Profundidad de color", screen.colorDepth);
  fila("Escala (devicePixelRatio)", window.devicePixelRatio);
  fila("Zona horaria",
       Intl.DateTimeFormat().resolvedOptions().timeZone || "no disponible");
  fila("Zona horaria (desfase, min)", new Date().getTimezoneOffset());
  fila("Idioma de Intl",
       Intl.DateTimeFormat().resolvedOptions().locale);
  fila("Complementos (plugins)", navigator.plugins.length);
  fila("Hash del canvas", huellaCanvas());
  fila("WebGL", tarjetaGrafica());

  const cuerpo = document.getElementById("tabla");
  for (const [nombre, valor] of filas) {
    const tr = document.createElement("tr");
    const th = document.createElement("th");
    th.textContent = nombre;
    const td = document.createElement("td");
    td.textContent = valor;
    tr.appendChild(th);
    tr.appendChild(td);
    cuerpo.appendChild(tr);
  }
})();
</script>
</body></html>
"""


def generar_html(activo):
    """HTML completo. `activo` = si el escudo anti-fingerprinting está puesto."""
    estado = "protegida" if activo else "expuesta"
    color = config.COLOR_OK if activo else config.COLOR_AVISO
    reemplazos = {
        "__NOMBRE__": config.NOMBRE,
        "__FONDO__": config.COLOR_FONDO,
        "__TEXTO__": config.COLOR_TEXTO,
        "__SUAVE__": config.COLOR_TEXTO_SUAVE,
        "__BORDE__": config.COLOR_BORDE,
        "__SUPERFICIE__": config.COLOR_SUPERFICIE,
        "__ESTADO__": estado,
        "__ESTADO_COLOR__": color,
    }
    html = _CABECERA
    for clave, valor in reemplazos.items():
        html = html.replace(clave, valor)
    return html

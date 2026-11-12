# modo_lectura.py
# Modo lectura: extrae el artículo principal de una página y lo muestra en un
# overlay reversible, sin librerías ni red.
#
# Se inyecta un objeto `window.MnLector` en cada página (mundo principal de JS,
# antes de que la web ejecute). Desde Python lo llamamos con runJavaScript.
#
# Heurística propia (sin Readability):
#   1. <article>, luego <main>, luego [role=main].
#   4. Si nada de eso, puntúa bloques <section>/<div> por tamaño de texto y
#      cantidad de párrafos; gana el de mayor puntaje (mín. 2 párrafos y
#      300 caracteres).
#
# No se persiste: al recargar o cerrar la pestaña se sale del modo lectura.

from PyQt6.QtWebEngineCore import QWebEngineScript

import config

NOMBRE_SCRIPT = "modo_lectura"
ID_ESCRITURA = "mn-lector"


CSS_LECTOR = """
#mn-lector {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: __FONDO__; color: __TEXTO__; z-index: 2147483647;
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  font-size: 18px; line-height: 1.75;
  padding: 46px 64px 64px 64px; box-sizing: border-box;
  overflow: auto;
}
#mn-lector #mn-lector-salir {
  position: fixed; top: 16px; right: 20px; z-index: 2147483648;
  background: __ACENTO__; color: white; border: none; border-radius: 8px;
  padding: 8px 16px; font-size: 14px; cursor: pointer;
  box-shadow: 0 2px 6px rgba(0,0,0,0.35);
}
#mn-lector #mn-lector-salir:hover { background: __ACENTO_FUERTE__; }
#mn-lector #mn-lector-contenido {
  max-width: 740px; margin: 0 auto;
}
#mn-lector #mn-lector-contenido * { color: __TEXTO__ !important; }
#mn-lector #mn-lector-contenido p { margin: 1.1em 0; }
#mn-lector #mn-lector-contenido h1,
#mn-lector #mn-lector-contenido h2,
#mn-lector #mn-lector-contenido h3 {
  color: __ACENTO_SUAVE__; margin: 1.5em 0 0.7em 0;
}
#mn-lector #mn-lector-contenido h1 { font-size: 30px; }
#mn-lector #mn-lector-contenido h2 { font-size: 24px; }
#mn-lector #mn-lector-contenido h3 { font-size: 20px; }
#mn-lector #mn-lector-contenido a { color: __ACENTO__; text-decoration: underline; }
#mn-lector #mn-lector-contenido img { max-width: 100%; height: auto; }
#mn-lector #mn-lector-contenido blockquote {
  border-left: 3px solid __ACENTO__; margin: 1em 0; padding-left: 14px;
  color: __TEXTO_SUAVE__;
}
"""

JS_LECTOR = r"""
(function () {
    if (window.MnLector) return;
    var ID = "mn-lector";
    var MnLector = {
        activo: false,
        original: null,
        overlay: null,

        activar: function () {
            if (this.activo) return true;
            var articulo = this._encontrar();
            if (!articulo) {
                try {
                    document.dispatchEvent(new CustomEvent("mn-lector-sin-articulo"));
                } catch (e) {}
                return false;
            }
            // Clonamos el articulo en el overlay sin tocar el original.
            // Las operaciones del DOM van en setTimeout para evitar reentrancia
            // con el motor de Qt al inyectar el script desde Python.
            var copia = articulo.cloneNode(true);
            var self = this;
            setTimeout(function () {
                var overlay = document.createElement("div");
                overlay.id = ID;
                overlay.innerHTML = (
                    '<button id="mn-lector-salir" onclick="window.MnLector && window.MnLector.desactivar()">Salir</button>' +
                    '<div id="mn-lector-contenido"></div>'
                );
                var cont = overlay.querySelector("#mn-lector-contenido");
                cont.appendChild(copia);
                document.body.appendChild(overlay);
                self.overlay = overlay;
                self.activo = true;
                self._aplicarEstilos();
            }, 0);
            return true;
        },

        desactivar: function () {
            if (!this.activo) return true;
            var self = this;
            setTimeout(function () {
                if (self.overlay && self.overlay.parentNode) {
                    self.overlay.parentNode.removeChild(self.overlay);
                }
                self.overlay = null;
                self.activo = false;
            }, 0);
            return true;
        },

        alternar: function () {
            return this.activo ? this.desactivar() : this.activar();
        },

        esta_activo: function () {
            return this.activo;
        },

        _aplicarEstilos: function () {
            var estilo = document.createElement("style");
            estilo.textContent = __CSS__;
            var head = document.head || document.documentElement;
            head.insertBefore(estilo, head.firstChild);
        },

        _puntos: function (bloque) {
            var ps = bloque.getElementsByTagName("p");
            var texto = bloque.textContent || "";
            var largo = texto.length;
            if (largo < 300 || ps.length < 2) return -1;
            return ps.length * 12 + Math.min(largo, 3000) / 250;
        },

        _encontrar: function () {
            var selectores = ["article", "main", "[role=main]"];
            for (var i = 0; i < selectores.length; i++) {
                var candidato = document.querySelector(selectores[i]);
                if (candidato && this._puntos(candidato) >= 0) {
                    return candidato;
                }
            }
            var bloques = document.querySelectorAll("section, div");
            var mejor = null;
            var mejorPuntos = -1;
            for (var i = 0; i < bloques.length; i++) {
                var puntos = this._puntos(bloques[i]);
                if (puntos > mejorPuntos) {
                    mejor = bloques[i];
                    mejorPuntos = puntos;
                }
            }
            return mejor;
        }
    };
    window.MnLector = MnLector;
})();
"""


def js_literal(texto):
    """Convierte un texto en un string literal de JS (comilla simple, escapado)."""
    return "'" + texto.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n") + "'"


def generar_js():
    """Devuelve el JS con el CSS ya embebido (colores del tema)."""
    css = (CSS_LECTOR
           .replace("__FONDO__", config.COLOR_FONDO)
           .replace("__TEXTO__", config.COLOR_TEXTO)
           .replace("__TEXTO_SUAVE__", config.COLOR_TEXTO_SUAVE)
           .replace("__ACENTO__", config.COLOR_ACENTO)
           .replace("__ACENTO_FUERTE__", config.COLOR_ACENTO_FUERTE)
           .replace("__ACENTO_SUAVE__", config.COLOR_ACENTO_SUAVE))
    return JS_LECTOR.replace("__CSS__", js_literal(css))


def generar_css():
    """Devuelve el CSS del modo lectura con los colores del tema (crudo)."""
    return (CSS_LECTOR
            .replace("__FONDO__", config.COLOR_FONDO)
            .replace("__TEXTO__", config.COLOR_TEXTO)
            .replace("__TEXTO_SUAVE__", config.COLOR_TEXTO_SUAVE)
            .replace("__ACENTO__", config.COLOR_ACENTO)
            .replace("__ACENTO_FUERTE__", config.COLOR_ACENTO_FUERTE)
            .replace("__ACENTO_SUAVE__", config.COLOR_ACENTO_SUAVE))


def crear_script():
    """Devuelve un QWebEngineScript listo para registrar en un perfil."""
    script = QWebEngineScript()
    script.setName(NOMBRE_SCRIPT)
    script.setSourceCode(generar_js())
    script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
    script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
    script.setRunsOnSubFrames(False)
    return script


# Heuristica de busqueda de articulo (JS). Se reutiliza en el overlay inyectado
# desde Python para no depender de un objeto global compartido entre mundos.
# Usa comillas simples para poder incrustarse en strings de Python.
JS_BUSCAR_ARTICULO = r"""
var _puntos = function (bloque) {
    var ps = bloque.getElementsByTagName('p');
    var texto = bloque.textContent || '';
    var largo = texto.length;
    if (largo < 300 || ps.length < 2) return -1;
    return ps.length * 12 + Math.min(largo, 3000) / 250;
};
var _encontrar = function () {
    var selectores = ['article', 'main', '[role=main]'];
    for (var i = 0; i < selectores.length; i++) {
        var candidato = document.querySelector(selectores[i]);
        if (candidato && _puntos(candidato) >= 0) {
            return candidato;
        }
    }
    var bloques = document.querySelectorAll('section, div');
    var mejor = null;
    var mejorPuntos = -1;
    for (var i = 0; i < bloques.length; i++) {
        var puntos = _puntos(bloques[i]);
        if (puntos > mejorPuntos) {
            mejor = bloques[i];
            mejorPuntos = puntos;
        }
    }
    return mejor;
};
"""

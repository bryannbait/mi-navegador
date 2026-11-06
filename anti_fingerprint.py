# anti_fingerprint.py
# Nivel 10: anti-fingerprinting (contra la "huella digital").
#
# ¿Qué es la huella? Cada web puede pedirle al navegador decenas de datos
# (resolución, tarjeta gráfica, canvas, idiomas, núcleos...) y combinarlos
# para reconocerte aunque borres cookies. Aquí normalizamos esos datos:
# todas las webs ven un perfil común y aburrido, no el tuyo.
#
# Dos capas:
#   1. Cabeceras HTTP: User-Agent sin "QtWebEngine" y Accept-Language.
#   2. Script JS inyectado en cada página (mundo principal, antes que el
#      código de la web) que reescribe las APIs que usa el fingerprinting.
#
# Límites conocidos (documentados en PRIVACIDAD.md): zona horaria, fuentes
# instaladas y algunas lecturas de WebGL no se pueden camuflar desde JS.

import json
import re
import secrets

from PyQt6.QtWebEngineCore import QWebEngineScript

import config


NOMBRE_SCRIPT = "privacidad_huella"

# Una sal distinta por ejecución: el "ruido" del canvas cambia cada vez que
# abres el navegador, pero se mantiene estable dentro de la misma sesión
# (si cambiara en cada recarga, rompería webs que usan canvas de verdad).
SAL_SESION = secrets.randbits(32)


# ---------------------------------------------------------------------------
# USER-AGENT Y CABECERAS
# ---------------------------------------------------------------------------

def limpiar_user_agent(ua):
    """Quita el token 'QtWebEngine/x.y' del UA por defecto de Qt.

    Así el navegador se presenta como Chrome normal, sin mentir sobre la
    versión: conservamos la versión real de Chromium que trae Qt (hoy 140),
    en vez de fijar una a mano que envejece mal.
    """
    if config.UA_PERSONALIZADO:
        return config.UA_PERSONALIZADO
    limpio = re.sub(r"\s*QtWebEngine/[\d.]+", "", ua or "")
    return limpio.strip() or ua


def cabecera_client_hints(ua):
    """Sec-CH-UA que debe coincidir con navigator.userAgentData del JS.

    Chromium manda por defecto solo la marca 'Chromium'. Si el UA dice
    Chrome y el JS anuncia Google Chrome, la cabecera tiene que decir lo
    mismo o la incoherencia se nota desde el servidor.
    """
    coincidencia = re.search(r"Chrome/(\d+)", ua or "")
    version = coincidencia.group(1) if coincidencia else "140"
    texto = (
        f'"Chromium";v="{version}", "Google Chrome";v="{version}", '
        f'"Not=A?Brand";v="24"'
    )
    return texto.encode("ascii")


def plataforma_js(ua):
    """Valor de navigator.platform coherente con el UA."""
    ua = ua or ""
    if "Windows" in ua:
        return "Win32"
    if "Macintosh" in ua or "Mac OS X" in ua:
        return "MacIntel"
    if "Android" in ua:
        return "Linux armv8l"
    return "Linux x86_64"


def plataforma_ua(ua):
    """Valor de navigator.userAgentData.platform coherente con el UA."""
    ua = ua or ""
    if "Windows" in ua:
        return "Windows"
    if "Macintosh" in ua or "Mac OS X" in ua:
        return "macOS"
    if "Android" in ua:
        return "Android"
    return "Linux"


# ---------------------------------------------------------------------------
# SCRIPT JS
# ---------------------------------------------------------------------------

_JS = r"""
(function () {
    'use strict';
    if (window.__huellaProtegida) return;
    window.__huellaProtegida = true;

    var SAL = __SAL__;
    var IDIOMAS = __IDIOMAS__;
    var IDIOMA = __IDIOMA__;
    var PLATAFORMA_JS = __PLATAFORMA_JS__;
    var PLATAFORMA_UA = __PLATAFORMA_UA__;
    var NUCLEOS = __NUCLEOS__;
    var MEMORIA = __MEMORIA__;
    var RUIDO_CANVAS = __RUIDO_CANVAS__;

    // ---------- utilidades ----------

    function hashTexto(texto) {
        // FNV-1a de 32 bits: barato y suficiente para repartir semillas.
        var h = 2166136261;
        for (var i = 0; i < texto.length; i++) {
            h ^= texto.charCodeAt(i);
            h = Math.imul(h, 16777619);
        }
        return h >>> 0;
    }

    // Semilla distinta por sitio: el ruido de una web no sirve para
    // correlacionarte con otra, y el mismo sitio siempre da el mismo ruido.
    var SEMILLA = (hashTexto(location.hostname || 'local') ^ SAL) >>> 0;

    function definir(proto, prop, valor) {
        try {
            Object.defineProperty(proto, prop, {
                get: function () { return valor; },
                configurable: true,
                enumerable: true
            });
        } catch (e) { /* propiedad no configurable: la dejamos como está */ }
    }

    // ---------- Client Hints coherentes con el UA ----------

    if ('userAgentData' in navigator) {
        var mayor = (navigator.userAgent.match(/Chrome\/(\d+)/) || [])[1] || '140';
        var completa = mayor + '.0.0.0';
        var marcas = [
            { brand: 'Chromium', version: mayor },
            { brand: 'Google Chrome', version: mayor },
            { brand: 'Not=A?Brand', version: '24' }
        ];
        var datosUA = {
            brands: marcas,
            mobile: false,
            platform: PLATAFORMA_UA,
            getHighEntropyValues: function () {
                return Promise.resolve({
                    architecture: 'x86',
                    bitness: '64',
                    brands: marcas,
                    fullVersionList: [
                        { brand: 'Chromium', version: completa },
                        { brand: 'Google Chrome', version: completa },
                        { brand: 'Not=A?Brand', version: '24.0.0.0' }
                    ],
                    mobile: false,
                    model: '',
                    platform: PLATAFORMA_UA,
                    platformVersion: '10.0.0',
                    uaFullVersion: completa,
                    wow64: false
                });
            },
            toJSON: function () {
                return { brands: marcas, mobile: false, platform: PLATAFORMA_UA };
            }
        };
        definir(Navigator.prototype, 'userAgentData', datosUA);
    }

    // ---------- navigator ----------

    definir(Navigator.prototype, 'hardwareConcurrency', NUCLEOS);
    definir(Navigator.prototype, 'deviceMemory', MEMORIA);
    definir(Navigator.prototype, 'platform', PLATAFORMA_JS);
    definir(Navigator.prototype, 'vendor', 'Google Inc.');
    definir(Navigator.prototype, 'maxTouchPoints', 0);
    definir(Navigator.prototype, 'webdriver', false);
    definir(Navigator.prototype, 'language', IDIOMA);
    definir(Navigator.prototype, 'languages', Object.freeze(IDIOMAS.slice()));

    // GPC (Global Privacy Control): señal legal de "no vendas mis datos".
    // Va en la cabecera Sec-GPC y también aquí, porque hay webs que solo
    // miran la propiedad de JavaScript.
    if (__GPC__) {
        definir(Navigator.prototype, 'globalPrivacyControl', true);
    }

    // El locale por defecto de Intl viene del sistema operativo. Si
    // navigator.language dice es-MX y Intl dice es-SV, es una incoherencia
    // que los scripts de fingerprinting comprueban. Lo alineamos.
    function parchearIntl(nombre) {
        var Original = Intl[nombre];
        if (!Original) return;
        function Envoltorio(locales, opciones) {
            if (locales === undefined || locales === null) locales = IDIOMA;
            return new Original(locales, opciones);
        }
        Envoltorio.prototype = Original.prototype;
        if (Original.supportedLocalesOf) {
            Envoltorio.supportedLocalesOf = function (l) {
                return Original.supportedLocalesOf(l);
            };
        }
        try { Intl[nombre] = Envoltorio; } catch (e) {}
    }
    parchearIntl('DateTimeFormat');
    parchearIntl('NumberFormat');

    // ---------- pantalla ----------

    // Resoluciones de escritorio habituales: si la real se parece a una de
    // estas, la web ve exactamente esa (así no queda un número raro tipo
    // 1900x1000). Si no, se redondea a múltiplos de 100.
    var RESOLUCIONES = [
        [1280, 720], [1280, 1024], [1366, 768], [1440, 900], [1536, 864],
        [1600, 900], [1680, 1050], [1920, 1080], [1920, 1200],
        [2560, 1440], [2560, 1600], [3440, 1440], [3840, 2160]
    ];

    function resolucionCercana(ancho, alto) {
        var mejor = null;
        var mejorDistancia = 121; // margen máximo: 120 px en total
        for (var i = 0; i < RESOLUCIONES.length; i++) {
            var d = Math.abs(ancho - RESOLUCIONES[i][0])
                  + Math.abs(alto - RESOLUCIONES[i][1]);
            if (d < mejorDistancia) {
                mejorDistancia = d;
                mejor = RESOLUCIONES[i];
            }
        }
        if (mejor) return mejor.slice();
        return [
            Math.max(100, Math.floor(ancho / 100) * 100),
            Math.max(100, Math.floor(alto / 100) * 100)
        ];
    }

    var realAncho = screen.width;
    var realAlto = screen.height;
    var realAvailAlto = screen.availHeight;
    var resolucion = resolucionCercana(realAncho, realAlto);
    var barraTareas = Math.max(0, realAlto - realAvailAlto) || 40;

    definir(Screen.prototype, 'width', resolucion[0]);
    definir(Screen.prototype, 'height', resolucion[1]);
    definir(Screen.prototype, 'availWidth', resolucion[0]);
    definir(Screen.prototype, 'availHeight',
            Math.max(480, resolucion[1] - barraTareas));
    definir(Screen.prototype, 'colorDepth', 24);
    definir(Screen.prototype, 'pixelDepth', 24);

    // ---------- canvas ----------

    // Perturba unas pocas muestras (≈0.2 %) en ±1: el degradado no cambia a
    // la vista, pero el hash del canvas ya no te identifica. En WebGL
    // readPixels puede devolver float (0..1): ahí el paso es diminuto.
    function enturbiar(datos, semilla) {
        var total = datos.length >>> 2;
        if (!total) return;
        var esFlotante = (typeof Float32Array !== 'undefined')
            && (datos instanceof Float32Array);
        var paso = esFlotante ? 1e-6 : 1;
        var tope = esFlotante ? 1 : 255;
        var cambios = Math.max(1, Math.floor(total / 500));
        var s = semilla >>> 0;
        for (var k = 0; k < cambios; k++) {
            s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
            var pixel = s % total;
            var canal = (s >>> 9) & 3;
            var delta = ((s >>> 13) & 1) ? 1 : -1;
            var i = pixel * 4 + canal;
            if (i >= datos.length) continue;
            var v = datos[i] + delta * paso;
            if (v >= 0 && v <= tope) datos[i] = v;
        }
    }

    if (RUIDO_CANVAS) {
        var getImageDataOriginal = CanvasRenderingContext2D.prototype.getImageData;

        CanvasRenderingContext2D.prototype.getImageData = function () {
            var imagen = getImageDataOriginal.apply(this, arguments);
            try { enturbiar(imagen.data, SEMILLA); } catch (e) {}
            return imagen;
        };

        // Pinta un píxel alterado antes de exportar y lo restaura después,
        // para que toDataURL/toBlob también devuelvan algo distinto.
        function pincel(canvas) {
            var ctx = canvas && canvas.getContext ? canvas.getContext('2d') : null;
            if (!ctx || !canvas.width || !canvas.height) return null;
            try {
                var s = SEMILLA >>> 0;
                var x = s % canvas.width;
                var y = (s >>> 8) % canvas.height;
                var previo = getImageDataOriginal.call(ctx, x, y, 1, 1);
                var nuevo = ctx.createImageData(1, 1);
                for (var i = 0; i < 4; i++) nuevo.data[i] = previo.data[i];
                nuevo.data[0] = (nuevo.data[0] + 1) % 256;
                return {
                    aplicar: function () { ctx.putImageData(nuevo, x, y); },
                    restaurar: function () { ctx.putImageData(previo, x, y); }
                };
            } catch (e) {
                return null; // canvas "tainted" (imagen de otro origen)
            }
        }

        var toDataURLOriginal = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function () {
            var p = pincel(this);
            if (p) p.aplicar();
            try {
                return toDataURLOriginal.apply(this, arguments);
            } finally {
                if (p) p.restaurar();
            }
        };

        var toBlobOriginal = HTMLCanvasElement.prototype.toBlob;
        HTMLCanvasElement.prototype.toBlob = function (callback, tipo, calidad) {
            var p = pincel(this);
            if (p) p.aplicar();
            try {
                return toBlobOriginal.call(this, function (blob) {
                    if (p) p.restaurar();
                    if (typeof callback === 'function') callback(blob);
                }, tipo, calidad);
            } catch (e) {
                if (p) p.restaurar();
                throw e;
            }
        };
    }

    // ---------- WebGL ----------

    function parchearWebGL(proto) {
        if (!proto || !proto.getParameter) return;

        var getParameterOriginal = proto.getParameter;
        proto.getParameter = function (parametro) {
            // 37445/37446 = UNMASKED_VENDOR/RENDERER_WEBGL
            if (parametro === 37445) return 'Google Inc. (Intel)';
            if (parametro === 37446) {
                return 'ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 '
                     + 'vs_5_0 ps_5_0, D3D11)';
            }
            return getParameterOriginal.apply(this, arguments);
        };

        // La huella también se puede leer con readPixels.
        var readPixelsOriginal = proto.readPixels;
        if (readPixelsOriginal && RUIDO_CANVAS) {
            proto.readPixels = function (x, y, ancho, alto, formato, tipo, pixeles) {
                readPixelsOriginal.apply(this, arguments);
                if (pixeles && pixeles.length) {
                    try { enturbiar(pixeles, SEMILLA ^ 0x9e3779b9); } catch (e) {}
                }
            };
        }
    }
    if (window.WebGLRenderingContext) {
        parchearWebGL(WebGLRenderingContext.prototype);
    }
    if (window.WebGL2RenderingContext) {
        parchearWebGL(WebGL2RenderingContext.prototype);
    }

    // ---------- dispositivos multimedia ----------

    // enumerateDevices revela cuántas cámaras/micros tienes y sus IDs.
    // Dejamos un dispositivo genérico por tipo, sin etiquetas.
    try {
        var medios = navigator.mediaDevices;
        if (medios && medios.enumerateDevices) {
            var enumerarOriginal = medios.enumerateDevices.bind(medios);
            Object.defineProperty(medios, 'enumerateDevices', {
                configurable: true,
                writable: true,
                value: function () {
                    return enumerarOriginal().then(function (lista) {
                        var vistos = {};
                        var salida = [];
                        for (var i = 0; i < lista.length; i++) {
                            var tipo = lista[i].kind || 'otro';
                            if (vistos[tipo]) continue;
                            vistos[tipo] = true;
                            salida.push({
                                deviceId: 'id-' + tipo + '-' + SEMILLA.toString(16),
                                kind: tipo,
                                label: '',
                                groupId: 'grupo-' + SEMILLA.toString(16)
                            });
                        }
                        return salida;
                    });
                }
            });
        }
    } catch (e) {}

    // ---------- red y batería ----------

    try {
        var conexion = navigator.connection;
        if (conexion) {
            var protoConexion = Object.getPrototypeOf(conexion) || conexion;
            definir(protoConexion, 'effectiveType', '4g');
            definir(protoConexion, 'rtt', 50);
            definir(protoConexion, 'downlink', 10);
            definir(protoConexion, 'saveData', false);
        }
    } catch (e) {}

    if ('getBattery' in navigator) {
        var bateria = {
            charging: true,
            chargingTime: 0,
            dischargingTime: Infinity,
            level: 1,
            onchargingchange: null,
            onchargingtimechange: null,
            ondischargingtimechange: null,
            onlevelchange: null,
            addEventListener: function () {},
            removeEventListener: function () {},
            dispatchEvent: function () { return true; }
        };
        definir(Navigator.prototype, 'getBattery', function () {
            return Promise.resolve(bateria);
        });
    }
})();
"""


# ---------------------------------------------------------------------------
# GENERACIÓN E INSTALACIÓN DEL SCRIPT
# ---------------------------------------------------------------------------

def generar_js(ua):
    """Devuelve el código JS con los valores de config ya inyectados."""
    idiomas = list(config.FP_IDIOMAS) or ["es-MX"]
    reemplazos = {
        "__SAL__": str(SAL_SESION),
        "__IDIOMAS__": json.dumps(idiomas, ensure_ascii=False),
        "__IDIOMA__": json.dumps(idiomas[0], ensure_ascii=False),
        "__PLATAFORMA_JS__": json.dumps(plataforma_js(ua), ensure_ascii=False),
        "__PLATAFORMA_UA__": json.dumps(plataforma_ua(ua), ensure_ascii=False),
        "__NUCLEOS__": str(int(config.FP_NUCLEOS)),
        "__MEMORIA__": str(int(config.FP_MEMORIA_GB)),
        "__RUIDO_CANVAS__": "true" if config.FP_RUIDO_CANVAS else "false",
        "__GPC__": "true" if config.FP_ENVIAR_GPC else "false",
    }
    codigo = _JS
    for clave, valor in reemplazos.items():
        codigo = codigo.replace(clave, valor)
    return codigo


def crear_script(perfil):
    """Crea el QWebEngineScript para este perfil (mundo principal)."""
    script = QWebEngineScript()
    script.setName(NOMBRE_SCRIPT)
    script.setSourceCode(generar_js(perfil.httpUserAgent()))
    script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
    # MainWorld: tiene que ser el mismo mundo que ve la web; si no, las webs
    # no verían nuestras reescrituras de navigator/canvas.
    script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
    script.setRunsOnSubFrames(True)
    return script


def esta_activo(perfil):
    return bool(perfil.scripts().find(NOMBRE_SCRIPT))


def activar(perfil):
    quitar(perfil)
    perfil.scripts().insert(crear_script(perfil))


def quitar(perfil):
    for script in perfil.scripts().find(NOMBRE_SCRIPT):
        perfil.scripts().remove(script)


def aplicar(perfil, activo):
    """Activa o desactiva en caliente (se nota a partir de la próxima carga).

    Al desactivar devolvemos el UA y el Accept-Language originales del perfil,
    para que el interruptor sirva también para comparar con y sin protección.
    """
    if activo:
        original = perfil.property("ua_original")
        perfil.setHttpUserAgent(
            limpiar_user_agent(original or perfil.httpUserAgent())
        )
        perfil.setHttpAcceptLanguage(config.FP_ACCEPT_LANGUAGE)
        activar(perfil)
    else:
        original = perfil.property("ua_original")
        if original:
            perfil.setHttpUserAgent(original)
        perfil.setHttpAcceptLanguage(
            perfil.property("accept_language_original") or ""
        )
        quitar(perfil)


def preparar_perfil(perfil, activo=None):
    """Deja el perfil listo: UA limpio, idioma y protecciones.

    Se llama una vez por perfil (normal e incógnito). Guardamos los valores
    originales en el perfil para poder restaurarlos si se desactiva.
    """
    if perfil.property("ua_original") is None:
        perfil.setProperty("ua_original", perfil.httpUserAgent())
        perfil.setProperty(
            "accept_language_original", perfil.httpAcceptLanguage()
        )
    if activo is None:
        activo = config.ANTI_FINGERPRINT
    aplicar(perfil, activo)
    return perfil

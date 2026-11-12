# test_anti_fingerprint.py
# Pruebas de la capa de privacidad que se pueden hacer sin navegador:
# cabeceras, plataformas, generación del script y la página de diagnóstico.

import re
import unittest

import config
from herramientas.servidor_cabeceras import clasificar, construir_html
from interfaz import pagina_privacidad
from privacidad import anti_fingerprint as af

UA_QT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) QtWebEngine/6.11.0 Chrome/140.0.0.0 Safari/537.36"
)


class UserAgentTest(unittest.TestCase):

    def test_quita_el_token_de_qt(self):
        limpio = af.limpiar_user_agent(UA_QT)
        self.assertNotIn("QtWebEngine", limpio)
        self.assertIn("Chrome/140.0.0.0", limpio)
        self.assertTrue(limpio.startswith("Mozilla/5.0"))

    def test_no_rompe_un_ua_sin_qt(self):
        ua = "Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0"
        antes = config.UA_PERSONALIZADO
        config.UA_PERSONALIZADO = None
        try:
            self.assertEqual(af.limpiar_user_agent(ua), ua)
        finally:
            config.UA_PERSONALIZADO = antes

    def test_ua_vacio_no_revienta(self):
        antes = config.UA_PERSONALIZADO
        config.UA_PERSONALIZADO = None
        try:
            self.assertEqual(af.limpiar_user_agent(""), "")
            self.assertIsNone(af.limpiar_user_agent(None))
        finally:
            config.UA_PERSONALIZADO = antes

    def test_ua_personalizado_manda(self):
        antes = config.UA_PERSONALIZADO
        config.UA_PERSONALIZADO = "MiNavegador/1.0"
        try:
            self.assertEqual(af.limpiar_user_agent(UA_QT), "MiNavegador/1.0")
        finally:
            config.UA_PERSONALIZADO = antes

    def test_client_hints_coincide_con_el_ua(self):
        cabecera = af.cabecera_client_hints(af.limpiar_user_agent(UA_QT))
        self.assertIsInstance(cabecera, bytes)
        texto = cabecera.decode("ascii")
        self.assertIn('"Chromium";v="140"', texto)
        self.assertIn('"Google Chrome";v="140"', texto)
        self.assertIn("Not=A?Brand", texto)

    def test_plataformas(self):
        self.assertEqual(af.plataforma_js(UA_QT), "Win32")
        self.assertEqual(af.plataforma_ua(UA_QT), "Windows")
        self.assertEqual(
            af.plataforma_js("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15)"),
            "MacIntel",
        )
        self.assertEqual(
            af.plataforma_ua("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15)"),
            "macOS",
        )
        self.assertEqual(
            af.plataforma_js("Mozilla/5.0 (Linux; Android 14)"), "Linux armv8l"
        )
        self.assertEqual(
            af.plataforma_ua("Mozilla/5.0 (Linux; Android 14)"), "Android"
        )
        self.assertEqual(af.plataforma_js("Mozilla/5.0 (X11; Linux)"),
                         "Linux x86_64")


class ScriptTest(unittest.TestCase):

    def setUp(self):
        self.js = af.generar_js(af.limpiar_user_agent(UA_QT))

    def test_no_quedan_marcadores_sin_reemplazar(self):
        restos = re.findall(r"__[A-Z_]+__", self.js)
        self.assertEqual(restos, [])

    def test_inyecta_los_valores_configurados(self):
        self.assertIn(str(af.SAL_SESION), self.js)
        self.assertIn("es-MX", self.js)
        self.assertIn(f"var NUCLEOS = {int(config.FP_NUCLEOS)}", self.js)
        self.assertIn('PLATAFORMA_JS = "Win32"', self.js)

    def test_no_filtra_el_nombre_de_qt(self):
        self.assertNotIn("QtWebEngine", self.js)

    def test_ruido_de_canvas_configurable(self):
        antes = config.FP_RUIDO_CANVAS
        try:
            config.FP_RUIDO_CANVAS = False
            self.assertIn("var RUIDO_CANVAS = false;",
                          af.generar_js(UA_QT))
            config.FP_RUIDO_CANVAS = True
            self.assertIn("var RUIDO_CANVAS = true;",
                          af.generar_js(UA_QT))
        finally:
            config.FP_RUIDO_CANVAS = antes

    def test_gpc_configurable(self):
        antes = config.FP_ENVIAR_GPC
        try:
            config.FP_ENVIAR_GPC = False
            self.assertIn("if (false) {", af.generar_js(UA_QT))
            config.FP_ENVIAR_GPC = True
            self.assertIn("if (true) {", af.generar_js(UA_QT))
        finally:
            config.FP_ENVIAR_GPC = antes

    def test_la_sal_es_estable_durante_la_ejecucion(self):
        self.assertIsInstance(af.SAL_SESION, int)
        self.assertIn(str(af.SAL_SESION), af.generar_js(UA_QT))


class PaginaPrivacidadTest(unittest.TestCase):

    def test_estado_protegida_y_expuesta(self):
        activa = pagina_privacidad.generar_html(True)
        expuesta = pagina_privacidad.generar_html(False)
        self.assertIn("protegida", activa)
        self.assertIn("expuesta", expuesta)
        self.assertIn(config.COLOR_OK, activa)
        self.assertIn(config.COLOR_AVISO, expuesta)

    def test_rellena_los_marcadores(self):
        html = pagina_privacidad.generar_html(True)
        self.assertNotIn("__NOMBRE__", html)
        self.assertNotIn("__ESTADO__", html)
        self.assertIn(config.NOMBRE, html)

    def test_muestra_los_datos_que_nos_importan(self):
        html = pagina_privacidad.generar_html(True)
        for dato in ("navigator.userAgent", "hardwareConcurrency",
                     "deviceMemory", "globalPrivacyControl", "userAgentData",
                     "Hash del canvas", "WebGL"):
            self.assertIn(dato, html, dato)


class ServidorCabecerasTest(unittest.TestCase):

    CABECERAS = [
        ("Host", "127.0.0.1:8000"),
        ("User-Agent", "Mozilla/5.0 <script>"),
        ("Accept-Language", "es-MX,es;q=0.9"),
        ("Sec-GPC", "1"),
    ]

    def test_clasifica_destacadas_y_resto(self):
        destacadas, resto = clasificar(self.CABECERAS)
        nombres = [n for n, _ in destacadas]
        self.assertIn("User-Agent", nombres)
        self.assertIn("Sec-GPC", nombres)
        self.assertEqual([n for n, _ in resto], ["Host"])

    def test_escapa_el_html(self):
        html = construir_html(self.CABECERAS, "/")
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>", html)
        self.assertIn("Sec-GPC", html)
        self.assertIn("class=\"destacada\"", html)


if __name__ == "__main__":
    unittest.main()

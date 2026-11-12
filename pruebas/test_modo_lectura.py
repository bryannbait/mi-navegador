# test_modo_lectura.py
# Envoltorio del modo lectura: comprueba que el JS generado trae las piezas
# clave y que el QWebEngineScript queda bien configurado. No necesita Qt
# mostrado (sí importa PyQt6, que ya está en el venv).

import unittest

import config
from interfaz.modo_lectura import crear_script, generar_js, NOMBRE_SCRIPT
from PyQt6.QtWebEngineCore import QWebEngineScript


class GeneracionTest(unittest.TestCase):

    def test_js_tiene_objeto_mnlector(self):
        js = generar_js()
        self.assertIn("window.MnLector = MnLector;", js)

    def test_js_tiene_metodos_clave(self):
        js = generar_js()
        for metodo in ("activar", "desactivar", "alternar", "esta_activo",
                       "_encontrar", "_puntos"):
            self.assertIn(metodo, js, metodo)

    def test_js_tiene_heuristica_y_salir(self):
        js = generar_js()
        self.assertIn("article", js)
        self.assertIn("main", js)
        self.assertIn("[role=main]", js)
        self.assertIn("mn-lector-salir", js)
        self.assertIn("Salir", js)

    def test_css_embebido_con_colores_del_tema(self):
        js = generar_js()
        self.assertNotIn("__CSS__", js)
        self.assertNotIn("__FONDO__", js)
        self.assertIn(config.COLOR_FONDO, js)
        self.assertIn(config.COLOR_TEXTO, js)
        self.assertIn(config.COLOR_ACENTO, js)
        self.assertIn(config.COLOR_FONDO, js)

    def test_js_sin_marcadores_sin_reemplazar(self):
        js = generar_js()
        restos = [m for m in ("__CSS__", "__FONDO__", "__TEXTO__",
                              "__TEXTO_SUAVE__", "__ACENTO__",
                              "__ACENTO_FUERTE__", "__ACENTO_SUAVE__")
                  if m in js]
        self.assertEqual(restos, [], restos)

    def test_script_configurado(self):
        script = crear_script()
        self.assertEqual(script.name(), NOMBRE_SCRIPT)
        self.assertEqual(
            script.injectionPoint(),
            QWebEngineScript.InjectionPoint.DocumentCreation)
        self.assertEqual(
            script.worldId(), QWebEngineScript.ScriptWorldId.MainWorld)
        self.assertEqual(script.runsOnSubFrames(), False)
        self.assertIn("window.MnLector", script.sourceCode())


if __name__ == "__main__":
    unittest.main()

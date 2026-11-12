# test_zoom.py
# Pruebas del modelo de zoom por sitio (sin interfaz): límites, pasos,
# persistencia, reset, host vacío y modo solo-memoria (incógnito).

import json
import os
import tempfile
import unittest

from modelos.zoom import (
    MAX_FACTOR, MIN_FACTOR, FACTOR_DEFECTO, Zoom, host_de,
    pasar_a_factor, pasar_a_puntos,
)


class HelpersTest(unittest.TestCase):

    def test_puntos_y_factor(self):
        self.assertEqual(pasar_a_puntos(1.25), 125)
        self.assertEqual(pasar_a_puntos(1.0), 100)
        self.assertEqual(pasar_a_factor(125), 1.25)
        self.assertEqual(pasar_a_factor(100), 1.0)

    def test_host_sin_puerto(self):
        class Url:
            def host(self):
                return "ejemplo.com"
        self.assertEqual(host_de(Url()), "ejemplo.com")

    def test_host_vacio(self):
        self.assertEqual(host_de(None), "")
        self.assertEqual(host_de(type("X", (), {"host": lambda self: None})()), "")


class ZoomTest(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.ruta = os.path.join(self._tmp.name, "zoom.json")

    def leer(self):
        with open(self.ruta, encoding="utf-8") as f:
            return json.load(f)

    def test_sin_archivo_esta_vacio(self):
        z = Zoom(self.ruta)
        self.assertEqual(z.obtener("ejemplo.com"), FACTOR_DEFECTO)
        self.assertEqual(z.datos, {})

    def test_establecer_y_obtener(self):
        z = Zoom(self.ruta)
        z.establecer("ejemplo.com", 1.2)
        self.assertEqual(z.obtener("ejemplo.com"), 1.2)
        self.assertEqual(self.leer(), {"ejemplo.com": 1.2})

    def test_limites(self):
        z = Zoom(self.ruta)
        z.establecer("a", 0.1)   # por debajo del minimo
        self.assertEqual(z.obtener("a"), MIN_FACTOR)
        z.establecer("b", 5.0)   # por encima del maximo
        self.assertEqual(z.obtener("b"), MAX_FACTOR)

    def test_paso_de_diez_por_ciento(self):
        z = Zoom(self.ruta)
        z.establecer("a", 1.23)   # no es multiplo de 10 %
        self.assertEqual(z.obtener("a"), 1.2)
        z.establecer("b", 1.27)
        self.assertEqual(z.obtener("b"), 1.3)

    def test_host_vacio_no_se_guarda(self):
        z = Zoom(self.ruta)
        z.establecer("", 2.0)
        z.establecer(None, 2.0)
        self.assertEqual(z.datos, {})
        self.assertFalse(os.path.exists(self.ruta))

    def test_restablecer_borra_la_entrada(self):
        z = Zoom(self.ruta)
        z.establecer("a", 1.5)
        z.restablecer("a")
        self.assertEqual(z.obtener("a"), FACTOR_DEFECTO)
        self.assertEqual(self.leer(), {})

    def test_restablecer_sin_entrada_no_revienta(self):
        z = Zoom(self.ruta)
        z.restablecer("inexistente")
        self.assertEqual(z.datos, {})

    def test_archivo_corrupto_no_revienta(self):
        with open(self.ruta, "w", encoding="utf-8") as f:
            f.write("{no es json")
        z = Zoom(self.ruta)
        self.assertEqual(z.obtener("a"), FACTOR_DEFECTO)

    def test_valores_no_numericos_se_ignoran(self):
        with open(self.ruta, "w", encoding="utf-8") as f:
            json.dump({"a": "abc", "b": 1.5, "c": None}, f)
        z = Zoom(self.ruta)
        self.assertEqual(z.datos, {"b": 1.5})

    def test_no_es_diccionario_se_ignora(self):
        with open(self.ruta, "w", encoding="utf-8") as f:
            json.dump([{"a": 1.5}], f)
        self.assertEqual(Zoom(self.ruta).datos, {})

    def test_modelo_en_memoria_no_escribe(self):
        z = Zoom(None)
        z.establecer("a", 1.5)
        self.assertEqual(z.obtener("a"), 1.5)
        self.assertEqual(os.listdir(self._tmp.name), [])
        z.restablecer("a")
        self.assertEqual(z.obtener("a"), FACTOR_DEFECTO)


class AjusteTest(unittest.TestCase):

    def test_subir_y_bajar_un_paso(self):
        z = Zoom(None)
        self.assertEqual(z.ajuste(1.0, mas=True), 1.1)
        self.assertEqual(z.ajuste(1.1, mas=True), 1.2)
        self.assertEqual(z.ajuste(1.2, mas=False), 1.1)
        self.assertEqual(z.ajuste(1.0, mas=False), 0.9)

    def test_no_se_pasa_del_maximo(self):
        z = Zoom(None)
        self.assertEqual(z.ajuste(MAX_FACTOR, mas=True), MAX_FACTOR)
        self.assertEqual(z.ajuste(1.95, mas=True), MAX_FACTOR)

    def test_no_se_pasa_del_minimo(self):
        z = Zoom(None)
        self.assertEqual(z.ajuste(MIN_FACTOR, mas=False), MIN_FACTOR)
        self.assertEqual(z.ajuste(0.55, mas=False), MIN_FACTOR)


if __name__ == "__main__":
    unittest.main()

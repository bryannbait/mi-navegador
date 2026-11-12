# test_sesion.py
# Pruebas del modelo de sesión (sin interfaz): guardar, restaurar, archivos
# corruptos, tope de pestañas y clamps del índice activo.

import json
import os
import tempfile
import unittest

from modelos.sesion import MAX_PESTANAS, Sesion, normalizar_entrada


class NormalizarTest(unittest.TestCase):

    def test_http_y_https_se_aceptan(self):
        self.assertEqual(
            normalizar_entrada({"url": "https://a.test/x", "titulo": "A"}),
            {"url": "https://a.test/x", "titulo": "A", "fijada": False},
        )
        self.assertEqual(
            normalizar_entrada({"url": "http://b.test"}),
            {"url": "http://b.test", "titulo": "", "fijada": False},
        )

    def test_otros_esquemas_se_descartan(self):
        for url in ("about:blank", "file:///C:/a.txt", "data:text/html,x",
                    "javascript:alert(1)", "chrome://settings", ""):
            self.assertIsNone(normalizar_entrada({"url": url}), url)

    def test_entrada_nueva(self):
        self.assertEqual(
            normalizar_entrada({"nueva": True}),
            {"nueva": True, "fijada": False},
        )

    def test_basura(self):
        self.assertIsNone(normalizar_entrada(None))
        self.assertIsNone(normalizar_entrada("https://a.test"))
        self.assertIsNone(normalizar_entrada([]))
        self.assertIsNone(normalizar_entrada({"titulo": "sin url"}))

    def test_fijada_solo_si_es_true(self):
        self.assertTrue(normalizar_entrada(
            {"url": "https://a.test", "fijada": True})["fijada"])
        self.assertFalse(normalizar_entrada(
            {"url": "https://a.test", "fijada": "si"})["fijada"])


class SesionTest(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.ruta_archivo = os.path.join(self._tmp.name, "sesion.json")

    def leer(self):
        with open(self.ruta_archivo, encoding="utf-8") as f:
            return json.load(f)

    def test_sin_archivo_empieza_vacia(self):
        s = Sesion(self.ruta_archivo)
        self.assertTrue(s.vacia())
        self.assertEqual(s.pestanas(), [])
        self.assertEqual(s.activa(), 0)

    def test_ida_y_vuelta(self):
        s = Sesion(self.ruta_archivo)
        s.guardar([
            {"url": "https://a.test/1", "titulo": "Uno"},
            {"nueva": True},
            {"url": "https://b.test/2", "titulo": "Dos", "fijada": True},
        ], activa=2)

        otra = Sesion(self.ruta_archivo)
        self.assertEqual(len(otra.pestanas()), 3)
        self.assertEqual(otra.activa(), 2)
        self.assertFalse(otra.vacia())
        self.assertEqual(otra.pestanas()[0]["url"], "https://a.test/1")
        self.assertTrue(otra.pestanas()[1]["nueva"])
        self.assertTrue(otra.pestanas()[2]["fijada"])

    def test_el_json_tiene_version_y_estructura(self):
        s = Sesion(self.ruta_archivo)
        s.guardar([{"url": "https://a.test"}], activa=0)
        datos = self.leer()
        self.assertEqual(datos["version"], 1)
        self.assertEqual(datos["activa"], 0)
        self.assertEqual(datos["pestanas"][0]["url"], "https://a.test")

    def test_archivo_corrupto_no_revienta(self):
        with open(self.ruta_archivo, "w", encoding="utf-8") as f:
            f.write("{esto no es json")
        s = Sesion(self.ruta_archivo)
        self.assertTrue(s.vacia())

    def test_otra_version_se_ignora(self):
        with open(self.ruta_archivo, "w", encoding="utf-8") as f:
            json.dump({"version": 99, "activa": 0, "pestanas": [
                {"url": "https://a.test"}]}, f)
        self.assertTrue(Sesion(self.ruta_archivo).vacia())

    def test_version_faltante_se_ignora(self):
        with open(self.ruta_archivo, "w", encoding="utf-8") as f:
            json.dump({"pestanas": [{"url": "https://a.test"}]}, f)
        self.assertTrue(Sesion(self.ruta_archivo).vacia())

    def test_lista_en_vez_de_objeto_se_ignora(self):
        with open(self.ruta_archivo, "w", encoding="utf-8") as f:
            json.dump([{"url": "https://a.test"}], f)
        self.assertTrue(Sesion(self.ruta_archivo).vacia())

    def test_tope_de_pestanas(self):
        entradas = [{"url": f"https://a.test/{i}"} for i in range(50)]
        s = Sesion(self.ruta_archivo)
        s.guardar(entradas, activa=49)
        self.assertEqual(len(s.pestanas()), MAX_PESTANAS)

        otra = Sesion(self.ruta_archivo)
        self.assertEqual(len(otra.pestanas()), MAX_PESTANAS)
        # Se conservan las primeras 30 y el índice se recorta al 29.
        self.assertEqual(otra.pestanas()[0]["url"], "https://a.test/0")
        self.assertEqual(otra.pestanas()[-1]["url"], "https://a.test/29")
        self.assertEqual(otra.activa(), MAX_PESTANAS - 1)

    def test_tope_al_cargar_un_archivo_ajeno_grande(self):
        with open(self.ruta_archivo, "w", encoding="utf-8") as f:
            json.dump({"version": 1, "activa": 0, "pestanas": [
                {"url": f"https://a.test/{i}"} for i in range(100)
            ]}, f)
        self.assertEqual(len(Sesion(self.ruta_archivo).pestanas()),
                         MAX_PESTANAS)

    def test_indice_activo_se_recorta(self):
        s = Sesion(self.ruta_archivo)
        s.guardar([{"url": "https://a.test"}], activa=7)
        self.assertEqual(s.activa(), 0)
        self.assertEqual(Sesion(self.ruta_archivo).activa(), 0)

        s.guardar([{"url": "https://a.test"}], activa=-3)
        self.assertEqual(s.activa(), 0)

    def test_activa_invalida_al_cargar(self):
        for valor in ("2", None, 3.5, True):
            with open(self.ruta_archivo, "w", encoding="utf-8") as f:
                json.dump({"version": 1, "activa": valor, "pestanas": [
                    {"url": "https://a.test"}]}, f)
            self.assertEqual(Sesion(self.ruta_archivo).activa(), 0, valor)

    def test_sin_pestanas_activa_es_cero(self):
        s = Sesion(self.ruta_archivo)
        s.guardar([], activa=5)
        self.assertTrue(s.vacia())
        self.assertEqual(s.activa(), 0)

    def test_borrar_deja_el_archivo_vacio(self):
        s = Sesion(self.ruta_archivo)
        s.guardar([{"url": "https://a.test"}], activa=0)
        s.borrar()
        self.assertTrue(s.vacia())
        self.assertEqual(self.leer()["pestanas"], [])

    def test_modelo_en_memoria_no_escribe(self):
        s = Sesion(None)
        s.guardar([{"url": "https://a.test"}], activa=0)
        # El modelo en memoria sí recuerda lo guardado...
        self.assertEqual(len(s.pestanas()), 1)
        # ...pero no hay archivo que tocar.
        self.assertEqual(os.listdir(self._tmp.name), [])
        s.borrar()
        self.assertTrue(s.vacia())

    def test_una_entrada_invalida_no_tumba_la_lista(self):
        s = Sesion(self.ruta_archivo)
        s.guardar([
            {"url": "https://a.test"},
            {"url": "javascript:alert(1)"},
            {"nueva": True},
        ], activa=0)
        self.assertEqual(len(s.pestanas()), 2)
        self.assertEqual(s.pestanas()[1], {"nueva": True, "fijada": False})

    def test_carpeta_inexistente_se_crea(self):
        ruta = os.path.join(self._tmp.name, "sub", "sesion.json")
        s = Sesion(ruta)
        s.guardar([{"url": "https://a.test"}], activa=0)
        self.assertTrue(os.path.isfile(ruta))


if __name__ == "__main__":
    unittest.main()

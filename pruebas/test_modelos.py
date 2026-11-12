# pruebas/test_modelos.py
# Pruebas de los modelos de datos (sin interfaz).
#
# Ejecutar desde la raíz del proyecto:
#   venv\Scripts\python.exe -m unittest discover -s pruebas -v

import json
import os
import tempfile
import unittest

from modelos.descargas import Descargas
from modelos.favoritos import Favoritos
from modelos.historial import Historial, MAX_ENTRADAS
from modelos.modelo_json import ModeloJSON
from modelos.preferencias import Preferencias


class ModelosTest(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.carpeta = os.path.join(self._tmp.name, "datos")
        os.makedirs(self.carpeta, exist_ok=True)

    def ruta(self, nombre):
        return os.path.join(self.carpeta, nombre)

    def leer(self, nombre):
        with open(self.ruta(nombre), encoding="utf-8") as f:
            return json.load(f)

    # ---------- historial ----------

    def test_historial_anade_guarda_y_recarga(self):
        ruta = self.ruta("historial.json")
        h = Historial(ruta)
        h.añadir("Ejemplo", "https://ejemplo.test")
        h.añadir("Ejemplo 2", "https://ejemplo.test/2")

        self.assertEqual(len(h.todos()), 2)
        self.assertEqual(self.leer("historial.json")[0]["titulo"], "Ejemplo 2")
        self.assertEqual(len(Historial(ruta).todos()), 2)

    def test_historial_ignora_urls_internas_y_repetidas(self):
        h = Historial(self.ruta("historial.json"))
        h.añadir("Interna", "about:blank")
        h.añadir("Datos", "data:text/html,hola")
        h.añadir("Archivo", "file:///C:/x.html")
        self.assertEqual(h.todos(), [])

        h.añadir("Uno", "https://uno.test")
        h.añadir("Otra vez", "https://uno.test")
        self.assertEqual(len(h.todos()), 1)

    def test_historial_busca_y_borra(self):
        h = Historial(self.ruta("historial.json"))
        h.añadir("Python", "https://python.test")
        h.añadir("Qt", "https://qt.io")

        self.assertEqual([e["titulo"] for e in h.buscar("PYTHON")], ["Python"])
        self.assertEqual(len(h.buscar("  ")), 2)

        h.borrar_todo()
        self.assertEqual(h.todos(), [])
        self.assertEqual(self.leer("historial.json"), [])

    def test_historial_respeta_el_tope(self):
        h = Historial(self.ruta("historial.json"))
        for i in range(MAX_ENTRADAS + 5):
            h.añadir(f"Pagina {i}", f"https://p{i}.test")
        self.assertEqual(len(h.todos()), MAX_ENTRADAS)

    # ---------- favoritos ----------

    def test_favoritos_crud(self):
        ruta = self.ruta("favoritos.json")
        f = Favoritos(ruta)

        f.añadir("Uno", "https://uno.test")
        f.añadir("Duplicado", "https://uno.test")
        self.assertTrue(f.existe("https://uno.test"))
        self.assertEqual(len(f.todos()), 1)

        f.renombrar("https://uno.test", "Renombrado")
        self.assertEqual(f.todos()[0]["titulo"], "Renombrado")

        f.eliminar("https://uno.test")
        self.assertFalse(f.existe("https://uno.test"))
        self.assertEqual(Favoritos(ruta).todos(), [])

    # ---------- descargas ----------

    def test_descargas_marca_las_interrumpidas(self):
        ruta = self.ruta("descargas.json")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump([
                {"nombre": "a", "estado": "en curso"},
                {"nombre": "b", "estado": "completada"},
            ], f)

        d = Descargas(ruta)
        self.assertEqual(d.todos()[0]["estado"], "interrumpida")
        self.assertEqual(d.todos()[1]["estado"], "completada")

    def test_descargas_anade_y_limita(self):
        d = Descargas(self.ruta("descargas.json"))
        for i in range(205):
            d.añadir(f"f{i}", f"C:/tmp/f{i}", f"https://x.test/{i}", i)

        self.assertEqual(len(d.todos()), 200)
        self.assertEqual(self.leer("descargas.json")[0]["nombre"], "f204")

    # ---------- preferencias ----------

    def test_preferencias_por_defecto_y_persistencia(self):
        ruta = self.ruta("preferencias.json")
        p = Preferencias(ruta)
        self.assertEqual(p.get("motor_busqueda"), "duckduckgo")
        self.assertTrue(p.get("mostrar_barra_favoritos"))

        p.set("motor_busqueda", "brave")
        self.assertEqual(Preferencias(ruta).get("motor_busqueda"), "brave")

    def test_preferencias_rellena_claves_nuevas(self):
        ruta = self.ruta("preferencias.json")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump({"motor_busqueda": "google"}, f)

        p = Preferencias(ruta)
        self.assertEqual(p.get("motor_busqueda"), "google")
        self.assertTrue(p.get("anti_fingerprint"))

    # ---------- base ----------

    def test_archivo_corrupto_no_rompe(self):
        ruta = self.ruta("historial.json")
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("{esto no es json")
        self.assertEqual(Historial(ruta).todos(), [])

    def test_modelo_en_memoria_no_toca_el_disco(self):
        modelo = ModeloJSON(None)
        modelo.entradas.append({"x": 1})
        modelo.guardar()
        self.assertEqual(modelo.todos(), [{"x": 1}])


if __name__ == "__main__":
    unittest.main()

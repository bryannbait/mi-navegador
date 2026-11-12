# test_descargas.py
# Pruebas del modelo de descargas y del servidor local de pruebas.
#
# El servidor se levanta en un puerto libre y se comprueba el soporte de
# Range, que es lo que permite pausar y reanudar.

import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from herramientas.servidor_descargas import Manejador, interpretar_rango
from modelos.descargas import Descargas, ESTADOS_FINALES, puede_reintentar


class ManejadorSilencioso(Manejador):
    """Igual que el real, pero sin escribir cada petición en la consola."""

    def log_message(self, formato, *args):
        pass


class RangoTest(unittest.TestCase):

    def test_sin_cabecera(self):
        self.assertIsNone(interpretar_rango("", 1000))
        self.assertIsNone(interpretar_rango(None, 1000))

    def test_rango_normal(self):
        self.assertEqual(interpretar_rango("bytes=0-99", 1000), (0, 99))
        self.assertEqual(interpretar_rango("bytes=100-199", 1000), (100, 199))

    def test_rango_abierto_y_recortado(self):
        self.assertEqual(interpretar_rango("bytes=900-", 1000), (900, 999))
        self.assertEqual(interpretar_rango("bytes=0-99999", 1000), (0, 999))

    def test_sufijo(self):
        self.assertEqual(interpretar_rango("bytes=-100", 1000), (900, 999))
        self.assertEqual(interpretar_rango("bytes=-5000", 1000), (0, 999))

    def test_basura(self):
        self.assertIsNone(interpretar_rango("paginas=1-2", 1000))
        self.assertIsNone(interpretar_rango("bytes=abc-def", 1000))
        self.assertIsNone(interpretar_rango("bytes=5000-", 1000))
        self.assertIsNone(interpretar_rango("bytes=100", 1000))


class ReintentoTest(unittest.TestCase):

    def test_solo_se_reintenta_lo_que_fallo_y_tiene_url(self):
        self.assertTrue(puede_reintentar(
            {"estado": "interrumpida", "url": "https://x.test/a.bin"}))
        self.assertTrue(puede_reintentar(
            {"estado": "cancelada", "url": "http://x.test/a.bin"}))

        self.assertFalse(puede_reintentar(
            {"estado": "completada", "url": "https://x.test/a.bin"}))
        self.assertFalse(puede_reintentar(
            {"estado": "interrumpida", "url": "file:///C:/a.bin"}))
        self.assertFalse(puede_reintentar(
            {"estado": "interrumpida", "url": ""}))
        self.assertFalse(puede_reintentar(None))


class ServidorTest(unittest.TestCase):

    MB = 1

    def setUp(self):
        self._mb_antes = Manejador.mb
        self._ritmo_antes = Manejador.ritmo_kb
        Manejador.mb = self.MB
        Manejador.ritmo_kb = 0
        self.addCleanup(self._restaurar)

        self.servidor = ThreadingHTTPServer(
            ("127.0.0.1", 0), ManejadorSilencioso
        )
        self.addCleanup(self.servidor.server_close)
        hilo = threading.Thread(target=self.servidor.serve_forever, daemon=True)
        hilo.start()
        self.addCleanup(self.servidor.shutdown)
        self.puerto = self.servidor.server_address[1]

    def _restaurar(self):
        Manejador.mb = self._mb_antes
        Manejador.ritmo_kb = self._ritmo_antes

    def url(self, ruta="/descarga.bin"):
        return f"http://127.0.0.1:{self.puerto}{ruta}"

    def test_descarga_completa(self):
        with urllib.request.urlopen(self.url(), timeout=20) as r:
            self.assertEqual(r.status, 200)
            datos = r.read()
        self.assertEqual(len(datos), self.MB * 1024 * 1024)
        self.assertEqual(datos[0], 0)
        self.assertEqual(datos[255], 255)

    def test_rango_parcial(self):
        peticion = urllib.request.Request(
            self.url(), headers={"Range": "bytes=100-199"}
        )
        with urllib.request.urlopen(peticion, timeout=20) as r:
            self.assertEqual(r.status, 206)
            self.assertEqual(
                r.headers["Content-Range"], "bytes 100-199/1048576"
            )
            self.assertEqual(r.headers["Accept-Ranges"], "bytes")
            datos = r.read()
        self.assertEqual(len(datos), 100)
        self.assertEqual(datos[0], 100)

    def test_cabecera_head_sin_cuerpo(self):
        peticion = urllib.request.Request(self.url(), method="HEAD")
        with urllib.request.urlopen(peticion, timeout=20) as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(r.headers["Content-Length"], "1048576")
            self.assertEqual(r.read(), b"")

    def test_pagina_de_inicio(self):
        with urllib.request.urlopen(self.url("/"), timeout=20) as r:
            html = r.read().decode("utf-8")
        self.assertIn("descarga.bin", html)

    def test_ruta_desconocida(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(self.url("/nada"), timeout=20)
        self.assertEqual(ctx.exception.code, 404)
        ctx.exception.close()


class ModeloDescargasTest(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.carpeta = os.path.join(self._tmp.name, "datos")
        os.makedirs(self.carpeta, exist_ok=True)

    def ruta(self, nombre="descargas.json"):
        return os.path.join(self.carpeta, nombre)

    def test_estados_finales_documentados(self):
        self.assertEqual(
            ESTADOS_FINALES, ("completada", "cancelada", "interrumpida")
        )

    def test_anadir_guarda_estado_y_fecha(self):
        d = Descargas(self.ruta())
        entrada = d.añadir("a.bin", "C:/tmp/a.bin", "https://x.test/a", 10)
        self.assertEqual(entrada["estado"], "completada")
        self.assertIn("fecha", entrada)

        with open(self.ruta(), encoding="utf-8") as f:
            guardado = json.load(f)
        self.assertEqual(guardado[0]["nombre"], "a.bin")

    def test_lo_que_estaba_en_curso_queda_interrumpido(self):
        with open(self.ruta(), "w", encoding="utf-8") as f:
            json.dump([{"nombre": "a", "estado": "en curso"}], f)
        d = Descargas(self.ruta())
        self.assertEqual(d.todos()[0]["estado"], "interrumpida")

    def test_el_motivo_se_conserva_al_recargar(self):
        with open(self.ruta(), "w", encoding="utf-8") as f:
            json.dump([{
                "nombre": "a", "estado": "interrumpida",
                "motivo": "Error de red",
            }], f)
        d = Descargas(self.ruta())
        self.assertEqual(d.todos()[0]["motivo"], "Error de red")

    def test_borrar_todo(self):
        d = Descargas(self.ruta())
        d.añadir("a", "C:/a", "https://x.test/a", 1)
        d.borrar_todo()
        self.assertEqual(d.todos(), [])
        with open(self.ruta(), encoding="utf-8") as f:
            self.assertEqual(json.load(f), [])


if __name__ == "__main__":
    unittest.main()

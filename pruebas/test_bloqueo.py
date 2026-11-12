# test_bloqueo.py
# Pruebas del gestor de bloqueo: caché del motor compilado y bloqueo.
# No abren ventanas ni tocan la red.

import os
import time
import unittest

from privacidad.gestor_bloqueo import GestorBloqueo
from rutas import RUTA_DATOS


class CacheTest(unittest.TestCase):

    def setUp(self):
        # Limpiar caché de test antes y después
        for f in ("cache_adblock.bin", "cache_adblock.json"):
            ruta = os.path.join(RUTA_DATOS, f)
            if os.path.exists(ruta):
                os.remove(ruta)

    def tearDown(self):
        for f in ("cache_adblock.bin", "cache_adblock.json"):
            ruta = os.path.join(RUTA_DATOS, f)
            if os.path.exists(ruta):
                os.remove(ruta)

    def test_primera_carga_compila_y_guarda_cache(self):
        t = time.perf_counter()
        gestor = GestorBloqueo()
        total = time.perf_counter() - t

        self.assertTrue(gestor.listo)
        self.assertGreater(gestor.reglas, 0)
        self.assertIsNotNone(gestor.engine)
        # Primera vez compila: ~1 s en esta máquina
        self.assertLess(total, 5.0)

        # Verificar que se creó el caché
        self.assertTrue(os.path.exists(os.path.join(RUTA_DATOS, "cache_adblock.bin")))
        self.assertTrue(os.path.exists(os.path.join(RUTA_DATOS, "cache_adblock.json")))

    def test_segunda_carga_usa_cache(self):
        # Primera carga para crear el caché
        GestorBloqueo()

        # Segunda carga debe usar caché
        t = time.perf_counter()
        gestor = GestorBloqueo()
        total = time.perf_counter() - t

        self.assertTrue(gestor.listo)
        self.assertGreater(gestor.reglas, 0)
        self.assertIsNotNone(gestor.engine)
        # Desde caché: < 1 s
        self.assertLess(total, 1.0)

    def test_bloqueo_funciona_con_motor_cacheado(self):
        GestorBloqueo()  # crea caché
        gestor = GestorBloqueo()  # usa caché

        # Anuncio típico de Google
        bloquea = gestor.debe_bloquear(
            "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js",
            "https://ejemplo.com",
            "script")
        self.assertTrue(bloquea)

        # Sitio normal no se bloquea
        no_bloquea = gestor.debe_bloquear(
            "https://ejemplo.com/imagen.png",
            "https://ejemplo.com",
            "image")
        self.assertFalse(no_bloquea)


if __name__ == "__main__":
    unittest.main()
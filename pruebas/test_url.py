# pruebas/test_url.py
# Prueba el helper que convierte QUrl a texto para guardar.

import unittest

from PyQt6.QtCore import QUrl

from navegador import url_a_texto


class UrlATextoTest(unittest.TestCase):

    def test_codifica_los_espacios(self):
        texto = url_a_texto(QUrl("https://ejemplo.test/a b"))
        self.assertEqual(texto, "https://ejemplo.test/a%20b")

    def test_conserva_el_resto(self):
        url = "https://ejemplo.test/ruta?q=1&x=2"
        self.assertEqual(url_a_texto(QUrl(url)), url)


if __name__ == "__main__":
    unittest.main()

# pruebas/test_pagina_inicio.py
# Pruebas del HTML de la página de nueva pestaña.

import unittest

import pagina_inicio


class PaginaInicioTest(unittest.TestCase):

    def test_escapa_html_de_los_favoritos(self):
        html = pagina_inicio.generar_html(
            [{"titulo": "<script>alert(1)</script>", "url": "https://ok.test/"}],
            "DuckDuckGo",
        )
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_muestra_ocho_accesos_y_solo_http(self):
        favoritos = [
            {"titulo": f"F{i}", "url": f"https://f{i}.test"} for i in range(12)
        ]
        favoritos.append({"titulo": "Interna", "url": "about:blank"})

        html = pagina_inicio.generar_html(favoritos, "DuckDuckGo")

        self.assertEqual(html.count('class="acceso"'), 8)
        self.assertNotIn("about:blank", html)

    def test_incognito_no_muestra_favoritos(self):
        html = pagina_inicio.generar_html(
            [{"titulo": "F", "url": "https://f.test"}],
            "DuckDuckGo",
            incognito=True,
        )
        self.assertNotIn("https://f.test", html)
        self.assertIn("Navegación privada", html)

    def test_incluye_la_direccion_de_busqueda(self):
        html = pagina_inicio.generar_html([], "DuckDuckGo")
        self.assertIn(pagina_inicio.PREFIJO_BUSQUEDA, html)


if __name__ == "__main__":
    unittest.main()

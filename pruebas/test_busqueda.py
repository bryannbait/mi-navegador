# test_busqueda.py
# Pruebas de la elección de motor y del respaldo (sin interfaz).
# El caso real: una red que corta search.brave.com; la búsqueda debe seguir
# funcionando con el motor de respaldo, sin cambiar la preferencia del usuario.

import unittest
from unittest import mock

import config
from modelos import busqueda, motores


class OrdenPorDefectoTest(unittest.TestCase):
    """Orden pedido: 1.º Brave Search, 2.º Google, 3.º DuckDuckGo."""

    def test_orden_configurado(self):
        self.assertEqual(config.MOTORES_RESPALDO, ["google", "duckduckgo"])

    def test_brave_primero_google_segundo(self):
        self.assertEqual(busqueda.elegir("brave", set()), "brave")
        self.assertEqual(busqueda.elegir("brave", {"brave"}), "google")

    def test_si_brave_y_google_fallan_va_duckduckgo(self):
        self.assertEqual(
            busqueda.elegir("brave", {"brave", "google"}), "duckduckgo")

    def test_url_de_respaldo_es_google(self):
        url, clave = busqueda.url_busqueda("brave", "youtube", {"brave"})
        self.assertEqual(clave, "google")
        self.assertEqual(url, "https://www.google.com/search?q=youtube")

    def test_google_como_elegido_no_se_cambia(self):
        self.assertEqual(busqueda.elegir("google", {"brave"}), "google")


class ElegirTest(unittest.TestCase):

    def test_motor_normal_si_responde(self):
        self.assertEqual(busqueda.elegir("brave", set()), "brave")

    def test_usa_respaldo_si_el_motor_esta_caido(self):
        with mock.patch.object(config, "MOTORES_RESPALDO", ["duckduckgo"]):
            self.assertEqual(busqueda.elegir("brave", {"brave"}), "duckduckgo")

    def test_sin_respaldo_configurado_devuelve_el_original(self):
        with mock.patch.object(config, "MOTORES_RESPALDO", []):
            self.assertEqual(busqueda.elegir("brave", {"brave"}), "brave")

    def test_respaldo_igual_al_motor_no_cambia_nada(self):
        with mock.patch.object(config, "MOTORES_RESPALDO", ["brave"]):
            self.assertEqual(busqueda.elegir("brave", {"brave"}), "brave")

    def test_respaldo_tambien_caido_devuelve_el_original(self):
        with mock.patch.object(config, "MOTORES_RESPALDO", ["duckduckgo"]):
            self.assertEqual(
                busqueda.elegir("brave", {"brave", "duckduckgo"}), "brave")

    def test_motor_desconocido_no_se_toca(self):
        with mock.patch.object(config, "MOTORES_RESPALDO", ["duckduckgo"]):
            self.assertEqual(busqueda.elegir("brave", {"google"}), "brave")


class UrlBusquedaTest(unittest.TestCase):

    def test_url_del_motor_elegido(self):
        url, clave = busqueda.url_busqueda("duckduckgo", "hola mundo", set())
        self.assertEqual(clave, "duckduckgo")
        self.assertEqual(url, "https://duckduckgo.com/?q=hola%20mundo")

    def test_url_con_respaldo(self):
        with mock.patch.object(config, "MOTORES_RESPALDO", ["duckduckgo"]):
            url, clave = busqueda.url_busqueda("brave", "youtube", {"brave"})
        self.assertEqual(clave, "duckduckgo")
        self.assertTrue(url.startswith("https://duckduckgo.com/?q=youtube"))

    def test_caracteres_especiales_se_codifican(self):
        url, _ = busqueda.url_busqueda("google", "a&b=c", set())
        self.assertIn("a%26b%3Dc", url)


class HostTest(unittest.TestCase):

    def test_host_de_plantilla(self):
        self.assertEqual(
            busqueda.host_de("https://search.brave.com/search?q={q}"),
            "search.brave.com")

    def test_clave_por_host_reconoce_el_motor(self):
        self.assertEqual(
            busqueda.clave_por_host("search.brave.com"), "brave")
        self.assertEqual(
            busqueda.clave_por_host("duckduckgo.com"), "duckduckgo")
        self.assertEqual(
            busqueda.clave_por_host("WWW.Google.COM"), "google")

    def test_clave_por_host_ignora_sitios_normales(self):
        self.assertIsNone(busqueda.clave_por_host("github.com"))
        self.assertIsNone(busqueda.clave_por_host(""))

    def test_todos_los_motores_tienen_host_identificable(self):
        for clave, motor in motores.MOTORES.items():
            host = busqueda.host_de(motor["url_busqueda"])
            self.assertEqual(busqueda.clave_por_host(host), clave)


class ConsultaTest(unittest.TestCase):

    def test_consulta_de_una_busqueda(self):
        self.assertEqual(
            busqueda.consulta_de("q=youtube"), "youtube")
        self.assertEqual(
            busqueda.consulta_de("?q=futbol%20libre"), "futbol libre")

    def test_consulta_con_otros_parametros(self):
        self.assertEqual(
            busqueda.consulta_de("source=web&q=opencode"), "opencode")

    def test_consulta_inexistente(self):
        self.assertEqual(busqueda.consulta_de(""), "")
        self.assertEqual(busqueda.consulta_de("source=web"), "")


class RetoTest(unittest.TestCase):
    """Google responde /sorry/index a QtWebEngine: hay que reconocerlo."""

    def test_reconoce_la_pagina_de_verificacion_de_google(self):
        self.assertEqual(
            busqueda.es_reto("www.google.com", "/sorry/index"), "google")

    def test_reconoce_la_verificacion_de_movil(self):
        self.assertEqual(
            busqueda.es_reto("consent.google.com", "/sorry/index"), "google")

    def test_un_resultado_normal_no_es_reto(self):
        self.assertIsNone(busqueda.es_reto("www.google.com", "/search"))
        self.assertIsNone(
            busqueda.es_reto("search.brave.com", "/search"))

    def test_un_sitio_cualquiera_no_es_reto(self):
        self.assertIsNone(busqueda.es_reto("github.com", "/sorry/index"))
        self.assertIsNone(busqueda.es_reto("", "/sorry/index"))

    def test_consulta_escondida_en_continue(self):
        query = (
            "continue=https%3A%2F%2Fwww.google.com%2Fsearch%3Fq%3Dyoutube"
            "&q=EgS-OTp2GPPx19cG"
        )
        self.assertEqual(busqueda.consulta_de_reto(query), "youtube")

    def test_consulta_con_espacios_en_continue(self):
        query = (
            "?continue=https://www.google.com/search%3Fq%3Dfutbol%2Blibre"
            "&q=abc"
        )
        self.assertEqual(busqueda.consulta_de_reto(query), "futbol libre")

    def test_sin_continue_usa_la_query_propia(self):
        self.assertEqual(busqueda.consulta_de_reto("q=youtube"), "youtube")
        self.assertEqual(busqueda.consulta_de_reto(""), "")


class NombreTest(unittest.TestCase):

    def test_nombre_conocido_y_desconocido(self):
        self.assertEqual(busqueda.nombre("brave"), "Brave Search")
        self.assertEqual(busqueda.nombre("inexistente"), "inexistente")


if __name__ == "__main__":
    unittest.main()

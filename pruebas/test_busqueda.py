# test_busqueda.py
# Pruebas de la elección de motor y del respaldo (sin interfaz).
# El caso real: una red que corta search.brave.com; la búsqueda debe seguir
# funcionando con el motor de respaldo, sin cambiar la preferencia del usuario.

import unittest
from unittest import mock

import config
from modelos import busqueda, motores


class ElegirTest(unittest.TestCase):

    def test_motor_normal_si_responde(self):
        self.assertEqual(busqueda.elegir("brave", set()), "brave")

    def test_usa_respaldo_si_el_motor_esta_caido(self):
        with mock.patch.object(config, "MOTOR_RESPALDO", "duckduckgo"):
            self.assertEqual(busqueda.elegir("brave", {"brave"}), "duckduckgo")

    def test_sin_respaldo_configurado_devuelve_el_original(self):
        with mock.patch.object(config, "MOTOR_RESPALDO", None):
            self.assertEqual(busqueda.elegir("brave", {"brave"}), "brave")

    def test_respaldo_igual_al_motor_no_cambia_nada(self):
        with mock.patch.object(config, "MOTOR_RESPALDO", "brave"):
            self.assertEqual(busqueda.elegir("brave", {"brave"}), "brave")

    def test_respaldo_tambien_caido_devuelve_el_original(self):
        with mock.patch.object(config, "MOTOR_RESPALDO", "duckduckgo"):
            self.assertEqual(
                busqueda.elegir("brave", {"brave", "duckduckgo"}), "brave")

    def test_motor_desconocido_no_se_toca(self):
        with mock.patch.object(config, "MOTOR_RESPALDO", "duckduckgo"):
            self.assertEqual(busqueda.elegir("brave", {"google"}), "brave")


class UrlBusquedaTest(unittest.TestCase):

    def test_url_del_motor_elegido(self):
        url, clave = busqueda.url_busqueda("duckduckgo", "hola mundo", set())
        self.assertEqual(clave, "duckduckgo")
        self.assertEqual(url, "https://duckduckgo.com/?q=hola%20mundo")

    def test_url_con_respaldo(self):
        with mock.patch.object(config, "MOTOR_RESPALDO", "duckduckgo"):
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


class NombreTest(unittest.TestCase):

    def test_nombre_conocido_y_desconocido(self):
        self.assertEqual(busqueda.nombre("brave"), "Brave Search")
        self.assertEqual(busqueda.nombre("inexistente"), "inexistente")


if __name__ == "__main__":
    unittest.main()

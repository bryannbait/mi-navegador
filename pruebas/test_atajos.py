# test_atajos.py
# Comprueba la tabla de atajos: sin colisiones, con los obligatorios y con
# todos los métodos existiendo de verdad en navegador.py.
#
# No importa Qt: atajos_tabla es una tabla de texto pura.

import os
import re
import unittest

from interfaz import atajos_tabla


RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_NAVEGADOR = os.path.join(RAIZ, "navegador.py")


class AtajosTest(unittest.TestCase):

    def test_no_hay_combinaciones_repetidas(self):
        repetidas = atajos_tabla.colisiones()
        self.assertEqual(repetidas, {}, f"atajos duplicados: {repetidas}")

    def test_estan_los_obligatorios(self):
        presentes = set(atajos_tabla.secuencias())
        obligatorios = [
            "Ctrl+L", "Ctrl+T", "Ctrl+W", "Ctrl+Tab", "Ctrl+Shift+Tab",
            "Ctrl+Shift+T", "Ctrl+F", "Ctrl+J", "Ctrl+H", "Ctrl+D",
            "Ctrl+Shift+N", "Ctrl+Shift+W", "F5", "F11", "Esc",
            "Alt+Left", "Alt+Right", "Alt+Home",
        ]
        for secuencia in obligatorios:
            self.assertIn(secuencia, presentes, secuencia)

    def test_las_pestanas_numeradas_van_de_1_a_9(self):
        numeradas = {
            atajos_tabla.normalizar(sec): (metodo, resto[0])
            for sec, metodo, *resto in atajos_tabla.ATAJOS_GLOBALES
            if metodo == "ir_a_pestana"
        }
        for numero in range(1, 9):
            self.assertEqual(numeradas[f"Ctrl+{numero}"],
                             ("ir_a_pestana", numero - 1))
        self.assertEqual(numeradas["Ctrl+9"], ("ir_a_pestana", -1))

    def test_cada_atajo_tiene_forma_valida(self):
        for atajo in atajos_tabla.ATAJOS_GLOBALES:
            self.assertIn(len(atajo), (2, 3), atajo)
            secuencia, metodo = atajo[0], atajo[1]
            self.assertTrue(secuencia, atajo)
            self.assertTrue(metodo, atajo)
            self.assertIsInstance(metodo, str, atajo)
            if len(atajo) == 3:
                self.assertIsInstance(atajo[2], int, atajo)

    def test_todos_los_metodos_existen_en_la_ventana(self):
        with open(RUTA_NAVEGADOR, encoding="utf-8") as archivo:
            codigo = archivo.read()
        for secuencia, metodo, *resto in atajos_tabla.ATAJOS_GLOBALES:
            self.assertIsNotNone(
                re.search(rf"^\s+def {re.escape(metodo)}\(", codigo, re.MULTILINE),
                f"{secuencia} apunta a {metodo}(), que no existe en navegador.py",
            )

    def test_normalizacion(self):
        n = atajos_tabla.normalizar
        self.assertEqual(n("ctrl+l"), "Ctrl+L")
        self.assertEqual(n("Control+L"), "Ctrl+L")
        self.assertEqual(n("shift+ctrl+t"), "Ctrl+Shift+T")
        self.assertEqual(n("Escape"), "Esc")
        self.assertEqual(n("Ctrl+PgDown"), "Ctrl+PgDown")
        self.assertEqual(n("Ctrl+PageDown"), "Ctrl+PgDown")
        self.assertEqual(n("Ctrl+="), "Ctrl+=")
        self.assertEqual(n("alt+home"), "Alt+Home")
        self.assertEqual(n("F5"), "F5")


if __name__ == "__main__":
    unittest.main()

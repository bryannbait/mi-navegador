# pruebas/test_rutas.py
# Comprueba que las rutas centralizadas apuntan a los sitios correctos.
# Es la red de seguridad si algún módulo cambia de carpeta.

import os
import unittest

from privacidad import gestor_bloqueo
import rutas
from descargas import RUTA as RUTA_DESCARGAS
from favoritos import RUTA as RUTA_FAVORITOS
from historial import RUTA as RUTA_HISTORIAL
from preferencias import RUTA as RUTA_PREFERENCIAS


class RutasTest(unittest.TestCase):

    def test_la_raiz_es_la_del_proyecto(self):
        self.assertTrue(os.path.isfile(os.path.join(rutas.RAIZ, "main.py")))
        self.assertTrue(os.path.isdir(rutas.RUTA_DATOS))

    def test_las_listas_estan_donde_toca(self):
        for nombre in ("easylist.txt", "easyprivacy.txt"):
            self.assertTrue(
                os.path.isfile(os.path.join(rutas.RUTA_LISTAS, nombre)),
                nombre,
            )

    def test_las_rutas_de_datos_caen_en_datos(self):
        for ruta in (RUTA_HISTORIAL, RUTA_FAVORITOS, RUTA_DESCARGAS,
                     RUTA_PREFERENCIAS):
            self.assertEqual(os.path.dirname(ruta), rutas.RUTA_DATOS)

    def test_el_gestor_usa_las_rutas_centrales(self):
        self.assertEqual(gestor_bloqueo.CARPETA_LISTAS, rutas.RUTA_LISTAS)
        self.assertEqual(
            os.path.dirname(gestor_bloqueo.RUTA_WHITELIST), rutas.RUTA_DATOS
        )


if __name__ == "__main__":
    unittest.main()

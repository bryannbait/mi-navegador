# servidor_descargas.py
# Servidor HTTP local para probar el panel de descargas sin depender de Internet.
#
# Uso (desde la raíz del proyecto):
#   venv\Scripts\python.exe herramientas\servidor_descargas.py
#   venv\Scripts\python.exe herramientas\servidor_descargas.py --mb 200 --ritmo 2048
#
#   --mb      tamaño del archivo de prueba (por defecto 20)
#   --ritmo   límite en KB/s para poder pausar a tiempo (0 = sin límite)
#   --puerto  puerto local (por defecto 8765)
#
# Luego, en el navegador:  http://127.0.0.1:8765/
#
# Soporta peticiones Range (bytes=inicio-fin), que es lo que usa Qt para
# reanudar una descarga pausada.

import argparse
import sys
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

BLOQUE = 64 * 1024
MAX_MB = 2048

PAGINA = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>Servidor de pruebas de descargas</title>
<style>
  body {{ background:#16161f; color:#e8e8f2; font-family:system-ui,sans-serif;
         max-width:640px; margin:60px auto; line-height:1.6; }}
  a {{ color:#8b7cff; }}
  code {{ background:#23232f; padding:2px 6px; border-radius:6px; }}
</style></head><body>
<h2>Servidor de pruebas</h2>
<p>Archivo de <b>{mb} MB</b>{ritmo}.</p>
<p><a href="/descarga.bin">Descargar descarga.bin</a></p>
<p>Prueba a pausar, reanudar y cancelar desde el panel (Ctrl+J).</p>
<p>Comprueba el tamaño final: <code>{bytes} bytes</code>.</p>
</body></html>
"""


def interpretar_rango(cabecera, total):
    """Traduce una cabecera Range a (inicio, fin) inclusivos.

    Devuelve None si no hay cabecera o no se entiende; en ese caso el
    servidor manda el archivo entero.
    """
    if not cabecera:
        return None
    texto = cabecera.strip()
    if not texto.lower().startswith("bytes="):
        return None

    parte = texto[6:].split(",")[0].strip()
    inicio_texto, separador, fin_texto = parte.partition("-")
    if not separador:
        return None

    try:
        if inicio_texto == "":
            # "bytes=-500": los últimos 500 bytes.
            cantidad = int(fin_texto)
            if cantidad <= 0:
                return None
            inicio = max(0, total - cantidad)
            return inicio, total - 1
        inicio = int(inicio_texto)
        fin = int(fin_texto) if fin_texto else total - 1
    except ValueError:
        return None

    if inicio < 0 or inicio >= total:
        return None
    return inicio, min(fin, total - 1)


class Manejador(BaseHTTPRequestHandler):
    mb = 20
    ritmo_kb = 0

    # ---------- rutas ----------

    def do_GET(self):
        ruta = urlparse(self.path).path
        if ruta in ("/", "/index.html"):
            self._pagina()
        elif ruta == "/descarga.bin":
            self._archivo(con_cuerpo=True)
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "No existe")

    def do_HEAD(self):
        ruta = urlparse(self.path).path
        if ruta == "/descarga.bin":
            self._archivo(con_cuerpo=False)
        elif ruta in ("/", "/index.html"):
            self._pagina(con_cuerpo=False)
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "No existe")

    # ---------- respuestas ----------

    def _pagina(self, con_cuerpo=True):
        ritmo = f" a {self.ritmo_kb} KB/s" if self.ritmo_kb else ""
        cuerpo = PAGINA.format(
            mb=self.mb,
            ritmo=ritmo,
            bytes=self.mb * 1024 * 1024,
        ).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        if con_cuerpo:
            self.wfile.write(cuerpo)

    def _archivo(self, con_cuerpo=True):
        total = self.mb * 1024 * 1024
        rango = interpretar_rango(self.headers.get("Range"), total)

        if rango is None:
            inicio, fin = 0, total - 1
            self.send_response(HTTPStatus.OK)
        else:
            inicio, fin = rango
            self.send_response(HTTPStatus.PARTIAL_CONTENT)
            self.send_header("Content-Range", f"bytes {inicio}-{fin}/{total}")

        enviar = fin - inicio + 1
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(enviar))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header(
            "Content-Disposition",
            f'attachment; filename="prueba-{self.mb}MB.bin"',
        )
        self.end_headers()

        if not con_cuerpo:
            return

        patron = bytes(range(256)) * (BLOQUE // 256)
        # El contenido debe empezar en "inicio", no en 0: giramos el patrón.
        desfase = inicio % 256
        patron = patron[desfase:] + patron[:desfase]
        restante = enviar
        try:
            while restante > 0:
                trozo = patron[: min(BLOQUE, restante)]
                self.wfile.write(trozo)
                restante -= len(trozo)
                if self.ritmo_kb > 0:
                    time.sleep(len(trozo) / (self.ritmo_kb * 1024))
        except (BrokenPipeError, ConnectionResetError):
            # El usuario canceló: es un caso normal en estas pruebas.
            pass

    def log_message(self, formato, *args):
        rango = self.headers.get("Range") if self.headers else None
        extra = f"  [Range: {rango}]" if rango else ""
        sys.stderr.write(
            f"{self.address_string()} {formato % args}{extra}\n"
        )


def main(argv=None):
    analizador = argparse.ArgumentParser(
        description="Servidor local para probar descargas."
    )
    analizador.add_argument("--mb", type=int, default=20,
                            help="tamaño en MB (por defecto 20)")
    analizador.add_argument("--puerto", type=int, default=8765,
                            help="puerto local (por defecto 8765)")
    analizador.add_argument("--ritmo", type=int, default=0,
                            help="límite en KB/s; 0 = sin límite")
    args = analizador.parse_args(argv)

    mb = max(1, min(args.mb, MAX_MB))
    Manejador.mb = mb
    Manejador.ritmo_kb = max(0, args.ritmo)

    servidor = ThreadingHTTPServer(("127.0.0.1", args.puerto), Manejador)
    print(f"Sirviendo un archivo de {mb} MB en "
          f"http://127.0.0.1:{args.puerto}/")
    print("Ctrl+C para parar.")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nParado.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()

# servidor_cabeceras.py
# Servidor local que muestra las cabeceras HTTP que manda el navegador.
#
# Uso (desde la raíz del proyecto):
#   venv\Scripts\python.exe herramientas\servidor_cabeceras.py
#   venv\Scripts\python.exe herramientas\servidor_cabeceras.py --puerto 8080
#
# Abrir http://127.0.0.1:8000/ y comparar con el escudo activado y desactivado:
#   - User-Agent: no debe contener "QtWebEngine"
#   - Accept-Language: debe ser el de config.FP_ACCEPT_LANGUAGE
#   - Sec-GPC: 1 con el escudo, ausente sin él
#   - Sec-CH-UA: debe coincidir con lo que anuncia navigator.userAgentData

import argparse
import html
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Cabeceras que interesan para la huella (el resto también se muestran).
DESTACADAS = ("user-agent", "accept-language", "sec-gpc", "sec-ch-ua",
              "sec-ch-ua-mobile", "sec-ch-ua-platform", "dnt", "referer")

PAGINA = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>Cabeceras recibidas</title>
<style>
  body {{ background:#0e0e13; color:#e8e8f2; margin:0; padding:40px 24px;
         font-family:"Segoe UI", system-ui, sans-serif; }}
  main {{ max-width:820px; margin:0 auto; }}
  h1 {{ font-size:22px; margin:0 0 6px 0; }}
  .sub {{ color:#9b9bb4; font-size:13px; margin-bottom:22px; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; }}
  th, td {{ text-align:left; padding:8px 10px; border-bottom:1px solid #2f2f40;
            vertical-align:top; }}
  th {{ color:#9b9bb4; font-weight:600; width:34%; white-space:nowrap; }}
  td {{ font-family:ui-monospace, Consolas, monospace; word-break:break-word; }}
  tr.destacada td {{ color:#a78bfa; }}
  .aviso {{ margin-top:22px; padding:14px 16px; border-radius:10px;
            background:#1e1e28; color:#9b9bb4; font-size:12px; line-height:1.6; }}
  code {{ background:#23232f; padding:2px 6px; border-radius:6px; }}
</style></head>
<body><main>
  <h1>Cabeceras que envía este navegador</h1>
  <div class="sub">Petición a <code>{ruta}</code> · servidor local, sin red.</div>
  <table><tbody>
{filas}
  </tbody></table>
  <div class="aviso">
    Con el escudo anti-fingerprinting activo, <code>User-Agent</code> no debe
    contener <code>QtWebEngine</code>, <code>Accept-Language</code> debe ser el
    configurado y <code>Sec-GPC</code> debe valer <code>1</code>. Desactívalo en
    el menú del escudo y recarga para comparar.
  </div>
</main></body></html>
"""


def clasificar(cabeceras):
    """Separa (nombre, valor) en destacadas y resto, ordenadas.

    Acepta cualquier iterable de pares (dict.items(), lista de tuplas...).
    """
    elementos = sorted(cabeceras, key=lambda par: par[0].lower())
    destacadas = [p for p in elementos if p[0].lower() in DESTACADAS]
    resto = [p for p in elementos if p[0].lower() not in DESTACADAS]
    return destacadas, resto


def construir_html(cabeceras, ruta):
    destacadas, resto = clasificar(cabeceras)
    lineas = []
    for nombre, valor in destacadas + resto:
        clase = ' class="destacada"' if (nombre, valor) in destacadas else ""
        lineas.append(
            f"    <tr{clase}><th>{html.escape(nombre)}</th>"
            f"<td>{html.escape(valor)}</td></tr>"
        )
    return PAGINA.format(ruta=html.escape(ruta), filas="\n".join(lineas))


class Manejador(BaseHTTPRequestHandler):

    def do_GET(self):
        cuerpo = construir_html(self.headers.items(), self.path).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, formato, *args):
        sys.stderr.write(f"{self.address_string()} {formato % args}\n")
        for nombre in ("User-Agent", "Accept-Language", "Sec-GPC",
                       "Sec-CH-UA"):
            valor = self.headers.get(nombre)
            if valor:
                sys.stderr.write(f"    {nombre}: {valor}\n")


def main(argv=None):
    analizador = argparse.ArgumentParser(
        description="Muestra las cabeceras HTTP que envía el navegador."
    )
    analizador.add_argument("--puerto", type=int, default=8000,
                            help="puerto local (por defecto 8000)")
    args = analizador.parse_args(argv)

    servidor = ThreadingHTTPServer(("127.0.0.1", args.puerto), Manejador)
    print(f"Escuchando en http://127.0.0.1:{args.puerto}/")
    print("Ctrl+C para parar.")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nParado.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()

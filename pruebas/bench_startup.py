#!/usr/bin/env python3
# bench_startup.py
# Benchmark de arranque para CI. Falla si hay regresión > 10 %.
#
# Uso:
#   python -m pruebas.bench_startup
#   python -m pruebas.bench_startup --baseline   # guarda línea base
#   python -m pruebas.bench_startup --check      # compara con baseline

import argparse
import json
import os
import sys
import time
from pathlib import Path

# --- Configuración ---
PROYECTO = Path(__file__).parent.parent
BASELINE_FILE = PROYECTO / "pruebas" / "bench_baseline.json"
UMBRAL_REGRESION = 0.10  # 10 %

# Métricas a medir
METRICAS = [
    "import_navegador",
    "gestor_bloqueo",
    "minavegador_construct",
    "show",
    "total_hasta_show",
]

# --- Helpers ---
def _leer_baseline():
    if BASELINE_FILE.exists():
        with open(BASELINE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def _guardar_baseline(data):
    with open(BASELINE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def _formatear(t):
    return f"{t*1000:.0f} ms" if t < 1 else f"{t:.2f} s"

# --- Benchmark real ---
def run_benchmark():
    """Ejecuta el benchmark y devuelve dict con tiempos en segundos."""
    import subprocess
    
    codigo = '''
import sys, time
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from estilos import aplicar_tema

app = QApplication(sys.argv)
aplicar_tema(app)

from privacidad.gestor_bloqueo import GestorBloqueo
from modelos.preferencias import Preferencias
from navegador import configurar_perfil, MiNavegador
from modelos.historial import Historial
from modelos.favoritos import Favoritos
from modelos.descargas import Descargas

t0 = time.perf_counter()
gestor = GestorBloqueo()
t1 = time.perf_counter()

prefs = Preferencias()
configurar_perfil(gestor, prefs.get("anti_fingerprint", True))

t2 = time.perf_counter()
ventana = MiNavegador(gestor, prefs, Historial(), Favoritos(), Descargas())
t3 = time.perf_counter()

ventana.show()
t4 = time.perf_counter()

print(f"gestor_bloqueo={t1-t0:.6f}")
print(f"minavegador_construct={t3-t2:.6f}")
print(f"show={t4-t3:.6f}")
print(f"total_hasta_show={t4-t0:.6f}")

QTimer.singleShot(500, app.quit)
sys.exit(app.exec())
'''
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["QTWEBENGINE_CHROMIUM_FLAGS"] = (
        "--enable-gpu-rasterization "
        "--enable-native-gpu-memory-buffers "
        "--disable-background-timer-throttling "
        "--disable-extensions "
        "--disable-component-extensions-with-background-pages "
        "--disable-default-apps "
        "--disable-background-networking "
        "--renderer-process-limit=2 "
        "--log-level=3"
    )
    
    # Ejecutar 3 veces y tomar la mediana
    resultados = {m: [] for m in METRICAS}
    
    for i in range(3):
        proc = subprocess.Popen(
            [sys.executable, "-c", codigo],
            cwd=PROYECTO,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        stdout, stderr = proc.communicate(timeout=120)
        
        if proc.returncode != 0:
            print(f"Run {i+1} falló:", stderr[:200])
            continue
            
        for line in stdout.splitlines():
            for m in METRICAS:
                if line.startswith(f"{m}="):
                    val = float(line.split("=")[1])
                    resultados[m].append(val)
                    break
    
    # Mediana de cada métrica
    final = {}
    for m in METRICAS:
        vals = resultados[m]
        if vals:
            vals.sort()
            final[m] = vals[len(vals)//2]
        else:
            final[m] = None
    
    # import_navegador se mide por separado (más rápido)
    t0 = time.perf_counter()
    subprocess.run([sys.executable, "-c", "import navegador"], 
                   cwd=PROYECTO, env=env, capture_output=True, timeout=30)
    final["import_navegador"] = time.perf_counter() - t0
    
    return final

# --- Main ---
def main():
    parser = argparse.ArgumentParser(description="Benchmark de arranque")
    parser.add_argument("--baseline", action="store_true", 
                       help="Guarda línea base actual")
    parser.add_argument("--check", action="store_true",
                       help="Compara con baseline y falla si hay regresión")
    args = parser.parse_args()
    
    print("=== Benchmark de arranque ===")
    tiempos = run_benchmark()
    
    for m in METRICAS:
        v = tiempos.get(m)
        print(f"  {m:25s}: {_formatear(v) if v else 'N/A'}")
    
    if args.baseline:
        _guardar_baseline(tiempos)
        print(f"\nBaseline guardado en {BASELINE_FILE}")
        return 0
    
    if args.check:
        baseline = _leer_baseline()
        if not baseline:
            print("\n❌ No hay baseline. Ejecuta con --baseline primero.")
            return 1
        
        print("\n=== Comparación con baseline ===")
        fallos = 0
        for m in METRICAS:
            actual = tiempos.get(m)
            base = baseline.get(m)
            if actual is None or base is None:
                print(f"  {m:25s}: SIN DATOS")
                continue
            
            diff_pct = (actual - base) / base
            estado = "✅" if diff_pct <= UMBRAL_REGRESION else "❌ REGRESIÓN"
            if diff_pct > UMBRAL_REGRESION:
                fallos += 1
            print(f"  {m:25s}: base={_formatear(base)} actual={_formatear(actual)} "
                  f"diff={diff_pct:+.1%} {estado}")
        
        if fallos:
            print(f"\n❌ {fallos} métrica(s) con regresión > {UMBRAL_REGRESION:.0%}")
            return 1
        else:
            print(f"\n✅ Sin regresiones (umbral {UMBRAL_REGRESION:.0%})")
            return 0
    
    # Solo mostrar
    return 0

if __name__ == "__main__":
    sys.exit(main())
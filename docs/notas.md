# Proyecto: Mi Navegador

## Estado actual: Nivel 10 completado (versión 1.3)

## Archivos:
- main.py           → punto de entrada (crea los modelos y la ventana)
- navegador.py      → clase MiNavegador (la ventana)
- estilos.py        → hoja de estilos QSS + paleta oscura
- rutas.py          → rutas absolutas: datos/, listas/ y assets/
- config.py         → colores, versión y opciones de privacidad
- privacidad/       → anti_fingerprint.py (Nivel 10), bloqueador.py (red + Sec-GPC)
                      y gestor_bloqueo.py (motor adblock Rust)
- modelos/          → modelo_json.py, historial.py, favoritos.py, descargas.py,
                      preferencias.py y motores.py
- interfaz/         → pestanas.py, pagina_inicio.py, atajos_vim.py, puente_vim.py
                      y las ventanas de historial, favoritos, descargas e incógnito
- requirements.txt  → dependencias (pip install -r requirements.txt)
- requirements-dev.txt → herramientas de desarrollo (ruff)
- pyproject.toml    → configuración de ruff
- iniciar.bat       → lanzador con doble clic
- pruebas.bat       → lanzador de pruebas
- datos/            → estado local: historial, favoritos, descargas, preferencias y whitelist
- docs/             → esta nota, guía de estudio, PRIVACIDAD.md y el leeme del rediseño
- pruebas/          → pruebas unitarias (unittest)

## Pendiente:
- Nivel 8: atajos de teclado completos (Vim hecho; faltan pruebas a mano)
- Nivel 9: descargas (panel hecho; falta probar con descargas grandes)
- Nivel 11: extras
- Nivel 10: probar a mano contra browserleaks/coveryourtracks (las pruebas
  automáticas ya pasan: UA, idiomas, pantalla, canvas, WebGL, media, toggle)

## Cómo lanzar:
Doble clic en iniciar.bat (usa el venv automáticamente).
O en CMD, sin activar nada:
  cd "C:\Users\Bal\Desktop\Organizado\Projecto Navegador\mi-navegador"
  venv\Scripts\python.exe main.py

## Pruebas:
  venv\Scripts\python.exe -m unittest discover -s pruebas -v
  (o doble clic en pruebas.bat)

## Linter:
  venv\Scripts\pip install -r requirements-dev.txt
  venv\Scripts\ruff.exe check .

Nota: si ejecutas "python main.py" con el Python del sistema, main.py
detecta que falta PyQt6 y se relanza solo con el venv del proyecto.

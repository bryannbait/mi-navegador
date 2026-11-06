# Proyecto: Mi Navegador

## Estado actual: Nivel 10 completado (versión 1.3)

## Archivos:
- main.py           → punto de entrada (crea los modelos y la ventana)
- navegador.py      → clase MiNavegador (la ventana) y estilos
- bloqueador.py     → interceptor de red (+ cabecera Sec-GPC)
- gestor_bloqueo.py → motor adblock (Rust)
- anti_fingerprint.py → Nivel 10: UA limpio, idiomas y camuflaje de APIs (nuevo)
- historial.py      → modelo historial
- ventana_historial.py
- favoritos.py      → modelo favoritos
- ventana_favoritos.py
- descargas.py       → modelo descargas
- ventana_descargas.py
- ventana_incognito.py → ventana incógnito (modelos solo en RAM + perfil protegido)
- atajos_vim.py     → atajos estilo Vim
- puente_vim.py     → detecta si el foco está en un input de la web
- requirements.txt  → dependencias (pip install -r requirements.txt)
- preferencias.py   → ajustes
- motores.py        → catálogo de buscadores
- config.py         → colores, versión y opciones de privacidad
- iniciar.bat       → lanzador con doble clic
- PRIVACIDAD.md     → qué protege el Nivel 10, límites y cómo comprobarlo

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

Nota: si ejecutas "python main.py" con el Python del sistema, main.py
detecta que falta PyQt6 y se relanza solo con el venv del proyecto.
# Proyecto: Mi Navegador

## Estado actual: Nivel 7 completado

## Archivos:
- main.py           → punto de entrada (crea los modelos y la ventana)
- navegador.py      → clase MiNavegador (la ventana) y estilos
- bloqueador.py     → interceptor de red
- gestor_bloqueo.py → motor adblock (Rust)
- historial.py      → modelo historial
- ventana_historial.py
- favoritos.py      → modelo favoritos
- ventana_favoritos.py
- descargas.py       → modelo descargas
- ventana_descargas.py
- ventana_incognito.py → ventana incógnito (modelos solo en RAM)
- atajos_vim.py     → atajos estilo Vim
- puente_vim.py     → detecta si el foco está en un input de la web
- requirements.txt  → dependencias (pip install -r requirements.txt)
- preferencias.py   → ajustes
- motores.py        → catálogo de buscadores
- config.py         → colores y constantes
- iniciar.bat       → lanzador con doble clic

## Pendiente:
- Nivel 8: atajos de teclado completos (Vim hecho; faltan pruebas a mano)
- Nivel 9: descargas (panel hecho; falta probar con descargas grandes)
- Nivel 10: anti-fingerprinting
- Nivel 11: extras

## Cómo lanzar:
Doble clic en iniciar.bat
O en CMD:
  cd %USERPROFILE%\Desktop\mi-navegador
  venv\Scripts\activate
  python main.py
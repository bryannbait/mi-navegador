# Pruebas manuales

Lo que no se puede automatizar (diálogos nativos, ventanas reales, red) se
prueba aquí. Cada bloque se firma con fecha al terminarlo.

## Preparación: servidor local de descargas

```bat
cd "C:\Users\Bal\Desktop\Organizado\Projecto Navegador\mi-navegador"
venv\Scripts\python.exe herramientas\servidor_descargas.py --mb 200
```

- `--mb N`: tamaño del archivo (por defecto 20).
- `--ritmo KB/s`: límite de velocidad. Con `--ritmo 512` un archivo de 200 MB
  tarda ~7 minutos y da tiempo a pausar, cancelar y cerrar la app.
- Abrir `http://127.0.0.1:8765/` y descargar `descarga.bin`.

El servidor acepta `Range`, que es lo que usa Qt al reanudar una descarga
pausada. Las pruebas automáticas de `pruebas/test_descargas.py` cubren el
modelo y el servidor; lo de abajo cubre la interfaz y el diálogo nativo.

## Nivel 9 — Descargas

Fecha: ____ / ____ / ______

| # | Escenario | Cómo | Resultado esperado | ✔ |
|---|---|---|---|---|
| 1 | Archivo grande con pausa | `--mb 200 --ritmo 512`, pausar a mitad y reanudar | Progreso avanza, se detiene al pausar, continúa al reanudar y termina con el tamaño exacto (`200 MB` = 209.715.200 B) | ☐ |
| 2 | Cancelar a mitad | Cancelar al 30 % | Estado **Cancelada**, sin fila colgada, archivo parcial en disco | ☐ |
| 3 | Cerrar la app a mitad | Lanzar descarga, cerrar la ventana sin esperar | Al abrir: entrada **Interrumpida**; el panel responde y ofrece **Reintentar** | ☐ |
| 4 | Tres descargas a la vez | Abrir tres pestañas con el mismo archivo y aceptar las tres | Tres filas independientes, progreso por separado, todas completan | ☐ |
| 5 | Cancelar el diálogo "Guardar como" | Lanzar descarga y pulsar Cancelar en el diálogo | No se crea ninguna entrada en el panel ni en `datos/descargas.json` | ☐ |
| 6 | Abrir archivo y carpeta | Con una descarga completada, pulsar **Abrir** y **Abrir carpeta** | Se abre el archivo con su programa y el Explorador en la carpeta | ☐ |
| 7 | Historial y tope | Descargar más de 200 archivos (o editar el JSON) | Solo se conservan las 200 últimas; **Borrar historial** deja el JSON vacío | ☐ |
| 8 | Reintentar | Con una entrada cancelada/interrumpida de una URL http(s), pulsar **Reintentar** | Se abre la URL en una pestaña nueva y vuelve a pedir el archivo | ☐ |

Notas de la última pasada:

-

## Nivel 10 — Privacidad

_(se completa en la fase A3)_

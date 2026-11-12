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

### Comprobación automática (página local, sin red)

Ejecutada el 12/11/2026 con el escudo activado, en una ventana real:

| Dato | Valor observado | Esperado | ✔ |
|---|---|---|---|
| `navigator.userAgent` | `...Chrome/140.0.0.0 Safari/537.36` (sin `QtWebEngine`) | Sin rastro de Qt | ✔ |
| `navigator.platform` | `Win32` | Coherente con el UA | ✔ |
| `navigator.vendor` | `Google Inc.` | Genérico | ✔ |
| Idioma / idiomas | `es-MX` / `es-MX, es, en-US, en` | Los de `config.py` | ✔ |
| `hardwareConcurrency` | `8` | `FP_NUCLEOS` | ✔ |
| `deviceMemory` | `8` | `FP_MEMORIA_GB` | ✔ |
| GPC | `true` | `FP_ENVIAR_GPC` | ✔ |
| `maxTouchPoints` / `webdriver` | `0` / `false` | Genéricos | ✔ |
| Pantalla | `1366 × 768`, 24 bits | Resolución de escritorio común | ✔ |
| `Intl` locale | `es-MX` | Igual que `navigator.language` | ✔ |
| Plugins | `0` | — | ✔ |
| Hash del canvas | `72b01e7a` (cambia en cada arranque) | Distinto por sesión | ✔ |
| WebGL | `Google Inc. (Intel) · ANGLE (Intel, UHD Graphics 620…)` | Genérico | ✔ |
| `navigator.userAgentData` | **no disponible** | — | ⚠ limitación conocida |

La última fila es real: QtWebEngine no implementa `navigator.userAgentData`, así
que la cabecera `Sec-CH-UA` y la API de JS no coinciden. Está documentado en
`docs/PRIVACIDAD.md` como pendiente.

### Checklist manual

Fecha: ____ / ____ / ______

| # | Comprobación | Cómo | Resultado esperado | ✔ |
|---|---|---|---|---|
| 1 | Página local con escudo ON | Escudo → «Comprobar mi huella» | Valores genéricos (tabla de arriba) | ☐ |
| 2 | Página local con escudo OFF | Desactivar y recargar | Aparecen los valores reales del equipo | ☐ |
| 3 | Cabeceras con escudo ON | `servidor_cabeceras.py` | Sin `QtWebEngine`, `Accept-Language` configurado, `Sec-GPC: 1` | ☐ |
| 4 | Cabeceras con escudo OFF | Desactivar y recargar | UA original con `QtWebEngine`, sin `Sec-GPC` | ☐ |
| 5 | Canvas estable | browserleaks.com/canvas, recargar dos veces | Mismo hash en la misma sesión; distinto tras reiniciar | ☐ |
| 6 | WebGL | browserleaks.com/webgl | Vendor/renderer genéricos | ☐ |
| 7 | Informe general | coveryourtracks.eff.org y creepjs | Sin valores únicos; el canvas no es el mismo que en Chrome | ☐ |

Notas de la última pasada:

-

## Nivel 11 — Sesión y pestañas

### Comprobación automática

Ejecutada el 12/11/2026 en ventanas reales:

| Escenario | Resultado observado | ✔ |
|---|---|---|
| Guardar 3 pestañas (una de inicio) al cerrar | `sesion.json` con `version: 1`, `activa: 1` y las URLs en orden | ✔ |
| Reabrir | 3 pestañas, mismas URLs y la misma activa | ✔ |
| Restauración diferida | Al arrancar solo hay 1 `QWebEngineView`; las demás son marcadores. Al pulsar otra pestaña se crea su vista (21 ms) y carga su URL | ✔ |
| Incógnito | Abre y cierra pestañas sin tocar `sesion.json` | ✔ |
| 30 pestañas guardadas | Construcción de la ventana: **0,53 s** (antes 4,44 s creando las 30 vistas); primera página cargada en 0,95 s | ✔ |
| Modelo (`pruebas/test_sesion.py`) | 21 pruebas: corrupción, versión distinta, tope, clamps, memoria | ✔ |

### Checklist manual

Fecha: ____ / ____ / ______

| # | Comprobación | Cómo | Resultado esperado | ✔ |
|---|---|---|---|---|
| 1 | Ida y vuelta real | Abrir 4 pestañas con sitios distintos, cerrar la ventana y volver a abrir | Se reabren en el mismo orden; la activa es la misma | ☐ |
| 2 | Solo la activa carga al arrancar | Abrir 10 pestañas, cerrar y reabrir | Solo la activa descarga de inmediato; las demás cargan al pulsarlas | ☐ |
| 3 | Archivo corrupto | Cerrar, estropear `datos/sesion.json` a mano y abrir | Arranca con una pestaña de inicio; el archivo se reescribe al cerrar | ☐ |
| 4 | Incógnito | Abrir incógnito, navegar y cerrar; luego abrir la ventana normal | La sesión normal no cambia | ☐ |
| 5 | Restauración desactivada | (B5) Desactivar «Restaurar sesión» en el menú y cerrar | No se guarda nada; al abrir sale una pestaña nueva | ☐ |

Notas de la última pasada:

-

## Nivel 11 — Pestañas fijadas

### Comprobación automática

Ejecutada el 12/11/2026 en ventanas reales:

| Escenario | Resultado observado | ✔ |
|---|---|---|
| Fijar una pestaña | Se mueve al principio y muestra el icono de pin | ✔ |
| Fijar una segunda | Se coloca al final del bloque de fijadas (orden entre ellas estable) | ✔ |
| Desfijar | Sale del bloque y queda justo detrás de las fijadas; vuelve su favicon | ✔ |
| `Ctrl+Shift+P` | Alterna el estado de la pestaña actual (acción registrada y disparada) | ✔ |
| Cerrar y reabrir (`Ctrl+Shift+T`) | La pestaña vuelve con su estado de fijada | ✔ |
| Datos por pestaña al arrastrar | `setTabData` viaja con la pestaña: mover una fijada a la derecha conserva su estado | ✔ |
| Guardar y restaurar | `sesion.json` guarda `fijada` y la restauración pone las fijadas primero, remapeando el índice activo | ✔ |

### Checklist manual

Fecha: ____ / ____ / ______

| # | Comprobación | Cómo | Resultado esperado | ✔ |
|---|---|---|---|---|
| 1 | Menú contextual | Clic derecho en una pestaña | «Fijar pestaña», «Cerrar pestaña», «Reabrir pestaña cerrada» | ☐ |
| 2 | Icono visible | Fijar una pestaña con favicon | Se ve el pin a la izquierda; al desfijar vuelve el favicon | ☐ |
| 3 | Arrastrar | Arrastrar una fijada entre las demás fijadas | Se reordena sin perder el pin | ☐ |
| 4 | Persistencia | Fijar dos, cerrar y abrir | Las dos aparecen a la izquierda y con pin | ☐ |
| 5 | Cerrar una fijada | Cerrarla y pulsar `Ctrl+Shift+T` | Vuelve fijada a la izquierda | ☐ |

Notas de la última pasada:

-


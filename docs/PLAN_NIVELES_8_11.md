# Plan: cerrar Niveles 8-10 y construir el Nivel 11

> Estado: **propuesta para revisar**. No se ha modificado código.
> Base: `main` en `1dc3d20` (fusión de la reestructuración), 21 tests OK, ruff limpio.

## 1. Objetivo

1. **Cerrar los niveles 8, 9 y 10** con pruebas reales y los ajustes que salgan de ellas.
2. **Nivel 11** con dos funciones nuevas:
   - Restaurar sesión y pestañas fijadas.
   - Modo lectura y zoom recordado por sitio.

## 2. Estado de partida (inventario)

| Área | Hoy |
|---|---|
| Atajos globales | 18 acciones en `navegador._crear_atajos` (Ctrl+L/K, Ctrl+T/W, Ctrl+J, Ctrl+H/D, Ctrl+Shift+N/O/B, Ctrl+Tab, F5, Esc, Alt+flechas/Inicio) |
| Atajos Vim | `j/k/d/u/G/f/F/r/t/x/J/K/H/?/i`, comandos `:t`, `:q`, `:open`, `:hist`, `:fav`, `:inc`, `:top`, búsqueda `/` |
| Descargas | Panel con progreso, pausa/reanudar, cancelar, abrir archivo/carpeta; historial de 200; “en curso” pasa a “interrumpida” al reiniciar |
| Privacidad | UA limpio, Client Hints, idiomas, ruido canvas/WebGL, GPC, interruptor del escudo; sin pruebas automáticas en el repo |
| Pestañas | `Pestanas` envuelve `QTabBar` + `QStackedWidget`; sin fijar, sin reabrir cerradas, sin selección por número |
| Zoom / lectura | No existe |
| Sesión | No se guarda: al cerrar se pierden las pestañas |

## 3. Reglas para esta iteración

- **Sin dependencias nuevas** salvo justificación explícita (nada de Readability, nada de red).
- Todo dato personal nuevo vive en `datos/` (ignorado por git).
- **Incógnito nunca escribe** sesión, zoom ni lectura.
- Un **commit por fase**, en rama `nivel-8-11`, con `main` intacto hasta el final.
- Cada fase termina con: `unittest` verde, `ruff check` limpio y prueba manual anotada.
- Si una fase falla: se revierte esa fase y se reporta; no se encadena la siguiente.

## 4. Secuencia

| Fase | Contenido | Entregable |
|---|---|---|
| 0 | Línea base y tag `pre-niveles` | Tag + tablero de pruebas manuales vacío |
| A1 | Nivel 8: atajos | `docs/ATAJOS.md` + atajos nuevos + matriz manual |
| A2 | Nivel 9: descargas | Servidor local de pruebas + correcciones + informe |
| A3 | Nivel 10: privacidad | Tests puros + página de diagnóstico + checklist |
| B1 | Sesión | `modelos/sesion.py` + guardar/restaurar + tests |
| B2 | Pestañas fijadas | Menú contextual + orden + persistencia + tests |
| B3 | Zoom por sitio | `modelos/zoom.py` + atajos + persistencia + tests |
| B4 | Modo lectura | `interfaz/modo_lectura.py` + botón + atajo |
| B5 | Integración y cierre | Menú, versión 1.4, docs, merge |

---

## Bloque A — Cerrar 8, 9 y 10

### A1 · Nivel 8: atajos completos

**Problema actual:** hay 18 atajos globales, pero faltan los de gestión de pestañas y ventana, no hay tabla única y no existe una prueba manual reproducible.

**Añadir (núcleo):**

| Atajo | Acción |
|---|---|
| `Ctrl+Shift+T` | Reabrir última pestaña cerrada (pila de 10) |
| `Ctrl+1..8` | Ir a la pestaña 1..8 |
| `Ctrl+9` | Ir a la última pestaña |
| `Ctrl+PageDown` / `Ctrl+PageUp` | Siguiente / anterior (alias de Ctrl+Tab) |
| `F11` | Pantalla completa |
| `Ctrl+Shift+W` | Cerrar ventana |
| `Ctrl+Shift+P` | Fijar/desfijar pestaña (se implementa en B2) |
| `Ctrl+Alt+R` | Modo lectura (se implementa en B4) |
| `Ctrl+=` / `Ctrl+-` / `Ctrl+0` | Zoom (se implementa en B3) |

**Opcional (decidir):** `Ctrl+F` (buscar en página con la API `findText`), `Ctrl+P` (imprimir a PDF), `Ctrl+Shift+I` (DevTools). Los dos últimos no son triviales con QtWebEngine y propongo dejarlos fuera.

**Diseño:**
- Pila de cerradas: lista de `(url, titulo)` en memoria, máximo 10; se llena en `cerrar_pestana` y se consume con `nueva_pestana(url)`.
- Tabla de atajos única en `navegador._crear_atajos` para evitar duplicados; prueba que detecte colisiones.
- `docs/ATAJOS.md`: tabla completa (global, Vim, comandos `:`).

**Verificación:**
- Prueba automática de la tabla: sin atajos duplicados y con los obligatorios presentes.
- Matriz manual en 3 contextos: ventana, página y campo de texto. Ningún atajo debe disparar mientras se escribe en un input.
- Reabrir 3 pestañas seguidas, incluyendo una fijada (cuando exista B2).

**Archivos:** `navegador.py`, `interfaz/atajos_vim.py`, `docs/ATAJOS.md`, `pruebas/test_atajos.py`.

**Aceptación:** tabla completa, 0 conflictos, matriz manual pasada, tests verdes.

---

### A2 · Nivel 9: descargas

**Problema actual:** el flujo pide siempre “Guardar como”, no hay reintento y el comportamiento con archivos grandes, cancelaciones y reinicios no está probado de forma reproducible.

**Escenarios obligatorios:**

1. Archivo local de ~200 MB: progreso, pausa, reanudar, completar.
2. Cancelar a mitad: estado `cancelada`, sin fila colgada.
3. Cerrar la app a mitad: al abrir, la entrada queda `interrumpida` y el panel responde.
4. Tres descargas simultáneas.
5. Cancelar el diálogo “Guardar como”: no crea entrada.
6. Abrir archivo y carpeta desde el panel.
7. Historial: tope de 200 y borrado.

**Diseño:**
- `herramientas/servidor_descargas.py`: servidor HTTP local con soporte `Range` y un archivo generado al vuelo (no se commitea).
- Botón **“Reintentar”** para entradas `interrumpida`/`cancelada`: abre la URL origen en una pestaña (no se puede reanudar una descarga muerta de Qt).
- Ajuste: si el archivo destino ya existe, pedir confirmación (hoy el diálogo ya lo hace).
- Pruebas de modelo ampliadas; el panel se prueba a mano.

**Verificación:** los 7 escenarios, con captura del estado final del JSON.

**Archivos:** `interfaz/ventana_descargas.py`, `modelos/descargas.py`, `herramientas/servidor_descargas.py`, `pruebas/test_descargas.py`, `docs/PRUEBAS_MANUALES.md`.

**Aceptación:** 200 MB sin congelar la UI; pausa/reanudar funciona; reinicio deja `interrumpida`; reintento abre el origen.

---

### A3 · Nivel 10: privacidad comprobable

**Problema actual:** las pruebas existen en la cabeza del autor, no en el repo; no hay forma de ver los valores que ve la web sin ir a un sitio externo.

**Diseño:**

1. **Tests puros** (`pruebas/test_anti_fingerprint.py`):
   - `limpiar_user_agent`, `cabecera_client_hints`, `plataforma_js`, `plataforma_ua`.
   - `generar_js` contiene el ruido y no contiene valores reales del equipo.
   - `activar/quitar/esta_activo` quedan documentados como manuales (requieren perfil y display).
2. **Página interna de diagnóstico** (`interfaz/pagina_privacidad.py`):
   - HTML local generado, sin red.
   - Muestra UA, plataforma, idiomas, `hardwareConcurrency`, `deviceMemory`, pantalla, zona horaria, renderer WebGL y hash de canvas.
   - Se abre con un botón del menú o `:privacidad`.
3. **Servidor de cabeceras** (`herramientas/servidor_cabeceras.py`):
   - Imprime `User-Agent`, `Accept-Language`, `Sec-GPC` y `sec-ch-ua` recibidos.
   - Se abre en `http://127.0.0.1:8000` para comparar con el escudo activado/desactivado.
4. **Checklist manual** en `docs/PRUEBAS_MANUALES.md`:
   - browserleaks: Canvas, WebGL, Client Hints, Hardware.
   - coveryourtracks (EFF).
   - Comparación con el escudo ON/OFF.
5. **Límites documentados:** fuentes, renderer real de WebGL, TLS, IP y extensiones no se cubren.

**Verificación:** tests verdes; página interna coherente con el servidor local; checklist firmada.

**Archivos:** `privacidad/anti_fingerprint.py` (solo si hace falta exponer algo), `interfaz/pagina_privacidad.py`, `herramientas/servidor_cabeceras.py`, `pruebas/test_anti_fingerprint.py`, `docs/PRUEBAS_MANUALES.md`.

**Aceptación:** mismo UA/idiomas en página interna, servidor y browserleaks; GPC presente con el escudo ON y ausente OFF.

---

## Bloque B — Nivel 11

### B1 · Restaurar sesión

**Formato** (`datos/sesion.json`, ignorado por git):

```json
{
  "version": 1,
  "activa": 0,
  "pestanas": [
    {"url": "https://ejemplo.com", "titulo": "Ejemplo", "fijada": true},
    {"nueva": true, "fijada": false}
  ]
}
```

**Diseño:**
- `modelos/sesion.py`: cargar/guardar, validar versión, tolerar JSON corrupto, tope de 30 pestañas.
- Guardar en `closeEvent` antes de guardar los modelos, solo en ventana normal.
- No guardar URLs internas (`about:`, `data:`, `file:`); se serializan como `{"nueva": true}`.
- Restaurar al final de `MiNavegador.__init__`: las fijadas primero, luego el resto; índice activo validado.
- Incógnito: sin lectura ni escritura.
- Si no hay sesión o está vacía: una pestaña de inicio como hoy.

**Riesgo:** arranque lento con muchas pestañas. Mitigación: tope 30; medir; si supera 2 s, cargar solo la activa y diferir el resto (fase B1b opcional).

**Tests:** guardar/cargar, corrupción, tope, orden fijadas, índice fuera de rango, incógnito no escribe.

**Archivos:** `modelos/sesion.py`, `navegador.py`, `pruebas/test_sesion.py`.

---

### B2 · Pestañas fijadas

**Diseño:**
- Estado por pestaña con `QTabBar.setTabData` (`{"fijada": bool}`).
- Menú contextual en la barra: “Fijar/Desfijar pestaña”, “Cerrar pestaña”.
- Al fijar, reordenar a la izquierda; al restaurar, fijadas primero.
- Indicador visual: `QLabel` con icono `pin` en el lado izquierdo de la pestaña (nuevo SVG en `assets/icons/`).
- Atajo `Ctrl+Shift+P`.
- Cerrar una fijada permitido (como Chrome); se puede reabrir con `Ctrl+Shift+T`.

**Tests:** estado por índice sobrevive a mover pestañas; serialización; restaurar orden.

**Archivos:** `interfaz/pestanas.py`, `navegador.py`, `assets/icons/pin.svg`, `assets/icons/helpers.py` (sin cambios si el SVG encaja), `pruebas/test_sesion.py`.

---

### B3 · Zoom recordado por sitio

**Diseño:**
- `modelos/zoom.py` + `datos/zoom.json`: `{"ejemplo.com": 1.25}`.
- Rango 50 %–200 %, paso 10 %; `Ctrl+=`, `Ctrl+-`, `Ctrl+0`.
- Aplicar al terminar la carga y al cambiar de host; mostrar “Zoom: 125 %” en la barra de estado.
- Incógnito: modelo en memoria (`ruta=None`), no escribe.
- Opcional: capturar `Ctrl+rueda` con un event filter para persistir también ese gesto (si resulta simple; si no, se documenta como solo sesión).
- Normalizar host con `url.host()`; los puertos comparten zoom.

**Tests:** límites, pasos, persistencia, reset, host vacío, incógnito.

**Archivos:** `modelos/zoom.py`, `navegador.py`, `pruebas/test_zoom.py`.

---

### B4 · Modo lectura

**Diseño:**
- `interfaz/modo_lectura.py`: CSS + JS propios, sin librerías ni red.
- Heurística: prioriza `<article>`, `<main>`, `[role=main]`; si no, puntúa bloques por densidad de párrafos; clona el mejor candidato en un overlay `#mn-lector` con tipografía del tema y un botón “Salir”.
- Activar/desactivar por pestaña; no se persiste.
- Botón en la barra (icono `book-open`) y `Ctrl+Alt+R`; comando `:lector`.
- Si no encuentra contenido: aviso “No se detectó un artículo” y no toca la página.
- Sitios de prueba: Wikipedia, un diario, un blog, una documentación y una página sin artículo.

**Riesgo:** heurística imperfecta. Mitigación: overlay reversible, fallback claro, lista de sitios y ajuste posterior.

**Archivos:** `interfaz/modo_lectura.py`, `navegador.py`, `assets/icons/book-open.svg`, `pruebas/test_modo_lectura.py` (envoltorio/JS generado), `docs/PRUEBAS_MANUALES.md`.

---

### B5 · Integración y cierre

- Menú compacto (hamburguesa) con: restaurar sesión (check), modo lectura, zoom (acercar/alejar/restablecer) y “Comprobar privacidad”.
- `config.VERSION = "1.4"`.
- README, `docs/notas.md`, `docs/ATAJOS.md` y `docs/PRUEBAS_MANUALES.md` al día.
- Suite completa + ruff + smoke real de 2,5 s + prueba manual profunda.
- Merge a `main` con `--no-ff` y push (solo tras tu visto bueno).

---

## 5. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Restaurar 30 pestañas ralentiza el arranque | Alto | Tope, medición y carga diferida si hace falta |
| Datos de sesión/zoom contienen historial | Privacidad | `datos/` ignorado, nunca en incógnito, backups en Temp |
| Modo lectura rompe páginas | Medio | Overlay reversible, fallback, lista de sitios |
| Zoom por host falla con redirecciones | Bajo | Aplicar tras `loadFinished` con el host final |
| Diálogo de descargas impide automatizar | Medio | Servidor local + guion manual; el modelo sí se testea |
| Atajos pisan al navegador o al sistema | Medio | Tabla única, prueba de colisiones, matriz en inputs |
| Validación de privacidad depende de la red/región | Bajo | Checklist con resultados y fecha; límites documentados |

## 6. Estimación

| Fase | Esfuerzo |
|---|---|
| 0 + A1 | 5–7 h |
| A2 | 4–6 h |
| A3 | 4–6 h |
| B1 | 6–8 h |
| B2 | 3–5 h |
| B3 | 3–4 h |
| B4 | 8–12 h |
| B5 | 3–4 h |
| **Total** | **36–52 h** |

## 7. Decisiones abiertas (defaults propuestos)

1. **Restaurar sesión:** activado por defecto, con interruptor en el menú.
2. **Modo lectura:** heurística propia, sin librerías externas.
3. **Zoom:** 50–200 % en pasos de 10 %; `Ctrl+rueda` persistente solo si es sencillo.
4. **Atajos opcionales:** incluir `Ctrl+F` (buscar en página); dejar fuera imprimir y DevTools.
5. **Versión:** 1.4.

## 8. Criterios de aceptación global

- 0 regresiones: los 21 tests actuales siguen verdes.
- Suite nueva ≥ 40 tests en total.
- `ruff check .` limpio.
- Niveles 8–10 con checklist manual completo y fechado.
- Sesión, fijadas, zoom y lectura funcionando en la prueba real.
- `main` fusionado solo con tu aprobación.

# Nivel 10 — Anti-fingerprinting (huella digital)

## 1. El problema

Las cookies las puedes borrar. Tu **huella digital** no: es el conjunto de
datos que el navegador le entrega a cualquier web sin preguntar.

Una web puede leer, entre otras cosas:

- `navigator.userAgent`, `navigator.platform`, `navigator.language`
- `navigator.hardwareConcurrency` (núcleos) y `navigator.deviceMemory` (RAM)
- `screen.width/height`, `colorDepth`, `devicePixelRatio`
- El resultado de dibujar un texto en un `<canvas>` (depende de tu GPU y de
  las fuentes instaladas: casi único)
- El nombre de tu tarjeta gráfica vía WebGL
- `Intl.DateTimeFormat()` (zona horaria e idioma del sistema)
- `navigator.mediaDevices.enumerateDevices()` (cuántas cámaras/micros)
- `navigator.connection`, `navigator.getBattery()`…

Con 5–10 de esos datos, un sitio puede reconocerte con bastante precisión
aunque entres en incógnito, porque el incógnito solo aísla cookies y caché.

## 2. Qué hace ahora MiNavegador

### Cabeceras HTTP

| Antes | Ahora |
|---|---|
| `...QtWebEngine/6.11.2 Chrome/140...` | `...Chrome/140.0.0.0 Safari/537.36` (sin rastro de Qt) |
| `Accept-Language` vacío | `es-MX,es;q=0.9,en-US;q=0.8,en;q=0.7` |
| `Sec-CH-UA` solo anunciaba «Chromium» | «Chromium» + «Google Chrome» con la versión real |
| — | `Sec-GPC: 1` (Global Privacy Control) |

La versión de Chrome **no está escrita a mano**: se toma la de Qt y solo se
quita el token `QtWebEngine/x.y`. Así no envejece cuando actualices PyQt6
(antes estaba fijada en Chrome/120 y ya iba por 140).

### APIs de JavaScript

El script `anti_fingerprint.py` se inyecta en **cada página y cada iframe**,
en el mundo principal, en `DocumentCreation` (antes de que corra el JS de la
web). Sustituye:

| Dato | Lo que ve la web |
|---|---|
| `hardwareConcurrency` | `8` |
| `deviceMemory` | `8` |
| `platform` | `Win32` (coherente con el UA) |
| `languages` / `language` | `es-MX, es, en-US, en` |
| `userAgentData` (Client Hints) | Marcas Chromium/Google Chrome con la **misma** versión que el UA |
| `screen.*` | Resolución de escritorio común más cercana (1920×1080, 1366×768…), `colorDepth` 24 |
| `canvas.getImageData` | Ruido de ±1 en ~0,2 % de las muestras |
| `canvas.toDataURL` / `toBlob` | Un píxel alterado mientras se exporta (se restaura después) |
| WebGL vendor/renderer | `Google Inc. (Intel)` / `ANGLE (Intel, UHD Graphics 620…)` |
| WebGL `readPixels` | Ruido leve |
| `enumerateDevices` | Un dispositivo genérico por tipo, sin etiquetas ni IDs reales |
| `connection` | `4g`, rtt 50, downlink 10 |
| `getBattery` | Siempre cargando al 100 % |
| `Intl.DateTimeFormat/NumberFormat` | Locale `es-MX`, igual que `navigator.language` |
| `globalPrivacyControl` | `true` (además de la cabecera `Sec-GPC`) |

### El ruido es estable, no aleatorio en cada carga

La semilla del ruido se calcula con `hash(dominio) ^ sal_de_la_sesión`:

- **Misma web, misma sesión** → mismo ruido. Una web que use canvas de verdad
  (un editor de imágenes, por ejemplo) no se rompe entre recargas.
- **Otra web** → otro ruido, así no pueden correlacionarte entre sitios.
- **Otra sesión del navegador** → otra sal, así la huella de ayer no sirve hoy.

La sal se genera con `secrets.randbits(32)` al arrancar (`SAL_SESION`).

### Incógnito

La ventana de incógnito crea su propio `QWebEngineProfile` y aplica las
mismas protecciones (`preparar_perfil`), según la preferencia, además del
aislamiento de cookies que ya tenía.

## 3. Cómo se activa y se desactiva

1. **Menú del escudo** (el botón con el contador de bloqueos):
   - Arriba dice si la huella está *protegida* o *expuesta*.
   - Casilla **«Proteger contra fingerprinting»**.
   - El cambio se aplica **al recargar** la página (los scripts de un perfil
     se leen en cada carga, no hace falta reiniciar el navegador).
   - Al desactivarla se restauran también el **User-Agent** y el
     **Accept-Language** originales del perfil, para poder comparar.
   - La preferencia se guarda en `preferencias.json`.

2. **`config.py`** (valores por defecto):

```python
ANTI_FINGERPRINT = True      # interruptor global
FP_IDIOMAS       = ["es-MX", "es", "en-US", "en"]
FP_ACCEPT_LANGUAGE = "es-MX,es;q=0.9,en-US;q=0.8,en;q=0.7"
FP_NUCLEOS       = 8         # hardwareConcurrency
FP_MEMORIA_GB    = 8         # deviceMemory
FP_RUIDO_CANVAS  = True      # ruido en canvas/WebGL
FP_ENVIAR_GPC    = True      # cabecera Sec-GPC
UA_PERSONALIZADO = None      # None = automático (quita solo "QtWebEngine")
```

## 4. Lo que **no** cubre (importante)

El anti-fingerprinting reduce la entropía, no te vuelve anónimo:

- **IP y DNS**: tu proveedor y las webs te ven igual. Para eso hace falta Tor
  o una VPN, no un navegador.
- **Zona horaria**: sigue siendo la del sistema (`America/Mexico_City`).
  Camuflarla obliga a reescribir `Date` e `Intl` y desincroniza el reloj de
  las webs; no merece la pena para este proyecto.
- **Fuentes instaladas**: `document.fonts.check()` puede seguir delatando
  tipografías raras.
- **Audio**: no tocamos `AudioContext`/`OfflineAudioContext`.
- **Algunas lecturas de WebGL**: `readPixels` desde JS está camuflado, pero
  exportar un canvas WebGL con `toDataURL` no pasa por nuestro parche 2D.
- **Plugins/PDF**: QtWebEngine no expone plugins y un Chrome real sí. No lo
  falsificamos (sería más sospechoso un PDF Viewer falso).
- **`navigator.userAgentData`**: QtWebEngine no lo implementa, así que no hay
  nada que parchear. La cabecera `Sec-CH-UA` sí se manda, y eso es una
  incoherencia que un sitio puede notar (cabecera de Chrome, API ausente).
  Queda como pendiente conocido: se podría crear el objeto desde JS.
- **TLS/JA3 y tamaño de paquetes**: capas por debajo del navegador.
- **Funciones nativas**: nuestros parches son JavaScript; una web muy
  avanzada podría notar que `navigator.getBattery.toString()` no dice
  `[native code]`.
- Sigue diciendo que eres Chrome en Windows. Es una mentira **coherente**,
  pero no es Tor Browser.

Aun así, la combinación de canvas + WebGL + pantalla + hardware + idioma es
mucho menos única que antes, y el canvas ya no da el mismo hash.

## 5. Cómo comprobarlo

### Sin salir del navegador

1. **Menú del escudo → «Comprobar mi huella (página local)»** (o `:privacidad`).
   Abre una página generada por el propio navegador, sin red, con la tabla de
   todo lo que una web puede leer. Debe mostrar valores genéricos: 8 núcleos,
   8 GB, `Win32`, idioma `es-MX`, GPC `true` y un hash de canvas distinto en
   cada arranque.
2. **`herramientas/servidor_cabeceras.py`**: servidor local que imprime y
   muestra las cabeceras recibidas (`User-Agent`, `Accept-Language`, `Sec-GPC`,
   `Sec-CH-UA`).

```bat
venv\Scripts\python.exe herramientas\servidor_cabeceras.py
:: abrir http://127.0.0.1:8000/
```

Compara las dos cosas con el escudo activado y desactivado (hay que recargar).

### Contra sitios reales

Abre estas webs **con la protección activada** y recarga dos veces:

- https://coveryourtracks.eff.org/ (EFF, cobertura y rastreo)
- https://browserleaks.com/canvas (hash del canvas: debe cambiar respecto a
  Chrome normal y mantenerse igual entre recargas de la misma sesión)
- https://browserleaks.com/webgl (vendor/renderer genéricos)
- https://abrahamjuliot.github.io/creepjs/ (informe completo; no esperes
  0 % de confianza, es normal)

Prueba también a desactivar la casilla del escudo, recargar y comparar: los
valores vuelven a los reales. Así ves el efecto de cada capa.

El registro de estas pasadas se anota en `docs/PRUEBAS_MANUALES.md`.

## 6. Preguntas de estudio (Nivel 10)

1. ¿Por qué el script se inyecta en `MainWorld` y no en `ApplicationWorld`
   (que es donde vive el detector de Vim)?
2. ¿Por qué `DocumentCreation` y no `Deferred`?
3. ¿Por qué el ruido depende del dominio y de una sal de sesión, en vez de
   ser aleatorio en cada llamada?
4. ¿Qué diferencia hay entre **bloquear** una petición (Nivel 5) y
   **camuflar** una API (Nivel 10)?
5. ¿Por qué un UA de Chrome/120 con Chromium/140 debajo era, en sí mismo,
   una huella?
6. ¿Por qué `navigator.language = "es-MX"` sin tocar `Intl` sería peor que
   no tocar ninguno de los dos?

## 7. Archivos que toca este nivel

- `privacidad/anti_fingerprint.py` → script JS + configuración de perfiles
- `config.py` → opciones `FP_*`, `UA_PERSONALIZADO`, versión
- `navegador.py` → `configurar_perfil()` delega aquí; casilla y diagnóstico en el escudo
- `interfaz/ventana_incognito.py` → aplica la protección a su perfil propio
- `privacidad/bloqueador.py` → cabeceras `Sec-GPC` y `Sec-CH-UA`
- `modelos/preferencias.py` → `anti_fingerprint` por defecto en `true`
- `interfaz/pagina_privacidad.py` → página local de diagnóstico (nuevo)
- `herramientas/servidor_cabeceras.py` → servidor local que muestra cabeceras (nuevo)
- `pruebas/test_anti_fingerprint.py` → pruebas sin navegador (nuevo)

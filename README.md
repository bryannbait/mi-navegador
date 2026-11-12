# MiNavegador

Navegador de escritorio escrito en **Python con PyQt6 / Qt WebEngine (Chromium)**.
No implementa su propio motor: aporta la interfaz, la privacidad y la lógica
alrededor de Chromium.

- **Versión:** 1.3
- **Plataforma:** Windows (probado con Python 3.14)
- **Interfaz:** tema oscuro con acento violeta, configurable en `config.py`

## Funciones

- Pestañas con barra propia y página de inicio (reloj, buscador y accesos a favoritos).
- Bloqueo de anuncios y rastreadores con el motor Rust `adblock`
  (EasyList + EasyPrivacy, ~135.000 reglas) y whitelist por dominio.
- Modo incógnito con perfil off-the-record y modelos solo en RAM.
- Historial, favoritos y descargas persistentes; ventanas de gestión.
- Buscadores intercambiables (DuckDuckGo, Brave, Google…) desde la barra.
- Atajos estilo Vim (`Ctrl+Alt+...`) y navegación por teclado.
- Anti-fingerprinting "Nivel 10": UA limpio, idiomas coherentes, ruido
  determinista en canvas/WebGL, Global Privacy Control. Ver `docs/PRIVACIDAD.md`.

## Requisitos

Dependencias fijadas en `requirements.txt`:

| Paquete | Versión |
|---|---|
| PyQt6 | 6.11.0 |
| PyQt6-WebEngine | 6.11.0 |
| adblock | 0.6.0 |

## Instalación

```bat
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

## Cómo lanzar

Doble clic en `iniciar.bat`, o desde CMD:

```bat
cd "C:\Users\Bal\Desktop\Organizado\Projecto Navegador\mi-navegador"
venv\Scripts\python.exe main.py
```

Si ejecutas `python main.py` con el Python del sistema, `main.py` detecta que
falta PyQt6 y se relanza solo con el venv del proyecto.

## Estructura

```
mi-navegador/
├── main.py              punto de entrada
├── config.py            tema, versión y opciones de privacidad
├── navegador.py         ventana principal (MiNavegador)
├── estilos.py           hoja QSS + paleta oscura
├── pestanas.py          barra de pestañas
├── pagina_inicio.py     página de nueva pestaña (HTML generado)
├── motores.py           catálogo de buscadores
├── modelo_json.py       persistencia base (JSON)
├── historial.py         modelo de historial   + ventana_historial.py
├── favoritos.py         modelo de favoritos   + ventana_favoritos.py
├── descargas.py         modelo de descargas   + ventana_descargas.py
├── preferencias.py      ajustes del navegador
├── ventana_incognito.py ventana de incógnito
├── bloqueador.py        interceptor de red
├── gestor_bloqueo.py    motor adblock + whitelist
├── anti_fingerprint.py  privacidad / huella digital
├── atajos_vim.py        atajos estilo Vim
├── puente_vim.py        detector de inputs en la web
├── assets/icons/        iconos SVG + helpers.py
├── listas/              EasyList y EasyPrivacy
├── datos/               estado local (ignorado por git)
├── docs/                notas, guía de estudio y privacidad
├── pruebas/             pruebas unitarias (unittest)
├── iniciar.bat
└── requirements.txt
```

## Datos

Todo el estado local vive en `datos/` y está ignorado por git:
`historial.json`, `favoritos.json`, `descargas.json`, `preferencias.json` y
`whitelist.json`. El modo incógnito no escribe en esta carpeta.

## Pruebas

```bat
venv\Scripts\python.exe -m unittest discover -s pruebas -v
```

O doble clic en `pruebas.bat`.

## Documentación

- [Notas y pendientes](docs/notas.md)
- [Guía de estudio](docs/GUIA_ESTUDIO.md)
- [Privacidad y anti-fingerprinting](docs/PRIVACIDAD.md)
- `docs/LEEME_REDISENO.txt` (nota histórica del rediseño 1.2)

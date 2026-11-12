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
├── rutas.py             rutas absolutas (datos/, listas/, assets/)
├── navegador.py         ventana principal (MiNavegador)
├── estilos.py           hoja QSS + paleta oscura
├── privacidad/
│   ├── anti_fingerprint.py  UA, idiomas y camuflaje de APIs
│   ├── bloqueador.py        interceptor de red
│   └── gestor_bloqueo.py    motor adblock + whitelist
├── modelos/
│   ├── modelo_json.py   persistencia base (JSON)
│   ├── historial.py     historial
│   ├── favoritos.py     favoritos
│   ├── descargas.py     descargas
│   ├── preferencias.py  ajustes del navegador
│   └── motores.py       catálogo de buscadores
├── interfaz/
│   ├── pestanas.py      barra de pestañas
│   ├── pagina_inicio.py página de nueva pestaña (HTML generado)
│   ├── atajos_vim.py    atajos estilo Vim
│   ├── puente_vim.py    detector de inputs en la web
│   ├── ventana_historial.py
│   ├── ventana_favoritos.py
│   ├── ventana_descargas.py
│   └── ventana_incognito.py
├── assets/icons/        iconos SVG + helpers.py
├── listas/              EasyList y EasyPrivacy
├── datos/               estado local (ignorado por git)
├── docs/                notas, guía de estudio y privacidad
├── pruebas/             pruebas unitarias (unittest)
├── iniciar.bat
├── pruebas.bat
├── requirements.txt
├── requirements-dev.txt herramientas de desarrollo (ruff)
├── pyproject.toml       configuración de ruff
└── README.md
```

## Datos

Todo el estado local vive en `datos/` y está ignorado por git:
`historial.json`, `favoritos.json`, `descargas.json`, `preferencias.json` y
`whitelist.json`. El modo incógnito no escribe en esta carpeta.

## Pruebas y linter

```bat
venv\Scripts\pip install -r requirements-dev.txt
venv\Scripts\python.exe -m unittest discover -s pruebas -v
venv\Scripts\ruff.exe check .
```

O doble clic en `pruebas.bat`.

## Documentación

- [Notas y pendientes](docs/notas.md)
- [Guía de estudio](docs/GUIA_ESTUDIO.md)
- [Privacidad y anti-fingerprinting](docs/PRIVACIDAD.md)
- `docs/LEEME_REDISENO.txt` (nota histórica del rediseño 1.2)

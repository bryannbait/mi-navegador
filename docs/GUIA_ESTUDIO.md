🧠 PARTE 1: Modelo mental — ¿qué hace un navegador?
Un navegador es un programa que hace 4 cosas, en este orden:

text
1. RECIBIR una URL del usuario
        ↓
2. PEDIR la página por la red (HTTP/HTTPS)
        ↓
3. INTERPRETAR el HTML/CSS/JS y CONSTRUIR la página
        ↓
4. DIBUJARLA en pantalla y permitir interacción
Cada paso tiene su propio "departamento":

Paso	Quién lo hace	En tu navegador
1. Recibir URL	La barra de direcciones	QLineEdit + método navegar()
2. Pedirla	El motor de red	QWebEngineProfile + interceptor
3. Interpretarla	El motor de renderizado (Blink)	QWebEngineView (Chromium por dentro)
4. Dibujarla	El sistema de pintado	Qt + GPU
Punto clave: tú no has escrito el motor. Escribiste el pegamento entre el motor (Chromium) y el usuario. Eso es lo que hace Brave, Edge, Opera, Vivaldi… todos usan el motor de otro y construyen encima.

🏗️ PARTE 2: Arquitectura de tu navegador
Tu proyecto tiene 3 capas:

text
┌──────────────────────────────────────────┐
│  CAPA 3: UI (lo que el usuario ve)       │
│  main.py, ventana_*.py                   │
│  → Botones, pestañas, menús              │
├──────────────────────────────────────────┤
│  CAPA 2: Lógica (lo que decides)         │
│  gestor_bloqueo.py, motores.py           │
│  → Qué bloquear, dónde buscar            │
├──────────────────────────────────────────┤
│  CAPA 1: Modelo (los datos)              │
│  historial.py, favoritos.py,             │
│  preferencias.py                         │
│  → JSON en disco                         │
└──────────────────────────────────────────┘
Regla de oro: cada capa solo habla con la de al lado. La UI no sabe cómo se guarda un JSON. El modelo no sabe que existe una ventana. Esa separación es lo que se llama arquitectura en capas y es el 60% de la ingeniería de software.

📚 PARTE 3: Conceptos por nivel (con qué estudiar de cada uno)
Nivel 1: Ventana y motor
Conceptos: aplicación GUI, bucle de eventos, motor de renderizado.
Preguntas para autoevaluarte:

¿Por qué necesitas QApplication antes de crear la ventana?

¿Qué significa "bucle de eventos" y por qué la app no termina hasta que lo cierras?

¿Por qué Python no hace lento el motor? (pista: el motor es C++).

Nivel 2: Pestañas
Conceptos: contenedor de widgets, identificación de emisor de señales.
Preguntas:

¿Por qué self.sender() es clave cuando hay varias pestañas?

¿Qué diferencia hay entre una señal y un método normal?

¿Qué pasa si creas un QWebEngineView sin meterlo en un contenedor?

Nivel 3: Historial
Conceptos: persistencia, serialización, JSON.
Preguntas:

¿Por qué guardamos en loadFinished y no en urlChanged?

¿Qué pasa si el JSON está corrupto? ¿Cómo lo manejas?

¿Qué es una lista y qué es un diccionario en Python?

Nivel 4: Favoritos
Conceptos: patrón modelo-vista, refresco centralizado.
Preguntas:

¿Por qué _refrescar_favoritos() es una sola función y no tres separadas?

¿Por qué guardamos al instante y no al cerrar?

¿Qué diferencia hay entre QDialog.exec() y .show()?

Nivel 5: Bloqueo
Conceptos: interceptación de red, parsing, optimización.
Preguntas:

¿Por qué bloquear antes de descargar es más rápido que descargar y luego esconder?

¿Qué es un set y por qué es más rápido que una lista para buscar?

¿Qué es Rust y por qué es más rápido que Python?

Nivel 6: Motores de búsqueda
Conceptos: peticiones HTTP asíncronas, cancelación, autocompletado.
Preguntas:

¿Por qué la UI no se congela al pedir sugerencias?

¿Qué es una API y qué es un JSON de respuesta?

¿Por qué cancelamos la petición anterior antes de lanzar la nueva?

🧪 PARTE 4: Ejercicios offline para practicar
Puedes hacer esto sin internet, leyendo tu propio código:

Ejercicio 1: Traza una búsqueda
En main.py, sigue el flujo cuando escribes "python" y pulsas Enter. Anota en papel:

Qué método se llama primero.

Qué pasa si empieza con !.

Qué pasa si tiene un punto.

Qué URL final se construye.

Qué objeto la carga.

Ejercicio 2: Dibuja el árbol de widgets
Haz un árbol así:

text
MiNavegador (QMainWindow)
├── QToolBar (barra principal)
│   ├── QPushButton ← atrás
│   ├── QPushButton → adelante
│   ├── QPushButton ⟳ recargar
│   ├── QPushButton ⌂ inicio
│   ├── QLineEdit (barra direcciones)
│   ├── QPushButton 🦆 motor
│   ├── QPushButton 🛡️ escudo
│   └── ...
├── QToolBar (barra favoritos)
└── QWidget (central)
    ├── QProgressBar
    └── QTabWidget
        ├── QWebEngineView (pestaña 1)
        ├── QWebEngineView (pestaña 2)
        └── ...
Esto te da claridad mental sobre cómo está construida la UI.

Ejercicio 3: Modifica un color
En config.py, cambia COLOR_ACENTO a "#ff0000" (rojo). Ejecuta. Anota qué partes cambian. Vuelve a ponerlo.

Ejercicio 4: Añade un motor
Añade "kagi": {...} a motores.py. Cópialo de otro motor. Sin ejecutar, predice qué pasará. Luego ejecuta (sin internet solo cambia el icono).

Ejercicio 5: Lee el JSON
Abre historial.json y favoritos.json con el Bloc de notas. Entiende la estructura. Es lo mismo que un diccionario de Python, solo que guardado como texto.

📖 PARTE 5: Conceptos de ingeniería que ya usaste (con nombre técnico)
Lo que ya hiciste tiene nombre. Esto te va a servir para la universidad y el trabajo:

Lo que hiciste	Nombre técnico
Separar main.py, config.py, motores.py	Separación de responsabilidades (SRP)
Usar historial.py sin UI dentro	Patrón modelo-vista (MVC simplificado)
Guardar en JSON	Serialización / Persistencia
_refrescar_favoritos() centralizado	Single source of truth
Cancelar peticiones de sugerencias	Debouncing / Cancelación de operaciones
Bloqueo antes de descargar	Intercepción en capa de red
Perfil incógnito aislado	Sandboxing
QWebEngineView por pestaña	Multiproceso / Aislamiento por contexto
Whitelist por sitio	Lista blanca / política de excepciones
Atajos con QAction	Registro de comandos / Command pattern
Saber estos nombres te va a permitir buscar mejor en Google, leer papers, entender código ajeno y hablar en entrevistas técnicas.

🎯 PARTE 6: Plan de estudio de 2 horas
Puedes hacer esto sin internet:

Tiempo	Qué hacer
0:00 – 0:15	Lee PARTE 1 y 2 de esta guía.
0:15 – 0:30	Haz el Ejercicio 2 (dibuja el árbol de widgets).
0:30 – 0:45	Haz el Ejercicio 1 (traza una búsqueda).
0:45 – 1:00	Lee el código de main.py de arriba a abajo sin modificarlo.
1:00 – 1:15	Lee historial.py, favoritos.py, motores.py y contesta las preguntas.
1:15 – 1:30	Haz Ejercicios 3 y 4.
1:30 – 1:45	Haz Ejercicio 5 (lee los JSON).
1:45 – 2:00	Relee PARTE 5. Subraya los conceptos que no conozcas.
🧩 PARTE 7: Preguntas que deberías poder contestar al final
Si puedes contestar estas 10 preguntas, entendiste el navegador:

¿Qué hace QApplication?

¿Por qué cada pestaña tiene su propio QWebEngineView?

¿Qué diferencia hay entre urlChanged y loadFinished?

¿Por qué guardamos el historial en loadFinished?

¿Qué es un set y por qué lo usamos para dominios?

¿Qué hace un "interceptor de red"?

¿Cómo sabe Qt qué pestaña emitió una señal?

¿Por qué la UI no se congela al pedir sugerencias?

¿Por qué el modo incógnito usa un QWebEngineProfile distinto?

¿Qué diferencia hay entre un motor de búsqueda y un motor de renderizado?

📚 PARTE 8: Recursos para cuando vuelva internet
Guárdalos aquí para no perderlos:

Documentación oficial:

Qt for Python: https://doc.qt.io/qtforpython-6/

PyQt6 docs: https://www.riverbankcomputing.com/static/Docs/PyQt6/

QtWebEngine: https://doc.qt.io/qt-6/qtwebengine-overview.html

Conceptos web:

MDN Web Docs: https://developer.mozilla.org/es/

Cómo funciona un navegador (artículo clásico): busca "How browsers work" de Tali Garsiel.

AdBlock / filtros:

EasyList: https://easylist.to/

Sintaxis AdBlock Plus: https://help.adblockplus.org/hc/en-us/articles/360062733293

Repos para inspirarte:

qutebrowser: https://github.com/qutebrowser/qutebrowser

Brave (parcialmente abierto): https://github.com/brave/brave-browser

Para profundizar en Python:

Documentación oficial: https://docs.python.org/es/3/

Real Python: https://realpython.com/

Para la universidad:

Estructuras de datos en Python (listas, sets, dicts): son la base de todo lo que hiciste.

Patrones de diseño (MVC, Observer, Factory).

Programación orientada a objetos: herencia, super(), composición.

🎓 PARTE 9: Cómo se relaciona con tu carrera
Estás en Ing. en Sistemas y Computación, ciclo 2. Lo que acabas de hacer toca:

Programación orientada a objetos: usaste clases, herencia, super().__init__().

Estructuras de datos: set para dominios, list para historial, dict para preferencias.

Interfaces gráficas: no lo verás formalmente hasta más adelante, pero ya tienes ventaja.

Redes: HTTP, intercepción, peticiones asíncronas.

Bases de datos (versión ligera): persistencia en JSON es el paso previo a SQL.

Arquitectura de software: separación por capas, patrón MVC.

Seguridad: modo incógnito, whitelist, bloqueo de rastreadores.

Cuando en la universidad te hablen de "sistema de gestión de X", tú ya habrás construido uno con interfaz, persistencia y lógica separada. Vas a ir con ventaja.

✨ PARTE 10: Un consejo final
Lo más importante que hiciste en estos 6 niveles no fue copiar código. Fue:

Aceptar que no entendías algo y preguntar.

Iterar: probar, romper, arreglar, entender.

Construir sobre lo que ya tenías: cada nivel usó los anteriores.

Tener un objetivo final: llegar a Brave o superior.

Esa mentalidad es el trabajo de un ingeniero de software. El código es solo el resultado.

Cuando vuelvas, seguimos con el Nivel 7. Mientras, guarda esta guía, haz los ejercicios y no te frustres si algo no queda claro la primera vez. Programar es leer mucho más de lo que escribes.
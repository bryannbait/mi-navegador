# Atajos de teclado

Documento único de referencia. La fuente de verdad de los atajos globales es
`interfaz/atajos_tabla.py`; las pruebas (`pruebas/test_atajos.py`) fallan si hay
una combinación repetida o si un atajo apunta a un método que no existe.

## Atajos globales

Funcionan en cualquier pestaña, también con el foco dentro de la página.

| Atajo | Acción |
|---|---|
| `Ctrl+L` / `Ctrl+K` | Ir a la barra de direcciones |
| `Ctrl+F` | Buscar en la página |
| `Ctrl+T` | Nueva pestaña |
| `Ctrl+W` | Cerrar pestaña |
| `Ctrl+Shift+T` | Reabrir la última pestaña cerrada (hasta 10) |
| `Ctrl+Shift+P` | Fijar o desfijar la pestaña actual |
| `Ctrl+=` / `Ctrl+-` / `Ctrl+0` | Zoom: acercar / alejar / restablecer |
| `Ctrl+Tab` / `Ctrl+PgDown` | Pestaña siguiente |
| `Ctrl+Shift+Tab` / `Ctrl+PgUp` | Pestaña anterior |
| `Ctrl+1` … `Ctrl+8` | Ir a la pestaña 1–8 |
| `Ctrl+9` | Ir a la última pestaña |
| `Ctrl+Shift+N` | Nueva ventana de incógnito |
| `Ctrl+Shift+W` | Cerrar la ventana |
| `F11` | Pantalla completa (alternar) |
| `Ctrl+J` | Panel de descargas |
| `Ctrl+H` | Historial |
| `Ctrl+D` | Añadir o quitar de favoritos |
| `Ctrl+Shift+O` | Gestionar favoritos |
| `Ctrl+Shift+B` | Mostrar u ocultar la barra de favoritos |
| `F5` / `Ctrl+R` | Recargar (o detener si está cargando) |
| `Esc` | Detener la carga / cerrar la barra de búsqueda |
| `Alt+Left` | Atrás |
| `Alt+Right` | Adelante |
| `Alt+Home` | Página de inicio |

### Buscar en la página (`Ctrl+F`)

| Tecla | Acción |
|---|---|
| Escribir | Busca mientras escribes y muestra `3 de 12` |
| `Enter` | Siguiente coincidencia |
| `Mayús+Enter` | Coincidencia anterior |
| `Esc` | Cierra la barra y quita el resaltado |

`Esc` cierra primero la barra de búsqueda; si está cerrada, detiene la carga.

## Atajos estilo Vim

Actúan solo cuando el foco **no** está en un campo de texto (ni de la interfaz
ni de la web).

| Tecla | Acción |
|---|---|
| `j` / `k` | Bajar / subir |
| `d` / `u` | Media página abajo / arriba |
| `gg` / `G` | Ir arriba del todo / al final |
| `f` / `F` | Atrás / adelante |
| `r` | Recargar o detener |
| `t` | Nueva pestaña |
| `x` | Cerrar pestaña |
| `J` / `K` | Pestaña siguiente / anterior |
| `H` | Página de inicio |
| `i` | Foco al primer campo de la web |
| `/` | Buscar en la página (barra inferior) |
| `:` | Modo comando |
| `?` | Ayuda rápida |

### Comandos con `:`

| Comando | Acción |
|---|---|
| `:t` | Nueva pestaña |
| `:q` / `:w` / `:wq` | Cerrar pestaña |
| `:qa` | Cerrar la ventana |
| `:open URL` | Abrir una dirección |
| `:hist` | Historial |
| `:fav` | Favoritos |
| `:inc` | Ventana de incógnito |
| `:privacidad` / `:priv` | Página local de diagnóstico de privacidad |
| `:top` | Página de inicio |
| `:help` | Ayuda rápida |

## Pendiente en esta iteración

Estos atajos se añadirán en sus fases y aparecerán en la tabla al implementarse:

| Atajo | Fase | Acción |
|---|---|---|
| `Ctrl+Alt+R` | B4 | Modo lectura |

## Reglas de diseño

1. Una combinación, una acción. La tabla es única y las pruebas detectan
   duplicados; no se registran atajos sueltos en otros módulos.
2. Nada de `PowerShell` ni dependencias nuevas: todo es `QKeySequence`.
3. Los atajos de la tabla usan `Ctrl+PgDown`/`Ctrl+PgUp`. Escribir
   `Ctrl+PageDown` se acepta al normalizar, pero Qt lo interpreta mal y el
   atajo quedaría muerto.
4. Si un atajo nuevo choca con el navegador web (por ejemplo `Ctrl+F` dentro de
   un sitio), gana el atajo global: es el comportamiento esperado en un
   navegador.

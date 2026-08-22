# Tarea 2 - Inventario RPG con Prolog, PySwip y REST

Implementación de la actividad de Laboratorio de Inteligencia Artificial 1. El
proyecto integra un motor de inferencia en SWI-Prolog con un backend Python y un
frontend HTML/CSS/JavaScript. La consulta sale del formulario, viaja por `fetch`
al endpoint GET y regresa al DOM como JSON generado desde las variables
unificadas por Prolog.

## Estructura

```text
Tarea2/
├── backend/app.py              # API REST y puente PySwip
├── frontend/index.html         # Formulario y estructura visual
├── frontend/styles.css         # Archivo CSS intencionalmente vacío
├── frontend/app.js             # fetch y render dinámico del JSON
├── prolog/inventario.pl        # hechos, regla principal y recursividad
├── evidencias/                 # capturas de ejecución y petición
├── requirements.txt            # dependencia Python
└── README.md                   # documentación técnica
```

## Requisitos

- Python 3.10 o superior.
- SWI-Prolog instalado y disponible como `swipl`.
- PySwip 0.3.3, instalable con `pip install -r requirements.txt`.

PySwip necesita localizar la instalación de SWI-Prolog. En macOS se verifica
con `swipl --version`; en Windows o Linux se debe agregar el ejecutable a `PATH`
si el instalador no lo hizo automáticamente.

## Ejecución

Desde la carpeta `Tarea2`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python backend/app.py
```

El servidor escucha en `http://127.0.0.1:5000`. Si el puerto está ocupado, se
puede cambiar sin editar el código:

```bash
PORT=5050 python backend/app.py
```

También se aceptan `--host` y `--port`, por ejemplo:

```bash
python backend/app.py --host 127.0.0.1 --port 5050
```

Abre `http://127.0.0.1:5000/` para utilizar la interfaz.

## Pruebas directas

### Prolog

La consulta siguiente comprueba compilación, unificación, los seis métodos de
listas y el recorrido recursivo:

```bash
swipl -q -g "consult('prolog/inventario.pl'), procesar_inventario(pocion_roja, TotalItems, Invertida, Unica, Ordenada), writeln(resultado(TotalItems, Invertida, Unica, Ordenada)), halt."
```

`inventario_principal/1` tiene cuatro elementos e incluye dos apariciones de
`pocion_roja`. `inventario_secundario/1` tiene cuatro elementos distintos. La
regla `procesar_inventario/5` concatena ambas listas con `append/3`, cuenta con
`length/2`, valida el parámetro con `member/2`, invierte con `reverse/2`, quita
duplicados con `sort/2`, conserva duplicados al ordenar con `msort/2` y termina
llamando a `mostrar_inventario/1`.

### API REST

```bash
curl -i "http://127.0.0.1:5000/api/health"
curl -i "http://127.0.0.1:5000/api/inventario?item=pocion_roja"
curl -i -X OPTIONS "http://127.0.0.1:5000/api/inventario" \
  -H "Origin: http://localhost:5500" \
  -H "Access-Control-Request-Method: GET"
```

La ruta principal es `GET /api/inventario?item=<nombre>`. La respuesta exitosa
contiene `total_items`, `inventario_invertido`, `inventario_unico` e
`inventario_ordenado`; todas son transformaciones recibidas desde Prolog y no
listas quemadas en el frontend. El servidor también responde el preflight
`OPTIONS` y añade `Access-Control-Allow-Origin: *`, `Access-Control-Allow-Methods`
y `Access-Control-Allow-Headers` en todas sus respuestas.

## Flujo técnico

```text
Formulario HTML
      │ fetch(GET /api/inventario?item=...)
      ▼
Python CORSRequestHandler
      │ PySwip: procesar_inventario/5
      ▼
SWI-Prolog
      │ unificación de TotalItems y listas
      ▼
Respuesta JSON ───────────────► renderización dinámica en el DOM
      └────────────────────────► impresión recursiva en consola del backend
```

El parámetro se normaliza y valida antes de convertirse en átomo citado. Esto
evita que el texto del formulario se interprete como código Prolog. La interfaz
usa `textContent` y crea cada `<li>` desde el arreglo JSON; no replica valores
calculados a mano.



# Fase 0 · Qué hay montado y por qué (explicado al detalle)

Fecha: 20 nov 2026

Esto no es un resumen con palabras grandes ("capa de configuración", "arquitectura limpia"). Es: qué escribirías tú a mano si esto no existiera, y qué pieza concreta te lo evita. Viene de frontend/React, así que las comparaciones usan eso.

## 1. `pyproject.toml` + `uv`: qué resuelve exactamente

**Sin esto:** cada vez que alguien clona el repo, tendría que instalar Python a mano, crear un entorno virtual a mano (`python -m venv .venv`), activarlo, instalar cada librería una por una con versiones que podrían no coincidir con las tuyas, y cruzar los dedos.

**Con `uv`:** un archivo (`pyproject.toml`) lista las librerías, y `uv.lock` fija la versión exacta de cada una (y de sus propias dependencias). `uv sync` lee los dos y te deja un `.venv/` idéntico al mío.

Es literalmente el mismo problema que `package.json` + `package-lock.json` + `npm install` en un proyecto de React. `uv` es a Python lo que `npm`/`pnpm` es a Node, pero además sustituye a `pip`, `venv` y `pyenv` a la vez.

| Pieza | Qué hace, literal |
|---|---|
| `pyproject.toml` | Lista qué librerías necesita el proyecto y con qué rango de versión. |
| `uv.lock` | Fija la versión exacta instalada de cada librería, para que a ti y a mí nos instale lo mismo. |
| `uv sync --dev` | Lee los dos archivos anteriores y crea/actualiza `.venv/` con exactamente esas librerías. |
| `uv run <comando>` | Ejecuta ese comando usando el Python de `.venv/`, sin que tengas que "activarlo" tú a mano. |

**En una frase:** `pyproject.toml` + `uv.lock` son el `package.json` + lockfile de este proyecto, y `uv` es el `npm install` / `npm run`.

## 2. `pydantic` y `pydantic-settings`: qué resuelve exactamente

Mira `src/hipocampo/config.py`:

```python
class Settings(BaseSettings):
    database_path: Path = Field(default=Path("data/hipocampo.db"))
    vault_config: Path = Field(default=Path("configs/demo.yaml"))
    embedding_model: str = Field(default="intfloat/multilingual-e5-small")
```

**Sin `pydantic-settings`**, para leer el `.env` tendrías que hacer esto a mano:

```python
import os
database_path = os.environ.get("DATABASE_PATH", "data/hipocampo.db")
# y si alguien pone DATABASE_PATH=42, tu código no se entera hasta que
# explota mucho más tarde, al intentar usarlo como una ruta de archivo.
```

**Con `pydantic-settings`**, `Settings()` lee las variables de entorno (y el archivo `.env`) automáticamente, y además **valida el tipo**: si `DATABASE_PATH` no es una ruta válida, falla al arrancar, no a mitad de ejecución. Es el mismo trabajo que hace Zod cuando validas el body de una request en una API de Next.js: "esto que llega de fuera, ¿tiene la forma que espero?".

`VaultConfig` en el mismo archivo hace lo mismo pero para `configs/demo.yaml`:

```python
class VaultConfig(BaseModel):
    name: str
    path: Path
    fields: VaultFields = Field(default_factory=VaultFields)
```

Si el YAML tiene un campo mal escrito o le falta `name`, `VaultConfig.load(path)` lanza un error claro en el momento de cargarlo, no un `KeyError` críptico tres funciones más abajo.

**Verbos literales:**

| Pieza | Qué hace |
|---|---|
| `BaseSettings` (de `pydantic-settings`) | Lee variables de entorno y `.env`, y las convierte a los tipos de Python que declaraste (`Path`, `str`...). |
| `BaseModel` (de `pydantic`) | Igual, pero para datos que vienen de un YAML, un JSON o una request HTTP en vez de variables de entorno. |
| `Field(default=...)` | Declara el valor si no viene nada puesto. |

**En una frase:** `pydantic` es Zod para Python — declaras la forma de los datos una vez, y valida y convierte automáticamente cada vez que algo entra desde fuera (`.env`, YAML, en el futuro: JSON de la API).

## 3. SQLite: qué es, literal, y qué hace cada archivo nuevo

**Sin base de datos**, para guardar 400 notas con sus metadatos tendrías que inventarte tu propio formato de archivo y tu propia forma de buscar en él ("abre todos los `.json`, parsea cada uno, filtra a mano").

**Con SQLite**, `data/hipocampo.db` es **un solo archivo binario** en tu disco (no un servidor que arranca y escucha un puerto, como haría Postgres). Cuando ejecutas:

```python
conn = sqlite3.connect("data/hipocampo.db")
conn.execute("SELECT * FROM notes WHERE area = ?", ("rrhh",))
```

Python abre ese archivo, lo lee con el motor de SQLite (viene incluido en Python, no se instala nada aparte) y te devuelve filas. Es exactamente igual de literal que abrir un archivo con `fs.readFile` en Node, solo que en vez de texto plano, el archivo tiene una estructura de tablas que SQLite sabe leer e indexar rápido.

**Una migración** (`db/migrations/001_init.sql`) es, literal, un archivo con comandos `CREATE TABLE`. `storage/db.py` tiene una función, `run_migrations`, que:

1. Mira qué archivos de `db/migrations/*.sql` ya se ejecutaron antes (los apunta en una tabla, `schema_migrations`).
2. Ejecuta los que falten, en orden, uno por uno.

```python
def run_migrations(conn, migrations_dir=MIGRATIONS_DIR):
    done = applied_migrations(conn)          # { "001_init" } o vacío
    for path in sorted(migrations_dir.glob("*.sql")):
        version = path.stem                   # "001_init"
        if version in done:
            continue                            # ya se ejecutó, no la repitas
        conn.executescript(path.read_text())   # ejecuta el CREATE TABLE...
        conn.execute("INSERT INTO schema_migrations VALUES (?)", (version,))
```

Así, si mañana añades `002_add_chunks_fts.sql`, cualquiera que ejecute `uv run hipocampo init-db` (tú, yo, o GitHub Actions en otra máquina) acaba con exactamente las mismas tablas, sin que nadie tenga que acordarse de qué comandos ejecutar a mano.

**Por qué SQLite y no Postgres** (la decisión original): está en [ADR 0002](../adr/0002-sqlite-en-windows-nativo.md). Resumen de una línea: Postgres es un programa aparte que tendrías que instalar y tener siempre arrancado (como un `npm run dev` que nunca para); SQLite es solo un archivo, cero instalación en Windows.

**En una frase:** una migración es un archivo con instrucciones `CREATE TABLE`, y `run_migrations` es la función que se asegura de que cada instrucción se ejecute **una sola vez**, en el orden correcto, en cualquier máquina.

## 4. `typer`: qué resuelve exactamente

Mira `src/hipocampo/cli.py`:

```python
app = typer.Typer()

@app.command()
def init_db() -> None:
    ...
```

**Sin `typer`**, para que `uv run hipocampo init-db` funcione desde la terminal tendrías que parsear `sys.argv` a mano:

```python
import sys
if sys.argv[1] == "init-db":
    init_db()
elif sys.argv[1] == "version":
    ...
```

**Con `typer`**, cada función con `@app.command()` se convierte automáticamente en un subcomando (`init-db`, `version`), con `--help` generado solo a partir de los nombres de los parámetros y sus docstrings. Es el equivalente a usar un router (como el de Next.js) en vez de leer `window.location.pathname` a mano y hacer `if`/`else`.

**En una frase:** `typer` convierte funciones de Python en comandos de terminal, generando el `--help` y el parseo de argumentos solo.

## 5. `ruff`, `pytest`, GitHub Actions: para qué sirve cada uno

| Herramienta | Qué comprueba, literal |
|---|---|
| `ruff check` | Lee el código sin ejecutarlo y avisa de errores de estilo o patrones peligrosos (una variable que nunca se usa, un import que falta). Es el ESLint de este proyecto. |
| `ruff format` | Reescribe el código con un formato consistente (igual que Prettier). |
| `pytest` | Ejecuta las funciones `test_*` de `tests/` y comprueba que cada `assert` sea cierto. Si uno falla, para y te dice cuál y por qué. |
| `.github/workflows/ci.yml` | Le dice a GitHub: "cada vez que alguien empuje código, instala el proyecto con `uv` y ejecuta `ruff` y `pytest` en un ordenador limpio". Así un fallo que solo pasa en tu máquina (o en la mía) se detecta igual. |

**En una frase:** `ruff` es ESLint+Prettier, `pytest` es tu framework de tests (como Vitest), y GitHub Actions es quien los ejecuta automáticamente en cada push, en una máquina limpia que no conoce tus atajos locales.

## 6. Por qué el código está repartido en `config.py` / `domain.py` / `storage/` / `cli.py`

No es una convención decorativa: es que **cada archivo solo puede hablar con el siguiente**, nunca al revés.

- `domain.py` no importa nada del proyecto: son solo las "formas" de los datos (`Note`, `Chunk`...). Como los `types.ts` de un proyecto de TypeScript.
- `storage/db.py` solo sabe hablar con SQLite. No sabe qué es una "Estrategia de recuperación" ni nada de negocio.
- `cli.py` no sabe cómo se aplica una migración: solo llama a `connect()` y `run_migrations()` y pinta el resultado en pantalla.

Esto importa porque, cuando en la Fase 4 aparezca `retrieval/service.py` (la pieza que decide cómo buscar), el MCP server, la API y la CLI van a llamar **a la misma función** `search(...)`. Si la lógica estuviera repartida dentro de `cli.py`, tendrías que copiarla tres veces, una por cada puerta de entrada.

## Autocomprobación

Antes de pasar a la Fase 1, intenta responder esto sin mirar el código (está en el README por si quieres contarlo fuera):

1. Si borro `data/hipocampo.db` y ejecuto `uv run hipocampo init-db` otra vez, ¿qué pasa? ¿Y si lo ejecuto dos veces seguidas sin borrar nada?
2. ¿Qué diferencia hay entre lo que valida `pydantic` en `Settings` y lo que valida en `VaultConfig`? ¿De dónde viene cada uno?
3. Si quisiera añadir un comando nuevo `uv run hipocampo stats`, ¿en qué archivo lo escribirías y qué NO debería hacer esa función directamente?

Si alguna no te sale clara, pregúntamela y la repasamos con ejemplos, no con la teoría de nuevo.

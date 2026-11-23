# Instalar Postgres + pgvector en Windows nativo

Guía de la Fase 0 para el equipo de desarrollo (Windows 10/11, sin WSL2 ni Docker). El porqué está en el [ADR 0007](adr/0007-postgres-pgvector-en-windows-nativo.md).

Resumen: Postgres se instala con un asistente. **pgvector no tiene instalador para Windows**, así que se compila una vez con las herramientas de C++ de Microsoft. Son unos 30-45 minutos la primera vez, casi todo esperando descargas.

| Paso | Qué | Tiempo aprox. |
|---|---|---|
| 1 | PostgreSQL 17 (instalador de EDB) | 10 min |
| 2 | Visual Studio 2022 Build Tools (C++) | 15-20 min, ~6-8 GB |
| 3 | Compilar e instalar pgvector | 5 min |
| 4 | Crear usuario, bases y extensión | 5 min |
| 5 | Conectar Hipocampo y pasar los tests | 5 min |

## 1. PostgreSQL 17

1. Descarga el instalador de **PostgreSQL 17** para Windows x86-64 desde [postgresql.org/download/windows](https://www.postgresql.org/download/windows/) (te lleva a EDB). Usa **17.3 o posterior**: con 17.0-17.2 pgvector falla al compilar (`unresolved external symbol float_to_shortest_decimal_bufn`).
2. En el asistente:
   - Carpeta: la de por defecto, `C:\Program Files\PostgreSQL\17`. Apúntala, la usarás en el paso 3.
   - Componentes: **PostgreSQL Server** y **Command Line Tools**. pgAdmin 4 es opcional (una interfaz gráfica, útil para mirar tablas). Stack Builder no hace falta.
   - Contraseña del superusuario `postgres`: elige una y guárdala en tu gestor de contraseñas. No va en el repo.
   - Puerto: **5432**. Locale: el de por defecto.
3. Añade `C:\Program Files\PostgreSQL\17\bin` al `PATH` (Inicio → "Editar las variables de entorno del sistema" → Path → Nuevo), para tener `psql` en cualquier terminal.
4. Comprueba en una terminal nueva:

   ```powershell
   psql --version                     # psql (PostgreSQL) 17.x
   Get-Service postgresql-x64-17      # Status: Running
   ```

Postgres queda como **servicio de Windows** que arranca solo. Si prefieres que no gaste RAM cuando no lo usas: `services.msc` → `postgresql-x64-17` → Tipo de inicio: Manual, y lo arrancas con `Start-Service postgresql-x64-17` (PowerShell como administrador).

## 2. Visual Studio 2022 Build Tools

pgvector está escrito en C y hay que compilarlo contra tu Postgres. Para eso hace falta el compilador de Microsoft (MSVC). No hace falta el Visual Studio completo, solo las Build Tools.

Opción A, con `winget` (PowerShell):

```powershell
winget install Microsoft.VisualStudio.2022.BuildTools --override "--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

Opción B, a mano: descarga **"Herramientas de compilación para Visual Studio 2022"** desde [visualstudio.microsoft.com/es/downloads](https://visualstudio.microsoft.com/es/downloads/) (sección "Herramientas para Visual Studio") y en el instalador marca la carga de trabajo **"Desarrollo para el escritorio con C++"** (incluye MSVC v143 y el SDK de Windows).

También necesitas **Git para Windows** ([git-scm.com](https://git-scm.com/download/win)), que de todas formas usas para clonar el repo.

## 3. Compilar e instalar pgvector

1. En el menú Inicio busca **"x64 Native Tools Command Prompt for VS 2022"**, clic derecho → **Ejecutar como administrador**. Tiene que ser esta consola (es `cmd`, no PowerShell): es la que deja preparado el compilador de 64 bits. Como administrador, porque el último paso copia archivos dentro de `C:\Program Files`.
2. Ejecuta, línea a línea:

   ```bat
   set "PGROOT=C:\Program Files\PostgreSQL\17"
   cd %TEMP%
   git clone --branch v0.8.7 https://github.com/pgvector/pgvector.git
   cd pgvector
   nmake /F Makefile.win
   nmake /F Makefile.win install
   ```

   - `PGROOT` le dice al compilador dónde está tu Postgres (sus cabeceras `.h` y sus librerías). Las comillas van alrededor de todo `PGROOT=...` porque la ruta tiene espacios.
   - `v0.8.7` es la última versión de pgvector a 23 nov 2026. Si hay una más nueva en [github.com/pgvector/pgvector/tags](https://github.com/pgvector/pgvector/tags), usa esa.
   - `nmake` es el `make` de Microsoft: el primero compila `vector.dll`, el segundo la copia (junto con `vector.control` y los `vector--*.sql`) a las carpetas de Postgres.

### Si algo falla

| Error | Causa | Solución |
|---|---|---|
| `Cannot open include file: 'postgres.h'` | `PGROOT` apunta a otro sitio | Revisa la ruta del paso 1 y repite el `set` con comillas. |
| `error C2196: case value '4' already used` | Consola equivocada (32 bits o PowerShell normal) | Abre la **x64 Native Tools**, `nmake /F Makefile.win clean` y repite. |
| `unresolved external symbol float_to_shortest_decimal_bufn` | Postgres 17.0-17.2 | Actualiza Postgres a 17.3 o posterior. |
| `Access is denied` en el `install` | Consola sin permisos de administrador | Ábrela con "Ejecutar como administrador" y repite solo el último `nmake`. |
| `'nmake' is not recognized` | Build Tools sin la carga de trabajo de C++ | Abre "Visual Studio Installer" → Modificar → marca "Desarrollo para el escritorio con C++". |

**Plan B, si la compilación se atasca:** hay binarios precompilados de un tercero en [github.com/andreiramani/pgvector_pgsql_windows/releases](https://github.com/andreiramani/pgvector_pgsql_windows/releases) (elige el zip para **pg17**). No son oficiales. Se copian a mano, con el servicio de Postgres parado: `vector.dll` a `C:\Program Files\PostgreSQL\17\lib`, y `vector.control` y los `vector--*.sql` a `C:\Program Files\PostgreSQL\17\share\extension`.

## 4. Usuario, bases de datos y extensión

Hipocampo no se conecta como `postgres` (el superusuario), sino con un usuario propio con permisos solo sobre sus bases. Es lo que se hace en cualquier proyecto real.

```powershell
psql -U postgres
```

Te pide la contraseña del paso 1. Dentro de `psql`:

```sql
CREATE ROLE hipocampo LOGIN PASSWORD 'hipocampo';
CREATE DATABASE hipocampo OWNER hipocampo;
CREATE DATABASE hipocampo_test OWNER hipocampo;

\c hipocampo
CREATE EXTENSION vector;
SELECT extversion FROM pg_extension WHERE extname = 'vector';   -- 0.8.7

\c hipocampo_test
CREATE EXTENSION vector;
\q
```

- Dos bases: `hipocampo` para tus datos y `hipocampo_test` para los tests, que **borran sus tablas en cada ejecución**.
- `CREATE EXTENSION vector` lo hace `postgres` porque pgvector no es una extensión "de confianza": solo un superusuario puede activarla. Se hace una vez por base.
- La contraseña `hipocampo` es de desarrollo y Postgres solo escucha en `localhost` por defecto. Si quieres otra, cámbiala aquí y en tu `.env`.
- Si `psql` avisa de `Console code page (850) differs from Windows code page (1252)`, ejecuta `chcp 1252` antes de `psql` para ver bien las tildes. No afecta a los datos.

## 5. Conectar Hipocampo

```powershell
cd C:\Users\<tu-usuario>\code\hipocampo
copy .env.example .env        # DATABASE_URL y TEST_DATABASE_URL ya apuntan a lo de arriba
uv sync --dev
uv run hipocampo init-db      # Applied 1 migration(s): 001_init
uv run pytest                 # todos en verde, ninguno "skipped"
```

Si los tests de base de datos salen como `skipped`, no encuentran el Postgres de `TEST_DATABASE_URL`: revisa que el servicio está en marcha y que la base `hipocampo_test` existe.

Para mirar las tablas a mano:

```powershell
psql -U hipocampo -d hipocampo -c "\dt"
```

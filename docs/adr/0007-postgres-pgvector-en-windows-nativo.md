# Postgres + pgvector, instalado nativo en Windows (sustituye al ADR 0002)

Fecha: 23 nov 2026 · Estado: aceptada · Sustituye a: [ADR 0002](0002-sqlite-en-windows-nativo.md)

La base de datos vuelve a ser **PostgreSQL 17 con la extensión pgvector**, pero ahora instalado **nativo en Windows**: ni WSL2 ni Docker. Postgres corre como un servicio de Windows (instalador oficial de EDB) y pgvector se compila una vez con las Build Tools de Visual Studio. El driver de Python es `psycopg` 3, con el paquete `pgvector` para pasar vectores como arrays de numpy.

El motivo es el mismo que llevó a elegir Postgres en la primera versión de la spec: **es lo que se usa en la industria** y lo que Alejandro va a ver en clientes. Un RAG "de verdad" suele ser una tabla de Postgres con una columna `vector` y un índice HNSW. Aprender eso (servidor, conexión, roles, extensiones, índices aproximados, transacciones) es más útil para su trabajo de FDE que aprender las particularidades de SQLite. El ADR 0002 cambió a SQLite solo para evitar WSL2; con Postgres nativo ese problema desaparece.

## Considered Options

- **SQLite + sqlite-vec** (ADR 0002, ahora sustituida): un archivo y cero instalación, pero no es lo habitual en producción, la búsqueda vectorial es exacta (sin HNSW) y los tipos son pobres (fechas y JSON como texto).
- **Postgres + pgvector en WSL2** (la decisión original): instalación fácil con `apt`, pero obliga a gestionar WSL2, que Alejandro no quiere.
- **Postgres + pgvector con Docker Desktop**: lo más reproducible, pero Docker Desktop en Windows consume RAM que hace falta para los modelos (16 GB) y añade otra capa.
- **Postgres + pgvector nativo en Windows** (elegida): Postgres se instala con un asistente; pgvector no tiene instalador oficial para Windows, así que hay que compilarlo (una vez, ~15 minutos siguiendo [docs/INSTALACION-WINDOWS.md](../INSTALACION-WINDOWS.md)).

## Consequences

- **Instalación más larga en la Fase 0**: Postgres 17 (EDB), Visual Studio 2022 Build Tools con "Desarrollo para el escritorio con C++" (unos 6-8 GB de disco) y compilar pgvector con `nmake`. Es la parte más frágil del proyecto y está documentada paso a paso con los errores típicos.
- **Plan B** si la compilación se atasca: el binario precompilado de un tercero (`andreiramani/pgvector_pgsql_windows`, para Postgres 17). No es oficial; se usa sabiendo eso.
- **Un servicio más en el equipo**: el servicio `postgresql-x64-17` arranca con Windows y usa unos 50-100 MB de RAM en reposo. Se puede poner en arranque manual.
- **Modelo de datos con tipos de verdad**: `DATE`, `TIMESTAMPTZ`, `JSONB`, `TEXT[]` y `vector(384)` (SPEC.md §9). El embedding vuelve a ser una columna de `chunks` y la búsqueda semántica usa un índice **HNSW** por coseno: el concepto de búsqueda aproximada entra en la Fase 3.
- **Búsqueda léxica con `bm25s`** en Python (como en la spec original), no con FTS5. Postgres trae búsqueda de texto completo (`tsvector`), pero su ranking (`ts_rank`) no es BM25; compararlo es un experimento opcional.
- **Los tests de base de datos necesitan un Postgres** (`TEST_DATABASE_URL`, una base aparte que los tests vacían). Si no lo encuentran, se saltan con un aviso; en GitHub Actions corren contra un contenedor `pgvector/pgvector:pg17` (Docker solo en CI, no en el equipo de Alejandro).
- `001_init.sql` se reescribe para Postgres en vez de añadir una migración nueva: la base SQLite no tiene datos que conservar y una base Postgres empieza vacía. Es la única excepción a "nunca cambies una migración aplicada".

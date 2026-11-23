# SQLite + sqlite-vec, en Windows nativo sin WSL2 ni Docker

> **Estado: sustituida** por el [ADR 0007](0007-postgres-pgvector-en-windows-nativo.md) (23 nov 2026): se vuelve a Postgres + pgvector, instalado nativo en Windows. Se conserva para entender el cambio.

La base de datos es un único archivo SQLite (`data/hipocampo.db`), con la extensión `sqlite-vec` para los vectores y `FTS5` (incorporado en SQLite) para la búsqueda léxica con BM25. Todo corre en Windows nativo: sin WSL2, sin Linux de por medio, sin Docker Desktop. Alejandro prefiere trabajar así, y evita instalar y mantener un servidor de base de datos en un equipo que no es el más potente (Ryzen 5 1600, 16 GB).

Se sustituye así la decisión original (Postgres + pgvector en WSL2, ADR 0002 previo), que daba más parecido a un cliente real pero obligaba a instalar y aprender WSL2.

## Considered Options

- **Postgres + pgvector en WSL2** (descartada): más parecido a producción, pero añade una capa (WSL2) que Alejandro no quiere gestionar.
- **Postgres nativo en Windows**: evita WSL2, pero la instalación de Postgres y de la extensión pgvector en Windows es más frágil y menos documentada que en Linux.
- **SQLite + sqlite-vec** (elegida): un archivo, sin servicio de Windows que arrancar, `pip install sqlite-vec` y listo. FTS5 ya trae BM25, así que tampoco hace falta `bm25s`.

## Consequences

- El modelo de datos usa tipos de SQLite (TEXT para fechas y JSON, sin arrays nativos): ver SPEC.md §9.
- `sqlite-vec` hace búsqueda exacta por vecino más cercano, no aproximada (HNSW); con cientos de Notas es más que suficiente y no hace falta índice aproximado.
- Si el proyecto creciera a decenas de miles de Chunks o a varios usuarios a la vez, Postgres sería la migración natural; no es necesaria para los objetivos de este proyecto.
- Se pierde la frase "esto es lo que verás en un cliente real" asociada a Postgres; se recupera en el README explicando el trade-off y por qué se eligió así a propósito.

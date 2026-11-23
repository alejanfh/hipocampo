# Hipocampo · Plan por fases

Cada fase deja algo que funciona y una cifra medida. No se pasa a la siguiente sin medir y sin cerrar el ciclo de aprendizaje.

**Ritmo:** 4-5 h por semana, más en días de teletrabajo. **Meta:** fases 0-6 enseñables a mediados de enero de 2027 (antes de hablar con el próximo cliente de Capitole).

## Ciclo de cada fase

1. **Concepto primero (15-30 min).** Claude explica los conceptos de la fase antes de tocar código. Si algo no queda claro, se usa la skill `explain-granular`.
2. **Construir.** Claude Code escribe el código en pasos pequeños (un commit por paso), con tests. Alejandro lee cada diff y pregunta lo que no entienda.
3. **Medir.** Se pasa la evaluación y se apunta la cifra.
4. **Teach-back.** Claude hace 3-4 preguntas de comprensión. Alejandro responde con sus palabras, sin mirar. Claude corrige.
5. **Nota de aprendizaje.** `docs/aprendizajes/NN-<fase>.md`, escrita a partir de esas respuestas (plantilla en `docs/aprendizajes/README.md`).
6. **ADR** si se tomó una decisión difícil de revertir.

## Calendario orientativo

| Semana | Fases |
|---|---|
| 19-22 nov | 0 |
| 23-29 nov | 1 |
| 30 nov-6 dic | 2 |
| 7-20 dic | 3 (semana de llaves del piso: margen) |
| 21 dic-3 ene | 4 |
| 4-17 ene | 5 y 6 → **versión enseñable** |
| Después | 7, 8, 9 y opcional 10 |

---

## Fase 0 · Preparación (≈2 h)

**Objetivo:** entorno listo y repo vacío pero sano.

- Instalar en Windows: `uv` (instalador oficial, PowerShell), Python 3.12 (con `uv python install`), Node LTS, Claude Code. Nada de WSL2 ni Docker: todo nativo.
- Instalar **Postgres 17 + pgvector** nativos siguiendo [INSTALACION-WINDOWS.md](INSTALACION-WINDOWS.md): Postgres con el instalador de EDB, pgvector compilado con las Build Tools de Visual Studio, usuario `hipocampo` y bases `hipocampo` y `hipocampo_test` ([ADR 0007](adr/0007-postgres-pgvector-en-windows-nativo.md)).
- El repo vive en una ruta corta sin espacios, p. ej. `C:\Users\<tu-usuario>\code\hipocampo` (evita rutas con tildes o OneDrive, que dan problemas a algunas librerías de Python en Windows).
- Crear el repo público `hipocampo` en GitHub y clonarlo.
- Copiar estos documentos (CLAUDE.md, CONTEXT.md, docs/).
- Esqueleto: `pyproject.toml`, `src/hipocampo/`, `tests/`, ruff, pytest, `.gitignore`, `.env.example`, CLI `hipocampo --help`.
- `db/migrations/001_init.sql` aplicado.
- GitHub Actions: ruff + pytest en cada push.

**Hecho cuando:** `uv run pytest` pasa sin tests saltados, `uv run hipocampo --help` responde y `psql -U hipocampo -d hipocampo -c "\dt"` ve las tablas.

**Conceptos:** entornos virtuales y lockfiles; `.env` y separar configuración de código; qué es una migración; qué es un servidor de base de datos (servicio, puerto, usuarios y roles) y qué es una extensión de Postgres.

## Fase 1 · Vault demo y set de evaluación (≈4 h)

**Objetivo:** tener sobre qué medir antes de construir nada.

- Seguir [DEMO-VAULT.md](DEMO-VAULT.md): biblia de la empresa → generar Notas por lotes con Claude Code → `scripts/check_vault.py` (frontmatter válido, enlaces que existen, hechos versionados presentes).
- `configs/demo.yaml`.
- Generar ~60 Preguntas de evaluación en `eval/demo.yaml` (los cuatro tipos); Alejandro revisa 15.
- Alejandro escribe ~20 preguntas de su vault real en `eval/real.local.yaml`.

**Hecho cuando:** `check_vault.py` pasa y hay 60 + 20 preguntas.

**Conceptos:** por qué se mide antes de optimizar; qué hace buena a una pregunta de evaluación; datos sintéticos y sus trampas (el generador y el evaluado no deben "hablar igual").

## Fase 2 · Ingesta, BM25 y arnés de evaluación (≈4 h)

**Objetivo:** la primera cifra.

- `ingest/`: discover, parse (frontmatter, wikilinks, encabezados, quitar dataview), chunk por encabezados. Tests con Notas pequeñas de ejemplo.
- Guardar en `notes` y `chunks` (sin embeddings aún: la columna `embedding` queda a NULL hasta la fase 3).
- `retrieval/lexical.py` con bm25s + stemming español.
- `eval/`: cargar el set, recall@5, MRR, temporal@1, latencia, informe en Markdown.
- `hipocampo eval search --strategy lexical`.

**Hecho cuando:** hay cifra de BM25 en demo y en real.

**Conceptos:** BM25 (TF, IDF, normalización por longitud); stemming y stopwords; recall@k y MRR; tests unitarios en Python.

## Fase 3 · Embeddings y pgvector (≈5 h)

**Objetivo:** búsqueda semántica y la primera comparación.

- `ingest/embed.py` con e5-small (prefijos `passage:`/`query:`), por lotes, con barra de progreso.
- `retrieval/semantic.py`: vecinos más cercanos por coseno (`<=>`) con el índice HNSW de pgvector; medir el efecto de `hnsw.ef_search` frente a la búsqueda exacta.
- Comparar 2-3 tamaños de Chunk (p. ej. 200/400/800 tokens).
- Experimento: e5-small vs bge-m3 (recall, tiempo de indexado, latencia, RAM).

**Hecho cuando:** tabla BM25 vs semántica (2 modelos, 3 tamaños).

**Conceptos:** qué es un embedding y qué significa la dimensión; similitud coseno; búsqueda aproximada (HNSW) y por qué no comparar con todo; por qué los vectores fallan con nombres propios y cifras.

## Fase 4 · Híbrida, filtros y rerank (≈4 h)

**Objetivo:** la mejor estrategia y saber por qué lo es.

- `retrieval/fusion.py` (RRF), filtros por metadatos, desempate por fecha, diversidad por Nota.
- `retrieval/rerank.py` con el cross-encoder sobre los 20 primeros.
- `retrieval/service.py`: la interfaz única `search(...)` y las Trazas.
- Medir cada mejora por separado (híbrida, + filtros, + rerank).

**Hecho cuando:** tabla completa de la Evaluación de búsqueda.

**Conceptos:** RRF y por qué fusionar posiciones y no puntuaciones; bi-encoder vs cross-encoder; coste de latencia del rerank; arquitectura por capas (servicio y repositorios).

## Fase 5 · Servidor MCP (≈3 h)

**Objetivo:** Claude responde con tus Notas.

- `mcp_server.py` con `search_notes`, `read_note`, `list_areas` e instrucciones del servidor.
- Conectar a Claude Code y a Claude Desktop, los dos en Windows nativo (ver SPEC.md §11).
- Probar 10 preguntas a mano y revisar las Trazas.

**Hecho cuando:** Claude Desktop responde preguntas del demo citando `[[Notas]]`.

**Conceptos:** qué es MCP (cliente, servidor, herramientas, transporte stdio); cómo escribir descripciones de herramientas que el modelo elige bien; grounding y alucinaciones; Búsqueda agéntica.

## Fase 6 · Evaluación de respuestas: el experimento estrella (≈4 h)

**Objetivo:** responder "¿cuándo compensa un RAG?".

- Comando `.claude/commands/evaluar-respuestas.md` (subagentes que responden y juzgan con rúbrica).
- Tres modos: Contexto completo, agéntica con Hipocampo, agéntica con grep. En demo y en real.
- README con las dos tablas, el diagrama y las decisiones. **Versión enseñable.**

**Hecho cuando:** las tablas están en el README y sabes explicar el resultado en 2 minutos.

**Conceptos:** LLM como juez y sus sesgos; rúbricas; por qué el vault real (42 Notas) seguramente no necesita RAG y el demo sí; qué es un "harness" de evaluación.

## Fase 7 · Ingesta incremental (≈2 h)

- `content_hash`, reprocesar solo lo cambiado, borrar lo eliminado, test de idempotencia.
- Opcional: `hipocampo watch` que reindexa al detectar cambios (o tras `git pull` del vault).

**Conceptos:** idempotencia; transacciones; por qué esto es lo que cuesta en producción.

## Fase 8 · Web: buscador explicable (≈5 h)

- `api.py` (FastAPI) sobre el servicio. `web/` con las pantallas de SPEC §13.
- Captura y GIF de "Comparar" para el README.

**Conceptos:** FastAPI (rutas, dependencias, modelos pydantic como contrato); CORS; tipar el contrato entre Python y TypeScript.

## Fase 9 · Contarlo (≈2 h)

- README final en inglés: problema, arquitectura, tablas, decisiones con enlace a los ADRs, cómo ejecutarlo.
- Post de LinkedIn con la tabla y el GIF.
- Línea de CV con las cifras reales, p. ej.: *"Built Hipocampo, a local hybrid-search engine over Obsidian knowledge bases exposed to Claude via MCP (Python, Postgres/pgvector, FastAPI, Next.js); evaluation-driven: recall@5 from X% (BM25) to Y% (hybrid + rerank), and measured when RAG beats full-context and grep-based agentic search."*

## Fase 10 (opcional) · Permisos por departamento

- Cada Nota del demo con `acceso: [todos | direccion | rrhh ...]`, la Consulta lleva el rol y el filtro se aplica en la búsqueda (nunca después).
- Preguntas de evaluación que comprueban que no se filtra nada.

**Conceptos:** por qué filtrar antes y no después; el tema de seguridad número uno en RAG de empresa.

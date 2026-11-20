# Hipocampo · Especificación

> El hipocampo es la parte del cerebro que indexa los recuerdos y ayuda a recuperarlos. Este proyecto hace eso para un segundo cerebro: indexa notas y recupera las que hacen falta.

Fecha: 19 nov 2026 · Autor: Alejandro · Estado: aprobada para empezar

El vocabulario está en [CONTEXT.md](../CONTEXT.md). Las decisiones difíciles de revertir, en [docs/adr/](adr/). El orden de trabajo, en [PLAN.md](PLAN.md).

## 1. Por qué existe

1. **Aprender** backend, Python e IA aplicada (RAG, embeddings, evaluación, MCP) a fondo, entendiendo el porqué de cada pieza. Es el objetivo principal.
2. **Enseñarlo y medirlo**: repo open source con una tabla de resultados que demuestra criterio de ingeniería (CV, LinkedIn, entrevistas de FDE / AI engineer).
3. **Usarlo** con el vault real solo si mide mejor que lo que ya existe (Claude leyendo el repo del vault). Es un plus, no un requisito.

Orden de prioridad si chocan: 1 > 2 > 3.

## 2. Qué es, en una frase

Un **motor de búsqueda** sobre vaults de Obsidian (híbrido, con filtros y rerank, todo en local y gratis) que se expone como **servidor MCP** para que Claude, con la suscripción de Alejandro, busque, lea y responda citando notas. Una web en Next.js sirve para ver **por qué** sale cada resultado.

## 3. Restricciones

| Restricción | Consecuencia |
|---|---|
| **Coste cero.** Nada de APIs de pago ni servicios en la nube. | Embeddings y rerank en local. Quien redacta la respuesta es Claude vía MCP con la suscripción ([ADR 0001](adr/0001-solo-busqueda-y-claude-por-mcp.md)). |
| **Windows nativo, sin WSL2 ni Docker, con Ryzen 5 1600 y 16 GB de RAM.** | SQLite + `sqlite-vec` como base de datos, un solo archivo, sin servidor que instalar ([ADR 0002](adr/0002-sqlite-en-windows-nativo.md)). Modelos pequeños que corran en CPU. |
| **El vault real nunca sale del ordenador** ni se sube al repo. | Ruta en `.env`, su configuración y sus preguntas en archivos ignorados por git. |
| **Alejandro no escribe código a mano**: Claude Code lo escribe, él lo entiende y lo revisa. | Cada fase acaba con preguntas de comprensión y una nota de aprendizaje (ver PLAN.md). |
| 4-5 h por semana, más en días de teletrabajo. | Fases cortas que dejan algo medible. |

## 4. Fuera de alcance (v1)

- Demo pública desplegada y cualquier cosa con coste.
- Chat propio con generación en la web (el chat es Claude con el MCP).
- Permisos por departamento (fase opcional al final).
- Escribir en el vault. Hipocampo solo lee.
- Frameworks de RAG (LangChain, LlamaIndex) para las piezas centrales ([ADR 0004](adr/0004-piezas-centrales-sin-framework.md)).

## 5. Arquitectura

```
                 ┌──────────────── Vault (Markdown) ───────────────┐
                 │ vault demo (repo)        vault real (solo local) │
                 └───────────────┬─────────────────────────────────┘
                                 │ ingest (parse → chunk → embed)
                                 ▼
             ┌──────────────────────────────────────────┐
             │ SQLite + sqlite-vec (archivo local)      │
             │ notes · chunks(+embedding) · traces      │
             └──────────────────┬───────────────────────┘
                                │
                 ┌──────────────┴──────────────┐
                 │ retrieval service (Python)  │
                 │ BM25 · vectores · RRF ·     │
                 │ filtros · rerank            │
                 └──┬───────────┬───────────┬──┘
                    │           │           │
              MCP server    FastAPI      eval runner
             (stdio)        /search      (recall@5, MRR)
                    │           │
          Claude Desktop /   web Next.js
          Claude Code        (buscador explicable)
          (redacta y cita)
```

Idea clave: **un único servicio de búsqueda** y tres puertas de entrada finas (MCP, HTTP, evaluación). Es la arquitectura por capas que usa el equipo de backend de IAG: los endpoints no tienen lógica, la lógica vive en el servicio y el acceso a datos en repositorios.

## 6. Stack

| Pieza | Elección | Porqué corto |
|---|---|---|
| Lenguaje backend | Python 3.12 | Lo que piden las ofertas de IA y el punto débil a reforzar. |
| Paquetes | `uv` | Rápido, un solo comando, el estándar actual. |
| Calidad | `ruff` (lint + formato), `pytest`, `mypy` en modo básico | Feedback inmediato al revisar lo que escribe Claude. |
| Modelos de datos | `pydantic` v2 | Validación y tipos, igual que en FastAPI. |
| Base de datos | SQLite + extensión `sqlite-vec`, driver estándar `sqlite3` | Un archivo, cero instalación en Windows. Ver ADR 0002. |
| Migraciones | SQL plano numerado (`db/migrations/001_*.sql`) | Ver el SQL tal cual ayuda a aprender, con o sin servidor. |
| Búsqueda léxica | `bm25s` + `PyStemmer` (español) | BM25 de verdad, rápido, y enseña stemming y stopwords. |
| Embeddings | `sentence-transformers` con `intfloat/multilingual-e5-small` (384 dim) | Corre en CPU. Comparar una vez con `BAAI/bge-m3` (1024 dim). Ver ADR 0005. |
| Rerank | Cross-encoder multilingüe pequeño (`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`) | Corre en CPU sobre ~20 candidatos. |
| MCP | SDK oficial de Python (`mcp`, FastMCP), transporte stdio | Lo mínimo para conectarlo a Claude Desktop y Claude Code. |
| API HTTP | FastAPI | Lo que usáis en IAG. Solo para la web. |
| Frontend | Next.js (App Router) + TypeScript + Tailwind + shadcn/ui | Tu terreno: aquí el valor es el diseño del buscador explicable. |
| CLI | `typer` | `hipocampo ingest`, `hipocampo search`, `hipocampo eval`. |

Versiones exactas: las fija Claude Code en la fase 0 con la última estable de cada una.

## 7. Configuración

### `.env` (no se sube)

```
DATABASE_PATH=data/hipocampo.db
VAULT_CONFIG=configs/demo.yaml          # o configs/real.local.yaml
EMBEDDING_MODEL=intfloat/multilingual-e5-small
```

### Configuración de vault (`configs/<vault>.yaml`)

```yaml
name: demo
path: vault-demo/                 # en real.local.yaml: ruta absoluta al vault real
include: ["**/*.md"]
exclude: ["Plantillas/**", ".obsidian/**"]
fields:
  date: fecha                     # campo del frontmatter que es la fecha
  area: departamento              # en el vault real: area
  tags: etiquetas
filters: [area, folder, date]     # qué se puede usar como Filtro
index_notes: true                 # notas con el mismo nombre que su carpeta (índices); en el vault real son índices dataview y se pueden excluir
```

`configs/*.local.yaml` está en `.gitignore`. El repo incluye `configs/real.example.yaml` con valores falsos para que se vea cómo se configura.

## 8. Ingesta

**Entrada:** una Configuración de vault. **Salida:** filas en `notes` y `chunks`.

1. **Descubrir** archivos con `include`/`exclude`.
2. **Parsear** cada Nota: frontmatter (YAML), título (primer `#` o nombre de archivo), encabezados, `[[wikilinks]]` (incluidos `[[Nota|alias]]` y `[[Nota#Sección]]`), y quitar bloques ` ```dataview ` (no son contenido).
3. **Trocear** (chunking) por encabezados:
   - Cada sección (`##`, `###`) es un Chunk candidato.
   - Si pasa de **~400 tokens**, se parte por párrafos con **~50 tokens de solape**.
   - Si es muy corta (< 40 tokens), se une a la siguiente de la misma Nota.
   - Cada Chunk lleva delante un **encabezado de contexto** que se indexa pero no se muestra: `Nota: <título> · Sección: <ruta de encabezados> · Área: <area> · Fecha: <fecha>`. Así un trozo suelto ("son 3 días") sigue sabiendo de qué habla.
   - Tamaños parametrizables: la fase 3 compara 2-3 configuraciones.
4. **Embeddings**: e5 exige prefijos, `passage: ` al indexar y `query: ` al buscar. Si falta, el recall cae y no da error: es el típico fallo silencioso.
5. **Guardar** en una transacción por Nota (si una falla, no deja la Nota a medias).
6. **Incremental** (fase 7): `content_hash` (SHA-256 del archivo) por Nota. Solo se reprocesa lo que cambió; se borran Notas que ya no existen. Ejecutar dos veces seguidas no cambia nada (idempotente).

## 9. Modelo de datos

```sql
-- requiere cargar la extensión sqlite-vec en cada conexión (ver storage/db.py)

CREATE TABLE notes (
  id            INTEGER PRIMARY KEY,
  vault         TEXT NOT NULL,
  path          TEXT NOT NULL,                -- relativa al vault
  title         TEXT NOT NULL,
  folder        TEXT NOT NULL,
  area          TEXT,
  note_date     TEXT,                         -- ISO 8601 (YYYY-MM-DD); SQLite no tiene tipo fecha
  tags          TEXT NOT NULL DEFAULT '[]',    -- JSON array
  frontmatter   TEXT NOT NULL DEFAULT '{}',    -- JSON object
  links         TEXT NOT NULL DEFAULT '[]',    -- JSON array de títulos de [[wikilinks]] salientes
  content_hash  TEXT NOT NULL,
  updated_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  UNIQUE (vault, path)
);

CREATE TABLE chunks (
  id            INTEGER PRIMARY KEY,
  note_id       INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
  ordinal       INTEGER NOT NULL,              -- posición dentro de la nota
  heading_path  TEXT NOT NULL,                 -- "Política > Excepciones"
  text          TEXT NOT NULL,                 -- lo que se muestra
  indexed_text  TEXT NOT NULL,                 -- encabezado de contexto + text
  token_count   INTEGER NOT NULL,
  UNIQUE (note_id, ordinal)
);

-- Tabla virtual de sqlite-vec: el embedding vive aparte, enlazado por rowid = chunks.id
CREATE VIRTUAL TABLE chunk_embeddings USING vec0(
  embedding FLOAT[384]                         -- dimensión según el modelo (ver ADR 0005)
);

-- Búsqueda léxica con FTS5 (BM25 incorporado) en vez de bm25s en memoria
CREATE VIRTUAL TABLE chunks_fts USING fts5(
  indexed_text, content='chunks', content_rowid='id'
);

CREATE TABLE traces (
  id            INTEGER PRIMARY KEY,
  created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  source        TEXT NOT NULL,                 -- mcp | web | eval | cli
  vault         TEXT NOT NULL,
  query         TEXT NOT NULL,
  strategy      TEXT NOT NULL,
  filters       TEXT NOT NULL DEFAULT '{}',    -- JSON
  params        TEXT NOT NULL DEFAULT '{}',    -- JSON: top_k, pesos, modelo...
  results       TEXT NOT NULL,                 -- JSON: [{chunk_id, note_path, score, signals}]
  latency_ms    TEXT NOT NULL                  -- JSON: {lexical, semantic, rerank, total}
);
```

Nota de diseño: se cambió `bm25s` (en memoria) por **FTS5**, la búsqueda de texto completo incorporada en SQLite, porque ya trae BM25 y evita mantener un índice aparte; se sigue aprendiendo stemming y tokenización, ahora configurando el tokenizador de FTS5. `sqlite-vec` sustituye a pgvector: misma idea (vector + índice), motor distinto. Cambiar de modelo de embeddings cambia la dimensión: se re-crea `chunk_embeddings` del vault. Se documenta en la nota de aprendizaje de la fase 3.

## 10. Búsqueda

Interfaz única del servicio:

```python
def search(query: str, *, strategy: Strategy = "hybrid_rerank",
           filters: Filters | None = None, top_k: int = 8) -> SearchResponse
```

| Estrategia | Cómo funciona |
|---|---|
| `lexical` | BM25 sobre `indexed_text` con stemming español y stopwords. |
| `semantic` | Embedding de `query: <consulta>` y vecinos más cercanos por coseno (`sqlite-vec`, búsqueda exacta: el vault cabe de sobra para no necesitar un índice aproximado). |
| `hybrid` | Top 50 de cada una, fusionados con **Reciprocal Rank Fusion** (`score = Σ 1/(60 + posición)`). |
| `hybrid_rerank` | `hybrid` y luego el cross-encoder puntúa los 20 primeros contra la consulta. Por defecto. |

- **Filtros** (`area`, `folder`, `date_from`, `date_to`) se aplican en las dos búsquedas antes de fusionar.
- **Nota más reciente**: si dos Resultados de Notas distintas empatan en tema, el más reciente sube (desempate por `note_date`). Se mide en las preguntas temporales.
- **Diversidad**: como máximo 3 Chunks de la misma Nota en el top-k.
- Cada **Resultado** lleva `signals`: `{lexical_rank, semantic_rank, rrf_score, rerank_score}`. Es lo que pinta la web.
- Cada búsqueda escribe una **Traza**.

## 11. Servidor MCP

Transporte **stdio**. Herramientas (descripciones en inglés, pensadas para que el modelo las elija bien):

| Herramienta | Entrada | Salida |
|---|---|---|
| `search_notes` | `query`, `area?`, `folder?`, `date_from?`, `date_to?`, `top_k?` | Lista de Resultados: título, ruta, fecha, sección, texto, puntuación. |
| `read_note` | `path` | La Nota entera con su frontmatter y sus enlaces. |
| `list_areas` | — | Áreas y carpetas con el número de Notas y la fecha más reciente. |

Instrucciones del servidor (las lee el modelo): buscar antes de responder; si dos Notas se contradicen, mandar la más reciente y decirlo; citar siempre `[[Título]]`; si no está, decir "no aparece en el vault".

Conexión (todo en Windows nativo):
- **Claude Code**: `claude mcp add hipocampo -- uv --directory C:\Users\<tu-usuario>\code\hipocampo run hipocampo-mcp`.
- **Claude Desktop**: en `claude_desktop_config.json`, `"command": "uv"`, `"args": ["--directory", "C:\\Users\\<tu-usuario>\\code\\hipocampo", "run", "hipocampo-mcp"]`.

## 12. API HTTP (para la web)

- `GET /search?q=&strategy=&area=&folder=&date_from=&date_to=&top_k=` → `SearchResponse` (con `signals`).
- `GET /notes/{path}` → Nota renderizable (Markdown + frontmatter + enlaces entrantes y salientes).
- `GET /areas` → lo mismo que `list_areas`.
- `GET /traces?limit=` → últimas Trazas.
- CORS solo para `localhost:3000`. Sin autenticación: solo corre en local.

## 13. Web: buscador explicable

Next.js en `web/`. Pantallas:

1. **Buscar**: caja de búsqueda, selector de estrategia, filtros (área, carpeta, fechas). Cada Resultado muestra título, sección, fecha, el texto con los términos resaltados y **una barra por señal** (posición en BM25, posición en vectores, RRF, rerank). Se entiende de un vistazo por qué salió.
2. **Comparar**: la misma consulta con dos estrategias lado a lado. Es la captura del README.
3. **Nota**: Markdown renderizado, `[[enlaces]]` navegables y enlaces entrantes.
4. **Trazas**: tabla de las últimas búsquedas (fuente, estrategia, latencias).

## 14. Evaluación

### Set de evaluación

`eval/demo.yaml` (público) y `eval/real.local.yaml` (privado, ignorado por git):

```yaml
- id: q017
  type: temporal            # fact | temporal | multi_note | unanswerable
  question: "¿Cuántos días de teletrabajo a la semana permite la política actual?"
  expected_answer: "3 días, desde marzo de 2026."
  relevant_notes: ["RRHH/Politica de teletrabajo 2026.md"]
  distractor_notes: ["RRHH/Politica de teletrabajo 2025.md"]   # solo en temporales
```

- Demo: ~60 preguntas generadas con Claude Code a partir del vault demo, 15 revisadas a mano, repartidas en los cuatro tipos.
- Real: ~20 escritas por Alejandro.

### Evaluación de búsqueda (gratis, sin LLM)

`hipocampo eval search --vault demo --strategy all` calcula, por estrategia y por tipo de pregunta:
- **recall@5**: ¿alguna Nota relevante en los 5 primeros?
- **MRR**: media de 1/posición de la primera Nota relevante.
- **Temporal correcta@1** (solo temporales): ¿sale la Nota vigente antes que la desfasada?
- Latencia p50 y p95.

Las preguntas `unanswerable` no cuentan para recall; sirven para la evaluación de respuestas. Resultados en `eval/results/<fecha>-<estrategia>.json` y una tabla Markdown que se pega en el README.

### Evaluación de respuestas (con la suscripción)

Un comando de Claude Code, `.claude/commands/evaluar-respuestas.md`, que Alejandro lanza a mano:
1. Para cada pregunta y cada modo (**Contexto completo**, **Búsqueda agéntica con Hipocampo**, **Búsqueda agéntica con grep**), un subagente responde.
2. Otro subagente juzga con una rúbrica fija: ¿correcta?, ¿fiel a las Notas (sin inventar)?, ¿citas correctas?, ¿dice "no lo sé" cuando toca?
3. Guarda las respuestas y los juicios en `eval/results/` y resume la tabla.

Es el experimento estrella: cuándo compensa un RAG frente a leerlo todo (vault real: 42 Notas, cabe en contexto) o frente a grep.

## 15. Vault demo

Detallado en [DEMO-VAULT.md](DEMO-VAULT.md). Resumen: base de conocimiento de una SaaS B2B ficticia, 300-500 Notas en 6 carpetas, con hechos que cambian en el tiempo, generada en lotes con Claude Code y versionada en `vault-demo/`.

## 16. Estructura del repo

```
hipocampo/
├── CLAUDE.md                  # cómo trabaja Claude Code aquí
├── CONTEXT.md                 # glosario
├── README.md                  # en inglés, para GitHub
├── pyproject.toml · uv.lock · .env.example · .gitignore
├── configs/                   # demo.yaml, real.example.yaml (*.local.yaml ignorados)
├── data/                      # hipocampo.db (ignorado por git)
├── db/migrations/             # 001_init.sql, ...
├── src/hipocampo/
│   ├── config.py              # .env + vault.yaml → objetos pydantic
│   ├── domain.py              # Note, Chunk, SearchResult, Filters...
│   ├── ingest/                # discover.py, parse.py, chunk.py, embed.py, pipeline.py
│   ├── retrieval/             # lexical.py, semantic.py, fusion.py, rerank.py, service.py
│   ├── storage/               # db.py, notes_repo.py, chunks_repo.py, traces_repo.py
│   ├── eval/                  # dataset.py, metrics.py, runner.py, report.py
│   ├── mcp_server.py
│   ├── api.py                 # FastAPI
│   └── cli.py                 # typer
├── tests/                     # unitarios por módulo + un test de extremo a extremo con un vault mini
├── vault-demo/                # el vault de la empresa ficticia
├── eval/                      # demo.yaml, results/ (real.local.yaml ignorado)
├── scripts/                   # generación y comprobación del vault demo
├── web/                       # Next.js
├── .claude/commands/          # evaluar-respuestas.md, nueva-fase.md
└── docs/
    ├── SPEC.md · PLAN.md · DEMO-VAULT.md
    ├── adr/
    └── aprendizajes/          # una nota por fase, en español
```

## 17. Seguridad y privacidad

- `.gitignore` incluye `.env`, `configs/*.local.yaml`, `eval/*.local.yaml`, `eval/results/*real*`, `data/*.db`.
- Un test comprueba que ningún archivo versionado contiene la ruta del vault real ni nombres de su carpeta raíz.
- Las Trazas del vault real se quedan en el archivo `.db` local (fuera del repo). Nunca se exportan.
- `read_note` solo lee rutas dentro del vault configurado (nada de `../`).

## 18. Cómo sabremos que está bien (v1)

- `hipocampo ingest` y `hipocampo eval search` funcionan de cero en un Windows limpio (PowerShell o cmd) siguiendo el README, sin instalar nada aparte de Python y `uv`.
- Tabla del README con, como mínimo: BM25 → vectores (e5-small) → vectores (bge-m3) → híbrida → híbrida + rerank, con recall@5, MRR, temporal@1 y latencia.
- Tabla de evaluación de respuestas: contexto completo vs agéntica con Hipocampo vs agéntica con grep, en demo y en real.
- Claude Desktop responde preguntas del vault demo citando Notas vía MCP.
- Una nota de aprendizaje por fase en `docs/aprendizajes/`.

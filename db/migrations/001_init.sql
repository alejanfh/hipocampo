-- Phase 0: base schema. See docs/SPEC.md §9 for the design rationale and
-- docs/adr/0007-postgres-pgvector-en-windows-nativo.md for why Postgres + pgvector.
--
-- `CREATE EXTENSION vector` needs a superuser the first time in each
-- database (pgvector is not a "trusted" extension). The setup steps in the
-- README run it as `postgres`; here it's IF NOT EXISTS, so it's a no-op
-- once done and only fails if pgvector isn't installed on the server.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS notes (
  id            BIGSERIAL PRIMARY KEY,
  vault         TEXT NOT NULL,
  path          TEXT NOT NULL,
  title         TEXT NOT NULL,
  folder        TEXT NOT NULL,
  area          TEXT,
  note_date     DATE,
  tags          TEXT[] NOT NULL DEFAULT '{}',
  frontmatter   JSONB NOT NULL DEFAULT '{}',
  links         TEXT[] NOT NULL DEFAULT '{}',
  content_hash  TEXT NOT NULL,
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (vault, path)
);

CREATE TABLE IF NOT EXISTS chunks (
  id            BIGSERIAL PRIMARY KEY,
  note_id       BIGINT NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
  ordinal       INT NOT NULL,
  heading_path  TEXT NOT NULL,
  text          TEXT NOT NULL,
  indexed_text  TEXT NOT NULL,
  token_count   INT NOT NULL,
  -- Nullable on purpose: phase 2 stores chunks before phase 3 computes
  -- embeddings. 384 = multilingual-e5-small (ADR 0005); another model
  -- means a new migration that changes the dimension.
  embedding     vector(384),
  UNIQUE (note_id, ordinal)
);

-- Approximate nearest-neighbour index for cosine distance (`<=>`).
-- Rows with a NULL embedding are simply left out of the index.
CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw
  ON chunks USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS traces (
  id            BIGSERIAL PRIMARY KEY,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  source        TEXT NOT NULL,
  vault         TEXT NOT NULL,
  query         TEXT NOT NULL,
  strategy      TEXT NOT NULL,
  filters       JSONB NOT NULL DEFAULT '{}',
  params        JSONB NOT NULL DEFAULT '{}',
  results       JSONB NOT NULL,
  latency_ms    JSONB NOT NULL
);

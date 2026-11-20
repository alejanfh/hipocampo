-- Phase 0: base schema. See docs/SPEC.md §9 for the design rationale and
-- docs/adr/0002-sqlite-en-windows-nativo.md for why SQLite + sqlite-vec.
--
-- Note: `chunk_embeddings` (sqlite-vec virtual table) and `chunks_fts`
-- (FTS5 virtual table) are created lazily by storage/db.py, not here,
-- because they depend on the embedding dimension (configurable) and on
-- the sqlite-vec extension being loaded on the connection first.

CREATE TABLE IF NOT EXISTS notes (
  id            INTEGER PRIMARY KEY,
  vault         TEXT NOT NULL,
  path          TEXT NOT NULL,
  title         TEXT NOT NULL,
  folder        TEXT NOT NULL,
  area          TEXT,
  note_date     TEXT,
  tags          TEXT NOT NULL DEFAULT '[]',
  frontmatter   TEXT NOT NULL DEFAULT '{}',
  links         TEXT NOT NULL DEFAULT '[]',
  content_hash  TEXT NOT NULL,
  updated_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  UNIQUE (vault, path)
);

CREATE TABLE IF NOT EXISTS chunks (
  id            INTEGER PRIMARY KEY,
  note_id       INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
  ordinal       INTEGER NOT NULL,
  heading_path  TEXT NOT NULL,
  text          TEXT NOT NULL,
  indexed_text  TEXT NOT NULL,
  token_count   INTEGER NOT NULL,
  UNIQUE (note_id, ordinal)
);

CREATE TABLE IF NOT EXISTS traces (
  id            INTEGER PRIMARY KEY,
  created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  source        TEXT NOT NULL,
  vault         TEXT NOT NULL,
  query         TEXT NOT NULL,
  strategy      TEXT NOT NULL,
  filters       TEXT NOT NULL DEFAULT '{}',
  params        TEXT NOT NULL DEFAULT '{}',
  results       TEXT NOT NULL,
  latency_ms    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS schema_migrations (
  version       TEXT PRIMARY KEY,
  applied_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

"""Postgres connection and migrations. See
docs/adr/0007-postgres-pgvector-en-windows-nativo.md for why Postgres +
pgvector, and docs/SPEC.md §9 for the schema.
"""

from __future__ import annotations

from pathlib import Path

import psycopg
from psycopg.rows import dict_row

MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "db" / "migrations"

Connection = psycopg.Connection[dict]


def connect(database_url: str) -> Connection:
    """Open a connection to the Postgres server at `database_url`.

    Unlike a file database, nothing is created here: the server must be
    running and the database must already exist (README, "Cómo empezar").
    `row_factory=dict_row` lets repositories read columns by name
    (`row["title"]`) instead of by position.
    """
    return psycopg.connect(database_url, row_factory=dict_row)


def register_vector_type(conn: Connection) -> None:
    """Teach psycopg to send/receive pgvector's `vector` type as numpy
    arrays. Only possible once `CREATE EXTENSION vector` has run in this
    database (the first migration does it), so call it after migrating.
    Nothing needs it until phase 3.
    """
    from pgvector.psycopg import register_vector

    register_vector(conn)


def applied_migrations(conn: Connection) -> set[str]:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "version TEXT PRIMARY KEY, "
        "applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
    )
    conn.commit()
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    # psycopg opens a transaction on the first query and keeps it open until
    # commit. Close it, so each migration below gets its own real transaction
    # instead of a savepoint inside this one (which `close()` would discard).
    conn.commit()
    return {row["version"] for row in rows}


def run_migrations(conn: Connection, migrations_dir: Path = MIGRATIONS_DIR) -> list[str]:
    """Apply every `NNN_*.sql` file in `migrations_dir` that hasn't run yet,
    in filename order, each inside its own transaction. In Postgres even
    `CREATE TABLE` is transactional, so a migration that fails halfway
    leaves nothing behind. Never edit a migration that has already been
    applied anywhere — add a new one (CLAUDE.md "Reglas técnicas").
    """
    done = applied_migrations(conn)
    applied: list[str] = []
    for path in sorted(migrations_dir.glob("*.sql")):
        version = path.stem
        if version in done:
            continue
        sql = path.read_text(encoding="utf-8")
        with conn.transaction():
            # No parameters, so psycopg sends the whole file as one
            # multi-statement script.
            conn.execute(sql)  # type: ignore[arg-type]
            conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (version,))
        applied.append(version)
    return applied

"""SQLite connection and migrations. See docs/adr/0002-sqlite-en-windows-nativo.md
for why SQLite instead of a server database, and docs/SPEC.md §9 for the schema.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "db" / "migrations"


def connect(database_path: Path) -> sqlite3.Connection:
    """Open a connection with the settings this project relies on everywhere:
    - `PRAGMA foreign_keys = ON`: SQLite ignores `REFERENCES ... ON DELETE
      CASCADE` unless you ask for it, on every single connection.
    - `row_factory = sqlite3.Row`: lets repositories read columns by name
      instead of by position, which is what the rest of the code expects.
    """
    database_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try_load_vec_extension(conn)
    return conn


def try_load_vec_extension(conn: sqlite3.Connection) -> bool:
    """Load the sqlite-vec extension if it's installed. Returns whether it
    loaded. Safe to call even before phase 3, when nothing needs it yet —
    `chunk_embeddings` (the vec0 virtual table) is only created once this
    succeeds.
    """
    try:
        import sqlite_vec  # type: ignore[import-not-found]
    except ImportError:
        return False

    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return True


def applied_migrations(conn: sqlite3.Connection) -> set[str]:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "version TEXT PRIMARY KEY, "
        "applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')))"
    )
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {row["version"] for row in rows}


def run_migrations(conn: sqlite3.Connection, migrations_dir: Path = MIGRATIONS_DIR) -> list[str]:
    """Apply every `NNN_*.sql` file in `migrations_dir` that hasn't run yet,
    in filename order, each inside its own transaction. Never edit a
    migration that has already been applied anywhere — add a new one
    (CLAUDE.md "Reglas técnicas").
    """
    done = applied_migrations(conn)
    applied: list[str] = []
    for path in sorted(migrations_dir.glob("*.sql")):
        version = path.stem
        if version in done:
            continue
        sql = path.read_text(encoding="utf-8")
        with conn:
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO schema_migrations (version) VALUES (?)",
                (version,),
            )
        applied.append(version)
    return applied

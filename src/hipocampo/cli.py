"""Command-line entry point. Kept thin on purpose (CLAUDE.md "Capas"): every
command here just calls into `config`, `storage`, `retrieval` or `eval` and
prints the result. New commands land here as later phases add them
(`ingest`, `search`, `eval`).
"""

from __future__ import annotations

import typer
from rich.console import Console

from hipocampo.config import Settings
from hipocampo.storage.db import connect, run_migrations

app = typer.Typer(help="Hipocampo: local hybrid-search engine over Obsidian vaults.")
console = Console()


@app.command()
def init_db() -> None:
    """Create the database file (if missing) and apply any pending migrations."""
    settings = Settings()
    conn = connect(settings.database_path)
    try:
        applied = run_migrations(conn)
    finally:
        conn.close()

    if applied:
        console.print(f"[green]Applied {len(applied)} migration(s):[/green] {', '.join(applied)}")
    else:
        console.print("[dim]Database already up to date.[/dim]")
    console.print(f"Database file: {settings.database_path.resolve()}")


@app.command()
def version() -> None:
    """Print the installed Hipocampo version."""
    from hipocampo import __version__

    console.print(__version__)


if __name__ == "__main__":
    app()

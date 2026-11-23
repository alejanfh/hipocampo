"""Command-line entry point. Kept thin on purpose (CLAUDE.md "Capas"): every
command here just calls into `config`, `storage`, `retrieval` or `eval` and
prints the result. New commands land here as later phases add them
(`ingest`, `search`, `eval`).
"""

from __future__ import annotations

import psycopg
import typer
from psycopg.conninfo import conninfo_to_dict
from rich.console import Console

from hipocampo.config import Settings
from hipocampo.storage.db import connect, run_migrations

app = typer.Typer(help="Hipocampo: local hybrid-search engine over Obsidian vaults.")
console = Console()


@app.command()
def init_db() -> None:
    """Apply any pending migrations to the database in DATABASE_URL."""
    settings = Settings()
    try:
        conn = connect(settings.database_url)
    except psycopg.OperationalError as exc:
        console.print(f"[red]Can't connect to {_redact(settings.database_url)}[/red]\n{exc}")
        console.print(
            "Is the PostgreSQL service running and does the database exist? "
            "See README, 'Cómo empezar'."
        )
        raise typer.Exit(code=1) from exc
    try:
        applied = run_migrations(conn)
    finally:
        conn.close()

    if applied:
        console.print(f"[green]Applied {len(applied)} migration(s):[/green] {', '.join(applied)}")
    else:
        console.print("[dim]Database already up to date.[/dim]")
    console.print(f"Database: {_redact(settings.database_url)}")


def _redact(url: str) -> str:
    """Describe a connection URL without its password, for printing."""
    parts = conninfo_to_dict(url)
    host, port = parts.get("host", "localhost"), parts.get("port", "5432")
    return f"{parts.get('dbname', '?')} at {host}:{port} (user {parts.get('user', '?')})"


@app.command()
def version() -> None:
    """Print the installed Hipocampo version."""
    from hipocampo import __version__

    console.print(__version__)


if __name__ == "__main__":
    app()

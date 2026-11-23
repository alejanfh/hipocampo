from typer.testing import CliRunner

from hipocampo.cli import app

runner = CliRunner()


def test_init_db_applies_migrations(database_url, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", database_url)

    first = runner.invoke(app, ["init-db"])
    second = runner.invoke(app, ["init-db"])

    assert first.exit_code == 0
    assert "001_init" in first.stdout
    assert "already up to date" in second.stdout
    assert "password" not in first.stdout


def test_init_db_explains_connection_errors(monkeypatch):
    # Port 1 is never a Postgres server: the connection is refused at once.
    monkeypatch.setenv("DATABASE_URL", "postgresql://nobody:secret@localhost:1/nope")

    result = runner.invoke(app, ["init-db"])

    assert result.exit_code == 1
    assert "Can't connect" in result.stdout
    assert "secret" not in result.stdout


def test_version_prints_something():
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.stdout.strip() != ""

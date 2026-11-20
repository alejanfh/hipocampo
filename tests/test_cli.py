from typer.testing import CliRunner

from hipocampo.cli import app

runner = CliRunner()


def test_init_db_creates_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "data" / "hipocampo.db"))

    result = runner.invoke(app, ["init-db"])

    assert result.exit_code == 0
    assert (tmp_path / "data" / "hipocampo.db").exists()


def test_version_prints_something():
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.stdout.strip() != ""

from hipocampo.storage.db import applied_migrations, connect, run_migrations


def test_run_migrations_creates_tables(tmp_path):
    conn = connect(tmp_path / "test.db")

    applied = run_migrations(conn)

    assert "001_init" in applied
    tables = {
        row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert {"notes", "chunks", "traces", "schema_migrations"} <= tables


def test_run_migrations_is_idempotent(tmp_path):
    conn = connect(tmp_path / "test.db")

    first_run = run_migrations(conn)
    second_run = run_migrations(conn)

    assert first_run == ["001_init"]
    assert second_run == []  # already applied, nothing to do
    assert applied_migrations(conn) == {"001_init"}


def test_foreign_keys_are_enforced(tmp_path):
    conn = connect(tmp_path / "test.db")
    run_migrations(conn)

    fk_enabled = conn.execute("PRAGMA foreign_keys").fetchone()[0]

    assert fk_enabled == 1

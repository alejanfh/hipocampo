from hipocampo.storage.db import applied_migrations, register_vector_type, run_migrations


def test_run_migrations_creates_tables(conn):
    applied = run_migrations(conn)

    assert "001_init" in applied
    rows = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    ).fetchall()
    tables = {row["table_name"] for row in rows}
    assert {"notes", "chunks", "traces", "schema_migrations"} <= tables


def test_run_migrations_is_idempotent(conn):
    first_run = run_migrations(conn)
    second_run = run_migrations(conn)

    assert first_run == ["001_init"]
    assert second_run == []  # already applied, nothing to do
    assert applied_migrations(conn) == {"001_init"}


def test_pgvector_extension_is_enabled(conn):
    run_migrations(conn)

    row = conn.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'").fetchone()

    assert row is not None


def test_cosine_distance_on_embedding_column(conn):
    """The whole reason for pgvector: store a vector and order by distance."""
    run_migrations(conn)
    register_vector_type(conn)
    note_id = conn.execute(
        "INSERT INTO notes (vault, path, title, folder, content_hash) "
        "VALUES ('test', 'a.md', 'A', '', 'h') RETURNING id"
    ).fetchone()["id"]
    near, far = [1.0] + [0.0] * 383, [0.0] * 383 + [1.0]
    for ordinal, vector in enumerate([far, near]):
        conn.execute(
            "INSERT INTO chunks (note_id, ordinal, heading_path, text, indexed_text, "
            "token_count, embedding) VALUES (%s, %s, '', 't', 't', 1, %s::vector)",
            (note_id, ordinal, str(vector)),
        )

    query = str([0.9, 0.1] + [0.0] * 382)
    rows = conn.execute(
        "SELECT ordinal, embedding <=> %s::vector AS distance FROM chunks ORDER BY distance",
        (query,),
    ).fetchall()

    assert [row["ordinal"] for row in rows] == [1, 0]  # `near` comes first


def test_deleting_a_note_deletes_its_chunks(conn):
    run_migrations(conn)
    note_id = conn.execute(
        "INSERT INTO notes (vault, path, title, folder, content_hash) "
        "VALUES ('test', 'a.md', 'A', '', 'h') RETURNING id"
    ).fetchone()["id"]
    conn.execute(
        "INSERT INTO chunks (note_id, ordinal, heading_path, text, indexed_text, token_count) "
        "VALUES (%s, 0, '', 't', 't', 1)",
        (note_id,),
    )

    conn.execute("DELETE FROM notes WHERE id = %s", (note_id,))

    assert conn.execute("SELECT count(*) AS n FROM chunks").fetchone()["n"] == 0

"""Shared test fixtures.

The storage tests need a real Postgres with pgvector: mocking SQL would
test nothing. They use TEST_DATABASE_URL (a separate database, never the
one in DATABASE_URL, because every test wipes its tables) and are skipped
with a clear reason when that server isn't reachable.
"""

from __future__ import annotations

import psycopg
import pytest
from pydantic_settings import BaseSettings, SettingsConfigDict

from hipocampo.storage.db import connect

DEFAULT_TEST_DATABASE_URL = "postgresql://hipocampo:hipocampo@localhost:5432/hipocampo_test"

APP_TABLES = ("traces", "chunks", "notes", "schema_migrations")


class TestSettings(BaseSettings):
    """Same `.env` / environment lookup as the app's Settings, test-only key."""

    __test__ = False  # not a test class, despite the name
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    test_database_url: str = DEFAULT_TEST_DATABASE_URL
    # CI sets this so a missing database fails the run instead of skipping.
    require_test_database: bool = False


@pytest.fixture
def database_url() -> str:
    """URL of an empty test database (app tables dropped before each test)."""
    settings = TestSettings()
    url = settings.test_database_url
    try:
        conn = connect(url)
    except psycopg.OperationalError as exc:
        if settings.require_test_database:
            raise
        pytest.skip(f"Postgres test database not reachable ({exc.__class__.__name__})")
    with conn:
        conn.execute(f"DROP TABLE IF EXISTS {', '.join(APP_TABLES)} CASCADE")
    return url


@pytest.fixture
def conn(database_url):
    connection = connect(database_url)
    yield connection
    connection.close()

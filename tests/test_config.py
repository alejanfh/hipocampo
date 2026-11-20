from pathlib import Path

from hipocampo.config import Settings, VaultConfig


def test_settings_defaults(monkeypatch, tmp_path):
    # Isolate from any real .env in the repo root during the test run.
    monkeypatch.chdir(tmp_path)
    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.database_path == Path("data/hipocampo.db")
    assert settings.vault_config == Path("configs/demo.yaml")
    assert settings.embedding_model == "intfloat/multilingual-e5-small"


def test_vault_config_load(tmp_path):
    config_path = tmp_path / "demo.yaml"
    config_path.write_text(
        """
        name: demo
        path: vault-demo/
        exclude: ["Plantillas/**"]
        fields:
          date: fecha
          area: departamento
          tags: etiquetas
        """,
        encoding="utf-8",
    )

    config = VaultConfig.load(config_path)

    assert config.name == "demo"
    assert config.path == Path("vault-demo/")
    assert config.fields.area == "departamento"
    assert config.exclude == ["Plantillas/**"]


def test_vault_config_field_defaults(tmp_path):
    config_path = tmp_path / "minimal.yaml"
    config_path.write_text("name: minimal\npath: notes/\n", encoding="utf-8")

    config = VaultConfig.load(config_path)

    # Defaults match the real vault's own frontmatter field names.
    assert config.fields.date == "fecha"
    assert config.fields.area == "area"
    assert config.filters == ["area", "folder", "date"]

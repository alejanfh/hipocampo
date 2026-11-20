"""Two layers of configuration, kept deliberately separate (see CONTEXT.md
"Configuración de vault" and docs/SPEC.md §7):

- `Settings`: machine-level, from `.env` (which database file, which vault
  config to use, which embedding model). Never committed.
- `VaultConfig`: vault-level, from `configs/<vault>.yaml` (where the notes
  live, which frontmatter fields mean what). One file per vault; the demo
  vault's config is public, the real vault's is not.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Machine-level settings, loaded from environment variables / `.env`."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_path: Path = Field(default=Path("data/hipocampo.db"))
    vault_config: Path = Field(default=Path("configs/demo.yaml"))
    embedding_model: str = Field(default="intfloat/multilingual-e5-small")


class VaultFields(BaseModel):
    """Which frontmatter key means what, for this particular vault.

    Different vaults name things differently (the demo vault uses
    `departamento`, the real vault uses `area`) — this mapping is what lets
    the same code work for both without caring which.
    """

    date: str = "fecha"
    area: str = "area"
    tags: str = "etiquetas"


class VaultConfig(BaseModel):
    """A vault's configuration: `configs/<vault>.yaml`."""

    name: str
    path: Path
    include: list[str] = Field(default_factory=lambda: ["**/*.md"])
    exclude: list[str] = Field(default_factory=list)
    fields: VaultFields = Field(default_factory=VaultFields)
    filters: list[str] = Field(default_factory=lambda: ["area", "folder", "date"])
    index_notes: bool = True

    @classmethod
    def load(cls, path: Path) -> VaultConfig:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls.model_validate(raw)


def load_vault_config(settings: Settings | None = None) -> VaultConfig:
    """Load the vault config pointed at by `Settings.vault_config`."""
    settings = settings or Settings()
    return VaultConfig.load(settings.vault_config)

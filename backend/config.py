from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "postgres"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    job_tracker_storage_dir: Path = Field(default=Path("storage/documents"))

    backend_host: str = "127.0.0.1"
    backend_port: int = 9002
    frontend_origin: str = "http://localhost:9001"
    log_level: str = "INFO"
    scrape_timeout_ms: int = 20_000
    codex_cli_command: str = "codex"
    codex_cli_args: str = "exec -"
    codex_cli_timeout_seconds: int = 120
    codex_bridge_prompt_file: Path = Field(default=Path("backend/prompts/codex_bridge.md"))
    codex_job_extraction_prompt_file: Path = Field(
        default=Path("backend/prompts/job_post_extraction.md")
    )

    ssh_sync_host: str | None = None
    ssh_sync_port: int = 22
    ssh_sync_user: str | None = None
    ssh_sync_key_file: Path | None = None
    ssh_sync_remote_dir: str | None = None
    ssh_sync_interval_seconds: int = 300

    @property
    def ssh_sync_configured(self) -> bool:
        return bool(self.ssh_sync_host and self.ssh_sync_user and self.ssh_sync_remote_dir)

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parent.parent

    def resolve_project_path(self, path: Path) -> Path:
        expanded = path.expanduser()
        if expanded.is_absolute():
            return expanded.resolve()
        return (self.project_root / expanded).resolve()

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def storage_dir(self) -> Path:
        return self.resolve_project_path(self.job_tracker_storage_dir)

    @property
    def codex_bridge_prompt_path(self) -> Path:
        return self.resolve_project_path(self.codex_bridge_prompt_file)

    @property
    def codex_job_extraction_prompt_path(self) -> Path:
        return self.resolve_project_path(self.codex_job_extraction_prompt_file)


@lru_cache
def get_settings() -> Settings:
    return Settings()

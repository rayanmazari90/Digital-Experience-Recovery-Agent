from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Digital Experience Recovery Agent"
    env: str = "dev"
    database_path: Path = Path("./var/dera.sqlite3")
    storage_root: Path = Path("./workspace-storage")
    hermes_base_url: str = "http://127.0.0.1:8000"
    hermes_api_key: str = "dev-local-only"
    hermes_model: str = "digital-recovery-agent"
    hermes_enabled: bool = False
    cors_allow_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    api_auth_enabled: bool = False
    api_key: str = "dev-local-only"
    retention_days: int = 7
    max_upload_bytes: int = 1_000_000
    allow_sensitive_payloads: bool = False
    tts_provider: str = "kokoro"
    tts_kokoro_voice: str = "af_heart"
    tts_kokoro_lang_code: str = "a"
    tts_kokoro_speed: float = 1.22
    tts_sample_rate: int = 24000
    tts_max_chars: int = 420

    model_config = SettingsConfigDict(
        env_prefix="DERA_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

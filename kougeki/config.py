"""Application configuration using :mod:`pydantic` settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment or ``.env``."""

    openai_api_key: str = ""
    chat_model: str = "gpt-4.1-mini-2025-04-14"
    moderation_model: str = "omni-moderation-latest"
    log_level: str = "INFO"
    log_file: str = "kougeki.log"
    chat_temperature: float = 0.1
    llm_weight: float = 0.7
    hate_weight: float = 0.2
    violence_weight: float = 0.1

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def is_configured(self) -> bool:
        return bool(self.openai_api_key)


settings = Settings()

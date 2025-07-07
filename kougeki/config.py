import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(slots=True)
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    chat_model: str = "gpt-4.1-mini-2025-04-14"
    moderation_model: str = "omni-moderation-latest"

    @property
    def is_configured(self) -> bool:
        return bool(self.openai_api_key)


settings = Settings()

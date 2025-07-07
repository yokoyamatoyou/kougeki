"""Entry point for the Kougeki GUI tool."""

from kougeki.view import ModerationView
from kougeki.logging_config import setup_logging
from kougeki.config import settings

if __name__ == "__main__":
    setup_logging()
    if not settings.is_configured:
        raise RuntimeError(
            "OpenAI API key is not configured. Set OPENAI_API_KEY in .env"
        )
    app = ModerationView()
    app.mainloop()

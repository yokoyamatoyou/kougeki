from kougeki.view import ModerationView
from kougeki.logging_config import setup_logging

if __name__ == "__main__":
    setup_logging()
    app = ModerationView()
    app.mainloop()

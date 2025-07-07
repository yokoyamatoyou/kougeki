# Kougeki

Simple GUI tool for analyzing text aggressiveness using OpenAI API.
The application loads an Excel file, sends each row to the moderation
and chat endpoints asynchronously, and writes the results back.

## Requirements

- Python 3.11+
- OpenAI API key in `.env`
- Optional `LOG_LEVEL` and `LOG_FILE` for logging

Run `python main.py` to start the GUI.

## Running Tests

Install test dependencies and execute the suite:

```bash
python -m pip install -r requirements.txt
pytest -q
```

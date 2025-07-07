# Kougeki

Simple GUI tool for analyzing text aggressiveness using OpenAI API.
The application loads an Excel file, sends each row to the moderation
and chat endpoints asynchronously, and writes the results back.
Moderation scores are combined with the LLM prediction to create an
``aggressiveness_overall`` column representing the final rating.

## Requirements

- Python 3.11+
- OpenAI API key in `.env`
- The application exits if the key is missing
- Optional `LOG_LEVEL` and `LOG_FILE` for logging
- `pandas` for reading and writing Excel files

Run `python main.py` to start the GUI.

## Running Tests

Install test dependencies and execute the suite:

```bash
python -m pip install -r requirements.txt
pytest -q
```

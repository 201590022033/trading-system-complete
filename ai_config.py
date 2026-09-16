"""Local-only AI runtime configuration; never prints or persists values."""
from pathlib import Path
import os
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent

def project_environment(environ=None):
    source = os.environ if environ is None else environ
    disabled = str(source.get("PYTHON_DOTENV_DISABLED", "") if environ is not None else os.environ.get("PYTHON_DOTENV_DISABLED", "")).lower()
    values = {} if disabled in {"1", "true", "yes"} else {
        k: v for k, v in dotenv_values(ROOT / ".env").items() if v is not None
    }
    values.update(dict(source))
    return values

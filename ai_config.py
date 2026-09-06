"""Local-only AI runtime configuration; never prints or persists values."""
from pathlib import Path
import os
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent

def project_environment(environ=None):
    values = {k: v for k, v in dotenv_values(ROOT / ".env").items() if v is not None}
    values.update(dict(os.environ if environ is None else environ))
    return values

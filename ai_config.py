"""Local-only AI runtime configuration; never prints or persists values."""
from pathlib import Path
import os
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent

def project_environment(environ=None):
    source = os.environ if environ is None else environ
    # Process-wide opt-out is a safety boundary, including explicit mappings.
    disabled = any(str(env.get('PYTHON_DOTENV_DISABLED','')).strip().lower() in {'1','true','yes'}
                   for env in (os.environ,source))
    values = {} if disabled else {
        k: v for k, v in dotenv_values(ROOT / ".env").items() if v is not None
    }
    values.update(dict(source))
    return values

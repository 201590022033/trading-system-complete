"""Explicit service role prevents a cron deployment from accidentally starting web."""
import os


def command(environ):
    role = environ.get("RAILWAY_START_ROLE", "web")
    if role == "worker":
        return ["python", "-m", "workers.heartbeat", "--scheduled"]
    if role != "web":
        raise ValueError("unknown Railway start role")
    return ["gunicorn", "--bind", "0.0.0.0:"+environ.get("PORT", "8080"), "--workers", "1", "app:app"]


if __name__ == "__main__":
    argv = command(os.environ)
    os.execvp(argv[0], argv)

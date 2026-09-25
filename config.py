"""Zugangsdaten aus Umgebungsvariablen lesen.

Tokens und Passwörter stehen bewusst NICHT im Quelltext und nicht in einer
JSON-Datei im Projektordner, sondern in einer lokalen .env-Datei, die per
.gitignore von der Versionsverwaltung ausgeschlossen ist.
Vorlage: .env.example

Ist python-dotenv installiert, wird .env automatisch geladen; ansonsten
funktionieren weiterhin ganz normale Umgebungsvariablen des Systems.
"""

import os

try:  # optionale Abhängigkeit
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - hängt von der Installation ab
    pass


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def telegram_config() -> dict:
    return {
        "token": _env("TELEGRAM_BOT_TOKEN"),
        "chat_id": _env("TELEGRAM_CHAT_ID"),
    }


def email_config() -> dict:
    return {
        "address": _env("GMAIL_ADDRESS"),
        "app_password": _env("GMAIL_APP_PASSWORD"),
        "to": _env("REMINDER_EMAIL_TO") or _env("GMAIL_ADDRESS"),
    }


def telegram_ready() -> bool:
    c = telegram_config()
    return bool(c["token"] and c["chat_id"])


def email_ready() -> bool:
    c = email_config()
    return bool(c["address"] and c["app_password"] and c["to"])


def language() -> str:
    """Sprache der Oberfläche, Standard Deutsch."""
    return _env("PLANNER_LANGUAGE", "de") or "de"

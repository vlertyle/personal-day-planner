"""Zugangsdaten aus Umgebungsvariablen lesen und speichern.

Tokens und Passwörter stehen bewusst NICHT im Quelltext und nicht in einer
JSON-Datei im Projektordner, sondern in einer lokalen .env-Datei, die per
.gitignore von der Versionsverwaltung ausgeschlossen ist.
Vorlage: .env.example

Die Oberfläche (main.py) erlaubt weiterhin die Eingabe von Token und
Passwörtern in eigenen Feldern - "Zugangsdaten aus Umgebungsvariablen lesen"
heißt nur, dass sie NICHT im Quelltext oder in einer versionierten Datei
landen. save_env_values() schreibt die Eingaben in die lokale .env.

Ist python-dotenv installiert, wird .env beim Programmstart automatisch
geladen; ansonsten funktionieren weiterhin ganz normale Umgebungsvariablen
des Betriebssystems.
"""

import os

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

try:  # optionale Abhängigkeit
    from dotenv import load_dotenv

    load_dotenv(ENV_PATH)
except ImportError:  # pragma: no cover - hängt von der Installation ab
    pass


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def telegram_config() -> dict:
    return {
        "enabled": _bool_env("TELEGRAM_ENABLED"),
        "token": _env("TELEGRAM_BOT_TOKEN"),
        "chat_id": _env("TELEGRAM_CHAT_ID"),
    }


def email_config() -> dict:
    return {
        "enabled": _bool_env("EMAIL_ENABLED"),
        "address": _env("GMAIL_ADDRESS"),
        "app_password": _env("GMAIL_APP_PASSWORD"),
        "to": _env("REMINDER_EMAIL_TO") or _env("GMAIL_ADDRESS"),
    }


def telegram_ready() -> bool:
    """Ob per Telegram gesendet werden darf: aktiviert UND vollständig ausgefüllt."""
    c = telegram_config()
    return c["enabled"] and bool(c["token"] and c["chat_id"])


def email_ready() -> bool:
    """Ob per E-Mail gesendet werden darf: aktiviert UND vollständig ausgefüllt."""
    c = email_config()
    return c["enabled"] and bool(c["address"] and c["app_password"] and c["to"])


def language() -> str:
    """Sprache der Oberfläche, Standard Deutsch."""
    return _env("PLANNER_LANGUAGE", "de") or "de"


# ---------- Speichern der Einstellungen aus der Oberfläche ----------


def _read_env_file() -> dict:
    """Aktuellen Inhalt der .env als Dictionary lesen (leer, wenn Datei fehlt)."""
    values = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip()
    return values


def save_env_values(updates: dict) -> None:
    """Werte in die lokale .env schreiben und sofort im laufenden Prozess übernehmen.

    Bestehende, hier nicht genannte Schlüssel bleiben erhalten. Die Datei wird
    dabei neu geschrieben, Kommentare aus .env.example gehen dabei verloren -
    das ist hier bewusst in Kauf genommen, damit das Format einfach bleibt.
    """
    values = _read_env_file()
    values.update({k: str(v) for k, v in updates.items()})

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        for key, value in values.items():
            f.write(f"{key}={value}\n")

    os.environ.update(values)

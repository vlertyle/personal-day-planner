"""Kleine Übersetzungsschicht (i18n).

Alle sichtbaren Texte liegen in locales/<sprache>.json, nicht im Code.
Eine neue Sprache hinzufügen = eine neue JSON-Datei anlegen.

    from i18n import t, set_language
    set_language("de")
    t("app.title")                      -> "Persönlicher Tagesplaner"
    t("stats.day", done=2, total=5)     -> "2 von 5 Aufgaben erledigt"
"""

import json
import os

LOCALES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locales")
DEFAULT_LANGUAGE = "de"

_strings: dict = {}
_language = DEFAULT_LANGUAGE


def available_languages() -> list[str]:
    """Alle Sprachen, für die eine JSON-Datei existiert."""
    if not os.path.isdir(LOCALES_DIR):
        return []
    return sorted(f[:-5] for f in os.listdir(LOCALES_DIR) if f.endswith(".json"))


def set_language(language: str = DEFAULT_LANGUAGE) -> None:
    """Sprachdatei laden. Unbekannte Sprache -> Fallback auf Deutsch."""
    global _strings, _language

    path = os.path.join(LOCALES_DIR, f"{language}.json")
    if not os.path.exists(path):
        language = DEFAULT_LANGUAGE
        path = os.path.join(LOCALES_DIR, f"{DEFAULT_LANGUAGE}.json")

    with open(path, "r", encoding="utf-8") as f:
        _strings = json.load(f)
    _language = language


def current_language() -> str:
    return _language


def t(key: str, **kwargs) -> str:
    """Übersetzten Text holen. Platzhalter werden per str.format() gefüllt.

    Fehlt ein Schlüssel, wird der Schlüssel selbst zurückgegeben –
    so bleibt die Anwendung benutzbar und die Lücke ist sofort sichtbar.
    """
    if not _strings:
        set_language(DEFAULT_LANGUAGE)

    text = _strings.get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text

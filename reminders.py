"""Versand der Erinnerungen – Telegram und E-Mail.

Dieses Modul kennt die Oberfläche nicht. Es kann nur:
  - aus einer Aufgabenliste einen Erinnerungstext bauen
  - diesen Text per Telegram-Bot oder per Gmail (SMTP) verschicken

Zugangsdaten kommen aus config.py (Umgebungsvariablen), nicht aus Parametern
im Code oder aus einer JSON-Datei.

Verwendet ausschließlich die Standardbibliothek:
    smtplib / email.message -> E-Mail
    urllib                  -> HTTP-Aufruf der Telegram-Bot-API
"""

import smtplib
import urllib.error
import urllib.parse
import urllib.request
from email.message import EmailMessage

import config
from i18n import t

TELEGRAM_API = "https://api.telegram.org"


def build_reminder_text(tasks_for_today: list[dict]) -> str | None:
    """Erinnerungstext aus den offenen Aufgaben des Tages.

    Gibt None zurück, wenn nichts offen ist – dann wird nichts verschickt.
    """
    unfinished = [task for task in tasks_for_today if not task["done"]]
    if not unfinished:
        return None

    lines = [t("reminder.header")]
    for task in unfinished:
        lines.append(
            t(
                "reminder.item",
                category=t(f"category.{task['category']}"),
                text=task["text"],
            )
        )
    return "\n".join(lines)


def send_telegram_message(text: str) -> bool:
    """Nachricht über die offizielle Telegram-Bot-API senden."""
    cfg = config.telegram_config()
    if not (cfg["token"] and cfg["chat_id"]):
        return False

    url = f"{TELEGRAM_API}/bot{cfg['token']}/sendMessage"
    data = urllib.parse.urlencode(
        {"chat_id": cfg["chat_id"], "text": text}
    ).encode("utf-8")

    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10) as response:
            return response.status == 200
    except (urllib.error.URLError, OSError) as error:
        print("Telegram:", error)
        return False


def send_email_reminder(subject: str, body: str) -> bool:
    """E-Mail über den Gmail-SMTP-Server senden.

    GMAIL_APP_PASSWORD ist nicht das normale Kontopasswort, sondern ein
    16-stelliges App-Passwort (Google-Konto -> Sicherheit -> App-Passwörter).
    """
    cfg = config.email_config()
    if not (cfg["address"] and cfg["app_password"] and cfg["to"]):
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = cfg["address"]
    message["To"] = cfg["to"]
    message.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as smtp:
            smtp.login(cfg["address"], cfg["app_password"])
            smtp.send_message(message)
        return True
    except (smtplib.SMTPException, OSError) as error:
        print("E-Mail:", error)
        return False

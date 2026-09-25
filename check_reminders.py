"""Erinnerungen prüfen und versenden – ohne Fenster, für die Aufgabenplanung.

Ablauf:
  1. Aufgaben von heute aus tasks_data.json lesen
  2. prüfen, ob etwas offen ist
  3. wenn ja: Telegram und/oder E-Mail versenden (je nachdem, was in .env
     hinterlegt ist)

Täglich automatisch starten:
  Windows  – Aufgabenplanung: täglich 8:00, Programm python.exe,
             Argument check_reminders.py, Arbeitsordner = Projektordner
  Linux/macOS – crontab -e:  0 8 * * * cd /pfad/zum/projekt && python3 check_reminders.py
"""

import config
import reminders
from i18n import set_language, t
from task_manager import TaskManager, today_str


def main() -> None:
    set_language(config.language())

    manager = TaskManager()
    text = reminders.build_reminder_text(manager.get_tasks_for_date(today_str()))

    if text is None:
        print(t("reminder.nothing"))
        return

    if config.telegram_ready():
        ok = reminders.send_telegram_message(text)
        print(t("reminder.sent_telegram", ok=ok))

    if config.email_ready():
        ok = reminders.send_email_reminder(t("reminder.subject"), text)
        print(t("reminder.sent_email", ok=ok))


if __name__ == "__main__":
    main()

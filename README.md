# Tagesplaner

Desktop-Anwendung zur Tagesplanung mit Statistik, Monatskalender und
automatischen Erinnerungen per Telegram oder E-Mail. Geschrieben in Python
mit tkinter, die Oberfläche ist mehrsprachig (Deutsch und Ukrainisch).

## Funktionen

- Aufgaben anlegen, abhaken, kommentieren und löschen
- Kategorien: Schule, Sport, IT, Haushalt – farblich markiert
- Tages- und Wochenstatistik mit Fortschrittsbalken und Disziplin-Score
- Monatskalender: jeder Tag wird nach Erledigungsgrad eingefärbt, ein Klick
  springt zu den Aufgaben dieses Tages
- Tägliche Erinnerung an offene Aufgaben per Telegram-Bot oder Gmail
- Speicherung in einer lokalen JSON-Datei, kein Server nötig
- Mehrsprachigkeit über JSON-Dateien im Ordner `locales/`

## Screenshots

<!-- Bilder in docs/screenshots/ ablegen und hier einbinden -->
![Aufgabenübersicht](docs/screenshots/01-aufgaben.png)
![Statistik](docs/screenshots/03-statistik.png)
![Kalender](docs/screenshots/04-kalender.png)

## Technologien

| Bereich | Einsatz |
| --- | --- |
| Python 3.10+ | Programmiersprache |
| tkinter / ttk | grafische Oberfläche |
| json | Speicherung der Aufgaben und Übersetzungen |
| smtplib, email | Versand der E-Mail-Erinnerungen |
| urllib | Aufruf der Telegram-Bot-API |
| unittest | automatisierte Tests |
| python-dotenv | optional: Zugangsdaten aus `.env` laden |

## Installation

```bash
git clone https://github.com/BENUTZERNAME/tagesplaner.git
cd tagesplaner
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Konfiguration

Zugangsdaten stehen nicht im Quelltext, sondern in einer lokalen
`.env`-Datei, die per `.gitignore` ausgeschlossen ist:

```bash
cp .env.example .env
```

Anschließend in der `.env` eintragen:

| Variable | Bedeutung |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Token des Bots von @BotFather |
| `TELEGRAM_CHAT_ID` | Chat-ID des Empfängers |
| `GMAIL_ADDRESS` | Absenderadresse |
| `GMAIL_APP_PASSWORD` | 16-stelliges App-Passwort von Google |
| `REMINDER_EMAIL_TO` | Empfängeradresse der Erinnerung |
| `PLANNER_LANGUAGE` | `de` oder `uk` |

Ohne diese Werte startet die Anwendung normal, die Erinnerungen sind dann
lediglich deaktiviert.

## Verwendung

```bash
python main.py
```

Erinnerungen ohne geöffnetes Fenster verschicken:

```bash
python check_reminders.py
```

Täglich automatisch starten:

- Windows: Aufgabenplanung, täglich 8:00 Uhr, Programm `python.exe`,
  Argument `check_reminders.py`, Arbeitsordner = Projektordner
- Linux/macOS: `crontab -e` und eintragen
  `0 8 * * * cd /pfad/zum/projekt && python3 check_reminders.py`

## Tests

```bash
python -m unittest discover -s tests -v
```

16 Tests decken das Datenmodell, die Statistik, die Datumsfunktionen, die
Übersetzungen und den Aufbau des Erinnerungstextes ab. Sie brauchen weder
eine Oberfläche noch eine Internetverbindung.

## Projektstruktur

```
tagesplaner/
├── main.py              Oberfläche (tkinter)
├── task_manager.py      Datenmodell: Aufgaben, Statistik, JSON-Datei
├── i18n.py              Übersetzungsschicht
├── config.py            Zugangsdaten aus Umgebungsvariablen
├── reminders.py         Versand per Telegram und E-Mail
├── check_reminders.py   Skript für die tägliche Aufgabenplanung
├── locales/             de.json, uk.json
├── tests/               Unit-Tests
├── .env.example         Vorlage für Zugangsdaten
└── requirements.txt
```

Die Trennung ist bewusst gewählt: `task_manager.py` enthält die Logik und
kennt keine Fenster, `main.py` enthält nur die Darstellung. Dadurch lässt
sich die Logik ohne Oberfläche testen.

## Sprache wechseln

Eine weitere Sprache hinzufügen: eine Datei `locales/xx.json` mit denselben
Schlüsseln anlegen und `PLANNER_LANGUAGE=xx` setzen. Ein Test prüft, dass
alle Sprachdateien denselben Satz an Schlüsseln enthalten.

## Lizenz

MIT

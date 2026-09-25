"""Datenmodell des Tagesplaners.

Diese Datei kennt weder tkinter noch Fenster – sie verwaltet nur Aufgaben
und die JSON-Datei. Dadurch ist sie ohne GUI testbar (siehe tests/).

Eine Aufgabe ist ein Dictionary:
    {
        "id": 1,
        "text": "Mathe-Hausaufgabe",
        "category": "school",        # stabile ID, Anzeige über i18n
        "date": "2026-09-20",        # JJJJ-MM-TT
        "done": False,
        "comment": "",
        "created_at": "2026-09-20T18:30:00"
    }
"""

import datetime
import json
import os

DATA_FILE = "tasks_data.json"

# Stabile Kategorie-IDs. Der sichtbare Name kommt aus locales/<sprache>.json.
CATEGORIES = ["school", "sport", "it", "home"]

# Hintergrundfarbe der Tabellenzeile je Kategorie
CATEGORY_COLORS = {
    "school": "#AED6F1",
    "sport": "#F5CBA7",
    "it": "#A9DFBF",
    "home": "#D2B4DE",
}

# Altbestand aus der ukrainischen Version auf die neuen IDs abbilden
LEGACY_CATEGORIES = {
    "Школа": "school",
    "Спорт": "sport",
    "IT": "it",
    "Домашні справи": "home",
}


class TaskManager:
    def __init__(self, filename: str = DATA_FILE):
        self.filename = filename
        self.tasks: list[dict] = []
        self.load()

    # ---------- Datei ----------

    def load(self) -> None:
        """Aufgaben aus der JSON-Datei laden; fehlt oder defekt -> leere Liste."""
        self.tasks = []
        if not os.path.exists(self.filename):
            return

        with open(self.filename, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return

        if isinstance(data, list):
            self.tasks = [self._migrate(t) for t in data]

    def save(self) -> None:
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _migrate(task: dict) -> dict:
        """Aufgaben aus älteren Versionen auf das aktuelle Format bringen."""
        category = task.get("category", "")
        task["category"] = LEGACY_CATEGORIES.get(category, category or CATEGORIES[0])
        task.setdefault("comment", "")
        task.setdefault("done", False)
        return task

    # ---------- CRUD ----------

    def add_task(self, text: str, category: str, date_str: str, comment: str = "") -> dict:
        """Neue Aufgabe anlegen und sofort speichern."""
        new_id = max((t["id"] for t in self.tasks), default=0) + 1
        task = {
            "id": new_id,
            "text": text,
            "category": category,
            "date": date_str,
            "done": False,
            "comment": comment,
            "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
        }
        self.tasks.append(task)
        self.save()
        return task

    def toggle_done(self, task_id: int) -> None:
        task = self.find(task_id)
        if task is not None:
            task["done"] = not task["done"]
            self.save()

    def set_comment(self, task_id: int, comment: str) -> None:
        task = self.find(task_id)
        if task is not None:
            task["comment"] = comment
            self.save()

    def delete_task(self, task_id: int) -> None:
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        self.save()

    def find(self, task_id: int) -> dict | None:
        for t in self.tasks:
            if t["id"] == task_id:
                return t
        return None

    # ---------- Abfragen ----------

    def get_tasks_for_date(self, date_str: str) -> list[dict]:
        return [t for t in self.tasks if t["date"] == date_str]

    def get_tasks_for_range(self, start_date: str, end_date: str) -> list[dict]:
        return [t for t in self.tasks if start_date <= t["date"] <= end_date]

    # ---------- Statistik ----------

    @staticmethod
    def _stats(tasks: list[dict]) -> tuple[int, int, int]:
        total = len(tasks)
        done = sum(1 for t in tasks if t["done"])
        percent = round(done / total * 100) if total else 0
        return total, done, percent

    def stats_for_date(self, date_str: str) -> tuple[int, int, int]:
        """(gesamt, erledigt, Prozent) für einen Tag."""
        return self._stats(self.get_tasks_for_date(date_str))

    def stats_for_range(self, start_date: str, end_date: str) -> tuple[int, int, int]:
        """(gesamt, erledigt, Prozent) für einen Zeitraum, z. B. eine Woche."""
        return self._stats(self.get_tasks_for_range(start_date, end_date))


# ---------- Datums-Hilfsfunktionen ----------


def today_str() -> str:
    return datetime.date.today().isoformat()


def week_range(date_str: str) -> tuple[str, str]:
    """(Montag, Sonntag) der Woche, in der date_str liegt."""
    d = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    monday = d - datetime.timedelta(days=d.weekday())
    sunday = monday + datetime.timedelta(days=6)
    return monday.isoformat(), sunday.isoformat()


def is_valid_date(date_str: str) -> bool:
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

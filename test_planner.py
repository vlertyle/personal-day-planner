"""Tests für den Tagesplaner.

Getestet wird die Logik ohne Oberfläche: Datenmodell, Statistik,
Übersetzungen und der Aufbau des Erinnerungstextes.

Ausführen:  python -m unittest discover -s tests -v
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
import i18n  # noqa: E402
import reminders  # noqa: E402
from task_manager import TaskManager, is_valid_date, week_range  # noqa: E402


class TaskManagerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        os.unlink(self.tmp.name)
        self.manager = TaskManager(self.tmp.name)

    def tearDown(self):
        if os.path.exists(self.tmp.name):
            os.unlink(self.tmp.name)

    def test_add_task_assigns_increasing_ids(self):
        first = self.manager.add_task("Mathe", "school", "2026-09-20")
        second = self.manager.add_task("Laufen", "sport", "2026-09-20")
        self.assertEqual(first["id"], 1)
        self.assertEqual(second["id"], 2)
        self.assertFalse(first["done"])

    def test_toggle_done_switches_both_ways(self):
        task = self.manager.add_task("Python lernen", "it", "2026-09-20")
        self.manager.toggle_done(task["id"])
        self.assertTrue(self.manager.find(task["id"])["done"])
        self.manager.toggle_done(task["id"])
        self.assertFalse(self.manager.find(task["id"])["done"])

    def test_delete_task_removes_only_that_task(self):
        keep = self.manager.add_task("Bleibt", "home", "2026-09-20")
        remove = self.manager.add_task("Weg", "home", "2026-09-20")
        self.manager.delete_task(remove["id"])
        self.assertEqual([t["id"] for t in self.manager.tasks], [keep["id"]])

    def test_tasks_are_persisted_to_disk(self):
        self.manager.add_task("Speichern", "it", "2026-09-20", comment="Notiz")
        reloaded = TaskManager(self.tmp.name)
        self.assertEqual(len(reloaded.tasks), 1)
        self.assertEqual(reloaded.tasks[0]["comment"], "Notiz")

    def test_corrupt_file_does_not_crash(self):
        with open(self.tmp.name, "w", encoding="utf-8") as f:
            f.write("{kaputt")
        self.assertEqual(TaskManager(self.tmp.name).tasks, [])

    def test_legacy_categories_are_migrated(self):
        legacy = [{"id": 1, "text": "Alt", "category": "Школа", "date": "2026-09-20", "done": False}]
        with open(self.tmp.name, "w", encoding="utf-8") as f:
            json.dump(legacy, f, ensure_ascii=False)
        manager = TaskManager(self.tmp.name)
        self.assertEqual(manager.tasks[0]["category"], "school")
        self.assertEqual(manager.tasks[0]["comment"], "")

    def test_stats_for_date(self):
        done = self.manager.add_task("A", "it", "2026-09-20")
        self.manager.add_task("B", "it", "2026-09-20")
        self.manager.add_task("C", "it", "2026-09-21")
        self.manager.toggle_done(done["id"])
        self.assertEqual(self.manager.stats_for_date("2026-09-20"), (2, 1, 50))

    def test_stats_for_empty_day_is_zero_not_error(self):
        self.assertEqual(self.manager.stats_for_date("2026-01-01"), (0, 0, 0))


class DateHelperTest(unittest.TestCase):
    def test_week_range_starts_on_monday(self):
        # 2026-09-20 ist ein Sonntag
        self.assertEqual(week_range("2026-09-20"), ("2026-09-14", "2026-09-20"))

    def test_is_valid_date(self):
        self.assertTrue(is_valid_date("2026-09-20"))
        self.assertFalse(is_valid_date("20.09.2026"))
        self.assertFalse(is_valid_date("2026-13-01"))


class I18nTest(unittest.TestCase):
    def test_german_is_default_and_translates(self):
        i18n.set_language("de")
        self.assertEqual(i18n.t("category.school"), "Schule")

    def test_placeholders_are_filled(self):
        i18n.set_language("de")
        self.assertIn("5", i18n.t("stats.today", done=3, total=5, percent=60))

    def test_unknown_language_falls_back_to_german(self):
        i18n.set_language("xx")
        self.assertEqual(i18n.current_language(), "de")

    def test_all_locales_share_the_same_keys(self):
        i18n.set_language("de")
        german = set(_load_locale("de"))
        for language in i18n.available_languages():
            self.assertEqual(german, set(_load_locale(language)), f"Schlüssel fehlen in {language}.json")


class ReminderTextTest(unittest.TestCase):
    def setUp(self):
        i18n.set_language("de")

    def test_no_text_when_everything_is_done(self):
        tasks = [{"text": "A", "category": "it", "done": True}]
        self.assertIsNone(reminders.build_reminder_text(tasks))

    def test_only_open_tasks_appear(self):
        tasks = [
            {"text": "Erledigt", "category": "it", "done": True},
            {"text": "Offen", "category": "school", "done": False},
        ]
        text = reminders.build_reminder_text(tasks)
        self.assertIn("Offen", text)
        self.assertNotIn("Erledigt", text)
        self.assertIn("Schule", text)


class ConfigEnvFileTest(unittest.TestCase):
    """save_env_values() schreibt die .env - hier auf eine temporäre Datei umgelenkt."""

    def setUp(self):
        self.original_path = config.ENV_PATH
        self.tmp = tempfile.NamedTemporaryFile(suffix=".env", delete=False)
        self.tmp.close()
        os.unlink(self.tmp.name)
        config.ENV_PATH = self.tmp.name
        for key in ("TELEGRAM_ENABLED", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
            os.environ.pop(key, None)

    def tearDown(self):
        config.ENV_PATH = self.original_path
        if os.path.exists(self.tmp.name):
            os.unlink(self.tmp.name)

    def test_save_creates_file_and_updates_environment(self):
        config.save_env_values({"TELEGRAM_ENABLED": True, "TELEGRAM_BOT_TOKEN": "abc123"})
        self.assertTrue(os.path.exists(self.tmp.name))
        self.assertEqual(os.environ["TELEGRAM_BOT_TOKEN"], "abc123")
        self.assertTrue(config.telegram_config()["enabled"])

    def test_save_preserves_keys_not_mentioned_in_the_update(self):
        config.save_env_values({"TELEGRAM_BOT_TOKEN": "first"})
        config.save_env_values({"TELEGRAM_CHAT_ID": "999"})
        saved = config._read_env_file()
        self.assertEqual(saved["TELEGRAM_BOT_TOKEN"], "first")
        self.assertEqual(saved["TELEGRAM_CHAT_ID"], "999")

    def test_ready_is_false_when_not_enabled_even_with_full_fields(self):
        config.save_env_values(
            {
                "TELEGRAM_ENABLED": False,
                "TELEGRAM_BOT_TOKEN": "abc123",
                "TELEGRAM_CHAT_ID": "999",
            }
        )
        self.assertFalse(config.telegram_ready())


def _load_locale(language: str) -> dict:
    path = os.path.join(i18n.LOCALES_DIR, f"{language}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    unittest.main()

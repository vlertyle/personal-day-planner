"""Persönlicher Tagesplaner – grafische Oberfläche (tkinter).

Aufbau des Projekts:
    task_manager.py  – Datenmodell: Aufgaben, JSON-Datei, Statistik (ohne GUI)
    i18n.py          – Übersetzungen, Texte liegen in locales/*.json
    config.py        – Zugangsdaten aus Umgebungsvariablen (.env)
    reminders.py     – Versand der Erinnerungen (Telegram / E-Mail)
    main.py          – diese Datei: Fenster, Tabellen, Schaltflächen

Die Oberfläche enthält selbst keine Logik: Sie ruft den TaskManager auf und
zeichnet das Ergebnis neu.

Start:  python main.py
"""

import calendar as cal_module
import datetime
import tkinter as tk
from tkinter import messagebox, ttk

import config
import reminders
from i18n import set_language, t
from task_manager import (
    CATEGORIES,
    CATEGORY_COLORS,
    TaskManager,
    is_valid_date,
    today_str,
    week_range,
)

WINDOW_SIZE = "950x620"


def discipline_text(percent: int) -> tuple[str, str]:
    """Bewertung der Wochendisziplin: (Text, Farbe)."""
    if percent >= 80:
        return t("stats.discipline_high", percent=percent), "#1E8449"
    if percent >= 50:
        return t("stats.discipline_mid", percent=percent), "#B7950B"
    return t("stats.discipline_low", percent=percent), "#C0392B"


class PlannerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(t("app.title"))
        self.root.geometry(WINDOW_SIZE)

        self.manager = TaskManager()
        self.selected_date = today_str()

        today = datetime.date.today()
        self.cal_year = today.year
        self.cal_month = today.month

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tasks_tab = ttk.Frame(self.notebook)
        self.stats_tab = ttk.Frame(self.notebook)
        self.calendar_tab = ttk.Frame(self.notebook)
        self.reminders_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.tasks_tab, text=t("tab.tasks"))
        self.notebook.add(self.stats_tab, text=t("tab.stats"))
        self.notebook.add(self.calendar_tab, text=t("tab.calendar"))
        self.notebook.add(self.reminders_tab, text=t("tab.reminders"))

        self.build_tasks_tab()
        self.build_stats_tab()
        self.build_calendar_tab()
        self.build_reminders_tab()

        self.refresh_tasks_view()
        self.refresh_calendar()

    # ------------------------------------------------------
    #  Hilfsfunktionen für Kategorien
    # ------------------------------------------------------

    @staticmethod
    def category_label(category_id: str) -> str:
        return t(f"category.{category_id}")

    def category_id(self, label: str) -> str:
        for category_id in CATEGORIES:
            if self.category_label(category_id) == label:
                return category_id
        return CATEGORIES[0]

    # ------------------------------------------------------
    #  Registerkarte "Aufgaben"
    # ------------------------------------------------------

    def build_tasks_tab(self):
        top = ttk.Frame(self.tasks_tab)
        top.pack(fill="x", pady=6)

        ttk.Button(top, text=t("tasks.prev_day"), command=lambda: self.change_day(-1)).pack(side="left", padx=4)
        ttk.Button(top, text=t("tasks.today"), command=self.go_today).pack(side="left", padx=4)
        ttk.Button(top, text=t("tasks.next_day"), command=lambda: self.change_day(1)).pack(side="left", padx=4)

        self.date_label = ttk.Label(top, text="", font=("Arial", 13, "bold"))
        self.date_label.pack(side="left", padx=20)

        ttk.Label(top, text=t("tasks.filter")).pack(side="left", padx=(20, 4))
        self.filter_var = tk.StringVar(value=t("tasks.filter_all"))
        filter_box = ttk.Combobox(
            top,
            textvariable=self.filter_var,
            values=[t("tasks.filter_all")] + [self.category_label(c) for c in CATEGORIES],
            state="readonly",
            width=18,
        )
        filter_box.pack(side="left")
        filter_box.bind("<<ComboboxSelected>>", lambda event: self.refresh_tasks_view())

        # Tabelle
        columns = ("status", "text", "category", "comment")
        self.tree = ttk.Treeview(self.tasks_tab, columns=columns, show="headings", height=15)
        self.tree.heading("status", text=t("tasks.col_status"))
        self.tree.heading("text", text=t("tasks.col_text"))
        self.tree.heading("category", text=t("tasks.col_category"))
        self.tree.heading("comment", text=t("tasks.col_comment"))

        self.tree.column("status", width=40, anchor="center")
        self.tree.column("text", width=320)
        self.tree.column("category", width=130, anchor="center")
        self.tree.column("comment", width=300)

        self.tree.pack(fill="both", expand=True, padx=4, pady=6)
        self.tree.bind("<Double-1>", lambda event: self.toggle_selected())

        actions = ttk.Frame(self.tasks_tab)
        actions.pack(fill="x", pady=4)

        ttk.Button(actions, text=t("tasks.add"), command=self.open_add_task_dialog).pack(side="left", padx=4)
        ttk.Button(actions, text=t("tasks.toggle"), command=self.toggle_selected).pack(side="left", padx=4)
        ttk.Button(actions, text=t("tasks.comment"), command=self.open_comment_dialog).pack(side="left", padx=4)
        ttk.Button(actions, text=t("tasks.delete"), command=self.delete_selected).pack(side="left", padx=4)

        stat_frame = ttk.Frame(self.tasks_tab)
        stat_frame.pack(fill="x", pady=8)

        self.day_stat_label = ttk.Label(stat_frame, text="", font=("Arial", 11))
        self.day_stat_label.pack(side="left", padx=4)

        self.day_progress = ttk.Progressbar(stat_frame, length=250, maximum=100)
        self.day_progress.pack(side="left", padx=10)

    # ------------------------------------------------------
    #  Registerkarte "Statistik"
    # ------------------------------------------------------

    def build_stats_tab(self):
        frame = ttk.Frame(self.stats_tab, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=t("stats.today_title"), font=("Arial", 14, "bold")).pack(anchor="w")
        self.today_stat_label = ttk.Label(frame, text="", font=("Arial", 12))
        self.today_stat_label.pack(anchor="w", pady=(2, 4))
        self.today_progress = ttk.Progressbar(frame, length=400, maximum=100)
        self.today_progress.pack(anchor="w", pady=(0, 20))

        ttk.Label(frame, text=t("stats.week_title"), font=("Arial", 14, "bold")).pack(anchor="w")
        self.week_stat_label = ttk.Label(frame, text="", font=("Arial", 12))
        self.week_stat_label.pack(anchor="w", pady=(2, 4))
        self.week_progress = ttk.Progressbar(frame, length=400, maximum=100)
        self.week_progress.pack(anchor="w", pady=(0, 20))

        self.discipline_label = ttk.Label(frame, text="", font=("Arial", 13, "bold"))
        self.discipline_label.pack(anchor="w", pady=(10, 0))

        ttk.Button(frame, text=t("stats.refresh"), command=self.refresh_stats).pack(anchor="w", pady=20)

    # ------------------------------------------------------
    #  Registerkarte "Kalender"
    # ------------------------------------------------------

    def build_calendar_tab(self):
        top = ttk.Frame(self.calendar_tab)
        top.pack(pady=8)

        ttk.Button(top, text="◀", command=lambda: self.change_month(-1)).pack(side="left", padx=6)
        self.calendar_label = ttk.Label(top, text="", font=("Arial", 14, "bold"))
        self.calendar_label.pack(side="left", padx=10)
        ttk.Button(top, text="▶", command=lambda: self.change_month(1)).pack(side="left", padx=6)

        legend = ttk.Frame(self.calendar_tab)
        legend.pack(pady=4)
        self._legend_box(legend, "#58D68D", t("calendar.legend_done"))
        self._legend_box(legend, "#F7DC6F", t("calendar.legend_partial"))
        self._legend_box(legend, "#EC7063", t("calendar.legend_open"))
        self._legend_box(legend, "#EAECEE", t("calendar.legend_empty"))

        self.calendar_days_frame = ttk.Frame(self.calendar_tab)
        self.calendar_days_frame.pack(pady=10)

    @staticmethod
    def _legend_box(parent, color: str, text: str):
        box = tk.Frame(parent, bg=color, width=16, height=16)
        box.pack(side="left", padx=(10, 3))
        ttk.Label(parent, text=text).pack(side="left")

    # ------------------------------------------------------
    #  Registerkarte "Erinnerungen"
    # ------------------------------------------------------

    def build_reminders_tab(self):
        frame = ttk.Frame(self.reminders_tab, padding=20)
        frame.pack(fill="both", expand=True)

        tg = config.telegram_config()
        mail = config.email_config()

        # ---------- Telegram ----------
        ttk.Label(frame, text=t("reminders.telegram_title"), font=("Arial", 13, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 6)
        )

        self.telegram_enabled_var = tk.BooleanVar(value=tg["enabled"])
        ttk.Checkbutton(frame, text=t("reminders.enable"), variable=self.telegram_enabled_var).grid(
            row=1, column=0, sticky="w"
        )

        ttk.Label(frame, text=t("reminders.token_label")).grid(row=2, column=0, sticky="w")
        self.telegram_token_entry = ttk.Entry(frame, width=48)
        self.telegram_token_entry.insert(0, tg["token"])
        self.telegram_token_entry.grid(row=2, column=1, sticky="w", pady=2)

        ttk.Label(frame, text=t("reminders.chatid_label")).grid(row=3, column=0, sticky="w")
        self.telegram_chatid_entry = ttk.Entry(frame, width=48)
        self.telegram_chatid_entry.insert(0, tg["chat_id"])
        self.telegram_chatid_entry.grid(row=3, column=1, sticky="w", pady=2)

        ttk.Button(frame, text=t("reminders.test_telegram"), command=self.test_telegram).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(6, 24)
        )

        # ---------- Email (Gmail) ----------
        ttk.Label(frame, text=t("reminders.email_title"), font=("Arial", 13, "bold")).grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(0, 6)
        )

        self.email_enabled_var = tk.BooleanVar(value=mail["enabled"])
        ttk.Checkbutton(frame, text=t("reminders.enable"), variable=self.email_enabled_var).grid(
            row=6, column=0, sticky="w"
        )

        ttk.Label(frame, text=t("reminders.email_label")).grid(row=7, column=0, sticky="w")
        self.email_address_entry = ttk.Entry(frame, width=48)
        self.email_address_entry.insert(0, mail["address"])
        self.email_address_entry.grid(row=7, column=1, sticky="w", pady=2)

        ttk.Label(frame, text=t("reminders.password_label")).grid(row=8, column=0, sticky="w")
        self.email_password_entry = ttk.Entry(frame, width=48, show="*")
        self.email_password_entry.insert(0, mail["app_password"])
        self.email_password_entry.grid(row=8, column=1, sticky="w", pady=2)

        ttk.Label(frame, text=t("reminders.to_label")).grid(row=9, column=0, sticky="w")
        self.email_to_entry = ttk.Entry(frame, width=48)
        self.email_to_entry.insert(0, mail["to"])
        self.email_to_entry.grid(row=9, column=1, sticky="w", pady=2)

        ttk.Button(frame, text=t("reminders.test_email"), command=self.test_email).grid(
            row=10, column=0, columnspan=2, sticky="w", pady=(6, 24)
        )

        # ---------- Speichern ----------
        ttk.Button(frame, text=t("reminders.save"), command=self.save_reminder_settings).grid(
            row=11, column=0, columnspan=2, sticky="w", pady=(4, 10)
        )

        self.reminders_status_label = ttk.Label(frame, text="", font=("Arial", 10, "bold"))
        self.reminders_status_label.grid(row=12, column=0, columnspan=2, sticky="w")

        ttk.Label(frame, text=t("reminders.env_note"), foreground="#7F8C8D", wraplength=760).grid(
            row=13, column=0, columnspan=2, sticky="w", pady=(20, 6)
        )
        ttk.Label(frame, text=t("reminders.cron_note"), foreground="#7F8C8D", wraplength=760).grid(
            row=14, column=0, columnspan=2, sticky="w"
        )

    def _collect_reminder_settings(self) -> dict:
        """Alle Felder der Registerkarte in ein Dictionary für .env lesen."""
        return {
            "TELEGRAM_ENABLED": self.telegram_enabled_var.get(),
            "TELEGRAM_BOT_TOKEN": self.telegram_token_entry.get().strip(),
            "TELEGRAM_CHAT_ID": self.telegram_chatid_entry.get().strip(),
            "EMAIL_ENABLED": self.email_enabled_var.get(),
            "GMAIL_ADDRESS": self.email_address_entry.get().strip(),
            "GMAIL_APP_PASSWORD": self.email_password_entry.get().strip(),
            "REMINDER_EMAIL_TO": self.email_to_entry.get().strip(),
        }

    def save_reminder_settings(self):
        """Eingaben in die lokale .env schreiben (nicht in Quelltext oder Git)."""
        config.save_env_values(self._collect_reminder_settings())
        self.reminders_status_label.config(text=t("reminders.saved"), foreground="#1E8449")

    def test_telegram(self):
        if not (self.telegram_token_entry.get().strip() and self.telegram_chatid_entry.get().strip()):
            messagebox.showwarning(t("msg.error"), t("reminders.missing_fields"))
            return
        self.save_reminder_settings()
        ok = reminders.send_telegram_message(t("reminders.test_message"))
        self._show_result(ok, "reminders.telegram_ok", "reminders.telegram_fail")

    def test_email(self):
        if not (
            self.email_address_entry.get().strip()
            and self.email_password_entry.get().strip()
            and self.email_to_entry.get().strip()
        ):
            messagebox.showwarning(t("msg.error"), t("reminders.missing_fields"))
            return
        self.save_reminder_settings()
        ok = reminders.send_email_reminder(t("reminders.test_subject"), t("reminders.test_message"))
        self._show_result(ok, "reminders.email_ok", "reminders.email_fail")

    def _show_result(self, ok: bool, ok_key: str, fail_key: str):
        self.reminders_status_label.config(
            text=t(ok_key) if ok else t(fail_key),
            foreground="#1E8449" if ok else "#C0392B",
        )

    # ------------------------------------------------------
    #  Dialoge
    # ------------------------------------------------------

    def open_add_task_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title(t("dialog.new_task"))
        dialog.geometry("380x330")
        dialog.grab_set()

        ttk.Label(dialog, text=t("dialog.task_text")).pack(anchor="w", padx=10, pady=(12, 0))
        text_entry = ttk.Entry(dialog, width=42)
        text_entry.pack(padx=10)
        text_entry.focus()

        ttk.Label(dialog, text=t("dialog.category")).pack(anchor="w", padx=10, pady=(12, 0))
        category_var = tk.StringVar(value=self.category_label(CATEGORIES[0]))
        ttk.Combobox(
            dialog,
            textvariable=category_var,
            values=[self.category_label(c) for c in CATEGORIES],
            state="readonly",
        ).pack(padx=10)

        ttk.Label(dialog, text=t("dialog.date")).pack(anchor="w", padx=10, pady=(12, 0))
        date_entry = ttk.Entry(dialog, width=42)
        date_entry.insert(0, self.selected_date)
        date_entry.pack(padx=10)

        ttk.Label(dialog, text=t("dialog.comment")).pack(anchor="w", padx=10, pady=(12, 0))
        comment_entry = ttk.Entry(dialog, width=42)
        comment_entry.pack(padx=10)

        def save_task():
            text = text_entry.get().strip()
            date_str = date_entry.get().strip()

            if not text:
                messagebox.showwarning(t("msg.error"), t("msg.empty_text"))
                return
            if not is_valid_date(date_str):
                messagebox.showwarning(t("msg.error"), t("msg.bad_date"))
                return

            self.manager.add_task(
                text, self.category_id(category_var.get()), date_str, comment_entry.get().strip()
            )
            dialog.destroy()
            self.refresh_tasks_view()
            self.refresh_calendar()

        ttk.Button(dialog, text=t("dialog.save"), command=save_task).pack(pady=18)

    def open_comment_dialog(self):
        task = self._selected_task()
        if task is None:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title(t("dialog.edit_comment"))
        dialog.geometry("380x170")
        dialog.grab_set()

        ttk.Label(dialog, text=t("dialog.task_name", text=task["text"]), wraplength=340).pack(padx=10, pady=(12, 6))
        entry = ttk.Entry(dialog, width=42)
        entry.insert(0, task["comment"])
        entry.pack(padx=10)
        entry.focus()

        def save_comment():
            self.manager.set_comment(task["id"], entry.get().strip())
            dialog.destroy()
            self.refresh_tasks_view()

        ttk.Button(dialog, text=t("dialog.save"), command=save_comment).pack(pady=16)

    # ------------------------------------------------------
    #  Aktionen
    # ------------------------------------------------------

    def _selected_task(self) -> dict | None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo(t("msg.info"), t("msg.select_task"))
            return None
        return self.manager.find(int(selection[0]))

    def toggle_selected(self):
        task = self._selected_task()
        if task is None:
            return
        self.manager.toggle_done(task["id"])
        self.refresh_tasks_view()
        self.refresh_calendar()

    def delete_selected(self):
        task = self._selected_task()
        if task is None:
            return
        if messagebox.askyesno(t("msg.confirm"), t("msg.delete_task")):
            self.manager.delete_task(task["id"])
            self.refresh_tasks_view()
            self.refresh_calendar()

    # ------------------------------------------------------
    #  Navigation
    # ------------------------------------------------------

    def change_day(self, delta: int):
        d = datetime.datetime.strptime(self.selected_date, "%Y-%m-%d").date()
        self.selected_date = (d + datetime.timedelta(days=delta)).isoformat()
        self.refresh_tasks_view()

    def go_today(self):
        self.selected_date = today_str()
        self.refresh_tasks_view()

    def change_month(self, delta: int):
        month = self.cal_month + delta
        if month > 12:
            month, self.cal_year = 1, self.cal_year + 1
        elif month < 1:
            month, self.cal_year = 12, self.cal_year - 1
        self.cal_month = month
        self.refresh_calendar()

    def select_date_from_calendar(self, date_str: str):
        self.selected_date = date_str
        self.notebook.select(self.tasks_tab)
        self.refresh_tasks_view()

    # ------------------------------------------------------
    #  Anzeige aktualisieren
    # ------------------------------------------------------

    def refresh_tasks_view(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        tasks = self.manager.get_tasks_for_date(self.selected_date)

        selected_filter = self.filter_var.get()
        if selected_filter != t("tasks.filter_all"):
            category = self.category_id(selected_filter)
            tasks = [task for task in tasks if task["category"] == category]

        for task in tasks:
            self.tree.insert(
                "",
                "end",
                iid=str(task["id"]),
                values=(
                    "✓" if task["done"] else "–",
                    task["text"],
                    self.category_label(task["category"]),
                    task["comment"],
                ),
                tags=(task["category"],),
            )

        for category, color in CATEGORY_COLORS.items():
            self.tree.tag_configure(category, background=color)

        self.date_label.config(text=t("tasks.date_label", date=self.selected_date))

        total, done, percent = self.manager.stats_for_date(self.selected_date)
        self.day_stat_label.config(text=t("tasks.day_summary", done=done, total=total, percent=percent))
        self.day_progress["value"] = percent

        self.refresh_stats()

    def refresh_stats(self):
        total, done, percent = self.manager.stats_for_date(self.selected_date)
        self.today_stat_label.config(text=t("stats.today", done=done, total=total, percent=percent))
        self.today_progress["value"] = percent

        monday, sunday = week_range(self.selected_date)
        w_total, w_done, w_percent = self.manager.stats_for_range(monday, sunday)
        self.week_stat_label.config(
            text=t("stats.week", start=monday, end=sunday, done=w_done, total=w_total, percent=w_percent)
        )
        self.week_progress["value"] = w_percent

        text, color = discipline_text(w_percent)
        self.discipline_label.config(text=text, foreground=color)

    def refresh_calendar(self):
        for widget in self.calendar_days_frame.winfo_children():
            widget.destroy()

        year, month = self.cal_year, self.cal_month
        self.calendar_label.config(text=t("calendar.month_title", month=t(f"month.{month}"), year=year))

        for index in range(7):
            tk.Label(
                self.calendar_days_frame, text=t(f"weekday.{index}"), font=("Arial", 10, "bold")
            ).grid(row=0, column=index, padx=3, pady=3)

        for week_index, week in enumerate(cal_module.monthcalendar(year, month), start=1):
            for day_index, day in enumerate(week):
                if day == 0:
                    continue
                date_str = f"{year:04d}-{month:02d}-{day:02d}"
                total, _done, percent = self.manager.stats_for_date(date_str)

                if total == 0:
                    bg = "#EAECEE"
                elif percent == 100:
                    bg = "#58D68D"
                elif percent == 0:
                    bg = "#EC7063"
                else:
                    bg = "#F7DC6F"

                tk.Button(
                    self.calendar_days_frame,
                    text=str(day),
                    bg=bg,
                    width=4,
                    height=2,
                    command=lambda d=date_str: self.select_date_from_calendar(d),
                ).grid(row=week_index, column=day_index, padx=3, pady=3)


def main() -> None:
    set_language(config.language())
    root = tk.Tk()
    PlannerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

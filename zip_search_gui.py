#!/usr/bin/env python3
"""Grafische Oberfläche (Tkinter) für zip_search.py.

Start:
    python zip_search_gui.py
"""

import io
import os
import queue
import threading
import tkinter as tk
import zipfile
from tkinter import filedialog, messagebox, ttk

from zip_search import search_zip, write_report


class ZipSearchApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Zip-Suche")
        self.geometry("800x550")
        self.minsize(500, 350)

        self.zip_var = tk.StringVar()
        self.needle_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.ignore_case_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="Bereit.")
        self.results_queue = queue.Queue()

        self._build_widgets()

    def _build_widgets(self):
        form = ttk.Frame(self, padding=10)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Zip-Datei:").grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(form, textvariable=self.zip_var).grid(
            row=0, column=1, sticky="ew", padx=5)
        ttk.Button(form, text="Durchsuchen…", command=self.choose_zip).grid(
            row=0, column=2)

        ttk.Label(form, text="Suchbegriff:").grid(row=1, column=0, sticky="w", pady=3)
        needle_entry = ttk.Entry(form, textvariable=self.needle_var)
        needle_entry.grid(row=1, column=1, sticky="ew", padx=5)
        needle_entry.bind("<Return>", lambda _e: self.start_search())

        ttk.Label(form, text="Ausgabedatei:").grid(row=2, column=0, sticky="w", pady=3)
        ttk.Entry(form, textvariable=self.output_var).grid(
            row=2, column=1, sticky="ew", padx=5)
        ttk.Button(form, text="Speichern unter…", command=self.choose_output).grid(
            row=2, column=2)

        ttk.Checkbutton(
            form, text="Groß-/Kleinschreibung ignorieren",
            variable=self.ignore_case_var,
        ).grid(row=3, column=1, sticky="w", padx=5, pady=3)

        self.search_button = ttk.Button(form, text="Suchen", command=self.start_search)
        self.search_button.grid(row=3, column=2, sticky="ew")

        result_frame = ttk.Frame(self, padding=(10, 0, 10, 0))
        result_frame.pack(fill="both", expand=True)
        self.text = tk.Text(result_frame, wrap="none", state="disabled",
                            font=("Courier", 10))
        yscroll = ttk.Scrollbar(result_frame, orient="vertical", command=self.text.yview)
        xscroll = ttk.Scrollbar(result_frame, orient="horizontal", command=self.text.xview)
        self.text.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        result_frame.rowconfigure(0, weight=1)
        result_frame.columnconfigure(0, weight=1)

        bottom = ttk.Frame(self, padding=10)
        bottom.pack(fill="x")
        self.progress = ttk.Progressbar(bottom, mode="indeterminate", length=120)
        self.progress.pack(side="right")
        ttk.Label(bottom, textvariable=self.status_var).pack(side="left")

    def choose_zip(self):
        path = filedialog.askopenfilename(
            title="Zip-Datei wählen",
            filetypes=[("Zip-Dateien", "*.zip"), ("Alle Dateien", "*.*")],
        )
        if path:
            self.zip_var.set(path)
            if not self.output_var.get():
                base = os.path.splitext(path)[0]
                self.output_var.set(base + "_suchergebnisse.txt")

    def choose_output(self):
        path = filedialog.asksaveasfilename(
            title="Ergebnisse speichern unter",
            defaultextension=".txt",
            filetypes=[("Textdateien", "*.txt"), ("Alle Dateien", "*.*")],
        )
        if path:
            self.output_var.set(path)

    def start_search(self):
        zip_path = self.zip_var.get().strip()
        needle = self.needle_var.get()
        output = self.output_var.get().strip() or "suchergebnisse.txt"

        if not zip_path:
            messagebox.showwarning("Zip-Suche", "Bitte eine Zip-Datei auswählen.")
            return
        if not needle:
            messagebox.showwarning("Zip-Suche", "Bitte einen Suchbegriff eingeben.")
            return

        self.output_var.set(output)
        self.search_button.configure(state="disabled")
        self.progress.start(10)
        self.status_var.set("Suche läuft…")
        self._set_text("")

        # Suche im Hintergrund, damit die Oberfläche nicht einfriert
        threading.Thread(
            target=self._search_worker,
            args=(zip_path, needle, self.ignore_case_var.get(), output),
            daemon=True,
        ).start()
        self.after(100, self._poll_results)

    def _search_worker(self, zip_path, needle, ignore_case, output):
        try:
            with zipfile.ZipFile(zip_path) as zf:
                results = search_zip(zf, needle, ignore_case)
            buf = io.StringIO()
            files, hits = write_report(buf, zip_path, needle, ignore_case, results)
            report = buf.getvalue()
            with open(output, "w", encoding="utf-8") as out:
                out.write(report)
            self.results_queue.put(("ok", report, files, hits, output))
        except FileNotFoundError:
            self.results_queue.put(("error", f"Datei nicht gefunden:\n{zip_path}"))
        except zipfile.BadZipFile:
            self.results_queue.put(("error", f"Keine gültige Zip-Datei:\n{zip_path}"))
        except OSError as exc:
            self.results_queue.put(("error", f"Fehler: {exc}"))

    def _poll_results(self):
        try:
            item = self.results_queue.get_nowait()
        except queue.Empty:
            self.after(100, self._poll_results)
            return

        self.progress.stop()
        self.search_button.configure(state="normal")
        if item[0] == "ok":
            _, report, files, hits, output = item
            self._set_text(report)
            self.status_var.set(
                f"{hits} Treffer in {files} Datei(en). Gespeichert in: {output}")
        else:
            self.status_var.set("Fehler.")
            messagebox.showerror("Zip-Suche", item[1])

    def _set_text(self, content):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.text.configure(state="disabled")


if __name__ == "__main__":
    ZipSearchApp().mainloop()

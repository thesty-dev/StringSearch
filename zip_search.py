#!/usr/bin/env python3
"""Durchsucht alle Dateien in einer Zip-Datei (inkl. Unterverzeichnisse und
verschachtelter Zip-Archive) nach einem String und schreibt die Treffer in
eine Textdatei.

Beispiel:
    python zip_search.py archiv.zip "Suchbegriff" -o ergebnisse.txt -i
"""

import argparse
import io
import sys
import zipfile
from datetime import datetime

ENCODINGS = ("utf-8", "cp1252", "latin-1")


def decode(data):
    """Bytes in Text umwandeln; probiert gängige Kodierungen durch."""
    for enc in ENCODINGS:
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1", errors="replace")


def is_binary(data):
    return b"\x00" in data[:8192]


def search_text(data, needle, ignore_case):
    """Liefert (Zeilennummer, Zeile) für jede Zeile mit Treffer."""
    text = decode(data)
    cmp_needle = needle.lower() if ignore_case else needle
    hits = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        haystack = line.lower() if ignore_case else line
        if cmp_needle in haystack:
            hits.append((lineno, line.strip()))
    return hits


def count_binary(data, needle, ignore_case):
    """Zählt Treffer in Binärdateien (UTF-8 und UTF-16 kodiert)."""
    if ignore_case:
        data = data.lower()
        needle = needle.lower()
    total = 0
    for enc in ("utf-8", "utf-16-le"):
        total += data.count(needle.encode(enc))
    return total


def search_zip(zf, needle, ignore_case, prefix=""):
    """Durchsucht ein geöffnetes ZipFile rekursiv; liefert Ergebnis-Dicts."""
    results = []
    for info in zf.infolist():
        if info.is_dir():
            continue
        path = prefix + info.filename
        try:
            data = zf.read(info)
        except (RuntimeError, zipfile.BadZipFile, NotImplementedError) as exc:
            results.append({"path": path, "error": str(exc)})
            continue

        # Verschachtelte Zip-Dateien ebenfalls durchsuchen
        if info.filename.lower().endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as inner:
                    results.extend(
                        search_zip(inner, needle, ignore_case, path + "/")
                    )
                continue
            except zipfile.BadZipFile:
                pass  # doch keine gültige Zip-Datei -> normal durchsuchen

        if is_binary(data):
            count = count_binary(data, needle, ignore_case)
            if count:
                results.append({"path": path, "binary": count})
        else:
            hits = search_text(data, needle, ignore_case)
            if hits:
                results.append({"path": path, "lines": hits})
    return results


def write_report(out, zip_path, needle, ignore_case, results):
    out.write("Suche in Zip-Datei\n")
    out.write("==================\n")
    out.write(f"Archiv:      {zip_path}\n")
    out.write(f"Suchbegriff: {needle!r}\n")
    out.write(f"Groß/klein:  {'ignoriert' if ignore_case else 'beachtet'}\n")
    out.write(f"Datum:       {datetime.now():%d.%m.%Y %H:%M:%S}\n\n")

    files_with_hits = 0
    total_hits = 0
    for res in results:
        if "error" in res:
            out.write(f"[FEHLER] {res['path']}: {res['error']}\n\n")
        elif "binary" in res:
            files_with_hits += 1
            total_hits += res["binary"]
            out.write(f"{res['path']}  (Binärdatei, {res['binary']} Treffer)\n\n")
        else:
            files_with_hits += 1
            total_hits += len(res["lines"])
            out.write(f"{res['path']}  ({len(res['lines'])} Treffer)\n")
            for lineno, line in res["lines"]:
                out.write(f"    Zeile {lineno}: {line}\n")
            out.write("\n")

    out.write("------------------\n")
    out.write(f"Dateien mit Treffern: {files_with_hits}\n")
    out.write(f"Treffer gesamt:       {total_hits}\n")
    return files_with_hits, total_hits


def main():
    parser = argparse.ArgumentParser(
        description="Durchsucht alle Dateien einer Zip-Datei nach einem String."
    )
    parser.add_argument("zipdatei", help="Pfad zur Zip-Datei")
    parser.add_argument("suchbegriff", help="Gesuchter String")
    parser.add_argument(
        "-o", "--output", default="suchergebnisse.txt",
        help="Ausgabedatei (Standard: suchergebnisse.txt)",
    )
    parser.add_argument(
        "-i", "--ignore-case", action="store_true",
        help="Groß-/Kleinschreibung ignorieren",
    )
    args = parser.parse_args()

    try:
        with zipfile.ZipFile(args.zipdatei) as zf:
            results = search_zip(zf, args.suchbegriff, args.ignore_case)
    except FileNotFoundError:
        sys.exit(f"Datei nicht gefunden: {args.zipdatei}")
    except zipfile.BadZipFile:
        sys.exit(f"Keine gültige Zip-Datei: {args.zipdatei}")

    with open(args.output, "w", encoding="utf-8") as out:
        files, hits = write_report(
            out, args.zipdatei, args.suchbegriff, args.ignore_case, results
        )

    print(f"{hits} Treffer in {files} Datei(en). Ergebnisse: {args.output}")


if __name__ == "__main__":
    main()

# StringSearch

`zip_search.py` durchsucht alle Dateien einer Zip-Datei – inklusive aller
Unterverzeichnisse und verschachtelter Zip-Archive – nach einem String und
schreibt die Ergebnisse in eine Textdatei.

Benötigt nur Python 3 (keine zusätzlichen Pakete).

## Verwendung

```
python zip_search.py <zipdatei> <suchbegriff> [-o ausgabe.txt] [-i]
```

| Option | Bedeutung |
|---|---|
| `-o`, `--output` | Ausgabedatei (Standard: `suchergebnisse.txt`) |
| `-i`, `--ignore-case` | Groß-/Kleinschreibung ignorieren |

Beispiel:

```
python zip_search.py archiv.zip "Hallo" -i -o ergebnisse.txt
```

Für Textdateien werden Dateipfad, Zeilennummer und Zeile ausgegeben,
für Binärdateien die Anzahl der Treffer.

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

## Grafische Oberfläche

```
python zip_search_gui.py
```

Zip-Datei auswählen, Suchbegriff eingeben, optional Ausgabedatei festlegen und
auf **Suchen** klicken. Die Ergebnisse werden im Fenster angezeigt und in der
Ausgabedatei gespeichert (Standard: `<zipname>_suchergebnisse.txt`).

Die Oberfläche nutzt Tkinter, das bei Python unter Windows und macOS bereits
dabei ist. Unter Linux ggf. nachinstallieren, z. B. `sudo apt install python3-tk`.
`zip_search_gui.py` und `zip_search.py` müssen im selben Ordner liegen.

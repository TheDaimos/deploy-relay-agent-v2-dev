# DRA V2 DEV 0.1.57 – Git-Dateibaum-Diagnose aufgelöst

**Datum:** 11.10.2026  
**Zweig:** `feature/v2-10-inventory-operation-contract`  
**Status:** Statische Diagnoseverbesserung mit Negativtests, HA-Realtest ausstehend. **Keine Installationsfreigabe.**

## Beobachtung des echten 0.1.56-HA-Tests

Ein echter, **ausschließlich im privaten Archiv** `TheDaimos/Project-Log-And-Export` abgelegter DRA-V2-Quellvorschau-Export wurde ausgewertet. Er bestätigte `status=failed`, `stage=tree`, `reason=tree_invalid` und `installation_enabled=false`; frühere Phasen (Repository / Commit / Manifest) wurden zuvor durchlaufen.

Das 0.1.56-Diagnoseschema unterscheidet bei `tree_invalid` noch **nicht**, ob der Fehler bei GitHub-HTTP, Übertragungsvalidierung, JSON-Baumantwort, unsicherem Pfad/Dateityp, fehlendem Quellordner oder Datei-Grenzwerten entstanden ist. **Es wäre deshalb fachlich falsch, aus der einen Kategorie eine konkrete HTTP-Ursache, eine manipulierte Datei oder eine beschädigte HA-Installation abzuleiten.**

Die read-only Prüfung des öffentlichen `TheDaimos/gewitterradar` im Standardzweig hat zu diesem Zeitpunkt einen vollständigen Baum (954 Einträge) und 125 Dateien im Manifest-Quellverzeichnis (20.078.990 Byte) ohne erkennbaren Verstoß gegen die bestehenden V2-Baum-/Dateibudgets ergeben. **Das ist kein Beweis, dass bei der HA-Anfrage exakt derselbe Commit/Quellstand oder dieselben GitHub-Zugriffsbedingungen verwendet wurden.** Der echte Diagnoseexport wird ausdrücklich **nicht** in dieses öffentliche Repository kopiert.

## Änderung in 0.1.57

Die reine GitHub-Leseprüfung bleibt unverändert streng, aber ihre internen **festen Fehlercodes** unterscheiden HTTP 401/403/404/429 sowie andere HTTP-Fehler, ohne Antwortinhalte oder Daten auszugeben. HTTP 403 kann beispielsweise Berechtigungsschutz **oder** eine GitHub-Anfragebegrenzung bedeuten; die Oberfläche behauptet deshalb keines von beiden als bewiesen.

Bei der Stufe `tree` wird ausschließlich aus **exakt erlaubten, eigenen Fehlermeldungen** eine von mehreren fest definierten Kategorien gewählt:

- `tree_remote_authentication`, `tree_remote_forbidden`, `tree_remote_not_found`, `tree_remote_rate_limited`, `tree_remote_http` – unterscheidbare GitHub-HTTP-Familien.
- `tree_transport_invalid`, `tree_response_too_large`, `tree_json_invalid` – Antwort/Transportprüfung.
- `tree_incomplete`, `tree_entry_limit` – unvollständiger bzw. übergroßer Git-Dateibaum.
- `tree_path_invalid`, `tree_entry_invalid`, `tree_file_invalid` – unsichere Struktur/Pfade/Dateiidentitäten.
- `tree_source_empty`, `tree_budget_exceeded` – leere Installationsquelle / echtes Überschreiten des wirksamen V2-Budgets.
- `tree_invalid` bleibt als **konservativer unbekannter Fehler**. Neue, unvorhergesehene Ausnahme-Texte werden **niemals** unbereinigt in UI, Download, Zwischenablage oder Git-Export übernommen.

Die vorhandenen Diagnoseattribute (Phasenkette, Laufzeit, gesamte HA-Prozess-CPU-Zeit, verfügbare Kerne, eingestellte und tatsächlich aktive Parallelität) und die bis zu acht flüchtig aufbewahrten Ergebnisse bleiben erhalten. Alle neuen Fehlercodes sind explizit Teil der serverseitigen Positivliste. **Keine neuen GitHub-Schreibfunktionen, kein ungeprüfter Dateizugriff und keine Freigabe von Installationen.**

## Prüfumfang

- `tests/test_v2_source_remote.py`: simulierte GitHub-HTTP-Antworten 401, 403, 404, 429 und 500 ausgerechnet beim Abruf des Git-Dateibaums; Rückgabe nur fester Fehlercodes, keine Rohantwort.
- `tests/test_v2_source_diagnostics.py`: Klassifizierung und Positivliste; fremde/unbekannte Fehlermeldungen führen zu `tree_invalid`, nicht zur Protokollierung von Rohdaten.
- Unverändert: strikte Git-SHA-Pin-Bindung, vollständige Git-Baumprüfung, aktive V2-Grenzen 1.000 Dateien/32 MiB, isolierter V1/V2-Betrieb und separate Backupsperre.

## Nächster und einziger erforderlicher HA-Realtest

Nachdem die vollständige CI für **0.1.57** grün ist, installiert der Betreiber über den **bewährten DRA-V1-Aktualisierungsweg** gezielt 0.1.57 in HA DEV. Anschließend genau eine neue **Gewitterradar – Vorschau berechnen** und über die goldene **Logs**-Schaltfläche **Export nach Git** ausschließlich nach `TheDaimos/Project-Log-And-Export` senden. Wenn die Vorschau unverändert scheitert, kann die neue Kategorie den nächsten Fehlerort bestimmen, ohne Sicherheitswerte zu lockern.

**Verboten:** Eigenständige HA-Installation, automatischer HA-Neustart, Änderungen an DRA V1 DEV/PUB, V2 PUB, V2-main, WeatherRouter oder privatem Exportarchiv sowie das Zusammenführen des Entwurfs-PR #2.

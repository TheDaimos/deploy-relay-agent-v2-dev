# DRA V2 DEV 0.1.60 – begrenzte GitHub-Lese-Wiederholung

**Datum:** 11.10.2026  
**Arbeitszweig:** `feature/v2-10-inventory-operation-contract`  
**Status:** GitHub-CI der Implementierung und Negativtests gesondert verifizieren. HA-Realabnahme offen. **Keine Installationsfreigabe.**

## Nachvollziehbarer Anlass

Der im ausschließlich privaten Zentralarchiv `TheDaimos/Project-Log-And-Export` abgelegte echte 0.1.59-Export hat die neue Zuordnung zu einem registrierten Projekt bestätigt: vollständiger Repositoryname **nur im privaten Archiv**, projektbezogene pseudonyme Kennung und individuelle Prüfkennung in den normalen Logs. Die aktuelle Quellprüfung schlug nach erfolgreichem Repository-, Commit- und Manifest-Schritt **beim Abruf des Git-Dateibaums** mit `tree_transport_invalid` fehl. Das bedeutet: Die GitHub-Antwort wurde durch den Leseclient nicht erfolgreich verifiziert. Die konkrete unterliegende Ausnahme (Verbindungsabbruch, Payload-/TLS-Transport, JSON-Kodierung usw.) war vom alten Code nicht unterscheidbar; deshalb ist eine Behauptung, die eigentliche Ursache sei bereits sicher identifiziert, unzulässig.

Unabhängige GitHub-Abfrage des Standardzweigs von `TheDaimos/gewitterradar`: Der Dateibaum war vollständig (`truncated=false`), enthielt zum Prüfzeitpunkt 954 Einträge und hatte in der JSON-Abfrage etwa 252 KB. Die im DRA gesetzten Größenobergrenzen von 3.000 Einträgen sowie 4 MiB HTTP-Body sind damit anhand des **öffentlichen** Git-Baums nicht offensichtlich verletzt. Das beweist weder, dass der HA-Client exakt dieselben GitHub-Antwortbytes empfing, noch garantiert es den späteren Zugriff.

GitHub-API-Vertrag: `GET /repos/{owner}/{repo}/git/trees/{tree_sha}?recursive=1` liefert die Einträge unter `tree`; `truncated=true` signalisiert unvollständige Daten. Dokumentation: https://docs.github.com/en/rest/git/trees.

## Änderung

Der vorhandene `_get`-Leseclient in `remote_source.py` bleibt auf `https://api.github.com` beschränkt, verwendet weiterhin `GET` ohne Weiterleitungen, einen SHA-gepinnten Dateibaum, begrenzte Antworten und eine 12-Sekunden-Frist **pro Leseversuch**.

- **Nur bei einer nicht konkret klassifizierten Transportausnahme während der Verbindung oder Antwortübertragung** wird maximal **einmal** dieselbe idempotente GitHub-GET-Anfrage erneut ausgeführt. Der zweite Versuch erfolgt nach kurzer fester Wartezeit von 150 ms. Wiederholt sich der Fehler, bleibt die Antwort ausdrücklich `GitHub response could not be verified` und die Vorschau wird **nicht** freigegeben.
- GitHub HTTP 401/403/404/429, andere Nicht-200-Antworten, eine übergroße HTTP-Antwort sowie andere explizite `PreflightError`-Sicherheitsverstöße lösen **keine** Wiederholung aus.
- Eine tatsächlich erhaltene, aber nicht als gültiges UTF-8-JSON-Objekt lesbare HTTP-Antwort liefert die gesonderte sichere Kategorie `invalid GitHub JSON`; auch diese **wird nicht wiederholt**.
- `CancelledError` wird nicht verschluckt; der bestehende äußere Zeitwächter von 45 Sekunden und alle GitHub-/Dateisystem-Grenzen bleiben bestehen.
- Kein Logging von Ausnahmetexten, Repository-Pfaden, Antwortinhalten, HTTP-Headern, GitHub-Zugangsdaten oder persönlichen Quellmetadaten. Die bestehende Zusatzausgabe eines Repositorynamens ist weiterhin **ausschließlich** für den ausdrücklich angeforderten Export in das private zentrale Archiv vorgesehen.

**Nicht geändert:** Der Quell-/Zielbesitz, HA-Projektdateien, DRA V1, V2-PUB/main, WeatherRouter, `TheDaimos/Project-Log-And-Export`, die gespeicherte Warteschlange oder Draft-PR #2. Installation, Wiederherstellung, echte V2-Sicherung, Sammelinstallation und Neustart bleiben gesperrt.

## Automatische Prüfungen

`tests/test_v2_source_remote.py` umfasst gezielte Lese-Simulationen:

1. Git-Dateibaum: einmaliger Verbindungsabbruch, anschließender erfolgreicher zweiter GET, unveränderte URL und verbotene Redirects;
2. zwei Transportfehler: maximal zwei Versuche, keine falsche Quellfreigabe, keine lokale Veränderung;
3. HTTP 403: Abbruch ohne Wiederholungsversuch;
4. kaputtes JSON: separate sichere Fehlerkategorie ohne Wiederholung.

Bestehende positive und negative Quell-, Ziel-, Diagnose- und Admin-Isolationstests bleiben unverändert.

## Nächster HA-Realtest

Nach erfolgreicher vollständiger CI für DEV 0.1.60 aktualisiert der Projektinhaber ausschließlich manuell über den bestehenden **DRA V1** im HA-DEV-Labor. Danach **eine** Gewitterradar-Quellvorschau, bei Fehlschlag den neuen privaten Diagnoseexport mit vollständiger Repozuordnung. Erfolg der Vorschau benötigt weiterhin eine echte vollständige Quell- und lokale Bestandsprüfung; ein erfolgreicher GitHub-Lese-Wiederholungsversuch selbst ist **keine Installationsfreigabe**. Keine selbstständige HA-Installation, kein automatischer Neustart.

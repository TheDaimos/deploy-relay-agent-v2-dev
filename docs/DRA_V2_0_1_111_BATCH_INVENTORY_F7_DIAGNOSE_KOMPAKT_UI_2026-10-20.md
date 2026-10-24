# DRA V2 0.1.111 DEV – sechsfacher Sammelvorlauf, Quell-Dateibestand und kompakte Fehleranzeige

**Datum:** 20.10.2026  
**Repository/Zweig:** `TheDaimos/deploy-relay-agent-v2-dev` / `feature/v2-10-inventory-operation-contract`  
**HA-Befund:** 0.1.110 DEV, Laufzeit und Oberfläche identisch, sechs Projekte gewählt, Vorbereitung gescheitert, **keine Installation gestartet**.

## 1. Tatsächlich nachgewiesener HA-Ablauf

Der neue Screenshot zeigt fünf verarbeitete Projekte: `gewitterradar` und `weather_router` mit `prepared`, `weather_router_private_extensions`, `test_repo_dra_v2` und `deploy_relay` mit `up_to_date`. Das sechste Projekt **DRA V2 DEV – Nur Testlabor** scheitert in `inventory` mit `source_invalid`. Dies ist ein **Lesefehler der Vorbereitung**, kein fehlgeschlagener Installationsschritt. „5 von 6 Teilaufträgen abgeschlossen“ war in dieser Phase missverständlich; der Status zeigt **fünf geprüfte Quellen**, **nicht fünf ausgeführte Installationen**.

Die vorherige Projektkennungs-Korrektur 0.1.110 hat damit den ursprünglichen DRA-V1-Referenzabbruch überwunden; dies ist kein Beweis, dass alle anderen Programm- und Quellenverträge vollständig korrekt sind.

## 2. Export2Git nachgelesen und strikt getrennt

Im privaten Archiv `TheDaimos/Project-Log-And-Export` wurde der tatsächlich vorhandene Export
`exports/deploy-relay-agent-v2/2026-10/diagnostics/2026-10-20T11-05-09Z__deploy-relay-agent-v2__0.1.110__diagnostics__c31a6d8ed2b9154278c0553a0530bd50.json`
gelesen. Er enthält einen **separaten** Lese-/Quelltest für `TheDaimos/deploy-relay-agent-dev` mit `manifest_target_protected`. Dieser Export enthält **nicht** die sechsfachen Sammelvorbereitungsereignisse und darf **nicht** als Nachweis der Ursache des DRA-V2-`inventory`-Abbruchs interpretiert werden.

## 3. Quell-Dateibestandsgrenze geprüft

Das reale `deploy-relay.json` im DRA-V2-Entwicklungszweig legt `max_files: 51` und `max_uncompressed_bytes: 3145728` fest. Der zum Prüfzeitpunkt ermittelte GitHub-Dateibaum enthält im verwalteten Integrationsverzeichnis **51 Dateien** mit rund **870 KB**. Die Dateigrenze ist ausgeschöpft; allein diese Feststellung beweist **nicht**, dass der aktuelle Fehler `inventory_file_limit` lautet. Das Manifest wurde deshalb nicht auf Verdacht gelockert.

Die Brücke `v1_source_bridge.py` verschluckte zuvor die genaue `SourceInventoryError` und reichte lediglich `verified source inventory unavailable` weiter. Auch der Batch-Status lieferte nur `source_invalid`. Damit waren Dateigrenze, Größenlimit, unsichere und doppelte Pfade sowie andere Quellenfehler nicht unterscheidbar.

## 4. Änderungen 0.1.111 DEV

- `v1_source_bridge.py`: feste, ausnahmslos nicht geheime Fehlerklassen für `inventory_file_limit`, `inventory_byte_limit`, `inventory_duplicate_paths`, `inventory_directory_cycle`, `inventory_unsafe_path` und `inventory_read_unavailable`. Unbekannte Fehler und Pfadangaben bleiben verborgen.
- `batch_installation.py`: zulässige Inventarfehler werden im lesbaren HA-Status als `error_detail` geführt. Die Stufe bleibt `inventory`; fehlgeschlagene Vorbereitung startet keine Installation.
- `websocket_api.py`: stellt sicher, dass die bereits klassifizierte Fehlerklasse nicht im letzten Fehlerhandler durch einen pauschalen Wert überschrieben wird.
- `frontend/lab.js`: Der große Sammelauftrags-Status verwendet nun eine kurze Zusammenfassung und eine aufklappbare, mehrspaltige Projektliste. Die ausführliche Fehlerdiagnose bleibt im Installationsbereich; die zusätzlichen festen Inventarfehler werden lesbar übersetzt. Damit wird der obere Bereich bei sechs Projekten erheblich kürzer.
- `manifest.json`, `const.py`, `frontend/lab.js`: Versionsgleichheit `0.1.111`. Die automatisierten Frontend-Testdaten sind entsprechend synchronisiert.
- `tests/test_v2_batch_installation.py`: zusätzliche Positiv-/Negativprüfung der ausschließlich erlaubten Inventar-Fehlerklassen und Unterdrückung beliebiger privater Pfade.

**GitHub Actions:** Lauf `39412848642`, **SUCCESS** auf Programmcommit `88a2a0eb613bd8d810ff968914aee8b30cf3e199`. Der vorangehende Lauf `39412805384` auf dem neuen Testcommit war ebenfalls erfolgreich. Die GitHub-CI ist keine HA-Realabnahme.

## 5. Freigabegrenzen und nächster sicherer HA-Test

Der **ursächliche** Inventarfehler ist noch **nicht** eindeutig bestimmt. Insbesondere wurde eine Erhöhung von `max_files` nicht als unbewiesene vermeintliche Reparatur vorgenommen. Der nächste Schritt ist ein bewusst über DRA V1 installiertes 0.1.111-DEV-Testsystem auf HA DEV. Dort:

1. Python- und Frontend-Version 0.1.111 überprüfen.
2. Sechs Projekte **nur vorbereiten**. Keine Freigabe für `batch/start`.
3. Bei erneutem Abbruch die neue kompakte Detailklasse fotografieren. Falls `inventory_file_limit`: das 51-Dateien-Budget samt berechtigter Quellmenge prüfen und nur danach gezielt korrigieren. Falls `inventory_read_unavailable`: separat GitHub-Leseweg, konkrete feste Commitquelle und Zugriff untersuchen.
4. Falls alle sechs Quellen vorbereitbar sind: die vollständige **installierte Version / neue Version / 40-stelliger Commit / Ref / Änderungen**-Tabelle kontrollieren. Für WeatherRouter ist `deploy/dev` einzuhalten, sofern nicht ausdrücklich manuell abweichend gewählt.
5. Die reale Sammelinstallation, DRA-Selbstupdates, Gerätewechsel und den gemeinsamen HA-Neustart **erst nach getrennter bestätigter Realfreigabe** prüfen.

Keine Änderungen an DRA V1, Gewitterradar, WeatherRouter oder dem Archiv. Keine bereits ausgeführten HA-Installationen behaupten; V1-Sicherung/Journal/Rückfall und explizite Freigaben bleiben unverändert.

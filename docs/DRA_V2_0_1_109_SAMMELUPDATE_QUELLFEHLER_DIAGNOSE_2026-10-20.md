# DRA V2 0.1.109 DEV – Quellfehler im Sammelupdate nachvollziehbar anzeigen

**Datum:** 20.10.2026  
**Entwicklungszweig:** `feature/v2-10-inventory-operation-contract`  
**Ausgangslage:** Auf Home Assistant läuft laut Screenshot V0.1.108 DEV mit passender Python-/Oberflächenversion.

## Beobachtung

DRA V2 wählte sechs aktive Projekte für den Sammellauf aus und brach in Schritt 1/4 mit „Quell- oder Manifestprüfung fehlgeschlagen“ ab. Der Bildschirm zeigte weder das auslösende Projekt noch den GitHub-Fehler. Ein für die Analyse nutzbarer Logexport stand dem Anwender nicht zur Verfügung.

Ein zweiter Screenshot zeigt den funktionierenden DRA-V1-Sammelupdate-Dialog: fünf Projekte werden angezeigt, zwei haben Änderungen. Das isolierte Test-Repo war dort nicht Teil der Auswahl. Aus den beiden Bildern folgt **nicht**, welches Projekt DRA V2 konkret blockiert.

Alle sechs angegebenen Repository-Manifeste wurden in GitHub lesend geprüft: Sie sind grundsätzlich vorhanden und deklarieren gültige V1-Projektidentitäten. Daraus ergibt sich **keine** Freigabe für die konkrete Installation auf Home Assistant. Private Repository-Zugriffsrechte der HA-Instanz sind von GitHub außerhalb HA nicht beweisbar.

## Nachgewiesener Programmfehler

Die V2-WebSocket-Strecke fragte zunächst sämtliche GitHub-Zweige und empfohlenen Commits ab, bevor `BatchDeployment.prepare()` einen serverseitigen Status mit Projektkennung erzeugte. Bei einer `PreflightError` in dieser ersten Schleife wurde der Fehler zu `batch_source_invalid` verallgemeinert. Die Oberfläche zeigte deshalb weder fehlendes Projekt noch Prüfphase. Das erschwerte auch die Unterscheidung zwischen einem ungültigen Ref und einem fehlenden Token.

## Implementierung 0.1.109

- HA legt bereits beim Beginn der GitHub-Referenzprüfung eine lesbare Auftragsdiagnose an: `inspecting_sources`, `project_key`, `check_stage:source_reference`.
- Wird die nachfolgende GitHub-Abfrage abgelehnt, ist `failed` mit auslösendem Projekt, Prüfschritt und bereinigter Fehlerklasse sichtbar. Kein zusätzlicher Logexport erforderlich.
- Die Quellenbrücke bewahrt getrennte, nicht geheime Prüfphasen: `manifest`, `inventory`, `local_comparison`. Fehler einer Versionsprüfung bleiben `version_detection`.
- Öffentliche, fest definierte GitHub-Fehlerkategorien wie 401, 403, 404 und 429 sowie bekannte Empfehlungs-/Formatfehler dürfen angezeigt werden. Unbekannte Fehlertexte, Tokens, Antwortkörper und Dateipfade werden **nicht** ausgegeben.
- Die bestehende Bindung von Prüfübersicht, ausgewählten Refs und festgehaltenen Commits bleibt unverändert.
- Der Status ist während der Vorbereitung auf anderen Geräten lesbar. Eine bestehende noch gültige Sammelfreigabe darf nicht stillschweigend durch eine neue GitHub-Abfrage ersetzt werden.
- Negativtests prüfen die Projektzuordnung, erlaubte Fehlerklassen, das Fehlen fremder Fehlermeldungen oder Tokeninhalte und das Verhindern konkurrierender Freigaben.

## Grenzen und nächste HA-Abnahme

**Unbekannt bleibt, welches der sechs Projekte auf der konkret installierten HA-Instanz versagt hat.** Eine erfolgreiche GitHub-CI kann die dort hinterlegten GitHub-Tokens, Rate-Limits, Netzverbindung und Dateibestände nicht ersetzen.

1. Die neue Version kontrolliert über DRA V1 installieren und Laufzeit-/Oberflächenversion vergleichen.
2. Sammelupdate mit den bisherigen sechs Projekten **nur vorbereiten**, keine Installation bestätigen.
3. Bei erneutem Fehler direkt im Sammelupdate unter „Projekt“, „Prüfschritt“ und „Weitere Eingrenzung“ nachsehen. Screenshot genügt, ein Git-Export wird nicht vorausgesetzt.
4. Nur das konkret gemeldete Problem beheben (z. B. Repository-Zugriff, fehlerhafte Referenz, Manifest oder lokaler Vergleich), danach Quellvorbereitung neu ausführen.
5. Vor einer echten Installation die zusätzliche verbindliche Versions-/Commit-Tabelle überprüfen und erst dann freigeben.

**Installationsfreigabe, Selbstupdate von DRA V2 und HA-Realabnahme bleiben bis zu echten Tests ausstehend.** DRA V1 sowie die GR- und WR-Repositories wurden nicht geändert.

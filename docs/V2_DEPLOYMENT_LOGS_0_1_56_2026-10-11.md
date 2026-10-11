# DRA V2 DEV 0.1.56 – Deployment-Protokolle und kompakte Exportleiste

**Datum:** 11.10.2026  
**Zweig:** `feature/v2-10-inventory-operation-contract`  
**Status:** Funktion und isolierte Tests implementiert, CI-/HA-Abnahme getrennt nachweisen. Schreibfunktionen bleiben gesperrt.

## Oberfläche – Entscheidung des Projektinhabers

In der Kopfzeile des vorhandenen vierstufigen Deployment-Bereichs sitzt rechts von **Deployment** eine kleine goldumrandete, abgerundete Schaltfläche **Logs** – in Farbe, Größe und Materialanmutung nach dem bestehenden Hinweis **Prüfung ausstehend**. Die Hauptkarte wächst erst bei geöffneten Logs; die zentrale Deployment-Schaltfläche, die V1-inspirierte Ladeleiste und alle vier Stufenkacheln behalten die bisherige Reihenfolge.

Nach dem Tippen erscheinen direkt unter der Kopfzeile drei Schaltflächen:
1. **Export nach Git** – nur ein ausdrücklich gespeichertes, vor jedem Upload als privat bestätigtes Repository; vorhandener Zentralarchivmechanismus und seine Wiederholwarteschlange, keine Veröffentlichung im Projektquellrepository.
2. **JSON herunterladen** – unabhängig von Git-Zugang, nur bereinigte Daten.
3. **Zwischenablage** – dasselbe serverseitig validierte JSON wie beim Download, kein eigenes unbereinigtes Browserprotokoll.

Der Bereich zeigt die **bis zu acht letzten Prüfungen** aus der laufenden V2-DEV-HA-Sitzung. Alte Daten werden beim HA-Neustart bewusst nicht als dauerhaftes Ereignisprotokoll vorgetäuscht. Eine fehlgeschlagene Vorschau bleibt exportierbar; bisher war der Export ausschließlich erfolgreich abgeschlossenen synthetischen Messungen vorbehalten.

## Backend- und Fehlerdaten

Die admin-geschützte Quellprüfung führt eine begrenzte Ablaufspur mit Zeitpunkten relativ zum Start, zuletzt erreichtem Schritt, Zeitdauer, fest definierter Fehlerkategorie und eigener Diagnosekennung:

- Auftragsannahme, Repositoryzugriff, Commitbestimmung, Manifest und deklarierte Ressourcengrenzen;
- Git-Dateibaum, lokale HA-Dateibestandsprüfung, Dateivergleich, Zielbesitzprüfung;
- Erfolg/Fehler, gemessene Prüfdauer und gesamte CPU-Zeit des gemeinsamen Home-Assistant-Prozesses;
- beim Prüfungsstart beobachtete verfügbare CPU-Kerne;
- konfigurierte maximale Zahl gleichzeitiger Leseaufträge (1–4), konfigurierte Arbeitsprozesse (1–12), gespeicherte Betriebsart (sequenziell/gesteuert);
- **wirksame Runtime-Schranken**: höchstens ein aktiver Leseauftrag, null Schreibaufträge; Arbeitsprozessbudget derzeit nicht wirksam verdrahtet.

Die konfigurierte Zahl von Prozessen darf niemals als tatsächlich gestartete Zahl ausgegeben werden. Die gemessene Prozess-CPU-Zeit bezieht sich auf **alle Komponenten im HA-Prozess**, nicht isoliert auf DRA V2; eine direkte komponentenspezifische CPU-Zuordnung ist dadurch nicht belegt. Keine Polling-Dauerschleife, nur gezielte Erfassung bei einer tatsächlich angeforderten Quellprüfung.

Die abgespeicherten Daten sind eine strikte Positivliste: **keine Repositorynamen oder privaten Git-URLs, keine Branch-/Commit-Quelle, Dateinamen, lokale Pfade, Geheimnisse, HTTP-Header, Antworten, Tracebacks, Rohfehlermeldungen, Rohprotokolle oder Umgebungsvariablen**. Exporte bleiben strikt schema- und größenvalidiert. Das geschützte Zielverzeichnis und das V1-Konfigurations-/Sicherungsverzeichnis werden nicht verändert.

## Schnittstellen / Sicherheit

Alle drei neuen WebSocket-Kommandos ausschließlich mit `require_admin`, eigene präfixgebundene V2-Domain:
- `deploy_relay_v2_dev/deployment/logs`
- `deploy_relay_v2_dev/deployment/logs/download`
- `deploy_relay_v2_dev/deployment/logs/export`

Sie enthalten **keine** V2-Installations-, Restore- oder Neustartaktion. Git- und JSON-Ausgabe verwenden denselben strengen zentralen Archivumschlag `daimos-project-log-export-v1` mit Test-ID `V2-SOURCE-PREVIEW` und dem neuen internen Diagnose-Snapshot `dra-v2-dev-git-source-diagnostic.v1`. Token und Ziel werden niemals aus einem Browserprotokoll übernommen; der Zentralexport muss separat vom HA-Administrator bereits eingerichtet worden sein. Bei Git-Fehlern kein automatisches öffentliches Ersatzziel.

Ressourcenverbrauch: höchstens acht berichtigte Ereignisberichte im Arbeitsspeicher, keine eigene persistente Logdatei, kein permanentes Mitprotokollieren von HA-Ereignissen, keine neuen GitHub-Actions-Artefakte.

## Test- und Ausbringungsgrenzen

Automatische Prüfungen decken strenge Positivlisten, Quellenphasen und Fehlerkategorien, CPU-Limits, Mutationsschutz, unabhängige Snapshots, Geheimnisabweisung, den bestehenden privaten Archivumschlag samt Wiederholwarteschlangen-Validierung und die drei administrativen Schnittstellen ab. Bestehende Isolationsprüfungen zählen nun 31 WebSocket-Handler; der Manifest-Dateiplan wurde auf 25 Moduldateien angepasst.

**HA-Realtest noch offen:** Nur nach ausdrücklicher Aktualisierung durch den Projektinhaber über DRA V1 die mobile Goldpille öffnen, Gewitterradar einmal schreibgeschützt prüfen, im Log den Fehlschritt kontrollieren, zunächst JSON downloaden und bei vorhandenem privatem Archiv auf Wunsch nach Git exportieren. Die eigentliche Schreibfreigabe, Installation, echte Sicherung, Wiederherstellung, Sammelupdate-Installation und Neustartsteuerung bleiben gesperrt.

**Repositoryschutz:** DRA V1 DEV/PUB, V2 PUB, V2-main, WeatherRouter, privates Archiv unverändert; neue echte Exporte ausschließlich ins vom Nutzer gewählte private `TheDaimos/Project-Log-And-Export`. PR #2 bleibt Entwurf.

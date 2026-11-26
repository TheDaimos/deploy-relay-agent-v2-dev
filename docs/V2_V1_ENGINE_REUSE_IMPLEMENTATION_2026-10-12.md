# DRA V2 – V1-Installationsengine wiederverwenden: erster realer Implementierungsblock

**Datum:** 12.10.2026  
**Zweig:** `feature/v2-10-inventory-operation-contract`  
**Stand:** Code umgesetzt und als zusammengehöriges Paket CI-geprüft. **Keine HA-Schreibfreigabe, keine zusätzliche V2-DEV-Versionsnummer nur für einen Zwischenstand.** Die in HA installierte Version bleibt 0.1.72; für die neu ergänzten Bausteine ist noch keine HA-Realabnahme erfolgt.

## Die eigentliche Umsetzung

Die **bereits aus öffentlicher DRA-V1-Referenz im V2-Repository vorhandenen** Kernmodule wurden als eigenständiges Python-Paket `custom_components/deploy_relay_v2_dev/v1_engine/` eingebunden. **Keine Änderungen an DRA-V1-DEV/PUB.**

Dabei sind die bewährten V1-Dateien `deployment.py`, `github_client.py`, `source_inventory.py`, `manifest.py`, `planner.py`, `preview.py`, `integrity.py`, `lifecycle_policy.py`, `path_policy.py`, `runtime_policy.py`, `version_markers.py`, `repository.py`, `transaction.py` übernommen; ihre eigentlichen Algorithmen bleiben unverändert. Nur in der V2-Kopie von `deployment.py` wurden die **zwei bisherigen fest codierten V1-Speicherpfade** über die eigene Konstante `DEPLOY_DATA_DIR = "deploy_relay_v2_dev"` isoliert, zusammen mit einem minimalen eigenen V1-Kompatibilitäts-`const.py`. V1-Sicherungen, V1-Transaktionsordner und V1-Laufzeit bleiben unangetastet.

**V1-Funktionen sind jetzt im V2-Code vorhanden:** gültige Deployment-Manifeste, fixierte Git-Quellen, SHA-256-Quellinventar, lokale Vorschau, Staging, unabhängige Transaktionssicherung, tatsächliches Schreiben, Nachprüfung, automatischer Rückfall und der konkrete Recovery-Zustand. **Die laufende V2-UI darf die Engine noch nicht aufrufen.**

Die zwei echten Verbindungsmodule:

- `v1_source_bridge.py`: bereitet **rein lesend** anhand eines verifizierten festen Git-Commits und registrierter Projektidentität V1-Manifest, V1-Quellinventar und die tatsächliche V1-Dateivorschau vor. Keine Browserdaten können ohne spätere serverseitige Registrierungs-/Adminprüfung als Freigabe dienen.
- `server_deployment_jobs.py`: separater, HA-Task-fähiger Ausführungsadapter. Er übernimmt V1-kompatible interne Objekte, bucht genau einen schreibenden serverseitigen Auftrag, führt die echte V1-Engine aus und unterscheidet `success`, `failed`, `recovery_required` und `interrupted`. Idempotente Auftragskennung und Wiederabfrage über den bestehenden V2-Operationsvertrag. **Noch nicht an HA-`__init__.py`, WebSocket oder Schaltflächen angeschlossen.** Vor späterer Freigabe ist auch eine belastbare Wiederanlaufbehandlung bei unterbrochener laufender Mutation nötig.

## Was wirklich automatisch geprüft wurde

- **Tatsächliche V1-Engine auf künstlichem Dateisystem ausgeführt:** ein verändertes und ein neues Modul werden nach V1-Algorithmus installiert, Prüfsummen/Dateizustände geprüft und das Transaktionsjournal erstellt. Erfolg bestätigt.
- **Gezielte Störung nach Dateischreiben:** der Originalinhalt wird von der unveränderten V1-Rückfallfunktion wiederhergestellt; neu hinzugefügte Datei wird entfernt; Journal meldet `rolled_back`. Bestätigt.
- **Fehler vor Schreibbeginn:** keine Zielmutation; V1-Datenbereich unverändert. Bestätigt.
- **Symbolische Verknüpfungen:** vor Dateizugriff gesperrt. Bestätigt.
- **Serverseitige Ausführung:** Auftragsstatus während laufender Arbeit abfragbar, dieselbe Anfrage erzeugt keine zweite Installation, parallele zweite Schreibanforderung wird verweigert, Fehler-/Recovery-Familien werden ohne Fehlermeldungsinhalte ausgegeben. Bestätigt.
- **Quellübergabe:** Manifest ausschließlich von festem Git-Commit, Ref-/Projekt-/Commit-Prüfung, echte read-only V1-Differenzvorschau, falsche Referenz und Identität vor Verarbeitung gesperrt. Bestätigt.
- Isoliertes DRA-V2-Installationsmanifest: Dateigrenze gezielt von 28 auf 45 erhöht (15 V1-Engine-Dateien + zwei Verbindungsmodule), 3-MiB-Bytebudget unverändert, DRA-V1-Verzeichnis weiterhin nicht im V2-Installationsziel.

**Gebündelte CI:** [GitHub Actions 38180708687 – SUCCESS](https://github.com/TheDaimos/deploy-relay-agent-v2-dev/actions/runs/38180708687) auf Code-Checkpoint `c8c855c30da98491a45cc751a1845af4cef708bf`. Bestehende DRA-V2-Oberflächen-/G2-/Isolationstests weiterhin erfolgreich. Kein Git-Artefakt, keine HA-Mutation.

## Der nächste konzentrierte Entwicklungsblock

Die übernommenen Engine-Bausteine und die V2-Hintergrundaufträge **miteinander produktiv anbinden**, inklusive Admin-/Einmalbestätigung, echter Git-Quellbindung und sicherer Transaktions-/Wiederanlaufbehandlung. Danach **geeignete echte Hash-/CPU-Arbeit begrenzt parallelisieren**, ohne die bewährte V1-Dateischreiblogik unkontrolliert zu vervielfachen. Die vorhandene zentrale V2-Deployment-Taste bleibt erhalten.

**Erst nach diesem zusammenhängenden funktionsfähigen Block einen einzigen gebündelten HA-DEV-Test anfordern** (Vorschau, Installation, Verbindungsabbruch, Sicherung und kontrollierter Fehlerfall). Kein Neustart oder Versionssprung für die jetzige reine Entwicklungszwischenstufe.

**C.K. – Eine Idee weiter gedacht.**

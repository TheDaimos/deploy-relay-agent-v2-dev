# DRA V2 0.1.124 DEV – normale Eigenaktualisierung und stabile Quellenauswahl

Datum: 26.11.2026
Branch: `feature/v2-10-inventory-operation-contract`
Status: Quellcode committed; HA-Realabnahme ausstehend; keine FINAL-Veröffentlichung.

## Anforderung des Betreibers

DRA V2 soll bei einem normalen **Einzelupdate** auch DRA V2 selbst aktualisieren können. Der gesonderte gelb umrandete Eigenaktualisierungs-Hinweisblock mit zusätzlichen Schaltflächen soll entfallen. V1-Installationsengine, Bestätigung, Sicherung, Prüfung, Rollback und serverseitiger Auftrag bleiben unverändert.

Zusätzlich: Native Dropdowns für Git-Zweige/Tags wurden durch wiederholte UI-Komplettrenders geschlossen.

## Umsetzung

- `frontend/lab.js`: Die normale Einzelupdate-Schaltfläche führt nach der schreibgeschützten V2-Vorschau in Schritt 2 bei Auswahl von DRA V2 direkt zu `_openSingleSelfUpdate(mainProject)`. Hierbei wird nur **dieses** Projekt im vorhandenen serverseitigen Batch-Vertrag selektiert, der dieselben Commit-, Review-, Backup-, Rollback- und Selbstupdate-zuletzt-Sicherheitsregeln nutzt. **Kein direkter Eigen-Schreibpfad, keine Freigabeumgehung.**
- Der alte Sonderhinweis `DRA V2: Eigenaktualisierung gesondert geschützt` einschließlich separater Schaltflächen und unbenutzter CSS-Regeln wurde aus der Ansicht entfernt.
- Das Haupt-Deployment bleibt für normale Projekte unverändert. DRA V2 verwendet nach Schritt 2 intern die bisherige Ein-Projekt-Batch-Ansicht (noch nicht vollständig vereinheitlichte Beschriftungen).
- Native Quellenauswahl `#dra-main-choice`: Während des Fokus kein destruktives komplettes Shadow-DOM-Render bei Status-Polling; nach `change` wird die Auswahl übernommen und normal neu gerendert.
- Versionsparität: UI, Python und Manifest auf `0.1.124` synchronisiert.

## Tests und Schutz

- Ergänzt: `tests/test_v2_source_choices.py::test_source_dropdown_survives_status_polling`.
- Angepasst: `tests/test_v2_batch_run_selection_contract.py` für den Normal-Button-Selbstupdatepfad; historisch veraltete exakte Versionsassertions in Batch/Post-Install-Tests auf bestehenden `_runtimeCompatible()`-Vertrag umgestellt.
- Öffentliche CI: `v2-version-parity.yml`, `v2-source-budget.yml`, `v2-validate.yml`; tatsächliche Ergebnisse sind pro HEAD zu prüfen, keine Behauptung über HA-Installation.
- Keine Änderung an WebSocket-Endpoints, Sicherheitsgrenzen, DRA V1 oder Produktivrepositories.

## Betreiberabnahme

Nach erfolgreicher CI: DEV-Version DRA V2 0.1.124 installieren (nur auf DEV). Prüfen: (1) Quell-Dropdown bleibt länger als zwei Pollzyklen geöffnet, (2) DRA V2 als Einzelprojekt auswählen und Vorschau berechnen, (3) normale 2/4-Taste beginnt exakt ein gesichertes DRA-V2-Selbstupdate, (4) weitere Freigabe bleibt ausdrücklich erforderlich, (5) 3/4 und 4/4 mit HA-Neustart nach regulärer Bestätigung, (6) kein Sonderhinweis mehr.

Keine eigenständige HA-Installation aus dem Chat; keine PROD-Änderung.

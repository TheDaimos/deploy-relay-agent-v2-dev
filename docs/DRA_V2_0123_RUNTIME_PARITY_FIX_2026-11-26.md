# DRA V2 0.1.123 DEV – MA-020-Einzelupdate: Versionsabweichung der Laufzeit behoben

**Datum:** 26.11.2026  
**Repository:** `TheDaimos/deploy-relay-agent-v2-dev`  
**Entwicklungszweig:** `feature/v2-10-inventory-operation-contract`  
**Geltung:** ausschließlich DRA V2 DEV. Keine Änderungen an DRA V1, V2 `main`, V2 PUB, GewitterRadar oder WeatherRouter.

## Reproduzierter Betreiberbefund

Auf der GewitterRadar-Einzelupdate-Vorschau (Git-Branch `feature/v4.14-monitored-areas`; Git-Quelle 4.14.2, lokal 4.14.1, 13 hinzugefügt, 16 geändert, 0 entfernt) blieb der Installationsschritt bei **„2/4 · Installation vorbereiten“**, ohne die erwartete V1-Sicherheitsfreigabe. Der vollständige Neustart von Home Assistant veränderte dieses Verhalten nicht.

Im DRA-V2-Header stand bereits die Ursache: **Oberfläche 0.1.123 DEV · HA-Laufzeit 0.1.122 DEV**. Die vom Betreiber bereitgestellte redigierte Diagnosedatei meldet den erfolgreich abgeschlossenen read-only Quellvergleich (`status=success`, `sources_verified=true`, `installation_enabled=false`), aber keinen Installationsauftrag.

## Quellcode-Ursache

- `custom_components/deploy_relay_v2_dev/frontend/lab.js`: `DRA_V2_UI_VERSION = "0.1.123"`
- `custom_components/deploy_relay_v2_dev/manifest.json`: `version = "0.1.123"`
- `custom_components/deploy_relay_v2_dev/const.py`: **irrtümlich** `VERSION = "0.1.122"`
- `websocket_api.py` liefert diese `const.VERSION` als Backend-Version aus; `panel.py` nutzt sie für den Skript-Cache-Parameter.
- Die bestehende `_prepareInstallation`-Zulassung fordert ausdrücklich `this._serverVersion === DRA_V2_UI_VERSION` und `_syncController`; bei Versionsabweichung wird die Vorbereitung nicht gestartet. Auch die Schaltfläche ist dann deaktiviert.

**Das ist ein beabsichtigter Sicherheitsvertrag, kein Anlass zum Aufweichen.** Die sichtbare Fortschrittsleiste stellt in diesem Zustand keinen aktiven Daten-/Installationsfortschritt dar.

## Minimaler Fix – keine Ablaufänderung

1. `const.py`: einzige Produktcodeänderung `0.1.122` → `0.1.123` (Commit `96e2ef73178a24ee0decc9882c7b12b24e7e6f06`).
2. `tests/test_v2_frontend_backend_version_parity.py`: automatisierter Gleichheitstest für manifest-/Frontend-/Python-Identität und unveränderte Controller-, Challenge-, Bestätigungs- und Duplicate-Start-Schutzverträge.
3. `.github/workflows/v2-version-parity.yml`: eigenständige öffentliche CI für Test und Python-/JS-Syntax, ohne eine vorhandene Prüfung abzuschalten.

Keine Änderung der Vier-Stufen-Anzeige, Pop-up-/Bestätigungslogik, V1-Engine, Backups, Rollback, Installationsschranken oder des Sammelupdates.

## Automatisierte Nachweise

- **PASS** auf Commit `9d076da4a2796cb7fd2014587f2e28f7c7138434`: [DRA V2 DEV Frontend/HA runtime version parity](https://github.com/TheDaimos/deploy-relay-agent-v2-dev/actions/runs/45781136802) einschließlich 3 Versions-/Freigabe-Vertragstests und Syntaxprüfungen.
- Standardbibliotheks-Testlauf der allgemeinen `v2-validate.yml`: **455 Python-Tests PASS** nach Korrektur des Test-Regex (`74c0cbd6053d34768dab45a36544934456716356`).
- Die breitere bestehende DRA-V2-JavaScript-Suite ist **weiterhin rot** mit mehreren überkommenen Tests (auch vor diesem Fix, beispielsweise bereits auf `fcb0e2669b`); **nicht** als Full-Green erklären, nicht durch Abschalten/Abschwächen kaschieren. Separater Legacy-Testwartungsbedarf; keine belegte Laufzeitregression durch den Einzeiler.

## Verbindlicher nächster HA-DEV-Schritt

**Keine Installation wurde durch diese Änderung ausgeführt.** Auf **DEV VM109** das vollständige DRA-V2-Integrationverzeichnis aus dem Feature-Branch über den vorgesehenen, noch funktionsfähigen V1-Installations-/DRA-Weg aktualisieren, nicht einzelne Dateien per Hand tauschen. Bereitstellung muss `const.py`, `manifest.json` und `frontend/lab.js` **gemeinsam** enthalten. Vor Installation DRA-V1-Vorschau und Rückfallsicherung prüfen; keine PROD-Änderung.

Anschließend Home Assistant vollständig neu starten und DRA V2 mit hartem Frontend-Reload öffnen. Erforderliches Ergebnis: **Oberfläche V0.1.123 DEV · HA-Laufzeit V0.1.123 DEV**, kein Versionswarnhinweis. GewitterRadar-Branch `feature/v4.14-monitored-areas` erneut ausschließlich lesend prüfen. Erst dann sollte die bekannte vorbereitende V1-Engine-Freigabe wieder wie zuvor erscheinen. **Diese tatsächliche UI-/HA-Funktionsabnahme steht noch aus.**

Keine Umgehung des Versionsschutzes, keine automatische Installation; Administratorbestätigung bleibt erforderlich.

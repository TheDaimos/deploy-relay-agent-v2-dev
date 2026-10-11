# DRA V2 DEV 0.1.72 – Klar erkennbare Versionsnummer in der Kopfzeile

**Datum:** 11.10.2026  
**Zweig:** `feature/v2-10-inventory-operation-contract`  
**Anlass:** Der Betreiber meldete anhand der realen HA-Oberfläche, dass die bisherige Aufschrift `V2 DEV` keine tatsächliche Versionsnummer enthält und damit Installationsstände schwer zuzuordnen sind.

## Umgesetzte Anzeige

Die ursprüngliche reine Bezeichnung `V2 DEV` im Kopfbereich wird durch eine kompakte, kontrastreiche, mobilfreundliche Versionsfläche direkt neben dem weiterhin sichtbaren Betriebsstatus **GESPERRT** ersetzt:

- **Oberfläche: V0.1.72 DEV**: vom **tatsächlich geladenen** JavaScript-Modul identifiziert; auch bei noch nicht erfolgter HA-Rückmeldung erkennbar, damit ein veralteter Browsercache nicht als neue Oberfläche durchgeht.
- **HA-Laufzeit: V0.1.72 DEV**: ausschließlich aus der vorhandenen admin-geschützten WebSocket-Antwort `deploy_relay_v2_dev/test/state.version` von `const.VERSION` übernommen. Keine Annahme aus Git-Branch, Manifestdatei in fremder Quelle oder Browsercache.
- **Noch nicht ermittelt**: vor der ersten erfolgreich beantworteten Statusanfrage oder nach Kommunikationsfehler. Keine veraltete Laufzeitversion behaupten.
- **Abweichung**: Bei unterschiedlichen gültigen Versionsnummern werden **beide** sichtbar gezeigt; dezent goldfarbener Warnzustand. Beispiel: **Oberfläche V0.1.72 DEV · Abweichung · HA-Laufzeit V0.1.71 DEV**. Das hilft, nach einem DRA-V1-Update einen noch alten Browserstand oder einen noch nicht geladenen Pythonstand festzustellen, ohne eine Ursache vorwegzunehmen.
- Das Versionsfeld ist in Haupt- **und** Einstellungsansicht Bestandteil derselben Kopfzeile. Lesbarkeit auf Mobilgeräten und barrierefreie Versionsbeschreibung wurden ergänzt.

**Wichtig:** Dies sind **Installations-/Laufzeitversionen**, keine Versionsangabe des ausgewählten Git-Projekts. Der Commit/Ref einer zu aktualisierenden Anwendung wird weiterhin gesondert im Bereich `Quelle & Version` ausgewiesen.

## Sicherheits- und Architekturgrenze

Nur vorhandene schreibgeschützte Versionsantwort genutzt; **kein** zusätzlicher WebSocket-Aufruf, keine neue Adminschnittstelle, kein Dateischreibzugriff für V2, keine V1-Zugriffsänderung. `G2_TEST_PYTHON_VERSION` ist nun an die eine tatsächliche JavaScript-Version gebunden, damit kein inkonsistenter zweiter Versionswert eingeführt wird.

Version `0.1.72` ist in V2-DEV-`const.py`, `manifest.json` und tatsächlich ausgelieferter `frontend/lab.js` aufeinander abgestimmt.

## Isolierte Tests und CI

Die ergänzten Node-Oberflächentests prüfen:

1. Noch keine Backend-Rückmeldung: keine erfundene HA-Versionsangabe.
2. Echt über `test/state` übergebene identische Version: beide Versionsstände sichtbar, keine Abweichungsmeldung.
3. Unterschiedlicher Pythonstand: deutlich sichtbare Versionsabweichung ohne Sicherheitsfreigabe.
4. Fehlende Erreichbarkeit nach zuvor gültigem Status: alte HA-Versionsbehauptung wird wieder entfernt.
5. Bereits vorhandene G2-Tests für Inkompatibilität und gesperrte Schreibschritte bleiben erhalten.

**GitHub-CI auf Codecheckpoint `9e5d73c5d29adf64f0295adc99ed8abd0d1c4149`: [38175085562 – SUCCESS](https://github.com/TheDaimos/deploy-relay-agent-v2-dev/actions/runs/38175085562).**

## HA-Nachtest (noch offen)

Nur wenn der Betreiber den neuen Versionsbereich real ansehen möchte: V2 DEV **0.1.72** wird regulär ausschließlich durch DRA V1 aus dem vorhandenen Featurezweig aktualisiert; anschließend HA-Neustart durch den Betreiber. In DRA V2 soll der Kopfbereich zwei eindeutige Versionen zeigen. Ein besonderer G3-Schreib-/Installations-Realtest ist **nicht** erforderlich und nicht freigegeben.

**Unverändert:** DRA V1 DEV/PUB, V2 DEV `main`, V2 PUB, WeatherRouter, das private Git-Exportarchiv. PR #2 bleibt offen, ohne Merge.

**C.K. – Eine Idee weiter gedacht.**

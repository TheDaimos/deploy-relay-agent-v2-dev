# DRA V2 DEV 0.1.83 – gebündelte Tests und Oberflächenabnahme

**Status:** Code implementiert, CI erfolgreich; Home-Assistant-Realabnahme steht aus.
**Freigegebener Zweig:** `feature/v2-10-inventory-operation-contract`
**Letzter Code-Checkpoint:** `b64091a6af1c299d110c8e8561854a85daae91fa`
**CI:** [38387313328](https://github.com/TheDaimos/deploy-relay-agent-v2-dev/actions/runs/38387313328) – SUCCESS.

## Enthaltene Änderungen

- [x] Tests-Rubrik unterhalb der Deployment-Ansicht aufklappbar.
- [x] G2-Verbindungstest in die Rubrik Tests verschoben, der bisherige serverseitige Lese-Prüfauftrag bleibt erhalten.
- [x] Deployment-Ansicht um den langen G2-Text und die G2-Schaltfläche bereinigt; kompakter Versionsstatus.
- [x] Schritt 3 bereits beim Übergeben eines bestätigten Installationsauftrags anzeigen; keine künstliche Verlängerung des serverseitigen Deployments.
- [x] Test 2: einen einzigen Zähler in `TheDaimos/Test-Repo-DRA-V2`, `main`, `payload/teststatus.json` um genau 1 erhöhen.
- [x] Test 2: ausdrückliches Häkchen vor dem Aufruf, nur HA-Administrator, eigener GitHub-Projekt-Token mit tatsächlichen Schreibrechten, kein Browser-Token und keine Speicherung eines zusätzlichen Schlüssels.
- [x] Strikte Prüfung aller JSON-Felder, fester GitHub-API-Pfad, SHA-basierte Konflikterkennung, sichere begrenzte Antwortverarbeitung. Kein generischer GitHub-Schreibdienst.
- [x] Sammelupdate-Zahnrad erhält identische metallische Schaltflächenklasse und Maße wie die Einzelprojekte.
- [x] Bestehende Installationsengine, V1, andere Projekte, V2 main und Draft-PR #2 unverändert.
- [x] Automatische Tests und CI vollständig grün.

## Nächste gebündelte Realabnahme

1. V2 0.1.83 per V1 installieren und Home Assistant einmal neu starten.
2. Versionsgleichheit und neue Rubrik Tests prüfen, G2 dort auffindbar; G2 nicht mehr in Deployment.
3. Sammelupdate-Einstellungen optisch neben einer gewöhnlichen Projektzeile vergleichen.
4. Test 2 ausdrücklich bestätigen und einmal `teststand` erhöhen. Falls kein geeigneter GitHub-Projekt-Token mit Schreibrecht eingerichtet ist, **nicht** andere Repositories oder Tokens als Ersatz wählen.
5. Anhand des bestätigten Git-Commits eine einzige schreibgeschützte Vorschau und anschließend genau eine echte isolierte Testinstallation ausführen. Erwartet: 1 geändert, 1 unverändert; sichtbarer Übergang durch Schritt 3 auf 4.
6. Audit prüfen. Keine produktiven Projekte installieren.

**Wichtig:** Automatische CI-Tests sind keine HA-Abnahme. Keine erneute Version allein für einzelne UI-Tests erzeugen.

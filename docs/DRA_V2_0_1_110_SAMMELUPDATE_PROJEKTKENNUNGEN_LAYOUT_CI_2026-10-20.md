# DRA V2 0.1.110 DEV – gebündelter Sammelupdate- und Layout-Testkandidat

**Datum:** 20.10.2026  
**Repository:** TheDaimos/deploy-relay-agent-v2-dev  
**Zweig:** `feature/v2-10-inventory-operation-contract`  
**HA-Ausgangslage:** Nachgewiesen ist lediglich die installierte 0.1.109 DEV. **0.1.110 ist nicht auf HA installiert und nicht realabgenommen.**

## 1. Nachgewiesener Fehler der sechsfachen Sammelvorbereitung

Der über die neue 0.1.109-Oberflächendiagnose gelieferte HA-Befund zeigt `Deploy Relay`, Phase `source_reference`, Fehlerklasse `source_invalid`, Detail `invalid deployment recommendation`. Es wurden **keine Teilinstallationen** gestartet. Grund: Der V2-Katalog generierte `deploy_relay_agent_dev` aus dem Repositorynamen, während Manifest und Kanalempfehlung des echten V1-Repositories `deploy_relay` ausweisen.

Es wurden außerdem die realen GitHub-Manifeste für WeatherRouter und private Erweiterungen geprüft. Auch hier wich die generierte Kennung vom verbindlichen Manifest ab: `weather_router_dev` statt `weather_router` und `weather_router_extensions_dev` statt `weather_router_private_extensions`.

**Gezielte Korrektur:** Nur diese drei verifizierten Repository-/Kennungspaare werden auf die verbindliche Identität abgebildet; ältere gespeicherte automatisch erzeugte Kennungen werden beim Laden nach exaktem Paarvergleich korrigiert. Individuelle Kennungen werden nicht ungeprüft überschrieben. Kollisionen bleiben verboten. Keine Abschwächung der Manifest-, Kanal-, Hash-, Eigentümer- oder Freigabeprüfung.

**Commits:** `6e33221d8568d638a54f1366e79a86d49afb69e4` und Regressionstests `2206b87b91a93968a08d9d52afe3abb0d9877224`, jeweils mit erfolgreicher GitHub-CI (39401840824 bzw. 39401938210).

## 2. Zweispaltige Notebook-/iPad-Querformatdarstellung

Die vorherige Oberfläche ordnete Projektwahl, Quelle, Installation und Fehlerdiagnose vertikal hintereinander an. Dadurch war der entscheidende HA-Fehler regelmäßig außerhalb des Bildschirmfotos.

In `frontend/lab.js` wurde für breite Darstellungen ab 1150 CSS-Pixeln eine echte Rasteraufteilung eingeführt:

- **Links:** Projektwahl und Quellen-/Projektinformationen.
- **Rechts:** Installation, Fortschritt und HA-Diagnose.
- **Unterhalb über beide Spalten:** ausführliche Tests.
- **Schmale Ansichten:** bisheriger einspaltiger Ablauf; auch bei ausgeblendeter Hauptansicht kein irrtümliches Einblenden durch die Rasterregel.

Zusätzlich erscheint bei einem gescheiterten Sammelvorlauf **direkt vor dem Installationskopf** eine kurze, bereinigte Fehlermeldung mit Projekt, Phase und Fehlerklasse. Die ausführliche unveränderte Fehlerdiagnose bleibt weiter vorhanden. Dies verändert keine Schreib-, Quell- oder Sicherheitsfreigabe.

Die Darstellung im echten Home-Assistant-Frontend auf Notebook und iPad muss noch praktisch geprüft werden. Ein Browser-/Screenshot-Realtest wurde nicht behauptet.

## 3. Einheitliche Kandidatenversion und Regressionstests

`0.1.110` ist in `manifest.json`, `const.py` und der sichtbaren Frontend-Versionskonstante identisch. Es gibt ergänzende Python-Vertragstests für verifizierte Projektkennungen und sichere Migration sowie einen Layout-/Fehleranzeige-Vertragstest. Die vorhandenen JavaScript-Verhaltensprüfungen wurden auf die neue Versionsprüfung umgestellt.

Die ersten 0.1.110-Prüfläufe meldeten erwartete Frontend-Testfehler, weil mehrere Testobjekte weiterhin eine HA-Python-Laufzeit `0.1.109` simulierten; das Programm hat deshalb die absichtlich falsche Versionskombination korrekt gesperrt. Der Testdatenabgleich wurde mit Commit `d2a0f84ab54ccc3dfef542f387f050e7a03e5e5a` korrigiert.

**Verbindlich:** Der abschließende Prüflauf auf diesem Code-/Testcommit muss vor einer Testinstallation vollständig `SUCCESS` melden. Ein älterer grüner Lauf ist kein Ersatz.

## 4. Ausstehende echte Prüfungen auf Home Assistant DEV

1. Nach grüner GitHub-Prüfung die neue 0.1.110 gezielt über die bewährte DRA-V1-Engine kontrolliert installieren. **Diese Installation erfolgte hier nicht.**
2. Python-Laufzeit und Oberfläche nach HA-Neustart auf genau 0.1.110 vergleichen.
3. Sechs Projekte **nur vorbereiten**, niemals schon die Sammelinstallation bestätigen. Den neuen Status samt Quellref, Commit, Version und Projektkennung prüfen.
4. Für WeatherRouter muss nach freier, bewusst gewählter Quellkonfiguration **`deploy/dev`** angezeigt werden; kein stiller Rückfall auf `main`.
5. Bei einem weiteren Quellabbruch das neue sofort sichtbare Projekt-/Phasenfeld fotografieren. Keine Behauptung, dass alle sechs Projekte wegen der ersten behobenen Kennung automatisch erfolgreich vorbereitet werden.
6. Vor jeder echten Sammelinstallation zusätzlich die verbindliche Versions-/Commit-Prüftabelle und die serverseitige Freigabebindung prüfen. Eigenaktualisierungen V1 vor V2, V2 zuletzt; keine automatische zweite Startanforderung und kein unbestätigter Neustart.
7. Notebook/iPad-Quer- und Hochformat sowie schmale/mobile Ansichten praktisch testen. Insbesondere keine waagerechten Überläufe, überdeckte Aktionen oder verlorene Fehlerdiagnosen zulassen.

## 5. Sicherheits- und Freigabegrenze

**Keine HA-Sammelinstallation, kein DRA-V2-Selbstupdate und kein HA-Neustart wurden ausgeführt oder freigegeben.** Die bestehenden V1-Journale, Sicherungen, Rückfälle und serverseitigen Einmalbestätigungen bleiben Voraussetzung. DRA V1, Gewitterradar, WeatherRouter und die privaten Erweiterungen wurden nicht verändert.

Die neue Version ist ein **GitHub-Testkandidat** und bleibt bis zum abschließend grünen CI-Lauf sowie der anschließenden bewusst freigegebenen HA-DEV-Realabnahme gesperrt.

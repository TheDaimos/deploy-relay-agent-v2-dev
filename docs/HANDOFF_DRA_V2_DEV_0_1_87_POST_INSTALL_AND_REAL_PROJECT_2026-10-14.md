# Chatübergabe – DRA V2 DEV 0.1.87 · Abschlussaktionen und erster echter Projekteinsatz

**Datum:** 14.10.2026 (Deutschland)
**Projekt:** Deploy Relay Agent V2 DEV – Nachfolger von DRA V1
**Repository:** `TheDaimos/deploy-relay-agent-v2-dev`
**Einzig zulässiger Entwicklungszweig:** `feature/v2-10-inventory-operation-contract`
**Verifizierter Code-Checkpoint vor dieser Übergabe:** `8e44830c8c7254e08b087f8672c065eca429d403`
**CI:** [GitHub Actions 38522060619 – SUCCESS](https://github.com/TheDaimos/deploy-relay-agent-v2-dev/actions/runs/38522060619)
**Codeversion:** **0.1.87 DEV** in `manifest.json`, `const.py` und `frontend/lab.js`.
**HA-Installation 0.1.87:** **NICHT bestätigt**. Letzte veröffentlichte Aufforderung vor dem neuen Block war 0.1.86 DEV; aus dem Chat lässt sich kein belegter HA-Stand 0.1.87 ableiten. Niemals eine installierte Version erfinden.
**Status dieser Übergabe:** Code und CI bis 0.1.87 erfolgreich, neue Nachinstallationsaktionen noch nicht live abgenommen. Der Nutzer hat ausdrücklich eine ausführliche Chatübergabe angefordert.

## 1. Zwingende Projektvorgaben und Arbeitsstil

- **DRA V2 ersetzt DRA V1**, kein neues allgemeines Installationssystem und kein dauerhafter V1/V2-Doppelbetrieb.
- Die **vorhandene V1-Engine** für Git-Quelle, fest gepinnten SHA, Vorschau, Staging, Sicherung, eigentliche Installation, Verifikation und automatischen Rückfall weiterverwenden. Sie ist bereits in V2 eingebunden.
- Schwerpunkt ist nun **der erste kontrollierte Einsatz für ein echtes Projekt**, danach echte parallel laufende unabhängige Projektaufträge und Mehrkernnachweis auf HA; nicht erneut bei der synthetischen Testdatei oder bei kosmetischen Einzeländerungen verharren.
- **Mehrere zusammenhängende Punkte vollständig im Code und in CI abschließen**, erst danach **eine gebündelte HA-Abnahme**. Keine Version pro Kleinständerung, keine Folge von unnötigen HA-Neustarts/Screenshots. Nutzer hat Verzögerung und kleinteilige Testerei mehrfach und deutlich kritisiert.
- Nur Entwicklungszweig oben verändern. **NICHT** V1-Repositories, V2 `main` / öffentliche Auslieferung, WeatherRouter, Gewitterradar, private Exportablage `TheDaimos/Project-Log-And-Export` oder Draft-PR #2 ändern/mergen, es sei denn, der Nutzer beauftragt dies gesondert. Private Git-Ablage ausschließlich lesend für Diagnose; keine Zugangsdaten in Logs/Dokumente.
- Der Nutzer bedient Home Assistant selbst: V2 DEV wird in der Übergangsphase **über DRA V1** eingespielt; nur er führt Installationen und Neustarts aus. Kein Neustart oder produktives Update durch den Assistenten ohne gesonderte Freigabe.
- Verbindliche Quellen zuerst lesen: `AGENTS.md`, `docs/V2_ROADMAP.md` (Neufassung 12.10.2026), dieses Handoff, `docs/DRA_V2_0_1_87_POST_INSTALL_ACTIONS_ABNAHME.md`. `docs/AI_CONTEXT.md` enthält historisch ältere 0.1.74-Stände: nicht gegen jüngere Commit-/Abnahmedokumente verwenden.
- Keine ungesicherte Zielmutation, keine Aufweichung der Admin-, Quell-SHA-, Zielpfad-, Bestätigungs-, Sicherungs-, Journal- und Rückfallkontrollen. V1 darf während eines V2-Updates **nicht dasselbe Ziel** schreiben.

## 2. Produktstand und bereits erledigte Realtests

**V1-basierte V2-Installationsengine:** Implementiert und vom HA-besessenen `DeploymentCoordinator` / `ServerDeploymentJobs` aufgerufen. V1-Manifest, SHA-genauer Bestand, Backup, Staging, Verifikation und Rollback werden wiederverwendet. Synthetische Engine-Fehler-/Rückfalltests sind CI-grün.

**Isoliertes echtes Testprojekt:** `TheDaimos/Test-Repo-DRA-V2`, Branch `main`, Manifest-Ziel **ausschließlich** `/config/dra_v2_testprojekt/`, Dateien `payload/testdatei.txt` und `payload/teststatus.json`. Das Testprojekt wurde auf HA **real über V2 installiert und geprüft**. Ein bestätigter Live-Auftrag `276ea7d711024fa0bba070f0a2bfc2a7` zeigte 4/4, alle vier Schritte grün, Status `success`, Phase `complete` und den vollständig grünen Balken. Auch der gespeicherte historische 4/4-Abschluss nach HA-Neustart wurde per Screenshot abgenommen. Audit-Export: private Ablage `TheDaimos/Project-Log-And-Export`, 16 Ereignisse aus zwei erfolgreichen Aufträgen, zuletzt separat bestätigt.

**Tests-Rubrik / G2:** G2-Verbindungstest als aufklappbare Entwicklungsdiagnose aus normalem Deployment entfernt. Test 2 erhöht im exakt festgelegten Testrepo ausschließlich `payload/teststatus.json.teststand` um 1 und nutzt einen echten separat berechtigten GitHub-Token; ausdrückliche Bestätigung, Adminroute, fixed path und Git-Blob-Konfliktkontrolle. Test 2 wurde **real** mit `2 → 3` und Commit `664fda7bf442` abgenommen. Der GitHub-Token `Contents: Read and write` wurde vom Nutzer gezeigt; Auswahl `Read-Only/Read-Write` in Projektverwaltung ist **rein informativ**, keine lokale Installationsgenehmigung.

**Oberfläche:** Ein zentraler vierstufiger Deployment-Ablauf; Audit-Tabelle mit Filter und Export; Projektübersicht mit angeglichenem Sammelupdate-Zahnrad; Quellstand-`Aktualisieren` als Leseabfrage. Fehler 2/4→4/4-/Neulauf nach 4/4 ist softwareseitig in 0.1.85 korrigiert und mit Regressionstest abgedeckt. In 0.1.86 wurde für verifizierten Null-Datei-Unterschied ein eigener **blau-türkiser** Status `Aktuell · Kein Update verfügbar` statt der irreführenden orangefarbenen Installationsvorbereitung gebaut; vorheriger Erfolg wird dann nur als Historie gezeigt. **HA-Realabnahme von 0.1.86 selbst ist nicht ausdrücklich bestätigt.** Nicht nochmal verschiedene Isoliertests nur für diese Texte einplanen.

**Parallelität/Mehrkern:** `OperationRegistry(max_mutating=4)`, Zielreservierung verhindert paralleles Schreiben auf identische, verschachtelte oder sich überschneidende Ziele; unabhängig vorbereitete Projekte dürfen parallel arbeiten. `parallel_preview.py` kann bei echten mehreren unabhängigen Manifest-Gruppen per begrenztem Spawn-`ProcessPoolExecutor` arbeiten. CI/Synthetic erfolgreich. **Echte parallele HA-Installationen und reale Mehrkernleistungsmessungen sind noch nicht abgenommen** – nicht als erledigt darstellen.

## 3. Zuletzt implementiert: 0.1.87 – Nachinstallationsaktionen (unmittelbarer letzter Entwicklungsblock)

Der Nutzer fordert komfortable Abschlussaktionen nach einem Update:
- **„Oberfläche aktualisieren“**, wenn die Installation ausschließlich sichere Frontend-Dateien verändert hat.
- **„Home Assistant neu starten“**, wenn Python- oder andere Backend-/gemischte Dateien es verlangen, mit sichtbarer Sicherheitsabfrage und ausdrücklicher zweiter Bestätigung.

**Vorhandene Klassifikation:** In `v1_engine/lifecycle_policy.py` wird `frontend_reload` nur dann gestattet, wenn alle **tatsächlich geänderten** Ziel-Dateipfade in sicheren Frontend-Pfaden liegen, z. B. `custom_components/<integration>/frontend/*` oder `www/*`. Python, gemischte und unbekannte Änderungen verbleiben bei `home_assistant_restart`. `server_deployment_jobs.py` übernimmt V1-Ergebnis `result.lifecycle` erst **nach** erfolgreicher Installation und Verifikation. `integration_reload` wird konservativ als HA-Neustartbedarf behandelt, da kein garantiertes allgemeines Integration-Neuladen in V2 vorhanden ist. Serverdatensatz enthält `restart_required` und `frontend_reload_possible`.

**Browser-Oberfläche:** `frontend/lab.js` zeigt die jeweils geeignete Nachaktion ausschließlich bei einer **aktuellen erfolgreich abgeschlossenen** V2-Installation, passender UI-/Python-Version und gültiger Jobidentität. Für Frontend nur Browser-Neuladen, **kein** Neustart der HA-Instanz. Für Backend Sicherheitsfrage `Home Assistant wirklich neu starten?` mit `Abbrechen` / `Ja, Home Assistant neu starten`. Bei keinem Nachaktionsbedarf `Keine weitere Aktion erforderlich`. Historische Audit-Datensätze, reine Vorschaubefunde und fehlgeschlagene Installationen dürfen keine Aktion autorisieren. Neuer Installationszyklus setzt eine alte offene Neustartabfrage zurück.

**Serverseitige Sicherheitsstrecke:** `websocket_api.py` Admin-Route `deploy_relay_v2_dev/deployment/restart`, erwartet `operation_id` und `confirm=true`; prüft echten V2-Auftrag in der aktiven Registry, `success`, `complete`, `restart_required=true`, derzeit keine weiteren laufenden V2-Schreibaufträge. Serverseitige Sperre `runtime.restart_pending` mit `restart_lock` schützt gegen doppelte Anforderungen. Einziger HA-Aktionsaufruf: `await hass.services.async_call("homeassistant", "restart", {}, blocking=False)`. Kein automatischer Neustart nach der Installation. Nur ausdrücklich bestätigter UI-Aufruf.

**Automatisierte Prüfung:** `tests/test_v2_post_install_actions.py` führt den realen Produktions-Neustarthandler isoliert mit simulierter HA-Laufzeit aus: keine Bestätigung, Fehler, falsche Phase, kein Neustartbedarf, ungültige ID, laufende Installation und Doppelanforderung dürfen keinen Dienstaufruf erzeugen; positiver Fall erzeugt genau einen `homeassistant.restart`-Aufruf; simulierter Dienstfehler hebt Sperre auf. `tests/test_v2_countdown.js` prüft die beiden UI-Fälle und die zweistufige Bestätigung. Gesamter CI-Lauf der **0.1.87**-Version **SUCCESS**: Run 38522060619, Commit `8e44830c8c7254e08b087f8672c065eca429d403`.

**WICHTIG:** 0.1.87 in HA **noch nicht als installiert oder real abgenommen behandeln**. Keinen tatsächlichen HA-Neustart durch den Assistenten anfordern/auslösen. Prüfspezifikation: `docs/DRA_V2_0_1_87_POST_INSTALL_ACTIONS_ABNAHME.md`.

## 4. Nächstes verbindliches Ziel: erster echter Projekteinsatz, keine weitere Entwicklungsschleife

**Vom Assistenten zuletzt empfohlenes erstes reales Projekt: Gewitterradar.** Repository `TheDaimos/gewitterradar`, Git-Branch `deploy/dev`, reales Ziel `/config/custom_components/gewitterradar/`. Manifest `deploy-relay.json` existiert mit Projekt-ID `gewitterradar`, `source=custom_components/gewitterradar`, `target=custom_components/gewitterradar`, `replace_directory`, `max_files=5000`, `max_uncompressed_bytes=157286400`, deklariert `home_assistant_restart`. WeatherRouter `TheDaimos/weather-router-dev` hat ebenfalls ein plausibles V1-Manifest, soll jedoch nicht gleichzeitig beim ersten Abnahmetest verändert werden.

**Konkrete Reihenfolge, kompakt und gebündelt:**
1. Wenn der Nutzer weiterarbeiten will: 0.1.87 DEV **über DRA V1 installieren** und HA **einmal** neu starten. Installierte Python- und UI-Version 0.1.87 abgleichen. Kein Bedarf, Zwischenversionen zu installieren.
2. In DRA V2 **Gewitterradar auswählen**, Ref `deploy/dev`, Quelle prüfen, echten Commit anzeigen und **schreibgeschützte Vorschau** für genau das Projekt ausführen; Pfad/Dateigruppen, Add/Change/Remove, angezeigten Nachaktionsbedarf und mögliche Warnungen prüfen. Bei `0 Änderungen` ist keine Installation nötig; dann keinen künstlichen Commit nur für einen UI-Test erzeugen, sondern auf sinnvolles echtes Update warten oder mit ausdrücklicher Nutzerzustimmung ein anderes sicheres Projekt wählen.
3. **Vor erstem produktivem V2-Schreibauftrag:** Nutzer bewusst über betroffene Pfade, Sicherung und potenziellen HA-Neustart informieren. Nicht automatisch oder ohne Freigabe installieren. DRA V1 darf zeitgleich nicht dieselben Gewitterradar-Dateien verändern.
4. Der Nutzer bestätigt im UI die echte V2-Installation; HA-eigener Auftrag soll die V1-Engine mit realer Sicherung, Staging, Schreibvorgang, Verifikation/gegebenenfalls Rückfall nutzen. Danach aktuellen 4/4-Status und Audit/Export prüfen. Bei Fehlern privaten Git-Export read-only analysieren.
5. Die **Nachaktions-Schaltfläche** anhand des serverseitigen Ergebnisses prüfen. Bei backendrelevantem Update `Home Assistant neu starten` samt Sicherheitsabfrage: zuerst `Abbrechen` zeigen/prüfen, danach nur mit bewusster Benutzerbestätigung Neustart. Bei Frontend-only `Oberfläche aktualisieren` ohne HA-Neustart. Keinen zusätzlichen künstlichen Updatezyklus nur für den seltenen Frontend-only-Fall verlangen.
6. Erst wenn ein reales Projekt auf HA zuverlässig über V2 aktualisiert wurde: **echte unabhängige parallele Projektaufträge** / **Mehrkernprozess-Nachweis** als nächster zusammenhängender Kernblock, mit gebündelter Abnahme. Danach V1-Nachfolger kontrolliert abschließen. V2 FINAL/PUB aktuell nicht freigeben.

**Unterschied zwischen CI und Realabnahme nie verwischen:** Synthetic-Rollback, parallele Aufträge und Neustart-Route sind automatisiert geprüft; reales Gewitterradar-Update, tatsächlicher V2-Ausfall/Rückfall, Frontend-Neuladen über V2 und per V2 angeforderter HA-Neustart sind noch nicht als HA-echt bestätigt.

## 5. Offene Entscheidungen und bekannte Risiken

- Kein aktueller Beleg, dass die Benutzer-HA-Instanz 0.1.87 installiert hat; bei Fortsetzung die tatsächliche Version kurz erfragen/aus Screenshot feststellen, nicht erraten.
- Der spätere parallele Echtprojektbetrieb darf nicht dieselben HA-Zielpfade mutieren. Vor erster Gewitterradar-Mutation muss eine sichere Rückfallmöglichkeit dokumentiert und die V1/V2-Gleichzeitigkeit ausgeschlossen sein.
- V2-Wunsch ist noch: Integration-eigener Backupprozess/HA-Neustart getrennt und nachvollziehbar; V1-Engine wird bereits genutzt. Keine neue Engine konzipieren.
- G2 prüft HA-eigene Hintergrundaufträge auch bei Browserunterbrechung; bisherige Testbasis reicht als Grundlage, aber eine live laufende größere Installation mit echter Browserunterbrechung ist noch kein HA-Nachweis. Beim ersten echten Projektupdate wenn möglich mit beobachten, nicht als isolierte zusätzliche Entwicklungsphase.
- Die automatische Frontendklassifikation ist konservativ. Sollte ein Frontend-Update JS-Dateien außerhalb der erlaubten Pfade verändern, ist der HA-Neustartbedarf absichtlich streng und muss nicht per kosmetischer Ausnahme umgangen werden.
- **Produktziel gegenüber Nutzerfrust:** Nutzer hat DRA V1 trotz ähnlich vieler UI-Funktionen deutlich schneller fertig entwickelt. In DRA V2 wurde zu viel kleinteilig getestet/geplant. Nicht mit „V2 ist komplexer“ rechtfertigen; tatsächlichen funktionierenden Produktfortschritt liefern.

## 6. Sofort verwendbare Fortsetzungsanweisung

Zuerst `AGENTS.md`, `docs/V2_ROADMAP.md`, diese Übergabe und `docs/DRA_V2_0_1_87_POST_INSTALL_ACTIONS_ABNAHME.md` lesen; aktuellen Code/CI gegen `8e44830c8c7254e08b087f8672c065eca429d403` prüfen. Die letzte Version ist **0.1.87 DEV**, Abschlussaktionen im Code und CI-grün, **HA-Realabnahme offen**. Nicht erneut Test-Repositories, 4/4-UI, G2 oder synthetische Einzeltests durchlaufen. Nächster Schritt: **ein gebündelter erster echter Gewitterradar-Updateversuch** über die übernommene V1-Engine und neue Abschlussaktionen, nur nach dem sicheren Quell-/Pfadvergleich und ausdrücklicher manueller Benutzerbestätigung. Danach echte Parallelität/Mehrkernverarbeitung auf HA. Nur autorisierter Featurezweig, keine Fremdprojekte verändern, keine eigenständigen HA-Neustarts.

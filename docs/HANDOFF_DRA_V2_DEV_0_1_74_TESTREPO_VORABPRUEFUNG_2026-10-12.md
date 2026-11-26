# VERBINDLICHE CHATÜBERGABE – DRA V2 DEV 0.1.74, Test-Repository und Projekt-Vorabprüfung
**Datum:** 12.10.2026  
**Projekt:** Deploy Relay Agent V2 DEV  
**Status:** DRA V2 DEV **0.1.74 auf Home Assistant installiert, HA neu gestartet, V2 bereit**; die erste echte Projektinstallation mit V2 ist noch **nicht** durchgeführt.  
**Diese Übergabe ist neuer als alle bisherigen 0.1.53–0.1.64-Übergaben.** Bei Widersprüchen gilt der aktuellste HA-Befund und diese Datei, nicht die historischen G3/G4/G5-Teilpläne.

## 1. Verbindliche Produktentscheidung des Betreibers – NICHT ERNEUT DISKUTIEREN

Der Betreiber hat den Assistenten **ausdrücklich eingefangen**, weil DRA V2 zu einem künstlich ausufernden Projekt aus Prüf- und Sicherheitsstufen geworden war.

**Ziel:** DRA V2 ersetzt DRA V1 als direkte Weiterentwicklung. **Bewährte V1-Installationsengine weiterverwenden**, dabei gezielt ergänzen:
1. echte Mehrkernverarbeitung rechenintensiver Arbeit, ohne die Home-Assistant-Ereignisschleife zu blockieren;
2. parallele, **serverseitig** bearbeitete Aufträge für voneinander unabhängige Projekte;
3. Weiterlaufen bei Browser-/App-/Netzwerkunterbrechung mit nachvollziehbarer Wiederverbindung;
4. bereits gemeinsam überarbeitete V2-Oberfläche und zentraler geführter Deployment-Knopf.

**Keine vollständige Neuerfindung von Git-Vergleich, Staging, Backup, Installieren, Prüfsummen, Restore oder Rollback.** Die funktionierenden V1-Algorithmen bilden den Kern. Es ist **kein** permanenter Parallelbetrieb von DRA V1 und V2 vorgesehen; V1 installiert V2 in der Entwicklungsübergangszeit lediglich vorübergehend. Keine neue V1/V2-übergreifende Besitzverwaltung oder eigenes Großprojekt G3/G4/G5. Schutz gegen kollidierende **V2**-Schreibvorgänge und funktionierende V1-Sicherung/Rückfall bleiben Pflicht.

**Verbindliche Arbeitsweise:** in zusammenhängenden Funktionsgruppen entwickeln und automatisch prüfen; keine neue Version, HA-Installation, Neustart, Einzelabnahme oder Screenshot für jede kleine Änderung. Für eine fertige Funktionsgruppe **eine gebündelte HA-Realabnahme**. Nicht permanent Zwischenfreigaben verlangen, keine künstlichen Wartephasen. Der Betreiber arbeitet allein. Deutsch ohne unnötiges Denglisch, knappe klare Anweisungen, kopierbare Git-Namen/Koordinaten. **DRA V2 soll zügig fertig werden.**

Siehe `AGENTS.md`, `docs/V2_ROADMAP.md`, `docs/AI_CONTEXT.md`.

## 2. Repositories, einzig erlaubte Schreibgrenze und Git-Status

**V2-Quellrepository:** `TheDaimos/deploy-relay-agent-v2-dev`  
**Einzig zur V2-Entwicklung freigegebener Zweig:** `feature/v2-10-inventory-operation-contract`  
**Zuletzt vor dieser Übergabedatei verifizierter Code-HEAD:** `cb4c31afb7f002be35cf803a1f7229286657d36e`  
**Letzter vollständig erfolgreicher CI-Lauf auf diesem Stand:** [GitHub Actions 38224370629](https://github.com/TheDaimos/deploy-relay-agent-v2-dev/actions/runs/38224370629) – **SUCCESS**.  
**Draft-PR #2:** offen, Draft, **nicht zusammengeführt**.

Keine Änderungen an V2-`main`, DRA V1 DEV/PUB, DRA V2 PUB, WeatherRouter oder `TheDaimos/Project-Log-And-Export`, keine Freigabe für einen Merge. Das private Archiv dient ausschließlich zur zulässigen privaten Diagnoseablage und bleibt unangetastet. Testdaten-Repository wurde auf ausdrücklichen Wunsch des Betreibers separat eingerichtet (siehe § 5). Kein automatischer HA-Neustart oder Projektupdate aus GitHub-Tools.

**Zu Beginn des Folgechats:** Den aktuellen HEAD und CI nochmals lesen – dieser konkrete SHA bezeichnet den **Code-Checkpoint vor Anlage der Übergabedatei**, nicht zwangsläufig den dann neuesten Dokumentations-HEAD.

## 3. Echter HA-Betriebsstand – vom Betreiber bestätigt

Der Betreiber hat **DRA V2 DEV 0.1.74** mit **DRA V1** auf Home Assistant installiert und Home Assistant anschließend vollständig neu gestartet. Auf die erneute Rückfrage stellte er ausdrücklich klar: „ja, ist neu gestartet und 174 ist bereit, das meinte ich mit meiner vorherigen aussage“.

**Nicht nochmals eine Installation oder einen Neustart von 0.1.74 verlangen.** Dies ist der aktuelle HA-Stand. 0.1.73 wurde nie separat abgenommen, die Änderungen sind in 0.1.74 gebündelt.

**Noch NICHT real bewiesen:** DRA V2 hat bislang **kein einziges reales Zielprojekt über seine neue eigene V2-Installationsstrecke aktualisiert**. Die HA-Realabnahme von serverseitiger V1-Installation, Backup, automatischem Rollback und paralleler Bearbeitung ist daher offen, trotz erfolgreicher automatischer CI-Tests. Die echte Mehrkernleistung ist unter Home Assistant noch nicht gemessen. Nicht behaupten, diese Realtests seien bereits bestanden.

## 4. Implementierter DRA-V2-Kern in 0.1.74

- 15 V1-kompatible Quellmodule in `custom_components/deploy_relay_v2_dev/v1_engine/` (V1-Algorithmen weitgehend unverändert; Sicherungs- und Transaktionsspeicher V2-eigen unter `/config/deploy_relay_v2_dev`).
- `v1_source_bridge.py`: festgelegter Git-Commit, V1-Manifest, Quellinventar/Prüfsummen und reale Dateivorschau.
- `parallel_preview.py`: reale, voneinander unabhängige Datei-Gruppen können zur Hash-/Dateivorschau begrenzt in bis zu vier Prozesse verteilt werden; bei Ein-Gruppen-Projekten oder nicht unterstütztem Prozessstart serieller V1-Pfad. **Kein Beleg einer Beschleunigung unseres Testprojekts mit nur einer Gruppe.**
- `deployment_coordinator.py`: projekt-/commitgebundene einmalige, kurzlebige Bestätigung. Es wird vor der Freigabe erneut ein Lesevergleich durchgeführt.
- `server_deployment_jobs.py`: HA-eigene, browserunabhängige Aufträge mit V1-Sicherung, wirklichem Installationscode, Integritätskontrolle und Rollback-/Wiederherstellungszustand.
- `operation_registry.py`: bis zu **vier gleichzeitig laufende, voneinander unabhängige V2-Schreibaufträge**; Zielpfadüberschneidungen sowie doppelte Projekte werden blockiert. Keine unkontrollierte Parallelinstallation desselben Ziels.
- `websocket_api.py`: Administrator-WebSocket `deployment/prepare`, `deployment/start`, `deployment/status`; letzterer bietet gemeinsame Statusübersicht mehrerer Aufträge.
- `frontend/lab.js`: eine zentrale geführte Schaltfläche, danach separate sichtbare Bestätigung „Ja, Update installieren“; serverseitigen Fortschritt, Auftragskennung und Status auch bei Projektwechsel anzeigen. HA-Neustart nur nach ausdrücklicher eigener Betreiberaktion.
- V1-Sicherungs-/Rückfallfunktion wurde **auf synthetischen echten Testdateien** automatisch installiert und bei provoziertem Fehler real zurückgerollt. Separate Parallelitätstests haben zwei bis vier gleichzeitige künstliche Engine-Aufträge nachvollzogen.

Die gebündelten KI-/CI-Berichte liegen in:
- `docs/V2_V1_ENGINE_REUSE_IMPLEMENTATION_2026-10-12.md`
- `docs/V2_V1_ENGINE_HA_SERVER_INSTALL_0_1_73_2026-10-12.md`
- `docs/V2_PARALLELE_PROJEKTUPDATES_0_1_74_2026-10-12.md`

Die Version **0.1.74** ist in Python-Laufzeit, Integrationsmanifest und JS-Oberfläche synchron.

## 5. Neues ungefährliches öffentliches Test-Repository – fertig und im HA registriert

**GitHub:** [TheDaimos/Test-Repo-DRA-V2](https://github.com/TheDaimos/Test-Repo-DRA-V2)  
**Sichtbarkeit:** public  
**Zweig:** `main`  
**Letzter Stand des Test-Repositories:** `8a617a7c6a59c7e41cc48365464c70cc14188f02`  
**Vom Betreiber bestätigt:** „Repo ist hinterlegt.“ Es wurde in der DRA-V2-Projektverwaltung angelegt/registriert. **Die tatsächliche Zugriffsart (`read_only` oder `read_write`) wurde noch nicht durch einen Screenshot nach der Speicherung bestätigt. Unbedingt vor dem Schreibtest prüfen.**

Dateien:
- `README.md` – öffentlicher Zweck/Einbindung;
- `deploy-relay.json` – V1-kompatibles DRA-Manifest;
- `payload/testdatei.txt`;
- `payload/teststatus.json`.

Verbindliche Manifestidentität:
```json
{
  "schema": "deploy-relay.deployment.v1",
  "project": {"id": "test_repo_dra_v2", "name": "DRA V2 Testprojekt"},
  "source": {"repository": "TheDaimos/Test-Repo-DRA-V2", "mode": "repository_contents"},
  "deployment": {"root": "/config", "groups": [
    {"id": "testdata", "source": "payload", "target": "dra_v2_testprojekt", "mode": "replace_directory"}
  ]},
  "lifecycle": {"after_install": "none"},
  "policy": {"allow_symlinks": false, "max_files": 8, "max_uncompressed_bytes": 32768}
}
```

**Alleiniger lokaler Schreibbereich:** `/config/dra_v2_testprojekt/`; dort sollen die zwei künstlichen Testdateien liegen. **Niemals** `/config/custom_components`, `.storage`, DRA selbst, Gewitterradar, WeatherRouter oder andere produktive Bereiche verändern. **Laut Testmanifest kein HA-Neustart erforderlich.** Public-Testrepo benötigt keinen Token für das Lesen; **Read-Write in DRA** ist ein lokaler Installations-Freigabemodus, **kein GitHub-Schreibrecht**.

Die Testdateien und das Manifest wurden nach Erstellung über GitHub nochmals überprüft, ohne Auffälligkeiten.

## 6. Benutzerbeobachtung und neue, NOCH NICHT IN HA INSTALLIERTE UI-Verbesserung

Der Betreiber hat beim ersten Projekt-Hinzufügen einen Screenshot geliefert: „Verbindung prüfen“ und „Token speichern“ waren ausgegraut, solange die Projektregistrierung noch nicht existierte. Das ist unpraktisch; er wünscht die Prüfung von Repository **und optionalem neu eingegebenen Token vor dem Speichern**.

**Im V2-Featurezweig inzwischen implementiert und CI-grün, aber noch nicht veröffentlicht/installiert:**
- Vorhandener Admin-WebSocket `deploy_relay_v2_dev/projects/connection_check` besitzt jetzt optional `draft:true` und `token` und kann ein **noch nicht registriertes** Repository mit optionalem **flüchtigem** Token per ausschließlich lesendem GitHub-GET prüfen.
- Ein bei der Vorprüfung eingegebener Token wird **nicht gespeichert**, nicht in den Rückgabewerten oder öffentlichen Logs ausgegeben. Er wird allein für die Prüfung verwendet. Die bisherige Prüfung registrierter Projekte bleibt gültig.
- Im Dialog „Projekt hinzufügen“ ist die Prüfung nun bereits vor Speichern möglich. Bei einem öffentlichen Repo funktioniert sie ohne Token.
- `_saveNewProject` speichert nach der Bestätigung das Projekt und **optional** den Token in der separaten V2-Tokenablage. Bei Tokenfehler bleibt die Projektregistrierung nachvollziehbar, ohne fälschlich vollständigen Erfolg zu behaupten.
- Der vormals missverständliche Hinweis „Zugriffsart nur zur Übersicht“ wurde präzisiert: `read_write` steuert die lokale Installationsfreigabe, jedoch nicht GitHub-Berechtigungen.
- Das JavaScript-Testpaket umfasst die Vorabprüfung eines noch ungespeicherten Projekts mit vorübergehendem Token und eines öffentlichen Projekts ohne Token, einschließlich Fehlerrückmeldungen und Speicherung.

**Aktueller Code-Checkpoint vor Übergabe:** `cb4c31afb7f002be35cf803a1f7229286657d36e`, **CI [38224370629 SUCCESS](https://github.com/TheDaimos/deploy-relay-agent-v2-dev/actions/runs/38224370629)**. Noch **kein Versionssprung** auf 0.1.75, weil die Änderung zusammen mit späteren Arbeiten ausgeliefert werden soll. In HA läuft **weiter 0.1.74**, also die alte Projektverwaltung; bei dort erneutem „Projekt hinzufügen“ darf die neue Vorabprüfung nicht erwartet werden.

**Wichtig für den Folgechat:** Diese Verbesserung jetzt **nicht** mit einem eigenen HA-Update/-Neustart abnehmen. Sie ist automatisiert getestet und für die nächste zusammenhängende DEV-Funktionsgruppe bereitzuhalten. Nicht erneut planen oder doppelt implementieren.

## 7. Unmittelbar nächster sinnvoller Schritt im neuen Chat: gebündelte erste REAL-Abnahme auf 0.1.74

**Nicht erneut V2 installieren, nicht erneut HA neu starten, nicht die neue Projektverwaltung vorzeitig ausliefern.**

1. Betreiber öffnet auf bereits laufender **0.1.74** das registrierte Projekt `TheDaimos/Test-Repo-DRA-V2`; kontrolliert, ob es **aktiv** und als `Read-Write` registriert ist (falls nicht, in Projekteinstellungen ändern). Public: kein Token nötig.
2. Wählt den Zweig `main` und führt **zuerst ausschließlich die schreibgeschützte Vorschau** der V2-Oberfläche aus. Erwartung bei bislang leerem Ziel: **zwei neue Dateien, keine entfernten**, Verzeichnis ausschließlich `dra_v2_testprojekt`. Eine tatsächliche Vorschau kann andere Zahlen ausweisen, falls das Ziel schon existiert – keine Zahl erfinden, Ergebnis zeigen lassen.
3. **Vor echter Mutation** überprüfen, ob Commit, Manifest-Projektkennung `test_repo_dra_v2`, Quellgruppe `payload`, Ziel `/config/dra_v2_testprojekt/` und erwartetes Neustartverhalten `none` stimmen. Die Vorschau muss selbst in 0.1.74 ungefährlich bleiben. Sollte sie fehlgehen, genau **eine** sinnvolle Diagnose/Anzeige einholen und Fehler im freigegebenen Code korrigieren, ohne weitere Testschlachten.
4. Erst **nach positiver Vorschau** ausdrücklich vom Betreiber eine einmalige Installation über V2 bestätigen lassen. Diese neue Installation ist real noch nicht abgenommen. Auftragskennung/Status, Sicherung, tatsächliche beiden Dateien und Ausführung bei geschlossenem/neu geöffnetem Browser zusammen prüfen; kein absichtliches Risiko an Produktivsystemen. Bei Fehler nicht wiederholt blind starten; sichere Ursache und V1-Transaktionsjournal prüfen. Private Diagnose nur ins private Export-Repository.
5. Ein zweiter **ungefährlicher Teststand** durch Änderung nur der zwei künstlichen Payload-Dateien kann später Backup/Änderungsinstallation belegen. Keine absichtliche Zerstörung einer produktiven Integration oder provozierter HA-Abbruch.
6. Echte parallele HA-Aufträge erfordern zwei **tatsächlich unabhängige** harmlose Projektziele und sind bis jetzt nur synthetisch getestet. Nicht unnötig eigens mehrere neue Produkt-/Testprojekte erfinden. Der erste echte Einzelprojektauftrag ist vorrangig.
7. Die kleine bereits automatisiert getestete **Vorab-Verbindungsprüfung** erst bei einer später ohnehin notwendigen gebündelten DEV-Version in HA übernehmen.

Prüfe unbedingt: Der Betreiber erwartet **keinen Einzeltest-Marathon**. Eine komplette, kompakte Prüfanweisung mit den sinnvollen Teilfällen reicht. Immer nur dann eine Rückmeldung anfordern, wenn sie zur tatsächlichen Diagnose oder sicheren Freigabe notwendig ist.

## 8. Grenzen und ehrliche Statuskommunikation

- **Installiert & bereit:** 0.1.74 auf HA, mit vollständig erfolgtem Neustart, vom Betreiber bestätigt.
- **Git/CI:** V2-Code einschließlich ungespeicherter Repository-/Token-Vorabprüfung grün, **aber diese neue UI-Änderung nicht installiert**.
- **Testrepo:** öffentlich und im Git vollständig vorbereitet; **in V2 laut Betreiber hinterlegt**, Zugriffsmodus noch ungeprüft.
- **Schreibende V2-Installation:** noch nie real gegen das Testrepo durchgeführt. Keine Behauptung „alles bereits real bestanden“.
- **Parallelität:** simulierte gleichzeitig laufende Aufträge bestanden; echte parallele HA-Installation noch nicht verifiziert.
- **Mehrkern:** bei unabhängig verwalteten Dateigruppen implementiert und automatisch geprüft; echte Mehrprozess-/Geschwindigkeitsmessung im HA noch offen.
- **Security:** V1-Sicherung/Rollback erhalten; Selbstupdate und parallele Zielkollision weiterhin sperren; kein neuer V1/V2-Großplan.
- **Repositoryarbeit:** ausschließlich erlaubten Zweig; Draft-PR #2 unverändert offen. Keine Git-Exports, Tokens oder privaten Daten in öffentliche Quellrepositories.

## 9. Empfohlener Startprompt für den Folgechat

```text
Bootstrap: Daimos

Projekt: Deploy Relay Agent V2 DEV
Repository: TheDaimos/deploy-relay-agent-v2-dev
Einziger erlaubter Entwicklungszweig: feature/v2-10-inventory-operation-contract

Lies zuerst vollständig:
1. AGENTS.md
2. docs/AI_CONTEXT.md
3. docs/HANDOFF_DRA_V2_DEV_0_1_74_TESTREPO_VORABPRUEFUNG_2026-10-12.md
4. docs/V2_ROADMAP.md

Prüfe anschließend den neuesten Git-HEAD und den zugehörigen CI-Status.

Verbindlich: Der Betreiber hat DRA V2 DEV 0.1.74 bereits über V1 installiert und Home Assistant neu gestartet. DRA V2 ist bereit. Nicht erneut ein Update/Neustart verlangen.

Neues öffentliches Test-Repo: TheDaimos/Test-Repo-DRA-V2, main, in V2 registriert. Installationsziel ausschließlich /config/dra_v2_testprojekt/. Die erste echte V2-Testinstallation steht aus. Nächster Schritt ist die harmlose schreibgeschützte Vorschau des Testprojekts auf der laufenden 0.1.74; Ziel/Manifest/Zugriffsart kontrollieren, erst danach eine ausdrücklich bestätigte Installation.

Die UI-Verbesserung „Repository und optionalen Token VOR dem Speichern prüfen“ ist bereits im DEV-Zweig implementiert und automatisch CI-grün, aber NICHT auf HA installiert. Nicht erneut implementieren oder dafür einen separaten HA-Neustart verlangen.

Arbeite strikt mit der bewährten V1-Engine; V2 verbessert nur Mehrkernverarbeitung, Parallelität, serverseitige Aufträge und die vorhandene Oberfläche. Keine ausufernden G3/G4/G5-Einzeltests oder neuen Parallelbetriebskonzepte. Tests sinnvoll bündeln. V1/PUB/main/WeatherRouter/privates Exportarchiv nicht ändern, Draft-PR #2 nicht mergen.

Führe die Entwicklung und gebündelte HA-Abnahme zügig und mit klaren, konkreten Anweisungen fort.
```

**C.K. – Eine Idee weiter gedacht.**

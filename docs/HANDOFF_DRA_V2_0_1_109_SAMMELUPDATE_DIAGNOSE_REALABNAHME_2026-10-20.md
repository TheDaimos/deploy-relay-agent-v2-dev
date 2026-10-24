# Verbindliche Chatübergabe – DRA V2 0.1.109 DEV / Sammelupdate, Quellfehler, Geräteüberwachung und Realabnahme

**Stand:** 20.10.2026, Deutschland  
**Projekt:** Deploy Relay Agent V2 (DRA V2 DEV)  
**Privates Repository:** TheDaimos/deploy-relay-agent-v2-dev  
**Einziger beschreibbarer Zweig:** feature/v2-10-inventory-operation-contract  
**Verifizierter Code-Basiscommit vor den Übergabecommits:** c80c126af5f4df5fee204701f3296c7a9ca02fe5  
**Verifizierte GitHub-Version:** 0.1.109 DEV (manifest.json, const.py, frontend/lab.js)  
**GitHub Actions:** Run 39388573164, SUCCESS auf exakt diesem HEAD  
**Letzte durch Nutzerscreenshot nachgewiesene HA-Version:** 0.1.108 DEV, Oberfläche = Python-Laufzeit  
**HA-Installation von 0.1.109:** NICHT nachgewiesen  
**Gesamtstatus:** CI-geprüfter neuer Korrekturkandidat; Sammelupdate, Versions-Zwischenfenster, geräteübergreifende Batch-Installation und Selbstupdate NICHT auf HA realabgenommen.

## 1. Wichtigster Grundsatz – keine scheinbaren Erfolge

Diese Übergabe ist verbindliche Bestandsaufnahme, KEIN Abschluss der Entwicklung. Eine erfolgreiche GitHub-CI oder angezeigte Quellprüfung bestätigt KEINE tatsächliche Installation. Niemals eine HA-Installation, einen HA-Neustart, den Abschluss eines Sammelupdates oder eine durchgeführte Rückfallsicherung behaupten, solange der entsprechende HA-Auftrag, das Journal und das installierte Projekt wirklich geprüft wurden.

**Den Nutzer nicht erneut durch viele kleine Versionen und bloße Oberflächentests schicken.** Weiterentwicklung möglichst vollständig eigenständig; gebündelte Korrekturen, ausführliche positive/negative Tests und GitHub-CI, danach wenige gezielte HA-Realtests. Der Nutzer hat mehrfach und nachvollziehbar kritisiert, dass DRA V1 in kürzerer Zeit fertig und funktionsfähig war, während V2 wiederholt grundlegende Bedienfehler zeigte. Priorität hat nachprüfbare Funktion, nicht Kosmetik.

Home Assistant führt alle Schreibaufträge aus. Desktop, Android und iPad sind reine Bedienungs- und Beobachtungsoberflächen. DRA V2 muss die bewährte V1-Engine und ihre Sicherung/Journal-/Rückfall-/Hashprüfung verwenden, keine zweite Deployment-Engine bauen.

### Strikte Repository- und Sicherheitsgrenzen

- NUR das private DRA-V2-Repository und NUR den obigen Featurezweig beschreiben; kein Merge/Release auf main, keine Veränderung von DRA V1, Gewitterradar, WeatherRouter, privaten Extensions oder öffentlichen Repositories ohne neuen ausdrücklichen Auftrag.
- DRA V1 ist weiterhin bewährter Weg, über den der Nutzer neue V2-Testkandidaten auf HA DEV installiert.
- Das zentrale private Diagnosearchiv TheDaimos/Project-Log-And-Export ist der vorgesehene Exportort. Nicht in fremden/öffentlichen Repositories diagnostische Exporte ablegen; Archiv nur lesend untersuchen, solange kein gesonderter Schreibauftrag vorliegt.
- Keinen GitHub-Token oder andere Zugangsdaten anzeigen; Fehlertexte bereinigen. Keine Selbstupdates außerhalb des vorgesehenen HA-seitigen Auftragsvertrags, keine Übernahme ohne Bestätigung, keine zweite Installation bei unklarer Startquittung.
- Nach einem HA-Neustart Vorbereitungen/Controllerzustände neu vom Server verifizieren; keine alte Browservorschau als Freigabe wiederverwenden.

## 2. Was der Nutzer zuletzt konkret gezeigt hat (20.10.2026)

### HA V0.1.108 – Sammelupdate scheitert VOR Installation

Nutzerscreenshot: DRA V2 HA-Laufzeit 0.1.108 = Oberfläche 0.1.108. Sechs von sechs installierbaren Projekten waren angehakt:

1. Deploy Relay Agent V1 – TheDaimos/deploy-relay-agent-dev
2. DRA V2 DEV – Nur Testlabor – TheDaimos/deploy-relay-agent-v2-dev
3. Gewitterradar – TheDaimos/gewitterradar
4. WeatherRouter – TheDaimos/weather-router-dev
5. WeatherRouter Private Extensions – TheDaimos/weather-router-extensions-dev
6. Test-Repo-DRA-V2 – TheDaimos/Test-Repo-DRA-V2

Die große Hauptschaltfläche zeigte „1/4 · Sammelinstallation prüfen und vorbereiten“. Die Vorbereitung endete mit der pauschalen Meldung **„Quell- oder Manifestprüfung fehlgeschlagen. Keine Installation gestartet. Status des betroffenen Projekts und Diagnose prüfen.“** Das auslösende Projekt und ein konkreter GitHub-Fehler wurden NICHT angezeigt. Der Nutzer erklärte ausdrücklich, dass ihm dafür **kein Log zur Verfügung steht**. Deshalb MUSS die UI selbst aussagekräftige, sichere Fehlerdaten liefern.

Ein anderer Screenshot zeigt DRA V1 mit fünf Projekten im Sammelupdate, davon **zwei mit Änderungen: Gewitterradar (10) und WeatherRouter (7)**; die übrigen dort ausgewählten Projekte waren aktuell. Die Test-Repo-Auswahl unterschied sich. Es ist daraus NICHT bewiesen, dass der Fehler von Test-Repo, Private Extensions, DRA V2 oder WeatherRouter stammt. Jede feste Zuordnung wäre Spekulation.

**Keine echte V2-Sammelinstallation der sechs Projekte belegt.** Solange eine unklare HA-Transaktion besteht, keinen zweiten Start senden.

### Offene Quellfrage WeatherRouter

Der Nutzer meldete mehrfach, dass WeatherRouter fälschlich nur „main“ anbietet oder aus „main“ versorgt wird. Das Repository TheDaimos/weather-router-dev besitzt laut vorheriger GitHub-Bestandsprüfung eine explizite Empfehlung für **deploy/dev** in deploy-relay-channel.json (auf main). Ab V2 0.1.105/0.1.107 wurden vorläufiges main, manuelle Quelle und eine ältere HA-Vorbereitung voneinander getrennt. Diese Korrekturen sind im GitHub-Code, aber die vollständige tatsächliche HA-Abnahme des Einzel- UND Sammelwegs ist weiterhin offen. Nicht aus einem CI-Erfolg ableiten, dass dieses Problem praktisch vollständig behoben ist.

## 3. Verbindliche neue Erkenntnis: GitHub 0.1.109 ist bereits entwickelt!

Die genaue, auf GitHub gespeicherte technische Antwort muss der nächste Chat VOR Codeänderungen vollständig lesen:

docs/DRA_V2_0_1_109_SAMMELUPDATE_QUELLFEHLER_DIAGNOSE_2026-10-20.md

Direktlink:
https://github.com/TheDaimos/deploy-relay-agent-v2-dev/blob/feature/v2-10-inventory-operation-contract/docs/DRA_V2_0_1_109_SAMMELUPDATE_QUELLFEHLER_DIAGNOSE_2026-10-20.md

**Dort nachgewiesener Programmfehler 0.1.108:**
Die V2-WebSocket-Strecke klärte zunächst alle GitHub-Referenzen und empfohlenen Commits ab, bevor BatchDeployment.prepare() überhaupt einen beobachtbaren HA-Status mit Projektkennung anlegte. Eine dabei auftretende PreflightError wurde nur als allgemeines batch_source_invalid ausgegeben. Die Oberfläche konnte auslösendes Projekt, Phase und GitHub-Zugriffsproblem somit nicht unterscheiden.

**In GitHub 0.1.109 implementiert, CI SUCCESS, HA NOCH UNGETESTET:**
- Bereits vor der GitHub-Referenzprüfung HA-Lesestatus inspecting_sources mit project_key und check_stage=source_reference.
- Bei Abbruch: failed mit Projekt, Prüfphase und bereinigter Fehlerklasse. UI zeigt den auslösenden Eintrag direkt; ein Logexport darf nicht Voraussetzung sein.
- Unterschiedliche Fehlerphasen source_reference, manifest, inventory, local_comparison, version_detection, batch_planning bleiben getrennt.
- Erlaubte, nicht geheime GitHub-Hinweise zu 401/403/404/429 und bekannten Quellfehlern. Rohdaten, Token, private Pfade, beliebige Fehlermeldungen bleiben gesperrt.
- Prüfübersicht und ihre gespeicherten Commit- und Referenzbindungen bleiben unverändert.
- Weitere vorbereitete Freigaben dürfen nicht durch konkurrierende, noch laufende Git-Abfragen unbemerkt ersetzt werden.
- Negative Tests für Status, Zuordnung, Fehlermeldungsbereinigung und konkurrierende Freigaben bereits umgesetzt.

**0.1.109 GitHub-Verifikation:** Code-Basiscommit c80c126af5f4df5fee204701f3296c7a9ca02fe5; Actions 39388573164 SUCCESS. Der aktuelle Zweig-HEAD kann wegen der verbindlichen Übergabe-Dokumentation einen neueren Commit enthalten. HA-Realabnahme ausstehend.

## 4. Entwicklungs-Chronologie seit der älteren Übergabe 0.1.99

Die ursprüngliche umfangreiche Übergabe lesen, aber keine bereits erledigten Punkte neu implementieren:
docs/HANDOFF_DRA_V2_0_1_99_GERAETEUEBERGREIFENDE_INSTALLATION_2026-10-16.md

### 0.1.101 / 0.1.102 – isolierte Testdateien und Gerätewechsel
- Im Test-Repo kann die Zahl synthetischer Testdateien mittels +/- gewählt und die simulierte HA-Wartezeit pro Datei eingestellt werden. Beispiel 6 Dateien × 20 Sekunden = 120 Sekunden künstliche HA-Wartezeit.
- Praktisch bestätigte Git-Erzeugung: Teststand 10 → 11, Commit aab81bfe374d. GitHub-Commit wurde gelesen: fünf neue Testdateien und eine geänderte Statusdatei.
- Praktischer HA-Auftrag bei Gerätewechsel zwischen Android und Desktop: serverseitig running/preflight mit Auftragskennung f89fbdf74bd149c990975f6ffb50d57d, anderer Browser als Beobachter. Dies beweist Annahme/Beobachtung, **NICHT** erfolgreichen Installationsabschluss.
- Git-Testfehler beim Entfernen noch nicht existierender Dateien korrigiert. Wiederherstellung der Scrollposition ergänzt.

### 0.1.103 – veraltete Sperrmeldung
- Falschen Banner „Gesperrter Betrieb“ entfernt, weil HA-Schreibaufträge im V2-Labor längst ausdrücklich zugelassen sind. Sicherheitsfreigaben blieben aktiv.

### 0.1.104 – HA-eigenes Sammelupdate und vorgemerkter Neustart
- Serverseitige Folge von bis zu acht ausgewählten Projekten, feste Commits, Administratorbestätigung, V1-Engine pro Teilinstallation.
- Bei Fehler keine weiteren Projekte starten; erfolgreiche Teilprojekte nicht falsch als rückgängig gemacht darstellen.
- Geräteübergreifende Statusanzeige und ausdrücklich bestätigter gemeinsamer HA-Neustart nach mehreren unabhängig erfolgreichen Updates.
- Laufzeitabhängigkeiten zwischen GR/WR sind nicht vollständig automatisch auflösbar; keine allgemeine atomare Sammeltransaktion.
- Neustart-Vormerkung ist HA-laufzeitgebunden, nicht als dauerhafte Speicherung über Integration-Neuladungen garantiert.

### 0.1.105 – wählbare Projekte und WeatherRouter-Quelle
- Auswahlkästchen je Projekt ausschließlich für den aktuellen Sammellauf, ohne batch_preselect dauerhaft zu ändern; Aufklappbereich behält Zustand.
- Eigenständige Quellen-/Branchabfrage; automatisch vorgewähltes main soll expliziter Projektvorgabe deploy/dev weichen, manuell gewähltes main bleibt zulässig.

### 0.1.106 – Selbstupdates im Sammelupdate
- DRA V1 kann wie im V1-Sammelupdate teilnehmen; DRA V2 ist separat bewusst auswählbar.
- HA sortiert: gewöhnliche Projekte → DRA V1 → DRA V2 zwingend zuletzt. Exklusive V2-Selbstupdate-Schreibphase, genauer Zielpfad-/Repository-/Manifest-Schutz und notwendiger HA-Neustart.
- Kein erfolgreicher V2-Selbstupdate-Realtest belegt. DRA V1 als Rückfallweg beibehalten.

### 0.1.107 – Haupttaste und WeatherRouter altes main
- Echter Fehler: Große Hauptschaltfläche rief zuvor nur read-only batch/preview auf und konnte Stufe 2 niemals erreichen; separater, schlecht sichtbarer Button führte erst zu batch/prepare. Die Haupttaste wurde mit HA batch/prepare und der geführten Stufe 2 verbunden.
- Alte serverseitige main-Vorbereitung darf Empfehlung deploy/dev nicht überlagern. Weiterhin HA-Realtest offen.
- HA-seitige Vorbereitung und Fehlerstatus sollten von anderen Geräten lesbar sein.

### 0.1.108 – verbindliche tabellarische Freigabe
- Zusätzliche Prüfübersicht zwischen HA-Vorbereitung und Installation: **Projekt, installierte Version, neue Version, vollständige 40-stellige Commitkennung, Ref, Änderungen**.
- Verlässlich belegte Versionen aus überprüften V1-Bestands-/Quellmarkern; unbekannte Versionen ausdrücklich „Nicht ermittelbar“ statt Schätzung.
- Prüfkennung über die festgehaltenen Zeilen; neuer Serverstart nur mit review_digest UND ausdrücklichem review_confirm.
- Responsive Tabelle für Desktop/Android/iPad.
- Praktischer HA-Stand 0.1.108 laut Nutzerscreenshot, dort Quellvorbereitung mit sechs Projekten gescheitert.

### 0.1.109 – reale Eingrenzung statt pauschaler Fehlermeldung
- Punkt 3 dieser Übergabe lesen. Projekt-/Prüfschritt-/GitHubfehler direkt in der Oberfläche. CI success; HA noch ohne Praxisbeleg.

## 5. Nützliche Quellmodule und Verträge

- custom_components/deploy_relay_v2_dev/frontend/lab.js – Hauptschaltfläche, Einmalauswahl, Gerätebeobachtung, Prüfübersicht, sichere Fehleranzeige, Version.
- custom_components/deploy_relay_v2_dev/websocket_api.py – Administrator-Schnittstellen, batch/prepare, batch/status, batch/takeover, batch/start, Quellen- und Fehlervertrag.
- custom_components/deploy_relay_v2_dev/batch_installation.py – serverseitige Vorbereitung, feste Commit-Auswahl, Review-Digest, Reihenfolge, Ergebnis, sichere Phase/Fehlerstatus.
- custom_components/deploy_relay_v2_dev/batch_version_summary.py – verifizierte installierte/neue Versionsmarker oder explizit unbekannt.
- custom_components/deploy_relay_v2_dev/remote_source.py – GitHub-Quellabfragen, Refs/Empfehlungen, 401/403/404/429.
- custom_components/deploy_relay_v2_dev/v1_source_bridge.py – eingefrorene, geprüfte V1-Quellbestände.
- custom_components/deploy_relay_v2_dev/server_deployment_jobs.py – tatsächliche HA-Transaktionen, V1-Engine und Neustart-Vormerkung.
- custom_components/deploy_relay_v2_dev/operation_journal.py und v1_engine/ – Journal/Sicherung/Rückfall.
- tests/test_v2_batch_installation.py, tests/test_v2_batch_version_summary.py, tests/test_v2_batch_run_selection_contract.py, tests/test_v2_countdown.js – relevante positive/negative Tests.
- docs/DRA_V2_0_1_104_BATCH_UND_NEUSTART_2026-10-16.md – Kernvertrag.
- docs/DRA_V2_0_1_105_QUELLEN_UND_SAMMELAUSWAHL_2026-10-17.md – Einmalauswahl und Selbstupdate-Nachtrag.
- docs/DRA_V2_0_1_107_SAMMELABLAUF_UND_WR_QUELLE_2026-10-17.md – früherer Stufe-1- und main-Fehler.
- docs/DRA_V2_0_1_109_SAMMELUPDATE_QUELLFEHLER_DIAGNOSE_2026-10-20.md – neuer vorrangiger Fehlerbericht.

**Hinweis:** Ältere Dokumentationsaussagen „Selbstupdates gesperrt“ sind durch die konkretere 0.1.106-Regel überholt; für Sammelupdates sind beide DRA-Projekte nach festem Vertrag wählbar, V2 zwingend zuletzt.

## 6. Priorisierter, möglichst eigenständiger Auftrag für den nächsten Chat

**P0 – GitHub-Stand prüfen und 0.1.109 NICHT doppelt implementieren**
1. HEAD, Version, neue Dokumentation und CI exakt prüfen; 0.1.109-Code lesen.
2. Fehlerschnittstellen auf konkrete Projektkennung, GitHub-Status und bereinigten Fehlertyp überprüfen. Keine Spekulation, welchem Repository auf HA der Zugriff fehlt.
3. Falls ein klarer Codefehler bei der sicheren UI-Anzeige erkennbar ist, im bestehenden Featurezweig mit Regressionstests beheben; sonst zunächst 0.1.109 als nächsten kontrollierten HA-Kandidaten verwenden. Keine Routine-Zwischenversion ohne sachlichen Grund.

**P1 – eine gezielte HA-Quellabnahme statt wiederholter Vollinstallation**
1. Nutzer aktualisiert kontrolliert über DRA V1 auf 0.1.109; Oberfläche und Python-Laufzeit bestätigen. Der Assistent selbst kann keinen tatsächlichen HA-Neustart/Installationsnachweis behaupten.
2. Die bisherige Auswahl mit sechs Projekten NUR vorbereiten; **nicht installieren**. Fehleranzeige soll konkretes Projekt, Prüfphase und sichere Fehlerklasse nennen. Screenshot genügt, Logexport ist NICHT verfügbar.
3. Nur diesen konkreten Blocker beheben (z. B. privates Repository/Tokenscope, GitHub-403/404, ungültige Projekt-Ref, Manifest- oder Zielpfadkonflikt). Vorhandenes Token nicht offenlegen; kein ungeprüftes Aufweichen von Sicherheitsregeln.
4. Danach einmalig die Quellen- und Versionsübersicht prüfen: GR/WR müssen aus beabsichtigten Zweigen/Commits kommen; WeatherRouter ausdrücklich deploy/dev, sofern nicht MANUELL andere Referenz gewählt. Neue und installierte Versionen nur mit beweisbarer Herkunft.
5. Wenn neue HA-Version erneut nicht vorankommt: status/phase/project_code und fehlgeschlagene WebSocket-Strecke nachvollziehen; keinen unsicheren zweiten Start.

**P2 – sichere echte Batch-Abnahme erst nach erfolgreichem P1**
1. Zunächst isoliertes Test-Repo oder klar unabhängige Testprojekte; keine produktiven GR/WR-Änderungen ohne bestätigten Quellstand und Freigabe.
2. Vorher tabellarische Prüfübersicht mit Projekt / installierte Version → neue Version / vollständiger Commit / Ref / Dateiänderungen; explizite Checkbox-Bestätigung, Prüfsummenbindung, keine unsichtbare Stufe.
3. Ein echter HA-Auftrag und V1-Journal, klarer Abschluss/Fehlerstatus und Sicherung/Rückfall je Teilprojekt; Doppelstart bei verlorener Quittung verhindern.
4. Desktop, Android, iPad: Beobachterstatus ohne Projektneuladen, Übernahme mit Bestätigung, Scroll-/Aufklappzustand stabil.
5. DRA-Selbstupdate als letzte Teilinstallation erst nach separater und nachvollziehbarer Realfreigabe; DRA V1 bis dahin bewährter Rückfall.
6. Zentral vorgemerkten, ausdrücklich bestätigten Neustart prüfen und nicht mehr Neustarts anfordern als fachlich notwendig.

## 7. Bedingungen für eine tatsächliche Abnahme

- GitHub-HEAD und HA-Laufzeit/Oberfläche exakt gleich, bestätigte Version nach Neustart.
- Jede ausgewählte Quelle korrekt und aktuell; insbesondere WeatherRouter deploy/dev nicht von altem main verdrängt.
- Bei GitHub-Fehler konkrete Projekt- und Phase-Erklärung sichtbar; keine Token-/Dateipfad-Leaks; kein Installationsstart nach gescheiterter Vorbereitung.
- Validierte Tabelle zeigt exakte feste Commitkennung und verifizierte oder als unbekannt markierte Versionswerte; für die exakt geprüfte Kombination erforderlich.
- Einmalige ausdrückliche Freigabe; keine Freigabe durch reine Auswahl, Browserwechsel oder verlorene WebSocket-Antwort.
- Serverseitige Transaktion mit korrelierbarer Auftragskennung, Audit/Journal und tatsächlichem Installations- und Verifikationsabschluss.
- Gestoppte Teilinstallation führt nicht zu späteren Teilinstallationen, lässt vorherige Erfolge jedoch korrekt bestehen.
- Sicherer HA-Neustart/Frontendaktualisierung und korrekte Geräteüberwachung.
- Keine HA-Realabnahme ohne tatsächlich ausgeführte und korrelierte Praxisbelege.

## 8. Kommunikation, Dokumentation, Prompt für den nächsten Chat

Vollständige, überprüfbare technische Antworten und eine neue Hand-off-Datei im selben privaten Repository speichern und auf GitHub zurücklesen. Im Nutzerchat klar zwischen „im Code“, „CI bestanden“ und „auf HA real getestet“ unterscheiden. Nutzer arbeitet allein, deutsch ohne Denglisch, bevorzugt einen einzigen kopierbaren Folgeprompt und konkrete GitHub-Direktlinks. Kein unnötiges Nachfragen oder pauschales „fertig“, wenn wesentliche Realitätstests noch ausstehen.

**Weiterführungsprompt:**

Bootstrap Daimos – DRA V2 0.1.109 DEV. Lies im privaten Repository TheDaimos/deploy-relay-agent-v2-dev ausschließlich auf feature/v2-10-inventory-operation-contract vollständig docs/HANDOFF_DRA_V2_0_1_109_SAMMELUPDATE_DIAGNOSE_REALABNAHME_2026-10-20.md sowie die dort verknüpften Originaldokumente. Verifiziere den Code-Basiscommit c80c126af5f4df5fee204701f3296c7a9ca02fe5 sowie den neuesten Zweig-HEAD und die zugehörigen CI-Prüfläufe; prüfe sämtliche offenen Punkte eigenständig. Auf HA ist zuletzt nur 0.1.108 belegt, 0.1.109 nicht realabgenommen. Oberste Priorität: die blockierte Sammelvorbereitung mit sechs Projekten ohne vorausgesetzten Logexport über die neue projekt- und phasenbezogene 0.1.109-Fehlerdiagnose aufklären; WeatherRouter-Referenz deploy/dev und die verbindliche Versions-/Commit-Prüfübersicht verproben. V1-Sicherheit, HA als alleinigen Ausführer, Einmalbestätigungen, Versionsprüfung und Rückfallschutz strikt bewahren. Keine unbewiesene Installations- oder Neustartfreigabe, keine unnötigen Zwischenversionen und keine Schreibzugriffe außerhalb des genannten Entwicklungszweigs. Bei weiteren Codekorrekturen alle positiven/negativen Tests samt GitHub-CI ausführen und den vollständig dokumentierten Stand wieder als Markdown im Featurezweig speichern.

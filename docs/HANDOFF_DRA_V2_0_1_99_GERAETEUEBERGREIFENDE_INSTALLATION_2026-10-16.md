# Verbindliche Chatübergabe – DRA V2 DEV, Gerätewechsel und Installationsstart
**Datum:** 16.10.2026
**Projekt:** Deploy Relay Agent V2 (DRA V2 DEV)
**Repository:** TheDaimos/deploy-relay-agent-v2-dev
**Einziger beschreibbarer Entwicklungszweig:** feature/v2-10-inventory-operation-contract
**GitHub-Code laut Prüfung:** 0.1.99 DEV, Commit 592684a6b2615e2a94ba6de209ad183f389dc8f0
**Letzte bestätigte HA-Installation:** 0.1.97 DEV (Desktop und Android); 0.1.98 und 0.1.99 sind NICHT als auf HA installiert/verprobt belegt.
**GitHub-Actions-Prüfung:** Run 38875674715 – SUCCESS zum Code-Commit 592684a6b261.
**Status:** Automatisierte Prüfungen erfolgreich; geräteübergreifende echte Installationsabnahme weiterhin OFFEN.

> Diese Übergabe hält den tatsächlichen Projekt- und Fehlerstand fest. Der nächste Chat muss die jüngste GitHub-Version und den HA-Iststand erneut getrennt feststellen. Keine bloße GitHub-Versionsnummer als erfolgreich installiert ausgeben.

## 1. Verbindlicher Arbeitsauftrag und Sicherheitsgrenzen

DRA V2 soll DRA V1 künftig ersetzen, nicht parallel eine neue Deployment-Engine entwickeln. Kernprinzip: Die bewährte V1-Engine für feste Quell-Commits, Bestandsprüfung, Staging, Sicherung, Installation, Hash-Verifikation, Rückfall und Journale wird serverseitig weiterverwendet. Home Assistant besitzt und trägt ALLE Aufträge. Desktop, Android, iPad/iOS sind austauschbare Bedien-/Beobachtungsgeräte; ein Browserabbruch beendet keine begonnene HA-Installation.

**Nur im Featurezweig feature/v2-10-inventory-operation-contract des Repositories TheDaimos/deploy-relay-agent-v2-dev schreiben.** DRA V1 / TheDaimos/deploy-relay-agent-pub, alle anderen Repositories, Projekt-Log-Archiv, main, Veröffentlichung und bestehende PR #2 READ ONLY; keine Merge-, Release-, oder Schreibaktionen dort. V1 darf lediglich als vorhandener Auslieferungsweg zur Installation der DEV-Version durch den Nutzer dienen. Keine HA-Installation, kein HA-Neustart oder produktive Bestätigung durch den Assistenten. Selbstinstallation von DRA V2 bleibt gesperrt. Fehler in der Schreiblogik niemals mit Umgehung von Administratorfreigabe, Zielschutz, unveränderlicher Commit-Bindung, Verfallszeit, Journal- und Rückfallschutz beheben.

**Arbeitsstil:** Möglichst selbständig und zügig mehrere zusammenhängende Fehler ursächlich korrigieren; negative/positive Tests und CI durchführen, anschließend nur eine gebündelte DRA-Bereitstellung und einen aussagekräftigen HA-Praxistest statt vieler Neustart-Zyklen. Kein blindes Neusenden einer unsicheren Installationsanforderung.

## 2. Technischer Architekturstand

### Serverseitige Bausteine
- custom_components/deploy_relay_v2_dev/deployment_coordinator.py: kurzlebige, serverseitige Installationsvorbereitungen, feste Commits, einmalige Bestätigungskennung, controller-Leasing, ausdrückliche Übernahme. Vorbereitungslaufzeit seit 0.1.97: 900 Sekunden (= 15 Minuten).
- custom_components/deploy_relay_v2_dev/server_deployment_jobs.py: HA-eigene Installationsaufträge, V1-Engine, bis zu vier voneinander unabhängige Aufträge und Zielpfad-Reservierungen, Protokollierung und Idempotenz/Einmalaufträge.
- custom_components/deploy_relay_v2_dev/v1_source_bridge.py und v1_engine/: Wiederverwendung V1-Manifest-/Inventar-/Vorschau-/Transaktionslogik.
- custom_components/deploy_relay_v2_dev/websocket_api.py: nur für HA-Administratoren zugängliche Schnittstellen zu Quellprüfung, deployment/prepare, deployment/prepared_status, deployment/control, deployment/sessions, deployment/start, deployment/status und Neustart.
- custom_components/deploy_relay_v2_dev/frontend/lab.js: UI, Projektanzeige, Anzeige von Aufträgen, Wiederverbindung, aktive/Beobachter-Bedienung, Bestätigungsdialog.
- Eigenes V2-Transaktionsverzeichnis: /config/deploy_relay_v2_dev; nicht V1-Daten/Transaktionen bearbeiten.

### Gewünschte Sitzungssemantik
1. Desktop prüft Projekt und bereitet festes Update vor.
2. Android/iPad ruft denselben HA-Vorbereitungsstand ab, ohne eine zweite Quellprüfung oder Vorbereitung zu verlangen.
3. Geräte dürfen den Auftrag beobachten, aber pro Projekt nur EINE aktive Bedienung haben; eine ausdrückliche Übernahme wechselt diese.
4. Das übernehmende Gerät darf nach eigener ausdrücklicher Bestätigung den vorbereiteten Serverauftrag starten; keine automatische Übertragung einer Benutzerbestätigung.
5. Server übernimmt komplette Installation und Fortschritt unabhängig vom Bediengerät; andere Geräte zeigen denselben tatsächlichen Auftrag. Keine doppelte Installation bei verlorenem WebSocket-Ergebnis.
6. Geräte ohne geladenen Projektbestand oder ohne aktuelle allgemeine HA-Statusantwort müssen dennoch eine aktive HA-Installation sicher als Lesestatus erkennen.
7. Nach Abschluss korrekter Hinweis auf Frontend-Aktualisierung oder HA-Neustart; keine automatische Neuanforderung und keine irreführenden Erfolgsmeldungen.

## 3. Verifizierte Entwicklungs- und Realtest-Chronologie

### Früherer bewährter Realtest
Mit DRA V2 0.1.91 gelang eine echte produktive Gewitterradar-Installation auf HA: Gewitterradar 4.11.78 aus deploy/dev, Commit d6fad7e660de; sieben geänderte und 136 unveränderte Dateien. Erforderlicher HA-Neustart und erneute Vorschau waren anschließend erfolgreich. Dies belegt grundsätzlich die V1-basierte Installationsstrecke, nicht den neuen geräteübergreifenden Start.

### V2 0.1.94 – Quellprüfung auf zwei Geräten
Am 15.10.2026 zwei private Diagnoseexporte, Desktop und Android, jeweils 0.1.94 und derselbe Quellprüfauftrag 26474cb318c94ec283d1135b034ca313 mit Erfolg, Laufzeit 2417 ms, Quellen verifiziert; identisches Ergebnis auf Server. Daraus allein ergibt sich noch keine vollständig synchrone Bedienoberfläche.

### V2 0.1.95/0.1.96 – Sitzungsmanager
Serverseitige Leseabfrage vorbereiteter Pläne, aktive Bedienung pro Projekt, Beobachtung und Übernahme, 45-Sekunden-Controller-Lease mit wiederholter Erneuerung. Vorbereitete Installation ist unabhängig vom lokalen Browser; CI grün. Beim ersten Android-Praxistest unter 0.1.96 wurde zwar die Bedienung übernommen, jedoch zunächst der Vorbereitungsdialog nicht wiederhergestellt; Android musste erneut vorbereiten.

### V2 0.1.97 – Vorbereitungs-Wiederherstellung
Fix: gültiger HA-gehaltener Installationsplan soll auch bei abweichender/staler lokaler Vorschau vorgehen, Vorbereitungsfrist von 120 auf 900 Sekunden. Bereits im Desktop-Layout kompakter Controllerstatus neben Überschrift „Deployment“. CI grün (Run 38870553027, Commit bd292bf2e44591cab058b4bcc2116d16ac7bcb59).

**Realtest Freitag 16.10.2026, DRA V2 HA 0.1.97:**
- Desktop: Gewitterradar ausgewählt; lokale Version 4.11.82, Git-Quellversion 4.11.83; Branch deploy/dev; festgehaltener Quellcommit 8149a043215f73c7caf500f6c109ffd3b638d52d; **7 Dateien neu, 7 geändert, 0 entfernt, 137 unverändert**.
- Desktop: Nach Vorschau und serverseitiger Vorbereitung erfolgreich „2/4 · Installation vorbereitet“, Schaltfläche „Ja, Update installieren“ sichtbar.
- Zweites Gerät: Im Beobachterzustand derselbe vorbereitete Commit und dieselben Dateiänderungen sichtbar, keine erneute Vorbereitung erforderlich. Controller-Blau = „Anderes Gerät steuert · Beobachtung“.
- Android: Auf „Übernehmen“ geklickt und bestätigt; Controller-Anzeige wechselte auf Grün („Dieses Gerät steuert den Vorgang“). Schaltfläche „Ja, Update installieren“ blieb sichtbar. **Geräteübergabe der Vorbereitung und aktive Kontrolle damit PRAKTISCH BESTANDEN.**
- Android: Auf „Ja, Update installieren“ geklickt. Danach verschwand die Vorbereitung, Anzeige fiel auf „2/4 · Installation vorbereiten“ zurück. Meldung: **„Auftragsannahme nicht bestätigt. Bitte zuerst Serverstatus aktualisieren.“**
- Das beweist NICHT, dass eine Installation stattfand, und NICHT zwingend, dass die Installation fehlschlug. Eine verlorene oder verweigerte Serverquittung und eine bereits angenommene HA-Transaktion mussten unterschieden werden.
- Währenddessen iPad mit DRA V2 0.1.97 geöffnet: angezeigtes „Kein aktives Projekt“, Python-/HA-Laufzeit „Noch nicht ermittelt“, Quellstand nicht geprüft und im sichtbaren Bereich kein laufender Installationsstatus. Das war unzureichende, projektauswahlabhängige Beobachtung, kein Beweis, dass kein HA-Auftrag läuft.
- Nutzer vermutete später, die bestätigte Gewitterradar-Installation sei nicht durchgeführt worden. **Noch kein eindeutiger serverseitiger Installationsbeleg vorliegend.** Nicht behaupten „Installiert“, „fehlgeschlagen“ oder „Rollback“, bevor Journal/Audit/Status/realer Gewitterradar-Versionsstand geprüft sind.

### Private Git-Exporte am 16.10.2026
Archiv-Repository (READ ONLY): TheDaimos/Project-Log-And-Export.
Gesuchter Pfad: exports/deploy-relay-agent-v2/2026-10/diagnostics/.
Bei letzter Prüfung war dort sichtbar:
2026-10-16T08-40-06Z__deploy-relay-agent-v2__0.1.97__diagnostics__8b5c27e53624aab7edbaf4233f0d3ddd.json
Inhalt: source_diagnostic captured_at 2026-10-16T08:39:27Z, status success, sources_verified true, reason none, stage target_claims, 3196 ms, run_id d81e213b4fda4004a01066670e421b35. **READ_ONLY_TEST / V2-SOURCE-PREVIEW; installation_enabled=false; dies ist KEIN Installationsnachweis.**
Nutzer meldete ausdrücklich ZWEI Exporte. In dem bisher geprüften Diagnoseverzeichnis wurde nur einer mit Datum 16.10. gefunden; zweiten noch auf anderen Archivpfaden, Exporttypen oder zeitversetzt prüfen. Nicht behaupten, dass es ihn nicht gibt. Ggf. GitHub-Archiv-Such-/Verzeichnisabfrage ausweiten; keine Schreibrechte.

## 4. Neuerer GitHub-Stand seit dem 0.1.97-Realtest – unbedingt zuerst prüfen

**Am 16.10.2026 erneut GitHub-Abfrage ausgeführt:**
- Featurezweig aktuell Commit 592684a6b2615e2a94ba6de209ad183f389dc8f0.
- const.py, manifest.json, frontend/lab.js zeigen 0.1.99 DEV.
- GitHub Actions „DRA V2 public validation“, Run 38875674715, completed / SUCCESS auf diesem Code-Commit.
- 0.1.98 und 0.1.99 entstanden bereits nach der dem Nutzer bekannten 0.1.97-Fehlersituation. **Diese Fortschritte nicht zurücksetzen oder parallel neu implementieren; zuerst vorhandene Entwicklung vollständig sichten.**

### Entwicklungsblock 0.1.98
Commit-Folge: 5e6de4f6de85 (unklare Annahme mit HA-Auftrag abgleichen), 819e03599185 (Tests zum verlorenen WebSocket-Ergebnis; Doppelstart sperren), 258f970d2a67 (sichere Ablehnungsgründe anzeigen), weitere Versionsdateien bis 95bad005d6a0.
Ziel und implementierte Richtung: Bei verlorener Bestätigung den serverseitigen Auftragszustand LESEND abfragen, vorher vorhandene Auftragskennungen unterscheiden, keinen zweiten Start blind senden und unklare Annahme als unklar markieren; vorbereiteten Stand nicht voreilig vergessen. Bei eindeutigem Fehler sicheren, eingegrenzten HA-Ablehnungsgrund anzeigen. Praxistest fehlt.

### Entwicklungsblock 0.1.99
Commit-Folge: e733075ffbf7 (Beobachtung von Projektauswahl und allgemeinem Status entkoppeln), f33432c1811e (sichere Projektnamen), d79abbdba8f0 (HA-Live-Installationsanzeige oberhalb der Projektauswahl), 93f3c553e006 (iPad-Test bei leerem Projekt/nicht ermittelter HA-Laufzeit), Versionserhöhung 925b29f6ce3b bis 6e26e61d822e, letzte Verbesserung 592684a6b261 (begrenztes Beobachter-Abfrageintervall).
Ziel und implementierte Richtung: Ein anderes Gerät zeigt aktive HA-Installationen lesend selbst dann, wenn keine Projektauswahl oder Versionen-/Projektinitialisierung stattgefunden hat. Globale Leseanzeige, aus sicherem HA-Status und ohne unautorisierte Steuerung. Praxistest fehlt.

**WICHTIG:** GitHub-CI kann funktional grün sein, ohne dass das real gemeldete Problem auf Android/iPad abgenommen ist. Aktuell 0.1.99 ist bereitliegender Code, nicht die nachgewiesen installierte HA-Version.

## 5. Hauptproblem für den neuen Chat

**P0 – tatsächlicher Installationsausgang und verlässliche Quittierung:**
1. Ohne erneute Installation den tatsächlichen Gewitterradar-Stand feststellen: lokal 4.11.82 oder 4.11.83? HA-Auftragsliste, V2-Transaktionsjournal und Audit, ggf. private Exporte. Erneut keine Installation bestätigen oder HA neu starten, solange serverseitiger Zustand ungeklärt ist.
2. Im Code den Ablauf UI _confirmInstallation(), HA WebSocket deployment/start, DeploymentCoordinator.confirm, ServerDeploymentJobs.start_verified, UI _pollInstallation() und Fehlermeldungs-/Verbindungsverlustzweige zusammen prüfen.
3. Herausfinden, ob Backend vor Aufnahme verweigert, HA-Auftrag aufgenommen aber Quittung verloren, oder Anzeige nach Empfang falsch war. Keine Ablehnung anhand der pauschalen Client-Meldung behaupten. Unterschied zwischen Start, Annahme, Fortschritt, terminalem Abschluss und Persistenz klar machen.
4. Neueren Code 0.1.98/0.1.99 zunächst vollständig berücksichtigen und Regressionstests durchlaufen lassen. Bei echtem Restfehler fixen, Ursachen dokumentieren, Doppelausführung strikt verhindern.
5. Sicherheits-Gates (Admin, Controller, explizite Bestätigung, genau ein gültiger Challenge, fixer Commit, Ziel-Exklusivität, V1-Journal/Backup/Rollback) unangetastet lassen.

**P1 – iPad/Beobachterfortschritt:** Auf iPad und inaktiver Desktop-Sitzung den tatsächlich HA-eigenen Installationszustand prominent, unabhängig von Projektauswahl, Initialisierung und Browser-Fokus zeigen. Status idealerweise mit Projektname, Auftragskennung, Stufe, Fortschritt, Ergebnis, Änderungszahl und etwaigen Folgemaßnahmen. Keine Erfolgsmeldung aus historischen Audits als laufendes Update ausgeben. Serverstatus nicht erfunden, nicht auf „Kein aktives Projekt“ zurücksetzen.

**P2 – Oberfläche:** Desktop: kompakter Status neben „Deployment“ umgesetzt, visuell gut. Android: volle Breite in separater Zeile; Status „Geräteübergreifende Bedienung“ optisch weiter veredeln; Grün aktive Bedienung, Blau Beobachtung, Gold Übergabe/besonderer Aufmerksamkeit. Gut erreichbare Übernahme, eindeutige Textzustände. Querformat iPad responsiv; keine unnötigen Vollbreiten-/Leerflächen. Kein kosmetischer Umbau, der P0 verzögert.

## 6. Konkrete technische Fundstellen für die Fortsetzung

- GitHub Quelle: TheDaimos/deploy-relay-agent-v2-dev, Branch feature/v2-10-inventory-operation-contract.
- Versionen: custom_components/deploy_relay_v2_dev/const.py, manifest.json, frontend/lab.js, JS-Versionstests.
- HA WebSocket: custom_components/deploy_relay_v2_dev/websocket_api.py, async_install_start / async_install_status / async_install_control / async_install_prepared_status.
- Controller: deployment_coordinator.py, control / require_controller / pending_status / confirm.
- Echte HA-Aufträge: server_deployment_jobs.py, start_verified / get / latest / list.
- Frontend: frontend/lab.js, _confirmInstallation, _pollInstallation, _restoreServerPreparation, _syncController, _refresh und globale Beobachteranzeige.
- Prüfungen: tests/test_v2_countdown.js; tests/test_v2_deployment_coordinator.py; tests/test_v2_server_deployment_jobs.py; tests/test_v2_parallel_deployment.py; tests/test_v2_40_security_isolation.py und übrige CI-Suite.
- Aktuelle Entwicklung folgt nachweislich bereits 0.1.98-/0.1.99-Änderungen. Vor jeder neuen Modifikation Featurezweig-HEAD nochmals prüfen, damit keine neueren Arbeiten überschrieben werden.
- Frühere Architektur- und Beschleunigungsregeln: AGENTS.md; docs/AI_CONTEXT.md (historisch teilweise veraltet), docs/V2_ROADMAP.md.

## 7. Priorisierter autonomer Fortsetzungsauftrag

1. **GitHub-Stand/CI und private Exporte erneut prüfen.** 0.1.99 am geprüften HEAD mit grünem CI, HA aber noch 0.1.97; zweite Nutzer-Exportdatei nach Möglichkeit finden.
2. **Code-Audit zum 0.1.97-Android-Fehler** auf Basis der bereits umgesetzten Nachbesserungen 0.1.98 und 0.1.99; nicht vorzeitig neue Architektur bauen.
3. **Gezielte Negativ-/Integrationstests**: verlorene WebSocket-Startantwort vor/nach HA-Annahme; serverseitige Ablehnung; Timeout; doppelte Bestätigung; abgelaufene Vorbereitung; anderer Controller; Gerätewechsel; Browser neu laden; fehlende Projektauswahl/iPad; HA-Laufzeitversion noch nicht initialisiert; eindeutige laufende und terminale Aufträge; Ausfall des Statusabrufs.
4. Falls notwendig weitere Code-Korrekturen **nur im freigegebenen V2-Featurezweig** bündeln, Versionsfolge sauber erhöhen, CI SUCCESS verifizieren.
5. **Ein einziges sinnvolles DRA-V1-Update** für die nächste HA-Realabnahme bereitstellen, keinen unnötigen Wechsel alle paar Minuten. Keine Selbstinstallation durch Assistenten.
6. **Abnahmekette:** Desktop Gewitterradar mit tatsächlichen Dateiänderungen und festem Commit prüfen/vorbereiten → Android beobachtet denselben Plan → aktive Übernahme → genau eine ausdrückliche Startbestätigung → serverseitige Auftragskennung tatsächlich bestätigt → Desktop/iPad zeigen denselben HA-Fortschritt und Abschluss → erst danach gegebenenfalls vom Nutzer bestätigter HA-Neustart → erneute Dateiversionsprüfung. Falls Update nicht mehr vorhanden: isoliertes Testprojekt verwenden und das Ziel strikt prüfen.
7. **Vollständig protokollieren:** Git-Code/CI vs. auf HA installierte Version stets getrennt; exakte Ursache und nachgewiesene Prüfungen dokumentieren; den Nutzer nur zu nötigen Realtests hinzuziehen. Offene Risiken ausdrücklich nennen.

## 8. Antworten, die ausdrücklich zu vermeiden sind

- „Die Installation lief“ allein wegen Klick auf „Ja, Update installieren“.
- „Die Installation schlug fehl“ allein wegen „Auftragsannahme nicht bestätigt“.
- „0.1.99 wurde auf HA installiert“, nur weil GitHub 0.1.99 und CI grün zeigt.
- „Zwei Exporte ausgewertet“, solange nicht tatsächlich beide geöffnet wurden.
- „iPad hat keinen Auftrag“, nur weil in der UI „Kein aktives Projekt“ steht.
- Eine zweite schreibende Anfrage schicken, solange der alte Auftragsstatus nicht verifiziert ist.
- Eigenmächtig V1, andere Repositories, main, PR #2 oder das private Archiv beschreiben.
- Viele unnötige DRA-/HA-Updatezyklen und Rückfragen statt eigenständiger Entwicklung.

## 9. Empfohlener Bootstrap-Prompt für den neuen Chat

> **Bootstrap: Daimos – DRA V2 DEV 0.1.99 / Geräteübergreifende Installation**
>
> Lies zuerst vollständig diese private Übergabe im Repository **TheDaimos/deploy-relay-agent-v2-dev**, Branch **feature/v2-10-inventory-operation-contract**, Datei **docs/HANDOFF_DRA_V2_0_1_99_GERAETEUEBERGREIFENDE_INSTALLATION_2026-10-16.md**. Prüfe dann den aktuellen Featurezweig, Code und CI erneut; dokumentierter Stand ist 0.1.99 DEV, Commit 592684a6b261, CI Run 38875674715 SUCCESS. Zuletzt auf Home Assistant praktisch bestätigt ist ausschließlich DRA V2 0.1.97.
>
> Hauptfehler: Der Desktop bereitete Gewitterradar 4.11.82 → 4.11.83, Commit 8149a043215f73c7caf500f6c109ffd3b638d52d vor (7 hinzugefügt, 7 geändert). Android konnte den vorbereiteten Plan sehen und die Bedienung erfolgreich übernehmen. Nach „Ja, Update installieren“ erschien aber „Auftragsannahme nicht bestätigt“; eine erfolgreiche oder fehlgeschlagene tatsächliche Installation ist nicht nachgewiesen. Das iPad zeigte währenddessen „Kein aktives Projekt“, HA-Laufzeit unbekannt und keine brauchbare Installationsüberwachung. Im privaten Archiv befindet sich zumindest ein 0.1.97-Quellprüfexport vom 16.10., der KEIN Installationsnachweis ist; Nutzer meldet zwei Exporte.
>
> Beachte, dass im GitHub-Zweig bereits 0.1.98 (unklare Auftragsannahme, keine Doppelübermittlung) und 0.1.99 (projektunabhängige HA-Beobachtung) implementiert und CI-grün sind; keine parallele Neuentwicklung und keine Rücksetzung. Arbeite möglichst eigenständig weiter: tatsächlichen Ausgang so weit möglich klären, Implementierung kritisch prüfen, Sicherheits-/Negativtests ergänzen, etwaige Restfehler beheben, CI abnehmen und erst danach eine gebündelte DRA-Version zur Benutzerinstallation bereitstellen. Nur der genannte V2-Featurezweig ist beschreibbar. DRA V1, andere Repositories, main, PR #2 und das private Archiv READ ONLY. Keine eigenmächtige HA-Installation/Neustart. Nächsten HA-Realtest so planen, dass Desktop vorbereiten, Android übernehmen/installieren und iPad/Desktop serverseitig beobachten können – mit möglichst nur einer Installation und einem Neustart.
>
> Arbeite ohne Routine-Rückfragen. Melde tatsächliche, belegbare Code-/CI-/HA-Stände getrennt und fordere nur unabdingbare Gerätehandlungen an.

---

**Verbindliche Kernbotschaft:** Der Softwarestand 0.1.99 hat bereits code- und CI-geprüfte Verbesserungen gegenüber der fehlgeschlagenen 0.1.97-Abnahme. Die HA-Praxisabnahme der echten Auftragsannahme und vollständig geräteübergreifenden Anzeige steht noch aus. Neue Änderungen müssen von diesem neueren Code ausgehen, nicht von 0.1.97.

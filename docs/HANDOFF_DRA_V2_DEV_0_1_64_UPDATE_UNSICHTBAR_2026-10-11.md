# AUSFÜHRLICHE CHATÜBERGABE – DRA V2 DEV 0.1.64 / Update in DRA V1 nicht sichtbar

**Erstellt:** 11.10.2026, nach umfangreicher Fortsetzung des DRA-V2-Entwicklungschats  
**Projekt:** Deploy Relay Agent V2 (DRA V2 DEV; isoliertes Home-Assistant-Testlabor)  
**Repository:** \`TheDaimos/deploy-relay-agent-v2-dev\` (**öffentliches Entwicklungsrepository**)  
**Einziger zur Bearbeitung freigegebener Zweig:** \`feature/v2-10-inventory-operation-contract\`  
**Letzter vor der Übergabe bestätigter Codecheckpoint:** \`e20a12dbb20ce91e83dae247b02b8352e39be59c\`  
**Letzter erfolgreicher zugehöriger GitHub-CI-Lauf:** \`38148357701\`, Status **SUCCESS**  
**Dateiversion:** \`0.1.64\` in \`const.py\` **und** \`custom_components/deploy_relay_v2_dev/manifest.json\` auf dem Featurezweig  
**Verbindliche aktuelle Benutzermeldung:** „**Ich kann das Update via DRA gerade nicht finden**.“  
**Status 0.1.64:** Quellcode/CI vorhanden; **nicht als in Home Assistant installiert bestätigt**, HA-Realabnahme der Git-Export-Korrektur **OFFEN**.  
**Status 0.1.63:** Benutzer zeigte erfolgreichen echten Gewitterradar-Quelltest und serverseitige Auftragshistorie, aber **fehlgeschlagenen privaten Git-Export**.  
**PR #2:** OPEN, **DRAFT**, **UNMERGED** – unverändert lassen.

> Diese Übergabe ist die maßgebliche neue Fortsetzung und **ersetzt nicht** die technischen Altdokumente, sondern zeigt die notwendigen Leseverweise. Der erste Arbeitsschritt des nächsten Chats ist das **Update-Sichtbarkeitsproblem der DRA-V1-Oberfläche**; nicht G3, G4, G5 oder ein automatischer Rückfall. Keine unaufgeforderte Installation, kein HA-Neustart.

---

## 0. Pflichtstart für den neuen Chat – Reihenfolge einhalten

1. GitHub: \`TheDaimos/project-defaults/START_HERE.md\` **vollständig** lesen und globalen Daimos-Bootstrap/Erinnerungsschutz beachten.
2. Im Repo \`TheDaimos/deploy-relay-agent-v2-dev\`, **Ref \`feature/v2-10-inventory-operation-contract\`**, zuerst \`AGENTS.md\`, dann \`docs/AI_CONTEXT.md\` vollständig lesen.
3. **Diese Übergabe** vollständig lesen.
4. Danach bei Bedarf die historische große Übergabe \`docs/HANDOFF_DRA_V2_DEV_0_1_53_2026-10-11.md\`, \`docs/V2_ROADMAP.md\`, \`docs/V2_GATES_NACH_SOURCE_PREVIEW_REALABNAHME_2026-10-11.md\`, \`docs/V2_PRIVATE_GIT_EXPORT_RECOVERY_0_1_64_2026-10-11.md\`, \`docs/V2_G2_20_PERSISTENTE_AUFTRAGSHISTORIE_0_1_63_2026-10-11.md\` öffnen.
5. Aktuellen HEAD, Version **in beiden** Manifest/Const-Dateien, CI und PR #2 **erneut** aus Git verifizieren; nichts aus der Erinnerung als neueste Commit-ID ableiten.
6. **WICHTIG:** Benutzer arbeitet **allein** und vor allem mobil. Deutsch ohne unnötiges Denglisch, kopierbare Kennungen/Pfade, **höchstens eine konkrete HA-Handlung pro Antwort**. GitHub-Arbeiten möglichst selbst erledigen, HA-Handlung nur bei echtem Bedarf.

### Unverrückbare Repository- und Datenschutzgrenzen

- **Schreibbar:** nur \`TheDaimos/deploy-relay-agent-v2-dev\` auf **\`feature/v2-10-inventory-operation-contract\`**, nach Prüfung der jeweiligen Änderung.
- **Nicht ändern:** DRA V1 DEV/PUB, DRA V2 PUB, DRA V2 DEV \`main\`, WeatherRouter, Gewitterradar, andere Produkte, privates Zentralarchiv. **PR #2 nicht zusammenführen.**
- **Echte Logs, HA-Diagnosen, Exporte** ausschließlich nach \`TheDaimos/Project-Log-And-Export\` (**privat**), für DRA V2 grundsätzlich unter \`exports/deploy-relay-agent-v2/<JJJJ-MM>/diagnostics/\`. **Keinerlei echte Diagnoserohdaten in dieses öffentliche DRA-V2-Quellrepository.**
- Keine Zugangsdaten, privaten Git-Inhalte, internen IPs, Dateisystemoriginale oder Token-Vollwerte in Logs, Tests, öffentlichen Dokumenten oder Screenshots.
- **Kein V2-Installieren, -Sichern, -Rücksichern, -Schreiben, -Sammelupdate, -Neustart oder Selbstupdate.** Die V2-Oberfläche hat die vier Stufen, aber nur Stufe 1 (reine Quellvorschau) ist tatsächlich aktiviert und geprüft.
- **Keine eigenständigen Home-Assistant-Installationen oder Neustarts.** Der Nutzer aktualisiert das isolierte V2-DEV-Testlabor manuell mit dem stabilen **DRA V1**.
- **CI grün ≠ HA-Realtest ≠ Freigabe zum Schreiben.**

---

## 1. NEUESTE BLOCKADE – DRA V1 zeigt 0.1.64 nicht als Update

### 1.1 Vom Benutzer gemeldet

Nachdem 0.1.64 fertig, versioniert, dokumentiert und CI-grün war, wurde der Nutzer gebeten, DRA V2 DEV über DRA V1 auf 0.1.64 zu aktualisieren. Seine unmittelbare Rückmeldung: **„Ich kann das Update via DRA gerade nicht finden“**. Danach fordert er wegen vollem Chat die detaillierte Übergabe.

**Noch kein Screenshot der DRA-V1-Projektauswahl oder Quellref zu diesem konkreten Problem; DRA-V1-Konfiguration auf der laufenden HA-Instanz ist daher nicht verifiziert.** Keine Updateerkennung oder erfolgreiche Installation behaupten.

### 1.2 NEUER GitHub-Befund, bereits unabhängig geprüft (11.10.2026)

- \`TheDaimos/deploy-relay-agent-v2-dev\` hat **Standardzweig \`main\`**.
- \`main\` enthält **weder** \`custom_components/deploy_relay_v2_dev/manifest.json\` **noch** \`deploy-relay.json\`; Git-Baumprüfung (74 Einträge) und gezielter Dateiabruf bestätigen das.
- Der **Featurezweig \`feature/v2-10-inventory-operation-contract\`** enthält **beide** Dateien. Sein Integrationsmanifest meldet **\`0.1.64\`**, \`const.py\` meldet **\`0.1.64\`**, das Projektmanifest nennt \`TheDaimos/deploy-relay-agent-v2-dev\` und die einzige Gruppe \`custom_components/deploy_relay_v2_dev\` → \`/config/custom_components/deploy_relay_v2_dev\`.
- Der genaue Quell-HEAD **vor dieser Übergabedatei**: \`e20a12dbb20ce91e83dae247b02b8352e39be59c\`, GitHub-CI \`38148357701\` **SUCCESS**.
- **Der fehlende Standardzweig-Inhalt ist ein plausibler und reproduzierbarer Erklärungsfaktor, falls DRA V1 den Standardzweig abfragt.** Er beweist *nicht*, dass die installierte DRA V1 tatsächlich den Standardzweig benutzt. Ältere V2-DEV-Versionen wurden erfolgreich über V1 installiert, sodass eine falsche/vergessene Ref-Auswahl, veralteter Prüfcache, Projektzuordnung oder eine andere V1-Quellversionsregel erst zu untersuchen ist.
- GitHub REST \`GET contents?ref=<branch>\` benötigt explizite Referenz für Nichtstandardzweige. DRA V1 **nicht** mit HACS gleichsetzen: DRA hat eine eigene Bereitstellungs-/Quellprüfung.

### 1.3 PRIORITÄT 1 / sichere nächste Schritte

**Zuerst rein lesend feststellen**, welchen Eintrag DRA V1 für DRA V2 DEV verwendet:
1. Stimmt das hinterlegte Repository exakt mit \`TheDaimos/deploy-relay-agent-v2-dev\` überein? Kein ähnlich benanntes V1/PUB-Repo, kein abweichender Quellkanal?
2. Welche **Quelle / Referenz / Branch** ist für dieses Projekt konfiguriert? Der bereitzustellende Stand existiert nur auf \`feature/v2-10-inventory-operation-contract\`; \`main\` kann diesen Stand nicht liefern.
3. Verwendet DRA V1 für die Updateerkennung Manifestversion, Commit-Vergleich oder eigene gespeicherte Ref/Installationsmetadaten? Falls nötig **Code des V1-Repositories nur lesend** untersuchen, V1 nicht verändern.
4. Wird das vorhandene Projekt als bereits aktuell angesehen, Quelle unzugänglich, Ref ungültig oder nicht als neues Update eingestuft? DRA-V1-Quelle und lokale bekannte Version **vergleichen, nicht erraten**.
5. Nur falls Auswahl über die bereits vorhandene DRA-V1-Bedienoberfläche unterstützt ist, dem Nutzer **eine einzige kontrollierte Aktion** zum Prüfen/Anpassen der Quellreferenz nennen. Erst nach verifiziert korrekter Quelle Updateerkennung erneut beurteilen. Nicht ungefragt Dateien überschreiben, keine öffentlichen Zweige verändern, **kein Merge und kein Push nach \`main\`**.
6. Falls die Referenz korrekt ist, Updateerkennungsfehler weiter untersuchen, bevor weitere Versionen erhöht oder Backend-Logik modifiziert werden.
7. Benutzer nicht zur Installation via DRA V2 oder unkontrolliertem HACS zwingen; der freigegebene Entwicklungs-Installationsweg ist **DRA V1**.

Ein geeigneter allererster HA-Schritt kann sein: **DRA V1 öffnen und Screenshot des DRA-V2-DEV-Projekteintrags mit „Quelle/Version/Ref“ senden**. Nur falls diese Infos fehlen; zunächst Git/DRA-V1-Code prüfen.

---

## 2. Zeitstrahl 0.1.53 → 0.1.64 – technische Tatsachen und Abnahmestatus

| Version | Entwicklung | Nachgewiesener Status |
|---|---|---|
| **0.1.53** | Hauptoberfläche auf eine zentrale **Deployment**-Schaltfläche und vier Statusfelder, V1-inspirierte schmale Ladebalkenanimation. Frühere Chatübergabe \`docs/HANDOFF_DRA_V2_DEV_0_1_53_2026-10-11.md\`. | CI erfolgreich; historischer UI-Checkpoint |
| **0.1.54** | Rein berechnete, sichere Zielkollisions-/Besitzprüfung \`target_ownership.py\`. | CI bestanden, keine echte V1/V2-Exklusivsperre |
| **0.1.55** | Manifest-Deklarationen kompatibler mit V1 (bis 5000 Dateien/150 MiB deklariert), **effektive V2-Prüfgrenzen weiter 1000 Dateien/32 MiB**. | CI bestanden; noch kein nachgewiesener HA-Erfolg |
| **0.1.56** | Goldene **Logs**-Schaltfläche neben Deployment; private Git-Übertragung, JSON, Zwischenablage, acht begrenzte Phasenprotokolle, CPU-/Parallelitätsangaben. | Git-Export erstmals real nachgewiesen; Fehler \`tree_invalid\` |
| **0.1.57** | Präzisere Git-Baum-Fehlerkategorien, ohne Rohdaten preiszugeben. | Echter Fehler u. a. \`manifest_invalid\`; noch nicht erfolgreich |
| **0.1.58** | Genauere Manifest-/GitHub-Fehlerdiagnose. | Echter Fehlerverlauf mit wechselnden Phasen, kein belastbarer Quellfehler-Nachweis |
| **0.1.59** | Sitzungsstabile anonyme Projektkennung, eindeutige Prüfkennung, Repo-Name **nur im privaten Git-Export**, bestätigungspflichtiges **Leeren** von HA-Laufzeitlogs. | Echte private Repozuordnung für Gewitterradar erfolgreich, aber \`tree_transport_invalid\` |
| **0.1.60** | Strikt begrenzte Wiederholung bei transientem **read-only** GitHub-Transportfehler; defektes JSON separat kategorisiert. | Echter Export \`tree_json_invalid\` – **Ursache des StreamReader-Fehlers weiter eingegrenzt** |
| **0.1.61** | GitHub-JSON bis EOF in kleinen Portionen lesen; harte 4-MiB-Grenze beibehalten. | **Gewitterradar-Quellvorschau REAL in HA erfolgreich:** Git, Manifest, Baum, lokale Dateibestandsaufnahme, Vergleich, Zielkollision durchlaufen; \`sources_verified=true\`, \`installation_enabled=false\`. Dokument: \`docs/HA_REALABNAHME_SOURCE_PREVIEW_0_1_61_2026-10-11.md\`. |
| **0.1.62 / G2-10** | HA-eigene serverseitige, nur lesende Prüfaufträge; einzelne Auftragskennung und Statusabfrage für Browserwechsel. | CI erfolgreich; isolierte Tests; kein separat vollständig abgenommener Android-/WLAN-Wechsel |
| **0.1.63 / G2-20** | Dauerhafte, sehr kleine Auftragszustands-Historie (8 Datensätze, 6000 Byte), admin-geschützte History-Abfrage, Wiederverbindung mit wachsendem Statusintervall, Unterbrechung statt ungerechtfertigter Wiederaufnahme nach HA-Neustart. | **Benutzer-Screenshot bestätigt echte erfolgreiche Gewitterradar-Quellprüfung, „Serverseitige Auftragshistorie“ mit „Damals erfolgreich“, aber die Git-Export-Schaltfläche zeigt „Privater Export fehlgeschlagen.“** Damit Teil-HA-Erfolg, nicht die vollständige Wiederverbindungs-/Neustartabnahme. |
| **0.1.64 – AKTUELLER SOURCE-HEAD** | Private Git-Export-Reparatur: GitHub-Repo-Metadaten bis EOF und 8192-Byte-Hardlimit lesen; zuvor gesicherten nicht versendeten Export über Logs zuerst retryen, dann bei erneutem Knopfdruck das aktuelle Protokoll. Sichtbarer Text unterscheidet ältere Datei und neuen Bericht. | **CI \`38148357701\` SUCCESS. NICHT in HA abgenommen, weil der Nutzer 0.1.64 in DRA V1 gerade nicht als Update findet.** |

**Präzisierung:** Das 0.1.63-Screenshot zeigt eine erfolgreiche Prüfung **bis Zielbesitz** und eine angezeigte historische Erfolgszeile; kein voller kontrollierter WLAN-Verbindungsabbruch-/HA-Neustart-Test wurde separat belegt. Keine automatische Überdehnung der Abnahme.

---

## 3. Aktueller privater Git-Exportfehler und was 0.1.64 genau repariert

### 3.1 Nutzerbeobachtung in 0.1.63

Im mobilen Bereich \`Deployment → Logs\`:

- **Erfolgreich** abgeschlossene schreibgeschützte Prüfung, Phase **Zielbesitz**, \`Kein Fehler\`; 1.888 ms (als Zeitspanne), CPU-/Parallelitätsangaben angezeigt.
- Projekt-/Prüfkennung sichtbar; auch die **serverseitige Auftragshistorie** wird gezeigt.
- Beim Drücken **Export nach Git**: „**Privater Export fehlgeschlagen. JSON-Download bleibt verfügbar.**“
- Lokale JSON-Ausgabe (vom Nutzer bereitgestellt) bestätigt Quellprüfung: \`status=success\`, \`reason=none\`, \`sources_verified=true\`, \`installation_enabled=false\`.
- Zum damaligen Abgleich war im privaten Archiv kein neuer 0.1.63-Git-Export angekommen; letzte unabhängig gelesene ältere archivierte DRA-V2-Diagnose stammte von 0.1.61.
- Benutzer erteilte ausdrücklich keine Freigabe, den Fehler mit öffentlichen Uploads oder Änderungen am Git-Archiv zu umgehen.

### 3.2 Zwei belastbare Codekorrekturen in 0.1.64

1. **Private Repository-Sichtprüfung:** \`custom_components/deploy_relay_v2_dev/git_measurement_export.py\`, \`_ensure_private_repository()\`. Bisher ein einziges \`response.content.read(8193)\`; bei fragmentierter \`aiohttp\`-Antwort ungültiges JSON. Jetzt bis EOF in 2048-Byte-Portionen lesen, **8192-Byte-Obergrenze** und Privacy-/Default-Branch-Prüfung streng beibehalten.
2. **Export-Warteschlange über Benutzeroberfläche:** \`websocket_api.py\`, \`async_deployment_logs_export\`. War ein fehlgeschlagener vorbereiteter Upload vorhanden, blockierte ein erneutes \`export()\` absichtlich; UI hatte aber keinen Weg, stattdessen \`retry_pending()\` aufzurufen. Jetzt **zuerst** gesicherte Originaldatei unter derselben ID übertragen, auf dem Aufruf **nicht** zugleich einen neuen Bericht anlegen. \`frontend/lab.js\` signalisiert \`pending_retried=true\` und unterscheidet die Rückmeldung.

**Nicht belegt:** Ob die eine echte Git-Fehlübertragung in 0.1.63 genau am abgeschnittenen Metadaten-JSON oder an fehlenden Rechten/GitHub-Netzwerkstatus scheiterte. Das ist ein reproduzierter und korrigierter Codefehler, **HA-Realabnahme der Korrektur weiterhin offen**.

### 3.3 Notwendige Abnahme nach Sichtbarkeit des Updates

- 0.1.64 **über DRA V1 manuell installieren** (nur nach Quellref-/Versionsprüfung und Benutzerentscheidung).
- In V2 \`Deployment → Logs\` sehen: falls Warteschlange vorhanden, sollte „**Gespeicherten Git-Export erneut senden**“ erscheinen. Nach Erfolg enthält die Quittung eine Exportkennung und weist auf die **ältere** Datei hin.
- Beim **zweiten ausdrücklichen** Tippen wird das aktuelle Quellprüfprotokoll exportiert. Nicht automatisch behaupten, der erste Retry sei bereits der letzte 0.1.63-Bericht.
- Die Datei und Export-ID gegen das private Archiv überprüfen. Nicht bei einem gescheiterten Upload die Warteschlange löschen oder neue Datei darüber schreiben.
- Falls weiterhin Fehler: den JSON-Download oder die knappe UI-Fehlermeldung nutzen; keine Tokens vom Nutzer fordern; API-/Rollenprüfung gezielt und ohne Rohdaten.
- Der korrigierte Source-/Diagnoseexport ist **kein** Beleg für V2-Installationsfähigkeit.

---

## 4. Architektur/Komponenten, die bei der Fortsetzung wichtig sind

- \`custom_components/deploy_relay_v2_dev/manifest.json\`, \`const.py\`: Version **0.1.64** im Featurezweig.
- \`deploy-relay.json\`: Source \`TheDaimos/deploy-relay-agent-v2-dev\`, Installationsziel ausschließlich \`/config/custom_components/deploy_relay_v2_dev\`, \`replace_directory\`; \`max_files=27\`, \`max_uncompressed_bytes=3145728\`, keine Symlinks. Dieses Manifest ist **nur auf Featurezweig** vorhanden.
- \`frontend/lab.js\`: Hauptoberfläche „Quelle & Version“, große zentrale „Deployment“-Schaltfläche, V1-Ladebalken, vier Statusstufen; goldene Logs-Pille, Leeren mit Bestätigung, Git/JSON/Zwischenablage, anonyme Projekt- und Prüfkennung, Status/History-Wiederverbindung.
- \`websocket_api.py\`: eigene Admin-WebSocket-Schnittstellen, einschließlich \`projects/source_job/start\`, \`.../status\`, \`.../history\` und \`deployment/logs\`, \`.../download\`, \`.../export\`, \`.../clear\`. Nur lesende HA-Quellprüfung.
- \`source_preview_jobs.py\`: HA-gebundener Prüfauftrag, höchstens einer aktiv, maximal vier flüchtige Resultate; doppelte identische Anforderung → gleiche Kennung; keine Schreibfreigabe, Entladen bricht sicher ab.
- \`source_job_history.py\`: eigene HA-Store-Historie max. 8 Datensätze/6000 Byte ohne Originaldaten, Repository, Commit, Token oder wiederverwendbare Quellvorschau. Nach HA-Neustart wartende Jobs konservativ \`interrupted\` markiert; keine automatische Wiederaufnahme.
- \`source_diagnostics.py\`: begrenzte Phasen-/Fehlerdiagnose, max. acht flüchtige Einträge, projekt-/prüfbezogene Kennung, CPU-/Kern-/Parallelitätsangaben (Prozess-CPU ist nicht DRA-exklusiv).
- \`git_measurement_export.py\`: **ausschließlich private** Git-Diagnosesenke, serverseitiger privater Reponame im Export, keine Offenlegung von Token, begrenzte persistente Wiederholwarteschlange.
- \`remote_source.py\`, \`source_preflight.py\`: GitHub-SHA-gebundene Git-/Manifest-/Bau-/HA-Quellprüfung; JSON bis EOF unter 4 MiB, nur Leseberechtigung. Tatsächliche Dateibudgets 1000/32 MiB, Manifestdeklaration kann größere V1-Obergrenzen haben.
- \`target_ownership.py\`: nur **rein berechnete** Kollisionen; kein exklusiver V1/V2-Dateibesitz bewiesen.
- \`backup_integrity.py\`: mathematische Sicherungs-/Hash-Verträge, **keine tatsächlich abgelegte, unabhängig rücklesbare V2-Sicherung**.
- Zentrale V2-V1-Bereitstellung über DRA V1, keine V2-Selbstinstallation.

### Relevante Tests

- \`tests/test_v2_source_remote.py\`: fragmentierter GitHub-HTTP-Datenstrom, Fehlerkategorien, Zeit-/Byte-/Pfadgrenzen.
- \`tests/test_v2_source_diagnostics.py\`: redigierte Diagnosen, sichere private Repozuordnung, Kennungen, Log-Leeren.
- \`tests/test_v2_40_git_measurement_export.py\`: private GitHub-Metadaten in Fragmenten, Byte-Hardlimit, nie veröffentlichtes Fallback, exakter Retry.
- \`tests/test_v2_deployment_logs_ui.py\`: sichere Goldpille, private Zielprüfung, Retry-Quittung.
- \`tests/test_v2_source_preview_jobs.py\`: browserunabhängige, schreibgeschützte Aufträge, Doppelaufrufe, Fehlersperre und Entladung.
- \`tests/test_v2_source_job_history.py\`: dauerhafte Metadaten, Neustart-Unterbrechung, ungültiger Speicher, kein alter Erfolgsnachweis als Freigabe.
- \`tests/test_v2_countdown.js\`: ein zentraler Vier-Stufen-Ablauf, Wiederverbindung/History-Anzeige, Änderungsschutz.
- \`tests/test_v2_dev_lab_isolation.py\`, \`tests/test_v2_40_security_isolation.py\`: keine fremden Integrationseingriffe, Admin-Schnittstellen, Sicherheitsgrenzen.

---

## 5. Sicherheits-Roadmap / offene Meilensteine – keine Sprünge

Die klare Reihenfolge aus \`docs/V2_GATES_NACH_SOURCE_PREVIEW_REALABNAHME_2026-10-11.md\` bleibt gültig:

1. **G2:** read-only HA-eigene Aufträge und geschützte Geschichte: **implementiert bis 0.1.63 und CI-getestet, nur teilweise HA-real geprüft**. Ein kompletter Browser-/WLAN-Unterbrechungstest und ein bewusst kontrollierter HA-Neustartfall sind noch separat abzunehmen. Git-Exportfehler 0.1.63 durch 0.1.64 im Code korrigiert, HA-Abnahme ausstehend.
2. **G3:** echte beweisbare Besitz-/Übergabesemantik von V1 zu V2 und prozessübergreifende Sperre. \`target_ownership.py\` ist nur statischer Vertrag; eine leere Konfliktliste ist KEIN Besitzbeweis. **Ohne exklusive V1/V2-Sperre keinerlei schreibende V2-Mutation.**
3. **G4:** tatsächlich vollständige V2-eigene Sicherung aller Originalbytes, Schutz der Dateimenge, unabhängiges Wiederlesen/Hashen, Staging, Wiederherstellungstests, Fehler-/Crash-Szenarien.
4. **G5:** einzelne überwachte Schreibtransaktion erst nach G3/G4, expliziter Adminbestätigung, SHA-/Zielbindung, verifiziertem Rückfall-/Recovery-Konzept. Kein Selbstupdate vor stabiler Einzelinstallation.
5. Später: sichere parallele Sammelinstallation, definierte Ressourcenbudgets, echter Fortschritt, gesondert bestätigter HA-Neustart, Selbstupdate und später produktiver Release.

**Verbindlicher neuer Nutzerwunsch:** Eine **Installierbarkeitsprüfung** blockiert vor Mutationsbeginn jeden nicht sicheren Installationsversuch, **ohne** unnötiges Rollback. Nach nachgewiesenem Fehler **während einer bereits begonnenen** Schreibtransaktion soll DRA nur mit validierter Originalbytes-Sicherung und gültiger Exklusivsperre automatisch auf den alten Stand zurückfallen, den Rückfall danach unabhängig bestätigen. Unklare/beschädigte Zustände → \`recovery_required\`. Fällt HA selbst aus, kann die intern in HA laufende V2-Integration **keinen** zuverlässigen automatischen Rückfall ausführen; externer Recovery-Wächter nur als gesondert abgenommene Zukunftsarchitektur. **Nur Spezifikation, nicht implementiert und keine Freigabe.** Details: \`docs/V2_INSTALLABILITY_GUARD_AND_AUTOMATIC_ROLLBACK_2026-10-11.md\`.

---

## 6. Verifizierte letzte GitHub-Stände / keine falschen Erfolgsmeldungen

- Repo \`TheDaimos/deploy-relay-agent-v2-dev\`, Standardbranch **\`main\`**, aber aktuell nur Entwicklungsreferenz (kein V2-Installationsmanifest).
- Entwicklungsfeature \`feature/v2-10-inventory-operation-contract\`: vor diesem Hand-off HEAD \`e20a12dbb20ce91e83dae247b02b8352e39be59c\`, Version 0.1.64, CI \`38148357701\` **SUCCESS**.
- PR #2: **DRAFT**, **OPEN**, **NOT MERGED**.
- Handoff selbst wird anschließend einen **neuen reinen Dokumentations-Commit** erzeugen. Dessen HEAD und CI sind getrennt zu prüfen.
- DRA V1 Updateerkennung für **0.1.64** ist **ungeklärt**, denn der Nutzer sieht das Update nicht. Kein Backend-Fehler als bewiesen behaupten, bevor Quellref/Repo/Version der gespeicherten DRA-V1-Installation kontrolliert sind.
- Keine Verwechslung von **GitHub-CI grün**, einer früheren **HA-Quellvorschau 0.1.61/0.1.63** und **erfolgreicher Installation von 0.1.64**.

---

## 7. Konkreter Auftrag für den NÄCHSTEN Chat

**Arbeitsauftrag A – Update-Sichtbarkeit lösen, keine riskante Kurzschlussaktion.**

1. Bootstrap und diese Dokumente vollständig lesen; aktuellen HEAD/CI/Version prüfen.
2. Prüfen, **wie DRA V1 eine aktuell installierte V2-DEV-Integration und deren Git-Quelle/Ref/Versionsstand ermittelt**. Bei Bedarf GitHub-Quellcode von DRA V1 **nur lesen**, keine Änderung.
3. Den bereits geprüften **Kontrast \`main\` ohne V2-Paket vs. Featurezweig mit 0.1.64** erläutern und die wahrscheinlichste konkrete Abweichung benennen, ohne unbekannte HA-Einstellungen zu erfinden.
4. Wenn nicht rein aus Git lösbar, **eine einzige präzise Smartphone-Aktion**: DRA V1 öffnen und Projekteintrag/Quelle/Ref/Versionsanzeige für V2 DEV zeigen oder mit UI prüfen. Von dort aus kontrolliert und unter Nutzerentscheidung die korrekte **Feature-Ref** auswählen, falls vom DRA-V1-Code/Bedienweg unterstützt.
5. **Keine V2-DEV-Manifeste nach \`main\` verschieben, keinen PR mergen, kein V1-PUB ändern, keine Repo-Version künstlich erhöhen**, nur damit irgendeine Updateanzeige entsteht.
6. Nach tatsächlich möglicher Installation auf 0.1.64 (manuell über DRA V1), den **aufbewahrten Git-Export aus 0.1.63** über „Gespeicherten Git-Export erneut senden“ sicher versenden. Danach gegebenenfalls mit einem zweiten ausdrücklichen Klick den aktuellen Bericht. Archivdatei/Export-ID privat verifizieren; keine Schreiberlaubnis für V2 daraus ableiten.

**Arbeitsauftrag B – G2-HA-Abnahmen anschließend fortsetzen:** Android-Reconnect, Verlauf, History nach HA-Neustart nur bei gesondertem Bedarf/Einverständnis. Danach G3/G4/G5 nach ursprünglichem Plan, keinerlei Sprünge.

### Empfohlene erste Antwort des neuen Chats nach Aktenprüfung

> Die Git-Quelle 0.1.64 ist vorhanden und CI-geprüft. DRA V1 muss dafür den Entwicklungszweig \`feature/v2-10-inventory-operation-contract\` nutzen; \`main\` enthält derzeit kein V2-Manifest. Ich prüfe jetzt die vorhandene Updateerkennung, ohne Zweige zusammenzuführen oder V1 zu verändern. Falls die aktuell gespeicherte Quellreferenz aus Git nicht bestimmbar ist, brauche ich **nur** einen Screenshot des V2-DEV-Projekteintrags in DRA V1, einschließlich Quelle und Ref.

**Nicht vom Nutzer verlangen:** weitere CPU-Messungen, wiederholte bereits erfolgreiche Gewitterradar-Quelltests, Zugangstoken, unnötige HA-Neustarts, manuelle Umkopieraktionen oder öffentliche Diagnoseuploads.

---

**C.K. – Eine Idee weiter gedacht.**

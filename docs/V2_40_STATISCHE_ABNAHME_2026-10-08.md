# V2-40 – Statische Abnahme von Journal und Neustart-Wiedererkennung (08.10.2026)

**Stand: V2-40-10/-20/-30 implementiert und statisch geprüft; V2-40-40 HA-Realabnahme offen.** Kein V2-PUB, kein PR-Merge, keine neue V2-Schreibberechtigung.

## Nachprüfbarer Ausgangspunkt

- Übergabe: `7099cc9f819319d20c3170459b1f244212b6f707` (80/80 Tests).
- V2-40 geprüfter Quellencheckpoint: `97978d6f647699b86370cc1b6b50c9bd08e1f232`.
- CI: https://github.com/TheDaimos/deploy-relay-agent-v2-dev/actions/runs/37808711670 – **SUCCESS, 100/100 Standardbibliothek-Tests**; Python-Syntax V1 und V2, JavaScript-Syntax und Sicherheitsbasisprüfungen grün.
- Eine strenge Negativprüfung schlug zuvor zurecht fehl (unzulässiges `progress_exact=True` bei `queued`); die Einlesevalidierung wurde korrigiert und die **komplette** CI erneut erfolgreich ausgeführt. Frühere rote Läufe sind keine abgeschlossenen Abnahmen.

## Statisch abgenommene Komponenten

| Umfang | Ergebnis |
| --- | --- |
| `operation_journal.py` | Versioniertes, eigenes Lesejournal mit `MAX_RECORDS=12`, `MAX_EVENTS=48`, 48-KiB-naher JSON-Obergrenze, exakt erlaubten Feldern/Enums und generischen Fehlermeldungen |
| `__init__.py` | Fixer HA-Store-Schlüssel `deploy_relay_v2_dev.journal`; vor Annahme neuer Aufträge vollständig laden/prüfen; unbekannte Version/Defekt verhindern Testlabor-Start |
| `readonly_task_supervisor.py` | `queued` vor Taskerzeugung persistent bestätigen; terminalen Status speichern; bei verweigerter Annahme keinen Task ausführen |
| `websocket_api.py` | Persistierte Historie bei `state/get` nur unter denselben drei `require_admin`-Befehlen; Laufzeitzustand ist vorrangig |
| `frontend/lab.js` | Fortschritt/Status und Hinweis auf persistierte Historie bzw. Unterbrechung; keine neuen Schaltflächen für Mutationen |
| `manifest.json`, `const.py` | Eigenständige Version `0.1.1` (V2-DEV-Testlabor), keine V1-Domäne |
| Automatische Prüfungen | 100/100 grün: Journal, Neustart-Konservativität, Schreibfehler, Start-/Ende-Reihenfolge, HA-Unload-Fakes, Idempotenz, Kollisions-/Sicherheitsgrenzen, Syntax |

### Persistenzvertrag

- **Nur** synthetische Leseaufträge des Testlabors (`preview`/`lab_readonly_preview`) werden gespeichert. `install`, `restore`, `batch_install`, `self_update` sind im V2-40-Journal nicht freigegeben. Eine spätere neue Version muss unklare schreibende Transaktionen separat als `recovery_required` behandeln.
- Abschluss `success` bleibt erhalten; vor Neustart offene Leseaufträge werden beim Laden `interrupted`; keine HA-Taskfabrik wird durch `load()` aufgerufen.
- Zwischenstände sind nur im RAM; Startannahme und terminaler Ausgang werden dauerhaft aufgezeichnet. Crash zwischen RAM-Erfolg und Persistenz kann konservativ `interrupted` statt unbelegtem `success` ergeben.
- Keine freien Fehlertexte, Rohprotokolle, fremden Pfade, privaten Projektkennungen, Tokens oder Repo-URLs im Journal. Keine Dateiwahl per WebSocket.
- Beschädigtes Schema, unerlaubte Felder, unplausible Zähler, fremde Vorgänge und Speicherfehler werden nicht als leere gültige Historie behandelt.
- Speicher-I/O nutzt Home Assistants asynchrone `Store`-Schnittstelle; keine 1-Sekunden-Journalschreibschleife, keine Leerlaufabfrage.

### Schutz des einzigen HA-DEV

- `deploy-relay.json`: weiterhin **genau eine** Installationsgruppe, ausschließlich `custom_components/deploy_relay_v2_dev`, maximal 24 Dateien, keine symbolischen Verknüpfungen.
- Bestehende `custom_components/deploy_relay`-, V1-DEV-/PUB- und V2-PUB-Pfade werden nicht modifiziert.
- Keine V2-Befehle für Installation, Wiederherstellung, Sammelaktualisierung, Projektänderung oder HA-Neustart.
- PR #2 bleibt Entwurf und darf nicht ohne ausdrückliche Freigabe zusammengeführt werden.

## Offene Pflicht-Gates vor HA-Abnahme

1. **V2-40-40, Vorschau:** Auf DRA V1 die konkrete Quelle `feature/v2-10-inventory-operation-contract` mit exakter SHA kontrollieren. Installationsvorschau muss *ausschließlich* `custom_components/deploy_relay_v2_dev` als Ziel nennen. Bei jeder V1-Pfadberührung **abbrechen**.
2. **Ausdrückliche Freigabe** des Projektinhabers für die reale V2-Testlaboraktualisierung; **keine** Installation durch Dokumentation oder CI auslösen.
3. Nach Update nur einzeln: Abschluss → nach autorisiertem HA-Neustart gleicher Status; aktiver Test → nach gesondert genehmigtem HA-Neustart Status `interrupted`, keine Wiederaufnahme.
4. V1-Updatefunktion, bestehende Projekte, HA-Latenz, CPU/RAM/I/O vor/nachher real prüfen; Details ohne private Logs dokumentieren.
5. Erst danach V2-40-50 Abschlussentscheidung; V2-50 nicht vorziehen.

**Keine behauptete Realabnahme:** Die früheren V2-30-Zweitsitzungs-/Browser- und V1-Parallelbetriebstests sind real bestätigt, aber sie ersetzen die neue gezielte V2-40-Neustart-Prüfung nicht.

Bezug: `docs/V2_40_PERSISTENZ_ENTWURF_2026-10-08.md`, `docs/V2_STUFENPLAN.md`, `docs/HANDOFF_DRA_V2_40_2026-10-08.md`, Issues #3/#4 und PR #2.

## HA-DEV: Eingangskontrolle nach Installation (08.10.2026)

- Nutzer bestätigte anhand der DRA-V1-Installationsansicht: isolierte Testlaboraktualisierung auf den **festen Quellencommit** `07649ac36c3814dd41f29836175ca49a81c958f3` erfolgreich, mit nachfolgend gefordertem vollständigem HA-Neustart. Die sichtbare Installation nannte eine V1-Transaktionssicherung, deren private Pfade/IDs hier nicht übernommen werden.
- Nach dem vollständigen Neustart bestätigte der Nutzer ausdrücklich: **Beide DRA-Integrationen funktionieren**. Screenshot der V2-DEV-Seitenleiste zeigt die aktuelle Journalbeschreibung und „Noch kein Test gestartet“ – das beweist Erreichbarkeit der neuen Oberfläche, **nicht** die Persistenz eines konkreten Auftrags.
- **V2-40-40 bleibt OFFEN:** Zuerst einen synthetischen Auftrag komplett durchlaufen lassen, Kennung und Status prüfen, danach nur mit gesonderter Freigabe einen erneuten HA-Neustart durchführen und dieselbe Kennung nachschlagen. Anschließend gezielt Unterbrechung eines aktiven Auftrags testen, ebenfalls mit eigener Neustartfreigabe.
- V1-Runtime und V2-Testlabor erreichbar; keine Aussage über Leistungsbaseline oder produktive V2-Schreibaufträge. HA-DEV bleibt die einzige HA-Instanz.

### HA-Pflichttest 1 – abgeschlossener Auftrag vor Neustart

- Datum: 08.10.2026, nach Installation des isolierten Testlabors 0.1.1 und einem bestätigten HA-Core-Neustart.
- Im echten HA-DEV wurde ein neuer synthetischer 20-Schritte-Leseauftrag gestartet. Nutzer-Screenshot: **„Erfolgreich abgeschlossen“**, **100 % der Testschritte**, eindeutige 32-stellige Auftragskennung sichtbar.
- Auftragskennung und Screenshot bleiben nur in der privaten Testkonversation; keine Sitzungskennung oder Nutzerdaten im öffentlichen Repository.
- **Ergebnis: Vorbedingung für Pflicht-Test 1 BESTANDEN.** Die tatsächliche dauerhafte Wiederauffindbarkeit ist **noch nicht geprüft**; dafür ist ein weiterer *ausdrücklich freigegebener* vollständiger HA-Core-Neustart nötig.
- Nach Neustart muss derselbe Auftrag mit demselben `operation_id`, Status `success` und 100 % angezeigt werden. Kein automatisches Neustarten des Auftrags.
- V2-Schreiboperationen, weitere HA-Änderungen und V2-PUB bleiben gesperrt.

### HA-Pflichttest 1 – Neustart-Wiederabruf BESTANDEN

- **08.10.2026, nach dem vollständig ausgeführten HA-Core-Neustart:** Die Home-Assistant-Companion-App zeigte zunächst die identische Kennung, Status `success` und `100 %`, allerdings zugleich einen Neustart-Hinweis. Daher wurde dieser erste Bildschirm **nicht** als ausreichender Nachweis gewertet (möglicher zwischengespeicherter Zustand).
- Anschließend schloss und öffnete der Nutzer die Companion-App erneut und führte den angeforderten Statusabruf aus. Der neue Screenshot (ca. 19:20 Uhr Ortszeit) zeigte weiterhin **exakt die ursprüngliche Auftragskennung**, **„Erfolgreich abgeschlossen“** und **„100 % der Testschritte“**, jetzt ohne Neustart-Hinweis.
- **Abnahme: PASS – abgeschlossener rein lesender V2-Testauftrag nach vollem HA-Core-Neustart weiterhin abrufbar.** Die Auftragskennung wird aus Datenschutzgründen nicht in diesem öffentlichen Abnahmeprotokoll wiedergegeben; Abgleich und Screenshots erfolgten in der privaten Testunterhaltung.
- **Noch nicht geprüft:** Neustart bei einem `running`-Auftrag mit erzwungenem `interrupted` und garantiert ausbleibender Wiederaufnahme. Dies ist der nächste gesondert freizugebende HA-Pflichttest. V2-40 als Gesamtgate bleibt bis dahin **OFFEN**.
- Unverändert: V2 keine Mutationen, V1 unverändert, nur ein HA-DEV, PR #2 Entwurf, kein V2-PUB.

### HA-Pflichttest 2 – Testfenster verlängert, Realabnahme offen

- Nutzer meldete am 08.10.2026, dass sich die Unterbrechung während des 20-Sekunden-Testauftrags nicht erfolgreich nachweisen ließ. **Keine Schlussfolgerung**, ob der Auftrag vor wirksamem HA-Abbruch bereits abgeschlossen war oder der Neustart andere Zeitabläufe hatte; dieser Versuch wird **nicht** als bestandene `interrupted`-Abnahme gewertet.
- Auf Wunsch des Nutzers wird die **rein künstliche** Versuchsdauer auf **40 Schritte × 1 Sekunde = rund 40 Sekunden** verlängert (V2-DEV-Version `0.1.2`); keine echte Installation, kein Git-Zugriff, keine Dateiveränderung, keine Änderung an V1, Journal oder Schreibberechtigungen. Der Fortschritt hat weiterhin echte 1-Sekunden-Schritte; keine zusätzliche Leerlaufabfrage.
- Neue Regression prüft feste Testdauer, Fortschritts-Gesamtzahl, Oberflächentext und unveränderte drei Admin-WebSocket-Kommandos. Ein grüner CI-Lauf sowie eine neue V1-Vorschau und ausdrückliche Installationsfreigabe sind **vor** HA-DEV-Aktualisierung Pflicht.
- Der erneute Neustarttest benötigt eine separate ausdrückliche Neustartfreigabe. **V2-40-40 bleibt offen**, bis dieselbe Auftragskennung nach dem HA-Neustart `interrupted` zeigt und keine neue Aufgabe gestartet wird.


### HA-Pflichttest 2 – 40-Sekunden-Auftrag nach HA-Neustart unterbrochen

- **08.10.2026, reales HA-DEV mit V2-DEV-Testlabor 0.1.2.** Nach grüner CI und geprüfter V1-Vorschau wurde das getrennte Testlabor aktualisiert. Der Nutzer legte in der Companion-App einen neuen künstlichen 40-Sekunden-Leseauftrag an; erster Screenshot um ca. 19:43 Uhr Ortszeit: Status `queued` („Wartet“), noch kein Fortschrittswert, neue 32-stellige Kennung.
- Der Nutzer führte den vorgesehenen HA-Neustart während des synthetischen Auftrags durch. Zweiter Screenshot nach dem Wiederanlauf (ca. 19:47 Uhr Ortszeit): **dieselbe Auftragskennung**, Status **`interrupted`** („Durch Beenden oder Neustart unterbrochen“), **77 % der Testschritte**, keine Wiederaufnahme angezeigt, Startknopf wieder freigegeben. Ein Erfolg bei 100 % wurde nicht behauptet.
- **Ergebnis: HA-Pflichttest 2 BESTANDEN**: ein vorher nicht terminaler, rein lesender Testauftrag bleibt wiedererkennbar, wird nicht als `success` ausgegeben und erscheint beim Wiederabruf als `interrupted`. Die Fortschrittsanzeige zeigt den zuletzt erfassten Stand; 77 % entsprechen bei 40 Schritten rechnerisch 31 abgeschlossenen Schritten, nicht einem nachträglichen Fortsetzen.
- Die private Auftragskennung und Screenshots verbleiben in der Testkonversation; keine Rohdaten oder lokalen Pfade in öffentlicher Dokumentation.
- **Noch offen vor V2-40-50:** V1-Funktionskontrolle nach diesem zweiten Neustart sowie Ressourcen- und Latenzbeobachtungen. Keine mutierenden V2-Operationen freigeben. PR #2 bleibt Entwurf, V2-PUB bleibt gesperrt.


### HA-DEV – DRA-V1-Funktionskontrolle nach Pflichttest 2

- **08.10.2026, ca. 20:01 Ortszeit:** Der Nutzer öffnete nach dem HA-Neustart die **Sammelprüfung von DRA V1** und zeigte den abgeschlossenen Status der Prüfung. Alle fünf eingebundenen Projekte wurden mit **„Aktuell“** und **0 Änderungen** angezeigt; „Keine ausgewählten Projekte benötigen eine Installation“.
- Die vorhandene V1-Bedienung und die rein lesende Sammelprüfung funktionieren somit **nach dem V2-40-Unterbrechungstest weiterhin**. Der Schreibzugriff war nicht freigegeben; kein Installationsversuch und keine Mutation wurde durchgeführt.
- **Abnahme V1-Betriebsschutz für V2-40-40: PASS.** Das bestätigt die Funktion der Prüfung, nicht sämtliche möglichen V1-Installationspfade; eine echte V1-Aktualisierung war zuvor während des Parallelbetriebs bereits erfolgreich bestätigt worden.
- Auf dem Screenshot war die Git-Quellrevision des V2-DEV-Projektes neuer als der installierte Laufzeitstand; zwischen den beiden Ständen liegen nur Dokumentationsänderungen, **kein erneutes HA-V2-Update daraus ableiten**.
- **Offen für V2-40-50:** reproduzierbare CPU-, RAM-, Datenträger-Ein-/Ausgabe- und Reaktionszeitmessungen. Keine Zahlen annehmen oder aus einem funktionsfähigen UI ableiten. Kein Vorziehen von V2-50 oder schreibenden V2-Funktionen.


### HA-DEV – Erste Proxmox-Ressourcenbeobachtung (08.10.2026)

- Der Nutzer stellte Proxmox-Bilder einer HA-VM bereit (VM-ID 109, circa 20:06–20:07 Uhr Ortszeit); VM-Hostname und private Bilddateien werden **nicht** in dieses öffentliche Dokument übernommen. **VM-Zuordnung durch den Nutzer bestätigt:** VM 109 ist die HA-DEV-Instanz mit DRA V1 und dem isolierten V2-Testlabor. Die CPU-Werte sind damit als VM-weite Beobachtung zuordenbar, jedoch weiterhin kein isolierter DRA-V2-Leistungsnachweis.
- Sichtbare Ausstattung: **12 virtuelle CPU-Kerne, ein Sockel, 7.168 MiB zugewiesener Arbeitsspeicher**. Die VM war online.
- CPU-Momentaufnahme: **1,39 %**; im angezeigten Verlauf von ungefähr **69 Minuten** stand **max. 5,47 %**. Dies sind *VM-weite* Werte einschließlich anderer Home-Assistant-Komponenten; kein isolierter DRA-V2-Verbrauch und keine V1-Vergleichsbasis.
- Die App meldete bei Arbeitsspeicher **„0 B“**, obwohl die Speicherverlaufsgrafik **„max 5,56 GiB“** auswies und einen nichtleeren Verlauf zeigte. Deshalb **keine valide aktuelle RAM-Belegung / RAM-Basis-Spitze** daraus ableiten. Die Anzeige muss über eine unabhängige Proxmox-Quelle plausibilisiert werden.
- Datenträger-Ein-/Ausgabe und Home-Assistant-Reaktionszeit sind auf diesen Bildern nicht ablesbar. CPU-Spitzen aus einem zeitlich gemischten Verlauf (einschließlich Neustarts) erlauben **keinen Nachweis fehlender zusätzlicher Last durch V2**.
- **Status V2-40-50: TEILMESSUNG / OFFEN.** Nächster gefahrloser Einzelschritt: Zuerst die VM-Zuordnung zu HA-DEV bestätigen; anschließend die Speicherbelegung über die Proxmox-Weboberfläche derselben VM prüfen. Keine Installation und kein Neustart notwendig; V2-Schreibfunktionen bleiben gesperrt.


### HA-DEV – Plausibilisierte RAM-Momentaufnahme (08.10.2026, 20:26 Uhr)

- Zweite Übersicht derselben, vom Nutzer als HA-DEV bestätigten VM 109: **CPU etwa 1 %**, **Arbeitsspeicher 3,2 GB von 7 GB**. CPU- und RAM-Kurven zeigen im sichtbaren kurzen Zeitraum ab ca. 20:25 Uhr geringe Schwankungen. Dies ersetzt die zuvor als unplausibel eingeordnete App-Anzeige „0 B“ **für die aktuelle RAM-Momentaufnahme**, nicht für den historischen Spitzenwert.
- Diese Werte sind ausschließlich **VM-weit** und Momentaufnahmen. Daraus lässt sich weder CPU-/RAM-Bedarf der einzelnen V2-Integration noch eine belastbare Leistungsänderung gegenüber V1 allein ableiten. Für einen Vergleich fehlen einheitliche Zeitfenster vor/während/nach einer identischen Belastung sowie Messwerte für Datenträger-Ein-/Ausgabe und HA-Reaktionszeit.
- **V2-40-50 bleibt TEILMESSUNG / OFFEN**. Keine erfundenen Messwerte, keine zusätzliche Installation oder Neustart aus der Messung abzuleiten; sicherheitsrelevante V2-Schreibfunktionen gesperrt. Nächste Messungen nur auf dieser bereits vorhandenen HA-DEV-Instanz.

### Ressourcenaudit – kontrollierter Messlauf, noch nicht auf HA-DEV installiert

Die 40-Sekunden-Warteaufgabe verursachte auf der bestätigten HA-DEV-VM 109 im Vergleich zu den Leerlaufbildern keinen aussagekräftigen CPU-Ausschlag: ca. 1 % VM-CPU und ca. 3,3 GB von 7 GB RAM (vorher 3,2 GB). Diese Differenz ist nicht dem V2-Modul zuordenbar. **Ein reiner Warteauftrag ist kein Belastungstest.**

Für die nächste gezielte Messung wurde **V2-DEV 0.1.3** mit einer ausdrücklich auszulösenden, separaten Messfunktion vorbereitet. Die bisherige 40-Sekunden-Aufgabe bleibt erhalten. Der neue Messlauf umfasst 10 s Basisphase, 20 s begrenzte synthetische Hash-Bearbeitung in **nur einem Executor-Thread** (maximal 32 Hashes und 40 ms Wandzeit pro Arbeitsschritt, maximal 20 Arbeitsschritte, konstant ungefähr 64 KiB Eingabe) und 10 s Nachlauf. Kein Lesen von Projektdateien, kein Netzwerk, keine Schreibtransaktion, keine zusätzliche Journalstruktur. Gleichzeitig bleibt höchstens ein Leseauftrag zulässig.

Die Messansicht zeigt lediglich Zähler, monotone Gesamtdauer, maximale Verzögerung der Zeitsteuerung und **prozessweite** CPU-Millisekunden pro Phase; kein fälschlicher DRA-spezifischer CPU-/RAM-Nachweis. Eine RAM-/I/O-Zuordnung über VM-Grafiken ist nur ergänzend und mit entsprechender Unsicherheit erlaubt. Der Bericht ist nur im Arbeitsspeicher verfügbar und wird nicht dauerhaft gespeichert; für die Operation selbst gelten unverändert Persistenz, `success` bzw. `interrupted` und die bestehenden Administratorrechte. Im Leerlauf keine Zusatzarbeit.

**Nicht durchgeführt:** erneute HA-Installation, neuer HA-Neustart oder Realtest mit diesem Messprofil. Vor jeder Installationsänderung: GitHub-CI, DRA-V1-Vorschau, ausdrückliche Nutzerfreigabe. V2-40-50 bleibt offen; V1 und V2-PUB unverändert.

### V2-40 Git-Export – isolierter Einbau als V2 DEV 0.1.4

Auf Wunsch des Nutzers wurde parallel zur V2-40-50-Ressourcenabnahme der direkte Git-Export nach dem Sicherheitsmuster von DRA V1 vorbereitet. Details und Freigabegrenze: `docs/V2_40_GIT_EXPORT_ENTWURF_2026-10-08.md`.

Der Backendexport liegt **nur** in `deploy_relay_v2_dev`. Ein separater Git-Schreibtoken wird ausschließlich in `deploy_relay_v2_dev.git_auth` gespeichert; keine Verwendung von V1-Tokens, keine Änderung am schreibgeschützten Operationsjournal. Git-Upload ist nur nach einem vollständig abgeschlossenen synthetischen Messlauf und explizitem Administrator-Klick zulässig. Öffentlicher Pfad fest unter `.deploy-relay/diagnostics/v2-dev/`, neues JSON mit ausschließlich validierten Zählern, kein Rohjournal oder private Auftragskennung.

Automatische Tests behandeln Fakes für GitHub und den Secret-Store, Manipulationen, defekte Antworten, Authentisierungs-/Schreibfehler, URL- und Pfadgrenzen. Keine echten GitHub-Diagnosedateien wurden hochgeladen.

**Gates:** V2-40-50 bleibt **OFFEN**; kein HA-DEV-Update auf Version 0.1.4 ohne V1-Vorschau und explizite Freigabe. Der Git-Export ist ein optionaler Diagnosepfad und keine Freigabe für Installationen, Projektbearbeitung oder V2-PUB. PR #2 bleibt Entwurf.


### HA-DEV – erster realer Git-Messexport verifiziert (08.10.2026)

- Im **öffentlichen Repository** `TheDaimos/deploy-relay-agent-v2-dev`, Branch `main`, wurde tatsächlich eine neue JSON-Datei unter `.deploy-relay/diagnostics/v2-dev/2026-10-08/20261008T205842Z-5ec6823c.json` gefunden. Git-Commit: `d8131253eee23c850387045491b5c4e329f47ade`, Nachricht `chore(diagnostics): export sanitized V2 DEV measurement [skip ci]`.
- Der Inhalt ist formal plausibel: `dra-v2-dev-git-measurement.v1`, isolierte Domäne `deploy_relay_v2_dev`, Version `0.1.4`, vollständig synthetischer Test mit `elapsed_ms=40056`. CPU-Prozesszeit: Basis 478 ms (10 s), Arbeitsphase 1291 ms (20 s), Nachlauf 598 ms (10 s). Zeitsteuerungsverzögerung maximal 2 ms; 640 synthetische Hash-Durchläufe.
- Öffentlichen **Dateiinhalt** geprüft: keine Auftragskennung, keine Git-Tokens, keine Rohprotokolle, Projektpfade oder private Konfigurationsdaten; nur vorgegebene Metadaten und Messzähler. Das ist ein **erfolgreicher realer Exportnachweis**, kein Beleg für alle Fehler- und Grenzfälle in der HA-Laufzeit.
- Die CPU-Zeit ist **prozessweit**, nicht DRA-spezifisch. Auch `max_wakeup_delay_ms=2` gilt ausschließlich für diesen Messlauf und schließt sonstige Performanceprobleme nicht aus. Ressourcenprüfung V2-40-50 bleibt für belastbare V1-Vergleiche, RAM/I/O und HA-Reaktionszeiten offen.
- Die Existenz des Exports belegt die Ausführung des V2-0.1.4-Exportpfads auf einem verbundenen System, ersetzt aber keine separat dokumentierte Installationsvorschau, Installer-Transaktion oder V1-Funktionsprüfung nach diesem Versionswechsel.


### Erweiterung der Ressourcenmessung – V2 DEV 0.1.5 (Entwicklung, HA-Realtest ausstehend)

Auf Anforderung des Nutzers ergänzt V2-40-50 den bestehenden ausdrücklich ausgelösten 40-Sekunden-Messlauf um **vier Speichermesspunkte**: beim Start, nach der 10-Sekunden-Basisphase, nach 20 Sekunden synthetischer Rechenarbeit und nach dem 10-Sekunden-Nachlauf. Die Messwerte kommen aus zwei fest verdrahteten Linux-Kernel-Pseudodateien, niemals aus Projektdateien:

- Linux \`/proc/meminfo\`: \`MemTotal\` (Gesamtspeicher), \`MemFree\` (unmittelbar frei), \`MemAvailable\` (einschließlich voraussichtlich verfügbarer Zwischenspeicher); „effektiv belegt“ wird exakt als \`MemTotal - MemAvailable\` berechnet.
- Linux \`/proc/self/status\`: \`VmRSS\` des **gesamten Home-Assistant-Prozesses**, nicht einzelner Integrationen. Speicherwerte in KiB (1024 Byte).
- Alle vier Stichproben laufen nach explizitem Teststart im Arbeiterfaden; begrenzte Lesegröße 16 KiB je Pseudodatei. **Keine zusätzliche Arbeit oder periodische Abfrage im Leerlauf.** Nicht lesbare/inkonsistente Daten werden \`null\`, niemals erfundene Nullen.
- Die Kernelwerte beschreiben ausschließlich den von Home Assistant aus sichtbaren Linux-Speicherraum. Je nach Virtualisierung/Containern kann dieser von der Proxmox-Gastsicht abweichen. Weder Ballooning noch Proxmox-VM-Werte werden ohne eigene Schnittstelle behauptet.
- **DRA-V1- und DRA-V2-RAM sind nicht isoliert messbar**, da beide Integrationen in ein und demselben Python-Prozess leben und Bibliotheken sowie Speicherverwaltung teilen. Beide Felder bleiben bewusst \`null\` mit festem Grund \`SHARED_HA_PROCESS_CANNOT_ATTRIBUTE\`. \`VmRSS\` ist weder die Summe noch eine korrekte Aufteilung dieser Komponenten.
- Der Git-Export erhält das neue Schema \`dra-v2-dev-git-measurement.v2\`, inklusive strikt geprüfter Zahlengrenzen, vier Snapshot-Namen und unveränderlicher Hinweisfelder; kein Gerät, Token, private Datei, Auftragskennung oder Rohfehler. Bereits vorhandene öffentliche \`v1\`-Exporte bleiben nach ihrem alten Schema gültig und werden nicht überschrieben.
- V2-DEV-Version \`0.1.5\` ist **noch nicht auf HA-DEV installiert**. Erst CI und gesonderte V1-Vorschau, dann ausdrückliche Installationsfreigabe. V2-40-50 bleibt bis zur realen Messung und V1-Funktionsprüfung **OFFEN**; V2-Schreibfunktionen bleiben gesperrt.

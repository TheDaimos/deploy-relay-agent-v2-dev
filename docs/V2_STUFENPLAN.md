# DRA V2 – verbindliche, öffentliche Umbaureihenfolge

Stand: 08.10.2026. Dies ist eine neu formulierte, veröffentlichungsfähige technische Planung. Der bisherige ausführliche Umbauplan bleibt als fachlicher Bezugsrahmen erhalten; keine privaten Diagnoseberichte oder Konfigurationen werden übernommen.

## Parallele Entwicklung zu V1

Der Projektinhaber hat die parallele V2-Entwicklung freigegeben. V1-RC3 und V1-HACS-Veröffentlichung bleiben getrennt und unverändert. Es ist zulässig, auf einem separaten V2-DEV-Zweig die Ist-Analyse, das Datenmodell und darauf aufbauende klar eingegrenzte Komponenten zu entwickeln. Eine V2-Veröffentlichung ist **nicht** freigegeben. Der verbindliche endgültige V1-FINAL-Vergleichsstand und die realen Referenzmessungen müssen vor einer V2-Freigabe vorliegen.

Abnahmeregel: Zu jedem Punkt gehören (1) Entwurf, (2) automatisierte Prüfungen, (3) Dokumentation, (4) exakter Git-Checkpoint und (5) reale Home-Assistant-Abnahme, sofern das Verhalten nur im System zuverlässig geprüft werden kann. Keine spätere Stufe als abgeschlossen markieren, bevor ihr eigenes Gate erfüllt ist. Vorbereitete, noch nicht verdrahtete Komponenten sind keine abgenommenen Laufzeitfunktionen.

| Gate | Thema | Stand |
| --- | --- | --- |
| V2-00 | Finaler V1-Referenzstand und Rückfallpunkt | OPEN |
| V2-05 | Ressourcen-/Mobilbaseline auf V1 | BLOCKED: Messwerte fehlen |
| V2-10 | Inventar WebSocket, Frontend, Speicher, Locks, Executor | STATIC REVIEW |
| V2-20 | Serverseitiges Operationsmodell, Übergänge und Tests | DRAFT (isoliert) |
| V2-30 | Auftragsmanager und Client-unabhängige Tasks | Isoliertes DEV-Testlabor real geprüft (Zweitsitzung, Browserneuladen, V1-Parallelbetrieb); produktive Schreibpfade weiterhin gesperrt |
| V2-40 | Journale, Persistenz und Neustart-Recovery | V2-40-10/-20/-30 statisch geprüft (101/101 CI in Testlabor 0.1.2); V2-40-40: beide HA-Neustarttests und anschließende V1-Sammelprüfung erfolgreich; V2-40-50 quantitative Ressourcenabnahme OFFEN |
| V2-50 | Echter Fortschritt aus dem Backend | NOT STARTED |
| V2-60 | Vorschau als Auftrag; Reconnect und Pagination | NOT STARTED |
| V2-70 | Installation als Auftrag; unveränderte Sicherheitsgrenzen | NOT STARTED |
| V2-80 | Restore als Auftrag | NOT STARTED |
| V2-90 | Sammelprüfung im Backend | NOT STARTED |
| V2-100 | Sammelinstallation im Backend; DRA zuletzt | NOT STARTED |
| V2-110 | Subscriptions und mehrere Clients | NOT STARTED |
| V2-115 | Diagnose/Logs/Export, ein redigiertes Modell | NOT STARTED |
| V2-120 | Frontend/Mobile: weniger Last, kein künstlicher Fortschritt | NOT STARTED |
| V2-125 | Native HA-Integrationsansicht und Logo | NOT STARTED |
| V2-130 | Ressourcen-/Worker-Audit mit dokumentierten Messungen | NOT STARTED |
| V2-140 | Sicherheits- und Wiederherstellungsaudit | NOT STARTED |
| V2-150 | Migration aus V1 einschließlich Sicherungen und Subentries | NOT STARTED |
| V2-160 | Vollständige reale HA-Abnahme | NOT STARTED |
| V2-170 | Release-Dokumentation und kontrollierte PUB-Übernahme | NOT STARTED |

## Unveränderliche Sicherheit

- Ausgangszustand LOCKED, Schreibfreigabe nur explizit und nicht über Neustarts persistent.
- Exakte Quell-SHA, serverseitige Autorisierung, verlässliche Vorprüfung, Pfadgrenzen.
- Sicherung vor Mutation, Ergebnisverifikation und definierter Rollback/RECOVERY_REQUIRED.
- Dateien/Git/Hashes außerhalb der Home-Assistant-Haupt-Ereignisschleife; begrenzte RAM- und I/O-Last.
- Nur eine globale Mutation gleichzeitig, bis messbar eine andere sichere Architektur akzeptiert ist.
- Alle Statusmeldungen und dauerhaften Diagnosen begrenzt und ohne Zugangsdaten, beliebige Pfade oder unredigierte Fehlertexte.
- Aktive Operationen besitzen das Backend, nicht ein Browserfenster.

## V2-Zusatzanforderungen für spätere Phasen

Im Schritt 4 nach erfolgreicher Sammelinstallation soll die Installationsaktion durch eine Neustartaktion ersetzt werden. Diese benötigt zunächst eine Sicherheitsabfrage und eine **zweite ausdrückliche Neustartbestätigung**. Erst dann darf eine autorisierte Home-Assistant-Neustartfunktion aufgerufen werden. Niemals bei unklarem Installations- oder Sicherungszustand.

Installationsfortschritt soll **im Installationsbereich** erscheinen und reale Phasen-/Dateizähler anzeigen statt eines laufenden Browser-Schätzwerts. Nach WLAN-/Mobilfunkwechsel oder Schließen der App muss ein autorisierter Client die unverändert vom Server besessene Operation wieder aufnehmen können.

## Dokumentierte Quellen

- Freigegebene öffentliche V1-Ausgangsbasis: `TheDaimos/deploy-relay-agent-pub` Commit `0c9d7f49f080dfe77b6c3910f89d6a61ae4b8cfa`.
- Neuer V2-DEV-Baselinecommit: `454dac719de325edc8e9749542c6ab7666bd2bf2`.
- V1-FINAL-SHA, V1-Leistungs- und reale V2-Benchmarks: noch nicht vorhanden.

## Nachtrag V2-30/V2-40 (08.10.2026)

Die früheren Gate-Statuswerte waren vor dem mittlerweile bestandenen Realtest des getrennten V2-DEV-Testlabors erstellt. Zweitsitzung, Notebook-Browserneuladen, V1-Gewitterradar-Update und anschließender HA-Neustart sind bestätigt. **Aktueller Stand vom 08.10.2026:** Beide V2-40-40-Realtests sind nun bestanden: Ein abgeschlossener Auftrag blieb nach vollem HA-Neustart mit identischer Kennung und Erfolg/100 % abrufbar. Ein späterer künstlicher 40-Sekunden-Leseauftrag wurde nach dem HA-Neustart mit identischer Kennung als `interrupted` bei 77 % angezeigt, ohne sichtbaren automatischen Neustart. Die V1-Funktions- und Ressourcenabschlussprüfung für V2-40-50 bleibt offen. Das Journal der V2-40-Implementierung ist zunächst auf synthetische Leseaufträge begrenzt; spätere schreibende Transaktionen bleiben untersagt. Statische Abnahme und CI: `docs/V2_40_STATISCHE_ABNAHME_2026-10-08.md`. V2-00/V2-05 und finale V2-PUB-Gates bleiben unverändert offen.

## Nachtrag: V2-40-Ressourcenmessung und Git-Export (08.10.2026)

HA-DEV VM 109: bei einem reinen 40-Sekunden-Warteauftrag VM-weite Auslastung ca. 1 % CPU und 3,3 GB von 7 GB RAM; das ist **kein isolierter DRA-V2-Leistungsnachweis**. Für V2-40-50 wurden ein ausdrücklicher, begrenzter Messlauf (V2 DEV 0.1.3) und auf Wunsch des Nutzers ein eigener, V1-konformer Git-Export für **ausschließlich anonyme Messzahlen** vorbereitet (V2 DEV 0.1.4). Der Git-Export kann nur in das öffentliche `TheDaimos/deploy-relay-agent-v2-dev` unter `.deploy-relay/diagnostics/v2-dev/` schreiben; kein V1-Zugang und keine V2-Installationsfreigabe.

Statische Tests/CI und GitHub-Review ersetzen **nicht** die ausstehende HA-DEV-Vorschau, Benutzerfreigabe, Realmessung und Git-Export-Abnahme. Die Stufen V2-50 ff. bleiben gesperrt.

## V2-40-50 Speicher-Messvertrag (08.10.2026)

Die vier Messpunkte und deren öffentliche Schema-/Attributionsregeln für **V2 DEV 0.1.5** sind in `docs/V2_40_MEMORY_MEASUREMENT_2026-10-08.md` verbindlich dokumentiert. Linux-Systemwerte und HA-Prozess-RSS sind getrennt zu kennzeichnen. RAM für V1 bzw. V2 einzeln kann im geteilten Python-Prozess **nicht seriös isoliert gemessen** werden; diese Werte bleiben `null`. V2-40-50 bleibt bis zum Realtest offen; V1 und V2-PUB dürfen nicht verändert werden.

## V2-40-50 – Restzeit und reale Messserien (08.10.2026)

Drei reale Speicher- und CPU-Messreihen mit V2 DEV 0.1.5 aus dem öffentlichen Git-Diagnoseverzeichnis wurden ausgewertet; die erste stammt nach Nutzerangabe aus dem HA-Startprozess und kann nicht als reiner DRA-Verbrauch gelten. Neu vorbereitet: V2 DEV 0.1.6 mit clientseitigem, backendverankertem Sekunden-Countdown, ohne zusätzliche Serveranfragen im Sekundentakt. Die vorhandene 40-Sekunden-Arbeit testet genau einen Hintergrundfaden und beweist keine Mehrkernleistung. CI und anschließende Installationsvorschau/Realabnahme bleiben verbindlich; V2-40-50 ist weiter OFFEN.

## V2-40-50 Mehrkern-Diagnose und Gesamttest (08.10.2026)

In V2 DEV 0.1.7 wurde ein separater begrenzter 1/2/4-Prozesse-Vergleich und ein einziger 83-Schritte-Gesamttest vorbereitet. Ein vollständig geprüfter Bericht kann manuell als ein anonymisierter Git-Export veröffentlicht werden. Entwicklung und statische Abnahme sind vom HA-Echttest zu unterscheiden; Dokumentation: `docs/V2_40_MULTICORE_AND_SUITE_2026-10-08.md`. Keine V1-Änderung und keine Installationsfreigabe; V2-40-50 bleibt OFFEN.

## V2-40-50 – Gesamttest auf HA-DEV nachgewiesen (09.10.2026)

V2 DEV 0.1.7 ist durch einen echten anonymisierten öffentlichen `dra-v2-dev-git-suite.v1`-Export vom 09.10.2026 nachgewiesen: 40 Warteschritte, 40 Sekunden CPU-/RAM-Messung, anschließende erfolgreiche Mehrkernstufen 1/2/4, alles in einem Bericht. Die Durchsatzverhältnisse 2,11×/3,92× sind ausschließlich kurze synthetische Messungen, keine isolierte DRA-Leistung. Detailwerte und Sicherheitsbewertung unter `docs/V2_40_STATISCHE_ABNAHME_2026-10-08.md`. **V2-40-50 bleibt bis zur DRA-V1-Funktionsprüfung nach dem Versionswechsel und den weiteren Ressourcen-Gates offen**; keine V2-Schreibaktionen freigegeben.

## V2-40-50 – V1-Parallelbetriebsprüfung nach 0.1.7 bestanden (09.10.2026)

Die DRA-V1-Sammelaktualisierung zeigt fünf Projekte einschließlich DRA V2 DEV 0.1.7 mit jeweils 0 Änderungen und `Aktuell`. Die Schaltflächen zur Schreibfreigabe und Installation sind deaktiviert; kein Schreibauftrag erfolgte. **V1-Lese- und Vorschaufunktion nach Versionswechsel PASS.** Noch offen bleiben Datenträger-E/A und HA-Reaktionszeit als quantitative V2-40-50-Gates; daher kein Final-Abschluss, keine Freigabe für V2-Schreibaktionen. Verbindliches Detail: `docs/V2_40_STATISCHE_ABNAHME_2026-10-08.md`.

## Vorgemerkter Funktionsentwurf: konfigurierbare Auftragsparallelität und CPU-Budget (09.10.2026)

Der Nutzer wünscht auswählbare sequenzielle/gesteuert parallele/ressourcenabhängige Auftragsplanung sowie die getrennte Konfiguration der Zahl gleichzeitiger Aufträge und der CPU-Arbeitsprozesse. Der Iststand V2 DEV 0.1.7 bleibt unverändert: ein aktiver synthetischer Auftrag, Mehrkernstufen 1/2/4 nacheinander. Die bestehende Sperre **maximal eine globale Mutation** ist ausdrücklich nicht aufgehoben. Verbindlicher Sicherheits- und Abnahmeentwurf: `docs/V2_PARALLELISM_AND_CPU_BUDGET_DESIGN_2026-10-09.md`. Umsetzung erst nach Abschluss der aktuellen V2-40-50-Ressourcenprüfung und gesondertem Freigabeschritt.


## Mehrkern-Probe 1/2/4/6/8/10/12 – V2 DEV 0.1.8 (09.10.2026)

Auf ausdrücklichen Nutzerwunsch wurde die feste schreibgeschützte Diagnosereihe auf sieben Stufen erweitert; Gesamttest 87 Schritte, versionierter strikter Git-Export v2. Die Stufen laufen nacheinander und starten maximal 12 kurzlebige Arbeitsprozesse gleichzeitig. Bestehende V1-Gesamtexporte bleiben lesbar. Keine produktive Schreibparallelisierung, keine Änderung an DRA V1 oder V2-PUB. Realabnahme 0.1.8 und V2-40-50 weiter offen; Details `docs/V2_40_MULTICORE_AND_SUITE_2026-10-08.md`.

## Verbindliche Arbeitsumstellung auf Funktionspakete (09.10.2026)

Auf ausdrücklichen Nutzerwunsch wird DRA V2 künftig mit **fachlich gebündelten Entwicklungsständen und risikogesteuerter gemeinsamer HA-Realabnahme** statt einer vollständigen HA-Installations-/Neustart-/Gesamttestkette pro kleiner Änderung umgesetzt. **Technische Stufen dürfen gemeinsam implementiert werden; jedes Gate behält einen eigenen dokumentierten Abnahmenachweis und wird nicht vorzeitig als DONE markiert.** CI/Testfälle bleiben pro Funktionsänderung verbindlich, HA-DEV-Installationsvorschau und ausdrückliche Nutzerfreigabe bleiben je Paketausbringung erforderlich. Schreib-, Recovery-, Migrations- und Neustartfunktionen behalten risikobedingt separate Realabnahmen. Die erste geplante Paketeinheit **A – Messung und Diagnose** bündelt präzise Zeitstempel, HA-Ereignisschleifen-Latenz, Prozess-I/O und einen gemeinsamen anonymisierten Git-Export als Abschluss der offenen V2-40-50-Ressourcenprüfung. Ausführlicher verbindlicher Vertrag: `docs/V2_BATCH_ENTWICKLUNG_UND_ABNAHME_2026-10-09.md`. Der Eintrag ist eine Planänderung, noch keine Code- oder HA-Änderung.

## Paket B1 – Opt-in-Projektverwaltung und Sicherungsrichtlinie (09.10.2026)

Nach ausdrücklicher Nutzerfreigabe für gebündelte V2-Entwicklung wurde im isolierten V2-DEV-Featurezweig **0.1.9** vorbereitet: eigene V2-Projektverwaltung, ausdrücklich bestätigte Übernahme von V1-Projektmetadaten ohne Übernahme von Geheimnissen oder V1-Backups, manuelle Neuanlage, projektbezogene Aufbewahrungsrichtlinie (10 voreingestellt; 3–100) und rein berechnender, konservativer Rotationsplan. Eine Installation aus V2, tatsächliche Sicherungsdateien, Löschen alter Sicherungen und Wiederherstellen sind **nicht** Bestandteil dieses Pakets und bleiben bis zu eigenen Transaktions-/Recovery-Tests **gesperrt**. Mehrere Funktionen werden gebündelt in einem einzigen HA-Realtest geprüft, sobald der Nutzer die konkrete 0.1.9-Aktualisierung ausdrücklich freigibt. Genauer Vertrag: `docs/V2_B1_PROJEKTE_BACKUPGRUNDLAGEN_2026-10-09.md`. Keine Abkürzung der alten Gates V2-70/80/140, keine V1-Mutation.

## Gebündeltes Paket DRA V2 DEV 0.1.11 – Einstellungen und Sammelvorauswahl (09.10.2026)

Gemeinsame Implementierung der rein **gespeicherten** DRA-Vorgaben für schreibgeschützte Leseparallelität (1–4) und Arbeitsprozesse (1–12), der projektbezogenen `batch_preselect`-Einstellung (Altbestand ohne Feld: `true`) und einer strikt nicht schreibenden Sammelauswahl-Vorschau (`not_checked`, kein Git-Abgleich). Die Werte **ändern noch nicht den aktiven Worker-/Auftragsscheduler**, aktiv bleibt genau ein Lese-Testauftrag, null Schreibaktionen. HA-Realabnahme erst nach ausdrücklicher Installationsfreigabe. Die allgemeinen Gate- und Sicherheitsregeln gelten unverändert. Technische Dokumentation: `docs/V2_0_1_11_SETTINGS_BATCH_2026-10-09.md`.


## V2 DEV 0.1.12 – Automatische CPU-Verfügbarkeit beim Start (09.10.2026)

Zur DRA-Settings-Entwicklung ergänzt: Beim Laden der V2-Integration Anzahl verfügbarer logischer Prozessoren ermitteln und gegenüber der gespeicherten Maximalvorgabe 1–12 prüfen. Sinkt die Verfügbarkeit unter den eingestellten Wert, wird dieser **vor weiterer Verwendung dauerhaft auf das verfügbare Maß reduziert**, mit gespeicherter, quittierbarer Warnung in der V2-Oberfläche. Bei einem Anstieg wird nur der beobachtete Wert still aktualisiert, keine automatische Erhöhung der Benutzerwahl. Alte Settings v1 bleiben erhalten und migrieren kontrolliert auf v2; bei fehlerhaften Messungen kein erfundener Wert. **Das aktiviert noch keine tatsächliche Worker-Affinität/Parallelität** und beweist keine cgroup-Quote. Detailvertrag `docs/V2_CPU_STARTUP_GUARD_2026-10-09.md`; HA-Realabnahme nach expliziter Freigabe offen.

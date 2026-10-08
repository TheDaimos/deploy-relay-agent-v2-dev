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

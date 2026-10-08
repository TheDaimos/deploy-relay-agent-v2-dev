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
| V2-40 | Journale, Persistenz und Neustart-Recovery | V2-40-10/-20/-30 implementiert, 100/100 CI grün; V2-40-40/-50 HA-Neustart-Realabnahme und Abschluss OFFEN |
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

Die früheren Gate-Statuswerte waren vor dem mittlerweile bestandenen Realtest des getrennten V2-DEV-Testlabors erstellt. Zweitsitzung, Notebook-Browserneuladen, V1-Gewitterradar-Update und anschließender HA-Neustart sind bestätigt. Ein bei HA-Neustart *aktiver* Auftrag war dabei noch nicht im Test: Das ist **V2-40-40** und ausdrücklich offen. Das Journal der V2-40-Implementierung ist zunächst auf synthetische Leseaufträge begrenzt; spätere schreibende Transaktionen bleiben untersagt. Statische Abnahme und CI: `docs/V2_40_STATISCHE_ABNAHME_2026-10-08.md`. V2-00/V2-05 und finale V2-PUB-Gates bleiben unverändert offen.

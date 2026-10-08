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

# DRA V2-40 – Persistenz, begrenztes Journal und konservative Neustart-Wiedererkennung

Stand: 2026-10-08 · **Entwurf / statische Abnahme vor HA-Realtest**. Gültig ausschließlich für `deploy_relay_v2_dev` im Zweig `feature/v2-10-inventory-operation-contract`. Die Gates V2-00/05 bleiben für die spätere V2-Freigabe offen. PR #2 bleibt Entwurf.

## A. Begriffe und Grenzen

- **Wiederfinden**: Abruf einer unveränderten Kennung aus einer anderen Browser-Sitzung in derselben HA-Core-Laufzeit (V2-30 real nachgewiesen).
- **Wiederherstellen**: Das Laden und Prüfen eines *vor* HA-Core-Neustart persistent geschriebenen Zustands und die konservative Kennzeichnung früher aktiver Aufträge.
- **Fortsetzen**: Erneutes Ausführen nach HA-Neustart. **Für V2-40 verboten**, selbst bei schreibgeschützten Aufträgen.
- Ein `operation_id` ist nur ein Suchschlüssel, kein Autorisierungsnachweis. Alle drei WebSocket-Befehle bleiben ausschließlich für Administratoren.
- V1 unter `deploy_relay`, seine Daten, sämtliche Projekte und andere Repositories bleiben unberührt.

## B. Datenträger und Speicherform

Home Assistants `homeassistant.helpers.storage.Store` (Version 1) mit **festem** Schlüssel `deploy_relay_v2_dev.journal`, also getrennt von `deploy_relay` und ohne clientseitig konfigurierbaren Pfad. `Store.async_load/async_save` übernimmt asynchrones und atomar vorgesehenes Schreiben; keine eigene blockierende Datei-I/O in der HA-Ereignisschleife. Keine Timer, kein Schreiben in jeder der 20 Sekunden und keine Leerlaufschleifen. Speicherung nur bei Annahme und terminalem Abschluss/Abbruch sowie nötiger Korrektur nach Neustart.

Inneres Dokument: `schema = dra-v2-dev-journal.v1`, Liste `records` mit maximal 12 Snapshot-Datensätzen und `events` mit maximal 48 Statusereignissen; Ereignisse enthalten ausschließlich Auftragskennung, Status und fest formatierte UTC-Zeit. Dokumentgröße und Zahl verschachtelter Einträge sind begrenzt. Doppelte Kennungen, falsche Schema-/Feldtypen, fremde Schlüssel, übergroße oder inkonsistente Zähler und unbekannte Phasen führen zur *vollständigen Ablehnung*, nicht zum stillen Überschreiben beschädigter Daten. Kein automatischer Schemawechsel.

Gespeichert wird eine **eigene Positivliste** aus dem Operationsmodell, ohne beliebige Metadaten, freie Clienttexte, Zugangsdaten, Repository-URLs, private Projektkennungen, Pfade, Ausnahmetexte, HTTP-Header oder Rohprotokolle. Im Testlabor ist ausschließlich `operation_type=preview`, `project_key=lab_readonly_preview` und `source_commit=null` zulässig. Erweiterungen für schreibende Vorgänge erfordern später eine neue, separat geprüfte Version und Sicherheitsfreigabe.

## C. Zustandsvertrag

| Vor dem Neustart | Nach dem Neustart | Folge |
| --- | --- | --- |
| `success`, `failed`, `cancelled`, `interrupted` | derselbe terminale Zustand | Historie bleibt abrufbar, kein Taskstart |
| `queued`, `waiting_for_resource`, `running`, `cancel_requested` bei **lesendem** Auftrag | `interrupted` | Abschlusszeit wird gesetzt; keine neue Aufgabe |
| Späterer unklarer **schreibender** Auftrag | `recovery_required` | manuelle Transaktionsprüfung nötig, niemals automatisch weiterarbeiten |
| Schema inkompatibel, Inhalt defekt, Lesefehler | Testlabor startet *nicht* mit leerem Journal | Daten bleiben unangetastet, Fehler nur generisch melden |
| Speicherfehler vor Start eines neuen Leseauftrags | Aufgabe nicht starten | Fehlschlag, niemals Bestätigung nicht persistierter Annahme |
| Crash zwischen In-Memory-Erfolg und dauerhaftem Schreiben | beim Wiederanlauf `interrupted` | kein erfundener Erfolg |

Terminale Status sind unveränderlich. Die Registry hält weiterhin höchstens einen laufenden Leseauftrag. Nach Restart werden frühere Kennungen ausschließlich zur Anzeige geladen; alte Anfrage-IDs dürfen keine Mutation legitimieren. Bei späteren Schreibaufträgen müssen Commit-SHA, Lock, Freigabe, Vorprüfung, Sicherungs- und Rückfallstatus unabhängig von diesem Lesejournal durch den gesonderten Transaktionspfad geprüft werden.

## D. Atomizität, Last und Ablauf

1. Beim Einrichten nur das V2-eigene Store-Dokument laden, *vollständig* prüfen und dann bisher aktive **Lese**einträge terminal als `interrupted` zurückschreiben, bevor das Testlabor Aufträge annimmt.
2. Bei `test/start` einen neuen Registereintrag erzeugen und den zulässigen `queued`-Snapshot persistent bestätigen, **bevor** ein HA-besessener Task gestartet wird. Misslingt dies, darf kein Task laufen.
3. Bei jedem terminalen Ereignis gespeicherten Snapshot mitsamt Journal-Ereignis schreiben. Zwischenfortschritte verbleiben bewusst nur im Speicher. Ein atomar serialisierender Schreibschutz vermeidet vertauschte Speicherstände.
4. Bei ordentlichem Entladen laufende **Lese**aufträge abbrechen, terminal schreiben; bei hartem Core-Ausfall greift beim nächsten Setup die konservative Startup-Normalisierung.
5. Beim autorisierten `test/state` und `test/get` aktuelle Registerdaten gegenüber bereits gespeicherter Historie bevorzugen. Keine Browser- oder HA-Startautomatik für Aufträge.
6. Nach jeder Speicherung nur die 12 jüngsten Operationen und 48 jüngsten Statusereignisse behalten; keine Geheimnisse im Journal. Keine dauerhafte Idempotenz-Freigabe nach Neustart.

## E. Sicherheits-/Fehlerabnahme (Pflicht)

- Begrenzungen, Schema-/Enumvalidierung, schadhafte Datensätze, Duplikate, unvollständige Werte, unerlaubte Schlüssel, falsche Zeitwerte, fehlende Store-API, Schreib- und Lesefehler sowie fehlende Datei.
- `queued/running/cancel_requested` werden nur `interrupted`, kein Task erzeugt; Abschluss bleibt Abschluss. Fehlerfall während Persistenz lässt keine falsche Erfolgsmeldung zu.
- Race: gleichzeitiges Taskende, geordneter Unload, Schreibsperre/Serialisierung und idempotenter Abruf.
- Admin-Prüfung auf allen drei WS-Kommandos; Namens-/Pfadkollisionen, V1-Dateischutz, keine V2-Mutationsbefehle.
- Python/JS-Syntax, gesamte Standardbibliothek-Testfolge und CI grün; anschließend exakter Git-Checkpoint dokumentieren.

## F. HA-Realabnahme – ausschließlich nach Vorschau und ausdrücklicher Freigabe

1. Auf **dem vorhandenen einzigen HA-DEV** nur die Vorschau der V2-Dateien unter `custom_components/deploy_relay_v2_dev` kontrollieren. `custom_components/deploy_relay` darf **nicht** erscheinen.
2. Erst nach Benutzerfreigabe Testlabor über DRA V1 aktualisieren; V1 und Gewitterradar müssen weiter funktionieren.
3. 20-Sekunden-Testauftrag vollständig abschließen, Kennung notieren; *nach* gesondert freigegebenem HA-Core-Neustart denselben Abschluss abrufen.
4. Neuen 20-Sekunden-Testauftrag starten; *während er läuft* nur nach gesonderter Freigabe HA-Core neu starten. Danach dieselbe Kennung muss `interrupted` anzeigen, ohne erneut zu laufen.
5. Administratorabruf von zwei Sitzungen, Aufbewahrungsgrenzen, CPU/RAM/I/O/HA-Reaktion dokumentieren; keinerlei reale V2-Installation/Restore/Neustartbefehl freischalten.

**Stand heute:** V2-30-Zweitsitzung, Browserneuladen und V1-Parallelbetrieb mit anschließendem HA-Neustart real bestätigt; **dieses V2-40-Neustart-Gate noch nicht durchgeführt**. Die älteren Statusangaben in V2-30-Unterlagen und Issues sind insofern historisch.

## G. Gates

`V2-40-10` Entwurf + statische Prüfung → `V2-40-20` reiner Codec + strenge Regressionen → `V2-40-30` HA-Store-Anbindung + gesicherter Lebenszyklus, Fakes/CI → `V2-40-40` Vorschau/Freigabe/HA-Realtest → `V2-40-50` Abschluss und Nachmessung. Kein Sprung zu V2-50, kein PR-Merge.

Bezug: `docs/V2_STUFENPLAN.md`, `docs/V2_20_OPERATION_CONTRACT.md`, `docs/V2_30_HA_TASK_ANBINDUNG.md`, Issues #3/#4 und PR #2.

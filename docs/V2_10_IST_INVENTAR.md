# V2-10 – statisches Inventar der öffentlichen V1-Integrationslaufzeit

Stand: 08.10.2026. Untersuchte Dateien stammen aus `deploy-relay-agent-v2-dev/main@454dac719de325edc8e9749542c6ab7666bd2bf2`. **Nur statischer Quellnachweis**. Mobile-Laufzeiten, Haupt-Ereignisschleifen-Latenz, WebSocket-Abbruch und RAM-Spitzen sind noch nicht real gemessen.

## 1. Bestehende WebSocket-Kommandos

Alle folgenden Endpunkte tragen im vorhandenen `websocket_api.py` `@websocket_api.require_admin`.

| Kommando `deploy_relay/panel/` | Python-Funktion | Art | Besonderheit |
| --- | --- | --- | --- |
| `state` | `websocket_panel_state` | read-only | Betriebsmodus, Projekte, Diagnosezusammenfassung |
| `set_mode` | `websocket_panel_set_mode` | Steuerung/Autorisierung | LOCKED/DEVELOPMENT, serverseitige Bestätigung |
| `import_project` | `websocket_panel_import_project` | Konfiguration mutierend | Projekt-Subentry, Quellzugang |
| `remove_project` | `websocket_panel_remove_project` | Konfiguration mutierend | Sicherheitsbestätigung |
| `sources` | `websocket_panel_sources` | Netz-/Quellenabfrage | Git-Quelle/Empfehlung |
| `select_source` | `websocket_panel_select_source` | Konfiguration mutierend | ausgewählte Ref/SHA |
| `preview` | `websocket_panel_preview` | read-only, langlaufend | gesamter Datei-/Vergleichsbestand in Antwort |
| `install` | `websocket_panel_install` | schreibend, langlaufend | doppelte Sperren, frische Sicherheitsprüfung, Sicherung |
| `backups` | `websocket_panel_backups` | read-only | Backupliste |
| `set_backup_retention` | `websocket_panel_set_backup_retention` | schreibende Verwaltungsoperation | Retention-Bereinigung |
| `restore_backup` | `websocket_panel_restore_backup` | schreibend, langlaufend | DEVELOPMENT + Bestätigung, Safety Snapshot |
| `configure_git_export` | `websocket_panel_configure_git_export` | Konfiguration mutierend | separater Schreibzugang, niemals an Client zurückgeben |
| `export_git` | `websocket_panel_export_git` | schreibend extern | redigierter Git-Diagnoseexport |
| `logs` | `websocket_panel_logs` | read-only | Ereignisfilter |
| `support_bundle` | `websocket_panel_support_bundle` | read-only | redigierte Diagnosedaten |
| `clear_logs` | `websocket_panel_clear_logs` | schreibend lokal | Diagnosebereinigung |

Nachweis: `websocket_api.py` ca. Zeilen 263–2107. Bestehende Kommandos dürfen beim Umbau nicht still verändert werden; neue `operations/*`-Schnittstellen erhalten eigenständige Abnahme.

## 2. Serverseitiger Lock-/Taskbesitz

`__init__.py` (ca. Zeilen 27–38): `DeployRelayRuntimeData` hält `deployment_mode=LOCKED`, `deployment_lock=asyncio.Lock()` und `resource_lock=asyncio.Lock()`. Beim Setup werden die Locks neu angelegt. `async_register_websocket_commands` wird in `async_setup_entry` aufgerufen. Beim Unload existiert derzeit kein separater langfristig weiterbestehender Auftragsmanager.

`websocket_api.py`:
- `preview` erwirbt `resource_lock` und erstellt eine frische Vorschau.
- `install` verwendet `async with deployment_lock`, prüft den DEVELOPMENT-Modus erneut, erwirbt `resource_lock`, führt Vorprüfung, Backup und Mutation aus.
- `restore_backup` nutzt ebenfalls `deployment_lock` plus `resource_lock` und eine explizite Bestätigung.
- Backuplisten/Bereinigung greifen auf `resource_lock` zu.
- Schwere Datei-/Hash-/Installationsarbeiten laufen über `hass.async_add_executor_job`; `deployment.py` delegiert andere blockierende Funktionen an bereitgestellten Executor oder `asyncio.to_thread`.

**Offen:** Was bei Abbruch der anfragenden WebSocket-Verbindung mit dem serverseitigen Coroutine-/Transaktionszustand passiert, ist durch Code allein nicht vollständig bewiesen. Erst Test mit realem Clientwechsel/Restart. Neue Aufgaben dürfen nicht blind per `asyncio.create_task` ohne HA-Lifecycle-Kontrolle angelegt werden.

## 3. Frontendbesitz und Last

`frontend/deploy-relay-panel.js`:
- Zentraler Transport: `_call(message)` → `this.hass.callWS(message)` (ca. 548–550).
- `_startProgress` richtet ein `setInterval` über **850 ms** ein und steigert die Prozentanzeige in Browser-Schritten; anschließend `_render()` (ca. 592–603).
- `_finishProgress()` setzt browserseitig **100 %** (ca. 613–623), unabhängig davon, ob der serverseitige Ende-Zustand schon vollständig sichtbar ist.
- `batch_check` ist eine JavaScript-Schleife: Sources → Source Selection → Preview je Projekt (ca. 1226–1325).
- `batch_install` ist eine JavaScript-Schleife: einzelne `install`-WebSocket-Aufrufe je Projekt; DRA selbst zuletzt (ca. 1375–1445).
- `_render()` zeichnet große Teile der Oberfläche neu (ab ca. 1528). Detailfilter arbeiten auf `this._preview.files` im Client (ca. 1520–1525).
- Das Diagnosepanel ist zwar als langlebige Komponente erhalten, aber häufige Parent-Updates können weitere Renderingkosten verursachen; Mobile-Messung fehlt noch.

**Folge:** Der Browser darf ab V2-50/60/90/100 weder die Auftragsreihenfolge noch Fortschrittswahrheit besitzen. Bei unbekanntem Gesamtfortschritt darf nicht einfach ein Prozentwert geraten werden.

## 4. Bereits vorhandene brauchbare V1-Bausteine

- `deployment.py`: `async_execute_deployment` führt Staging, Sicherung, Installation, Verifikation durch; blockierende Dateizugriffe über Executor.
- `preview.py`: `build_preview` ist synchrone/Executor-geeignete Berechnung.
- `diagnostic_store.py`: strukturierte, begrenzte und redigierte Ereignisse sowie Diagnoseläufe.
- `websocket_api.py`: `require_admin`, DEVELOPMENT-Prüfung, Locking und Fehlerfamilien; keine von UI-Flags abhängige Erlaubnis.
- `deployment.py`: Transaktionsjournal mit atomarer Schreibstrategie vorhanden, jedoch kein dauerhaftes operationsbezogenes Journal.

## 5. Fehlende V2-Fähigkeiten und Abnahmebelege

| Fehlende Fähigkeit | Zielphase | Status |
| --- | --- | --- |
| Servereigene `operation_id`, List/Get | V2-20/30 | Nicht aktiv |
| Clientunabhängige Taskverwaltung | V2-30 | Nicht aktiv |
| Persistente Auftragszustände/Recovery | V2-40 | Nicht aktiv |
| Echte, vergleichbare Backend-Fortschrittsdaten | V2-50 | Nicht aktiv |
| Vorschau-Pagination, stabile Reconnect-Sicht | V2-60 | Nicht aktiv |
| Install/Restore/Batches serverseitig orchestriert | V2-70–100 | Nicht aktiv |
| Subscribe/Unsubscribe ohne Polling-Sturm | V2-110 | Nicht aktiv |
| Ein kanonisches V2-Diagnose-Exportmodell | V2-115 | Nicht aktiv |
| Reduzierte Mobile-Renders, Akkuvergleich | V2-120/130 | Nicht gemessen |
| Reale V1-Referenz CPU/RAM/I/O | V2-05 | Offen |
| Reale Netzwechsel-/Recoveryprüfungen | V2-160 | Offen |

## 6. Erste isolierte Vorarbeit

`operation_model.py` ist ein unabhängig prüfbares Entwurfsmodul, keine laufende Backendintegration. Es kann Zustände und echte Zähler beschreiben, aber **es erteilt keine Schreibfreigabe und startet keine Operationen**. Ohne Operationsmanager/Persistenz/WebSocket-Vertrag sind die V2-20 bis V2-40-Freigaben ausdrücklich offen.

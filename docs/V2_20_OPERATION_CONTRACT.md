# V2-20 – Operation Model v0 (isolierter Entwurf)

Status: **DRAFT**. Begleitend zur laufenden V2-10-Analyse vorbereitet. Kein Codepfad in V1-Laufzeit verdrahtet.

## Zweck

Das reine Pythonmodul `custom_components/deploy_relay/operation_model.py` beschreibt erlaubte Operationsarten, Phasen und Zustände. Es ist unabhängig von Home Assistant, Netzwerk und Datenträgeroperationen. Es führt selbst **keine** Installation aus und vergibt **keine** Zugriffsberechtigung.

## Operationstypen und Status

Typen: `source_check`, `preview`, `install`, `restore`, `batch_check`, `batch_install`, `self_update`.

Zustände: `queued`, `waiting_for_resource`, `running`, `cancel_requested`, `success`, `failed`, `recovery_required`, `cancelled`, `interrupted`.

Terminal: `success`, `failed`, `recovery_required`, `cancelled`, `interrupted`. Ein Terminalzustand darf nicht in einen aktiven Zustand zurückwechseln. Der Zustand `cancel_requested` ist nur eine Anforderung: eine bereits begonnene Mutation darf sie bis zu einem sicheren Transaktionsende zurückstellen und ggf. noch erfolgreich beenden. Späterer Operation Manager muss Cancel- und Unlock-Grenzen unabhängig erzwingen.

## Fortschritt

- `current_index` und `total_count`: echte gemessene Zähler der **aktuellen Phase**.
- `phase_percent`: 0–100 % nur bezogen auf diese Phase, bei bekannten Zählern.
- `progress_percent`: **gesamtbezogen**; zunächst `null`, falls nur lokale Phasenzähler vorliegen. Nur wenn der Aufrufer nachweislich einen globalen Gesamtzähler liefert, darf er `overall=True` setzen.
- `progress_percent` wird vor einem bestätigten Erfolg höchstens 99; bei `SUCCESS` wird 100 gesetzt. Ohne belastbare Zählung bleibt der Gesamtwert unbekannt.
- Der Wert darf nicht zwischen Phasen abnehmen. Ein fortbestehender Wert aus einer früheren globalen Messung ist beim Wechsel zu unmessbaren Phasen **nicht exakt**.
- Rollback-/Recoveryfortschritt wird später als eigene Zeitlinie aufgenommen, nicht in einen normalen Installationsbalken hineingemischt.

## Datengrenze

Snapshots enthalten ausschließlich bekannte Felder, numerische Zähler und generische Fehlerfamilien. Kein beliebiges Dictionary, keine Tokenwerte, privaten Repository-URLs, Dateipfade, Exceptiontexte oder HTTP-Header. Projektbezug als begrenzte interne Kennung und Gitquelle nur als vollständig geprüfte Commit-SHA.

Wichtige Grenzen: Das Model selbst schützt nicht davor, dass ein zukünftiger aufrufender Adapter intern eine falsche `overall=True`-Angabe meldet, die Schreibfreigabe überspringt oder eine unsichere Quelle übergibt. Deshalb sind Adapter-Contract-Tests, Sicherheitsprüfung, Persistenz-, Cancel- und reale HA-Tests vor der Runtimeverdrahtung Pflicht.

## Noch offene Punkte für V2-20-Abnahme

- Das endgültige Schema mit den bereits vorhandenen Diagnose-Run-IDs und HA-Subentries abgleichen.
- Ergebnis- und Zeitangaben im Operationsjournal versionieren.
- Gemeinsame Idempotenz- und Speichergrenzen mit V2-30 festlegen.
- Zusätzliche Tests für fehlerhafte Snapshots, Shutdown und Recovery ergänzen.
- Keine Modell- oder Laufzeitphase als abgenommen markieren, bevor die verbindlichen Gates erfüllt sind.

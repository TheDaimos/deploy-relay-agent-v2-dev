# DRA V2 DEV 0.1.59 – Vertrauliche Repositoryzuordnung, Projektkennungen und Log-Leeren

**Datum:** 11.10.2026  
**Zweig:** `feature/v2-10-inventory-operation-contract`  
**Status:** Implementiert, statische CI und HA-Realabnahme getrennt verifizieren. **Keine Installation und kein Neustart aus V2.**

## Entscheidung und Umfang

Nach den echten HA-Tests mit unterschiedlichen Projekten wurde eine Zuordnung von Screenshot, Prüfung und Diagnoseexport benötigt. Der Projektinhaber hat bestätigt, dass **Repositorynamen im ausschließlich privaten Exportarchiv ausdrücklich zulässig** sind; zusätzlich werden kurze Projektkennungen verwendet.

- **Projektkennung** `P-XXXXXXXXXXXX`: Auf dem HA-Server aus dem normalisierten Repositorynamen und einem **nur zur aktuellen Runtime gültigen zufälligen geheimen Schlüssel** errechnet. Das Projekt erhält innerhalb desselben V2-HA-Laufs bei wiederholten Prüfungen dieselbe Kennung. Andere Projekte erhalten andere Kennungen. Nach HA-Neustart kann die Kennung wechseln. Das Kennzeichen stellt weder eine Git-Zugriffsberechtigung noch einen Eigentumsnachweis dar.
- **Prüfkennung:** Die bereits vorhandene zufällige 128-Bit-`run_id`. Die Oberfläche zeigt die ersten 12 Hexzeichen, der vollständige Wert wird in den Berichten exportiert.
- **Herkunft:** Repositorynamen werden ausschließlich dem serverseitig durch die administrative Projektliste bestätigten Aufruf zugeordnet; kein Name aus JavaScript, einer hochgeladenen Diagnose oder einem ungeprüften Browserfeld darf die Protokolle anreichern.
- **Oberfläche und lokaler JSON-Download/Zwischenablage:** Nur `project_ref` und `run_id`, **keine Repositorynamen** innerhalb der Diagnose. Die vertrauliche Zuordnung wird nicht über den allgemeinen Logs-WebSocket weitergegeben.
- **Ausdrücklich angeforderter privater Git-Export:** Zusätzlich `snapshot.private_source_repository = "Owner/Repo"` in demselben begrenzten Diagnose-Umschlag. Das ist **nur** beim nachweislich privaten, genau erlaubten Ziel `TheDaimos/Project-Log-And-Export` zulässig. Ein Export mit Repositoryzusatz wird beim Wiederanlauf der Warteschlange nur für dieses Archiv angenommen. Weitere Tests/Messarten bleiben vom Zusatz ausgeschlossen.
- **Historische Logs:** Ältere, bereits exportierte Diagnosen werden **nicht** stillschweigend ergänzt oder umgeschrieben. Nicht zuordenbare Prüfungen behalten `project_ref=null` und enthalten keinen willkürlichen Repositorynamen.

## Kompaktes „Leeren“ neben „Logs“

- Die Verwaltungsansicht erhält ein dezentes `Leeren` direkt neben der goldenen `Logs`-Schaltfläche, **nur wenn der HA-Server mindestens einen aktuellen, flüchtigen Quellprüfbericht meldet**.
- Kein sofortiges Löschen: Zuerst erscheint in der Logleiste eine Sicherheitsabfrage mit **„Ja, leeren“ / „Abbrechen“**.
- Admin-only WebSocket `deploy_relay_v2_dev/deployment/logs/clear` verlangt `confirm=true` und die vollständige `expected_run_id` des neuesten dem Benutzer angezeigten Ereignisses. Ist zwischenzeitlich ein anderer Prüflauf hinzugekommen, wird das Leeren abgelehnt und muss neu angefordert werden.
- Gelöscht werden ausschließlich die **maximal acht flüchtigen** Einträge samt nur serverseitiger Repositoryzuordnung der laufenden HA-Sitzung. **Keine** GitHub-Archivdatei, keine HA-Projektdatei, keine Zugangsdaten, kein dauerhafter Messauftrag und keine Export-Wiederholwarteschlange werden angetastet.

## Architektur- und Sicherheitsgrenzen

- Neue Funktionsänderungen nur im erlaubten DRA V2 DEV-Featurezweig. DRA V1 DEV/PUB, DRA V2 PUB/`main`, WeatherRouter und das private zentrale Archiv bleiben unverändert.
- `source_diagnostics.py` validiert `project_ref` streng und speichert Repositorynamen nur in der nicht serialisierten, flüchtigen Serverzuordnung pro `run_id`.
- `git_measurement_export.py` akzeptiert Repositorynamen ausschließlich über den expliziten `private_source_repository`-Parameter des **privaten** Exportaufrufs, nicht über die normalen Download- oder JSON-Schnittstellen. Für eine gemischte oder gefälschte Wiederholwarteschlange greifen zusätzliche strikte Schemakontrollen.
- Quellvorschau, GitHub-Zugriff und Eigentumsnachweis bleiben schreibgeschützt und fehlersicher. `0.1.58` zeigte mehrfach nicht erreichbare Commit-/GitHub-Stufen; eine Änderung der Diagnoseorganisation ist **keine Fehlerbehebung** an diesen Vorgängen.

## Automatisierte Prüfungen / Realtest

In den vorhandenen Tests werden die Stabilität innerhalb der HA-Laufzeit, die abweichenden Kennungen für verschiedene Projekte, das Nicht-Weitergeben von Repositorynamen an gewöhnliche Protokolle, die private Git-Anreicherung, Wiederholwarteschlangenvalidierung und das ausschließlich bestätigte flüchtige Leeren abgedeckt. Ein zusätzlicher Oberflächentest stellt den bedingten Schalter mit Sicherheitsabfrage sicher. WebSocket-Isolation und Admin-Pflicht bleiben verbindlich.

**HA-Abnahme:** Nutzer aktualisiert selbst über den bisherigen DRA-V1-Weg auf 0.1.59, startet für zwei verschiedene Projekte je eine schreibgeschützte Vorschau, prüft die sichtbaren Projekt-/Prüfkennungen, exportiert bei Bedarf eine davon explizit ins private Git-Archiv und bestätigt `Leeren` zunächst mit Abbrechen. Anschließend Leeren bestätigen, prüfen, dass die Einträge verschwinden, und verifizieren, dass frühere Git-Dateien weiterhin vorhanden sind. Kein automatischer Neustart und keine Installation durch V2.

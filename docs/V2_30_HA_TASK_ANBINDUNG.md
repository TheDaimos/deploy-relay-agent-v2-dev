# V2-30 – Home-Assistant-Hintergrundaufgaben (vorbereiteter Adapter)

> **Aktueller Nachtrag (08.10.2026):** Der untere Text beschreibt den damaligen Entwurfsstand. Der getrennte Adapter ist inzwischen ausschließlich im schreibgeschützten `deploy_relay_v2_dev`-Testlabor eingebunden. Zwei Sitzungen/Browserneuladen und V1-Parallelbetrieb wurden auf dem einzigen HA-DEV erfolgreich getestet. V2-40 besitzt nun einen geprüften Journalbaustein; gezielte Wiederherstellung aktiver Aufträge nach HA-Neustart bleibt als Realtest ausstehend. Keine Anbindung an V1 oder schreibende Operationen. Siehe `docs/V2_40_STATISCHE_ABNAHME_2026-10-08.md`.

Stand: 2026-10-08 · Status: **isolierter Entwurf, keine produktive Anbindung**.

## Technische Entscheidung

Langlaufende **schreibgeschützte** DRA-Vorschauaufträge sollen nach ausdrücklicher Administrator- und Quellenprüfung über `ConfigEntry.async_create_background_task(hass, coroutine, name, eager_start=False)` erzeugt werden. Nicht über die Antwort-Coroutine eines WebSocket-Clients und nicht über ein unkontrolliertes `asyncio.create_task` im aktiven HA-Integrationscode.

Die öffentliche Home-Assistant-Dokumentation empfiehlt ConfigEntry-eigene Taskmethoden für integrationsgebundene Coroutinen. Außerdem müssen Ressourcen beim Entladen eines Konfigurationseintrags kontrolliert aufgeräumt werden.

Quellen:
- https://developers.home-assistant.io/blog/2024/03/13/deprecate_add_run_job/
- https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-entry-unloading/
- https://github.com/home-assistant/core/blob/dev/homeassistant/config_entries.py

## Heutige Implementierung

`ha_preview_task_factory.py` ist ein **kleiner, nicht aktivierter Baustein**, der dem isolierten `ReadOnlyTaskSupervisor` die Schnittstelle zum Home-Assistant-ConfigEntry anbietet. Er verwendet `eager_start=False`, damit nach dem Registrieren eines Auftrags die Taskzuordnung zunächst erstellt werden kann.

Die automatische Prüfung `test_ha_preview_task_factory.py` benutzt einen nachgebildeten ConfigEntry und simuliert:
- Auftragsstart über den Entry statt über den anfragenden Browser,
- unabhängiges Weiterlaufen des Auftrags nach Rückkehr des Startaufrufs,
- Abbruch einer rein schreibgeschützten Vorschau durch Entladen des Entry mit eindeutigem Status `interrupted`,
- Ablehnung einer fehlenden/ungültigen Taskschnittstelle.

Das ist **kein echter Home-Assistant-Test**. Weder `__init__.py` noch bestehende `deploy_relay/panel/*`-WebSocket-Befehle verwenden den Adapter bislang.

## Zwingende nächste Sicherheitsprüfungen

1. Admin- und Quellberechtigung bei Start **und** List/Get/Cancel; Auftragskennung ist niemals eine Berechtigung.
2. Nur echte schreibgeschützte Vorschauarbeit an den Adapter binden; keine beliebigen Task-Funktionen aus Eingaben konstruieren.
3. Bestehenden `resource_lock` und Quell-/Manifest-/Pfadprüfungen des DRA-V1-Backends berücksichtigen.
4. HA-Test mit echtem ConfigEntry-Setup/Unload und Verbindungsausfall; keine Behauptung einer erfolgreichen Realabnahme aus Fakes.
5. Frühestens nach dokumentiertem Persistenz-/Recovery-Entwurf mutierende Install-/Restore-Aufträge verlagern: sichere Transaktionen dürfen **nicht** mit dem schreibgeschützten Unload-/Cancel-Verhalten abgebrochen werden.
6. Taskbeendigung während eines registrierungsbedingten Rennens und bei fehlgeschlagenem HA-Auftragseintrag gezielt prüfen.
7. Erst nach den Gates neue admin-only `deploy_relay/operations/*`-Befehle ergänzen.

**Freigabestatus:** V2-30 weiterhin DRAFT. V1-FINAL, V2-PUB, HACS, bestehende Installations- und Wiederherstellungspfade bleiben unverändert.

# DRA V2 DEV 0.1.74 – parallele Projektupdates mit unveränderter V1-Engine

**Stand:** 12.10.2026 · `feature/v2-10-inventory-operation-contract`  
**Ziel:** Die in 0.1.73 eingeführten echten V1-basierten Installationsaufträge können jetzt für **bis zu vier unabhängige Projekte gleichzeitig** auf Home Assistant laufen. **Keine zweite Installationsengine, kein systemweiter V1/V2-Sperrdienst, kein neuer aufwendiger Testschlachtplan.**

## Tatsächlich umgesetzt

- **Vier gleichzeitige HA-eigene V1-Installationsaufträge:** Nur die dedizierte V2-Schreibregistrierung hat `max_mutating=4`, während ihre bisherigen konservativen Vorgaben für andere Verwendungen unverändert bleiben. Es wird kein fünfter paralleler Schreibauftrag angenommen.
- **Zielverzeichnis-Sperren pro Auftrag:** Vor Zulassung werden aus dem echten V1-Manifest mit `build_plan` validierte Gruppen-Zielpfade reserviert; identische, verschachtelte und Groß-/Kleinschreibung abweichende Ziele sind untereinander ausgeschlossen. Ein Projekt kann nicht doppelt gleichzeitig geschrieben werden. Reservierungen werden erst nach abgeschlossener V1-Transaktion oder deren Rückfall freigegeben.
- **Idempotente Wiederanfragen:** Derselbe gültige Auftragsnachweis erzeugt keinen weiteren Schreibvorgang. Eine anders gebundene Wiederanfrage mit derselben ID wird verweigert.
- **V1-Journale im Parallelbetrieb:** Ein noch nicht abgeschlossenes Journal wird ausschließlich akzeptiert, wenn sein *exakter* Transaktionsname zuvor von einer tatsächlich laufenden V1-Engine gemeldet wurde. Alte, fremde, ungeklärte oder nach HA-Neustart verwaiste Journale sperren weitere Updates. Das bewährte V1-Format und die V1-Backup-/Rollback-Funktionen bleiben erhalten.
- **Projektbezogene Freigaben:** Für verschiedene Projekte dürfen zwei bestätigte Vorbereitungen gleichzeitig bestehen. Jede bleibt an das jeweils eigene Repository, den festen Git-Commit und ihre nur einmal verwendbare Bestätigung gebunden.
- **Gemeinsamer Statusabruf:** Der bestehende Admin-WebSocket-Befehl `deployment/status` liefert zusätzlich bis zu zwölf aktuelle Auftragsstatusdatensätze. Keine weitere WebSocket-Strecke notwendig. Die V2-Oberfläche zeigt parallel laufende Projekte und ermöglicht das Auswählen eines anderen Projekts, während dessen oder ein anderes Update serverseitig weiterarbeitet.
- **Version:** `manifest.json`, `const.py`, JavaScript-Oberfläche und zugehörige Versionsprüfungen einheitlich **0.1.74 DEV**.

## Gebündelte automatische Abnahme

**GitHub Actions 38215272085 – SUCCESS** ([Prüflauf](https://github.com/TheDaimos/deploy-relay-agent-v2-dev/actions/runs/38215272085)), Codecheckpoint `de81e28299c272ff0f0515a0e9aee9149835327a`.

Enthalten sind bestehende Funktionstests für die **echte V1-Engine** (synthetische Dateiinstallation, tatsächliche Sicherung, Verifizierung, erzwungener Rückfall), die 0.1.73-Backend-/Admin-/Bestätigungsfälle sowie die neuen zusammenhängenden Tests:

1. Zwei verschiedene Installationsaufträge erreichen nachweislich beide den Zustand `running`, bevor einer abgeschlossen ist.
2. Bis zu vier unabhängige Aufträge laufen, der fünfte wird abgewiesen.
3. Gleiches Projekt oder überlappende Eltern-/Unterverzeichnisse dürfen nicht doppelt geschrieben werden.
4. Aktives, exakt erkanntes V1-Transaktionsjournal blockiert nicht ein anderes Projekt; ein altes unvollständiges Journal sperrt neue Installationen.
5. Status- und Zielreservierungen werden nach Abschluss freigegeben.
6. Die Browseroberfläche zeigt zwei laufende Projekte gemeinsam und wechselt zwischen ihnen, ohne die serverseitigen Aufträge anzuhalten.

**Ehrliche Einschränkung:** Die Parallelitätsprüfungen verwenden kontrollierte synthetische Engine-Aufträge; die originale V1-Engine selbst wurde separat mit echtem Dateischreiben/Rückfall auf Testdateien geprüft. **Echte gleichzeitige Installationen auf einer HA-Instanz, echte Unterprozess-Ausführung, tatsächliche Leistungssteigerung und HA-Neustart während Mutation sind noch nicht real abgenommen.** Es wäre falsch, diese als bewiesen zu melden.

## Als Nächstes: eine gemeinsame HA-DEV-Abnahme

0.1.73 wurde nicht separat installiert; **0.1.74 bündelt beide Entwicklungsblöcke**. Daher kein Zwischenupdate nachholen.

Die gebündelte Realabnahme soll in **einer** Aktualisierungsrunde und maximal einem technisch erforderlichen Neustart stattfinden:

- Installierte und geladene V2-Versionen stimmen mit **0.1.74 DEV** überein; bisherige G2-/Diagnosewege bleiben verfügbar.
- Kontrollierter echter V2-Updateauftrag für ein geeignetes unkritisches Projekt: V1-Quellprüfung/Sicherung/Installation/Verifikation, eindeutige HA-Auftragskennung und Neustartinformation.
- Währenddessen Oberfläche verlassen oder Browser wechseln; der HA-Auftrag muss weiterlaufen und sein Status erneut auffindbar sein.
- Falls zwei **geprüft voneinander unabhängige**, unkritische Projektupdates anstehen, werden deren parallele Bearbeitung und eindeutige Statusanzeige in demselben Prüfblock abgenommen. **Keine erzwungene Störung oder absichtlich riskante zweite Installation nur für ein zusätzliches Testhäkchen.**
- Rückfall wird bereits automatisch auf echten **synthetischen Dateien** geprüft; kein absichtlich zerstörtes produktives HA-Projekt und kein ungeprüfter Neustart mitten in einer Dateitransaktion.

Keine HA-Installation, kein HA-Neustart, kein Merge von Draft-PR #2 oder Änderungen an V1/PUB/main/WeatherRouter durch den Assistenten.

**C.K. – Eine Idee weiter gedacht.**

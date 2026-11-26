# DRA V2 DEV 0.1.84 – Quelle & Version aktualisieren

**Stand:** 13.10.2026. CI erfolgreich, HA-Realabnahme noch offen.
**Zweig:** `feature/v2-10-inventory-operation-contract`
**Code-Checkpoint:** `dcebe1add91f11de671220b0cae25f631e73bd70`
**CI:** [38407275152](https://github.com/TheDaimos/deploy-relay-agent-v2-dev/actions/runs/38407275152) – SUCCESS.

## Implementiert

- Eigene Schaltfläche **Aktualisieren** rechts in `Quelle & Version`, unabhängig vom allgemeinen Aktualisieren und von der Deployment-Vorschau.
- Administratorgeschützte WebSocket-Abfrage `projects/source_head`, ausschließlich lesende GitHub-GET-Anfragen. Der Server verwendet den gespeicherten Projektzugang oder die bestehende Git-Leseanmeldung; keine neuen Zugangsdaten und keine Änderung im Test-Repository.
- Standardzweig über GitHub-Repositoryinformationen auflösen; den Commit der gewählten Git-Referenz unabhängig von Manifest, Inventar und Installation abfragen.
- Bei verändertem Commit eine bisherige Vorschau und Installationsvorbereitung ungültig machen; ein unveränderter Commit behält die gültige Vorschau.
- Resultat und Fehlergrund innerhalb der Quellenkarte anzeigen. Bei Versionabweichung, laufendem Auftrag oder bereits vorbereiteter Installationsfreigabe bleibt die Schaltfläche gesperrt.
- Keine automatischen Installationstätigkeiten und keine Änderungen an DRA V1, V2 main oder anderen Projekt-Repositories.

## Gebündelte HA-Abnahme

1. 0.1.84 DEV mittels DRA V1 installieren, HA neu starten und Version 0.1.84 für Oberfläche und Python-Laufzeit prüfen.
2. Unter Quelle & Version `Test-Repo-DRA-V2` wählen und **Aktualisieren** betätigen; neuester Commit soll erkannt werden.
3. Eine normale schreibgeschützte Vorschau berechnen; bei erneuter Aktualisierung mit gleichem Commit bleibt die Vorschau gültig.
4. Optional den Teststand ausschließlich über die zuvor real geprüfte **Test 2**-Funktion um eins erhöhen, dann **Quelle aktualisieren**. Der veränderte Commit muss angezeigt, die alte Vorschau gesperrt werden. Keine automatische Installation.
5. Ausgabe unter Audit/Logs nur bei Fehlern; keine zweite Testinstallation erforderlich.

**Hinweis:** Git-Quellstand-Aktualisieren berechnet nicht selbst die Änderungsliste und ist keine Installationsfreigabe. Die tatsächliche HA-Realabnahme entscheidet über Abschluss.

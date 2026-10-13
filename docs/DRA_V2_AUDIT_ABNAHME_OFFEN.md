# DRA V2 – Audit-Funktionsgruppe, verbindliche offene Abnahme

**Status: 0.1.77 DEV – CODE UND CI ABGESCHLOSSEN; HA-REALABNAHME OFFEN. ISSUE #9 BLEIBT OFFEN.**
**Nur Zweig:** `feature/v2-10-inventory-operation-contract`.
**Ausgangspunkt:** Audit-Oberfläche Commit `1e78da77384cc6617b6f2807d8723dcdc33c01a4`, CI 38251783919 erfolgreich – dies bestätigt NICHT die vollständige Audit-Funktion.

## Anforderungen und Abschlussbedingungen
- [x] Schaltfläche „Audit“ neben „Logs“, aufklappbar im Deployment-Hauptfenster ohne Untermenü
- [x] Moderne dunkle Tabelle, abgesetzte goldene Überschriften, farbliche Unterscheidung der Protokollstufen, mobil seitlich verschiebbar
- [x] Filter nach Stufe und Prüfphase, Suche, aufklappbare Details für vorhandene Quellprüfungsdaten
- [ ] **Serverseitige echte Auditereignisse** für die V1-Engine-Installationsphasen: Vorprüfung, Sicherung, Schreiben, Verifikation, Rückfall, Abschluss/Fehlschlag; mit realen Kennungen, Zeitstempeln, Phasen, Meldungen und Dauer
- [ ] Administrative, bereinigte, begrenzte und paginierte/ressourcenschonende Audit-Datenschnittstelle; keine Tokens, privaten Dateiinhalte oder unberechtigte Git-Schreibzugriffe
- [ ] Filter/Suche nach Projekt, Stufe, Vorgang, Phase und Kennung auf Basis tatsächlicher Ereignisse; Tabellenspalten nach DRA-V1-Vorbild
- [ ] Anzeige der lokalen deutschen Ortszeit durchgehend, UTC in gespeicherten/exportierten Ereignissen erhalten
- [ ] Zusammenhängende Vertrags-, Sicherheits- und Oberflächenprüfungen einschließlich realitätsnaher Ereignisfolgen
- [ ] CI auf dem freigegebenen Zweig vollständig erfolgreich und **eine** gebündelte HA-Realabnahme vor Fertigmeldung

## Wichtige Bestandsgrenze
`deployment/logs` liefert derzeit nur `runtime.source_diagnostics.entries()`, maximal acht Quellprüfungen, **keinen vollständigen Installationsereignisstrom**. Die UI darf Quellprüfungsphasen nicht als Installationsprotokolle ausgeben. Im Zweifel klar „noch nicht verfügbar“ anzeigen.

## Weitere verbindliche Projektregeln
GitHub Read-Only/Read-Write ist nur informative Token-Metadaten und keine lokale Installationsfreigabe. V1 und V2 main/PUB sowie andere Repositories unangetastet lassen. Draft-PR #2 offen lassen. Keine zusätzlichen Einzelupdate-/Neustartschleifen; V1-Engine wiederverwenden.

**Nicht schließen, bevor jede offene Anforderung anhand von Code, Prüfung und HA-Abnahme nachgewiesen ist.**

GitHub Issue: https://github.com/TheDaimos/deploy-relay-agent-v2-dev/issues/9

## Implementierungsfortschritt vom 12.10.2026

- Audit-Ereignisspeicher `deployment_audit.py` ergänzt: maximal 256 Einträge, UTC, geprüfte Phasen/Status und begrenzte Kennungen, ohne Dateiinhalte oder Tokens.
- `server_deployment_jobs.py` zeichnet echte V1-Engine-Phasen (staging, backup, install, verify_install, rollback) und terminale Zustände auf.
- Administratorgeschützte, rein lesende Schnittstelle `deployment/audit` und tabellarische Anzeige im bestehenden Audit-Bereich verbunden.
- Neue Vertragsprüfungen `tests/test_v2_deployment_audit.py` und bestehende Sicherheitsprüfungen erfolgreich; CI 38255519922.
- **Offen und nicht als fertig melden:** In-Memory-Audit übersteht keinen HA-Neustart; vollständige persistente Ereignishistorie, Export, tatsächliche HA-Realabnahme und der Abgleich der Darstellung mit der DRA-V1-Tiefendiagnose sind nicht abgeschlossen. Issue #9 offen lassen.
- **Keine HA-Installationsfreigabe:** Dieser Zwischenstand liegt ausschließlich im freigegebenen Featurezweig und ist noch nicht versioniert.

## 0.1.77 DEV – gebündelter Code-Checkpoint (12.10.2026)

**Git-Checkpoint:** `3323753b66b58dd71af761cc1f361b9a162e3ade`
**CI:** Lauf 38256815155 – SUCCESS.
**Nur Featurezweig; Draft-PR #2 nicht zusammenführen.**

Technisch implementiert und automatisch geprüft:
- Echte Ereignisse der V1-Engine in V2 `ServerDeploymentJobs`: Annahme, Start, Staging, Backup, Schreiben, Verifikation, Rollback und terminale Ergebnisse. Keine zusätzlichen V1-Schreibpfade.
- Administratorgeschützte `deployment/audit`-Schnittstelle, keine Dateiinhalte, Tokens, unkontrollierte Meldungen oder vollständigen Repositorynamen.
- Maximal 256 erlaubte Audit-Ereignisse und gesonderte dauerhafte HA-Speicherung `deploy_relay_v2_dev.deployment_audit`; abgeschlossene Aufträge werden gespeichert und nach HA-Neustart eingelesen. Bei beschädigter Historie wird nicht stillschweigend überschrieben.
- Audit-Schaltfläche neben Logs, aufklappbare Tabelle direkt im Deployment; Suche, Filter nach Projekt, Art, Stufe und Phase, farblich unterschiedene Kopf-/Datenzeilen und Zustände, aufklappbare Details.
- Echte kumulierte Laufzeit seit Installationsbeginn; Deutschland-Ortszeit in der Darstellung, UTC in Speicherung/JSON; lokaler JSON-Auditexport.
- Automatische Vertragsprüfungen, Speicher-Rundlauf und ungültige Daten geprüft.

**Noch ausdrücklich offen:**
- Einmalige gebündelte HA-Realabnahme mit V2 0.1.77: Audit öffnen, Quellprüfung und erste reale Testinstallation, Backup/Dateiergebnis/Abschluss sowie Audit nach erneuter HA-Laufzeit kontrollieren.
- Ereignisse aus unterbrochenen, noch nicht abgeschlossenen Aufträgen sind für Wiederherstellung ausschließlich durch die bestehenden V1-Transaktionsjournale abgesichert; im Audit werden Ereignisse anlässlich des abgeschlossenen Auftrags dauerhaft gespeichert.
- Die Quellprüfungsübersicht ist weiterhin auf acht Diagnosen begrenzt; die neue echte Installationshistorie auf 256 Ereignisse. Eine V1-identische unbegrenzte allgemeine Diagnose oder eigener privater Git-Auditexport wird nicht behauptet. Der bisherige private Git-Export der Quellprüfungen bleibt unverändert.

**Abnahme:** Issue #9 nur nach erfolgreichem realem Test schließen; vorab keine Fertigmeldung.

## 0.1.79 DEV – privater Audit-Export (12.10.2026)

- Ein eigener Audit-Knopf **Export nach Git** ist direkt in der aufgeklappten Audit-Tabelle ergänzt; bestehender lokaler JSON-Auszug bleibt erhalten.
- Serverroute `deployment/audit/export` nur für HA-Administratoren; Daten ausschließlich aus dem serverseitigen `deployment_audit` (keine Browser-Inhalte oder Tokens).
- Bestehende zentrale Git-Archivkonfiguration `TheDaimos/Project-Log-And-Export`, bestehende Token-Verwaltung, Privatprüfung und dauerhafte Wiederholwarteschlange werden wiederverwendet.
- Audit-Schema und Ereignisfelder werden explizit überprüft und bereinigt; höchstens 256 Einträge; die bestehende Exportgrößengrenze von 8192 Bytes bleibt unverändert. Ein zu großer Bericht wird sicher abgewiesen, nicht still gekürzt.
- CI 38270643989 für 0.1.79 DEV SUCCESS; Version `0.1.79`, Commit `26f42725b628344b7588ae3915b4f5c820b0cdea`.
- **Offen:** HA-Realtest des Git-Audit-Exports mit privater Repository-Bestätigung, inklusive Anzeige des erfolgreichen Exports; außerdem weiterhin verlässliche Wiederherstellung der 4/4-Abschlussanzeige nach HA-Neustart.
- Issue #9 bis zur vollständigen Abnahme offen lassen. Keine Änderung an DRA V1 oder V2 main.

## 0.1.80 DEV – Wiederherstellung 4/4 (13.10.2026)

- Der geführte Ablauf übernimmt nach Neuladen/HA-Neustart den letzten erfolgreich beendeten Auftrag aus dem bereits persistierten V2-Audit, projektbezogen und ausschließlich lesend.
- Anzeige: `4/4 · Letzter Abschluss (gespeichert)` mit Auftragskennung, Zeit und ausdrücklichem Hinweis, dass diese Anzeige **keine neue Installationsfreigabe** darstellt.
- Neue Vorschau über gesonderte Schaltfläche, die den historischen Zustand für die aktuelle Bedienung ausblendet; keine automatische Installation, kein Wiederverwenden eines abgelaufenen Bestätigungstokens.
- Aktuelle serverseitige Aufträge haben Vorrang vor historischen Erfolgen, eine neue aktuelle Vorschau ebenfalls.
- CI Lauf 38353864224 SUCCESS, Code-Checkpoint `694952699291b4e3d61929b34b9c5d06b5c529cc`.
- **Offen bis zur Realabnahme:** Nach Update auf 0.1.80 und HA-Neustart muss der historische 4/4-Abschluss wirklich erscheinen; anschließend für einen neuen Testcommit eine neue Vorschau und eine echte Installation auslösen und die unmittelbare 4/4-Umstellung belegen. Erst dann Issue #9 schließen.

## Realabnahme 13.10.2026 – 4/4 erfolgreich (DRA V2 0.1.80)

- **Historische 4/4-Wiederherstellung nach HA-Neustart:** vom Anwender per Screenshot bestätigt: 4/4, vollständiger grüner Fortschrittsbalken, vier grüne Schritte, Auftragskennung und Abschlusszeit.
- **Live-Übergang 3/4 auf 4/4:** vom Anwender per Screenshot bestätigt: Status `success`, Phase `complete`, 4/4, vollständig grüner Balken, alle vier Schritte grün. Auftrag `276ea7d711024fa0bba070f0a2bfc2a7`.
- **Audit-Export real verifiziert:** privates Archiv `TheDaimos/Project-Log-And-Export`, Datei `exports/deploy-relay-agent-v2/2026-10/diagnostics/2026-10-13T07-26-04Z__deploy-relay-agent-v2__0.1.80__diagnostics__ba8c23e429e236599f36d57833bbae53.json`; Schema `dra-v2-dev-git-audit.v1`, 16 Ereignisse von zwei erfolgreichen Aufträgen, einschließlich neuem Auftrag mit Phasen queued/running/staging/backup/install/verify_install/success.
- **Vorschau nach erster Installation:** Anwender prüfte 0 hinzugefügt / 0 geändert / 0 entfernt / 2 unverändert; Aktualisierung von Teststand 1 auf 2 wurde für die Live-Abnahme ausschließlich im isolierten Test-Repository durchgeführt.
- **Nächster separater Oberflächenblock:** Der G2-Verbindungstest wurde im Featurezweig aus der Deployment-Ansicht entfernt und die Laufzeitinformation komprimiert (Commit `f4bf55ee0f95f0cb868a9176cb3b30d85250737e`); noch nicht auf HA installiert.
- **Status:** Kernabnahme von Audit/privatem Export und Live-/historischem 4/4 abgeschlossen; offene weitere Verbesserungen getrennt bewerten. V1 und main nicht verändert.

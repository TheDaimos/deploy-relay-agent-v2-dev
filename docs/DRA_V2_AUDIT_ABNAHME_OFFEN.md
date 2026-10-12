# DRA V2 – Audit-Funktionsgruppe, verbindliche offene Abnahme

**Status: NICHT FERTIG / NICHT ZUR HA-INSTALLATION FREIGEGEBEN.**
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

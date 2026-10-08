# AGENTS.md – Öffentliche DRA-V2-Entwicklung

## Rolle und Geltungsbereich

Dieses öffentliche Repository ist die **V2-Entwicklungsquelle**, nicht der stabile HACS-Auslieferungskanal. Die ursprüngliche Integrationslaufzeit wurde ausschließlich aus dem bereits öffentlichen V1-Repository übernommen; Details stehen in docs/SOURCE_PROVENANCE.md.

**Startzustand:** Home-Assistant-Integration V1.0.0 als unveränderte Referenz. V2-Laufzeitentwicklung noch nicht begonnen, keine V2-FINAL-Freigabe.

## Verbindliche Regeln

1. Erst V1-Freigabe und Sicherheitsreferenz vollständig abnehmen; danach sequenziell V2 entwickeln.
2. Keine unveröffentlichte private Git-Historie, Diagnoseexporte, Backups, Erweiterungen, Zugangsdaten, interne IP-Adressen, lokalen Systeme oder personenbezogenen Dateien importieren. Immer die öffentliche Freigabefähigkeit vor einem Commit prüfen.
3. Keine zusätzlichen Funktionen in den stabilen V1-HACS-Auslieferungskanal einbringen, solange sie nicht separat freigegeben sind.
4. DRA startet schreibgeschützt/LOCKED. Schreibzugriff braucht explizite Freigabe und darf nach Home-Assistant-Neustart nicht dauerhaft aktiv bleiben.
5. Bewegliche Git-Quellen vor Vorschau und Installation auf einen exakten Commit-SHA auflösen. Quellen nicht still zwischen Vorschau und Installation wechseln.
6. Keine unkontrollierten Dateisystemziele, Path Traversal, beliebige Skripte oder privilegierte Shell-Ausführung ermöglichen.
7. Vor jeder Mutation eine gültige Sicherung anlegen; danach prüfen. Ein Fehler muss zu einem nachweisbar erfolgreichen Rückfall oder einem klaren Wiederherstellungszustand führen.
8. Clientverlust darf künftig keinen laufenden Auftrag abbrechen oder den Serverzustand unklar lassen. Die Benutzeroberfläche darf nicht Besitzer kritischer Abläufe sein.
9. Home Assistant in der Haupt-Ereignisschleife nicht durch blockierende Dateioperationen, Prüfsummen, Git-Daten oder Massendatenverarbeitung belasten.
10. Diagnoseereignisse vor Speicherung und Export redigieren. Keine Tokens, Projektdateiinhalte, privaten Metadaten oder unbeschränkten Protokollbestände veröffentlichen.
11. Schreibende Operationen und Home-Assistant-Neustart verlangen eigenständige, geprüfte Admin- und Bestätigungsschranken. Kein stiller oder erzwungener Neustart.
12. Jede Entwicklungsstufe benötigt nachvollziehbaren Quellstand, Tests, Dokumentation und reale Home-Assistant-Abnahme dort, wo statische Prüfungen nicht ausreichen.
13. GitHub Actions mit möglichst geringen Berechtigungen, öffentlichen Standard-Runnern und ohne pauschalen Artefaktupload. Keine privilegierte Ausführung fremder Pull Requests.
14. Änderungen an Lizenz, offiziellen Logos und veröffentlichten Markenrechten nur im Einklang mit LICENSE, COPYRIGHT.md und BRANDING.md.
15. Eine Änderung am Hauptzweig stellt weder ein V2-Installationspaket noch eine HACS- oder FINAL-Freigabe dar.

## Vor Arbeitsbeginn lesen

- README.md
- docs/V2_ROADMAP.md
- docs/PUBLIC_DEVELOPMENT_POLICY.md
- docs/SOURCE_PROVENANCE.md
- docs/SECURITY.md
- CONTRIBUTING.md

## Ablauf

Vor umfangreichen Änderungen zuerst den aktuellen Code prüfen und die Stufe aus docs/V2_ROADMAP.md ermitteln. Eingriffe klein halten und Tests ergänzen. Jeden Arbeitsstand über Pull Requests prüfen; große Umbauten nicht unbemerkt in den Hauptzweig übernehmen.

**C.K. – Eine Idee weiter gedacht.**

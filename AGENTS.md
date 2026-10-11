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

## Vorrangiger Produktauftrag – Kurskorrektur 12.10.2026

**Ausdrückliche Anweisung des Projektinhabers:** DRA V2 ist die **direkte Weiterentwicklung und der spätere Ersatz von DRA V1**, **keine** vollständige Neuerfindung der funktionierenden V1-Installationsengine und **keine** Infrastruktur zur dauerhaften parallelen Verwaltung von V1 und V2. **Oberste Umsetzungspriorität:** V1-Quellprüfung/Staging/Backups/Installation/Restore/Rollback in V2 weitgehend übernehmen, dazu echte **Mehrkern-/Parallelverarbeitung** und **serverseitige eigenständig weiterlaufende Installationsaufträge**; bereits entwickelte V2-Oberfläche erhalten.

Die umfangreichen historischen G3-/G4-/G5-Konzepte sind **nicht länger sequentiell abzuarbeitende Neuentwicklungsblöcke**, sondern nur Sicherheits-Checkpunkte der bewährten übernommenen Engine. Keine weitere separate Besitz-/Sperrarchitektur für einen vom Betreiber nicht vorgesehenen dauerhaften V1/V2-Doppelbetrieb. **Ein** V2-Auftrag darf weiterhin nicht mit anderen Schreibern dasselbe Ziel verändern; während der DEV-Migration V1 nur vorübergehend als Installationsweg für V2 verwenden und beim Umstieg deaktivieren. Sicherungs-/Integritäts-/Rückfallgarantien von V1 müssen erhalten bleiben.

**Arbeitsweise:** funktionierender Anwendungscode vor weiterer Planung; verwandte Funktionen gebündelt entwickeln und CI-prüfen, wenige kombinierte HA-Abnahmen statt ständig neuer Versionsstände/Neustarts. Kein eigenmächtiger HA-Neustart, keine produktive Mutation, kein Merge von PR #2; V1-Code nur lesen/als öffentliche Basis im freigegebenen V2-Featurezweig adaptieren, **V1-Repositories selbst niemals ändern**. Die **Neufassung von `docs/V2_ROADMAP.md` vom 12.10.2026** gilt vor älteren Konzeptplänen.

## Verbindlicher beschleunigter Entwicklungs- und Abnahmeablauf

**Nutzerentscheidung vom 12.10.2026:** DRA V2 darf nicht durch kleinteilige Einzelabnahmen und wiederholte HA-Neustarts unnötig verzögert werden. Ab sofort gilt **Entwicklung in Funktionsgruppen mit gemeinsamer Testabnahme**, bei gleichbleibender Sicherheit und Präzision:

1. **Zusammengehörige Aufgaben bündeln:** mehrere kompatible UI-, Diagnose-, Backend-, Sicherheits- und Dokumentationsänderungen in einem überprüfbaren DEV-Entwicklungsblock umsetzen. Keine neue Versions-/Installationsrunde nur wegen einer kleinen Darstellungskorrektur. Größere Änderungen intern durch kleine, nachvollziehbare Commits und Tests absichern.
2. **Selbstständig bis zum prüfbaren Gruppenstand arbeiten:** Quellprüfung, Umsetzung, Negativtests, Automatisierung, CI, Korrekturen, Dokumentation und erneute CI ohne einzelne Benutzerbestätigungen erledigen, solange dies im genehmigten DEV-Featurezweig und ohne HA-/Produktivmutation möglich ist.
3. **Ein gebündelter HA-Realtest pro sinnvoller Entwicklungsgruppe:** im Prüfplan mehrere zusammenhängende, voneinander unabhängige Szenarien anbieten, nicht eine separate Installations-/Neustartrunde je Einzeländerung. Für mehrere kompatible Tests **eine** reguläre Installation und einen HA-Neustart nur wenn technisch nötig. Rein lesende Oberflächenänderungen benötigen nicht automatisch einen Neustart.
4. **Abnahme unterscheiden:** statische/isolierte Tests und CI können ohne HA-Nutzeraktion vollständig abgeschlossen werden; HA-Realabnahmen nur für tatsächlich nicht anders beweisbare Laufzeiteigenschaften. Harte Sicherheitsgrenzen bleiben eigene Kriterien, können aber innerhalb desselben Gruppenprüflaufs nachgewiesen werden. Nicht getestete Realfälle nicht als bestanden bezeichnen.
5. **Nutzeraufwand minimieren:** nicht für jeden Zwischenschritt Screenshots, manuelles Logkopieren, „Fertig“-Rückmeldungen oder Git-Exports verlangen. Vorhandene echte Ergebnisse im freigegebenen privaten Archiv selbst lesen. Dem Betreiber **eine kompakte gruppierte Prüfanweisung** erst geben, wenn alle vorbereitbaren Schritte abgeschlossen sind; klare erwartete Ergebnisse und nur bei Fehlern weitere Nachweise.
6. **Fehlerbehandlung ohne Update-Schleifen:** erkannte Test-/CI-Fehler selbst korrigieren und die komplette Prüfgruppe erneut automatisch testen. Unnötige UI-/Dokumentationskorrekturen bis zur nächsten gebündelten DEV-Version sammeln.
7. **Sicherheit unverändert:** kein Vorziehen von Schreibrechten, Überspringen von G3/G4-Gates, vermeintlichen V1-Übergaben, ungeprüften Backups oder Installations-/Neustartfreigaben. Änderungen an DRA V1, V2 main/PUB, WeatherRouter, dem privaten Archiv sowie Merge von PR #2 bleiben ohne gesonderte Nutzerfreigabe ausgeschlossen. Installation und HA-Neustart führt ausschließlich der Betreiber aus.
8. **Effizienz berichten:** den Fortschritt als **Entwicklungsgruppe mit konkreter erledigter Arbeit, offenen Blockaden und einem nächsten gebündelten HA-Prüftermin** kommunizieren. Keine künstlichen Warte-/Freigabeschritte zwischen technisch zusammengehörigen Teilaufgaben.

Diese Gruppenabnahme erfüllt Regel 12 (nachvollziehbare Tests/Dokumentation/HA-Realabnahme), ersetzt jedoch das frühere unnötige **eine Änderung → eine Version → ein Neustart → ein Einzelscreenshot**-Muster.

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

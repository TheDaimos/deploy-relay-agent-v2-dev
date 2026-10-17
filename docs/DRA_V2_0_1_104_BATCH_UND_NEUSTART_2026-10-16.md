# DRA V2 0.1.104 DEV – serverseitiges Sammelupdate und aufgeschobener Neustart
Stand: 16.10.2026. Nur Entwicklungszweig `feature/v2-10-inventory-operation-contract`.

## Architektur und Sicherheitsgrenzen
- Home Assistant besitzt und führt alle Installationsaufträge aus. Browser sind nur Bedien- und Beobachteroberflächen.
- Alle Änderungen verwenden weiterhin `ServerDeploymentJobs.start_verified` und damit den vorhandenen V1-Motor (Staging, Sicherung, Installation, Verifikation, Transaktionsjournal, Rückfall).
- Das neue Modul `batch_installation.py` plant höchstens acht aktive, registrierte Projekte. Selbstupdate, doppelte Projekte und überlappende Zielpfade sind untersagt.
- HA liest die vom jeweiligen Repository empfohlene Git-Referenz und verifiziert für jedes Projekt den festen Quellcommit und die örtliche Vorschau. Browser dürfen weder Zielpfade noch Git-Dateiinhalte als Deploymentspezifikation einreichen.
- Nur die ausdrückliche einmalige Administratorbestätigung des vorbereiteten Sammelauftrags kann die serverseitige Reihenfolge starten. Die Eigentümersitzung wird geprüft; ein anderes Gerät muss eine vorbereitete Sitzung ausdrücklich übernehmen.
- Teilinstallationen laufen **nacheinander**. Ein Fehler stoppt sämtliche noch nicht begonnenen Teilaufträge. Eine vorher erfolgreich installierte Anwendung wird nicht ungefragt rückgängig gemacht; die V1-Rückfallsicherung gilt jeweils pro Teilauftrag.
- Eine verlorene WebSocket-Startantwort berechtigt den Browser nicht zu einer erneuten Übermittlung. Zustand und Audit müssen zunächst gelesen werden.
- Neue Leseschnittstellen und alle schreibenden Sammelschnittstellen sind HA-Administratoren vorbehalten.

## Neustartbündelung
- Jede erfolgreich abgeschlossene und verifizierte Einzel- oder Teilinstallation mit `restart_required` fügt ihre Auftragskennung zu einem HA-Laufzeit-eigenen Neustartbestand hinzu.
- Ein weiterer unabhängiger Installationsauftrag wird dadurch allein nicht gesperrt.
- Die globale Beobachteranzeige nennt die Projekte und bietet **einen** gemeinsamen Neustart nach zweistufiger Bestätigung an.
- Ist ein Neustart bereits angefordert oder irgendeine Installation aktiv, wird keine zweite Neustartanforderung ausgeführt.
- Die Vormerkung gilt für die laufende HA-Laufzeit und erlischt bei einer neuen HA-Instanz. Ein Neustart führt niemals allein wegen der Vormerkung automatisch aus.
- **Offene Grenze:** Für eine durch bloßes Neuladen der DRA-Integration (ohne vollständigen HA-Neustart) erhaltene Vormerkung ist derzeit keine dauerhafte Speicherung implementiert. Nicht als über Integration-Neuladungen hinweg garantiert ausgeben.

## Bekannte Einschränkungen
- Vollständige projektübergreifende Abhängigkeitsauflösung ist **nicht** implementiert. Insbesondere WeatherRouter und Gewitterradar können fachliche Neustartabhängigkeiten besitzen. Quell- und Zielschutz sind vorhanden, aber damit ist die semantische Kompatibilität unterschiedlicher Anwendungen nicht bewiesen.
- Ein Batch ist **keine** einzige global atomare Transaktion; die Sicherheitsgarantien gelten einzeln. Es gibt keinen automatischen gemeinsamen Rückfall bereits erfolgreicher Projekte.
- Vorbereitungen sind 15 Minuten gültig, gehen nach HA-Neustart verloren und benötigen dann eine neue Quellprüfung.
- Die neue echte Sammelinstallation und die globalen Neustarthinweise besitzen automatisierte Tests; eine praktische Abnahme auf Home Assistant über Desktop, Android und iPad ist noch offen.
- DRA V1, `main`, PR #2, andere Repositories und private Diagnosearchive wurden nicht verändert.

## Bereits automatisiert geprüfte Negativfälle
- Kein Start ohne ausdrücklich gültige Sammelbestätigung.
- Zweiter Start mit derselben Bestätigung abgewiesen.
- Übernahme einer Vorbereitung durch anderes Gerät nur nach Bestätigung; früherer Controller verliert Startberechtigung.
- Abgelaufene Vorbereitungen nicht installierbar.
- Überlappende Zielpfade führen zum Abbruch der gesamten Vorbereitung.
- Wenn ein Teilauftrag fehlschlägt, starten spätere Teilaufträge nicht.
- Bis dahin erfolgreiche Teilaufträge behalten ihren nachgewiesenen Abschluss und ihren ausstehenden Neustartbedarf.
- Keine Installationsaufnahme durch Leseabfragen, Gerätewechsel oder Browseraktualisierung.

## Kompakte HA-Realabnahme (erst nach Installation der Kandidatenversion über DRA V1)
1. Nach Neustart Versionsgleichheit `0.1.104 DEV` von Oberfläche und HA-Python prüfen.
2. Isoliertes Testprojekt mit echten Dateiänderungen kontrolliert durchführen; HA-Auftragskennung, Fortschritt, Abschluss und Audit prüfen.
3. Desktop: Sammelupdate nur mit voneinander unabhängigen Testprojekten oder bewusst geprüften Quellständen vorbereiten. Für jeden Eintrag Commit, Referenz und Änderungszahlen vor der Bestätigung kontrollieren.
4. Android: Vorbereitete Sammelbedienung ausdrücklich übernehmen und genau einmal starten. Desktop und iPad als Beobachter öffnen, ohne erneutes Starten.
5. Auf alle serverseitigen Einzelabschlüsse warten, bei Fehler keine weiteren Schreibaufträge senden, Audit/Journal untersuchen.
6. Zwei unabhängig erfolgreich abgeschlossene Updates mit Neustartbedarf müssen einen gemeinsamen Neustart anbieten. HA ausschließlich auf ausdrückliche Bestätigung neu starten.
7. Nach Neustart installierte Versionsstände und Projektfunktionen erneut prüfen. Die tatsächliche HA-Abnahme gesondert dokumentieren.

Die erfolgreiche GitHub-CI bestätigt die Softwareprüfungen, **nicht** die reale Ausführung oder das Verhalten der drei Geräte.

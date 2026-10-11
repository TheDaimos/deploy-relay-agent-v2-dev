# DRA V2 DEV 0.1.68 – Getrennte Historieneinträge und einklappbare Hinweise

**Datum:** 11.10.2026  
**Verbindlicher Zweig:** `feature/v2-10-inventory-operation-contract`  
**Status:** Nur V2-DEV-Frontend, Versionspaar und zugehörige Prüfungen geändert. **HA-Realabnahme 0.1.68 ausstehend**, keine V2-Schreibfreigabe.

## Anlass aus dem HA-Realtest

In DRA V2 DEV 0.1.67 wirkte die Auftragsanzeige innerhalb von `Deployment → Logs` zu dicht: die als Textreihen gerenderten Aufträge erschienen optisch kaum voneinander getrennt. Der lange technische Erklärtext darunter verlängerte die Anzeige beträchtlich. Der Nutzer wünschte eine sichtbare Trennung der einzelnen Aufträge und einen platzsparenden Aufklappbereich für den erklärenden Text.

## Änderungen in der Oberfläche

1. **Stärkere Bereichstrennung:** Eine zurückhaltende goldfarbene Linie trennt die Quellprüfprotokolle optisch von der **serverseitigen Auftragshistorie**.
2. **Eigenständige Auftragskarten:** Jeder Auftrag hat eine separate dunkel-metallische Karte mit Kontur, Abstand, abgerundeten Ecken und diskretem Schatten. In jeder Karte sind die gekürzte Auftragskennung, der Zustand und der Zeitpunkt übersichtlich verteilt. Der Status besitzt ein eigenes, zurückhaltend farbiges Kennzeichen: Grün (damals erfolgreich), Rot (Prüfung fehlgeschlagen), Bernstein (unterbrochen), Blau (begonnen). Keine zusätzliche Auftragssteuerung; ausschließlich Darstellungsfarben.
3. **Erkennbare Rollfläche:** Die Historie bildet innerhalb der Protokollseite eine auf mobilen Geräten begrenzte, separat rollbare Liste. Bei mehr als drei Einträgen weist ein erklärender Text auf das Wischen innerhalb dieser Liste und die Anzahl gespeicherter Aufträge hin; kein Eintrag wird stillschweigend gelöscht oder nicht abgefragt.
4. **Klappbare Hinweise:** Der bislang permanent sichtbare untere Text zu Projektkennungen, CPU-Zeiten, Arbeitsprozessen und Datenschutz steht gemeinsam mit der Historien-Erläuterung unter **„Hinweise zu Protokollen und Datenschutz“**, zu Beginn **geschlossen**. Implementierung über natives `<details><summary>` für tastaturbedienbares Öffnen und Schließen. Der Öffnungszustand wird bei regulären Oberflächen-Neuzeichnungen beibehalten, damit die Ansicht nicht bei jeder Aktualisierung wieder einklappt.
5. **Unveränderter Kopf:** Die goldene **„Aktualisieren“**-Schaltfläche aus 0.1.67 bleibt erreichbar und funktioniert unverändert.

Der Native-Aufklappmechanismus nutzt etablierte HTML-Funktionen, keine neue Bibliothek. Zusammen mit der vorhandenen CSS-Rollfläche werden mobile Bildschirme besser genutzt.

## Sicherheits- und Datenschutzgrenzen

- **Nur Frontend/Version/Test**; die serverseitige Auftragshistorie und ihre maximale Aufbewahrung von acht Datensätzen sind unverändert.
- Keine neuen WebSocket-Aktionen, Berechtigungen oder Git-Exporte.
- Gespeicherte Historie enthält weiterhin keine Repositorynamen oder Projektdateien. Es wird nur die bereits vorhandene gekürzte Auftragskennung dargestellt. Alle dynamischen Felder durchlaufen die vorhandene Escaping-Funktion.
- Nach einem HA-Neustart ist eine neue Quellprüfung erforderlich; alte Erfolge werden nicht wieder freigegeben. Keine Installation, Sicherung, Wiederherstellung oder HA-Neustart durch V2.
- Nur das vorhandene Featurezweig-Repository geändert. DRA V1, V2 PUB/main, WeatherRouter, das private Exportarchiv und PR #2 bleiben unangetastet.
- Echte Diagnoseexporte weiterhin nur nach `TheDaimos/Project-Log-And-Export`.

## Isolierte Abnahme

- Python-Standardbibliotheksvertragstests sowie Python-/JavaScript-Syntax.
- Node-Oberflächentests für voneinander getrennte Statuskarten, Roll-Hinweis, standardmäßig geschlossenen Aufklappbereich, beharrenden Öffnungszustand bei Oberflächen-Neuzeichnung und weiterhin gesperrte Deployment-Schritte.
- Der bestehende 60-Sekunden-Verbindungstest bleibt unverändert; sein Laufzeit-Versionstor erwartet beim nächsten DEV-Stand 0.1.68.
- **CI-Lauf ergänzen nach endgültigem Erfolg; nicht vorzeitig Erfolg behaupten.**

## Ein einziger HA-Realtest nach grünem CI

Der Betreiber installiert DRA V2 DEV **0.1.68** mit DRA V1 und startet HA bei Bedarf vollständig neu. Dann öffnet er **Deployment → Logs**, prüft die voneinander getrennten Aufträge und klappt **„Hinweise zu Protokollen und Datenschutz“** einmal auf und wieder zu. Der neue Aufbau darf weder eine Quellprüfung starten noch Schreibrechte erlauben. Screenshot nur bei Auffälligkeiten erforderlich.

**C.K. – Eine Idee weiter gedacht.**

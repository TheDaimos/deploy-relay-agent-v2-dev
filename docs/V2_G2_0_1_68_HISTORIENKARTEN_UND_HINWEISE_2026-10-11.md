# DRA V2 DEV 0.1.68 – Getrennte Historieneinträge und einklappbare Hinweise

**Datum:** 11.10.2026  
**Verbindlicher Zweig:** `feature/v2-10-inventory-operation-contract`  
**Status:** V2-DEV-Frontend 0.1.68 **HA-real bestätigt** (Screenshots vom 11.10.2026, 20:57 Ortszeit); keine V2-Schreibfreigabe. Die angekündigte weitere Verdichtung des Statusbereichs bleibt ausdrücklich ein **separates Folgeupdate**.

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
- **CI-Lauf erfolgreich:** [GitHub Actions 38164735204](https://github.com/TheDaimos/deploy-relay-agent-v2-dev/actions/runs/38164735204) auf Entwicklungscheckpoint `928e3dfb651f56ef8aff3012e3ef0ca40f438152`. Python-Vertragstests, Syntaxprüfungen, JavaScript-Oberflächenprüfungen einschließlich der neuen Karten- und Aufklappbereichstests sowie Ausschluss von Artefaktveröffentlichungen sämtlich **SUCCESS**. Folgende Änderungen betreffen nur die bereinigte Dokumentation und den Projektkontext. Die HA-Realabnahme steht weiterhin aus.

## Nachträgliche HA-Sichtabnahme 0.1.68

Die reale Companion-App-Ansicht bestätigt die deutlich getrennten Auftragskarten mit eigenständigem Statusabzeichen, dezenter goldener Bereichstrennung und den standardmäßig geschlossenen Bereich `Hinweise zu Protokollen und Datenschutz`. Die goldene Aktualisierungsschaltfläche funktioniert weiterhin; die Oberfläche zeigt den zuletzt bestätigten aktuellen Stand an. Der alte G2-Netzwechselauftrag ist noch sichtbar. Der geschlossene Aufklapper und die auf dem Mobilgerät lesbaren Karten sind **abgenommen**. Keine weitere Korrektur dieser Karten erforderlich.

Die Ansicht zeigt zudem mehrere ältere **„Damals erfolgreich“**-Datensätze nach dem Versionswechsel samt üblichem HA-Neustart. Dies belegt die Wiederanzeige **bereits abgeschlossener** historischer Aufträge nach dem Restart; es ersetzt **nicht** den noch offenen Test mit HA-Neustart **während eines laufenden** G2-Testauftrags.

### Separat gewünschter Folgeauftrag – Statusbereich weiter verdichten

**In V2 DEV 0.1.70 jetzt im Featurezweig implementiert, aber noch nicht HA-real abgenommen; erst nach G2-Retry-Test von installierter 0.1.69 aktualisieren.** Siehe [separates Korrekturprotokoll](V2_UI_0_1_70_KOMPAKTER_AUFTRAGSSTATUS_2026-10-11.md). Ursprüngliche Anforderungen:

- Die aktuell oberhalb der Karten stehenden Zeilen `Protokolle und Auftragshistorie sind aktuell.` und `Gespeicherte Auftragszustände; alte Ergebnisse sind nicht erneut freigegeben.` aus dem dauernd sichtbaren Layout **entfernen**.
- Links **direkt unter** der Überschrift `Serverseitige Auftragshistorie` statt dieser Zeilen einen **einzeiligen, zurückhaltenden Kurzstatus** anzeigen, auf gleicher Gesamthöhe wie die goldene Taste **„Aktualisieren“** rechts. Beispielsweise `Aktuell` nach bestätigtem Abruf, `Wird aktualisiert …` nur beim Laden und kurze deutliche Fehlerwarnung bei erfolglosem Abruf. Keinen falschen Aktualitätsstatus vor erfolgter Serverantwort darstellen.
- Die sicherheitsrelevante Information `Alte Ergebnisse werden nicht erneut freigegeben` nicht ersatzlos beseitigen, sondern in den bereits vorhandenen, standardmäßig geschlossenen Aufklapper **„Hinweise zu Protokollen und Datenschutz“** verschieben.
- Goldene Schaltfläche, rotierende Ladeanimation, verständliche Fehlerbehandlung, Fokusführung, Mobil-Layout, kein automatisches Ausführen einer Quellprüfung und sämtliche Sicherheitsgrenzen beibehalten.
- Änderungen in einem **eigenen späteren DEV-Versionsschritt** mit CI/HA-Abnahme prüfen; nicht mit der nächsten G2-Sicherheitsabnahme vermischen.

## Ein einziger HA-Realtest nach grünem CI

Der Betreiber installiert DRA V2 DEV **0.1.68** mit DRA V1 und startet HA bei Bedarf vollständig neu. Dann öffnet er **Deployment → Logs**, prüft die voneinander getrennten Aufträge und klappt **„Hinweise zu Protokollen und Datenschutz“** einmal auf und wieder zu. Der neue Aufbau darf weder eine Quellprüfung starten noch Schreibrechte erlauben. Screenshot nur bei Auffälligkeiten erforderlich.

**C.K. – Eine Idee weiter gedacht.**

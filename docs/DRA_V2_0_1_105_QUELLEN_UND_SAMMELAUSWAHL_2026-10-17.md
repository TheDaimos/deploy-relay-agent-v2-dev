# DRA V2 0.1.105 DEV – Quellenwahl / Sammelupdate

**Entwicklungszweig:** `feature/v2-10-inventory-operation-contract`  
**Datum:** 17.10.2026

## Befunde
- Die Projektauswahl wurde als gewöhnliches `details`-Element bei jeder serverseitigen Statusaktualisierung neu aufgebaut. Der Öffnungszustand war nicht gespeichert. Dieser Zustand bleibt nun im Panel erhalten; verzögerte Ereignisse entfernter Oberflächenelemente werden ignoriert.
- Bisher nahm die Sammelupdate-Auswahl sämtliche aktiven/vorausgewählten Projekte fest auf. Jetzt gibt es Checkboxen für die **einmalige Auswahl des aktuellen Durchlaufs**. Das gespeicherte Feld `batch_preselect` wird dadurch nicht verändert.
- Die DRA-V1- und DRA-V2-Repositories sind in diesem Sammellauf aus Sicherheitsgründen nicht installierbar und erscheinen lediglich als deaktivierte Einträge. Die bestehende serverseitige Prüfung gegen Selbstupdates bleibt erhalten.
- Die Quellenauswahl kann vom HA-Quellstatus bereits auf `main` gesetzt worden sein, bevor die projektseitige Empfehlung geladen wird. Die bisherige Bedingung `if (!this._mainSourceRef.trim())` ignorierte dann die Empfehlung. Jetzt gilt eine vorläufige Standardreferenz als ersetzbar, eine explizite Benutzerauswahl dagegen nicht.
- Der read-only-Aufruf zum Laden von Zweigen und Tags wird nicht mehr von der lange laufenden Dateibestandsprüfung blockiert. Eine eigenständige HA-Sperre für Quelllisten serialisiert bei Bedarf diese kleinen Leseabfragen.
- Die Quellfehlermeldung eines zuvor gewählten Einzelprojekts wird in der Sammelansicht nicht mehr als Sammelupdate-Fehler ausgegeben.

## Sicherheits- und Bedienvertrag
1. Die lokale Sammellaufauswahl wird vor jedem schreibgeschützten Auswahltest und vor der tatsächlichen serverseitigen Sammelvorbereitung übergeben.
2. Keine ausgewählten Projekte = keine Freigabe. Maximal acht geeignete Projekte pro Durchlauf.
3. Vorbereitete beziehungsweise laufende Sammelaufträge lassen ihre Projektauswahl nicht mehr verändern.
4. V1-Installationsengine, separate Administratorfreigabe, HA-Auftragsführung, Zielpfadschutz und Sicherheitsbestätigung bleiben unverändert.
5. Ein Git-Zweig ist keine Installationsfreigabe; erst eine vollständige, commitgebundene Quellprüfung kann einen Auftrag vorbereiten.
6. Die Wahl von `main` **durch den Benutzer** bleibt gültig. Nur automatisch vorbesetztes `main` wird durch eine explizite Projektvorgabe ersetzt.

## Abnahme
- Projektkombination inklusive Deploy Relay Agent V1 / V2, Gewitterradar und WeatherRouter: beide DRA-Projekte deaktiviert, verbleibende Auswahl aktiv steuerbar.
- Ausgewählte Projekte abwählen, neu anwählen und mehrfach neu laden: keine Veränderung der gespeicherten Standardvorauswahl.
- Liste für mehrere automatische Statuszyklen geöffnet halten.
- WeatherRouter-Einzelprojekt: empfohlene Referenz `deploy/dev`, sofern keine manuelle Referenz gesetzt wurde; manuelles `main` respektieren.
- Vorbereiteter Sammelauftrag: Auswahl gesperrt; Start weiterhin nur mit erneuter ausdrücklicher Bestätigung.
- Keine Installation anhand eines unbestätigten oder veralteten GitHub-Quellstatus.
- Desktop, Android und iPad: Wiederaufbau darf die Projektauswahl nicht selbständig zuklappen.

**GitHub CI ist kein Ersatz für die HA-Realabnahme.** Keine produktiven Installationen aus einer ungeprüften Sammelvorbereitung auslösen.

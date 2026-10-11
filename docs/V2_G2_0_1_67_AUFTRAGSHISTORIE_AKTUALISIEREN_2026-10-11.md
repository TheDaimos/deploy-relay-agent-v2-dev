# DRA V2 DEV 0.1.67 – Hochwertige Aktualisierung der Auftragshistorie

**Datum:** 11.10.2026  
**Entwicklungszweig:** `feature/v2-10-inventory-operation-contract`  
**Status:** Code umgesetzt, isolierte CI grün; **HA-Realabnahme von 0.1.67 noch offen**.  
**Abgrenzung:** ausschließlich Bedienoberfläche + bestehende schreibgeschützte WebSocket-Leseendpunkte. Keine neuen Rechte.

## Ausgangslage und realer HA-Befund

- Bei der G2-60-Verbindungsabnahme über WLAN und anschließend 5G mit VPN zeigte die Companion App weiterhin den **vor dem terminalen Abschluss geladenen** Stand der serverseitigen Auftragshistorie.
- Im direkten Chrome-Browser war der Status bereits aktualisiert. Nach dem Schließen und Wiederöffnen des DRA-V2-Protokollbereichs – beziehungsweise dem erneuten Betreten der V2-Ansicht – wurde auch in der Companion App **dieselbe Auftragskennung als „Damals erfolgreich“** sichtbar. Die echte Quellprüfung unter 0.1.66 hatte das Gewitterradar erfolgreich, schreibgeschützt und ohne Installationsfreigabe geprüft. Damit ist G2-60-B **vollständig** abgenommen: identischer Auftrag vor und nach WLAN→5G/VPN sowie terminaler historischer Erfolg.
- Der Befund zeigt eine **fehlende manuelle Aktualisierungsfunktion / veraltete Clientanzeige**, **keinen nachgewiesenen Verlust gespeicherter Aufträge**. Die serverseitige Historie bleibt unverändert gültig.

## Gestaltung und Bedienbarkeit

Im geöffneten Bereich **Deployment → Logs → Serverseitige Auftragshistorie** steht jetzt ein eigener, optisch hochwertiger und mobil bedienbarer Knopf:

**↻ Aktualisieren**

- **Optik:** zurückhaltender goldener Rahmen, dunkler metallisch abgestufter Hintergrund, goldene Beschriftung und passendes kreisförmiges Pfeilsymbol; fein dosierter Licht-/Tiefeneffekt, Hover- und Druckzustand, eigenständiger deutlicher Tastaturfokus.
- **Mobil:** 44-Pixel-Mindesthöhe, ausreichender Textkontrast, umbrechende Kopfzeile bei schmalen Bildschirmen; keine zusätzliche Schaltfläche auf der ohnehin umfangreichen Hauptseite.
- **Laden:** Der Pfeil rotiert dezent und die Aufschrift lautet „Wird aktualisiert …“. Bei aktivierter Einstellung für reduzierte Bewegung entfällt die Drehung.
- **Rückmeldung:** Ein `role="status"` mit `aria-live="polite"` zeigt „Protokolle und Auftragshistorie sind aktuell.“ bzw. bei Teilfehler „Aktualisierung unvollständig. Bitte Verbindung prüfen und erneut versuchen.“.
- **Sperre:** Mehrfaches Antippen während eines laufenden Abrufs erzeugt keinen parallelen zweiten Abruf. Das vorhandene Browser-/Android-Verhalten bleibt unangetastet.

## Technischer Vertrag

Die Schaltfläche ruft nur vorhandene administrative Leseaktionen auf:
1. `deploy_relay_v2_dev/deployment/logs`
2. `deploy_relay_v2_dev/projects/source_job/history`

Die Ergebnisse bleiben in den bestehenden getrennten, auf acht Einträge begrenzten Anzeigen. Es findet **kein** `projects/source_job/start`, keine Dateischreiboperation, kein erneuter Quellvergleich, keine Authentifizierungslockerung, keine Git-Übertragung, kein HA-Neustart und **keine Wiederfreigabe historischer Ergebnisse** statt.

Die zugrundeliegenden WebSocket-Handler wurden **nicht verändert**. Die Bedienoberfläche akzeptiert weiterhin ausschließlich die geprüften Schemas und `installation_enabled=false`. Der G2-Test-Versionsschutz wurde im Zuge des ordentlichen DEV-Versionssprungs auf **0.1.67** angepasst; der 60-Sekunden-Verbindungstest bleibt ansonsten technisch unverändert.

## Prüfungen

Automatischer GitHub-Actions-Lauf **[38162164733](https://github.com/TheDaimos/deploy-relay-agent-v2-dev/actions/runs/38162164733) – SUCCESS**, inklusive:
- Python-Vertragstests, Python- und JavaScript-Syntax
- Node-Oberflächentests für vorhandene V2-Abläufe
- Neue Tests: hochwertige Schaltfläche sichtbar, Mindestbedienbarkeit und Tastaturfokus, reduzierte Bewegung, Ladezustand, erneuter Abruf beider erlaubter Leseendpunkte, Verhinderung doppelter Klicks, Fehleranzeige ohne Schreibfreigabe
- Keine Artefakte und keine Installation aus CI heraus

**HA-Realtest nach vom Betreiber ausgeführtem V1-Update und üblichem HA-Neustart:** In DRA V2 DEV **Logs** öffnen, `Aktualisieren` antippen und prüfen, ob sich die Liste unmittelbar aktualisiert, auch nach Wechsel zwischen Companion App und Browser. Eine bereits vorhandene erledigte Kennung muss weiterhin als „Damals erfolgreich“ erscheinen. **Kein zusätzlicher G2-60-Test notwendig.**

## Unveränderte Sicherheitsgrenzen

`main`, V2 PUB, DRA V1, WeatherRouter und das private Exportarchiv wurden nicht verändert. Draft-PR #2 bleibt offen und darf nicht zusammengeführt werden. Echte Rohdiagnosen dürfen weiterhin ausschließlich nach `TheDaimos/Project-Log-And-Export`. V2-Einrichtung und Installations-/Schreibberechtigung bleiben gesperrt. HA-Neustarts löst ausschließlich der Betreiber selbst aus.

**C.K. – Eine Idee weiter gedacht.**

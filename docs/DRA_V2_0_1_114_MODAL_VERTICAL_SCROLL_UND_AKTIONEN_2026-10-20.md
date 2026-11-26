# DRA V2 0.1.114 DEV – Scrollposition und platzsparende Bestätigung

**Datum:** 20.10.2026  
**Repository:** `TheDaimos/deploy-relay-agent-v2-dev`  
**Zweig:** ausschließlich `feature/v2-10-inventory-operation-contract`

## Befund und Abgrenzung

Die horizontale Scrollposition der verbindlichen Sammelprüfübersicht bleibt nach der vorigen Korrektur auf HA erhalten; dies wurde vom Anwender real bestätigt. Beim **vertikalen Scrollen des Prüffensters** wurde die Position dagegen im ungefähr dreisekündigen Statusaktualisierungsrhythmus wieder nach oben gesetzt. Der Screenshot zeigt weiterhin untereinander platzierte Freigabeschaltflächen. Das schmale Fenster wurde unabhängig davon durch die spezifischere Breitenregel des 0.1.113-Codebestands adressiert.

## Umsetzung

`frontend/lab.js::_render()` erfasst jetzt vor jedem DOM-Neuaufbau nicht nur die bestehende horizontale Tabellenposition, sondern auch die **vertikale Position des Tabellenbereichs** und die **vertikale Position des Dialogs**. Anschließend werden alle drei Werte im neu aufgebauten, gleichnamigen Fenster wiederhergestellt. Es werden keine Freigabewerte, Projekte, Commits oder serverseitigen Aufträge geändert. Der Statusabruf bleibt aktiv.

Die drei Handlungsflächen der Prüfübersicht sind in einem responsiven Raster untergebracht. Auf breiten Darstellungen erscheinen sie nebeneinander, auf mittleren Breiten zweispaltig mit vollständiger dritter Zeile und auf sehr schmalen Bildschirmen einspaltig. Es wurden keine Bestätigungs- oder Schutzbedingungen geändert; die ausdrücklich zu bestätigende Sammelinstallation wird nicht automatisch ausgelöst.

`manifest.json`, `const.py` und die Oberflächenversionskonstante sind synchron auf **0.1.114 DEV** gesetzt. Bestehende Verhaltenstests wurden an die Version angepasst; ein zusätzlicher Vertragstest schützt vertikale Scrollwiederherstellung sowie responsive Rasterregeln.

## Entwicklungs- und Nachweisstand

- Programmänderung: `12156b5dfed5b3da02d795e39819d5b1b740fb84`
- Python-/Manifest- und Testanpassungen: Folgecommits im selben Zweig
- Letzter Testcommit: `efe46511c5a871e02632335c997ed73b44f3924b`
- CI ist vor einer Testfreigabe für **exakt diesen** Commit zu prüfen. Frühere, fehlgeschlagene Zwischenstände sind kein Nachweis der endgültigen Version.

## Ausstehende HA-Realabnahme

0.1.114 wurde durch diese Arbeit **nicht** auf Home Assistant installiert. Nach vollständig grüner CI kann der Anwender die Version kontrolliert über den DRA-V1-Weg auf HA DEV installieren. Dann die Sammelprüfübersicht mit sechs Projekten **nur vorbereiten**, Fenster vertikal herunterscrollen, mehrere Aktualisierungszyklen abwarten, waagerechte Tabellenposition und Aktionen auf Notebook/iPad prüfen. Die vollständigen Commits und WeatherRouter-`deploy/dev` müssen sichtbar und unverändert bleiben.

**Kein Sammelstart, kein Selbstupdate und kein HA-Neustart ohne ausdrückliche Freigabe und echte Realnachweise.** DRA V1, Gewitterradar und WeatherRouter bleiben unverändert.

## GitHub-CI – abschließend verifiziert

Der vollständige GitHub-Actions-Lauf **39427148194** wurde am Programm-/Testcommit **`efe46511c5a871e02632335c997ed73b44f3924b`** mit **completed / SUCCESS** verifiziert. Der spätere Dokumentationscommit betrifft ausschließlich Markdown und ändert die geprüfte Programmversion nicht. **GitHub-CI ist keine HA-Realabnahme.**

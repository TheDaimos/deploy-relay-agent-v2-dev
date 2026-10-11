# DRA V2 DEV 0.1.70 – Kompakter Aktualisierungsstatus in der Auftragshistorie

**Datum:** 11.10.2026  
**Repository:** `TheDaimos/deploy-relay-agent-v2-dev`  
**Verbindlicher Entwicklungszweig:** `feature/v2-10-inventory-operation-contract`  
**Status:** Code umgesetzt, vollständige GitHub-CI **SUCCESS** ([Lauf 38170793870](https://github.com/TheDaimos/deploy-relay-agent-v2-dev/actions/runs/38170793870), Code- und Dokumentationscheckpoint `d54d63dc9cfcc5b195d41758432896fe8440cab5`). **HA-Realabnahme noch ausstehend. Kein Update von 0.1.69 während des aktiven G2-Export-Wiederholtests erzwingen.**

## Ausgangslage und ausdrücklich gewünschte Korrektur

Der Betreiber hatte bei der HA-Abnahme von V2 DEV 0.1.68 verbindlich angefordert, die beiden platzraubenden Textzeilen `Protokolle und Auftragshistorie sind aktuell.` und `Gespeicherte Auftragszustände; alte Ergebnisse sind nicht erneut freigegeben.` direkt unter dem Kopfbereich zu entfernen. Stattdessen soll der knappe Aktualisierungsstatus **unmittelbar unter `Serverseitige Auftragshistorie` stehen, links auf der Höhe der vorhandenen goldenen Taste `Aktualisieren`**. Die Sicherheitsinformation über nicht erneut freigegebene historische Ergebnisse soll in den bestehenden Aufklappbereich wandern.

Dies war zuvor trotz Dokumentation **in 0.1.69 noch nicht umgesetzt**. Die Sichtprüfung der installierten 0.1.69 zeigte ausdrücklich weiterhin die beiden alten Zeilen. Dies ist ein übergangener, nicht abgearbeiteter Gestaltungsauftrag, kein Fehler des Anwenders.

## Umsetzung 0.1.70

- Linker Kopfbereich ist eine vertikale Textgruppe: **`Serverseitige Auftragshistorie`** mit direkt darunter liegendem **Kurzstatus**.
- Die vorhandene edle **goldene Aktualisieren-Taste** bleibt daneben rechts; auf kleinen Bildschirmen erhält die Überschrift einen flexiblen Bereich, statt den Status als neue Zeile über die gesamte Fensterbreite zu schieben.
- Statuswerte werden **ehrlich aus echten Serverantworten** gesetzt: `Nicht geprüft` vor dem ersten Abruf, `Wird geladen …` oder `Wird aktualisiert …` während der Leseabfragen, **`Aktualisiert`** ausschließlich bei erfolgreichem Abruf **beider** bestehenden Quellen, `Abruf fehlgeschlagen` bei ungültiger Antwort oder Verbindungsfehler.
- Der sichtbare Langsatz zur Aktualität entfällt; er wird weder doppelt noch permanent unter der Überschrift dargestellt. Ebenso entfällt der permanent sichtbare Datenschutz-/Freigabetext.
- Im vorhandenen anfangs geschlossenen Aufklappbereich `Hinweise zu Protokollen und Datenschutz` steht ausdrücklich: **Alte Prüfergebnisse werden niemals erneut freigegeben.** Der Hinweis wird nicht fachlich entfernt.
- Ein leeres historisches Ergebnis zeigt eine entsprechende Leerinformation innerhalb der eigentlichen Liste, keine neue langgezogene Kopfzeile.
- Für den barrierefreien Statuswechsel nutzt der Kurzstatus `role="status"`, `aria-live="polite"`, `aria-atomic="true"` sowie eine vollständige, verständliche Langbeschreibung für Hilfstechnologien. Gestalterisch wird bei Erfolg zurückhaltendes Grün, bei Ladung Gold und bei Fehlschlag dezentes Rot verwendet. Das Gold-Design und die Ladeanimation des eigentlichen Knopfes bleiben unverändert.

## Abgrenzung / Sicherheitsvertrag

**Ausschließlich** Frontend, UI-Tests, DEV-Versionskonstante, Manifest und bereinigte Dokumentation werden angepasst. Keine Änderung an den serverseitigen G2-Export-Verträgen oder den in 0.1.69 vorbereiteten DEV-Tests zum lokalen Zurückstellen und anschließenden bewussten `retry_pending()`.

Der noch laufende G2-Realtest unter der bereits in HA installierten **0.1.69** soll **zuerst** abgeschlossen werden. Für diese optische Nachbesserung wird kein erneuter HA-Neustart während des aktuellen Tests verlangt. Nach positiver isolierter CI kann **0.1.70 separat** durch den Betreiber über DRA V1 installiert und in HA angesehen werden.

DRA V1, V2 `main`/PUB, WeatherRouter, das private Zentralarchiv `TheDaimos/Project-Log-And-Export` und PR #2 bleiben unverändert; PR #2 nicht zusammenführen.

## Abnahme

- Isolierte JS-Prüfung bestätigt Positionierung der kurzen Statusmeldung in derselben Kopfzeile wie die Taste, Vorhandensein der zunächst neutralen, der lade-, erfolgs- und fehlerbezogenen Zustände sowie Fehlen beider alten Textzeilen in der sichtbaren Kopfansicht.
- Die bestehenden Leseendpunkte werden unverändert genutzt. **Keine** neue Quellprüfung und **keine** automatische Schreib-/Installationsfreigabe.
- Die HTML-Detailhinweise bleiben einklappbar und der Offen-Zustand bleibt wie bisher erhalten.
- **Isolierte CI erfolgreich:** Python-Vertragstests, Python-/JavaScript-Syntax, Node-UI- und G2-Retry-Sicherheitsprüfungen; keine Veröffentlichung von Artefakten. Run 38170793870, SUCCESS. Folgende reine Dokumentationsergänzungen ändern den getesteten Anwendungscode nicht.
- HA-Realabnahme: Bei der späteren separaten Aktualisierung sollte links direkt unter der Überschrift der Status `Aktualisiert` stehen und rechts die goldene Taste; darunter beginnen ohne zwei lange Hinweiszeilen sofort die Auftragskarten.

**C.K. – Eine Idee weiter gedacht.**

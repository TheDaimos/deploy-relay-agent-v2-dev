# DRA V2 0.1.118 DEV – farblich unterscheidbare Änderungen in der mobilen Kurzansicht

**Datum:** 20.10.2026  
**Repository:** `TheDaimos/deploy-relay-agent-v2-dev` (privat)  
**Entwicklungszweig:** ausschließlich `feature/v2-10-inventory-operation-contract`  
**Letzter vorgelegter HA-Realstand:** 0.1.116 DEV; für 0.1.118 liegt noch **keine HA-Realabnahme** vor.

## Verbindlicher Auftrag

Die mobile, aufklappbare Sammelprüfübersicht muss Projekte **mit** und **ohne** Änderungen bereits in der geschlossenen Kurzansicht unterscheiden. Neben dem Versionsvergleich werden sämtliche tatsächlich von HA geprüften Änderungsarten angezeigt, jedoch ausschließlich mit einem Wert größer null. Einheitliche Reihenfolge: **hinzugefügt (+), geändert (~), entfernt (−)**. Insbesondere **Rot (entfernt)** und **Gold (geändert)** müssen unmissverständlich verschieden sein.

Beispiele einer Kurzansicht (illustrativ, keine echten Installationsdaten):

- Gewitterradar: `4.11.59 → 4.11.67` – `+33` (grün), `−12` (rot)
- WeatherRouter: `0.10.14 → 0.10.25` – `+33` (grün), `~4` (gold), `−12` (rot)
- Ohne Änderungen: unveränderte, neutral umrandete Karte mit `Aktuell` bei nachgewiesenem `up_to_date`.

## Umsetzung und Grenzen

In `frontend/lab.js` ermittelt der Kartenaufbau aus den **serverseitig gelieferten Dateizahlen** `add`, `change` und `remove` sichere nichtnegative Anzeigewerte und baut die zusätzliche kurze Änderungszeile neben dem Versionsvergleich auf. **Versionsnummern sind keine Änderungsdetektoren**: Auch ein identisches Versionspaar kann Änderungen enthalten. Die bereits vorhandene Anzeige des gekürzten 12-stelligen Commits bleibt erhalten; der aufklappbare Detailbereich enthält unverändert den 40-stelligen Originalcommit, Git-Ref, Repository, Status und vollständige Dateiänderungszahlen.

**Farb- und Erkennungsregeln:**

- Hinzugefügt: Grün `#77e7ae`, Zeichen `+`.
- Geändert: helles Gold `#ffe082`, Zeichen `~`, goldener Hintergrund.
- Entfernt: kräftiges Rotrosa `#ff667f`, Zeichen `−`, rötlicher Hintergrund.
- Sämtliche Angaben erhalten einen eigenen farbigen Rand und ein vorangestelltes Symbol, damit die Unterscheidung nicht allein von der Farbwahrnehmung abhängt.
- Bei tatsächlichen Dateiänderungen besitzt die Kurzkarte eine deutlich abgesetzte linke Kante. Karten ohne Änderungen bleiben neutral; bei `up_to_date` wird `Aktuell` angezeigt. Wenn kein Dateiunterschied erkannt wird, der HA-Status aber nicht `up_to_date` ist, wird lediglich `Keine Dateiänderungen` angezeigt, keine Installation als abgeschlossen behauptet.
- Werte `+0`, `~0` und `−0` werden **in der Kurzansicht** unterdrückt. Der ausgeklappte vollständige Prüfbereich bleibt bestehen.
- Medienregel für mobile Karten bis 900 CSS-Pixel, die Desktop-Tabelle bleibt unverändert.

Die Änderungen sind **rein darstellerisch**. Weder der vom HA-Server geprüfte 40-stellige Commit noch `review_digest`, Controller-/Gerätewechsel, Bestätigungs-Checkbox, Installationsstart oder andere Schutzmechanismen werden verändert.

**Version:** `0.1.118 DEV` synchron in `frontend/lab.js`, `const.py`, `manifest.json` und Testvorgaben.

## Prüfungen

Ergänzt wurden echte JavaScript-Darstellungsfälle für gemischte Änderungen (`+33 / −12`, `+33 / ~4 / −12`), einzelne Arten sowie unveränderte Dateien. Die Vertragsprüfungen sichern zusätzlich die getrennten Rot- und Goldfarbwerte, die Kurzansicht und die unveränderte Installationsfreigabebindung ab.

**Letzter Programm-/Testcommit:** `93a21e6833e2c431465498adbf05acffb96af5f0`.  
**GitHub Actions:** Lauf `39439797010`, `completed / SUCCESS`; Job „Statische und sicherheitsbezogene Basispruefung“: **SUCCESS**. Frühere abgebrochene oder fehlgeschlagene Zwischenstände sind kein Freigabenachweis.

## Verbleibende Home-Assistant-Prüfung

Keine Installation oder Neustart ausgeführt. **0.1.118 ist ein CI-geprüfter Kandidat, nicht eine realabgenommene Version.** Erst nach gesonderter Zustimmung über DRA V1 auf HA DEV installieren. Danach ausschließlich eine vorbereitete Sammelprüfübersicht am Smartphone prüfen: Kurzansichten gemischter Änderungsarten, neutraler Status ohne Änderungen, Rot/Gold-Unterschied, 12-stelliger Kurzcommit, vollständiger Commit beim Öffnen, Scroll-/Aufklappzustand und geräteübergreifende Übernahme. Die Sammelinstallation bleibt ohne separate Freigabe gesperrt.

Keine Änderungen an DRA V1, Gewitterradar oder WeatherRouter.

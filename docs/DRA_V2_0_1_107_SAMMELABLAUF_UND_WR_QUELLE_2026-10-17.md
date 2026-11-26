# DRA V2 0.1.107 DEV – Sammelablauf und WeatherRouter-Quellenwahl
Stand: 17.10.2026. Entwickelt ausschließlich auf `feature/v2-10-inventory-operation-contract`.

## Reproduzierter Bedienfehler
Bisher rief die große geführte Schaltfläche im Sammelupdate nur `batch/preview` auf. Dieser Leseaufruf gibt ausdrücklich `sources_verified:false` und `installation_enabled:false` zurück und kann die Installationsvorbereitung **nicht** freigeben. Der serverseitige Aufruf `batch/prepare` war ausschließlich über eine zusätzliche, unauffällige Schaltfläche erreichbar. Deshalb blieb der geführte Ablauf auf Stufe 1 stehen.

### Korrektur
Die große Hauptschaltfläche steuert jetzt den vollständigen Sammelablauf:
1. **1/4**: `batch/prepare` auf Home Assistant mit ausgewählten Projekten; dabei feste Quellstände, echte lokale Änderungslisten und Zielpfade prüfen.
2. **2/4**: Nur wenn die HA-Antwort eine gültige, unverbrauchte Vorbereitung bestätigt, durch ausdrückliche Sicherheitsabfrage den Auftrag bestätigen. Ein anderes Gerät muss die Bedienung zuerst übernehmen.
3. **3/4**: Nur ein HA-seitig angenommener Auftrag zählt. Browser und Geräte beobachten den Auftrag, ohne Schreibanforderungen zu wiederholen.
4. **4/4**: Nur der nachgewiesene erfolgreiche serverseitige Batch-Abschluss ergibt den grünen Endzustand. Fehler und Abbrüche bleiben sichtbar.

Die separate untere Vorbereitungsaktion wurde als konkurrierender Bedienweg entfernt. Eine abweichende Browser-/HA-Version blockiert die Vorbereitung.

## Fehler- und Verlaufsdiagnose
- `batch/status` bleibt nun auch während einer langsamen, noch nicht abgeschlossenen Vorbereitung lesbar; keine Sperre des Beobachters durch die serverseitige Vorbereitungs-Sperre.
- Server liefert `preparing` mit bearbeitetem Projekt und Anzahl geprüfter Quellstände, oder `failed` mit bereinigter Fehlerkategorie statt einem endlosen Zustand.
- Nach Fehlern existiert keine gültige Installationsbestätigung. Es wurde dadurch keine Installation begonnen.
- Doppeltes Starten nach unklarer WebSocket-Antwort bleibt untersagt; zuerst den HA-Status und das Audit prüfen.
- Vertrauliche Tokens, Rohdateipfade und unbereinigte GitHub-Antworten werden nicht als Fehlermeldung ausgegeben.

## Reproduzierter WeatherRouter-Fehler
Das öffentliche Projekt `TheDaimos/weather-router-dev` besitzt auf `main` die gültige `deploy-relay-channel.json` mit der Empfehlung `deploy/dev`. DRA V2 konnte trotzdem eine ältere, serverseitig vorbereitete Installation mit `source_ref:main` wiederherstellen. Dieser bereits vorbereitete Zustand blockierte das automatische Anwenden des empfohlenen Zweigs, und weitere HA-Statusabfragen überschrieben die Oberfläche erneut mit `main`.

### Korrektur
- Wenn `main` lediglich die automatische Standardreferenz war, darf sie durch die nachgewiesene, ausdrücklich veröffentlichte Projektempfehlung `deploy/dev` ersetzt werden.
- Eine alte serverseitige Vorbereitung auf `main` wird dann **nicht** als Installationsfreigabe für `deploy/dev` dargestellt. Sie bleibt bis zum Ablauf auf HA und muss nicht mit einem Schreibvorgang aufgehoben werden.
- Eine **ausdrückliche** manuelle Benutzerentscheidung für `main` bleibt möglich und wird nicht überschrieben.
- Eine aktive Installation wird niemals stillschweigend auf eine andere Git-Referenz umgestellt.
- Nach Quellenwechsel sind alte Vorschau und alter Bestätigungszustand ungültig; Quellprüfung erneut durchführen.

## Abnahme (HA noch offen)
1. Nach DRA-V1-Installation Version 0.1.107 von Browser und HA-Laufzeit bestätigen.
2. WeatherRouter einzeln auswählen; Standard **deploy/dev** und Commit nachweisen. Keine noch gültige alte `main`-Vorbereitung als neue Freigabe akzeptieren.
3. Sammelupdate mit **isoliertem Testprojekt** starten; große Haupttaste löst tatsächlich `batch/prepare` aus und bringt nach erfolgreicher Prüfung den Ablauf zu **2/4**. Kein verdeckter zweiter Button erforderlich.
4. Fehlerfall mit ungültiger Quelle ausschließlich in einer isolierten Umgebung: Anzeige von `failed` plus sicherer Fehlerkategorie, **kein** Installationsstart.
5. Android übernimmt eine bereits vorbereitete Bedienung nur nach ausdrücklicher Bestätigung. Desktop/iPad verfolgen denselben HA-Auftrag.
6. Mindestens ein erfolgreicher Abschluss mit echtem V1-Journal und Verifikation; erst danach reale Sammelupdates erwägen.

**CI-Erfolg allein bestätigt keine HA-Realabnahme.** DRA V1 bleibt die bewährte Update- und Rückfallmöglichkeit. Alle Arbeiten betreffen nur dieses DRA-V2-Repository und den bestehenden Entwicklungszweig.

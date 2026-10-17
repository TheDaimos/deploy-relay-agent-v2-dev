# DRA V2 DEV 0.1.61 – vollständiges, begrenztes Lesen von GitHub-JSON-Antworten

**Datum:** 11.10.2026  
**Einziger Arbeitszweig:** `feature/v2-10-inventory-operation-contract`  
**Abnahmestand:** GitHub-CI nach Codeänderung SUCCESS; vollständige HA-/Android-Realabnahme von 0.1.61 ausstehend. Installation aus DRA V2 weiterhin gesperrt.

## Echte Beobachtung / belegte Ursache im Leseclient

Der ausdrücklich privat gespeicherte Export vom **11.10.2026, 10:00:27 UTC**, Testanwendung **DRA V2 DEV 0.1.60**, enthält für `TheDaimos/gewitterradar`:

- **Projektkennung** `P-7859B882AD37` (nur laufzeitstabil) / **Prüfkennung** `15bd44e0d049403baf39c987232b21b3`.
- `stage=tree`, `reason=tree_json_invalid`, `status=failed`, `sources_verified=false`, `installation_enabled=false`.
- Quellenphasen: Repository, Commit und Manifest vor dem Git-Dateibaum erreicht; Gesamtdauer **1.190 ms**; **23 ms HA-weiter Prozess-CPU-Wert**; **12** verfügbare Kerne; zwei Leseaufträge konfiguriert, tatsächlich **eins**, null Schreibaufträge.
- Diese realen Diagnosedaten **nicht** ins öffentliche Entwicklungsrepository übernehmen; Dokumentation der nötigen minimalen technischen Eckpunkte ist zulässig.

Der bis 0.1.60 implementierte GitHub-Leseclient hat bei HTTP 200 nur **einmal** `await response.content.read(MAX_RESPONSE+1)` ausgeführt und das Ergebnis anschließend direkt als UTF-8-JSON interpretiert. Bei `aiohttp.StreamReader.read(n)` bedeutet das aber **höchstens n Bytes**, nicht „lies exakt n Bytes bis zum Ende der HTTP-Antwort“: Der Aufruf darf bereits dann zurückkehren, wenn nur ein erster Datenblock vorhanden ist. Die Dokumentation bestätigt, dass `read(n)` weniger als `n` Bytes zurückgeben darf: https://docs.aiohttp.org/en/v3.14.0/streams.html . Ein dadurch abgeschnittenes JSON erklärt den Code `tree_json_invalid` sehr plausibel. Die konkreten HA-Netzwerkbytes sind unbekannt; die reproduzierte **programmierte Ursache** ist dagegen eindeutig nachweisbar.

## Präzise Korrektur

`custom_components/deploy_relay_v2_dev/remote_source.py` sammelt den HTTP-Antwortkörper jetzt in einer Schleife aus **maximal 64 KiB großen Leseportionen**, bis `read(...)` tatsächlich **b"" (EOF)** liefert. Für den gesamten dekodierten Antwortkörper gilt unverändert die harte Grenze **MAX_RESPONSE = 4 MiB**. Erreicht die bisherige Summe die Grenze, wird höchstens noch **ein** Byte gelesen, um eine zu große Antwort zuverlässig mit `GitHub response exceeds size limit` abzuweisen; es wird nie ein großer ungebundener `read(-1)`-Aufruf benutzt.

Weitere Schutzvorgaben bleiben erhalten:

- Festes API-Ziel ausschließlich `https://api.github.com`, kein Redirect, nur `GET`, keine V2-Schreibaktion.
- 12 Sekunden zeitliche Grenze je GET und gesamtes 45-Sekunden-Fenster der Quellprüfung, nur **eine** Wiederholung bei transientem Transportfehler.
- HTTP-Nicht-200-Antworten, zu große Bodies, ungültiges JSON, unvollständige Git-Bäume, Dateien/Pfade außerhalb des sicheren Manifests und nicht vollendete lokale HA-Bestandsaufnahme bleiben **fail-closed**.
- Geheimnisse, roher Antwortkörper und lokale HA-Pfade bleiben außerhalb der Diagnoseexports. Repozuordnung nur im privaten zentralen Archiv; projekt-/prüfbezogene Kennungen genügen für UI und lokale JSON-Ausgabe.
- Keine automatische Installation, Restore- oder Sicherungsfreigabe, paralleler Update-Schreibauftrag oder Neustart; DRA V1, V2 PUB, V2-main, WeatherRouter und das private Exportarchiv unverändert. PR #2 bleibt ein nicht zusammenzuführender Entwurf.

## Negativ- und Positivtests

`tests/test_v2_source_remote.py` wurde für das echte StreamReader-Verhalten nachgerüstet: `Content.read(n)` **verbraucht** nun die gelesenen Bytes, statt denselben Anfang immer neu zurückzugeben.

- **Positiv:** 60 erlaubte, simulierte Git-Dateien, deren JSON-Antwort absichtlich in Stücke von maximal **97 Byte** geteilt wird. Die Vorschau wird nur nach vollständiger EOF-Lektüre als überprüft gekennzeichnet, zeigt alle 60 geplanten Dateien und bleibt ausdrücklich **ohne Installation**. Die HTTP-Anfrage wird dabei nicht unnötig wiederholt.
- **Negativ:** Irreführend fehlender `Content-Length`-Header, Antwortkörper über dem Limit: sofort sichere Größenfehlermeldung, selbst bei tatsächlich zerstückelten Daten.
- Bestehende Negativtests für HTTP-403, fehlerhafte JSON-Antworten, Transportabbrüche, Integritätsprüfungen, Ziel-/Besitzsperren sowie Admin-Isolation bleiben unverändert gültig.

## Nächster HA-Realtest

Nach erfolgreicher CI für den endgültigen 0.1.61-HEAD aktualisiert der Projektinhaber DRA V2 DEV **eigenständig über DRA V1**, ohne automatischen Neustart durch den Assistenten. Danach ausschließlich die **Gewitterradar-Quellvorschau** über `1/4 · Vorschau berechnen` erneut ausführen. Bei Erfolg Screenshot der **bestätigten Quelle, Commit und Änderungsvorschau**; bei Fehlschlag den neuesten Bericht über **Logs → Export nach Git** ins private `TheDaimos/Project-Log-And-Export` senden. Der technische Datentransfer ist damit statisch geprüft, aber eine erfolgreiche HA-Ende-zu-Ende-Vorschau wird erst nach dem Realtest behauptet.

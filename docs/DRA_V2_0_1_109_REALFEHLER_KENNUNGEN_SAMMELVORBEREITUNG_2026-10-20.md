# DRA V2 – nachgewiesener Sammelvorbereitungsfehler und gezielte Korrektur

**Datum:** 20.10.2026  
**Repository:** TheDaimos/deploy-relay-agent-v2-dev  
**Zweig:** feature/v2-10-inventory-operation-contract  
**HA-Ausgangslage:** DRA V2 0.1.109 DEV, Python und Oberfläche übereinstimmend, Sammelvorbereitung mit sechs Projekten abgebrochen. **Kein Installationsstart.**

## 1. Tatsächlicher HA-Befund

Der neue, ohne Logexport lesbare HA-Status zeigt:

- **Projekt:** Deploy Relay (DRA V1)
- **Phase:** GitHub-Referenz / Lesezugriff / Kanalempfehlung
- **Fehlerkategorie:** `source_invalid`
- **Zusatz:** „Projekt-Empfehlungsdatei fachlich ungültig“
- **0 von 0 Teilaufträgen abgeschlossen**; kein Installationsstart.

Der Fehler liegt **beim ersten geprüften Projekt**. Aus dem Abbruch darf kein Fehler der übrigen fünf Projekte abgeleitet werden.

## 2. Ursache reproduzierbar aus Repository-Inhalten

`project_catalog.proposal()` leitete die Projektkennung bisher unabhängig von der verbindlichen `deploy-relay.json` aus dem GitHub-Repositorynamen ab. Dadurch erhielt DRA V1 den generierten Wert `deploy_relay_agent_dev`; das offizielle Manifest und die gültige Kanalempfehlung von `TheDaimos/deploy-relay-agent-dev` verwenden aber `deploy_relay`. `inspect_source_choices(expected_project_id=...)` verglich diese unterschiedlichen Kennungen und meldete fälschlich `invalid deployment recommendation`.

Das Problem betrifft nach lesender Prüfung der offiziellen Manifeste und Kanalempfehlungen auch:

| Repository | Bisher automatisch erzeugte Kennung | Verbindliche Manifestkennung |
|---|---|---|
| TheDaimos/deploy-relay-agent-dev | `deploy_relay_agent_dev` | `deploy_relay` |
| TheDaimos/weather-router-dev | `weather_router_dev` | `weather_router` |
| TheDaimos/weather-router-extensions-dev | `weather_router_extensions_dev` | `weather_router_private_extensions` |

Gewitterradar, Test-Repo und DRA V2 stimmen bezüglich der geprüften IDs überein. WeatherRouter empfiehlt laut aktueller Kanaldatei `deploy/dev`; DRA V2 empfiehlt seinen Featurezweig. Die fixierte Empfehlung bleibt weiterhin auf Projektkennung, Ref, Manifest und Commit zu prüfen.

## 3. Umgesetzte Korrektur

**Codecommit:** `6e33221d8568d638a54f1366e79a86d49afb69e4`  
**Testcommit:** `2206b87b91a93968a08d9d52afe3abb0d9877224`

Die drei konkret verifizierten Repo-Manifest-Zuordnungen sind im V2-Projektkatalog als begrenzte bekannte Identitäten hinterlegt. Die bestehende Ladefunktion stellt nur dann eine ältere automatisch abgeleitete Kennung um, wenn **sowohl das exakte Repository als auch die alte generierte Kennung** zusammenpassen. Beliebige andere oder benutzerdefinierte Kennungen bleiben unverändert. Kollisionen werden wie zuvor abgewiesen. Der Projektkatalog wird beim bloßen Laden nicht zurückgeschrieben; bei der nächsten vorgesehenen Speichermutation gelten die aktualisierten Kennungen.

Die bestehende strenge Prüfung der GitHub-Kanalempfehlung gegen die erwartete Projektkennung bleibt **aktiv**. Ebenso unverändert bleiben V1-Engine, Prüfsummenbindung, explizite Installationsfreigabe, Journal, Rückfallschutz und HA-Neustartsperre. Keine Änderung an DRA V1, WeatherRouter, Gewitterradar oder den Erweiterungs-Repositories.

Die Regressionstests prüfen neue korrekte Kennungen, Altbestände, das Nichtschreiben beim Laden sowie den sicheren Abbruch bei doppelten Zielidentitäten.

## 4. CI und Realtestgrenze

Die erste reine Codeänderung wurde durch GitHub Actions **39401840824 – SUCCESS** überprüft. Die Prüfung des nachgelagerten Testcommits ist separat erforderlich: **39401938210**; abschließenden Zustand anhand der Actions kontrollieren, nicht vorwegnehmen.

**Eine tatsächliche HA-Installation oder erfolgreiche Sammelvorbereitung nach dieser Korrektur ist nicht nachgewiesen.** Es ist deshalb noch keine Freigabe zur Sammelinstallation, zu Selbstupdates oder zum HA-Neustart erteilt.

## 5. Verbindliche nächste Schritte

1. Prüflauf zum aktuellen Code-/Teststand auf GitHub vollständig erfolgreich verifizieren. Anschließend nur bei grünem Ergebnis einen gebündelten neuen DRA-V2-DEV-Testkandidaten mit nachweislich synchronisierten Oberflächen-/Python-Versionen bereitstellen. Keine automatische HA-Installation.
2. In HA DEV die Installation kontrolliert über DRA V1 und durch den Anwender ausführen lassen. Oberfläche und Python-Laufzeit danach abgleichen.
3. Dieselben sechs Projekte **nur vorbereiten**, **nicht installieren**. Es muss eine echte Projekt-/Ref-/Commit-/Versionsprüfung sichtbar werden, oder es muss bei einem anderen konkreten Projekt eine sichere Fehlerdiagnose erscheinen.
4. Für WeatherRouter zwingend `deploy/dev` und den tatsächlich festgehaltenen Commit prüfen; niemals ungeprüft `main` annehmen.
5. Vor einer späteren Installationsfreigabe Einzel-/Sammel-Positiv- und Negativtests, doppelte Startquittung, Gerätewechsel, Teilabbruch, Selbstupdate-Endreihenfolge, V1-Rückfall sowie gemeinsamen Neustart auf HA nachweisen.

## 6. Bedienoberfläche – gemeldeter eigenständiger Mangel

Der Anwender weist wiederholt darauf hin, dass die vertikal aneinandergereihten Bereiche auf Notebook und iPad eine unnötig lange Oberfläche erzeugen und die sichere Diagnose außerhalb des sichtbaren Bereichs liegt. Ein eigener nächster UI-Auftrag soll auf breiten Ansichten eine **zweispaltige, responsive Aufteilung** der Projektauswahl/Quellinformationen und des Deployment-/Diagnosebereichs schaffen, auf schmalen Ansichten kontrolliert einspaltig bleiben und **Fehlerursache, Projekt, Phase und erste Aktion ohne langes Scrollen sichtbar halten**. Die aktuelle Änderung behebt zuerst den bestätigten technischen Quellblocker; keine Behauptung, das neue Layout sei bereits umgesetzt.

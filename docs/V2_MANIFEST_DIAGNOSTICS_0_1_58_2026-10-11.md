# DRA V2 DEV 0.1.58 – Manifest-Fehlerdiagnose

**Datum:** 11.10.2026  
**Zweig:** `feature/v2-10-inventory-operation-contract`  
**Status:** Diagnoseerweiterung implementiert; CI und Home-Assistant-Realabnahme getrennt kontrollieren. Kein Schreibzugriff.

## Evidenz aus echter HA-Realabnahme

Im ausschließlich privaten `TheDaimos/Project-Log-And-Export` wurde ein echter bereinigter Diagnoseexport von **0.1.57** gefunden und geprüft. Zeitstempel 2026-10-11T07:02:36Z, Stufe `manifest`, Kategorie `manifest_invalid`, 57 ms Laufzeit, 2 ms CPU-Zeit des **gesamten** Home-Assistant-Prozesses. Konfiguration: 12 Kerne verfügbar, maximal 4 Arbeitsprozesse und 2 Leseaufträge eingestellt, tatsächlich nur ein Leseauftrag erlaubt und keine Schreibaufträge.

Die vorangehende **0.1.56**-Messung hatte noch `tree_invalid` ergeben. Es darf **weder** aus dem Stufenwechsel auf eine Quelländerung **noch** aus `manifest_invalid` auf ein beschädigtes Manifest geschlossen werden: Die Kategorie 0.1.57 fasste GitHub-HTTP-Antworten, Antwortvalidierung, Dateiprüfsumme und Manifestregeln zusammen.

Die GitHub-Bestandsaufnahme ergab eine gültige `deploy-relay.json` im Standardzweig des öffentlichen `TheDaimos/gewitterradar`. Dagegen war im Standardzweig des älteren privaten `TheDaimos/gewitterradar-dev` kein `deploy-relay.json` abrufbar. **Das beweist nicht, dass im HA-Test dieses private Repository ausgewählt war.** Der bereinigte Diagnoseexport enthält bewusst keine Repository- oder Referenznamen, und die verwendete Quelle konnte somit nicht eindeutig zugeordnet werden.

## Änderungen 0.1.58

Die streng administrative und ausschließlich schreibgeschützte Quellvorschau unterscheidet nun serverseitig **ausschließlich fest definierte, unveränderliche Kategorien** innerhalb der Stufe `manifest`:

- HTTP 401 / 403 / 404 / 429 und andere HTTP-Fehler getrennt (403 kann Berechtigung oder GitHub-Begrenzung sein);
- Transportfehler, übergroße Antwort, unlesbares GitHub-JSON;
- leere/übergroße Manifestdatei, fehlerhafte Base64-/Dateikodierung;
- Abweichung zwischen Manifestinhalt und Git-Blob-Prüfsumme;
- unbekanntes Schema, unzulässige Projekt- oder Repositoryidentität, nicht unterstützter Quellmodus;
- unzulässige Sicherheitsrichtlinie, deklarierte Ressourcengrenzen, Deployment-Gruppen, geschützter Zielordner.

Unbekannte Ausnahmen bleiben konsequent `manifest_invalid`. Der Diagnoseexport enthält auch künftig **keine** Rohfehlermeldungen, sensiblen HTTP-Antworten, Token, lokale Dateipfade, Repositorynamen oder referenzierbaren GitHub-Schreibaktionen.

Die Prüfroutine selbst wird **nicht** liberalisiert: SHA-genaue Quelle, nur verwaltete Pfade, V2-Budget 1.000 Dateien / 32 MiB, Quell-/Zielschutz, vollständige Prüfung und eigenständige HA-Bestandsaufnahme bleiben unverändert. Die zentrale Deployment-Schaltfläche hat weiterhin nur die Lesevorschau. **Installation, Sicherung, Wiederherstellung, parallele Sammelaktualisierung und Neustartsteuerung bleiben gesperrt.**

## Tests

- `test_v2_source_diagnostics.py`: positive Zuordnung der bekannten Manifestfehler und Negativtest für unbekannte Fehlertexte und Zeitüberschreitungen, ausschließlich feste Positivliste.
- `test_v2_source_remote.py`: simulierte HTTP-Antworten 401/403/404/429/500 während Manifest-Abruf, absichtlich ungültige Git-Prüfsumme, falsches Schema und Repositoryidentität; kein Leck von HTTP-Antwortdaten.

Keine Daten aus dem echten privaten HA-Export in dieses öffentliche Quellcode-Repository übernommen.

## Nächster kontrollierter HA-Test

1. Betreiber installiert 0.1.58 selbst über den bewährten DRA-V1-DEV-Aktualisierungsablauf; **kein** eigenständiges Deployment/Neustart durch den Assistenten.
2. Im DRA-V2-Hauptmenü die **tatsächlich ausgewählte Projektquelle prüfen** (Gewitterradar und zugehöriges Repository/Ref, z. B. Screenshot von Projekt + Quelle & Version). **Keine unbelegte Annahme, welcher Zweig aktuell ausgewählt ist.**
3. Einmal `1/4 · Vorschau berechnen` starten, anschließend `Logs` öffnen und bereinigten Export ausschließlich in `TheDaimos/Project-Log-And-Export` hochladen.
4. Die neu erfasste Manifest-Kategorie auswerten. Nur wenn sie einen konkreten und reproduzierten Mangel belegt, einen zielgerichteten Fix vornehmen. Keine pauschale Erhöhung von Grenzen, keine Schreibfreigabe.

**DRA V1 DEV/PUB, V2 PUB/main, WeatherRouter, privates Archiv und Draft-PR #2 bleiben unverändert.**

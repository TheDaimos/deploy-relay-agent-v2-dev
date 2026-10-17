# DRA V2 DEV 0.1.54 – schreibgeschützter Zielbesitz- und Kollisionsvertrag

**Datum:** 11.10.2026  
**Arbeitszweig:** `feature/v2-10-inventory-operation-contract`  
**Status:** Implementiert für Quellvorschau und isolierte Mehrprojekt-Prüfung; automatisierte CI-Prüfung und HA-Realabnahme getrennt nachweisen. **Keine Installationsfreigabe.**

## Ausgangslage und abgegrenztes Ergebnis

V2 DEV 0.1.53 prüft GitHub-Quellen SHA-genau und liest begrenzte HA-Dateibestände. Das allein beweist weder exklusives Eigentum am Zielverzeichnis noch, dass V1 dasselbe Ziel nicht weiterhin verwaltet. Die bisherige reine Sammelidentitätsvorschau enthält keine vollständigen Zielverzeichnisse; sie kann deshalb keine Installationsplanung und keinen konfliktfreien parallelen Schreibauftrag belegen.

Paket 0.1.54 führt einen **rein berechnenden, seiteneffektfreien** Vertrag in `target_ownership.py` ein:

- Nimmt **ausschließlich intern erzeugte** vollständige Einzel-Quellvorschauobjekte mit exakten 40-stelligen Quell-Commits und explizit gesperrten Installationsflags an. Die bloße Übergabe eines Browserobjekts ist verboten und würde keine Quelle authentifizieren.
- Prüft Identitäten, Gruppen, erlaubte verwaltete `custom_components/<projekt>`-Zielwurzeln und Dubletten.
- Erkennt mehrfach verwendete Zielverzeichnisse **zwischen verschiedenen Projekten**. Schreibvarianten, die sich nur in Groß-/Kleinschreibung unterscheiden, gelten vorsorglich als dieselbe Zielwurzel.
- Kann zusätzlich von einem **künftigen separaten, serverseitig geprüften** V1-/Fremdbesitzinventar belegte Zielwurzeln als Konflikt aufnehmen. Der aktuelle Code liefert noch **kein solches verifiziertes externes Inventar**; eine leere Liste bedeutet deshalb ausdrücklich *nicht* „frei“.
- Gibt nur begrenzte Ergebnisse und Schutzflags zurück; niemals Token, Dateiinhalte, HA-Rohdaten oder fremde Diagnoseexporte.
- Hängt die rein informative Einzelprojekt-Prüfung an die bestehende admin-pflichtige Route `deploy_relay_v2_dev/projects/source_preview` als Feld `target_claims`. Sie erzeugt weder einen Schreibauftrag noch eine neue Route mit Schreibrechten.
- Härtet die bereits bestehende Manifestprüfung gegen nur in Groß-/Kleinschreibung unterschiedliche Zielwurzeln innerhalb **eines** Deployments ab.

## Entscheidung und harte Schutzgrenzen

**Immer, auch bei null gefundenen Kollisionen:**

```text
exclusive_ownership_verified = false
cross_process_lock_verified = false
backup_verified = false
handover_required = true
installation_enabled = false
parallel_installation_enabled = false
```

`conflict_count = 0` bedeutet nur **„unter den zur Prüfung bereitgestellten Angaben keine Zielkollision erkannt“**, nicht „freigegeben“. Die vollständige Laufzeitprüfung fehlt insbesondere für konkurrierende DRA-V1-Schreibaufträge, externe Veränderungen, einen atomaren Schutz gegen gleichzeitige Mutation, aufgelöste Symlinks/Hardlinks, Dateisystemzugriffsrechte, Speicherplatz und Verzeichnisbesitz. Ein bereits von V1 installiertes Ziel geht nicht allein durch einen V2-Metadatenimport oder eine erfolgreiche Vorschau in V2-Besitz über.

**Das Sammelupdate bleibt:** Gemeinsame Identitätsvorschau mit `sources_verified=false`, **ohne** verkettete installierbare Quellvorschauen. Der reine Kollisionsvertrag ist ein Baustein, kein heimlich implementierter paralleler Installer.

## Prüfungen

Neue Standardbibliothek-Tests in `tests/test_v2_target_ownership.py` überprüfen sichere Einzel- und Mehrprojektfälle, identische und case-insensitive Ziele, fremdbelegte Ziele, leere Fremdbesitzliste, doppelte Eigentümer/Repos, unzulässige Quellen/Commitwerte, Sicherheitsflags, manipulierte Gruppen, Maximalgrößen, nicht veränderte Eingabeobjekte und dauerhaft gesperrte Schreibfreigaben.

`tests/test_v2_source_preflight.py` prüft zusätzlich die case-insensitive doppelte Zielwurzel **im Manifest**. Alle CI-Tests laufen über den vorhandenen GitHub-Actions-Workflow; ein CI-Erfolg ist eine statische Prüfung, keine HA-/Android-Realabnahme.

## Nächster technischer Schritt (Gate bleibt offen)

1. Ein **serverseitig abfragbares, unabhängiges V1-/V2-/Fremdziel-Besitzinventar** entwerfen, das eine unbekannte oder konkurrierende Instanz immer als blockierend behandelt. Kein bloßes „Benutzer bestätigt Besitz“ als technischer Beweis.
2. Exakte Quell-, Projekt-, Ziel- und Sitzungsidentität als zeitlich begrenzten Freigabevertrag mit frischer Vorprüfung führen; jeder Quell-/Zielwechsel invalidiert die Freigabe.
3. Einen **prozessübergreifenden** Schreibschutz bzw. einen verifizierten Übergabevertrag zwischen DRA V1 und V2 konzipieren, **ohne V1 in diesem Auftrag zu verändern**. Wenn das nicht beweisbar ist, Installation weiterhin verweigern.
4. Eine echte vollständige, unabhängig von Quell-/Staging-Dateien erstellte **V2-eigene Datenträgersicherung**, die vor einer Mutation erneut aus Archivbytes vollständig verifiziert wird, mit Restore-/Rollback- und Neustart-Recovery-Tests.
5. Erst nach gesonderten Admin-/HA-/Fehlerabnahmen kontrolliert die Freigabephase 2 und spätere Installationsphase 3 anbinden. Zuerst Einzelinstallation, danach priorisierte und konfliktsichere Sammelinstallation; Selbstupdate zuletzt.
6. Realabnahme der bereits vorhandenen 0.1.53/0.1.54-UI und Quellvorschau im ausdrücklich vom Nutzer aktualisierten DEV-Labor. Kein eigenständiges HA-Update oder Neustart.

## Schutz der anderen Repositories

DRA V1 DEV/PUB, V2 PUB, V2 DEV `main`, WeatherRouter, das private Exportarchiv und PR #2 (Entwurf, nicht zusammenführen) bleiben unangetastet. **Neue echte Exporte** ausschließlich in `TheDaimos/Project-Log-And-Export`; dieses Paket erzeugt keine realen Exporte.

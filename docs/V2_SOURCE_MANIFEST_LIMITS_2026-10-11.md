# DRA V2 DEV 0.1.55 – V1-Manifestgrenzen bei begrenzter Quellvorschau

**Datum:** 11.10.2026  
**Arbeitszweig:** `feature/v2-10-inventory-operation-contract`  
**Abnahme:** Quellcode- und Negativtests; Home-Assistant-/Android-Realtest offen. Keine V2-Installationsfreigabe.

## Anlass und statisch nachvollziehbare Ursache

Eine im isolierten V2-DEV-Labor ausgeführte Einzel-Quellvorschau meldete eine nicht prüfbare Quelle. Die bisherige V2-Implementierung hat in `source_preflight.parse_manifest` die **vom Quellmanifest deklarierten Obergrenzen** mit ihren eigenen viel kleineren **tatsächlich erlaubten Scanbudgets** verwechselt: Deklarationen über 1.000 Dateien bzw. 32 MiB wurden bereits beim Lesen abgelehnt.

Das öffentliche Referenzprojekt `TheDaimos/gewitterradar` hat im `main`-`deploy-relay.json` zulässige V1-Manifestdeklarationen von **5.000 Dateien und 150 MiB**. Die Git-Baum-Bestandsaufnahme des entsprechenden öffentlichen Hauptzweigs ergab 125 Dateien unter `custom_components/gewitterradar/` mit insgesamt 20.078.990 Byte (rund 19,1 MiB) und einen vollständigen Git-Baum unterhalb der V2-Gesamtgrenze. Diese Zahlen sind eine öffentliche Quellprüfung, **keine Aussage über die lokale HA-Dateimenge**.

Die Kombination war daher ein reproduzierbarer *statischer* Ablehnungsgrund. Sie beweist allein noch nicht, dass jede weitere Voraussetzung der realen Vorschau erfüllt ist (Projekt-Repository, Token, HA-Dateizustand oder aktuelle Git-Quelle sind serverseitig erneut zu prüfen).

## Implementierter korrigierter Vertrag

`source_preflight.py` unterscheidet nun:

| Angabe | Vom V1-Quellmanifest akzeptiert | In V2 maximal tatsächlich geprüft |
| --- | --- | --- |
| Dateien | 5.000 | **1.000** |
| Datenvolumen | 150 MiB | **32 MiB** |

- Nur **positive echte Ganzzahlen** bis zu den V1-Manifest-Obergrenzen sind erlaubt.
- Der wirksame V2-Grenzwert ist je Feld das **Minimum** aus deklarierter Projektgrenze und harter V2-Lesegrenze. Ein Manifest kann das V2-Ressourcenbudget niemals erhöhen.
- Überschreitet eine wirkliche Quelle oder ein HA-Zielbestand die wirksamen 1.000 Dateien / 32 MiB, bricht die Vorschau weiterhin konsequent ab. Kein Überspringen, Abschneiden oder behauptetes `sources_verified=true` bei unvollständiger Bestandsaufnahme.
- SHA-genauer Commit, strenge Quell-/Zielpfade, vollständiger Git-Baum, Symlink-/Hardlink-Schutz, begrenzte GitHub-HTTP-Antwort und `O_NOFOLLOW` bleiben unverändert.
- Die vorhandenen Admin- und Zielbesitzprüfungen einschließlich `target_claims` aus 0.1.54 bleiben aktiv; auch bei erfolgreicher Vorschau bleiben `installation_enabled=false`, `backup_verified=false` und `handover_required=true`.
- Es wurden **weder** HA-Dateien **noch** das öffentliche Gewitterradar-Repository, DRA V1, V2 PUB, `main`, WeatherRouter oder das private Exportarchiv verändert.

## Testfälle und nächstes Realtest-Gate

`tests/test_v2_source_preflight.py` prüft akzeptierte V1-Grenzwerte samt wirksamer Begrenzung, echte Quellüberschreitungen, Listen mit über 1.000 Dateien sowie fehlerhafte und übergroße Deklarationen. `tests/test_v2_source_remote.py` prüft eine vollständige simulierte GitHub-Vorschau mit der V1-Deklaration und liest ausschließlich lokal angelegte künstliche Testdateien ohne Änderung.

**Noch ausstehend:** Der Nutzer installiert 0.1.55 selbst über DRA V1 im isolierten HA-DEV-Labor und führt genau **eine** schreibgeschützte Gewitterradar-Vorschau aus. Anschließend wird geprüft, ob der Zielbesitz-Vertrag sichtbar und der tatsächliche Quellstand SHA-gepinnt ist. Schlägt die Vorschau weiterhin fehl, ohne echte Diagnoseexporte öffentlich abzulegen die serverseitige Fehlkategorie bestimmen; nicht erneut die Ressourcenlimits pauschal erhöhen oder die Installation freischalten.

**Schutzgrenze:** Keine automatische Installation, kein automatischer Neustart. Neue echte Diagnose-/Testexporte ausschließlich in das private `TheDaimos/Project-Log-And-Export`, niemals in dieses öffentliche Projekt-Repository. Draft-PR #2 bleibt Entwurf.

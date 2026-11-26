# DRA V2 DEV – Selbstupdate ohne DRA-V1-Abhängigkeit (26.11.2026)

## Auftrag / bindende Betreiberentscheidung
DRA V2 soll sich über seinen vorhandenen eigenen Einzelupdate-Pfad aktualisieren können. DRA V1 darf keine zwingende externe Bootstrap-Voraussetzung bleiben. **Kein Umbau** des bestehenden V2-Installationsworkflows; Pop-up, 4 Schritte, HA-Controller, Challenge, ausdrücklich bestätigter Start, Backups, V1-basierte Engine und Rollback bleiben unverändert. Nur DEV-Branch, nicht PROD oder V1.

## Ursache
Die alte UI-Prüfung `this._serverVersion !== DRA_V2_UI_VERSION` sperrte bei 0.1.123-Frontend / 0.1.122-HA-Laufzeit bereits die Controller-Synchronisation. Damit war auch die vorbereitende Freigabe unmöglich, obwohl die read-only-Quellprüfung erfolgreich war.

## Implementierung
- `custom_components/deploy_relay_v2_dev/frontend/lab.js`: zentrale Methode `_runtimeCompatible()`, die vorhandene, wohlgeformte SemVer-Ziffern fordert und **identische Major-/Minor-Linie** voraussetzt. Patch-Abweichungen innerhalb der API-Linie (z. B. UI 0.1.123, HA 0.1.122) werden nicht länger aufgrund der Versionsnummer allein gesperrt; unbekannte Versionen und andere Major-/Minor-Linien bleiben gesperrt.
- Die bisherigen Gleichheits-Abbruchstellen für Controller, vorbereitete Session, Startvorbereitung, Selbstupdate/Batch, Status, Neustart und Buttons verwenden diese zentrale Prüfung; das G2-Experiment behält seinen gesonderten exakten Testversionsvertrag.
- Unterschiedliche, aber zugelassene Patchstände werden sichtbar als „Kompatible Patch-Versionen · Selbstupdate möglich“ gekennzeichnet. Kein stilles Vertuschen der Differenz.
- Die bestehenden WebSocket-Schema-/Challenge-/Commit-/Bestätigungsprüfungen bleiben unverändert. Insbesondere bedeutet kompatible Versionslinie **nicht**, dass der Backend-Start selbst autorisiert wäre.
- Das bestehende Einzel-Selbstupdate läuft über `_openSingleSelfUpdate` als **Ein-Projekt-Batch**, mit derselben abgesicherten HA-seitigen Engine, nicht über einen ungesicherten Direkt-Schreibpfad. Im Sammelupdate bleibt DRA V2 zuletzt.

## Tests
`tests/test_v2_frontend_backend_version_parity.py` wurde um einen Kompatibilitätsvertrag erweitert und verlangt weiterhin identische Versionsmarker innerhalb des gelieferten Builds sowie die unveränderten Freigabeprüfungen.

**Wichtige Grenze:** Eine gemeinsame Major-/Minor-Version ist eine technische Zulassungsregel, noch kein empirischer Nachweis der Kompatibilität *aller* künftigen Patches. Bei inkompatiblen Protokolländerungen muss die API-Linie erhöht bzw. die Prüfung präzisiert werden. Die HA-seitigen Schemaprüfungen müssen bestehen bleiben.

## Abnahme offen / Arbeitsauftrag für DRA-Entwicklungschat
1. Remote-HEAD und diff prüfen. Python-Suite, JS-Syntax, Frontend-Regressionen und relevante V2-Selbstupdate-, Einzelupdate-, Batch-, Absturz-/Rollback-Tests ausführen. Vorbestehende Legacy-JS-Fehler separat kennzeichnen; keine Tests abschalten.
2. Auf DEV VM109 in kontrolliertem Test zuerst die Ausgangslage UI 0.1.123 / HA 0.1.122 nachstellen. **Wichtig:** Eine bereits auf dem Browser laufende alte UI enthält die neue Regel noch nicht. Nur nach Laden der geänderten UI kann die neue Kompatibilitätsprüfung wirken. Keine beliebige Umgehung von HA-Backend-Grenzen.
3. Selbstupdate über DRA V2 als Einzelauftrag mit realer V1-Sicherung, Challenge, Bestätigung und sicherem Neustart durchführen; danach gleiche UI/HA-Version sowie GR-Einzelupdate prüfen.
4. Nach Crash oder abgebrochener Übertragung keinen zweiten Installationsstart ohne Server-Audit; bestehende Wiederaufnahme-/Rollback-Verträge beibehalten.
5. Keine Änderung an PROD/anderen Projekten ohne Betreiberfreigabe.

## Revisionsstand
Implementierung: `4374f2d0c28a65a278c50ab1a9443854049a3ebc`.
Regressionstest: `e5ab5ac962fdaed542dc814f37d2e631dd970291`.
Dokumentation wird im gleichen DEV-Branch abgelegt. Reale VM109-Abnahme und End-to-End-Selbstupdate sind **noch nicht bestätigt**.

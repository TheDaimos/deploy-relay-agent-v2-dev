# DRA V2 0.1.126 DEV – Eigenupdate: Git-Inventarprüfung resilient und eindeutig

Datum: 26.11.2026
Branch: `feature/v2-10-inventory-operation-contract`
Status: DEV-Code committed, öffentliche CI geprüft; Betreiberabnahme auf VM109 ausstehend.

## Befund / Betreiber-Nachweis

Beim Einzel-Selbstupdate in DRA V2 0.1.124 scheiterte die über die unveränderte Batch-Engine vermittelte Vorbereitung mit `status=failed`, `check_stage=inventory`, `error_code=source_invalid`, `error_detail=inventory_read_unavailable`. Der Screenshot meldete ausdrücklich **keine gestartete Installation**. Es handelt sich nicht um den gesonderten 2/4-Freigabe-Bug der Version 0.1.125.

Im aktuellen DRA-V2-Quellbranch enthält die verwaltete Integration genau 51 Git-Dateien (ca. 896 kB), keine Git-Symlinks, und das Selbstupdate-Manifest begrenzt auf 51 Dateien / 3 MiB. Damit ist eine reine Grenzwertüberschreitung für den geprüften Branch nicht belegt. `inventory_read_unavailable` ist ein generischer, datenschutzsicherer Fehlercode; die HA-Diagnose beweist **nicht**, ob tatsächlich HTTP-429, sekundäre 403-Drosselung, HTTP-5xx oder ein anderer GitHub-Lesefehler auftrat.

## Korrektur – V2-Adapter, unveränderte V1-Engine

- `v1_source_bridge.py`: Bis zu **drei** vollständige, strikt schreibgeschützte Inventar-Leseversuche, mit begrenzten Pausen von 2 und 5 Sekunden, **nur** wenn die unterlagerte V1-Inventarfunktion eine als vorübergehend erkennbare GitHub-Lesestörung meldet (primäre Rate-Limits, mögliche sekundäre 403-Drosselung, HTTP 429/500/502/503/504 oder Verbindungs-/Timeoutfehler).
- Jeder Versuch bleibt auf denselben zuvor bestätigten 40-stelligen Commit und das unveränderte Manifest festgelegt. V1-Inventarfunktion und V1-Installationsengine wurden **nicht** verändert; alle Dateihashes, Größenlimits, Verzeichnis-/Symlinkschutz, explizite Freigaben, Transaktionen und Rollback bleiben in Kraft.
- Pfadfehler, gefälschte Commits, fehlerhafte Manifeste und nicht klassifizierte Fehler werden weder akzeptiert noch automatisch übergangen.
- Falls die GitHub-Lesestörung auch nach drei Versuchen besteht, meldet der Backend-Status den erlaubten Code `inventory_transient_exhausted`; die Oberfläche erklärt den Ausfall ohne Rohantworten, Token, private Pfade oder Projektdateien preiszugeben. Keine Installation wird gestartet.

## Nachgewiesene Tests

- `tests/test_v2_frozen_v1_source_bridge.py`: Fehler beim ersten Leseversuch, erfolgreiches Weiterlesen am identischen SHA; sekundäre GitHub-403-Drosselung; dauerhaft erschöpfter Retry-Pfad; keine Wiederholung bei unsicheren Pfaden oder unerwarteten GitHub-Fehlern; keine Ziel-Dateischreibzugriffe.
- Öffentliche `v2-validate.yml`: **461 Python-Tests erfolgreich**, dazu JavaScript-Syntax und tatsächliche JS-Verhaltenstests. Ausführung auf Commit `4d41fe35e459`, Läufe `45841884598` und `45841889489` erfolgreich.
- `v2-version-parity.yml` und `v2-source-budget.yml`: bestanden auf der versionsgleichen Basis, nach `0.1.126`-Versionserhöhung, bevor ausschließlich Test-Fixtures aktualisiert wurden.

Die **tatsächliche GitHub-Drosselung auf VM109 ist nicht reproduziert** und die Installation bleibt bis zur Betreiberabnahme unbestätigt.

## Realabnahme / Bootstrap

Der Betreiber verwendet derzeit DRA V2 0.1.124. Der V2-Selbstupdatepfad ist gerade wegen des Inventarfehlers blockiert. Falls die bisherige DRA-V2-Sammel-/Einzel-Selbstaktualisierung mit dem vorhandenen Frontend nicht durchläuft, kann der **bestehende DRA V1** den Branch `feature/v2-10-inventory-operation-contract` einmalig auf DRA V2 0.1.126 einspielen. Niemals Sicherheitsprüfungen umgehen oder selbst Dateien an den Installationszielen ersetzen.

Danach in DRA V2 Oberfläche/HA-Laufzeit 0.1.126 bestätigen, eigene Git-Quelle schreibgeschützt prüfen, genau ein DRA-V2-Selbstupdate vorbereiten, Commit-Digest und explizite Freigabe prüfen, nach HA-Neustart Versionsgleichheit bestätigen. Bei erneutem Fehler den zulässigen `error_detail` und Quellref/Commit im DRA Audit vergleichen. Es darf nicht behauptet werden, dass ein über die CI hinausgehender HA-Test bereits bestanden sei.

Keine FINAL-Version, keine PROD-Änderung.

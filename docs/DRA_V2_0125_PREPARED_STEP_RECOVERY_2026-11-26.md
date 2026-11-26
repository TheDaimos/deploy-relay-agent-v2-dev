# DRA V2 0.1.125 DEV – Schritt 2: vorbereitete Installation wiederaufnehmen

Datum: 26.11.2026
Branch: `feature/v2-10-inventory-operation-contract`
Status: Auf Entwicklungsbranch committed, öffentliche CI geprüft; DEV-VM109-Realabnahme noch offen.

## Betreiberbeobachtung

GewitterRadar `feature/v4.14-monitored-areas`, DRA V2 0.1.124: `2/4 · Installation vorbereiten` bleibt stehen, obwohl Status `Vorbereitung abgeschlossen. Noch wurden keine Dateien geändert.` meldet. Kein Bestätigungsdialog erscheint. Versionsvergleich `4.14.4` (Quelle) zu `4.14.2` (lokal), `1` geänderte Datei, `291` unverändert.

Der vom Betreiber gelieferte Diagnoseexport `2026-11-26T14-29-30Z` ist **nur** ein schreibgeschützter Quelltest: `status: success`, `stage: target_claims`, `sources_verified: true`, `installation_enabled: false`; er enthält keinen serverseitigen Vorbereitungs-Challenge-Status. Kein Installationsstart wurde durch diese Diagnose bestätigt.

## Technische Eingrenzung

Die UI zeigte eine erfolgreiche Vorbereitung über `_installMessage`; `preparedInstall` wird jedoch nur gerendert, wenn `_installPreparation` aktuell ist und deren `source_ref` mit der ausgewählten Referenz übereinstimmt. Die reguläre 10-s- und Hintergrund-Synchronisation kann abgelaufene/nicht bestätigte Pending-Pläne aus der lokalen Ansicht entfernen, ohne bisher die alte Erfolgsmeldung zurückzusetzen. Das kann zu einer irreführenden Schritt-2-Anzeige führen. Ein konkretes Netzwerk-/Timing-Race auf VM109 ist damit noch nicht bewiesen.

## Implementierte Korrektur

1. Vor einem erneuten Schritt-2-Vorbereitungsversuch fragt `_resumeOrPrepareInstallation(project)` ausdrücklich den **serverseitigen Prepared-Status** ab. Ein vorhandener Challenge für exakt dieselbe Repository-/Ref-/Commit-Kombination wird nur wieder angezeigt; er wird weder ersetzt noch automatisch bestätigt.
2. Wenn kein gültiger HA-Prepared-Status mehr existiert, wird die bisherige lokale Erfolgsmeldung zurückgenommen und der gewöhnliche Vorbereitungsweg verwendet.
3. Der aus HA zurückgelesene Pending-Status wird gegen das bereits schreibgeschützt geprüfte Ref/Commit abgeglichen; eine fremde/ältere Freigabe wird nicht als aktueller Installationsplan präsentiert.
4. Eine neue `deployment/prepare`-Antwort wird auf dasselbe Ref und denselben unveränderlichen Commit geprüft. Eine Abweichung kann keine scheinbar erfolgreiche Freigabe auslösen.
5. Die unveränderte V1-Engine, Backup-/Rollback-Verträge, explizite Admin-/Controller-Bestätigung und 4-Schritte-Sicherheitsgrenzen bleiben erhalten. Keine direkte Schreiboperation ohne Freigabe.

## Test

`tests/test_v2_countdown.js`: Verhaltenstest für erfolgreiche Wiederaufnahme eines identischen bestehenden Server-Plans ohne erneuten Prepare-Aufruf und für erlaubten Prepare-Retry nur nach negativem serverseitigem Prepared-Lookup. Öffentliche V2-Gesamtvalidierung für Commit `ef6752510314` erfolgreich (GitHub Actions Run `45840012866`), einschließlich Python-Vertragstests, Python- und JavaScript-Syntax sowie JS-Verhaltenstest.

Die HA-Laufzeitprüfung auf VM109 steht noch aus. `0.1.125` ist DEV und keine FINAL-Version.

## Betreiberabnahme

DRA V2 0.1.125 über die bereits funktionierende DRA-V2-Eigenaktualisierung installieren und Backend-/Frontend-Versionsgleichheit prüfen. Anschließend GR 4.14.4 aus `feature/v4.14-monitored-areas` auswählen, Vorschau prüfen und Schritt 2 betätigen. Erwartet: vorbereiteter HA-Plan wird übernommen und der ausdrückliche Button `Ja, Update installieren` erscheint, ohne dass vorher Dateien geschrieben wurden. Falls nicht: Audit (Vorbereitungsphase) und `deployment/prepared_status`-Status gezielt prüfen; keine unkontrollierten Wiederholungen und keine manuellen HA-Dateioperationen.

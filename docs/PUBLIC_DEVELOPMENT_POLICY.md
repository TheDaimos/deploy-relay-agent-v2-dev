# Sicherheitsregeln für das öffentliche DRA-V2-Repository

## Veröffentlichung und Quellen

Nur bewusst veröffentlichte Inhalte und bereits freigegebene öffentliche Quellbasis. Eine private Git-Historie darf nicht geklont oder durch Änderung der Sichtbarkeit offengelegt werden.

Nicht veröffentlichen: Zugangsdaten, GitHub-PATs, Home-Assistant-Authentifizierung, .env, secrets.yaml, echte Backups, JSONL-Protokolle, Diagnoseexporte, private Erweiterungen, lokale Konfigurationsdateien, Infrastrukturkennungen, Geräte- oder personenbezogene Daten. Das Verbot gilt auch für Tests, GitHub Actions, Kommentare und Artefakte.

## GitHub Actions

- Öffentliche Standard-Runner, keine kostenpflichtigen großen Runner.
- Standardmäßig nur contents: read, keine Veröffentlichungstokens für eingehende Pull Requests.
- Keine privilegierte Ausführung von ungeprüftem Beitragscode.
- Aufträge bei veralteten Prüfständen abbrechen, unnötige Push-/Pull-Request-Doppelläufe vermeiden.
- Keinen pauschalen Artefaktupload; das GitHub-Artefaktspeicherkontingent ist von den kostenlosen öffentlichen Runner-Minuten getrennt.
- Quell-/Lizenz-/Sicherheitstests vor teureren HA-Tests; reale Abnahmen bleiben Pflicht.
- Keine automatische Installation und keine Freigabe aus Pull Requests.

## Lizenz und Identität

Ausgangsbasis: ausschließlich öffentlich freigegebene V1. Die Software ist GPL-3.0-only, die offiziellen Markenbilder sind nach BRANDING.md gesondert geschützt. Siehe SOURCE_PROVENANCE.md.

## Freigabe

Der Hauptzweig ist Entwicklung, nicht automatisch ein stabiler HACS-Kanal. Neue Versionskennungen und Veröffentlichungen benötigen Abnahmetests, Sicherheitsprüfung und dokumentierte Freigabe.

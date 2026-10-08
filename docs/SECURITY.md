# Deploy Relay Agent — Sicherheit

## Grundsatz

DRA ist absichtlich restriktiver als technisch möglich.

## Sicherheitsmodell

```text
LOCKED
→ explizite DEVELOPMENT-Freigabe
→ frische serverseitige Prüfung
→ Backup
→ Mutation
→ Verifikation
→ SUCCESS / ROLLBACK / RECOVERY_REQUIRED
```

## Keine stillen Schreibrechte

DEVELOPMENT ist runtime-only und wird nach einem HA-Neustart nicht beibehalten.

## Keine beliebigen Skripte

DRA ist kein Shell-Runner.

## Pfadgrenzen

Deploymentziele müssen im genehmigten DRA-Scope liegen. Traversal, unzulässige absolute Pfade und nicht freigegebene Dateisystemziele werden fail-closed behandelt.

## Git-Identität

Bewegliche Refs werden auf einen exakten Commit aufgelöst. Ein bereits eingefrorener Commit wird nicht still durch einen neueren Branchstand ersetzt.

## Backup / Recovery

Vor Mutation entsteht ein Wiederherstellungspunkt. Kann nach einem Fehler kein eindeutig sicherer Zustand bewiesen werden, muss DRA `RECOVERY_REQUIRED` melden.

## Tokens

Normaler Projektzugang:

```text
Metadata: Read
Contents: Read
```

Optionaler Diagnoseexport verwendet einen separaten projektspezifischen Schreibtoken.

## Diagnose

Secrets werden vor Persistenz und Export redigiert.

## Kein automatischer Neustart

DRA kann eine Nachaktion empfehlen, führt einen vollständigen Home-Assistant-Neustart aber nicht selbständig aus.

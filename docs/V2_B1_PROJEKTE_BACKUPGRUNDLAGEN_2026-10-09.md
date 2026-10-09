# DRA V2 – Paket B1: Projekte übernehmen, anlegen und Sicherungsrichtlinie

Stand: 09.10.2026 · V2 DEV **0.1.9** · Entwicklungsstand, keine HA-Realabnahme.

## Implementiert und automatisch geprüft

- V2-eigene persistente Projektliste in Home Assistants eigenem Store-Schlüssel
  deploy_relay_v2_dev.projects; genau ein lokaler Katalog für das isolierte
  DRA-V2-Testlabor. Striktes Schema dra-v2-dev-projects.v1, maximal 32 Projekte,
  begrenzte Daten und atomare Speicherung mittels HA Store. Beschädigte oder
  unbekannte Schemawerte führen zum konservativen Ladeabbruch, keine automatische
  Rücksetzung. Keine Daten im öffentlichen Git-Mess-Export.
- V1-Projektvorschau ausschließlich aus Home Assistants V1-Config-Subentries.
  Nur Anzeigename/Repository und vorhandene Sicherungs-Aufbewahrungszahl
  übernehmen, keine Tokens, Quell-Commits, lokalen Sicherungsverzeichnisse,
  ausgewählten Branches oder V1-Konfigurations-IDs. V1 niemals verändern.
  Erst durch einen **gesonderten Import-Klick** werden die validierten
  Vorschlagsmetadaten im privaten V2-Katalog gespeichert.
- Manuelles Vormerken eines GitHub-Repositories und Anzeigenamens. Strenge
  Namens-/Repository-Validierung, Fall-insensitive Dublettenprüfung und
  eindeutige lokale Projektkennungen. Alle neuen Einträge bleiben auf
  pending_review; **keine Annahme einer validierten GitHub-Quelle** ohne
  spätere V2-eigene Repository-/Manifestprüfung.
- Eigene Sicherungs-Aufbewahrungszahl pro Projekt. Standard **10**, Minimum
  **3**, Maximum **100**; Änderung ändert nur diese Richtlinie im privaten
  V2-Projektkatalog. Es werden dabei ausdrücklich keine vorhandenen
  V1-/V2-Sicherungsdateien gelöscht.
- Strenger, seiteneffektfreier **Rotationsplaner**: erkennt nur V2-eigene,
  vollständig verifizierte, projektidentische und nicht durch laufende
  Recovery geschützte Sicherungseinträge als Kandidaten, ordnet sie nach
  Datum, schützt die letzten konfigurierten Wiederherstellungspunkte und
  weist fremde, doppelte, unbekannte oder unvollständige Angaben zurück.
  Der Planer selbst **kopiert, sichert, löscht oder stellt nichts wieder her**.
- Fünf zusätzliche nur für Administratoren zugelassene WebSocket-Routen
  unter deploy_relay_v2_dev/projects/: list, v1_preview, import_v1, add,
  retention. Diese erlauben ausschließlich V2-Projektmetadaten und
  keine echten Installations-/Restore-/Restart-Mutationen. Die bisherige
  V2-Operationsverwaltung und der globale Mutationsschutz bleiben unberührt.
- Mobile Frontend-Sektion: V1-Vorschau und ausdrückliche Übernahme,
  manuelles Vormerken sowie pro Projekt die Aufbewahrungszahl. Namen
  werden vor Darstellung im HTML entschärft; keine Git-Tokens oder
  unkontrollierten externen URL-Aufrufe.

## Voraussetzungen vor einer tatsächlichen V2-Installation

Der Import eines bekannten V1-Projekts ist **nicht** die technische Autorisierung
für eine V2-Installation. Der vollständige unabhängige V2-Transaktionspfad muss
vorher separat implementiert und verifiziert werden:

1. V2-eigene GitHub-Zugangsdaten ausschließlich für benötigte Leserechte,
   keine Übernahme von V1-Secrets. Canonical Source-SHA fixieren.
2. Manifest und Projektkennung an der festen Source-SHA einlesen, erlaubte
   Projekt-Zielpfade, Ausschlüsse, Dateianzahl, Größen und geplante Änderungen
   prüfen und lesend anzeigen.
3. Dateien unter einem **ausschließlich V2-eigenen** Staging-Bereich
   materialisieren, SHA-256 und Dateigröße prüfen, keine Symlinks/Hardlinks.
4. Vor jeder Mutation vollständige, unabhängig restorable **V2-Sicherung**
   des tatsächlich betroffenen verwalteten Bereichs erzeugen (nicht nur
   einzelne Deltas), Dateihashes prüfen, Transaktion dauerhaft protokollieren.
5. **Zwei Freigaben**: flüchtige DEVELOPMENT-Schreibfreigabe und einzelne,
   eindeutig bestätigte Installation für ein Projekt/Commit; globale
   Mutationssperre zunächst **1**.
6. Installation atomar soweit möglich und vollständig nachprüfen;
   Fehler automatisch aus der frisch validierten Sicherung zurückrollen,
   bei unsicherem Resultat recovery_required, niemals still fortfahren.
7. Nach erfolgreicher Installation Retention getrennt und nur für
   ausschließlich V2-eigene, verifizierte, nicht geschützte Sicherungen
   durchführen; niemals vor bestätigter Fertigstellung oder gegen aktive
   Recovery. Ein Rotationsfehler darf keine wiederherstellbare Sicherung
   entfernen und wird als Warnung behandelt.
8. Manuelle Restore-Auswahl nur aus vollständigen und unabhängig verifizierten
   Sicherungen, jeweils neue Sicherheits-Sicherung vor der Wiederherstellung.
   HA-Neustart nur mit gesonderter Sicherheitsabfrage und zweiter Zustimmung.

Der tatsächliche Schutz- und Backup-Bereich muss vorher festgelegt und
vom V1-Bereich /config/deploy_relay getrennt sein. Bei projektbezogen
gleichen Installationszielen darf keine parallele V1/V2-Schreibaktion ohne
nachgewiesenen gemeinsamen Sicherheitsvertrag stattfinden. Bis dahin
sind produktive Schreib- und Restore-Befehle nicht verfügbar.

## Abnahme und Status

Das Paket ist **CODE/CI**-geprüft, nicht auf HA-DEV installiert oder
als V1-Übernahme tatsächlich ausgeführt. Nach Freigabe ist ein
gezielter V1-Vorschau-/V2-Import-/Neuanlage-/Aufbewahrungs-Realtest
möglich, ohne Installations- oder Restore-Schreibpfad freizugeben.

Der Benutzerwunsch nach realer Installation aus V2, echten Backups,
automatischer Rotation und Restore ist **noch offen** und wird erst mit
einem unabhängigen, geprüften V2-Transaktionskern erfüllt. Keine bloße
Übernahme der V1-Laufzeit oder des V1-Backup-Verzeichnisses.

V2-PUB, V1-DEV/PUB und V2-DEV main unverändert, Draft-PR #2 bleibt Entwurf.

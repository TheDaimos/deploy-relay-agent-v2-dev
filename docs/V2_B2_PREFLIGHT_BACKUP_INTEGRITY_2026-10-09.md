# DRA V2 DEV 0.1.13 – Paket B2/A: SHA-genaue GitHub-Quellprüfung und vollständiger Sicherungsnachweis

Stand: 09.10.2026 · Repository `TheDaimos/deploy-relay-agent-v2-dev` · `feature/v2-10-inventory-operation-contract`

## Ziel und verbindliche Trennung

Mehrere zusammengehörige Funktionen wurden als **ein Paket** entwickelt, ohne einen echten Installations-, Wiederherstellungs- oder HA-Neustartauftrag zu eröffnen.

**Neu bereitgestellt:** Aus einem bereits im eigenen V2-Projektverzeichnis registrierten Repository kann ein Administrator eine **ausschließlich lesende, streng begrenzte Quellprüfung** auslösen. Für **öffentliche** GitHub-Repositories wird zuerst der gewünschte Zweig oder ersatzweise der Standardzweig in einen **festen 40-stelligen Commit** aufgelöst. An dieser festen Revision werden `deploy-relay.json`, die zugehörige Git-Baumstruktur und deren Dateigrenzen geprüft. Anschließend erfolgt ein lesender Vergleich der ausgewählten Quelldateien mit dem tatsächlich vorhandenen HA-Zielordner.

**Nicht freigegeben:** Aus dem Prüfergebnis darf kein Installationsauftrag erzeugt werden; `installation_enabled=false`, `handover_required=true`, `backup_verified=false`. Es werden keine Dateien verändert, keine früheren V1-Sicherungen übernommen, keine V1-Zugangsdaten gelesen und keine fremde Integration installiert.

## Einzelne, nachvollziehbar gebündelte Funktionen

1. `source_preflight.py`: strenge V2-eigene Manifestprüfung nach dem v1-Manifestvertrag; nur `repository_contents`, `replace_directory`, `/config` als logisches Ziel, passende Repositorykennung, feste Datei-/Byte-Budgets, keine Symlinks und kein Zugriff auf `.storage`, `deploy_relay` oder `deploy_relay_v2_dev`. Komplexere Installationsarten sind bewusst noch `unsupported`, nicht stillschweigend freigegeben.
2. **Git-Baumprüfung** an vollständiger Commit-gebundener Revision: typisierte Blob-/Baumeinträge, Git-Blob-Hashes, Größen, Doppelungen, Normpfade und Quellgruppen. Unvollständige GitHub-Bäume, Symlinks, Submodule, falsche Modi und nicht unterstützte Quellstrukturen führen zum konservativen Abbruch.
3. `remote_source.py`: begrenzte öffentliche GitHub-HTTPS-GETs, keine Tokenübernahme, keine Weiterleitungen, feste Ziel-Domain und Aufrufdauer/Antwortgrößen. Der Manifestinhalt wird mit der von GitHub angegebenen Blob-ID abgeglichen; ein GitHub-Fehler gilt nie als „aktuell“.
4. **HA-Dateivergleich ohne Schreibzugriff**: ausschließlich als vom Manifest verwaltete Pfade definierte Ordner unter `custom_components/<projekt>`; echte reguläre Dateien mit `O_NOFOLLOW`, Dateigrößen-/Inode-Kontrolle, harte Dateianzahl-/Volumengrenzen. Symbolische Verknüpfungen und unvollständig lesbare Verzeichnisse führen zum Abbruch. Nur generierte, echte `__pycache__`-Verzeichnisse werden bei der Dateiliste übersprungen. Keine unbekannten externen lokalen Verzeichnisse und keine Dateiinhalte im Ergebnis.
5. **Differenzvorschau je Projekt**: getrennte Dateinamen für hinzugefügt, verändert, bei einer späteren Installation entfernt und unverändert; SHA-genau auf der Quelle und Git-Blob-Hash-genau im lesenden lokalen Bestand. Die UI zeigt eine begrenzte Zahl von Einträgen, sodass große Listen mobil bedienbar bleiben. Es wird nur geprüft, wenn der Administrator je Projekt „Git-Quelle prüfen“ klickt.
6. **Neue eigene V2-Admin-Route** `deploy_relay_v2_dev/projects/source_preview`: prüft nur bereits registrierte Repositories, höchstens eine gleichzeitig laufende Quellprüfung und eine begrenzte Laufzeit. Öffentliche, schreibgeschützte Vorschau; keine Installationsfreigabe und kein Auftragsjournal-Eintrag für eine Mutation.
7. `backup_integrity.py`: **rein berechnender** Vertrag für vollständige, projektbezogene V2-Sicherungen: erlaubte Zielwurzeln, gesamte Dateiliste, Größen, SHA-256 aller Datei-Bytes, Prüfung auf **exakt vollständige** Dateimenge ohne zusätzliche/fehlende oder manipulierte Dateien. Rückgabe einer positiven Integritätskontrolle bedeutet nur „diese Bytes stimmen zum Manifest“, **nicht**, dass ein V2-Sicherungsarchiv tatsächlich erstellt, auf Datenträger gesichert, transaktional nutzbar oder zur Wiederherstellung freigegeben wurde.

## Bewusste Einschränkungen und nächste Entwicklungs-Gates

- **Private Repositories:** Ohne eigenen V2-Lesezugang wird ein solches Repository als nicht zugänglich gemeldet. Weder der V1-GitHub-Token noch der separate öffentliche V2-Diagnoseexport-Token dürfen als Ersatz verwendet werden. Eine vom Nutzer ausdrücklich eingerichtete, nur lesende und separat gespeicherte V2-Authentifizierung ist später erforderlich.
- **Projektübergabe:** Das Manifest benennt mögliche Zielordner, jedoch noch keinen Beweis ihrer exklusiven V2-Verwaltung. Bei vorhandenen V1-installierten Projekten darf **keine** echte V2-Mutation stattfinden, bevor ein verbindlicher Übergabe-/Lock-Vertrag bestand hat.
- **Sicherung:** Eine unabhängige, tatsächlich auf V2-eigene Datenträgerpfade geschriebene **vollständige Sicherung** vor der Mutation, deren Nachprüfung und eine Rücksicherung bei Fehlern fehlen noch. Der Prüfsummenvertrag ist nur deren Sicherheitsbaustein. Rotationsplanung bleibt seiteneffektfrei; eine Löschfunktion ist weiterhin nicht vorhanden.
- **Schreibtransaktion:** Quellpinnen, Staging, unabhängige V2-Sicherung, freier Speicher, Dateisystem- und Sperrenkontrolle, doppelte Freigabe, globale Mutationssperre, Installationsabschluss-/Rückfallprüfung, Journal-Recovery und zusätzliche Restore-Sicherheitskopie sind weiterhin getrennt einzuführende Gates.
- **Systemressourcen:** Die noch offene V2-40-50-Abnahme (exakte Zeitkorrelation von CPU, I/O, HA-Reaktionszeit) wird nicht durch den erfolgreichen schreibgeschützten Quelltest ersetzt. Keine zusätzliche HA-Test- oder Neustartpflicht pro kleinem Codecheckpoint.

## Abnahmeumfang

Quell- und Negativtests decken die sichere Pfadprüfung, Quellbaumvalidierung, echte SHA-gebundene HTTP-Antworten mit künstlichem GitHub-Server, unveränderte HA-Dateien, symlink- und fehlerbedingte Abbrüche sowie SHA-256-basierte Komplettheitsprüfung von Sicherungsdatei-Bytes ab. JavaScript-Anzeige, V1-Trennung, Administratorpflicht und 24-Dateien-Deploygrenze gehören zur Paket-CI.

**Status:** Implementierung in V2 DEV 0.1.13 vorbereitet. HA-DEV-Realabnahme offen, keine V2-Installation auf der Nutzerinstanz veranlasst. DRA V1 DEV/PUB, V2-PUB und V2-DEV `main` unverändert; Entwurfs-PR #2 nicht zusammenführen.

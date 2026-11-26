# DRA V2 DEV 0.1.73 – V1-Engine an serverseitige Installation und V2-Oberfläche angeschlossen

**Datum:** 12.10.2026  
**Entwicklungszweig:** `feature/v2-10-inventory-operation-contract`  
**Status:** Funktional implementiert und CI-grün. **Noch keine echte HA-Realabnahme.**

## Ziel und Umsetzung

Der beschleunigte Entwicklungsauftrag ist verbindlich: **DRA V2 ersetzt V1** und verwendet die bereits bewährten V1-Algorithmen für Manifest, Quellinventar, Dateivorschau, Staging, Sicherung, Installation, Integritätskontrolle und automatischen Rückfall. Keine Neuentwicklung dieser Engine, keine dauerhafte gemeinsame V1/V2-Sperrarchitektur.

**Ab 0.1.73 neu verbunden:**

- `DeploymentCoordinator`: Baut an einem registrierten, ausdrücklich mit **Lese- und Schreibrechten** versehenen Projekt eine vollständige, an den festen Git-Commit gebundene V1-Manifestauswertung, Quellinventur und reale Zieldifferenz **erneut** auf. Vorbereitung ist ausschließlich lesend.
- **Einmalige Freigabe**: Eine zufällige 128-Bit-Bestätigungskennung gilt maximal 120 Sekunden und wird nach einer ausdrücklichen zweiten Administratoraktion verbraucht. Keine aus dem Browser übergebenen Dateipfade, Manifeste, Sicherungen oder beliebigen Installationspläne.
- `ServerDeploymentJobs`: Übernimmt die bereits in der V2-DEV-Quellbasis eingefügte und isolierte echte V1-`async_execute_deployment`-Engine. Die bestehende V1-Sicherung, automatische Rückfalllogik und vorhandenen Zielintegritätskontrollen bleiben im Kern erhalten. Der Auftrag wird als HA-eigene Hintergrundaufgabe unabhängig vom Browser abgearbeitet.
- Die V2-API hat drei neue **administrativ geschützte** Befehle: `deployment/prepare`, `deployment/start`, `deployment/status`. Ein Auftragsstatus nennt nur erlaubte Metadaten, keine Tokens oder Projektdateiinhalte.
- Die bestehende **eine zentrale V2-Deployment-Schaltfläche** bietet nach gültiger Vorschau Schritt 2, die neuerliche Prüfung. Erst danach erscheint eine gesonderte, klare Schaltfläche **„Ja, Update installieren“**. Fortschritt, Auftragskennung, Erfolg und Neustarterfordernis sind in der Oberfläche abfragbar. Nach Clientverlust kann die Auftragskennung erneut abgefragt werden.
- V2-Laufzeit und G2-Leseaufträge sind getrennt. Neue schreibende Aufträge benutzen einen eigenen `OperationRegistry`; der alte read-only G2-Journalvertrag wird nicht aufgeweicht.
- Beim normalen Entladen der V2-Integration werden laufende Schreibaufträge **abgewartet**, nicht absichtlich abgebrochen.
- Nach einem unterbrochenen HA-Lauf erkennt V2 unvollständig abgeschlossene Transaktionsjournale der **V2-eigenen** V1-Engine im Pfad `/config/deploy_relay_v2_dev/transactions`. Der nächste Versuch wird **gesperrt**, bis eine Wiederherstellung geprüft ist. V1-Backup-/Datenordner werden nicht gelesen oder beschrieben.
- Ein V2-Selbstupdate und ein Update von DRA V1 über diese neue Strecke sind gesperrt.

## Automatisch geprüft

1. V1-Engine: wirkliche Dateiinstallation auf künstlichem Dateisystem, Backup, verifizierte Originaldateien nach automatischem Rückfall, Fehler vor Mutation, symbolische Verknüpfungen und isolierte V1-/V2-Speicherung.
2. Serverseitiger Auftragsverwalter: Wiederabfrage ohne Browserbesitz, genau eine Ausführung bei gleicher Kennung, Sperre gegen zweite schreibende Operation, ehrliche Fehler- und Wiederherstellungszustände.
3. Einmalige Installationsfreigabe und Neustart: Vorbereitung ist nicht Installation; Bestätigung kann nicht wiederholt werden; nicht passende Commitidentität wird gesperrt; abgeschlossene/störende Transaktionsjournale werden unterschieden.
4. Bedienoberfläche: V2-DEV-Versionierung, Vorbereitung, separate Bestätigung, tatsächliche HA-Auftragsantwort einschließlich Neustarterfordernis und unveränderte G2-Funktionen.
5. Mehrkernfähige echte V1-Dateivorschau für **mehrere unabhängige Dateigruppen** via begrenzte Prozesse, mit Rückfall auf dieselbe sequenzielle V1-Vorschau. Ein-Dateigruppen-Projekte profitieren von dieser spezifischen Verbesserung noch nicht.

**Gebündelter Prüflauf:** [GitHub Actions 38212629113 – SUCCESS](https://github.com/TheDaimos/deploy-relay-agent-v2-dev/actions/runs/38212629113), Code `ad707fc2d0abb814734f6a4eb6c3217b2d39b884` (anschließend nur noch einzelne Folgekorrekturen und Dokumentation). Vor einem HA-Realtest nochmals den CI-Endstand auf den letzten Codecommit prüfen.

## Noch keine falsche Fertigmeldung

- Die 0.1.73-Strecke wurde **noch nicht auf einer realen HA-Instanz mit einem Projektupdate getestet**. Die neue Backend-API muss unter HA, inklusive Browsertrennung und V1-Rückfall, gemeinsam abgenommen werden.
- Das HA-Prozessende mitten in einer laufenden Dateimutation kann nicht durch einen bloßen Browserstatus garantiert abgefangen werden. Das vorhandene V1-Transaktionsjournal wird konservativ gesperrt, wenn es nicht terminal ist. Keine falsche automatische Wiederherstellungsbehauptung nach Stromverlust.
- Parallele Updates **mehrerer unabhängiger Projekte** sind noch nicht aktiv; derzeit wird ein mutierender Auftrag exklusiv geführt. Mehrkern-Prozesse werden für unabhängig verwaltete Dateigruppen der echten **Vorschau** eingesetzt, nicht für parallele Dateischreibtransaktionen.
- Home Assistant wird nicht eigenmächtig neu gestartet. Ein erforderlicher Neustart wird als Ergebnis markiert und muss weiterhin ausdrücklich vom Betreiber ausgelöst werden.
- Das übernommene V1-Konzept ist die Referenz, kein Anlass für weitere G3-/G4-/G5-Neuentwicklungsschlachten.

## Nächste gebündelte HA-Abnahme

Nur eine V2-DEV-Aktualisierung über den aktuell funktionierenden V1-Weg und **ein** erforderlicher HA-Neustart. Anschließend ein Paket mit drei zusammengehörigen Ergebnissen: klare Versionsanzeige, unveränderte echte Quellvorschau und kontrollierte Installation **eines unkritischen Projekts** mit serverseitigem Status, Sicherung und Neustartinformation. Browser-/Netzwechsel innerhalb desselben Auftrags. Kein V2-Selbstupdate und kein ungeprüftes produktives Sammelupdate. Eventuelle Diagnose nur im privaten Projektarchiv.

**Git-Grenzen:** Nur `feature/v2-10-inventory-operation-contract`. Keine Änderung von V1 DEV/PUB, V2 main/PUB, WeatherRouter oder privatem Archiv. PR #2 bleibt offen und unmerged.

**C.K. – Eine Idee weiter gedacht.**

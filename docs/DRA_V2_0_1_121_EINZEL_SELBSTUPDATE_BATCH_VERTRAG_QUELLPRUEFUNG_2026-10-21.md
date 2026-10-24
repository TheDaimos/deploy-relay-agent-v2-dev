# DRA V2 0.1.121 DEV – Einzel-Selbstaktualisierung über den geprüften HA-Sammelvertrag

**Datum:** 21.10.2026  
**Repository:** `TheDaimos/deploy-relay-agent-v2-dev` (privat)  
**Zweig:** ausschließlich `feature/v2-10-inventory-operation-contract`  
**Ausgangspunkt:** auf dem Anwender-Screenshot installierte `0.1.120 DEV`, Oberfläche und HA-Python übereinstimmend  
**Neuer Programm-/Teststand:** `0.1.121 DEV`  
**Letzter Programm-/Testcommit:** `0ea12702c5e689f70e52308e8dacea1cd39c6b68`  
**GitHub Actions:** `39582019041` – `completed / SUCCESS` auf exakt diesem Commit.

## 1. Anlass und realer HA-Befund

Die Einzelprojektauswahl zeigt **„DRA V2 DEV – Nur Testlabor“** mit Git-Ref `feature/v2-10-inventory-operation-contract`. Der Anwender beanstandet, dass eine Eigenaktualisierung bisher nur über das Sammelupdate möglich ist, obwohl DRA V2 beim bestehenden Sammelablauf nach allen anderen Projekten mit V1-Engine, Sicherung und Rückfall aktualisiert werden kann. Eine eigenständige Quellenprüfung des eigenen Projekts soll ebenfalls möglich sein.

Wichtig ist die Unterscheidung der angezeigten Zustände: Im vorgelegten Screenshot läuft **gleichzeitig ein HA-Sammelauftrag im Zustand `preparing` mit „0 von 5 Quellen geprüft“**, und die Oberfläche zeigt **„Anderes Gerät steuert · Beobachtung“**. Das Screenshot zeigt keine abgeschlossene, erfolgreiche oder fehlgeschlagene DRA-V2-Einzelquellenprüfung, sondern „Quellstand noch nicht geprüft“. Der Source-Scan-Lock auf HA verhindert während einer laufenden Sammelquellprüfung einen parallelen zweiten Leseauftrag. Das ist korrekt und darf nicht durch eine neue Sperrumgehung ersetzt werden.

Der zuvor in `0.1.120` korrigierte, unvollständige Read-only-Eigenvorschauvertrag wurde geprüft. Es fehlt für das aktuelle Screenshot jedoch ein zugehöriger vollständiger HA-Quellprüfbericht; ein konkreter neuerer HA-Lese- oder GitHub-Fehler ist daher **nicht** bewiesen. Ein künftiger tatsächlicher Quellabbruch muss mit seiner Quellendiagnose separat eingegrenzt werden.

## 2. Architekturentscheidung: dieselbe sichere Engine, ein einzelnes Projekt

**Keine zweite Installationsengine und keine Freischaltung von `deployment/prepare` für Eigenziele.** Die bereits implementierte HA-Methode `batch/prepare` erlaubt **ein bis acht** aktive ausgewählte Projekte, und die serverseitige Planung `BatchDeployment` enthält bereits:

- unveränderliche, durch Git-Commit festgelegte V1-Pläne;
- verbindliche Manifest-/Identitäts-/Zielprüfung einschließlich des Eigenziels `custom_components/deploy_relay_v2_dev` und der Neustartpflicht;
- getrennte, HA-seitig gespeicherte Vorbereitungs- und Installationsphasen;
- ausdrücklich geprüfte Projekt-, Versions-, Ref- und 40-stellige Commitangaben;
- Prüfsumme `review_digest`, einmalige `challenge`, gerätegebundene Übernahme und bewusste Doppelbestätigung;
- Einmalannahme durch HA, V1-Sicherung, Journal, Rückfall und Neustartvormerkung;
- DRA V1 vor DRA V2 und DRA V2 als letztem Projekt, sofern mehrere vorhanden sind.

Der neue **Einzel-Selbstaktualisierungsweg** verwendet deshalb **genau diesen vorhandenen Sammelvertrag mit ausschließlich dem einen explizit angeforderten Repository `TheDaimos/deploy-relay-agent-v2-dev`**. Dies ist logisch ein Einzelupdate, technisch ein abgesicherter Ein-Projekt-Sammelauftrag.

Der Backend-Endpunkt `deployment/prepare` bleibt für Eigenziele bei `self_update_blocked`. Kein zweiter direkter Schreibpfad wurde geschaffen.

## 3. Bedienung in der Oberfläche 0.1.121

Für das eigene DRA-V2-Einzelprojekt gibt es nun neben dem weiterhin verfügbaren schreibgeschützten Quellprüfweg die ausdrücklich benannte Aktion **„DRA V2 einzeln prüfen und aktualisieren“**. Zusätzlich bleibt der bisherige Wechsel zum normalen Sammelupdate verfügbar.

Nach ausdrücklichem Auslösen der neuen Aktion geschieht ausschließlich Folgendes:

1. Der Frontend-Code prüft, dass das gewählte Projekt tatsächlich das DRA-V2-Eigenrepository ist, aktiv ist, HA verbunden ist und Python-/Oberflächenversion übereinstimmen.
2. Ein bereits `inspecting_sources`, `preparing`, `prepared`, `queued` oder `running` befindlicher HA-Sammelauftrag wird **nicht überschrieben**; ebenso unterbindet eine ausstehende gemeinsame Neustartvormerkung den neuen Weg.
3. Die lokale Durchlaufauswahl wird auf **exakt ein Projekt** gesetzt: DRA V2. Weder DRA V1 noch Gewitterradar, WeatherRouter oder ein anderes ursprünglich vorausgewähltes Projekt werden automatisch mitgenommen.
4. Das bisherige `batch/prepare` wird einmal aufgerufen. Das ist **nur Quell-/Commit-/Versions-/Zielprüfung**, keine Installation.
5. Bei erfolgreicher HA-Vorbereitung folgt dieselbe bestehende verbindliche Prüfübersicht wie beim mehrteiligen Sammelupdate. **Erst** die separate Prüfübersichts-Checkbox, die erneute Zustimmung mit vollständigem Digest und der bereits vorhandene `batch/start`-Serverendpunkt können einen Installationslauf auslösen.
6. Der anschließende tatsächliche HA-Neustart wird ebenfalls nicht automatisch durch die neue Oberfläche ausgelöst.

Auch die große Aktionsschaltfläche nach einer positiv geprüften eigenen Einzelquellvorschau führt nun zu diesem geschützten Sammelmechanismus anstatt zum verbotenen direkten Selbstinstallationspfad.

**Keine gefährliche Abkürzung:** Der Benutzer kann weiterhin jede vorbereitete Selbstaktualisierung ohne Dateischreibvorgang schließen oder verwerfen.

## 4. Quellenprüfung bei gleichzeitigem Sammelauftrag

Die bestehende schreibgeschützte Einzelprojektvorschau bleibt zulässig, sobald der HA-Quellenpfad frei ist. Die Oberfläche zeigt nun bei eigenem DRA-V2-Projekt vor einem Start ausdrücklich an, wenn ein `inspecting_sources`, `preparing`, `prepared`, `queued` oder `running` befindlicher HA-Sammelauftrag existiert. Dabei wird **kein zweiter Quellauftrag** gestartet und die bestehende HA-Vorbereitung nicht durch einen neuen Auftrag ersetzt.

Eine nicht abgeschlossene Quelle darf nicht als „Aktuell“ oder erfolgreich geprüft gelten; Quellprüfung und tatsächliche Installation bleiben getrennte Sicherheitsgrenzen.

## 5. Implementierung und Regressionstests

**Geänderte Dateien:**

- `custom_components/deploy_relay_v2_dev/frontend/lab.js`: eigenständige Ein-Projekt-Aktion und nur ein Repository umfassende Übergabe an die bestehende HA-Batch-Vorbereitung, explizite Status-/Konflikthinweise, kein neuer Schreibpfad;
- `custom_components/deploy_relay_v2_dev/manifest.json`, `const.py`: Version `0.1.121`;
- `tests/test_v2_countdown.js`: Test, dass der Selbstweg nur DRA V2 auswählt und **nur** die Vorbereitung aufruft; Test, dass ein bereits vorbereitetes HA-Sammelupdate nicht verändert wird; Test, dass während einer Sammelquellprüfung keine konkurrierende Eigenvorschau gestartet wird;
- `tests/test_v2_batch_run_selection_contract.py`: Vertragsprüfung der unveränderten Backend-Endpunkte, der Selbstupdatesperre des direkten Endpunkts, der 1–8-Projekt-Auswahl, der Identitäts- und Neustartpflicht sowie der `review_digest`-/Bestätigungskopplung;
- `tests/test_v2_batch_installation.py`: zusätzlicher **serverseitiger Ein-Projekt-Selbstupdate-Test** mit exakter Ziel- und Commitprüfung. Ohne ausdrückliche Zustimmung oder mit falschem Digest wird die Installation verweigert. Ein simulierter erfolgreicher Engine-Durchlauf wird genau einmal als DRA-V2-Auftrag verzeichnet und ein HA-Neustart wird vorgemerkt. Dieser Test verändert keine echte HA-Installation.

**Wichtige Commits:**

- `f0fc406884e6739e42037afdd060407235356d9d` – Einzel-Selbstupdate-Aktion;
- `5dd8f735e67581d58cabfed74dee29da267a7ed8` – Frontend-Einzelprojekt- und Konflikttest;
- `64c0316728fc8bbb2c52182da954b40e12949b5f` – Backend-/Sicherheitsvertrag geschützt;
- `f8a58ab5fed2d55c46b7e09e1ad80a4c9883a253` – Quellenprüfkonflikt verständlich angezeigt;
- `fd5eab037bd2c30c455e9f51e949d087a9a88abd` – Quellprüfkonflikt mit JS-Verhaltenstest;
- `0ea12702c5e689f70e52308e8dacea1cd39c6b68` – zusätzlicher positiver und negativer serverseitiger Selbstupdate-Vertragstest.

**GitHub Actions `39582019041`: vollständig abgeschlossen, `SUCCESS`.** Die frühere erfolgreiche Sammelinstallation auf den Nutzerscreenshots betrifft eine andere, bereits tatsächlich installierte Version und ist **kein** Realnachweis für die neue 0.1.121-Funktion.

## 6. Ausstehender Home-Assistant-DEV-Realtest

0.1.121 wurde im Rahmen dieser Entwicklungsarbeit **nicht** auf Home Assistant installiert. **Kein Selbstupdate und kein HA-Neustart wurden ausgeführt oder freigegeben.**

Der nächste kontrollierte Test erfolgt ausschließlich nach gesonderter Entscheidung des Nutzers:

1. Den aktuell laufenden oder vorbereiteten HA-Sammelauftrag zuerst abschließen beziehungsweise ausdrücklich verwerfen; keine bestehende Zustimmung stillschweigend verlieren.
2. Den CI-geprüften DRA-V2-0.1.121-Stand gegebenenfalls kontrolliert über den bekannten DRA-V1-Weg installieren; Python-/Frontend-Version vergleichen.
3. Das DRA-V2-Einzelprojekt und die gewünschte Quelle prüfen, wenn der HA-Scanpfad frei ist; bei einem Quellenfehler die tatsächliche HA-Quellendiagnose auswerten statt „erfolgreich“ zu behaupten.
4. **„DRA V2 einzeln prüfen und aktualisieren“** auslösen. Nachweisen, dass im vorbereiteten Auftrag **nur DRA V2** mit einem festen 40-stelligen Commit, korrekt erkanntem Versionspaar, dem verifizierten Ziel und `home_assistant_restart` steht.
5. Die HA-Vorbereitung auf Notebook und Smartphone kontrollieren. Ohne Prüfübersichtsbestätigung darf keine Installation stattfinden.
6. Erst anschließend und **separat ausdrücklich freigegeben** die reale Ein-Projekt-Eigeninstallation samt Sicherung, Auftragsabschluss, Neustartvormerkung, Neustart und Wiederanmeldung/Versionsprüfung durchführen.

Die eigentliche HA-Realabnahme steht aus; **GitHub-CI ist keine HA-Realabnahme**. DRA V1, Gewitterradar und WeatherRouter bleiben unverändert.

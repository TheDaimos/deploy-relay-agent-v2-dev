# DRA V2 0.1.120 DEV – Eigenprojekt-Vorschau bei 1/4 korrigieren, Eigenupdate-Schutz erhalten

**Datum:** 21.10.2026  
**Repository:** `TheDaimos/deploy-relay-agent-v2-dev` (privat)  
**Entwicklungszweig:** ausschließlich `feature/v2-10-inventory-operation-contract`  
**Auf HA durch den Nutzer gezeigter Ausgangsstand:** 0.1.118 DEV (Python-Laufzeit und Oberfläche übereinstimmend)  
**Entwicklungsstand im Repository vor dem Auftrag:** 0.1.119 DEV  
**Neuer DEV-Testkandidat:** 0.1.120 DEV  
**Letzter Programm-/Testcommit:** `b2688427252c185c41c9015d2ee0d90f028e438a`  
**GitHub Actions:** `39573538679` – `completed / SUCCESS` (auf exakt diesem Programm-/Testcommit)

## 1. Befund aus dem HA-Screenshot

Die Oberfläche steht auf `DRA V2 DEV – Nur Testlabor` als **Einzelprojekt**, ausgewählter Ref `feature/v2-10-inventory-operation-contract`. Die große Schaltfläche zeigt `1/4 · Vorschau berechnen`. Die Statuszeile meldet `Quellprüfung konnte nicht abgeschlossen werden · Auftrag`. Die sichere Quelle wurde nicht bestätigt und keine Installation vorbereitet.

Der Screenshot belegt **keinen** neuen fehlgeschlagenen Schreibauftrag, keinen fehlgeschlagenen Sammellauf und keinen echten Selbstupdateversuch. Der untersuchte Pfad ist der **HA-eigene, schreibgeschützte Einzelquell-Leseauftrag**. Die konkrete HA-Fehlerursache der Aufnahme wurde mangels zugehöriger Diagnoseereignisse nicht als Realtest ausgelesen; im Quellcode wurde jedoch ein eigenständiger, deterministischer Fehler dieses Ablaufs nachgewiesen.

## 2. Reproduzierbarer Fehler im Quellvertrag

`remote_source.inspect_public_repository()` erlaubt für das eigene Repository ausdrücklich eine `readonly_self`-Vorschau und setzt `self_preview_readonly=True`. Danach erzeugt `websocket_api._inspect_source_preview()` unter `target_claims` den bewusst **nicht installierbaren** Sicherheitsstatus für dieses eigene Ziel.

Die vorherige Sonderbehandlung enthielt nur:
- `installation_enabled=False`
- `exclusive_ownership_verified=False`
- `handover_required=True`
- `self_target_protected=True`

Die nachgelagerte serverseitige Prüfung in `source_preview_jobs.SourcePreviewJobs.runner()` verlangt jedoch **zusätzlich** zwingend `cross_process_lock_verified is False` und `backup_verified is False`. Die beiden fehlenden Schlüssel lieferten `None` statt `False`, wodurch selbst eine fachlich erfolgreiche Vorschau zu `untrusted source result`, anschließend generisch `source_unavailable` und `failed` wurde. Die Oberfläche zeigte folglich `Quellprüfung konnte nicht abgeschlossen werden`.

**Gezielte Korrektur:** Die Sonderbehandlung erhält jetzt ausdrücklich auch
`cross_process_lock_verified=False` und `backup_verified=False`. Es wird **keine** Schutzprüfung abgeschaltet und **kein** Sicherheitsnachweis fälschlich als erbracht markiert. Die Angaben bleiben explizit negativ, damit der Leseauftrag angenommen werden kann, ohne eine schreibende Installation zu gestatten.

## 3. Separater Bedienfehler – Eigeninstallation im Einzelprojektmodus

Die API `deploy_relay_v2_dev/deployment/prepare` lehnt DRA-Eigenprojekte bewusst mit `self_update_blocked` ab. Im bisherigen Einzelprojektmodus konnte die Oberfläche nach einer erfolgreichen Lesekontrolle dennoch den nächsten Schritt `2/4 · Installation vorbereiten` anbieten, der diese Schutzsperre zwangsläufig erreichen würde. Die Blockierung als solche ist richtig, die sichtbare Benutzerführung war falsch.

Neue Benutzerführung für das eigene DRA-V2-Projekt:

1. Die vorhandene `1/4`-Vorschau darf weiter **schreibgeschützt** die Quelle prüfen.
2. Ein direkt sichtbarer Hinweis erläutert, dass Eigeninstallationen im Einzelprojektmodus nicht möglich sind.
3. Eine eindeutige Schaltfläche **„Zum Sammelupdate wechseln“** führt in den bereits vorhandenen Sammelmodus.
4. Nach positiver Einzelquellprüfung zeigt die große Aktionsschaltfläche **„2/4 · Eigenaktualisierung über Sammelupdate“** und führt ebenfalls ausschließlich zur Sammelauswahl, statt eine verbotene Einzelvorbereitung auszulösen.
5. Im Sammelmodus wird DRA V2 weiterhin **nicht automatisch vorausgewählt**. Die ausdrückliche Entscheidung, DRA V2 in den Durchlauf einzubeziehen, bleibt beim Nutzer; die serverseitige Planung schreibt DRA V2 zuletzt.
6. Dieser Wechsel startet **keine** Installation, keine Sammelvorbereitung und keinen Neustart.

Die `self_update_blocked`-Sperre des WebSocket-Installationsendpunkts bleibt unverändert. Einmalige Bestätigung, exakter Commit, `review_digest`, Geräteinhaberprüfung, Sicherung, Rückfall und Neustartsteuerung werden nicht verändert.

## 4. Code, Version und Prüfungen

**Änderungen ausschließlich im erlaubten DRA-V2-Zweig:**

| Gegenstand | Änderungszweck |
|---|---|
| `custom_components/deploy_relay_v2_dev/websocket_api.py` | Zwei zuvor fehlende, explizit negative Schutzfelder in der Read-only-Eigenvorschau |
| `custom_components/deploy_relay_v2_dev/frontend/lab.js` | Eindeutiger Eigenupdate-Hinweis; sichere Navigation statt verbotener Einzelinstallation |
| `const.py`, `manifest.json` und Frontend-Version | Einheiltlich auf `0.1.120 DEV` |
| `tests/test_v2_source_preview_jobs.py` | Positivtest: vollständige Read-only-Eigenvorschau endet mit `success` und ohne Installationsrecht; Negativtest: fehlende Sicherheitsfelder werden weiter abgewiesen |
| `tests/test_v2_countdown.js` | Frontend-Verhaltenstest für Quellenprüfung und ausdrücklich abgewählten DRA-V2-Eigeninstallationsanteil beim Wechsel in den Sammelmodus |
| `tests/test_v2_batch_run_selection_contract.py` | Prüft die beiden falschen Schutzwerte sowie fortgeltende API-Sperre und Benutzerführung |

**Relevante Implementierungscommits:**

- `c72e0f62e7098a4abaad56e970308a90b6403293` – Read-only-Schutzvertrag
- `739e26793f429dda4491d9340d55d795f1601c45` – Benutzerführung Einzelprojekt/Sammelmodus
- `0fa98b67a74e79cb032400fe08ebc9370950583a` – positive und negative Eigenvorschau-Tests
- `bd18663c22d5cdc8dcf66a1357cebfe5e9d5b7cb` – tatsächlicher JS-Verhaltenstest
- `b2688427252c185c41c9015d2ee0d90f028e438a` – letzte Vertragsprüfung

**GitHub Actions:** Lauf **`39573538679`**, Status **completed**, Ergebnis **SUCCESS**. Ausgeführter Job **„Statische und sicherheitsbezogene Basispruefung“: SUCCESS**. Der zuvor erfolgreich geprüfte Code-/Teststand ist maßgeblich, nicht bloß der nachfolgende Dokumentationscommit.

## 5. Ausstehender echter Home-Assistant-Test

**Nicht durchgeführt:** Installation von 0.1.120 auf HA, echte Read-only-Quellprüfung der eigenen Repository-Quelle, Gerätewechsel, Installationsfreigabe und HA-Neustart.

**Kontrollierter Testplan:**

1. Den CI-grünen Stand nach ausdrücklicher Zustimmung über den bereits bewährten DRA-V1-Weg auf HA DEV installieren (falls V2-Eigenupdate weiterhin nicht verfügbar). HA-Python und Oberfläche auf **0.1.120** prüfen.
2. `DRA V2 DEV – Nur Testlabor` als Einzelprojekt auswählen. Die schreibgeschützte Vorschau starten und prüfen, ob der bisherige generische Quellenabbruch verschwindet. Ein tatsächlicher Source- oder Zugriffsfehler kann weiterhin auftreten und muss separat diagnostiziert werden.
3. Nach erfolgreicher Vorschau die **neue** Anzeige `Eigenaktualisierung über Sammelupdate` prüfen. Eine Einzelinstallation darf weiter nicht vorbereitet oder durchgeführt werden.
4. In den Sammelmodus wechseln; DRA V2 muss zunächst **abgewählt** bleiben. Danach optional bewusst für einen reinen Vorbereitungstest wählen und die Review-Tabelle sowie das Einordnen als letztes Projekt prüfen.
5. Keine tatsächliche Eigeninstallation, keine weiteren Projekte und keinen Neustart ohne getrennte Realfreigabe starten.

**GitHub-CI ist ausdrücklich keine HA-Realabnahme.** Die tatsächliche Auflösung des vom Nutzer fotografierten HA-Abbruchs ist erst nach dem Realtest bestätigt. Keine Änderungen an DRA V1, Gewitterradar oder WeatherRouter vorgenommen.

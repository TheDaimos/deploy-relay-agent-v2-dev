# DRA V2 DEV 0.1.69 – G2 privater Export-Wiederholtest

**Datum:** 11.10.2026  
**Verbindlicher Zweig:** `feature/v2-10-inventory-operation-contract`  
**Status:** DEV-Code für kontrollierten HA-Test vorbereitet und vollständig CI-geprüft: [GitHub Actions Run 38167638211](https://github.com/TheDaimos/deploy-relay-agent-v2-dev/actions/runs/38167638211) – **SUCCESS** auf Code-/Kontext-Checkpoint `b44971d124d87473e638b96fd08e82ca16f68335`. **HA-Realabnahme weiterhin offen.** Keine V2-Schreib- oder Installationsfreigabe.

## Hintergrund

Nach der HA-Realabnahme der HA-eigenen Quellaufträge, des Clientwechsels (Companion App ↔ Chrome), des Netzwechsels (WLAN → 5G/VPN) und eines **HA-Neustarts während eines laufenden Leseauftrags** bleibt G2 der Nachweis des Wiederholversands eines vorher nicht übertragenen privaten Diagnoseberichts.

Der normale Git-Export wurde bereits real und wiederholt erfolgreich nach `TheDaimos/Project-Log-And-Export` durchgeführt. Das allein beweist **nicht**, dass `retry_pending()` die im HA-Store verbliebenen Originalbytes erneut verschickt.

## Kontrollierter Test ohne Token- oder Netzstörung

Der neue **ausschließlich im V2-DEV-Featurezweig implementierte** Verwaltungsprüfmodus ist innerhalb von `Deployment → Logs` unter `G2 – Wiederholversand sicher prüfen` standardmäßig geschlossen. Der Nutzer muss erst den Prüfabschnitt öffnen, dann **„G2-Test vorbereiten“** und anschließend **„Ja, lokal zurückstellen“** wählen.

Der Backend-Vertrag:
1. Ausschließlich bestehender administrativer WebSocket-Befehl `deployment/logs/export`, ergänzt um die beiden exakt booleschen und standardmäßig **false** gesetzten Parameter `g2_prepare` und `g2_confirm`. Keine neuen öffentlichen Endpunkte oder separaten Berechtigungsstufen.
2. Bestätigung muss wahr sein; das Git-Archiv muss **exakt** das private `TheDaimos/Project-Log-And-Export` sein. Es muss eine bereinigte echte aktuelle Quellprüfung vorliegen; der serverseitige private Zugang ist unverändert eingerichtet. Bestehende Warteschlangeneinträge werden niemals ersetzt.
3. Ein lesender GitHub-Repositorycheck bestätigt das private Ziel. Danach wird der echte bereinigte Quellprüfbericht über den bestehenden Payload-Validator und die HA-Speicherfunktion **dauerhaft nur lokal** abgelegt. **Kein GitHub-PUT bei der Vorbereitung.** Der Vorgang simuliert eine Unterbrechung **vor** der eigentlichen Übertragung. Es wird weder behauptet noch vorgetäuscht, dass ein echter HTTP-Fehler aufgetreten sei.
4. Die Oberfläche zeigt ausdrücklich `nur lokal gesichert`, exportiert weder heimlich noch automatisch und schaltet auf den vorhandenen Knopf `Gespeicherten Git-Export erneut senden` um.
5. Erst dieser **zweite ausdrückliche Nutzerklick** benutzt den **bestehenden** `retry_pending()`-Pfad und sendet das exakt gespeicherte ursprüngliche Archivpaket an das konfigurierte private Repository. Eine aktuelle, neuere Diagnose wird nicht gleichzeitig übertragen.
6. Bei tatsächlichem Fehler bleibt die unveränderte Datei im HA-Store erhalten; der Benutzer kann dieselbe Schaltfläche erneut verwenden. Ein zweiter Vorbereitungsversuch während einer Warteschlange ist gesperrt.
7. Nach erfolgreicher Übertragung erlischt `pending`. Die vorhandene Antwort mit `pending_retried=true` kennzeichnet den Wiederholversand und zeigt dessen Export-ID an. Ein weiterer Export wäre wieder ein neuer, separat ausdrücklich ausgelöster Vorgang.
8. **Neustartfestigkeit korrigiert:** Besteht nach dem Neustart eine gespeicherte Warteschlange, darf der Administrator sie auch dann erneut senden, wenn die **flüchtige Quellprotokollliste leer** ist. Der Server prüft den wartenden Bericht **vor** dem Erfordernis einer aktuellen Quellprüfung; die Oberfläche lässt den Retry bei `pending=true` unabhängig von der flüchtigen Loganzahl zu. Ein völlig neuer Export ohne aktuelle Quelle bleibt dagegen gesperrt.

## Sicherheitsgrenzen

- DRA V2 bleibt `LOCKED`: keine Projektschreibrechte, Installation, Sicherung, Wiederherstellung, neue Quellprüfung oder HA-Neustart durch diesen Test.
- Kein Passwort-/Tokenwechsel, kein absichtliches Sperren von DNS, Internet, GitHub oder Home Assistant, kein GitHub-Zielwechsel.
- GitHub-Contents-API: create-only, ohne fremden SHA und ohne Überschreibfunktion. Die Schnittstelle kann bereits existierende Dateien nicht ersetzen. Die GitHub-API dokumentiert `201 Created`, `409 Conflict` und `422 Validation failed` sowie die nötigen privaten Schreibrechte: https://docs.github.com/en/rest/repos/contents.
- Die im DEV-Backend erneut abzulegende Diagnose enthält keinerlei Git-Token. Es wird nur das explizit freigegebene private Archiv mit echten Exporten beschrieben; in dieses öffentliche Quellrepository gelangen nur bereinigte Tests und ein Ergebnisprotokoll ohne Rohdiagnose.
- Reale Netzwerkfehler sind hier **nicht** künstlich reproduziert; stattdessen wird exakt derselbe persistierte Warteschlangen-/Wiederholpfad vor dem HTTP-PUT durchlaufen. Den HTTP-Fehlervertrag decken weiterhin die separaten isolierten Tests (u.a. HTTP 503, 403, 422, ungültige Commitbestätigung) ab.
- DRA V1, V2 `main`/PUB, WeatherRouter, das private Exportarchiv sowie Draft-PR #2 bleiben unangetastet. PR #2 nicht zusammenführen.

## Automatisierte Abnahme

Zu prüfen sind:
- Getrennte Bestätigung und ausschließlich genehmigtes privates Ziel.
- Beim Vorbereiten **kein** GitHub-PUT, aber genau ein valider dauerhafter Bericht mit eindeutiger Export-ID.
- Nach simuliertem HA-Integrationsneustart unveränderte Rohbytes, Ziel, Pfad und Export-ID.
- Beim Retry eine einzige create-only GitHub-PUT-Anfrage mit Byte-für-Byte identischem Payload, danach leere Warteschlange.
- Doppelte Vorbereitung bei vorhandener Warteschlange, fehlendes privates Ziel/Token und ungültige Berechtigung stoppen sicher.
- Retry über bestehende UI/API auch **nach HA-Neustart ohne flüchtige Logs**.
- Bestehende Python-/JavaScript-Tests, 35 administrative Schnittstellen, Versionssynchronität und keine veröffentlichten CI-Artefakte.

## HA-Realabnahme – möglichst wenig Bedienaufwand

Nach grüner CI erfolgt die **Installation von DEV 0.1.69 über DRA V1 einschließlich üblichem HA-Neustart ausschließlich durch den Betreiber**. Dann:

1. Einmal eine normale, schreibgeschützte Gewitterradar-Quellprüfung unter V2 ausführen, damit eine echte aktuelle bereinigte Diagnose vorliegt.
2. `Deployment → Logs → G2 – Wiederholversand sicher prüfen` öffnen. **G2-Test vorbereiten** und **Ja, lokal zurückstellen** auslösen. Erwartet: Erfolgsmeldung `nur lokal gesichert`, Kennung sichtbar, kein neuer Export im privaten Archiv, oberer Knopf jetzt `Gespeicherten Git-Export erneut senden`.
3. Diesen Knopf **einmal ausdrücklich** drücken. Erwartet: `Zuvor gesicherten Export erneut nach Git übertragen`, gleiche Export-ID, `pending=false`; exakt **eine** neue Datei im privaten Archiv. Erst dann ist G2-40 in HA abgenommen.
4. Optional im eigenen separaten Durchgang: HA nach Schritt 2 neu starten, dann ohne neue Quellprüfung gespeicherten Export erneut senden. Dieses zusätzliche Szenario ist durch isolierte Tests abgedeckt, aber erst nach gesonderter Freigabe als HA-real zu bezeichnen. **Für die Erstabnahme kein zweiter Neustart erforderlich.**

Je Chatantwort **höchstens ein konkreter HA-Bedienschritt**, keine Screenshots bei normalem Erfolg nötig, kein zweiter Test ohne konkrete Notwendigkeit.

**C.K. – Eine Idee weiter gedacht.**

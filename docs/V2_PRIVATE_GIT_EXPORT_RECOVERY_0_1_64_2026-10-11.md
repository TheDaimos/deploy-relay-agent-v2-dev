# DRA V2 DEV 0.1.64 – privater Diagnoseexport: Übertragungsprüfung und Warteschlange

**Stand:** 11.10.2026  
**Entwicklungszweig:** `feature/v2-10-inventory-operation-contract`  
**Status:** Sicherheitserhaltende Fehlerbehebung im nur lesenden DEV-Testlabor; HA-Realtest der Korrektur noch offen.

## Beobachteter Fehler

Auf dem Android-HA-System wurde nach einer erfolgreichen schreibgeschützten Gewitterradar-Prüfung in DEV 0.1.63 beim Druck auf **Deployment → Logs → Export nach Git** die Fehlermeldung „Privater Export fehlgeschlagen. JSON-Download bleibt verfügbar“ angezeigt. Der vom Betreiber separat bereitgestellte lokale JSON-Diagnosebericht aus **DEV 0.1.63** zeigt die erfolgreich abgeschlossene Quellprüfung (`status=success`, `reason=none`, `sources_verified=true`, `installation_enabled=false`) und intakte anonyme Projekt-/Prüfkennungen. Diese Diagnose ist **keine** Bestätigung einer erfolgreichen Übertragung.

Der letzte im privaten `TheDaimos/Project-Log-And-Export` tatsächlich gelesene DRA-V2-Diagnoseexport stammte noch aus DEV 0.1.61. **Der vollständige lokale Bericht wird nicht in dieses öffentliche Quellrepository kopiert.**

Im Code wurden zwei konkrete Mängel festgestellt:
1. `MeasurementGitExport._ensure_private_repository()` überprüfte die zwingend erforderliche private GitHub-Repositorysichtbarkeit mit einem einzigen `await response.content.read(8193)`. Wie beim bereits behobenen Quellprüfdefekt garantiert `aiohttp.StreamReader.read(n)` kein vollständiges Lesen bis EOF. Eine normale, fragmentierte GitHub-JSON-Antwort kann so fälschlich als fehlgeschlagene Prüfung erscheinen.
2. Fehlgeschlagene Schreibversuche werden korrekt als **unveränderlicher vorbereiteter Bericht** mit festem Ziel und Exportkennung in der HA-Store-Warteschlange aufbewahrt. Die Deployment-Logs-Schaltfläche rief jedoch stets `export(...)` auf. Bei vorhandener Warteschlange weist der Backend-Vertrag jeden neuen Export aus Sicherheitsgründen ab; dadurch war ausgerechnet über diese Bedienoberfläche kein erneuter Versuch möglich.

**Nicht belegt:** Ob bei der konkreten ersten HA-Fehlübertragung wirklich ein fragmentiertes GitHub-Repository-Metadatenpaket, eine Berechtigungsänderung, ein Netzwerkfehler oder ein GitHub-Antwortfehler vorlag. Der neue Test reproduziert die verifizierte Code-Schwäche, nicht die unbekannten tatsächlichen Netzwerkbytes.

## Korrektur und Sicherheitsvertrag

- **Vollständiger begrenzter Abruf:** `_ensure_private_repository` liest nun in 2-KiB-Portionen bis zum echten EOF, mit weiterhin unveränderter harter Grenze von **8.192 Byte** für die Repositoryantwort. Zu große, ungültige, nicht private, umgeleitete oder ohne Berechtigung gelesene Antworten bleiben **fail-closed**; keine Übertragung, bevor `full_name`, `private=true` und `default_branch` geprüft sind.
- **Warteschlange erhalten:** Wenn ein vorbereiteter Bericht aus einem vorigen Fehlversuch vorliegt, löst `deployment/logs/export` **zunächst nur** `retry_pending()` aus. Dabei bleiben Originalbytes, Ziel, Pfad, Zeitstempel und Export-ID unangetastet. Auf diesem Aufruf wird **noch nicht** zusätzlich der jüngste Bericht versendet. Der Benutzer kann die aktuelle Diagnose nach erfolgreichem Versand des zuvor gespeicherten Berichts mit einem zweiten Druck exportieren.
- **Ehrliche Bestätigung:** Die WebSocket-Antwort enthält `pending_retried=true|false`; die Oberfläche meldet ausdrücklich, ob sie gerade den vorherigen ausstehenden Bericht oder die neue Diagnose nach Git übertragen hat. Bei Fehlschlag wird erklärt, dass ein vorbereiteter Bericht weiter lokal erhalten bleiben kann; JSON-Download/ Zwischenablage bleiben unabhängig verfügbar.
- **Privater Zielschutz:** Die Deployment-Logs dürfen unverändert ausschließlich nach `TheDaimos/Project-Log-And-Export` übertragen werden. Kein öffentlicher Ersatzupload, keine Ablage echter HA-Diagnosen im V2-Code-Repository, keine Token-Freigabe, keine Änderung fremder Repositorys.
- **Nicht geändert:** GitHub-Contents-API verwendet weiterhin ausschließlich create-only `PUT` mit dem zuvor festgestellten privaten Standardzweig; keine Überschreibung, kein automatischer Retry fremder Ziele, keine Mutation von HA-Projektdateien, Installation, Sicherung, Wiederherstellung oder Neustart.

## Prüfungen

Die automatisierten isolierten Tests decken ab:
- Eine sehr fragmentierte, **gültige** private GitHub-Repositoryantwort mit vielen `read()`-Teilstücken wird bis EOF gesammelt und als privat bestätigt.
- Eine Antwort über 8.192 Byte wird auch bei fehlenden Vollständigkeitsgarantien sicher abgewiesen und nicht hochgeladen.
- Nach einem simulierten HTTP-Fehlupload ist exakt **der ursprüngliche** Bericht mit derselben Exportkennung und demselben Ziel erneut übertragbar.
- Zusätzlicher echter Diagnosevertrags-Mock mit sicher synthetischem Gewitterradar-Quellprüfbericht und serverseitig ausschließlich privat ergänztem Repositorynamen.
- Kontrollvertrag für die Deployment-Logs-Schaltfläche: erst wartenden Bericht senden; danach neue Diagnose exportieren; keine irreführende Erfolgsmeldung für falsche Datei.

## Nächster HA-Test – ein Schritt je Rückmeldung

Betreiber aktualisiert **DRA V2 DEV 0.1.64 ausschließlich manuell über DRA V1**. Anschließend Deployment → Logs öffnen und **„Gespeicherten Git-Export erneut senden“** wählen, sofern der Server einen wartenden Export meldet, andernfalls „Export nach Git“.

Bei einer erfolgreichen Rückmeldung mit `pending_retried=true` ausdrücklich beachten: Zuerst wurde die ältere zurückgestellte Datei übertragen. Ein zweiter ausdrücklich ausgelöster Export ist für das letzte Quellprüfprotokoll nötig. Bei erneutem Fehler: lokale JSON-Diagnose herunterladen, Sichtmeldung dokumentieren und lediglich die admin-geschützten Exportstatusfelder (konfiguriert, privat, wartend; niemals vollständigen Token) auswerten.

**Abnahmekriterium:** Im privaten Zentralarchiv erscheint genau die bestätigte Datei mit derselben Exportkennung; `pending` ist danach `false`. HA-Quellprüfung aus 0.1.63 bleibt als bestanden erfasst, daraus folgt keine Installationsfreigabe. Draft-PR #2 bleibt Entwurf und unzusammengeführt.

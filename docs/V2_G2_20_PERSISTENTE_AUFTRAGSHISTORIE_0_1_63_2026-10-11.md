# DRA V2 DEV 0.1.63 – G2-20: dauerhafte Leseauftragshistorie und Verbindungswiederherstellung

**Datum:** 11.10.2026  
**Ausschließlicher Entwicklungszweig:** `feature/v2-10-inventory-operation-contract`  
**Status:** Implementiert; vollständige GitHub-CI mit isolierten Python- und JavaScript-Prüfungen. **HA-Realabnahme 0.1.62/0.1.63 noch offen.**

## Hintergrund

Die Gewitterradar-Quellvorschau wurde in Version 0.1.61 in Home Assistant tatsächlich schreibgeschützt abgenommen. G2-10 in 0.1.62 hat danach HA-eigene, browserunabhängige Leseaufträge eingeführt und statisch getestet. **Eine echte Android-/WLAN-Realabnahme von 0.1.62 wurde nicht berichtet.** G2-20 soll die Nachvollziehbarkeit nach dem Neustart verbessern, ohne die nie bewiesene automatische Wiederaufnahme von Arbeiten zu behaupten.

## Verbindlicher Zustand nach G2-20

### 1. Persistente, strikt begrenzte Historie

Neue Datei `source_job_history.py`, gespeichert ausschließlich unter dem eigenen HA-Storage-Schlüssel `deploy_relay_v2_dev.source_job_history` (Store Version 1).

- **Maximal acht Datensätze**, maximal **6.000 Byte** JSON insgesamt.
- Speicherung ausschließlich von 128-Bit-Auftragskennung, festem Zustand (wartend/erfolgreich/fehlgeschlagen/unterbrochen), UTC-Zeitpunkten und einer erlaubten Fehlermeldungskategorie.
- Für jeden Datensatz fest und unveränderlich: `installation_enabled=false`, `resume_allowed=false`, `source_preview_saved=false`.
- **Keine** Projektnamen, Repositoryadressen, Git-Referenzen, Commit-IDs, lokalen Pfade, installierten Dateien, Unterschiede der Dateiinhalte, Tokens, komplette JSON-Quellberichte oder Rohfehlermeldungen in dieser persistierten Historie.
- Schema wird bei jedem Start vollständig validiert. Unleserliche oder manipulierte Datensätze werden **nicht gelöscht oder überschrieben**; stattdessen verweigert die DEV-Integration kontrolliert ihre Initialisierung, bis die Ursache geprüft ist.
- Beim Laden nach HA-Neustart werden vorher als `queued` gespeicherte, niemals freigegebene Aufträge **ausschließlich als `interrupted`** gekennzeichnet und dieser Zustand dauerhaft gesichert. **Keine automatische Wiederholung einer GitHub-Prüfung.**
- Historischer `success` bedeutet lediglich, dass eine alte Prüfung damals endete. Ein alter Prüferfolg ist **nie** als aktuelle Quellvorschau im Browser verwendbar oder als Installationsfreigabe akzeptierbar.

### 2. Integration in serverseitige Leseaufträge

`source_preview_jobs.py` speichert den minimalen Queued-Datensatz **vor dem Start** der HA-eigenen Aufgabe. Schlägt die Ablage fehl, wird die Aufgabe überhaupt nicht gestartet. Beim echten Abschluss wird der Terminalzustand gespeichert, bevor ein Erfolg als solcher gemeldet wird. Bei Fehler, Abbruch, Entladen oder ausgefallenem Speicher kann niemals aus einem unbestätigten Ergebnis ein erfolgreicher, schreibberechtigter Auftrag werden.

Die bestehende ConfigEntry-gebundene Aufgabe wird weiterhin beim Entladen gestoppt. Die Historie enthält keine fortsetzbare Auftragsnutzlast; es erfolgt keine Weiterführung über einen HA-Neustart hinweg.

### 3. Administrative Statusschnittstelle

Neuer, ausschließlich für Administratoren bereitstehender schreibgeschützter WebSocket-Befehl:

`deploy_relay_v2_dev/projects/source_job/history`

Antwortvertrag `dra-v2-source-job-history-result.v1`: die maximal acht bereinigten Einträge in absteigender Reihenfolge und die festen Sperrmerkmale `installation_enabled=false`, `resume_allowed=false`, `source_preview_saved=false`.

Die bereits vorhandene Start-/Status-Schnittstelle bleibt für aktive Leseaufträge und wiederverwendbare Ergebnisse **nur innerhalb derselben HA-Laufzeit** zuständig. Die neue Historie ersetzt diese Laufzeitberichte nicht.

### 4. Mobile Oberfläche / Wiederverbindung

Der bestehende kleine goldene **Logs**-Bereich bekommt eine getrennt betitelte **serverseitige Auftragshistorie**, mit kurzer Auftragskennung, Zustand und Zeitstempel. Die Anzeige enthält weder vollständige Git-Repositories noch private Quellnamen. Auch ein historisch erfolgreicher Auftrag heißt ausdrücklich **„Damals erfolgreich“**, nicht „Quelle jetzt geprüft“.

Bei WLAN-/Browserunterbrechungen wird die Statusabfrage schrittweise von **1,2 Sekunden bis maximal 10 Sekunden** verlangsamt; die servereigene HA-Aufgabe wird dabei nicht beendet. Nach erfolgreicher Verbindung gilt wieder der kurze Standardabstand. Meldet HA nach dem Neustart keinen aktiven Auftrag mehr, wird die alte Vorschau verworfen und nur der historische Zustand angezeigt – eine **neue** Quellprüfung ist notwendig.

Der Verlauf wird bewusst erst beim Öffnen von Logs oder beim Verschwinden eines zuvor bekannten Auftrags abgefragt, nicht bei jeder gewöhnlichen Oberflächenaktualisierung.

## Nachträgliche HA-Realabnahme – 11.10.2026

**G2-Neustart-Unterbrechung: bestanden (V2 DEV 0.1.68).**

Der Betreiber startete den 60-Sekunden-G2-Leseauftrag für Gewitterradar und führte noch während der Laufzeit einen regulären Neustart der HA-DEV-Instanz durch.

Nach dem Neustart zeigt die mobile Auftragshistorie den entsprechenden Auftrag als **Unterbrochen** und frühere erfolgreiche Aufträge weiterhin als **Damals erfolgreich**. Die flüchtige Quellprotokollanzeige ist leer und fordert eine neue Vorschau. Dies entspricht dem vorgesehenen Verhalten: kein automatischer Neustart der Quellprüfung, kein Wiederverwenden historischer Erfolge als neue Installationsfreigabe.

**Abnahmeumfang:** Laufende Leseprüfung beim HA-Neustart, persistenter Unterbrechungsstatus und unveränderte historische Erfolge. Der separate Test des ausdrücklich wiederholten privaten Export-Warteschlangeneintrags (`retry_pending`) ist noch offen. Echte Exportdaten verbleiben ausschließlich im privaten Zentralarchiv. Kein Codeänderungs- oder Neustartbedarf für diese Abnahme.

## Sicherheit und Abgrenzung

Unverändert und nicht freigegeben: V1/V2-Übergabe- oder Zielbesitznachweis, globale Schreibsperre, V2-eigene echte Sicherungen, Integritätswiederherstellung, Einzelinstallation, Sammelinstallation, Home-Assistant-Neustart und Selbstupdate. Sämtliche Änderungen liegen nur im genannten DEV-Featurezweig. **Keine Änderungen an V1 DEV/PUB, V2 PUB/main, WeatherRouter oder dem privaten zentralen Diagnosearchiv `TheDaimos/Project-Log-And-Export`.** PR #2 bleibt offen, Entwurf, nicht zusammengeführt.

Der Export echter Home-Assistant-Protokolle erfolgt weiterhin ausschließlich manuell ins freigegebene private Archiv.

## Automatisierte Prüfungen

- `tests/test_v2_source_job_history.py`: Wiederanlauf nach Neustart führt zu `interrupted` ohne Wiederaufnahme; historischer Erfolg darf keine Vorschau freigeben; Speicherung ausschließlich der erlaubten Felder; manipulierter Datensatz wird abgewiesen; fehlgeschlagene Schreiboperation wird sicher zurückgerollt; Höchstgrenzen; keine Netzwerkaufgabe bei ausgefallenem Storage; echte SourcePreviewJobs-Anbindung speichert ausschließlich Metadaten.
- `tests/test_v2_source_preview_jobs.py`: weiterhin geprüft – nur ein aktiver Job, doppelte Anforderung, Fehler, geschützte Quelle, Entladen.
- `tests/test_v2_countdown.js`: wiedereröffnete Anzeige, zurückhaltende Wiederholversuche bei Verbindungsabbruch, Historienanzeige ohne aktuelle Quellfreigabe.
- Die CI prüft weiterhin sämtliche **35 administrativen WebSocket-Befehle** sowie den expliziten 27-Dateien-Modulhaushalt.

**Nächste reale HA-Abnahme:** Der Nutzer installiert DRA V2 DEV **0.1.63** selbst und ausschließlich über DRA V1. Anschließend einmal eine Gewitterradar-Quellvorschau anstoßen und überprüfen, dass Auftrag/Kennung, Ergebnis und die neue Historie erscheinen. **Kein** zusätzlich veranlasster Neustart für diesen Grundtest. Eine getrennte spätere Realabnahme kann das tatsächliche Wiederöffnen des Android-Browsers und eine kontrollierte HA-DEV-Neustart-Situation abdecken, ohne durch Chat-Software eigenständig HA zu verändern.

Referenz zum korrekten Home-Assistant-Entladen: https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-entry-unloading/

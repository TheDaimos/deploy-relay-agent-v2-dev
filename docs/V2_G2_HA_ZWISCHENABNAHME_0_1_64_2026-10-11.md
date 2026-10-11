# DRA V2 DEV 0.1.64 – G2: bereinigte HA-Zwischenabnahme

**Datum:** 11.10.2026  
**Alleiniger Arbeitszweig:** `feature/v2-10-inventory-operation-contract`  
**Status:** Teilabnahme der schreibgeschützten Quellprüfung und des privaten Git-Exports. **G2 insgesamt noch offen.**

## Verifizierte Ergebnisse

- Das Installations-/Versionsvergleichswerkzeug DRA V1 zeigte für V2 DEV die korrekte Projektquelle und den Featurezweig, Git- und Lokalversion jeweils **0.1.64**, sämtliche **27 verwalteten Dateien unverändert** und vollständige SHA-256-Vergleichsergebnisse. Daher bestand kein neues Installationsbedürfnis. Die vorher vermutete falsche Quellreferenz erwies sich **nicht** als Ursache.
- Die separat im ausschließlich privaten Zentralarchiv eingetroffenen, realen V2-Diagnosen wiesen die **aktive V2-DEV-Laufzeitversion 0.1.64** nach.
- Eine in HA tatsächlich ausgeführte **schreibgeschützte Gewitterradar-Quellprüfung** unter 0.1.64 endete erfolgreich. Alle acht vorgesehenen Prüfphasen bis einschließlich berechneter Zielkollision wurden erreicht, Ergebnis `success`, keine Fehlerkategorie, Quelle verifiziert. **Keine Installationsfreigabe.**
- Der zugehörige, vom Nutzer ausdrücklich angestoßene **private Git-Diagnoseexport** wurde im vorgeschriebenen privaten Archiv nachgewiesen. Damit ist der reguläre Exportweg unter 0.1.64 real bestätigt.
- Zwei weitere real ausgeführte, aber **erwartbar abgewiesene** Quellprüfungen unter 0.1.64 zeigten die bestehenden Schutzgrenzen: DRA V1 als geschütztes Ziel und V2-DEV-Standardzweig ohne Bereitstellungsmanifest. Diese Prüfungen sind **keine** negativen Befunde zur zuvor erfolgreich geprüften Gewitterradar-Quelle.

## Was ausdrücklich NICHT bewiesen wurde

- Dass der **vorher gespeicherte fehlgeschlagene Export** tatsächlich über `retry_pending()` mit derselben Exportkennung übertragen wurde. Neu hochgeladene Berichte beweisen nur den normalen Exportweg; der spezielle Wiederholpfad bleibt separat offen.
- Dass ein **während der Quellprüfung** unterbrochener Android-Browser bzw. WLAN-Wechsel die HA-eigene Aufgabe überlebt und nach der Rückkehr dieselbe Auftragskennung/den terminalen Zustand anzeigt.
- Die **persistente Auftragshistorie** nach einem kontrollierten HA-Neustart und die Markierung eines dann unterbrochenen Auftrags. Kein Neustart wurde angefordert oder ausgeführt.
- V1/V2-exklusive Besitzsperre, reale V2-eigene Sicherung, Rückfall, schreibende Installation, Sammelinstallation oder selbstständiger HA-Neustart.

## Datenschutz und Quellenlage

Diese Datei enthält nur eine **bereinigte, manuell bewertete Abnahmezusammenfassung** ohne Diagnose-JSON, aufbewahrte Rohprotokolle, Auftrags-/Exportkennungen, Zugangsdaten, private Git-Inhalte, lokale Pfade oder individuelle Geräteinformationen. Die Originalnachweise verbleiben **ausschließlich** im privaten `TheDaimos/Project-Log-And-Export`; nicht in dieses öffentliche Entwicklungsrepository kopieren. Eine öffentliche Kopie der privaten Dateien ist unzulässig.

## Nächste Abnahme in kleinen Schritten

1. In der bereits installierten V2-DEV-Version `Deployment → Logs` die **serverseitige Auftragshistorie** prüfen: Ein abgeschlossener Test erscheint als historischer Erfolg, ohne alte Vorschau oder Freigabe zu reaktivieren. Screenshot genügt; kein erneuter Git-Export nötig.
2. Einen gesonderten Android-Verbindungs-/Browserunterbrechungstest **während eines neuen laufenden schreibgeschützten Auftrags** planen. Wegen der derzeit kurzen Prüfzeiten muss die tatsächliche Unterbrechung nachgewiesen werden; bloßes Wiederöffnen nach Abschluss genügt nicht.
3. Kontrollierten HA-Neustartfall nur gesondert und durch den Betreiber freigegeben abnehmen; keinen Neustart automatisch auslösen.

**Schreibrechte für V2 bleiben gesperrt.** PR #2 bleibt OPEN/DRAFT/UNMERGED. Keine Änderungen an DRA V1, V2 PUB/main, WeatherRouter oder dem privaten Archiv.

**C.K. – Eine Idee weiter gedacht.**

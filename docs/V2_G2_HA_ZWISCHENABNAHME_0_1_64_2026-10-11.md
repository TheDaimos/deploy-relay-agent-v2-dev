# DRA V2 DEV 0.1.64 – G2: bereinigte HA-Zwischenabnahme

**Datum:** 11.10.2026  
**Alleiniger Arbeitszweig:** `feature/v2-10-inventory-operation-contract`  
**Status:** Teilabnahme der schreibgeschützten Quellprüfung, der privaten Git-Übertragung **und der sichtbaren serverseitigen Auftragshistorie im laufenden HA-System**. **G2 insgesamt noch offen.**

## Verifizierte Ergebnisse

- Das Installations-/Versionsvergleichswerkzeug DRA V1 zeigte für V2 DEV die korrekte Projektquelle und den Featurezweig, Git- und Lokalversion jeweils **0.1.64**, sämtliche **27 verwalteten Dateien unverändert** und vollständige SHA-256-Vergleichsergebnisse. Daher bestand kein neues Installationsbedürfnis. Die vorher vermutete falsche Quellreferenz erwies sich **nicht** als Ursache.
- Die separat im ausschließlich privaten Zentralarchiv eingetroffenen, realen V2-Diagnosen wiesen die **aktive V2-DEV-Laufzeitversion 0.1.64** nach.
- Eine in HA tatsächlich ausgeführte **schreibgeschützte Gewitterradar-Quellprüfung** unter 0.1.64 endete erfolgreich. Alle acht vorgesehenen Prüfphasen bis einschließlich berechneter Zielkollision wurden erreicht, Ergebnis `success`, keine Fehlerkategorie, Quelle verifiziert. **Keine Installationsfreigabe.**
- Der zugehörige, vom Nutzer ausdrücklich angestoßene **private Git-Diagnoseexport** wurde im vorgeschriebenen privaten Archiv nachgewiesen. Damit ist der reguläre Exportweg unter 0.1.64 real bestätigt.
- Zwei weitere real ausgeführte, aber **erwartbar abgewiesene** Quellprüfungen unter 0.1.64 zeigten die bestehenden Schutzgrenzen: DRA V1 als geschütztes Ziel und V2-DEV-Standardzweig ohne Bereitstellungsmanifest. Diese Prüfungen sind **keine** negativen Befunde zur zuvor erfolgreich geprüften Gewitterradar-Quelle.
- **Zusätzliche HA-Sichtabnahme (18:21 Ortszeit):** Im geöffneten Bereich `Deployment → Logs` wurde unter „Serverseitige Auftragshistorie“ der zuvor erfolgreiche Gewitterradar-Auftrag als **„Damals erfolgreich“** mit Zeitstempel dargestellt. Vorangegangene abgewiesene Quellprüfungen waren ebenfalls als **„Prüfung gescheitert“** sichtbar. Die Historie ist in der aktuellen HA-Laufzeit lesbar; der Screenshot beweist **keine** Wiederaufnahme eines alten Resultats und **keine** Speicherung über einen HA-Neustart hinweg. Schreibfreigabe blieb gesperrt.
- **Zusätzlicher unabhängiger Clienttest (18:24–18:25 Ortszeit):** Die vorangegangenen Screenshots entstanden in der Home-Assistant-Companion-App. Anschließend rief der Betreiber dieselbe HA-Instanz **direkt in einem getrennten mobilen Chrome-Browser** auf. Der Browser zeigte erneut die bisherige erfolgreiche Quellprüfung und insbesondere dieselbe gespeicherte Auftragshistorie einschließlich des zeitlich identischen, ausdrücklich als **„Damals erfolgreich“** bezeichneten letzten Auftrags und der vorherigen Fehler. Damit ist die **Anzeige einer serverseitig gespeicherten Auftragshistorie aus einem zweiten, unabhängigen Client derselben laufenden HA-Instanz** real bestätigt. Aus diesem Vergleich ergibt sich **keine** Aussage über eine Unterbrechung *während* eines laufenden Auftrags, einen HA-Prozessneustart, automatisches Fortsetzen oder den Zustand nach einem solchen Neustart.
- Dieselbe Oberfläche zeigte für die letzte schreibgeschützte Gewitterradar-Vorschau die berechneten Dateidifferenzen **0 hinzugefügt, 35 geändert, 16 entfernt, 90 unverändert**. Diese Zahlen belegen **keine tatsächlich ausgeführte Dateisystemmutation**. Die Anzeigen zu Ressourcen unterschieden korrekt 12 verfügbare Kerne von vier konfigurierten Arbeitsprozessen sowie einem tatsächlich möglichen parallelen Leseauftrag und null Schreibaufträgen.

## Zusätzlich beobachteter, nicht sicherheitskritischer Bedienhinweis

Nach Abschluss der Vorschau ist die große zentrale Schaltfläche optisch goldfarben und trägt „2/4 · Schreibzugriff freigeben“. Der Quellcode setzt sie in diesem Zustand aber tatsächlich auf `disabled`, weil nur Stufe 1 bedienbar ist; der erläuternde Text bestätigt die Sperre. **Kein Backend-Freigabefehler nachgewiesen.** Für die spätere Gestaltung sollte die gesperrte zweite Stufe weniger wie eine aktiv bedienbare Schaltfläche aussehen; eine Gestaltungsänderung benötigt eigene Versionierung, Tests und Abnahme.

## Was ausdrücklich NICHT bewiesen wurde

- Dass der **vorher gespeicherte fehlgeschlagene Export** tatsächlich über `retry_pending()` mit derselben Exportkennung übertragen wurde. Neu hochgeladene Berichte beweisen nur den normalen Exportweg; der spezielle Wiederholpfad bleibt separat offen.
- Dass ein **während der Quellprüfung** unterbrochener Android-Browser bzw. WLAN-Wechsel die HA-eigene Aufgabe überlebt und nach der Rückkehr dieselbe Auftragskennung/den terminalen Zustand anzeigt.
- Die **persistente Auftragshistorie** nach einem kontrollierten HA-Neustart und die Markierung eines dann unterbrochenen Auftrags. Kein Neustart wurde angefordert oder ausgeführt.
- V1/V2-exklusive Besitzsperre, reale V2-eigene Sicherung, Rückfall, schreibende Installation, Sammelinstallation oder selbstständiger HA-Neustart.

## Datenschutz und Quellenlage

Diese Datei enthält nur eine **bereinigte, manuell bewertete Abnahmezusammenfassung** ohne Diagnose-JSON, aufbewahrte Rohprotokolle, Auftrags-/Exportkennungen, Zugangsdaten, private Git-Inhalte, lokale Pfade oder individuelle Geräteinformationen. Die Originalnachweise verbleiben **ausschließlich** im privaten `TheDaimos/Project-Log-And-Export`; nicht in dieses öffentliche Entwicklungsrepository kopieren. Eine öffentliche Kopie der privaten Dateien ist unzulässig.

## Nächste Abnahme in kleinen Schritten

1. **Bereits HA-real geprüft:** Serverseitige Auftragshistorie im selben HA-Lauf: „Damals erfolgreich“, frühere fehlgeschlagene Aufträge, keine Schreibfreigabe. Diesen Test nicht unnötig wiederholen.
2. Einen gesonderten Android-Verbindungs-/Browserunterbrechungstest **während eines neuen laufenden schreibgeschützten Auftrags** planen. Wegen der derzeit kurzen Prüfzeiten muss die tatsächliche Unterbrechung nachgewiesen werden; bloßes Wiederöffnen nach Abschluss genügt nicht. Vor neuem HA-Auftrag die Testdurchführung möglichst ohne Timing-Risiko klären.
3. Kontrollierten HA-Neustartfall nur gesondert und durch den Betreiber freigegeben abnehmen; keinen Neustart automatisch auslösen.

**Schreibrechte für V2 bleiben gesperrt.** PR #2 bleibt OPEN/DRAFT/UNMERGED. Keine Änderungen an DRA V1, V2 PUB/main, WeatherRouter oder dem privaten Archiv.

**C.K. – Eine Idee weiter gedacht.**

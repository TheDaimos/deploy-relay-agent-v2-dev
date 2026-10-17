# DRA V2 – Verbindlicher verkürzter Fertigstellungsplan

**Neufassung: 12.10.2026 · ausdrückliche Kurskorrektur des Projektinhabers.**  
**Stand:** DRA V2 DEV 0.1.72 im isolierten Entwicklungszweig `feature/v2-10-inventory-operation-contract`.  
**Produktziel:** DRA V2 **ersetzt** DRA V1. V2 ist **keine Neuentwicklung der vorhandenen Installationsengine** und kein System zum dauerhaften gleichzeitigen Betrieb von V1 und V2.

## Einziges Ziel

Bewährte DRA-V1-Mechanik für Git-Quelle, Vorschau, Installation, Sicherung, Rückfall und HA-Neustart **so weit wie möglich übernehmen**. Dazu nur die **wesentlichen Verbesserungen**:
1. **Home-Assistant-eigene serverseitige Aufträge:** Weiterarbeiten bei Browser-/Netzverlust, eindeutig wiederauffindbare Aufträge, realer Fortschritt und klare Wiederanlaufzustände.
2. **Echte Mehrkernverarbeitung:** Geeignete, CPU-intensive Schritte außerhalb der HA-Hauptschleife auf mehreren Prozessen; sinnvoll begrenzte parallele unabhängige Verarbeitung. Keine Behauptung, dass die bisherigen synthetischen CPU-Messungen bereits reale Installationen parallelisieren.
3. **Beibehaltene und fertiggestellte V2-Oberfläche:** eine zentrale Deployment-Schaltfläche, vier Schritte, Logs, klare Version, mobil bedienbar. Keine weiteren grundlegenden Umbauten ohne konkrete Anforderung.

**Umsetzungstand 12.10.2026:** Übernahme der V1-Engine und V2-interner Quell-/Auftragsadapter bereits im DEV-Featurezweig codiert und anhand echter synthetischer Installation und automatischem Rückfall CI-grün geprüft. **Noch nicht in live HA/UI angeschlossen; daher keine V2-Schreibfreigabe.** [Prüfbericht](V2_V1_ENGINE_REUSE_IMPLEMENTATION_2026-10-12.md). Nächster Schwerpunkt ist das produktive Zusammenschalten der vorhandenen Bausteine und die reale, begrenzte Mehrkernverarbeitung – **keine weitere Neuplanung**.

## Bereits vorhanden – nicht erneut entwickeln

- DRA V1: produktiv erprobte Git-, Planungs-, Vorschau-, Staging-, Sicherungs-, Installations-, Integritäts-, Restore- und Rückfallengine.
- DRA V2 DEV 0.1.72: schreibgeschützte SHA-gepinnte Quellprüfung, browserunabhängige HA-Leseaufträge, nachvollziehbare Auftragsmetadaten und Wiederverbindung, Diagnose/privater Git-Export, die gemeinsam gestaltete Oberfläche.
- Einzelne frühe V2-Besitz-/Backup-Verträge sind **nur Vorarbeiten**; nicht als Ersatz für die reale V1-Engine oder eigenständige umfangreiche Entwicklungsziele fortführen.

## Jetzt entwickeln – als ein zusammenhängender Funktionsblock

1. **V1-Engine in die V2-Laufzeit einbinden.** Vorhandene öffentliche V1-Implementierung im V2-Quellrepository prüfen und unter dem eigenständigen V2-Namensraum gezielt adaptieren. Möglichst identische Regeln für Manifest, Commitbindung, Zielpfade, Vorschau, echte Sicherung, Installation, Restore und Rückfall; keine neue Sicherungs-/Dateisystemengine ohne belegten Grund. Die bestehenden V1-Sicherheitskontrollen behalten.
2. **Serverseitige Ausführung für echte V1-artige Aufträge anbinden.** Ein aktiver Auftrag wird von HA besessen, nicht vom Browser; eindeutige ID, Zustandsjournal und Wiederverbindung. Bei HA-Prozessausfall niemals fälschlich „erfolgreich“ melden. Nach tatsächlichem Dateischreiben aus gesichertem Journal sicher fortsetzen oder einen ehrlichen Wiederherstellungszustand melden; Rückfall nur bei geprüfter Sicherung.
3. **Mehrkern- und Parallelitätssteuerung an reale Arbeit binden.** CPU-intensive Prüfsummen/Dateivergleiche wo möglich in begrenzten Prozessen, I/O effizient und außerhalb der HA-Hauptschleife, mehrere unabhängige Projekte parallel. **Keine** parallelen mutierenden Aufträge gegen dasselbe Ziel, kein ungezügelter Prozessstart. Parallelität an echter Updatearbeit messen statt nur an synthetischer Last.
4. **V2-Funktionsumfang fertigstellen.** Eine zentrale Taste, Fortschritt und Status der echten Bereitstellung, Sicherung, Rückfall, gesondert bestätigter HA-Neustart. Danach V2 als V1-Nachfolger im kontrollierten HA-DEV-Umstieg abnehmen.

**Keine neue Architektur für dauerhaft gemeinsam betriebene V1 und V2.** Während der befristeten DEV-Umstellung darf V1 weiterhin V2 installieren, aber vor produktiven V2-Schreibaufträgen muss ausgeschlossen sein, dass V1 gleichzeitig dasselbe Ziel verändert. Endziel: **V1 wird bei der Umstellung deaktiviert/ersetzt**, kein umfangreicher gemeinsamer Sperr- und Besitzverwaltungsdienst. Die Eigenabsicherung paralleler **V2-Aufträge** bleibt notwendig.

## Entwicklung und Abnahme: gebündelt, zügig, sicher

- **Zusammenhängende Implementierung zuerst; keine künstlichen G3-/G4-/G5-Einzelstopps.** G3-/G4-/G5-Unterlagen bleiben technische Quellen für nachweislich notwendige Risiken, sind **kein verpflichtender sequenzieller Neuentwicklungs-Schlachtplan** mehr.
- Automatische Funktions-, Sicherheits- und Fehlerfalltests zusammen mit CI innerhalb des Entwicklungsblocks durchführen. Fehler eigenständig beheben und CI erneut prüfen.
- **Ein gebündelter HA-Realtest für eine funktional zusammenhängende Version**, mit mehreren Szenarien und möglichst nur einer Aktualisierung und einem technisch notwendigen Neustart. Kein Einzelscreenshot pro Teilschritt.
- Kein unnötiger Versionssprung für reine Dokumentation. Kein separates HA-Update für jede kleine Oberflächenkorrektur.
- Keine Freigabe zum Schreiben ohne wirklich vorhandene V1-abgeleitete Sicherung/Rückfall und überprüften gesicherten Ausführungspfad; CI ist noch keine reale Installationsabnahme.

## Unveränderte Entwicklungsgrenzen

Nur `TheDaimos/deploy-relay-agent-v2-dev`, Zweig `feature/v2-10-inventory-operation-contract`, darf im laufenden Auftrag geändert werden. V1 DEV/PUB, V2 PUB/`main`, WeatherRouter und das private `TheDaimos/Project-Log-And-Export` nicht verändern; Draft-PR #2 nicht zusammenführen. Echte HA-Diagnosen bleiben privat. **Keine eigenständige HA-Installation, Projektmutation oder HA-Neustart durch den Assistenten.**

**Erfolgskriterium:** Ein echtes Projekt lässt sich mit V2 so zuverlässig wie mit V1 installieren/sichern/rücksichern, seine serverseitige Ausführung bleibt bei Clientverlust eindeutig nachvollziehbar, und echte geeignete Arbeit profitiert nachweislich von Mehrkern-/Parallelverarbeitung. Danach ist der V2-Kern fertig; Zusatzfunktionen sind spätere Versionen.

**C.K. – Eine Idee weiter gedacht.**

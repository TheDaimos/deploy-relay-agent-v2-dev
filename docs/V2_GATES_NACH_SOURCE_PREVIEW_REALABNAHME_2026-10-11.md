# DRA V2 DEV – Freigabefahrplan nach erfolgreicher Quellvorschau

> **Historischer Stufenplan vom 11.10.2026 – durch die ausdrückliche Produkt-Kurskorrektur am 12.10.2026 als Ausführungsreihenfolge abgelöst.** G3/G4/G5 bleiben Sicherheitsnachweise der übernommenen V1-Engine, nicht eigenständige zwingend nacheinander neu zu entwickelnde Produktbereiche. Aktueller verbindlicher Fertigstellungsplan: [V2_ROADMAP.md](V2_ROADMAP.md). Keine parallele V1/V2-Verwaltungsarchitektur als Produktziel.\n\n

**Datum:** 11.10.2026  
**Technischer Ausgangsstand:** DRA V2 DEV 0.1.61 auf `feature/v2-10-inventory-operation-contract`.  
**Abnahme:** Gewitterradar: echte HA-Quellprüfung erfolgreich. Keine Installation, Sicherung oder Wiederherstellung freigegeben.

## Reihenfolge, ohne Sicherheits- oder Entwicklungsstufen zu überspringen

### G2 – Serverseitige Leseaufträge und Wiederverbindung

**Ausgangslage:** Es gibt ein Vorbereitungsmodell mit Kennungen, Zuständen und Journal. Die echte GitHub-Quellvorschau läuft aber derzeit direkt als WebSocket-Anfrage; ihr Abschluss nach Clientverlust ist noch nicht als eigenständiger, beständig beobachtbarer HA-Auftrag abgenommen.

Umsetzung und statische Abnahme:
1. Einen **einzigen** serverseitig besessenen, vom Client abfragbaren Quellprüfauftrag mit eindeutiger Kennung und versioniertem Zustandsvertrag anbinden. Nur HA darf seinen Zustand ändern. Mehrfaches Tippen/Anfordern darf keine unkontrollierten Doppelaufträge erzeugen.
2. Quell-Commit, Projekt, Ziel und Absicht SHA-genau bzw. kanonisch innerhalb der internen Auftragsidentität binden. Eine geänderte Projektauswahl darf alte Vorschauen niemals als gültige Grundlage verwenden.
3. Fortschritt, Abschluss, Fehlerkategorien und Abbruchwunsch redigiert journalisieren, **ohne** Geheimnisse, Rohdateien oder private Inhalte dauerhaft zu speichern.
4. Browserabbruch oder WLAN-Wechsel darf keine falsche Erfolgsmeldung verursachen. Es gibt definierte Begrenzungen für Laufzeit, Warteschlange, Aufbewahrung und Home-Assistant-Hauptschleife.
5. Nach Neustart unbekannte oder aktive Aufträge konservativ als unterbrochen deklarieren, keine automatische Wiederaufnahme von späteren Schreibaufträgen und keine falsche Freigabe.
6. Negative Tests für Doppelanforderungen, Quellenwechsel, Zeitüberschreitung, Browserverlust, unterbrochenen Store und fehlende Adminberechtigung. Dann isolierte HA-Realabnahme.

**Freigabe:** ausschließlich der neue schreibgeschützte Auftragsablauf, kein Schreiben.

### G3 – Fremd-/V1-Besitz und prozessübergreifende Sperre

**Ausgangslage:** Der rein berechnende `target_ownership.py`-Vertrag erkennt bekannte Kollisionen, kann aber fremde Eigentümer/aktive V1-Aufträge nicht tatsächlich ausschließen. Die Tatsache, dass bisher eine V1-Installation erfolgreich war, ist **kein** V2-Besitznachweis.

1. Serverseitig verifizierbare Belegung und Besitz jedes exakten Zielverzeichnisses samt Zeitpunkt, Besitzer, Datenquelle und Vertrauensstatus entwerfen.
2. Fremde, nicht auflösbare und nicht nachweisbar ruhende Eigentümer immer als **blockierend** behandeln. Eine leere Fremdbelegungsliste zählt nicht als Nachweis.
3. V1/V2-Wechsel nur über einen gesondert verifizierten Übergabe-/Sperrvertrag, der Konkurrenz zwischen Prozessen und Neustarts berücksichtigt; **keine Änderungen an V1 ohne neue explizite Nutzerfreigabe**. Ist Exklusivität ohne V1-Kooperation nicht beweisbar, bleibt jede V2-Mutation gesperrt.
4. Zielgruppen strikt auf verwaltete `custom_components/<projekt>`-Verzeichnisse begrenzen; Zielkollisionen auch bei unterschiedlicher Groß-/Kleinschreibung erkennen.
5. Quellstand-, Ziel- oder Projektauswahlwechsel invalidiert jede vorbereitete Freigabe.

**Freigabe:** sicher belegte Zustandsanzeigen und Negativtests. Noch kein tatsächlicher Schreibzugriff.

### G4 – Unabhängige vollständige Sicherung und Rückfall

**Ausgangslage:** `backup_integrity.py` prüft lediglich das Modell von Inventar/Byte-Prüfsummen; es gibt noch **keine** tatsächliche V2-eigene Datenträgersicherung.

1. Eigenständiger, abgetrennter, V2-spezifischer Speicherbereich und strikte Projekt-/Pfad-/Platzgrenzen. Keine V1-Sicherungen als Erfolg übernehmen.
2. Alle ursprünglichen Bytes und die exakte Dateimenge vollständig sichern; sichere Behandlung von Symlinks, Hardlinks, geöffneten Dateien und Änderungen während der Kopie.
3. Vollständig gespeicherte Archive vor jeder späteren Mutation **erneut aus dem Archiv** unabhängig einlesen und gegen das Manifest verifizieren. Metadaten allein sind kein Beweis.
4. Speicherung und Journal gegen Stromausfall/HA-Neustart absichern; Wiederherstellung nur aus nachgewiesenen, unveränderten Archivbytes. Eigenständige Sicherheitskopie vor Restore, selbst wenn die alte Installation beschädigt ist.
5. Umfassende isolierte Fehler- und Rückfalltests auf künstlichen Dateisystemen ohne Zugriff auf Benutzerordner. Erst danach eigens genehmigte HA-DEV-Realabnahme.

**Freigabe:** funktionsfähige Sicherung/Integritätsnachweis und klar abgegrenzte Wiederherstellungstests. **Nicht** stillschweigend Installation.

**Ergänzende verbindliche Anforderung:** [Installierbarkeitsprüfung, automatischer Rückfall und unabhängiger Recovery-Wächter](V2_INSTALLABILITY_GUARD_AND_AUTOMATIC_ROLLBACK_2026-10-11.md). Bei nachgewiesenem Preflight-Fehler keine Mutation und kein Rollback; nach belegtem Schreibbeginn ausschließlich geprüfte Restore-Transaktion, sonst `recovery_required`. Ein ausgefallener HA-Prozess benötigt eine gesonderte externe Wiederherstellungslösung.

### G5 – Schreibende Einzeltransaktion

Erst wenn G2–G4 einzeln bestanden und die V1/V2-Exklusivität tatsächlich belegbar sind:
- explizite Administrator-Bestätigung mit festem Quell-SHA und Zielidentität;
- erneute frische Bestandsaufnahme unmittelbar vor dem Schreiben, verifizierte Original-Bytes-Sicherung, kontrolliertes Staging und globale Schreibsperre;
- geprüfte Transaktion mit Wiederanlauf-/Rückfallzustand für Abbruch, Netzverlust und HA-Neustart, nachvollziehbare Abschlussprüfung;
- Wiederfreigabe der Installation **erst** nach allen technischen, negativen und Nutzer-Realabnahmen. Neustart weiterhin eigener bestätigungspflichtiger Schritt.

### Später

Konfliktsichere, vollständig serverseitige Sammelupdates mit mehreren Projekten; Ressourcen- und Lastabnahme; mobiles Fortschrittsmodell; Selbstupdate als letztes und danach separate Veröffentlichung.

## Nächste konkrete Bearbeitung

**Zuerst G2 als kleines, überprüfbares Paket entwickeln:** Serverseitige Quellprüfaufträge und Wiederverbindung, bestehende Testdaten und erfolgreiche GitHub-Leselogik wiederverwenden. Ohne HA-Dateischreiben und zunächst ohne erzwungenen Versionswechsel beim Betreiber. Danach G2-CI sowie exakt ein separat angeforderter HA-Test.

**Verbindliche Schutzgrenzen:** Entwicklung ausschließlich auf `feature/v2-10-inventory-operation-contract`. V1 DEV/PUB, V2 PUB und V2-main, WeatherRouter und privates Zentralarchiv bleiben unberührt. Draft-PR #2 nicht zusammenführen. Neue echte Exporte ausschließlich privat. **Keine selbstständigen HA-Installationen oder Neustarts.**

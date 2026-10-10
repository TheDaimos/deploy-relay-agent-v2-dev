# Ausführliche Chatübergabe – Deploy Relay Agent V2 DEV 0.1.53

**Übergabe erstellt:** 11.10.2026  
**Projekt:** Deploy Relay Agent V2 (DRA V2, isoliertes Home-Assistant-Entwicklungslabor)  
**Repository:** TheDaimos/deploy-relay-agent-v2-dev  
**Alleiniger zulässiger Arbeitszweig für diese Fortsetzung:** `feature/v2-10-inventory-operation-contract`  
**Letzter geprüfter Quellstand VOR dieser Übergabe:** `6d738aafec358d96013a763c9397a18a7ebca894`  
**Version in `const.py` und `manifest.json`:** `0.1.53`  
**CI für den Codecheckpoint:** GitHub Actions Run `38088703225`, **SUCCESS**.  
**Abnahmegrenze:** GitHub CI bestanden; Home-Assistant-/Android-Realabnahme für die letzten Oberflächenänderungen noch offen.  
**Zweck dieses Dokuments:** Den gesamten Entwicklungs- und Entscheidungsstand aus einem sehr umfangreichen Chat zuverlässig in Git sichern. Dieses Dokument ist **kein Installationsauftrag, kein Release und keine Freigabe**.

> **Für den nächsten Chat:** ZUERST `TheDaimos/project-defaults/START_HERE.md` lesen (Bootstrap „Daimos“), danach `AGENTS.md` und `docs/AI_CONTEXT.md` in diesem Repository, danach diese Übergabe vollständig. Nie eine alte Erinnerung anstelle des tatsächlichen Zweig-/CI-Stands verwenden. Bei widersprüchlichen historischen Aussagen gilt die aktuelle Implementierung auf dem oben genannten Zweig. Keine Sprünge in der verbindlichen V2-Roadmap.

---

## 1. Wichtigste verbindliche Sicherheits- und Projektregeln

1. **Keine Änderungen außerhalb des Featurezweigs** `feature/v2-10-inventory-operation-contract` ohne neue ausdrückliche Benutzerfreigabe. DRA V1 DEV/PUB, DRA V2 PUB, DRA V2 DEV `main` und WeatherRouter **unangetastet** lassen. **Entwurfs-PR #2 keinesfalls zusammenführen.**
2. DRA V1 ist die **stabile, reale Bereitstellungsmethode** für das getrennte DRA-V2-DEV-Testlabor. Es darf keine stille Installation und kein stiller oder automatischer Home-Assistant-Neustart aus dem Chat ausgelöst werden. Über das V1-Manifest kann DRA bei einer **vom Benutzer ausdrücklich gestarteten** Aktualisierung einen HA-Neustart gemäß dessen eigenem Ablauf vorsehen; das ist nicht gleichbedeutend mit einem funktionsfähigen V2-Installationspfad.
3. Die V2-Komponente bleibt isoliert: Domain `deploy_relay_v2_dev`, Panel `dra-v2-dev-lab`, statischer Pfad `/dra_v2_dev_static`. `deploy-relay.json` kopiert nur `custom_components/deploy_relay_v2_dev` unter `/config` und begrenzt die Bereitstellung auf 24 Dateien und 3 MiB entpackt, keine Symlinks.
4. **V2 ist kein freigegebenes produktives Installationssystem.** Lesen/Vorschauen und echte Testmessungen sind vorhanden; **Schreibfreigabe, tatsächliche Installation, dauerhafte V2-Sicherung, Wiederherstellung, Rotation und parallele Installation sind NICHT freigegeben**. Keine automatische Entsperrung durch erfolgreiches CI, einen erfolgreichen Git-Status oder eine korrekte Vorschau.
5. Nie Tokens, Passwörter, private Erweiterungen, Instanzdaten, unredigierte Exportdateien, HA-Backups, Diagnose-Rohdaten oder interne Infrastrukturinformationen im öffentlichen Projekt-Repository veröffentlichen. Nicht aus realen Benutzertests Beispiele/Fixtures mit echten Daten erstellen.
6. **Neue echte Exporte sämtlicher Daimos-Projekte ausschließlich in das private Repository `TheDaimos/Project-Log-And-Export`.** Gilt auch für DRA V2; niemals ersatzweise ein anderes Projekt-Repository verwenden. Globale Referenzen: `TheDaimos/project-defaults/START_HERE.md` und `docs/PRIVATE_EXPORT_INCIDENT_POLICY.md` dort. Bei tatsächlich nachgewiesenem neuem Fehl-Export zuerst den verbindlichen Sicherheitsalarm auslösen, keine stille Reparatur.
7. Sicherheitskern nach `AGENTS.md`: SHA-gepinntes Git, eindeutige Besitz- und Zielpfade, Fail-Closed, Admin-Schranken, bestätigte Freigabe vor Mutationen, vollständige V2-eigene Sicherung und Verifikation vor jedem Schreiben, sicherer Rückfall/Recovery, keine blockierende Arbeit in der HA-Haupt-Ereignisschleife, serverseitige Auftragsführung.
8. Der Nutzer ist alleiniger Entwickler; **keine Teamformulierung**. Deutsch ohne unnötiges Denglisch; technische Eigennamen wie GitHub, Commit, Branch, Deployment dürfen bleiben. Auf Smartphone-Bedienung und kopierbare einzelne Anweisungen achten. **Maximal eine konkrete HA-Testhandlung pro Antwort**, wenn Realabnahmen anstehen.
9. Git ist verbindlicher Erinnerungsträger. Exakte Speicher-/Kontextprozente ohne technische Messquelle niemals erfinden; bei großem Chat frühzeitig neue Übergabe anbieten.
10. **CI-grün ≠ HA-Realabnahme ≠ V2-Final.** Jede freigaberelevante Funktionsstufe separat prüfen, dokumentieren und erst nach positiver Realabnahme die nächste schreibende Stufe angehen.

## 2. Repositoryaufteilung und verbindliche Quellen

| Ort | Bedeutung |
| --- | --- |
| `TheDaimos/deploy-relay-agent-v2-dev` | Öffentliches Entwicklungsrepository; diese Fortsetzung ausschließlich auf Featurezweig |
| `TheDaimos/deploy-relay-agent-v2-pub` | Späterer Auslieferungskanal, in diesem Auftrag unverändert |
| `TheDaimos/deploy-relay-agent-dev` | Bestehendes DRA V1 DEV, stabile Referenz und derzeitiger HA-Bereitstellungsweg |
| `TheDaimos/deploy-relay-agent-pub` | Öffentlicher V1-Auslieferungskanal, unverändert |
| `TheDaimos/Project-Log-And-Export` | Einzig zulässiges **privates** Archiv neuer echter Test-/Diagnose-/HA-Exporte |
| `TheDaimos/project-defaults` | Projektübergreifender Bootstrap und verbindliche Sicherheits-/Erinnerungsregeln |
| `TheDaimos/home-assistant-dev-toolkit` | Nur bei konkretem Bedarf für wiederverwendbare Werkzeuge hinzuziehen |

**Projektdateien/Referenzen:**
- `AGENTS.md` – Sicherheits- und Entwicklungsregeln.
- `docs/V2_ROADMAP.md` – verbindliche Abfolge von V1-Referenz über serverseitige Jobs, Sicherung, Sammelupdate, Tests bis späterem Release. Der historische Einleitungsstand „Vorbereitung/V1.0.0“ ist veraltet und beschreibt nicht den laufenden 0.1.53-Testlaborstand.
- `docs/V2_CENTRAL_PRIVATE_DIAGNOSTICS_2026-10-09.md` – historisch fortgeschriebene Detailentscheidungen ab 0.1.15 bis 0.1.53, umfangreich.
- `docs/V2_B2_PREFLIGHT_BACKUP_INTEGRITY_2026-10-09.md` – verbindliche Quell-/Backup-Integritätsgrenzen und noch fehlende reale Transaktion.
- `docs/PUBLIC_DEVELOPMENT_POLICY.md` – Vertraulichkeit und CI-/Veröffentlichungsgrenzen.
- `deploy-relay.json` – tatsächlicher DRA-V1-Bereitstellungsvertrag für das isolierte V2-DEV-Verzeichnis.
- `custom_components/deploy_relay_v2_dev/const.py` und `manifest.json` – konsistente aktuelle Version 0.1.53.
- `custom_components/deploy_relay_v2_dev/frontend/lab.js` – V2-DEV-Oberfläche.
- `custom_components/deploy_relay_v2_dev/websocket_api.py` – ausschließlich administrative V2-WebSocket-Befehle.
- `custom_components/deploy_relay_v2_dev/project_catalog.py` – Projektkatalog, Sortierung, V1-Metadatenimport, Aufbewahrungswerte, virtuelle Sammelupdate-Position.
- `custom_components/deploy_relay_v2_dev/remote_source.py` und `source_preflight.py` – sichere, schreibgeschützte Git-/HA-Quellprüfung.
- `custom_components/deploy_relay_v2_dev/backup_integrity.py` – **rein berechnender** vollständiger Sicherungs-Integritätsvertrag, kein echtes Speichern oder Rücksichern.
- `tests/test_v2_countdown.js` und `tests/test_v2_dev_lab_isolation.py` sowie Python-Negativ-/Quell-/Katalogtests – verbindliche Regressionstests.

## 3. Tatsächlich vorhandener Funktionsumfang per 0.1.53

### 3.1 Home Assistant und Diagnose-/Messlabor

- Eigenständige registrierbare HA-Integration und Sidebar für DRA V2 DEV; keine Überschreibung der V1-Integration.
- Admin-WebSocket-Routen für echten lesenden HA-Testlauf, separate Mehrkernmessung, Gesamttest, Statusabruf und bisher begrenzten Auftragsverlauf; der frühere **synthetische Testauftrag mit künstlicher 40-Sekunden-Wartezeit wurde in 0.1.20 entfernt**. Nicht neu einführen.
- Meldungen und Diagnosen mit strukturiertem Status; der Teststatus wird während echter Aufträge aktualisiert, im Leerlauf keine unnötige Dauermessung. Mess-/Ressourcenangaben sind echte Beobachtungen, keine Garantie für CPU-Quoten.
- Auftragseinstellungen `04 · Auftragsverarbeitung`: Betrieb nacheinander bzw. Planvorgaben für parallele **lesende** Aufträge; Zahl der DRA-Arbeitsprozesse als Vorgabe. Nicht behaupten, dies sei schon eine voll betriebsfähige parallele Installationswarteschlange.
- Privater Git-Diagnoseexport mit eigenem Repo und Token, Serverpersistenz und grün/rot kenntlicher Prüfung, Download als JSON, Retry. Der Nutzer berichtete früher eine **erfolgreiche reale Übertragung** in das zentrale private Archiv. Das ist benutzerbestätigt; nicht ohne zusätzliche Prüfung als vollständiger unabhängiger Git-/HA-Integritätsnachweis darstellen.
- Exportidentität: Anwendung `deploy-relay-agent-v2`; nach Archivstandard unter `exports/deploy-relay-agent-v2/<JJJJ-MM>/...`, nicht im Quellrepository. Token-Endung nur serverseitig vermittelt, nie vollständiges Token zurückliefern.

### 3.2 Projektverwaltung

- Oberhalb des Hauptmenüs liegt auf Desktop/iPad ein breiter Projektbereich; mobile Oberfläche bleibt kompakt. Schaltfläche **Projektverwaltung** öffnet einen gesonderten Dialog.
- Projektliste enthält nummerierte Projektkarten/-zeilen; Git-Verbindung kann pro Projekt oder über **„Alle Projekte prüfen“** explizit geprüft werden. Zustände „Prüfen / Online / Offline“, gleich große Statusflächen und farbige Karten. Status wird nicht ohne reale Prüfung behauptet.
- Metallische, hochauflösende SVG-Schaltflächen für **Einstellungen, hoch, runter** mit Lichtkante, Materialverlauf, Tiefe, gedrücktem Zustand; unzulässige Richtungen matt. Durch Antippen/Klicken einer freien Projektzeile goldene Zeilenmarkierung, auch unabhängig von den Pfeilen.
- Inaktive Projekte erhalten **„Inaktiv“ rot und fett oben rechts**, ohne zusätzliche Zeilenhöhe. Git-Verfügbarkeit und administrativer Aktivstatus sind verschiedene Zustände.
- Projekt-Einstellungen: Repository ändern (mit abgesicherter Prüfung), vorhandenes GitHub-Token durch neues ersetzen, gespeicherte Token-Endung mit **fünf grünen Zeichen**, Token speichern, Verbindung prüfen, Anzeigename, Notiz, **Zugriffsart Read-Only / Read-Write rein informativ**, „Projekt aktiv“, sichere Entfernung mit Bestätigung. Rechteauswahl ändert keine echten GitHub-Berechtigungen.
- Projektaufnahme per Repository und selektiver **Import aus DRA V1** mit Vorauswahl „Alle“. Import übernimmt **V1-Projektmetadaten**, schreibt nicht in V1 und darf keine V1-Geheimnisse stillschweigend kopieren. Tokenübernahme ist nicht als uneingeschränkt vollautomatischer Nachweis annehmen; V2-Tokens müssen sicher getrennt hinterlegt beziehungsweise explizit geklärt werden.
- Projekte lassen sich für spätere Sammelaktualisierung separat aktivieren/deaktivieren. **Reihenfolge echter Projekte** steuert Anzeige, Vorauswahl und spätere priorisierte Sammelverarbeitung; Parallelität darf diese Priorität nicht stillschweigend aufheben.
- **Sammelupdate als virtueller Listeneintrag** seit 0.1.52: eigenständige Position, mit Pfeilen nach oben/unten verschiebbar bis Platz 1; gleiche Position im Hauptprojektwähler, **persistiert als `picker_batch_position`**. Kein GitHub-Repository und kein eigener Online-Status. Bewegung über einen echten Nachbarn ändert nur die virtuelle Position und **nicht** die relative Reihenfolge der echten Projekte. Alte Kataloge ohne Feld bleiben lesbar.
- Unter **„Alle Projekte prüfen“** befindet sich die Karte **Sammelaktualisierung** mit der Bearbeitung der gespeicherten Projektauswahl. Darunter eigene kompakte Karte **Deploy Relay Agent V2**, mit Status des gesonderten Lesezugangs und Zahnrad für eigene Einstellungen.
- V2-Systemkarte öffnet eigenes Fenster für **getrennten privaten GitHub-Lesezugang** und erweiterte Quellprüfung. Die Buttons „Lesezugang speichern“ und „Lesezugang entfernen“ stehen nebeneinander. Umfangreiche Hinweise sind gekürzt; optionale Quellzweigangaben in einklappbarem Bereich. Kein Token im DOM nach erfolgreicher Speicherung.

### 3.3 Separater Hauptprojektwähler

- Natives Android-`<select>` ersetzt durch eigens gerahmtes dunkles Popup mit Projektname, Repository, Linien und Auswahlhaken.
- Aktive Einzelprojekte sind auswählbar; inaktive werden gekennzeichnet, aber nicht ausgewählt.
- **Sammelupdate erscheint innerhalb derselben verschiebbaren Liste** an der in Projektverwaltung gewählten Position – nicht mehr unveränderlich als unterste Aktion.
- Sammelupdate übernimmt **alle aktiven, vorausgewählten Projekte** gemeinsam in die Hauptansicht. Ein Wechsel zurück auf ein Einzelprojekt beendet den Gruppenmodus.
- Für Sammelupdate ist derzeit nur `batch/preview` vorhanden: **serverbestätigte Projektidentitäten und Gruppenauswahl, keine verifizierten Quellen und keine Installation**. Kein aktives Projekt vorausgewählt → erklärende Meldung und keine Scheinauswahl.

### 3.4 Navigation und Fenster

- Oberflächen-Trennung: Hauptansicht vs. **Diagnose & Einstellungen**. Die Einstellungen bestehen aus einklappbaren Unterabschnitten; Projektverwaltung ist kein doppelt auf der Einstellungsseite gezeigtes Tabellenmonster mehr.
- Eigene mobile Projektverwaltung mit festem Kopfbereich, **darunter isoliertem Scrollbereich**; Scrollinhalt darf nicht oberhalb der Überschrift sichtbar werden. Scrollposition nach Neuzeichnen und verschobene Zeile erhalten.
- Smartphone-Knöpfe und Dialogaktionen mit optischer Druckrückmeldung.
- Android-native **Zurücktaste** führt aus Diagnose & Einstellungen zurück zum **DRA-V2-Hauptmenü**, bevor die normale HA-Navigation fortgesetzt wird; dieselbe URL mit eigenem `history.pushState`-Schritt, `popstate`-Listener und Bereinigung. Onscreen-„Hauptmenü“ räumt den Eintrag ebenfalls ab. Noch auf echter Android-/HA-Instanz abnehmen.

### 3.5 NEU 0.1.53 – zentrales Deployment statt doppelter Ablaufkästen

Die jüngste große Designentscheidung aus dem Chat ist **verbindlich**:

**Aufbau Hauptansicht:** (1) Projektwahl/Projektverwaltung, (2) „Quelle & Version“, (3) **„Deployment“** mit **einer großen zentralen Schaltfläche**, (4) schmaler animierter Fortschrittsbalken **direkt unter** der Schaltfläche, (5) darunter vier kompakte Prozessfelder, (6) nur tatsächlich verfügbare Quell-/Vorschauinformationen. Der separate riesige Block „Geführter Ablauf“, die alte doppelte Projektkarte, zusätzliche Diagnose-Karte und mehrfachen Vorschauknöpfe **sind entfernt**.

**Vier-Stufen-Konzept (visuelle Gestaltung und Ziel-Semantik):**

| Phase | Farbe | Hauptschaltfläche | Stand 0.1.53 |
| --- | --- | --- | --- |
| 1/4 | Blau | „Vorschau berechnen“ | **Echt und schreibgeschützt** für einzelne Quellen; in Sammelupdate nur Gruppenidentitätsvorschau |
| 2/4 | Orange | „Schreibzugriff freigeben“ | Nach **erfolgreich SHA-/quellgebundener Einzelquellprüfung** optisch erreicht, aber **deaktiviert** |
| 3/4 | Rot | „Update installieren“ | Rein vorgesehener künftiger Zustand; **nicht implementiert/freigegeben** |
| 4/4 | Grün | „Abschluss / Neustart oder Frontend“ | Rein vorgesehener künftiger Zustand; **nicht implementiert/freigegeben** |

- Nur der **große Button** löst die aktuelle zugelassene Aktion aus. Die vier Prozessfelder sind **Statusanzeige, keine weiteren Aktionsknöpfe**. Während einer echten Quellprüfung ist der Button gegen Wiederholung gesperrt und zeigt Arbeitszustand.
- **Original DRA-V1-Ladeanimation als gestalterische Grundlage** aus `TheDaimos/deploy-relay-agent-dev`, Datei `custom_components/deploy_relay/frontend/deploy-relay-panel.js`, `relay-preview-bar`: Balkenbewegung 0% → 55% → 100% mit Verschiebung -110% / 85% / 245% und Zyklus **1,05 s**. Leuchtreflex am Button analog `relay-preview-sheen` (ca. 1,15 s). In V2 als **schmaler bewegter Balken / Trennlinie** zwischen Hauptknopf und Prozessübersicht realisiert; bei erfolgreicher Vorschau statisch 25%; Einstellung „reduzierte Bewegung“ berücksichtigt. Kein künstlicher Fortschrittsprozentsatz einer Installation.
- Der Klick in der Einzelansicht verwendet die echte administrative Route `projects/source_preview`. Quelle, Referenz und Commit sind gebunden; die **Quellreferenzänderung verwirft die bisherige Vorschau**. Nach gültiger Antwort steigt die Anzeige auf Orange/2, bleibt dort gesperrt.
- Bei reiner Sammelupdate-Gruppenidentitätsprüfung **kein** Orange/2: `sources_verified=false`, `installation_enabled=false`. Solange nicht für jedes Ziel die Quelle einschließlich tatsächlicher Änderungen sicher feststeht, verbleibt die Gruppe in Schritt 1.
- Aus Sicherheitsgründen auch künftig: kritische Phase 2/3 nicht durch wiederholtes Antippen automatisch bestätigen; explizite Admin- und Sicherheitsabfragen vor Schreibfreigabe bzw. Installation. Schritt 4 muss **HA-Neustart vs. Frontend-Neuladen vs. kein Neustart** nach realem Plan unterscheiden; für echten HA-Neustart zweite Abfrage. Grün soll erfolgreiche Abschlusskontrolle signalisieren, nicht lediglich einen unbestätigten Neustartwunsch.

## 4. Was ausdrücklich NICHT fertig ist

### 4.1 V2-Installations- und Auftragssicherheit (höchste Priorität)

- Noch **kein** vollwertiges V2-eigenes Installations-/Änderungsjournal mit per HA-Neustart wiederaufnehmbaren, persistenten Schreibaufträgen und bestätigtem Wiederherstellungszustand.
- Noch **keine** geprüfte serverseitige Auftragsverarbeitung für parallele Installationen, Konfliktsperren, Lese-/Schreibtrennung, gebundene Commitquelle, seriell erforderliche Sperren, korrekte Fehlerfortsetzung und Wiederverbinden nach Android-Schließen/Netzwechsel.
- Noch **keine** nachweislich vollständige, V2-eigene und unabhängig nachgeprüfte Sicherungsdatei vor Mutation, keine tatsächliche Rotation, keine unabhängig verifizierte Wiederherstellung/Rückfallautomatik.
- `backup_integrity.py` verifiziert bereitgestellte Daten gegen ein vollständiges Manifest **rein rechnerisch** – es wurde damit noch kein tatsächlicher Sicherungsstand angelegt.
- `source_preflight.py` und `remote_source.py` liefern sichere **Lese-/Vorschau-Bausteine**, keine Garantie dafür, dass V1-verwaltete HA-Dateipfade V2 exklusiv gehören.
- Schritt-3- und Schritt-4-Backend (schreibendes Installieren, Restore, HA-Neustart oder Frontend-Neuladen) bleibt bis zur gesonderten Gate-Abnahme gesperrt. Insbesondere **keinen Button kosmetisch freischalten**, nur weil die UI nun schön aussieht.

### 4.2 Sammelupdate als echte parallele Installation (benutzerdefinierte Zielvorgabe)

- Nutzerziel: Ein Druck auf den Sammelupdate-Eintrag wählt **alle aktuell als aktiv + für Sammelupdate ausgewählten Projekte**. Später soll **ein gemeinsamer Installationsauftrag** sie parallel/gleichzeitig aktualisieren, nicht zur Auswahlbearbeitung zurückspringen. Diese Zielsemantik ist entschieden.
- **Heute real:** Gruppenauswahl plus read-only Identitätsvorschau; kein tatsächlicher Vergleich aller Ziel-Dateien, kein transaktionaler Parallel-Installer.
- Zukunft: Pro Projekt SHA-gepinnte Quellen-/Datenvorschau, Abhängigkeits-/Zielkollisionen erkennen; concurrency begrenzen und Fairness/Reihenfolge respektieren. Projekte mit gemeinsamen HA-Zielordnern dürfen nicht gleichzeitig schreiben. DRA-Selbstupdate **zuletzt** und nur nach sicherer Abstimmung wegen möglichem Agent-Neustart/Versionswechsel.
- Reihenfolge echter Projekte bleibt unabhängig von der verschiebbaren Position des virtuellen Sammelupdate-Eintrags.

### 4.3 Backup & Retention (frühere explizite Benutzerwünsche)

- Bereits vorhanden: Aufbewahrungszahl je Projekt, **3–100** (historischer Standard 10), per Popup gespeichert; echte Backup-Übersicht bewusst **deaktiviert**, solange es keine echte V2-eigene Backup-Inventarisierung gibt.
- **Noch offen:** Vollständig erfasste und unabhängig verifizierte Backups, Speicherbedarf je Projekt in MiB/MB auf realen Messungen, Anzahl/gesamt/Ø/Prognose sauber unterschieden, optionale besondere Sicherungen vor Rotation **festschreiben**, Speicherplatz-/Grenzwarnungen und echte Backup-Löschung erst nach ownership- und Restore-Absicherung.
- Benutzerentscheidung zum **Löschknopf**: **kein Papierkorb-Symbol**; stattdessen eindeutige Aktion „Backup entfernen“ und **zweite Sicherheitsabfrage mit Text „Wirklich löschen?“**. In 0.1.53 noch nicht als schreibende Funktion vorhanden.
- Keine nicht vorhandenen Backup-Größen erfinden, keine V1-Backups ohne Übergabe als V2-eigenes Inventar zeigen, keine Rotation oder Löschung von V1-eigenen Daten.
- Export von Protokollen/Backups nur nach geklärtem Schutz und ausschließlich am zulässigen Ziel; private Daten nie im öffentlichen Git.

### 4.4 Noch ausstehende fachliche Abnahmen

- DRA V2 DEV 0.1.53 **HA-/Android-Realtest** der neuen Deployment-UI, 1/4-Button, Fortschrittsbalken, Scroll-/Layout-Verhalten, Referenzwechsel und Zustand nach erfolgreicher bzw. fehlgeschlagener echter Vorschau.
- Frühere UI-Abnahmen für: virtuelle Sammelupdate-Position bis Platz 1, Erhalt nach Aktualisierung/Reload, gemeinsamer Picker; V2-Systemeinstellungsdialog; „Zurück“-Navigation aus Diagnose/Settings; Inaktiv-Kennzeichnung; Mehrkern- und Ressourcenansicht – nicht aus CI auf bestanden schließen.
- Ressourcen-/Ereignisschleifen-Abnahme (Roadmap V2-40-50), HA-Reaktionszeit, I/O und parallele Leseaufträge; JavaScript/Frontend auf Android (Touch, Dialog-Fokus, Scroll, Umbruch).
- Abschlussprüfung öffentlicher V2-Quellpakete und später separates V2-PUB-/HACS-/FINAL-Gate. **Jetzt noch kein Release.**

## 5. Änderungshistorie der jüngsten Iterationen

| Version | Kernentscheidung/Ergebnis |
| --- | --- |
| `0.1.15–0.1.17` | Zentrales privates Diagnosearchiv, Einrichtung der getrennten Repo-/Token-Daten, serverseitige Prüfung und JSON-Git-Export |
| `0.1.18–0.1.24` | Mobile Diagnose und Tests bereinigt; synthetischer Testlauf entfernt; Projektvorauswahl und Backup-Aufbewahrung in kompakte Dialoge verlagert |
| `0.1.25–0.1.42` | Projektverwaltung mit V1-Metadatenimport, Notiz, Aktivstatus, Reihenfolge, Token und Statusprüfung; V1-inspirierte Hauptansicht, getrennte Einstellungen, Android- und Desktop-Feinschliff |
| `0.1.43` | Echte metallische Zahnrad-/Pfeilgestaltung, rote Kennzeichnung inaktiver Projekte |
| `0.1.44` | Informative Read-Only/Read-Write-Auswahl in Token-Endungszeile; Projektzeile frei antippbar |
| `0.1.45` | „Inaktiv“ rot/fett **oben rechts** statt zusätzliche Zeile |
| `0.1.46` | Projektverwaltungsdialog: fixer Kopf, darunter eigenständiger Scrollbereich |
| `0.1.47` | Eigenes schönes Projekt-Popup statt nativer Android-Auswahlliste |
| `0.1.48` | Doppelte Projekt- und Diagnosekarten aus Hauptansicht entfernt |
| `0.1.49` | Sammelupdate-Auswahl in Projektverwaltung; V2-eigene Systemkarte/Einstellungen statt langer Texttapete |
| `0.1.50` | Android-native Zurücktaste aus Einstellungen zurück ins DRA-Hauptmenü |
| `0.1.51` | Tokenaktionen nebeneinander; Quellhinweise eingeklappt; Sammelupdate = gemeinsame Hauptprojektwahl |
| `0.1.52` | Virtuellen Sammelupdate-Eintrag frei sortierbar und separat dauerhaft gespeichert |
| **`0.1.53`** | **Eine Deployment-Schaltfläche, vier Statusschritte, DRA-V1-Ladeanimation, gültige Vorschau führt nur bis gesperrter Phase 2** |

Die ausführlichere Einzelhistorie/Begründung steht in `docs/V2_CENTRAL_PRIVATE_DIAGNOSTICS_2026-10-09.md`. Nicht alles erneut aus den alten Chats rekonstruieren, solange Dateien/CI-Quellen verfügbar sind.

## 6. Prüfstand, Git und bekannte wichtige Details

**Vor diesem Übergabedokument überprüft:**
- `feature/v2-10-inventory-operation-contract` war **identisch** zu `6d738aafec358d96013a763c9397a18a7ebca894` (GitHub-Commit-Vergleich).
- GitHub Actions `38088703225` für diesen Codecheckpoint war abgeschlossen mit **SUCCESS**.
- `const.py` und `manifest.json` tragen Version **0.1.53**.
- `deploy-relay.json` war unverändert vorhanden: isolierter Komponentenaustausch, `home_assistant_restart` als V1-Deployment-Lebenszyklus, ausschließlich bei vom Benutzer veranlasster Bereitstellung.
- Der Quelltext der neuen Deployment-UI liegt in `frontend/lab.js`; JS-Laufzeitprüfungen in `tests/test_v2_countdown.js`. Die UI-Verträge und Sicherheitsgrenzen werden auch in `tests/test_v2_dev_lab_isolation.py` geprüft.
- **Diese Dokumentationsübergabe erzeugt einen neuen Commit**, der natürlich nach dem oben genannten Codecheckpoint liegt. Bei Übernahme im nächsten Chat zuerst den **neuen aktuellen HEAD** lesen, Versionskennung 0.1.53 aber nicht ohne echte Codeänderung künstlich erhöhen. Den Hand-off-Commit nicht als neuen UI-/HA-Abnahmecheckpoint ausgeben.
- Repo-Basisdokumente `README.md` und `docs/V2_ROADMAP.md` haben teils **historisch veraltete Vorbereitungsformulierungen** (V1.0.0). Der isolierte Testlaborstand ist 0.1.53; die Roadmap-Sicherheitsabfolge gilt dennoch verbindlich. Eine spätere kontrollierte Dokumentbereinigung ist sinnvoll, jedoch kein Anlass, die Laufzeit still als „FINAL“ auszugeben.
- Alle neuen echten Diagnose-/Testexporte nur in das zentrale private Archiv; die obigen Commit- und CI-Kennungen sind harmlose Metadaten und kein Export.

**Verbindlicher Prüfablauf für weitere Commits:**
1. Zulässigen Zweig sowie aktuellen HEAD prüfen, neue Dateien nur dort schreiben.
2. Kleines sachlich abgegrenztes Änderungspaket; bestehende V1-/DRA-Sicherheit nicht abschwächen.
3. Jeweilige statische/Python-/JS-Tests und Negativtests erweitern; nach Git-Commit **GitHub CI vollständig abwarten** und bei Fehlern Joblogs ansehen, beheben, erneut CI.
4. Versionsnummer bei **echtem neuen DEV-Funktionsstand** synchron in `const.py` und `manifest.json` erhöhen, die Dokumentation nachführen; bloße Übergabedokumentation braucht keine Versionsanhebung.
5. Bei nutzerrelevanter Oberfläche **separater HA-Realtest**, maximal eine konkrete HA-Handlung je Antwort. Keine eigenständige HA-Installation/Neustartannahme.
6. Vor Änderungsfreigabe festhalten, was **implementiert**, was nur **Konzept/UI**, was **CI-abgenommen**, was **HA-abgenommen** ist. Änderungen in falschem Repo strikt unterlassen.

## 7. Empfohlene nächste Arbeitsreihenfolge im neuen Chat

### A. Kurzer Übergabe- und Realitätsabgleich
- Globalen Bootstrap und diese Datei lesen.
- Aktuellen Featurezweig/HEAD/CI prüfen, keine verdeckten Weiterentwicklungen annehmen.
- Über die 0.1.53-Oberfläche sprechen, ggf. Android-Screenshot/Einzelrealtest entgegennehmen; in der Zwischenzeit ohne unnötige Rückfragen sicherheitsrelevante Dokumentation/Tests kontrollieren.
- Das hier bestätigte UX-Konzept **nicht** wieder auf vier getrennte Aktionstasten zurückbauen.

### B. Danach fachlichen sicheren V2-Kern statt weiterer unnötiger Oberflächen-Umbauten planen/entwickeln
1. Quell- und Zielbesitzvertrag je Projekt, robustes Preflight inklusive SHA-, Schreibziel-, Restplatz-, Berechtigungs- und Kollisionsprüfung.
2. Vollständiges serverseitiges persistentes Jobmodell, Journal, Wiederverbindungs-/Abbruchsemantik und geregelte Parallelität (Lese- und Schreibpfade getrennt, begrenzter Ressourcenverbrauch).
3. **Echte vollständige V2-eigene Backup-Erstellung** vor jeder Mutation, unabhängige Hash-/Byteprüfung, sichere Restore-/Rollback-Prozedur; erst danach UI-Backupinventar und Lösch-/Aufbewahrungsfunktionen.
4. Explizite Admin-/Sicherheitsfreigabe für Schritt 2, echter sicherer, protokollierter Installationslauf für Schritt 3, anschließend nach Plan bedingter Neustart/Frontend-Neuladen + erneute Sicherung des Erfolgs für Schritt 4. Keine automatisierte Mehrfachbestätigung.
5. Erst nach einzelner transaktionaler Freigabe Sammelupdate mit allen aktivierten Projekten, echter Quellvorschau pro Projekt und begrenztem parallelem Lauf; Ziel-/Datenkonflikte strikt serialisieren; Reihenfolge und Selbstupdate zuletzt beachten.
6. Negative Testfälle, Ressourcen-/Android-Realabnahme, Sicherheitsreview und ausdrücklich separate Releaseentscheidung.

**Wenn ein Implementierungsgate noch nicht erfüllt ist:** Nicht einfach zum roten Installationsknopf springen. Den nächsten fehlenden Vertrag mit Tests schließen und offen dokumentieren.

## 8. Benutzerentscheidungen und Stil, die nicht erneut diskutiert werden müssen

- **DRA V2 soll V1 funktional übernehmen**, nicht neu erfunden werden; V2 stellt Verbesserungen bei Bedienung, Stabilität, Auftragsmodell und paralleler Bearbeitung bereit.
- Smartphone-Bedienung ist gleichberechtigt und muss sauber funktionieren; iPad/Desktop nutzen Platz sinnvoll. Metallische Schaltflächen, sichtbarer Druckzustand, konsistente Größe, klarer Farbstatus, kompakte Dialoge statt langer „Tapeten“.
- Eine einzige große Schaltfläche auf derselben Tipp-Position soll später alle vier Deployment-Phasen übernehmen; der **schmale DRA-V1-Ladebalken als Trennlinie** und die vier Prozessfelder darunter sind ausdrücklich gewünscht.
- GitHub-Token-Endung mit **letzten fünf grünen Zeichen** anzeigen, niemals vollständige Tokens zurückgeben. V2-Systemlesezugang und privater Diagnose-Git-Export sind strikt getrennte Credentials.
- Persönliche Projekt-Notizen und deklarierte Zugriffsart sind reine Metadaten, GitHub-Status nur nach echter Prüfung. Reihenfolge echter Projekte soll die spätere Sammelpriorität abbilden.
- Sammelupdate in Projektverwaltung und Hauptprojektwähler **frei verschiebbar**, gern an erster Stelle; aktiviert alle zuvor vorausgewählten aktiven Projekte als Gruppe.
- Backup entfernen: **kein Papierkorb**, sondern klare Löschaktion und **zweite Bestätigung „Wirklich löschen?“**, aber **erst mit echtem V2-Backupbesitz und Recovery**.
- Bedarf/Größen von Projekten, Backup-Speicher und geplanten Sicherungen nur aus echten sicher ermittelten Daten; keine erfundenen Zahlen.
- Eine nach Installation angebotene HA-Neustartaktion erfordert eine zusätzliche Sicherheitsabfrage und darf nie still starten. Abhängig von Installationsart differenzieren.
- Benutzer erwartet, dass Repo-Arbeit **direkt durch tatsächlich verfügbare GitHub-Werkzeuge** erfolgt, nicht grundlos an einen anderen Chat delegiert wird. Zugriffsrechte zuerst real prüfen, nicht pauschal verneinen.

## 9. Minimaler Übergabe-Abnahmesatz für den nächsten Chat

> **DRA V2 DEV 0.1.53, Featurezweig `feature/v2-10-inventory-operation-contract`.** Einzige Deployment-Schaltfläche mit vier Statusschritten + originaler DRA-V1-Ladebewegung ist CI-geprüft, Android-Realtest ausstehend. Echte schreibgeschützte Einzelquellvorschau vorhanden. Nach erfolgreicher Vorschau bleibt Schreibfreigabe **orange, aber gesperrt**; Gruppenidentitätsvorschau bleibt Phase 1. Es existieren **keine** echten V2-Installationen, vollständigen V2-Backups, Restore-/Rollback-Jobs oder parallel installierenden Sammelaufträge. **Nur Featurezweig ändern; V1, V2-PUB, V2-main, WeatherRouter und privates Exportarchiv nicht anfassen.** Neue echte Diagnoseexporte ausschließlich in `TheDaimos/Project-Log-And-Export`. **Nächster Schwerpunkt: sichere serverseitige V2-Auftrags-/Sicherungs-/Installationsarchitektur und gezielte HA-Abnahme, nicht erneute freie UI-Neukonzeption.**

---

**Ende des dauerhaft abgelegten Übergabestands.** Keine sensiblen Daten, Tokens, Diagnose-JSONs oder privaten Exportinhalte in diesem Dokument.

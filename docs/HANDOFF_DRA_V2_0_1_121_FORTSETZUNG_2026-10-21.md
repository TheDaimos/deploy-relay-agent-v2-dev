# Verbindliche Chatübergabe – DRA V2 DEV 0.1.121 / Sammelupdate, Einzel-Selbstupdate und HA-Realabnahme

**Stand:** 21.10.2026  
**Projekt:** Deploy Relay Agent V2 – DRA V2 DEV / Testlabor  
**Privates GitHub-Repository:** `TheDaimos/deploy-relay-agent-v2-dev`  
**Ausschließlich zu beschreibender Zweig:** `feature/v2-10-inventory-operation-contract`  
**Aktueller verifizierter GitHub-HEAD vor dieser Übergabe:** `02a854d6f029d5274c69cb7fb3d71dd7dd967862`  
**GitHub-Version:** `0.1.121 DEV` (laut `const.py`)  
**Letzter erfolgreicher GitHub-Actions-Lauf:** `39582265521`, `completed/success`, auf `02a854d6...`  
**Letzter ausdrücklich in aktueller GitHub-Dokumentation als Anwender-Screenshot bestätigter HA-Stand:** `0.1.120 DEV`, Frontend = Python.  
**0.1.121 auf HA installiert?** Nicht nachgewiesen.  
**0.1.121 Selbstupdate auf HA realabgenommen?** Nein.  
**Charakter dieser Übergabe:** Verbindliche Fortsetzungsunterlage, keine behauptete Produktivfreigabe.

## 1. Verbindlicher Einstieg im nächsten Chat

Zuerst den tatsächlichen neuen Branch-HEAD samt CI und folgende Originaldateien **vollständig** aus GitHub lesen, nicht nur die Zusammenfassungen:

1. `docs/DRA_V2_0_1_121_EINZEL_SELBSTUPDATE_BATCH_VERTRAG_QUELLPRUEFUNG_2026-10-21.md`
2. `docs/HANDOFF_DRA_V2_0_1_109_SAMMELUPDATE_DIAGNOSE_REALABNAHME_2026-10-20.md`
3. `docs/HANDOFF_DRA_V2_0_1_99_GERAETEUEBERGREIFENDE_INSTALLATION_2026-10-16.md`
4. `docs/DRA_V2_0_1_107_SAMMELABLAUF_UND_WR_QUELLE_2026-10-17.md`
5. `docs/DRA_V2_0_1_105_QUELLEN_UND_SAMMELAUSWAHL_2026-10-17.md`
6. `docs/DRA_V2_0_1_104_BATCH_UND_NEUSTART_2026-10-16.md`

Zusätzlich die aktuelle Implementierung in `batch_installation.py`, `batch_version_summary.py`, `server_deployment_jobs.py`, `deployment_coordinator.py`, `remote_source.py`, `websocket_api.py`, `frontend/lab.js`, `project_catalog.py` und zugehörige Tests lesen. Zuletzt erneut Branch-HEAD und CI prüfen. Keine veraltete Version aus einer früheren Chatphase als aktuellen Codezustand behandeln.

## 2. Zielbild und unabänderliche Sicherheitsanforderungen

DRA V2 soll DRA V1 mindestens funktional ersetzen und dessen bewährte Engine wiederverwenden. Home Assistant ist der **einzige ausführende Server**. Desktop, Android und iPad sind lediglich Bedienungs-/Beobachtungsoberflächen. Aufträge müssen nach Browserwechsel und Sitzungsübernahme auf HA bestehen bleiben. Keine Vervielfältigung der V1-Deployment-Engine.

**Kein Installationsstart ohne** geprüfte festgelegte Git-Commits, verifizierte Zielpfade, V1-Sicherung/Journal, serverseitig gebundene einmalige Freigabe, ausdrückliche Benutzerbestätigung und unverändert gültigen Plan-Digest. Bei unklarer WebSocket-Antwort keinen zweiten Start blind senden.

**Repositorygrenzen:** Nur DRA-V2-Featurezweig ändern, keine Änderungen an DRA V1, Gewitterradar, WeatherRouter, dessen privaten Extensions, `main` oder produktiven Integrationen ohne neue ausdrückliche Freigabe. GitHub-Tokens und andere Geheimnisse nie protokollieren. Zentrales privates Diagnosearchiv: `TheDaimos/Project-Log-And-Export`; keine privaten Exporte in öffentliche oder andere Repositories.

## 3. Konkrete Nutzermeldungen und praktische Befunde

### A – Das isolierte Testprojekt und Gerätewechsel

Beim Test-Repository `TheDaimos/Test-Repo-DRA-V2` wurden per +/- sechs synthetische Testdateien vorbereitet (z.B. je 20 Sekunden künstliche Wartezeit). Praktisch nachgewiesen: Git-Teststand 10 → 11, Commit `aab81bfe374d`; fünf neue Dateien und eine geänderte Statusdatei. Ein HA-Auftrag war geräteübergreifend als `running/preflight` zu sehen, mit Kennung `f89fbdf74bd149c990975f6ffb50d57d`. Android steuerte und Desktop beobachtete. **Das beweist keine abgeschlossene Installation.** Früherer GR-Installationsstart über Android war nicht erfolgreich bestätigt; der Nutzer installierte GR damals über DRA V1.

### B – 0.1.108 scheitert bei sechs ausgewählten Sammelprojekten

Auf Nutzerscreenshots: HA-Python und Oberfläche beide `0.1.108`. Das Sammelupdate hatte angehakt: DRA V1, DRA V2, Gewitterradar, WeatherRouter, WeatherRouter Private Extensions, Test-Repo-DRA-V2. Haupttaste `1/4 · Sammelinstallation prüfen und vorbereiten` führte zu **„Quell- oder Manifestprüfung fehlgeschlagen. Keine Installation gestartet.“** Betroffenes Projekt und echte Fehlerklasse waren für den Nutzer nicht erkennbar. Nutzer konnte ausdrücklich **keinen Logexport anbieten**. Keine Installation der sechs Projekte nachgewiesen.

DRA V1 zeigte bei einer anderen Sammelauswahl erfolgreich echte Änderungen: GR zehn Dateien, WR sieben Dateien; V1 arbeitet schneller und zuverlässig. Dieser V1-Befund beweist nicht, welches der sechs V2-Projekte scheiterte.

### C – WeatherRouter-Quelle

Mehrfaches Problem: DRA V2 verwendet/zeigt für `TheDaimos/weather-router-dev` irreführend `main`. WeatherRouter veröffentlicht eine ausdrückliche Empfehlung `deploy/dev` in `deploy-relay-channel.json`. Bereits implementierte Korrekturen trennen vorläufige Standardreferenz von bewusster manueller Wahl und von älterer serverseitiger `main`-Vorbereitung. **Nicht ohne erneuten HA-Einzel- und Sammelrealtest behaupten, dass die praktischen Fehler vollständig erledigt sind.**

### D – Bedienung des Sammelupdates

Wiederholt bei Stufe 1 stecken geblieben, große Haupttaste führte zunächst nur zum schreibgeschützten `batch/preview` statt zur echten `batch/prepare`-Vorbereitung. In 0.1.107 korrigiert und CI-getestet. Der separate schlecht sichtbare Vorbereitungsbutton wurde als konkurrierender Weg entfernt. Checkboxen pro Lauf, Aufklappzustand und geräteübergreifende Beobachtung sind implementiert. Automatische Statusaktualisierung darf Auswahl, Scrollposition und Öffnungszustand nicht zerstören.

### E – Verbindliche tabellarische Freigabe aus Nutzeranforderung

Vor dem tatsächlichen Installationsstart muss eine **eigene, gut lesbare tabellarische Prüfübersicht** für sämtliche ausgewählten Projekte erscheinen. Spalten: Projekt, **installierte Version**, **neue Version**, **vollständiger 40-stelliger Commit**, **ausgewählte Ref/Branch**, Dateiänderungen/Status. Beispielwerte des Nutzers waren illustrative Versionswerte, keine tatsächlichen GR-Feststellungen. Versionsangaben nicht erfinden. Bei fehlendem oder widersprüchlichem Versionsnachweis `Nicht ermittelbar` anzeigen.

In 0.1.108 und Folgeständen: Versionen aus geprüften V1-Inventar-/Markerangaben, lokale Hashprüfung, tabellarisches Zwischenfenster mit mobiler horizontaler Scrollbarkeit, `review_digest` über unveränderliche Projekteinträge, aktive Bestätigungs-Checkbox, getrennte endgültige Startbestätigung und serverseitiger Digest-Abgleich. Besonders überprüfen, ob der gesamte Zwischenfenstervertrag mit den tatsächlich gelesenen HA-Daten konsistent ist. Keine Freigabe allein aufgrund der Browseroberfläche.

## 4. Aktuell jüngster Entwicklungsblock 0.1.121 DEV

Die vollständige Primärquelle ist `docs/DRA_V2_0_1_121_EINZEL_SELBSTUPDATE_BATCH_VERTRAG_QUELLPRUEFUNG_2026-10-21.md`.

DRA V1 kann sich innerhalb eines Sammelupdates selbst aktualisieren. DRA V2 darf ebenfalls am Sammelupdate teilnehmen; serverseitige Reihenfolge: gewöhnliche Projekte → DRA V1 → DRA V2 **immer zuletzt**. Das V2-Selbstupdate benötigt eine explizite Auswahl, den exakten eigenen Zielpfad `custom_components/deploy_relay_v2_dev`, verifizierten Manifest-/Neustartvertrag und ein exklusives Schreibfenster.

**Neue Funktion 0.1.121:** `DRA V2 einzeln prüfen und aktualisieren` im Einzelprojektmodus. Keine zweite Engine, keine Freischaltung des gesperrten direkten Eigenupdatepfads; stattdessen dasselbe sichere `batch/prepare`-/`batch/start`-Verfahren mit **genau einem Repository**. Vorbereitete/running/inspecting Sammelaufträge werden nicht überspielt; eine parallele Quelle wird nicht gegen den HA-Scan-Lock gestartet. Benutzer muss Quellen, Commit, Tabelle, Digest und Installation weiterhin separat bestätigen. Danach HA-Neustart vormerken, nicht eigenständig auslösen.

Dokumentierter Code-/Testcommit `0ea12702c5e689f70e52308e8dacea1cd39c6b68`, GitHub Actions `39582019041` erfolgreich. Nachfolgender Dokumentationscommit als geprüfter aktueller HEAD `02a854d6f029d5274c69cb7fb3d71dd7dd967862` mit GitHub Actions `39582265521`, ebenfalls `success`.

**Wichtig:** 0.1.121 wurde nicht real auf HA installiert oder als Selbstupdate durchgeführt. Der Nutzer hatte zuvor auf Screenshot 0.1.120 mit übereinstimmender Frontend-/Python-Version. Ein zur Zeit jener Diagnose parallel laufender HA-Sammelauftrag befand sich bei `preparing`, `0 von 5 Quellen geprüft`; deshalb ist fehlende parallele Einzelquellenprüfung noch kein nachgewiesener neuer GitHub-Fehler.

## 5. Was bereits entwickelt ist – nicht doppelt implementieren

- V1-basierte serverseitige Einzelinstallation mit Sicherung, Journal, Verifikation, Rückfall und Hashprüfung.
- Geräteübergreifender Installationsstatus, bestätigte Übernahme und HA-eigene Auftragskennung.
- Variable Testdateianzahl und einstellbare Testverzögerung pro Datei.
- Servereigener sequenzieller Sammelauftrag (maximal acht aktive Projekte), sichere Quell-/Ziel-/Commit-Festlegung, Abbruch weiterer Teilinstallationen bei einem Fehler.
- Einmalige Sammellaufauswahl per Kontrollkästchen ohne Änderung gespeicherter Standardauswahl.
- DRA-V1-/DRA-V2-Selbstupdate-Reihenfolge mit V2 zuletzt, exklusive V2-Schreibphase.
- HA-Neustartvormerkung und ausdrücklich bestätigter gemeinsamer Neustart nach unabhängigen Installationen.
- Großschaltfläche zum wirklichen Beginn der Batchvorbereitung statt bloßem Vorschauzyklus.
- Quellenempfehlung `deploy/dev`, sofern der Benutzer `main` nicht bewusst manuell gewählt hat.
- Projekt-/Fehlerphasenanzeige für `inspecting_sources`, `source_reference`, `manifest`, `inventory`, `local_comparison`, `version_detection`, `batch_planning`, `preparing`, `failed`.
- Tabellarische verbindliche Versions-, Commit- und Ref-Prüfübersicht mit Digest.
- Neue abgesicherte DRA-V2-Einzel-Selbstaktualisierung über Ein-Projekt-Batch in 0.1.121.

## 6. Was noch offen ist / Priorität

**P1 – Wirkliche HA-Realabnahme von 0.1.121 statt weiterer kosmetischer Versionen.** Vorher den tatsächlich laufenden/vorbereiteten HA-Sammelstatus prüfen und nicht versehentlich eine laufende Vorbereitung überschreiben. Nach Zustimmung des Nutzers den aktuellen Kandidaten über bewährten DRA-V1-Weg installieren, dann Frontend-/Python-Stand vergleichen.

**P1 – Sammelupdate:** Nur mit absichtlich begrenzter, kontrollierter Projektauswahl Quellprüfung starten. Pro Projekt Git-Referenz/40-stelligen Commit, installierte und neue Version, Dateiänderungen und Prüfübersicht prüfen. Bei Fehlern muss HA den auslösenden Projektschritt sichtbar liefern, auch ohne Logexport. Keine ungeprüfte Sammelinstallation echter GR-/WR-Projekte.

**P1 – WeatherRouter:** Einzel- und Sammelmodus müssen bei automatischer Wahl den tatsächlich empfohlenen `deploy/dev` nachweisen. `main` nur bei ausdrücklicher Benutzerwahl. Unveränderliche Quellbindung vor Start auf HA verifizieren.

**P1 – Gerätewechsel:** Desktop → Android → iPad/Notebook, dieselbe HA-Auftragskennung und derselbe serverseitige Fortschritt, keine doppelten Startanfragen. Abschließenden Status, installierte Dateien und V1-Journal tatsächlich überprüfen.

**P1 – Selbstupdate:** DRA V2 als einziges Projekt vorbereiten; negative Fälle (fehlende Prüfübersicht, anderer Digest, konkurrierender Sammelauftrag) prüfen. Reales V2-Selbstupdate und HA-Neustart erst nach ausdrücklicher Zustimmung und ausreichender Diagnose-/Rückfallmöglichkeit.

**P2 – Neustartbündelung:** Unabhängige Einzelupdates nacheinander dürfen bis zum nötigen gemeinsamen HA-Neustart möglich bleiben; Abhängigkeiten zwischen WR/GR müssen fachlich berücksichtigt werden. Keine automatische globale Rollback-Behauptung. Neustartvormerkung bisher HA-laufzeitgebunden, nicht nach jedem Integration-Reload garantiert.

**P2 – Bedienqualität:** Aufgeklappte Auswahl, Scrollposition und Farb-/Schrittzustände auf Desktop, Android, iPad konsistent halten. Die Haupttaste muss alle Schritte führen; niemals eine wirksame Schaltfläche so verstecken, dass der Ablauf scheinbar hängt.

## 7. Entwicklungs- und Testdisziplin

- Vor einer Änderung den aktuellen GitHub-Code gegen die tatsächlichen Nutzerfehler vergleichen. Nur belegte Regressionen beheben.
- Positive und negative Testfälle, insbesondere Abbruch, Token-/Manifestfehler, Quelllock, falscher Commit, verweigerte/sich wiederholende Startbestätigung, veralteter Digest, Selbstupdate-Konkurrenz.
- Keine Versprechen von Hintergrundarbeit ohne tatsächlich gestartete Automation; kein stillschweigender HA-Zugriff ohne einen real vorhandenen Zugriff.
- Änderungen bündeln statt viele einzelne HA-Installationen verlangen.
- CI-ID und exakten getesteten Commit angeben. CI nicht als Realabnahme ausgeben.
- Vollständigen technischen Entwicklungs-/Abnahmebericht als echte Markdown-Datei im selben GitHub-Featurezweig speichern, committen, erneut über GitHub lesen und dann einen echten Direktlink bereitstellen.
- Nutzer arbeitet allein: nicht von „eurem Team“ oder „ihr“ sprechen; auf Deutsch ohne unnötiges Denglisch.

## 8. Verbindlicher Startprompt für den nächsten Chat

> **Bootstrap Daimos – DRA V2 DEV Fortsetzung ab 0.1.121**
>
> Öffne zuerst vollständig `TheDaimos/deploy-relay-agent-v2-dev@feature/v2-10-inventory-operation-contract`, insbesondere `docs/HANDOFF_DRA_V2_0_1_121_FORTSETZUNG_2026-10-21.md`, die darin genannten Originalberichte und den aktuellen GitHub-HEAD samt Actions. Beachte ausdrücklich: GitHub 0.1.121, Actions 39582265521 SUCCESS; letzter dokumentierter HA-Screenshot 0.1.120; keine 0.1.121-HA-Realabnahme. Prüfe eigenständig alle verbleibenden Kernprobleme der Sammelinstallation, WeatherRouter-Quellwahl `deploy/dev`, verbindlichen tabellarischen Versions-/Ref-/Commit-Freigabe, geräteübergreifenden HA-Ausführung und des neuen gesicherten Ein-Projekt-Selbstupdates. Ändere ausschließlich den vorhandenen Featurezweig; DRA V1 und andere Repositories nicht verändern. Prüfe Sicherheits-/Negativfälle und CI, und fordere nur die unbedingt notwendigen gezielten HA-Realtests. Halte einen laufenden HA-Auftrag unangetastet und starte niemals ohne ausdrückliche Freigabe. Dokumentiere alle Ergebnisse als vollständige GitHub-Markdown-Datei und verifiziere den Rückleseinhalt.

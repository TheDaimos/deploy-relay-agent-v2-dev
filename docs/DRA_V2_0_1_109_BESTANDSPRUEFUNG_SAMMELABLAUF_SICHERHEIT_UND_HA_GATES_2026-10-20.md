# DRA V2 0.1.109 DEV – Bestandsprüfung, Sammelablauf und offene HA-Nachweise

**Datum:** 20.10.2026  
**Repository/Zweig:** `TheDaimos/deploy-relay-agent-v2-dev` / `feature/v2-10-inventory-operation-contract`  
**Ausgangs-HEAD:** `f3d4a74105cbbe768678852b985a2fcdc5bd0190`  
**Code-Basiscommit 0.1.109:** `c80c126af5f4df5fee204701f3296c7a9ca02fe5`  
**CI Code-Basis:** 39388573164 – SUCCESS  
**CI HEAD:** 39399949568 – SUCCESS  
**Zuletzt durch Anwender belegte HA-Laufzeit:** 0.1.108; 0.1.109 auf HA **nicht** nachgewiesen.

## 1. Geprüfte Ausgangslage

Die verbindliche Übergabe `docs/HANDOFF_DRA_V2_0_1_109_SAMMELUPDATE_DIAGNOSE_REALABNAHME_2026-10-20.md` und der vorangegangene technische Fehlerbericht `docs/DRA_V2_0_1_109_SAMMELUPDATE_QUELLFEHLER_DIAGNOSE_2026-10-20.md` wurden vollständig gelesen. Zusätzlich wurden der gegenwärtige Zweig, die Actions-Läufe und relevante Implementierungen in `websocket_api.py`, `batch_installation.py`, `frontend/lab.js` und `tests/test_v2_batch_installation.py` untersucht. Die ursprüngliche Korrektur wird **nicht erneut implementiert**.

Der nachgewiesene Fehler in 0.1.108 war die fehlende Zuordnung des Quellabbruches zu einem Projekt während des frühen GitHub-Referenzabgleichs. In 0.1.109 wird vor jeder Quellenabfrage `source_inspection_started(project_id)` aufgerufen. Der schreibende HA-Prozess stellt über seinen lesbaren Sammelstatus `inspecting_sources`, `project_key`, `check_stage` und bei Abbruch `failed`, `error_code` sowie ausschließlich zulässige `error_detail` bereit. Oberfläche und WebSocket-Fehlerantwort nutzen diese Angaben. Die Anzeige benötigt **keinen Git- oder Logexport**.

**Wichtig:** Das tatsächliche Fehlerprojekt unter den sechs auf HA ausgewählten Repositories ist damit nicht bewiesen. Es wäre unzulässig, anhand der älteren Screenshots ein bestimmtes privates Repo oder ein Token als Ursache festzulegen.

## 2. Nachvollzogene Sicherheits- und Ablaufverträge

| Prüffeld | Auf Codeebene festgestellt | Grenze |
|---|---|---|
| Frühe Quellfehler | Projekt-/Phasenstatus noch vor `BatchDeployment.prepare()` | Ursache auf HA erst nach dortigem Durchlauf beweisbar |
| Sichere Fehlertexte | Zulässigkeitsliste für 401/403/404/429, Empfehlung/Quellenformat; unbekannte Rohfehler verworfen | Keine Token- oder Antwortkörperausgabe |
| HA als Ausführer | Die Oberfläche fragt an; Planung, Freigabestatus und Einzelaufträge liegen serverseitig | Kein HA-Auftrag durch diese Repository-Prüfung gestartet |
| Versions-/Commit-Prüfübersicht | `review_digest` bindet Repository, Projekt, Ref, vollständigen Commit, Versionsfelder und Änderungszahlen | Nachweis der real angezeigten Tabelle auf HA offen |
| Startschutz | `challenge`, Eigentümerkennung, `confirm`, `review_confirm` und `review_digest` erforderlich | Gerätewechsel/Quittungsverlust real zu prüfen |
| Selbstupdates | V1 vor V2; V2 letzter Schreibauftrag, Identitäts-/Zielschutz | Echter Selbstupdate-Erfolg nicht belegt |
| Teilfehler | Folgeinstallationen stoppen; vorherige Teil-Erfolge bleiben erhalten | Journal/Datensicherung/Rückfall auf HA konkret zu prüfen |
| Neustart | Gemeinsame HA-seitige Neustart-Vormerkung vorgesehen | Neustart und Persistenz nicht real bestätigt |
| Gerätewechsel | HA-seitiger Status abrufbar, Übernahme mit ausdrücklicher Bestätigung | Desktop/Android/iPad-Ende-zu-Ende offen |

Der vorhandene Regressionstestbestand enthält insbesondere Fälle für sichere frühe Referenzfehler, unbekannte Fehlertexte, vorbereitete Freigaben gegen konkurrierende Quellenprüfung, Prüfsummenbindung, Stopp nach Teilausfall, Eigentümerwechsel, Zielüberschneidungen und Selbstupdate-Sortierung. CI wurde anhand der GitHub-Ergebnisse verifiziert; **diese Prüfung ist keine eigenständig durchgeführte lokale Testausführung und keine HA-Realabnahme**.

## 3. WeatherRouter: getrennte Quellregel

Das Ziel `deploy/dev` ist laut Übergabe ausdrücklich die empfohlene WeatherRouter-Quelle. Der aktuelle Sammelweg ermittelt Empfehlungen in `inspect_source_choices` serverseitig und verwendet die dort zurückgegebene feste Ref samt Commit. **Ob die tatsächlich auf der HA-Instanz ausgegebene Ref für WeatherRouter `deploy/dev` ist, bleibt bis zum HA-Vorbereitungsergebnis offen.** Nicht allein aus dem Code oder einem `main`-Standardzweig auf den real verwendeten Ref schließen.

**Freigabeprüfung:** In der Prüftabelle muss für WeatherRouter das gewünschte `deploy/dev` mit vollständig gebundenem 40-Zeichen-Commit erscheinen, sofern kein abweichender Ref ausdrücklich manuell gewählt wurde. Stimmt dies nicht, **keinen Sammelstart bestätigen**; die konkrete Quellenherkunft und eine möglicherweise ältere HA-Vorbereitung klären.

## 4. Verbleibender verpflichtender Ablauf: zuerst nur vorbereiten

1. V0.1.109 gezielt über den bereits bewährten DRA-V1-Weg auf HA DEV installieren; die tatsächliche Python-Laufzeit **und** die geladene Oberfläche danach unabhängig bestätigen. Diese Handlung wurde hier nicht ausgeführt.
2. Die sechs bisherigen Projekte auswählen und ausschließlich `1/4 · Sammelinstallation prüfen und vorbereiten` ausführen. **Keine Installation freigeben.**
3. Bei Fehler die auf derselben Oberfläche sichtbaren Werte **Projekt**, **Prüfschritt**, **Fehlerkategorie** und ggf. **Weitere Eingrenzung** sichern (Bildschirmaufnahme reicht; kein Logexport nötig). Einen Quellzugriffsfehler nur beim dort benannten Projekt beheben.
4. Bei erfolgreicher Vorbereitung die vollständige Projekt-/Versions-/Commit-/Ref-Tabelle und alle Änderungszahlen überprüfen. Besonders `deploy/dev` für WeatherRouter und die Selbstupdate-Reihenfolge prüfen. Falls ein Versionsmarker unbekannt ist, darf keine Version erfunden werden.
5. Erst nach dokumentiert erfolgreichem reinen Vorlauf einen **gesondert bestätigten** isolierten Test mit dem Test-Repository auf HA DEV durchführen; Anfangsquittung, einmalige Auftragskennung, Zwischenstatus, Verifikation, V1-Journal und Abschluss tatsächlich korrelieren.
6. Negativtest: Quellenfehler ohne Installationsstart, verweigerte/alte Freigabe, Browserwechsel mit/ohne Übernahme, unterbrochene Transaktion, Teilausfall ohne Start späterer Projekte, unerreichbarer Quellref und Neustart-Sperre.
7. Danach erst einen genehmigten, geräteübergreifenden Sechs-Projekt-Lauf planen; DRA V2 als letzte Teilinstallation und gemeinsamer Neustart brauchen zusätzliche konkrete HA-Belege.

## 5. Ergebnis und Freigabestatus

**Repository-Bestandsprüfung:** durchgeführt.  
**0.1.109-Quellfehlerdiagnose:** im geprüften Code vorhanden.  
**GitHub Actions:** geprüfter Code-Basislauf und Zweig-HEAD-Lauf erfolgreich.  
**Neue Programmkorrektur:** keine; bei der statischen Prüfung keine weitere sichere Fehlerursache nachgewiesen, die ohne HA-Befund sachlich gerechtfertigt wäre.  
**Installation/Sechs-Projekt-Sammellauf/Selbstupdate/Neustart auf HA:** **nicht geprüft, nicht freigegeben, nicht als erfolgreich behauptet**.  
**DRA V1, WeatherRouter, Gewitterradar, andere Repositories:** unverändert.

Keine zweite HA-Installation bei unklarer Quittung. Keine Abschwächung der Quell-, Manifest-, Sicherheits- oder Eigentümerprüfungen. Die nächste wirksame Diagnose erfolgt über die in 0.1.109 bereits eingebaute Oberflächenanzeige beim **reinen HA-Vorbereitungslauf**.

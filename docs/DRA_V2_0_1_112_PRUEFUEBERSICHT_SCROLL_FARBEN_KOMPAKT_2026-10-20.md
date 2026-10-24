# DRA V2 0.1.112 DEV – Prüfübersicht, Scrollposition und farbige Änderungszahlen

**Datum:** 20.10.2026  
**Repository:** `TheDaimos/deploy-relay-agent-v2-dev`  
**Entwicklungszweig:** ausschließlich `feature/v2-10-inventory-operation-contract`  
**Letzte durch Screenshot bestätigte HA-Laufzeit:** V0.1.111 DEV (Prüfübersicht erreicht); 0.1.112 auf Home Assistant **nicht** nachgewiesen.

## 1. Verifizierter Anwenderbefund

Die sechsfach vorbereitete Sammelauswahl kann inzwischen das verbindliche Prüffenster erreichen. Die auf dem Notebook sichtbare Tabelle verfügt über die erforderlichen Felder `Projekt`, `Installierte Version`, `Neue Version`, vollständige Commitkennung, Ref und Dateiänderungen. Der Nutzer hat beim horizontalen Scrollen nach rechts reproduzierbar beobachtet, dass sich die Tabelle nach ungefähr drei Sekunden wieder nach links ausrichtet. Außerdem verbreiterte der Zusatztext „Version nicht vollständig nachgewiesen“ die Versionszellen unnötig. Die Änderungsangaben waren monochrom und schlecht zu überfliegen.

## 2. Implementierte Korrekturen

- **Wiederherstellung der Scrollposition:** `frontend/lab.js::_render()` liest die aktuelle `scrollLeft`-Position von `.dra-batch-review-table-wrap` unmittelbar vor dem DOM-Neuaufbau und setzt sie auf dem neu erstellten Scrollbereich zurück. Dies betrifft die sichtbare Tabelle bei der regelmäßigen HA-Statusaktualisierung. Die zu prüfenden Daten, freigegebenen Commits und die Prüfsummenbindung werden nicht verändert.
- **Kompakte Versionsangaben:** Die Tabelle zeigt bei fehlendem Versionsnachweis ausschließlich **„Nicht ermittelbar“**, ohne den breiten zusätzlichen Erklärungstext pro Zeile. Der übergeordnete allgemeine Warnhinweis bleibt bestehen, und eine Versionsnummer wird weiterhin nicht erfunden.
- **Farben für Änderungszahlen:** Nur Werte ungleich null werden hervorgehoben: `+N` grün, `−N` rot, `~N` goldgelb für veränderte Dateien. Nullwerte behalten die Grundfarbe und nehmen dadurch keine zusätzliche Aufmerksamkeit in Anspruch. „Aktuell – keine Installation“ bleibt textlich erkennbar.
- **Versionseinheit:** Python-Laufzeit, Manifest und Oberflächenkennung sind auf **0.1.112 DEV** abgeglichen.
- **Regressionstests:** `tests/test_v2_batch_run_selection_contract.py` prüft das Scrollpositions-Sichern/-Wiederherstellen, das Fehlen des Versions-Zusatztexts und die bedingte farbliche Kennzeichnung. Die bestehenden `tests/test_v2_countdown.js`-Versionserwartungen wurden auf 0.1.112 umgestellt.

## 3. Änderungsnachweise

- Erste Änderung des Scroll- und Versionsbereichs: `dd6f4ea342e33b675c72a2049c5f87ca60a98a0f`
- Kompakte Versionseinträge: `be5fbbc5890b711fcabfade4deba1e29c18a18ba`
- Synchronisierung der Version und Testvorgaben: nachfolgende Commits im selben Entwicklungszweig
- Tatsächliche farbige Tabellenwerte: `fac9c2954f078b5d182e7af10488709c827d9540`
- Ergänzter Testschutz: `92acdf552863feee1cfe20bef1c0527cb115bbeb`

Die Codeänderungen wurden in GitHub geschrieben. Für die **endgültige CI-Bewertung zählt nur** der vollständige GitHub-Prüflauf auf dem letzten Testcommit, nicht ein erfolgreicher Lauf auf einem älteren Zwischenstand.

## 4. Grenzen und nächster HA-Realtest

**Keine Installation und keine Sammelinstallation wurden durch diese Änderung ausgeführt.** DRA V1, Gewitterradar, WeatherRouter und die privaten Erweiterungen wurden nicht verändert.

Nach vollständigem CI-Erfolg darf 0.1.112 nur kontrolliert über den bisherigen V1-Installationsweg auf HA DEV geprüft werden. Danach zunächst nur die sechsfach vorbereitete Prüfübersicht öffnen und **keine Sammelinstallation bestätigen**. Den Tabellenbereich nach rechts verschieben, mindestens zwei Statusaktualisierungen abwarten und überprüfen, ob die Position erhalten bleibt. Anschließend Darstellung auf Notebook, iPad und schmalem Bildschirm sowie die Farbwerte und den unveränderten vollständigen 40-stelligen Commit abnehmen. WeatherRouter-`deploy/dev` und Selbstupdate-Reihenfolge müssen weiterhin unabhängig überprüft werden.

**GitHub-CI ≠ HA-Realabnahme.** Die endgültige Installations-, Neustart- und Selbstupdate-Freigabe bleibt ausstehend.

## 5. Abschließende GitHub-CI-Verifikation

Der vollständige GitHub-Actions-Prüflauf **39424958820** wurde auf dem maßgeblichen Programm-/Testcommit **`92acdf552863feee1cfe20bef1c0527cb115bbeb`** mit Status **completed / SUCCESS** verifiziert. Der nachfolgende Commit dieser Markdown-Dokumentation ändert keinen Programm- oder Testcode. Damit ist 0.1.112 ein CI-geprüfter Kandidat für eine **kontrollierte HA-DEV-Testinstallation**, aber keine erfolgreich realabgenommene Version.

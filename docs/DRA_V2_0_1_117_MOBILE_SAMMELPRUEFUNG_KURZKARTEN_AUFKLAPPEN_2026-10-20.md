# DRA V2 0.1.117 DEV – mobile Sammelprüfübersicht als kompakte Projektkarten

**Datum:** 20.10.2026  
**Repository:** `TheDaimos/deploy-relay-agent-v2-dev` (privat)  
**Entwicklungszweig:** ausschließlich `feature/v2-10-inventory-operation-contract`  
**Ausgangsstand auf den Anwenderbildern:** V0.1.116 DEV, Oberfläche und HA-Python übereinstimmend. Die vorbereitete Sammelprüfübersicht wurde erfolgreich von Desktop auf Smartphone übernommen; die Tabellenansicht war mobil nahezu unbenutzbar.

## 1. Anwenderbefund und verbindliche Darstellungsregel

Die vorgelegten Smartphone-Aufnahmen belegen, dass das bisherige, mindestens 810 CSS-Pixel breite Desktop-Raster auf schmalen Geräten nur teilweise sichtbar ist. Insbesondere neue Versionen, Referenzen und Commitkennungen wurden rechts abgeschnitten; Warnhinweis und Prüfkennung beanspruchten zusätzlichen Raum. Es handelt sich um ein Darstellungsproblem der bereits vorbereiteten serverseitigen Prüfübersicht, **nicht** um einen Fehler bei der eigentlichen Auftragsübernahme.

Der Nutzer hat deshalb eine konkrete Kurzübersicht vorgegeben:

- **Zunächst sichtbar:** Projekt, installierte Version → neue Version, Commitkennung mit **12 Zeichen** auf dem Smartphone.
- **Über einen Aufklapppfeil pro Projekt:** Repository, Git-Referenz, **vollständiger 40-Zeichen-Commit**, Status und farbige Dateiänderungen (hinzugefügt, geändert, entfernt).
- **Desktop/ausreichend breiter Bildschirm:** die bisherige vollständige tabellarische Prüfübersicht erhalten.
- **Sicherheitsvertrag:** verkürzte Commitkennungen sind ausschließlich Darstellung. Die vorbereiteten vollständigen Commits, `review_digest`, Einmal-Bestätigung, Geräteinhaberprüfung und der serverseitige Installationsvertrag bleiben unverändert.

## 2. Implementierte Änderungen

**`custom_components/deploy_relay_v2_dev/frontend/lab.js`**

- Neue `dra-batch-review-mobile-list` mit einem semantischen `details/summary`-Eintrag je Projekt.
- In der kompakten Zeile: Projektname, alter und neuer Versionswert mit Pfeil sowie ein eindeutig als `Commit` beschrifteter **12-Zeichen-Anfang**. Fehlende Versionen heißen unverändert ausschließlich `Nicht ermittelbar`.
- Nach Öffnen: tatsächliches Repository, festgehaltener Git-Ref, vollständiger 40-stelliger Commit, Installationsstatus und die Anzahl hinzugefügter (`+`, grün), geänderter (`~`, goldgelb) und entfernter (`−`, rot) Dateien. Nullwerte werden nicht farblich hervorgehoben.
- Eigene Schaltfläche `Vollständigen Commit kopieren` in der erweiterten Karte, mit Prüfung des 40-stelligen Hexadezimalformats und Fehlerbehandlung der Zwischenablage. Die volle Kennung bleibt im Text auswählbar.
- Für Ansichtsbreiten bis **900 CSS-Pixel** wird die breite Desktop-Tabelle ausgeblendet und stattdessen die mobile Kartenliste angezeigt. Breite Ansichten behalten die vollständige Desktop-Tabelle. Das Prüf- und Freigabefenster ist damit nicht auf eine horizontale Teilansicht beschränkt.
- Bei jeder automatischen HA-Aktualisierung merkt sich `_render()` die geöffneten Projektkarten über deren Projektkennungen und stellt den Zustand nach dem Neuaufbau wieder her. Die schon bestehenden vertikalen und horizontalen Scrollpositionsschutzmaßnahmen bleiben bestehen.
- Die vorhandenen Warnhinweise, die vollständige Prüfkennung, die verpflichtende Bestätigungs-Checkbox sowie die Schaltflächen zum Schließen, Verwerfen und gesonderten Installationsstart bleiben erhalten. Auf schmalen Geräten bleiben die Handlungsflächen responsiv; sie werden nicht ungefragt aktiviert.
- Frontend-Version **0.1.117**.

**`const.py` und `manifest.json`:** Versionsgleichheit auf **0.1.117 DEV**.

## 3. Regressionstests und GitHub-CI

- Erweiterter Python-Vertragstest in `tests/test_v2_batch_run_selection_contract.py` schützt Kurz-/Vollcommit, das mobile Aufklappmuster, den Erhalt geöffneter Karten, die mobile Medienregel und die bestehende Prüfkennungsbindung.
- Erweiterter echter JavaScript-Verhaltenstest in `tests/test_v2_countdown.js` erstellt eine vollständige Testvorbereitung, prüft Projektname, Versionspaar, 12-stelligen Kurzcommit, vollständigen Commit im Detailbereich, Kopierfunktion, Desktop-Tabelle und gesperrten Bestätigungsbutton. Ein simulierter Neuaufbau bestätigt, dass eine geöffnete Projektkarte geöffnet bleibt.
- Nach zwischenzeitlich fehlgeschlagenen, reparierten Testdatei-Prüfungen wurde der vollständige GitHub-Actions-Lauf **`39436315501`** auf dem maßgeblichen Programm-/Testcommit **`19f47755aac6bce020d933e18fd44a5f11276acf`** mit **`completed / SUCCESS`** verifiziert.
- Keine neue Programmänderung nach dem erfolgreichen genannten CI-Code-Commit; die folgende Markdown-Dokumentation ist rein beschreibend.

## 4. Echte Home-Assistant-Realabnahme weiterhin offen

**Die V0.1.117 wurde nicht auf HA DEV installiert, es wurde keine Sammelinstallation gestartet, kein Neustart ausgelöst und keine neue Realabnahme behauptet.** Alle Änderungen liegen ausschließlich im privaten DRA-V2-Entwicklungszweig; DRA V1, Gewitterradar und WeatherRouter bleiben unverändert.

**Kontrollierter nächster Test:**

1. 0.1.117 auf HA DEV erst nach ausdrücklicher Genehmigung über den bewährten DRA-V1-Weg installieren und Python-/Oberflächenversion abgleichen.
2. Die Sammelvorbereitung auf Desktop **nur lesen/vorbereiten**, nicht installieren, und anschließend auf dem Handy als bestätigtes Steuergerät übernehmen.
3. Mobil die Projektkarten durchsehen, je Karte öffnen und schließen, überprüfen, ob zwölfstellige Kurzkennungen und vollständige 40-stellige Originalkennungen identisch zu den Desktopdaten sind; Kopieren prüfen.
4. Während wiederholter automatischer Statusabfragen kontrollieren, ob geöffnete Detailkarten und vertikale Position unverändert bleiben. Hoch-/Querformat und iPad gesondert überprüfen.
5. Checkbox, `review_digest`, Sperre bei unbestätigter Installation sowie WeatherRouter-Ref `deploy/dev` prüfen. Ein späterer Installationslauf bleibt ein **separat ausdrücklich freizugebender** Schritt.

**GitHub Actions ist keine Home-Assistant-Realabnahme.** Keine Eigenaktualisierung, Sammelinstallation oder gemeinsamer Neustart ohne den jeweils tatsächlichen Nachweis.

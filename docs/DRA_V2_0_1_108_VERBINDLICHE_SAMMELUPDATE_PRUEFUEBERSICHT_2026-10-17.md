# DRA V2 0.1.108 DEV – verbindliche Sammelupdate-Prüfübersicht
Stand: 17.10.2026 · Zweig `feature/v2-10-inventory-operation-contract`

## Auftrag und Zielbild

Vor jeder schreibenden Sammelinstallation muss der Anwender projektübergreifend sehen,
**welche Anwendung von welchem installierten Stand auf welche neue Version und genau
welchen Git-Commit aus welcher Referenz aktualisiert werden soll.**

Die neue tabellarische Prüfübersicht liegt ausdrücklich zwischen Quellenvorbereitung und
Installationsfreigabe. Die große geführte Deployment-Schaltfläche bleibt der Einstieg.

| Projekt | Installierte Version | → | Neue Version | Commit (vollständig) | Ausgewählt · Ref | Dateiänderungen |
| --- | --- | --- | --- | --- | --- | --- |
| Gewitterradar (nur Anschauungsbeispiel) | V4.11.88 | → | V4.11.94 | 40-stelliger SHA aus der echten HA-Prüfung | deploy/dev | + / ~ / − |

**Die Beispielversionsstände sind keine Aussage über die tatsächlich installierten Stände.**

## Datenherkunft und Verifikation

- Home Assistant lädt pro ausgewähltem Projekt den explizit empfohlenen Zweig über die
  registrierte GitHub-Verbindung, löst dessen Commit auf und erstellt eine quellcommitgebundene
  V1-Dateibestandsaufnahme.
- Die vorhandene V1-Quellinventur enthält bereits begrenzt eingelesene Versionsmarker.
  Die neue Funktion `batch_version_summary.py` verwendet *diese* Daten, statt
  eine zweite GitHub-Versionsermittlung zu entwickeln.
- Lokale Versionsmarker werden ausschließlich aus vorab durch die V1-Vorschau
  geprüften Dateien gelesen. Es gibt Größenbegrenzungen, Dateitypprüfung,
  Schutz vor symbolischen Verknüpfungen und abschließenden SHA-256-Abgleich gegen
  den von der Vorschau erfassten Dateistand. Die Datei-I/O findet nicht in der
  HA-Ereignisschleife statt.
- Nur eindeutig zueinander passende Versionsmarker aus Git und installierter
  Datei erhalten `version_status: verified_pair`.
  Bei fehlenden lokalen Markern lautet der Stand **Nicht ermittelbar**.
  Fehlen auch die Quellmarker oder widersprechen sich gleichrangige Marker,
  wird keine neue Version behauptet.
- Versionsangaben dienen ausschließlich zur Anzeige; als Installationsidentität
  gilt weiterhin ausschließlich der feste, vollständige Commit und das gültige
  V1-Manifest. Ein nicht ermittelbarer Versionsstand ist eine sichtbare Warnung,
  **keine erfundene Aktualisierungsnummer**.

## Prüfung und Freigabe

1. HA sendet für jede vorbereitete Zeile Projekt, Quell-Ref, vollständigen
   40-stelligen Commit, installierte und neue Version beziehungsweise
   `null`, Herkunft des Versionsmarkers, Versionsstatus und Änderungszahlen.
2. HA berechnet daraus eine deterministische SHA-256-Prüfkennung
   (`review_digest`).
3. Auf Desktop, Android oder iPad zeigt das Zwischenfenster die gesamte
   Liste als Tabelle; auf kleinen Geräten waagerecht scrollbar.
4. Die endgültige Freigabe bleibt deaktiviert, bis der Anwender das
   gesonderte Bestätigungskästchen markiert hat.
5. Beim Installationsstart werden zusätzlich zu bisheriger
   Admin-/Controller-/Challenge-Prüfung die ausdrückliche
   `review_confirm`-Erklärung und **die identische serverseitig
   berechnete `review_digest`** erzwungen.
6. Eine veraltete Prüfkennung, eine nicht erfolgte Prüfung oder eine
   einmal verbrauchte Vorbereitung berechtigt **niemals** zum Schreiben.
7. Ein Benutzer kann die Übersicht schließen, ohne den Batch zu starten.
   Wer eine falsche Auswahl erkennt, kann die Vorbereitung auf HA
   ausdrücklich **verwerfen**, wodurch die Freigabe aufgehoben wird;
   erst dann werden geänderte Projektauswahlen erneut geprüft.
8. Bei Bedienungsübernahme auf einem anderen Gerät muss die dortige
   Prüfübersicht erneut ausdrücklich bestätigt werden.

Die Tabelle zeigt den auf HA **zum Zeitpunkt der Vorbereitung**
festgehaltenen Commit. Ein Git-Zweig kann danach weiterlaufen.
DRA installiert ausdrücklich den angezeigten Commit, keinen heimlich
nachgeladenen neueren Zweigstand.

## Automatisierte Negativprüfungen

- Installation ohne Häkchen ausgeschlossen.
- Fremde/veraltete Prüfkennung ausgeschlossen.
- Nur HA-festgehaltene Quellref/Version/Commit-Kombination zulässig.
- Alte V1-Quellinventur mit unpassendem lokalen SHA meldet
  die lokale Version als unbekannt.
- Fehlende Dateien, widersprüchliche Marken und Symlinks melden
  keine behauptete installierte Version.
- Verwerfen durch fremde Bedienung oder ohne Bestätigung verweigert.
- Verworfenes Challenge kann keinen weiteren Start bewirken.
- Bestehende Tests für V1-Journal, Sicherheitsfreigaben, Gerätestatus,
  parallele Installationen, Rückfall, Test-Dateien und Zeitsteuerung
  bleiben bestehen.

## HA-Realabnahme – noch offen

1. Version 0.1.108 DEV über DRA V1 installieren und Python-/JS-Version vergleichen.
2. Nur das isolierte Testprojekt auswählen, Sammelvorbereitung ausführen und
   das Zwischenfenster öffnen. Versionsfelder bei Unbekanntem korrekt anzeigen,
   40-stelligen Commit und Ref auf Übereinstimmung mit Git prüfen.
3. Bestätigungskästchen zunächst auslassen: keine Installation möglich.
4. Vorbereitung verwerfen, auf anderen Browsern prüfen, ob die Freigabe
   tatsächlich ungültig ist. Anschließend neu vorbereiten.
5. Desktop als Bediener, Android/iPad als Beobachter – bei Gerätewechsel
   erneut explizit übernehmen und prüfen.
6. Ein bewusst bestätigter Test-Batch muss seine einzelnen V1-Auftragsjournale
   und Installationsprüfungen erfolgreich abschließen. Erst nach dieser
   Abnahme produktive Projekte in Sammelupdates aufnehmen.

CI ist kein Ersatz für die HA-Realabnahme. DRA V1, andere Repositories
und produktive Installationen wurden im Rahmen dieses Entwicklungsauftrags
nicht verändert.

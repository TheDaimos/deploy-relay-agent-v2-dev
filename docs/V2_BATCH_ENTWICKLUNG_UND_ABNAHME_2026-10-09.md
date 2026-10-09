# DRA V2 – Entwicklung in Funktionspaketen und risikogesteuerte Abnahme

Stand: 09.10.2026 · **Ab sofort verbindliche Entwicklungs- und Abnahmemethodik für V2 DEV**.
Bestätigter Nutzerwunsch: mehrere zusammengehörige Funktionen in einer Entwicklungsiteration bündeln und anschließend **gezielt als Paket** real prüfen, statt für jede kleine Erweiterung dieselbe vollständige HA-Kette zu wiederholen.

## Grundsatz: gemeinsame Entwicklung, getrennte Gates

Eine **Implementierungseinheit ist nicht dasselbe wie ein Abnahmegate**. Mehrere vorhandene Punkte aus `docs/V2_STUFENPLAN.md` dürfen fachlich gemeinsam vorbereitet, implementiert und in einem DEV-Stand getestet werden, **solange jeder Punkt seine eigene nachvollziehbare Abnahme behält**. Vorbereitete Funktionen und bestandene CI sind keine automatisch bestandenen HA-Realtests. Keine offenen Sicherheitsgates oder Release-/V1-Referenzanforderungen überspringen oder stillschweigend als DONE markieren.

**Neue Standardfolge je Funktionspaket:**

1. **Paketvertrag**: eine Liste zusammengehöriger Änderungen, gemeinsamer Daten-/Schnittstellenvertrag, Auswirkung auf V1 und HA, Risiko- und Testmatrix, sichere Rückfallgrenze.
2. **Gebündelte Implementierung auf V2-DEV-Featurezweig**: mehrere zusammengehörige Funktionen im selben Versionsstand. Für jedes Teilgebiet gezielte automatisierte Positiv-, Negativ-, Abbruch- und Regressionstests. CI nach Codeänderungen, sofortige Korrektur roter Tests; Dokumentation und Versions-/Schemaentwicklung synchron.
3. **Statische Paketabnahme**: vollständige Paket-CI auf dem exakten SHA; nur erlaubte V2-Installationspfade, kein V1-/PUB-/Main-Eingriff, keine unzulässigen Journal-/Exportfelder, keine offenen Blocker.
4. **Eine V1-Installationsvorschau je Paket**: betroffene Dateien und Quell-SHA kontrollieren. **Vor einer Installation ausdrückliche Zustimmung des Nutzers**; zusätzlicher HA-Neustart nur wenn notwendig und separat genehmigt.
5. **Gezielte HA-Realabnahme des Pakets**: definierte relevante Szenarien, möglichst ein gemeinsamer Durchlauf mit phasenweisen Ergebnissen, einem anonymisierten Git-Export und V1-Sammelprüfung nach dem Paketwechsel. Kein Volltest aller unberührten, zuvor abgenommenen Funktionen ohne konkretes Risiko.
6. **Gate-Matrix pflegen**: jede Teilfunktion erhält separat `CI PASS/FAIL`, `HA PASS/FAIL/NOT_TESTED`, Nachweislink/Commit, offene Einschränkungen; die Paketfreigabe bleibt offen, solange ein sicherheitskritischer Teiltest offen ist.
7. **Gezielter Nachtest**: bei Korrekturen nur betroffene Funktionen plus relevante Nachbarn und Basisschutz prüfen; vollständige HA-Regression nur bei Änderung an gemeinsamem Kern (Journal, Berechtigungen, Recovery, Schreib-/Neustartpfade, globale Ressourcenlocks, Datenformat-Migration).

**Ohne ausdrückliche neue Nutzerfreigabe kein Deployment, kein Neustart, keine produktive Schreibaktion.**

## Geplante Entwicklungs-/Abnahmepakete

| Paket | Bündelung | Ein gemeinsamer HA-Nachweis | Nicht vorgezogen / Voraussetzung |
| --- | --- | --- | --- |
| **A – Messung und Diagnose** (zuerst) | V2-40-50 quantitative Ressourcenabnahme; überschneidende V2-115-Diagnosebausteine; Zeitstempel, nachweisbare HA-Ereignisschleifen-Reaktionszeit, Prozess-I/O-Zähler, CPU-/RAM-Phasen, Mehrkernmessung und ein gemeinsamer redigierter Git-Bericht | Im schreibgeschützten Gesamttest Basis/Last/Nachlauf mit **UTC-Start/Ende und monotonen Laufzeiten pro Phase**, Eventloop-Latenz, /proc-Prozess-I/O und vorhandenen CPU-/RAM-/Mehrkernwerten. Ein Export, gekoppelte Referenzkurve; anschließend V1-Sammelprüfung | Kein automatischer HA-Neustart, keine fremden /config-Dateien, keine Behauptung von DRA-spezifischen Prozesszählern, keine falsche Zuordnung von Proxmox-VM-Spitzen |
| **B – Leseauftrags- und Bedienkern** | Gemeinsame Vorbereitung V2-50/60/90/110/120: echter serverseitiger Lese-Fortschritt, Wiederverbinden mehrerer Clients, begrenzte Listen-/Seitenabrufe, schreibgeschützte Sammelvorschau, schlanke mobile Bedienung | Ein definierter Wiederverbindungs-/Mehr-Client-/Warteschlangen- und Lesevorschau-Durchlauf, ein Export; V1-Kontrolle | Erst nach A-Gates soweit Abhängigkeiten betroffen; keine produktive Installations-, Restore- oder Batch-Schreibfreigabe |
| **C – Schreibtransaktionen** | Vorbereitung V2-70/80/100/140: Installations- und Restore-Verträge, Sicherungs-/Rollback-Konzept, Konflikt- und Ressourcensperren, Neustartbestätigung, DRA zuletzt | **Keine gemeinsame pauschale HA-Schreibfreigabe**. Für Installieren, Wiederherstellen, Sammelinstallation, Abbruch/Recovery und HA-Neustart **jeweils eigene positive und negative Sicherheitsabnahmen**, getrennte Zustimmungen | Bestehender globaler Mutations-Lock `1` bleibt, bis ein gesonderter Nachweis ausdrücklich etwas anderes zulässt. Kein produktiver HA-Eingriff durch diese Planung |
| **D – Oberfläche, Migration, Veröffentlichung** | V2-125/150/160/170 und übrige UX-/Dokumentationsarbeit: zentrale Darstellung, Integration, Migration, Publikationsmaterial | Gemeinsame Sichtprüfung/Kompatibilität und abschließende Release-Regression nach Erfüllung sämtlicher Sicherheitsgates | Kein V2-PUB, kein Draft-PR-Merge, keine Migration vor besonderer Genehmigung |

Die Paketübersicht beschreibt **Zusammenarbeit und Reihenfolge**, keine automatische Statusänderung im bisherigen Stufenplan.

## Konkreter erster Paketzuschnitt A – ohne unnötige Realtestschleifen

- **Absolute Zeitkorrelation**: UTC-Start/Ende der gesamten Operation und aller Testphasen; monotone Dauer in Millisekunden, Uhrzeit-/Zeitzonenangaben getrennt. Damit externe Proxmox-Bilder präzise zuordnen, aber nicht ungeprüft Ursache = DRA behaupten.
- **HA-Reaktionsfähigkeit**: kleiner, begrenzter und nur während des ausdrücklich gestarteten Messauftrags laufender Ereignisschleifen-Takt; `n`, Median, hohe Perzentile (sofern ausreichend Stichproben) und Maximum dokumentieren, Messfehler als `unavailable`. Kein Blockieren der HA-Ereignisschleife.
- **Datenträger-Ein-/Ausgabe**: schreibgeschützte, streng festgelegte Linux-Prozesszähler, soweit verfügbar, an vier Phasengrenzen; klar als **Prozess-gesamt** und nicht DRA/V1/V2 einzeln bezeichnet. VM-weite Proxmox-Werte gehören nur als separate, freiwillige Vergleichsdaten ins Protokoll.
- **Ein gemeinsamer Export**: bestehende CPU-/RAM- und sieben Mehrkernstufen bleiben erhalten. Neues abwärtskompatibel versioniertes öffentliches JSON mit ausschließlich erlaubten Zahlen, festen Methodenschlüsseln, Zeitstempeln und höchstens begrenzter Dateigröße. Keine freien privaten Nutzerfelder, Tokens, Projektpfade, IPs oder Auftragskennungen.
- **Gezielte Realabnahme**: nach einem einzigen freigegebenen Update genau ein Gesamttest mit Git-Export; zusätzlicher Latenz-/I/O-Fall nur bei Fehler oder unvollständigem Nachweis. DRA-V1-Sammelprüfung einmal nach dem Paketwechsel. HA-Neustart nur bei tatsächlich technischer Notwendigkeit und eigens erteilter Freigabe.
- **Zugehörige Einzelgates**: V2-40-50 wird erst dann `PASS`, wenn seine definierten quantitativen Kriterien wirklich nachgewiesen sind. V2-115-Teilfunktionen können parallel vorbereitet werden, V2-115 bleibt als Gesamtgate offen, bis seine eigenen ausstehenden Anforderungen erfüllt sind.

## Immer einzeln abnehmen (unveränderliche Schutzgrenzen)

- Änderungen an Autorisierung, Git-Schreibzugang, Installationspfaden und Berechtigungen.
- Journal-Schema, Recoverability nach Absturz, Unterbrechung und Wiederaufnahme schreibender Aufträge.
- Installation, Restore, Sicherung/Rollback, Sammelinstallation, DRA-Selbstaktualisierung.
- HA-Core-Neustart mit **eigener Sicherheitsabfrage und zweiter ausdrücklicher Bestätigung**.
- Schreibparallelität, projektbezogene Ressourcenlocks und Migration aus V1.
- V2-PUB-Veröffentlichung und Zusammenführung des Entwurfs-PR.

**Unverändert geschützt:** V1-DEV und V1-PUB nicht ändern; V2-PUB und V2-DEV-`main` nicht ändern, PR #2 nicht mergen; nur isolierte V2-DEV-Featurequelle; höchstens eine globale Mutation, solange kein neues separat abgenommenes Sicherheitsmodell besteht. Bei jedem HA-Test Vorher-/Nachher-V1-Kontrolle soweit einschlägig.

## Zeitgewinn und messbare Entwicklung

Erfolg wird nicht an der bloßen Anzahl gesparter Einzeltests gemessen, sondern an **weniger HA-Installationen und -Neustarts pro abgeschlossener, nachvollziehbarer Funktion**. Im gemeinsamen Bericht stehen Paketversion, Quell-SHA, tatsächlich geprüfte Funktionen, genaue Zeitpunkte, Laufzeiten, Ergebnis pro Teilfunktion, nicht prüfbare Punkte und Links zu CI/Git. Fehler in einer Komponente machen den gesamten Paketstatus nicht irreführend grün.

**Aktueller Stand:** V2 DEV 0.1.8 (7 Mehrkernstufen) wurde auf HA-DEV real geprüft und DRA V1 funktionierte nach HA-Neustart weiter. V2-40-50 ist wegen der fehlenden korrelierbaren Latenz-/I/O-Nachweise weiterhin OFFEN. Das erste neue Funktionspaket A soll diese Lücke zusammen mit Diagnoseverbesserungen schließen. In diesem Dokument sind **noch keine neuen Laufzeitfunktionen implementiert und keine Installation genehmigt**.

## Weiterer Paketbaustein V2 DEV 0.1.13 (09.10.2026)

Bei einzelnen registrierten öffentlichen GitHub-Projekten kann jetzt eine echte **schreibgeschützte** Quellprüfung mit festem Commit und lokalem Dateivergleich angefordert werden. **Keine automatische Sammelinstallation, keine automatischen Schreibaktionen oder verfügbare Rücksicherung** wurden dadurch freigegeben. Ein privat geschütztes Repository gilt ohne separates V2-Lesetoken als nicht zugänglich; es wird niemals als aktuell fingiert.

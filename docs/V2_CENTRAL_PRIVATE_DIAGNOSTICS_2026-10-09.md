# DRA V2 DEV 0.1.15 – Referenz für zentrales privates Diagnosearchiv

Stand 09.10.2026 | Featurezweig \`feature/v2-10-inventory-operation-contract\` | **Code-/CI-Abnahme; Home-Assistant-Realabnahme ausstehend**

## Verbindliche Referenzen

Die Ausführung richtet sich nach:
- Privatrepository \`TheDaimos/Project-Log-And-Export/README.md\`
- \`docs/EXPORT_STANDARD_V1.md\` im zentralen Privatrepository, insbesondere verbindlicher DRA-V2-Identitätsvertrag vom 09.10.2026
- \`docs/SECURITY.md\` im zentralen Privatrepository.

## Unveränderliche Identität, Metadaten und Ordner

- **Anwendungs-ID:** \`deploy-relay-agent-v2\`, unveränderlich, nie neu vergeben.
- **Anzeigename:** \`Deploy Relay Agent V2\`, ein exportbezogenes Pflichtfeld, darf sich später ändern, ohne technische ID oder Archivordner zu ändern.
- **Version:** tatsächliches \`VERSION\` der laufenden V2-Integration; im Codecheckpoint \`0.1.15\`.
- **Exportzeitpunkt:** ISO 8601, UTC (\`YYYY-MM-DDTHH:MM:SSZ\`).
- **Export-ID:** kryptografisch erzeugte 128-Bit-Hexkennung, pro neu angelegtem Export neu. **Wiederholversuche behalten exakt dieselbe Export-ID und denselben Dateipfad.**
- **Quelle:** \`source.repository=TheDaimos/deploy-relay-agent-v2-dev\`; \`source.commit\` nur falls tatsächlich sicher bekannt und überprüft, sonst \`null\`.
- **Exportart:** \`diagnostics\`, Quelltest \`V2-CPU-RAM\`, \`V2-MULTICORE\` oder \`V2-READONLY-FULL\`. Keine erfundene Capability-Nummer.
- **Metadatenschema:** \`daimos-project-log-export-v1\`; ursprünglicher bereinigter DRA-V2-Messinhalt bleibt strukturell unter \`snapshot\` erhalten (bestehende \`dra-v2-dev-git-measurement.v2\` / \`dra-v2-dev-git-suite.v2\`).
- **Archivpfad:**

  \`exports/deploy-relay-agent-v2/<YYYY-MM>/diagnostics/<UTC-Zeit>__deploy-relay-agent-v2__<Version>__diagnostics__<Export-ID>.json\`

  Die Ordnerbildung folgt **ausschließlich der festen ID**. Anzeigenamen werden niemals als Dateinamen-/Ordnerbestandteil übernommen.

Der bisherige, für Diagnoseexporte verwendete Pfad \`.deploy-relay/diagnostics/v2-dev/\` im V2-Entwicklungsrepository bleibt nur als **historisches Archiv** erhalten. V2 stellt **keinen neuen Export mehr in ein öffentliches Projektrepository** zu.

## Serverseitige Autorisierung und privates Ziel

- **Kein vorbelegtes Repository:** Jeder Administrator speichert sein persönliches privates Export-Repository als `Eigentümer/Repository`. `TheDaimos/Project-Log-And-Export` ist nur eine mögliche freiwillige Wahl, ausdrücklich kein Standard. Standardzweig wird beim Export aus den privaten GitHub-Metadaten gelesen.
- **GitHub-Berechtigungen:** Eigener, eng begrenzter Token für das ausdrücklich gewählte private Repository (`Contents: Read and write`, `Metadata: Read`). Der Token wird nur serverseitig dauerhaft gespeichert, nicht im Diagnoseexport oder Browser-Speicher.
- **Einmalige Token-Eingabe:** In V2 DEV 0.1.16 erfolgt sie auf ausdrücklichen Administratorwunsch im Git-Export-Dialog; danach bleibt der Token ausschließlich serverseitig gespeichert. Als Alternative kann die HA-Serverumgebung den Zugang bereitstellen.
- **HA-Realabnahme:** Der Dialog benötigt keine Änderung der HA-Startumgebung. Die sichere Speicherung und Authentifizierung sind anhand der konkreten HA-DEV-Instanz noch real zu überprüfen; es wurde keine HA-Installation ausgelöst.
- **Privatsperre:** Vor jedem Upload wird exakt das gespeicherte Repository per GitHub geprüft: `private=true`, `full_name` entspricht der Einstellung und ein gültiger Standardzweig ist vorhanden. Bei fehlender Berechtigung oder öffentlichem Ziel keinerlei Upload.
- **Append-only:** GitHub Contents API wird ausschließlich mit einer **CREATE**-Anfrage ohne \`sha\` beschickt. Ein bereits existierender Pfad kann nicht überschrieben werden; HTTP 409/422 oder fehlerhafte Bestätigung gelten nicht als Erfolg.

## Geheimnisbereinigung, Wiederholung und Status

- DRA V2 übernimmt nur streng validierte, fest definierte **numerische Messfelder** (CPU/RAM/Mehrkern), keine willkürlichen JSON-Einträge, geheimen Werte, Dateipfade, Projektlisten, Tokens oder Auftragskennungen. Verdächtige Inhalte werden **vor Archivierung/Upload abgewiesen**, nicht stillschweigend unbereinigt gespeichert.
- **Lokaler sicherer Rückfall:** Im privaten HA-Store `deploy_relay_v2_dev.archive_queue` wird Schema `dra-v2-dev-central-export-queue.v2` mit selbstgewähltem Repository und höchstens einem bereinigten, zielgebundenen Export gespeichert. Bei Fehlern manueller Wiederholversuch nur an dasselbe Ziel. Zielwechsel während eines ausstehenden Exports gesperrt.
- Beim Laden nach HA-Neustart wird der gesamte gespeicherte Datensatz **einschließlich verschachtelter Messfelder** erneut strikt geprüft. Manipulierte, unvollständige oder unbekannte Versionen führen konservativ zur Ablehnung, ohne dass vorhandene Beweise gelöscht werden.
- **Status:** Das Export-Repository-Feld bleibt beim Erststart leer. GitHub-Schaltfläche bleibt ohne explizit gespeichertes privates Repository und Serverzugang gesperrt. Ein unabhängiger JSON-Download benötigt beides nicht. Nach Git-Erfolg werden Export-ID und Pfad angezeigt.
- Die bisherige schreibgeschützte Messung, der Mehrkerntest und die Gesamttestfolge bleiben erhalten; nur ihr Diagnose-**Ziel** und die verbindliche Metadatenhülle wurden umgestellt.

## Künstliche Abnahmefälle vor HA-Reallauf

- Erfolgreicher Upload zur echten **privaten Zielkennung** mit korrekt strukturierter Pflichtmetadatenhülle, Quellversion, eindeutiger Export-ID und passendem UTC-Monat.
- Zwei Exporte derselben Messung erhalten **verschiedene** IDs und niemals ein \`sha\`-Überschreibfeld.
- Umbenennung des Anzeigenamens lässt \`application.id\` und den Ablagepfad unverändert.
- Fehlende Pflichtangaben, unzulässige Versionen/Commit-SHAs und verfälschte Archivpfade werden abgelehnt.
- Strenger Ausschluss von Authentifizierung, unbekannten Feldern und verschachtelten Geheimnissen; auch lokal gespeicherte Daten werden vor Wiederholung erneut geprüft.
- Fehlende/ungültige Server-Zugangsdaten: kein Upload.
- Keine Berechtigung (403), gesperrter/veränderter privater Zielzustand, Netzwerkfehler (503) und Dateikollision (422): **kein öffentlicher Ersatz**, ein bereinigter Datensatz bleibt für explizite Wiederholung erhalten, niemals überschreiben.
- Reibungslose CPU/RAM-/7-Stufen-Mehrkern-/Gesamttestfunktionalität und dokumentierte Isolierung von V1.
- JavaScript-Oberfläche, WebSocket-Administratorpflicht, keine Exporte/Secrets im öffentlichen GitHub-Actions-Protokoll und unveränderte V2-Dateigrenzen.

**Keine echte private Archivprobe durchgeführt.** HA-Abnahme erfordert die ausdrückliche Repositorywahl sowie einen nur darauf begrenzten serverseitigen Zugang; lokaler JSON-Download benötigt beides nicht. DRA V1, V2-PUB und V2-DEV `main` unverändert, Entwurfs-PR #2 ungemergt.

## Verbindlicher Nachtrag V2 DEV 0.1.15 – Kein Standardrepo, unabhängiger Download

- **Leerer Ausgangszustand:** Keine öffentliche oder private GitHub-Ablage ist vorbelegt, weder TheDaimos noch eine andere Organisation. Jeder Administrator wählt sein eigenes privates Repository ausdrücklich selbst aus.
- **Persistenz und Privatsperre:** Das Administrator-Repository wird ohne Token getrennt gespeichert. Eine neue GitHub-Übertragung ist nur nach Prüfung von `private=true` und der exakten Repositoryidentität möglich. Server-Token wird nicht an Browser übertragen.
- **Kein Umleiten:** Ein ausstehender Export ist an die ursprüngliche Repositorywahl gebunden. Wechsel/Entfernen sind bis zu einem sicheren Abschluss gesperrt; Wiederholung nutzt dieselbe Export-ID.
- **JSON-Download:** Ein erfolgreich abgeschlossener Diagnose-Test kann unabhängig von GitHub als bereinigte JSON-Datei heruntergeladen werden. Die Datei enthält das vollständige verpflichtende Metadatenschema und eine einmalige Export-ID; kein Token, kein Upload, keine Warteschlange.
- **Adminschutz:** Frei von GitHub-Konfiguration bedeutet nicht öffentlich für fremde Nutzer. Download und Einstellungen setzen eine HA-Administratorberechtigung voraus.
- **Prüfung:** Künstliche Fälle für leeres Ziel, eigenständig funktionierenden Download, private Repositoryauswahl, unzulässige Namen, fehlende GitHub-Rechte, Archivkollision und unterbundenen Zielwechsel.


## Erweiterung 0.1.16: Kompakter Exportdialog

Die Diagnose-Hauptansicht zeigt nur noch „JSON herunterladen“ und „Git-Export“.
Der Git-Export öffnet einen eigenen Dialog für die manuelle Auswahl eines privaten
GitHub-Repositories, die einmalige Eingabe des dazugehörigen Tokens sowie
Speichern, Prüfen, Exportieren, Wiederholen und Entfernen der Konfiguration.
Es gibt weiterhin **kein vorbelegtes Repository**.

Die GitHub-Zugangsdaten werden beim Einrichten über die authentifizierte
Home-Assistant-WebSocket-Verbindung an den Server übertragen und dort in
einem separaten privaten Home-Assistant-Speicher unter
`deploy_relay_v2_dev.archive_credentials` hinterlegt. Sie werden nicht
an die Oberfläche zurückgegeben. Die Eingabe ist maskiert und wird nach
dem Absenden und beim Schließen gelöscht. Die HA-Verbindung sollte mit
HTTPS/WSS geschützt sein; HA-`.storage` wird nicht automatisch verschlüsselt.

Ein Wechsel des Repositories bei noch ausstehendem Export bleibt untersagt.
Ein neuer Token für dasselbe Repository darf dagegen gesetzt werden, um
die bestehende Exportkennung und das bisherige Ziel bei der Wiederholung
zu erhalten. Fehlende Rechte oder fehlgeschlagene Verbindung erzeugen
keinen öffentlichen Ersatzexport.

Lokaler JSON-Download bleibt unabhängig von GitHub und dem eingerichteten
Repository verfügbar. Alle technischen Anwendungsmetadaten bleiben erhalten.
Die vorhandene serverseitige Umgebungsvariable bleibt als optionaler Altweg
erhalten. Ein tatsächlicher HA-Realtest ist noch ausstehend.

## Korrekturpaket V2 DEV 0.1.17 – Exportfreigabe, gespeicherter Status, sichtbare Token-Endung

Aufgrund der HA-Nutzerrückmeldung nach V2 DEV 0.1.16 wurden drei konkrete Fehlfunktionen gemeinsam behoben.

1. **Reale Wiederherstellung der gespeicherten Anzeige:** Das `Repository`-Feld im Dialog konnte nach einer Neuzeichnung das Literal `undefined` erhalten, weil der vorherige HTML-Eingabewert nicht existierte. Nur echte Zeichenfolgen werden nun übernommen; bei einem neu geöffneten Dialog wird der gespeicherte Repo-Wert angezeigt. Der eigene private HA-Store `deploy_relay_v2_dev.archive_credentials` behält Repository und Token über Seiten- und HA-Neustarts; das Passwortfeld selbst bleibt aus Sicherheitsgründen leer.
2. **Klarer Hauptbildschirm:** Neben dem GitHub-unabhängigen `JSON herunterladen` sind die separaten Schaltflächen `Git-Export` (zunächst gesperrt) und `Export-Einstellungen` sichtbar. **Git-Export** wird erst bei konfiguriertem Repository + gültigem serverseitigem Token + vorhandenem erfolgreichen Diagnosedatensatz aktiv. `Export-Einstellungen` bleibt immer zugänglich, auch ohne Messung, damit Einrichtung und Fehlersuche nicht blockieren. Repository wird sichtbar angezeigt, vom gespeicherten Token kommen ausschließlich die **letzten fünf Zeichen** an den authentifizierten HA-Administrator zurück; `•••••xxxxx` als beschrifteter Hinweis. Der vollständige Schlüssel wird nicht zurückgesendet, nicht in öffentliche Protokolle und nicht in Diagnosedokumente aufgenommen. Bei einer ausschließlich über die HA-Umgebung bereitgestellten Zugangsdatenkonfiguration wird keine irreführende Token-Endung vorgetäuscht.
3. **Prüfbestätigung:** `Speichern & prüfen` wird nach bestätigtem privaten Lesezugriff **grün**, bei Fehler **rot**. Der gespeicherte private Zugang lässt sich bei unverändertem Repository **ohne neue Token-Eingabe** überprüfen (`archive_repository/check`, Admin-only). Grün bedeutet hier **private Repositorysichtbarkeit / GitHub-Lesezugriff**, nicht automatisch erprobte Schreibrechte; die werden erst bei einem realen Upload geprüft. Erneutes Öffnen zeigt einen grünen „Gespeichert“-Status, ohne eine neue Live-Git-Abfrage vorzutäuschen.
4. **Diagnose-Freigabekette vereinheitlicht:** Zuvor wurde die Exportierbarkeit fälschlich am **allerletzten Auftrag** festgemacht; eine später gestartete schreibgeschützte Vorschau konnte einen erfolgreichen CPU/RAM-Messlauf unsichtbar machen. Ein neuer gemeinsamer serverseitiger Selektor ermittelt den **letzten tatsächlich erfolgreichen und noch im Speicher vorhandenen Diagnosedatensatz**, unabhängig von späteren nicht exportfähigen Testaufträgen. Genau derselbe Selektor gilt für `diagnostics_export_ready` im Zustand, `download_json` und `git_export`. Fehlgeschlagene/unterbrochene Diagnosen oder alte Berichte ohne nachweislich erfolgreichen Auftrag werden nicht freigegeben.
5. **Korrekte Fehlerrückmeldung:** Eine fehlgeschlagene Übertragung darf in der Oberfläche keinen angeblich ausstehenden Wartedatensatz erzeugen. Stattdessen wird der tatsächliche Warteschlangenstatus erneut serverseitig abgerufen. War ein Upload erfolgreich, erscheinen weiterhin Export-ID und Zielpfad; bei Ausfall der Verbindung bleibt der zuletzt sicher bekannte Status und die Fehlermeldung sichtbar.
6. **Abnahme ohne Nutzer-Geheimnisse:** Synthetische Python- und JavaScript-Tests für den allein mit Adminsicht erlaubten Fünf-Zeichen-Hinweis, Wiederherstellung über neue Store-Instanz, keine vollständigen Token-Rückgaben, UI-Freigabe ohne Repo gesperrt, nach gültiger Messung und Einrichtung aktiv, grünen/roten Status, Wiederholung ohne Token-Neueingabe, literal `undefined` sowie Messungswahl nach späterer Vorschau. Keine Änderung an V1 oder an HA-DEV wurde durch die Umsetzung veranlasst.

**Noch offen:** HA-Realabnahme der korrigierten V2 DEV 0.1.17 sowie der tatsächlichen GitHub-Schreibberechtigung. Historische Dateien bleiben unverändert, keine Exporte in ein öffentliches Repository.


## Oberflächenordnung V2 DEV 0.1.18 (09.10.2026)

- Teststeuerung mit eingerahmtem Auftragsstatus, Restzeit und direkter Statusaktualisierung.
- Diagnoseexport unmittelbar neben der Teststeuerung auf breiten Bildschirmen und direkt darunter auf Mobilgeräten; unverändert unabhängiger JSON-Download, privater Git-Export und jederzeit erreichbare Exporteinstellungen.
- Messergebnisse sind in einem eigenen, nachgeordneten Bereich mit seitlich verschiebbaren Tabellen; Projektverwaltung, Auftragsverarbeitung und Sammelvorschau als optisch getrennte Bereiche.
- Maximale Inhaltsbreite 1600 px mit zweispaltiger Desktopanordnung ab 1100 px und einspaltiger Mobilansicht; keine Änderung an Export-Backend, Tokenpersistenz, Privatsperre oder den V1-Integrationen.
- Benutzer meldete am 09.10.2026 einen erfolgreichen privaten Git-Export in der HA-Oberfläche (sichtbare Export-ID und Zielpfad). Das ist eine Benutzerbestätigung, keine vom Entwicklungsprozess unabhängig abgeglichene GitHub-Dateiverifikation.
- Die Freigabe für die Installation über DRA V1 bleibt eine gesonderte Benutzerhandlung; dieser Commit installiert oder startet Home Assistant nicht neu.

## V2 DEV 0.1.19 – Bereinigung der Teststeuerung (10.10.2026)

Die veraltete Schaltfläche „Testauftrag starten“ für die künstliche 40-Sekunden-Auftragsprüfung wurde aus der normalen Benutzeroberfläche entfernt. CPU-/RAM-Messlauf, Mehrkern-Diagnose und Gesamttest bleiben bedienbar. Der interne schreibgeschützte Testauftrag und sein serverseitiger Prüfvertrag bleiben für Entwicklung und Regressionstests vorhanden. Keine Änderung an Git-Export, V1 oder HA-Neustartverhalten.

## V2 DEV 0.1.20 – Künstlichen Altauftrag vollständig entfernt (10.10.2026)

Der alte schreibgeschützte 40-Sekunden-Warteauftrag einschließlich WebSocket-Route und Frontend-Startmethode entfällt vollständig. Der echte 40-Sekunden-CPU-/RAM-Messlauf verwendet weiterhin die serverseitige Auftragsverwaltung und funktioniert unabhängig vom Browser. Mehrkern-Diagnose, Gesamttest und Diagnoseexport bleiben erhalten. Frühere Journal-Einträge werden nicht gelöscht. Keine HA-Installation oder automatischer Neustart.

## V2 DEV 0.1.21 – Git-Quellprüfung im Projekt sichtbar (10.10.2026)

Die Projektliste erhält eigene Spalten für Sammelupdate und Git-Quelle, mobil als einzeln beschriftete Projektkarten. Die schreibgeschützte Quellprüfung zeigt den laufenden Zustand sowie Erfolg/Fehler und bei Erfolg Commit und Dateizahlen unmittelbar beim betroffenen Projekt; die ausführliche Ergebnisliste bleibt darunter verfügbar. Ursache der vorher unklaren Bedienung: Rückmeldung ausschließlich unterhalb des weit entfernten GitHub-Lesezugangbereichs. Kein Installations- oder Schreibpfad geändert. Eine erfolgreiche Quelle ist keine Installationsfreigabe.

## V2 DEV 0.1.22 – Sammelupdate nur im eigenen Bereich (10.10.2026)

Der redundante Sammelupdate-Ein/Aus-Knopf wurde aus der Projektliste in Abschnitt 05 entfernt. Die gespeicherte Vorauswahl und die Kontrollkästchen samt schreibgeschützter Auswahlprüfung bleiben unverändert ausschließlich in Abschnitt 06 · Sammelaktualisierung. Quellprüfung und Projektmetadaten bleiben separate Vorgänge. Der geplante größere Oberflächenumbau nach der DRA-V1-Optik ist hiervon unabhängig und noch nicht umgesetzt.

## V2 DEV 0.1.23 – Sammelaktualisierung als Dialog (10.10.2026)

Abschnitt 06 zeigt nur „Projektauswahl bearbeiten“ und die Anzahl aktivierter Projekte. Das Fenster zeigt die Auswahl mit Häkchen und den Aktionen „Speichern“ und „Abbrechen“. Ein Abbruch verwirft ungespeicherte Änderungen; der Speichervorgang verwendet vorhandene Administrator-WebSocket-Routen und bestätigt jedes Projekt. Bei einer Teilstörung bleibt das Fenster mit Fehlermeldung offen; die bereits bestätigten Einträge bleiben gespeichert und ein erneuter Speicherversuch ist möglich. „Auswahl prüfen (ohne Installation)“ wird nicht mehr in der Benutzeroberfläche angeboten. Es werden keine Updates oder Installationen ausgelöst.

## V2 DEV 0.1.24 – Backup & Retention (10.10.2026)

Die Aufbewahrungsvorgaben wurden aus der breiten Projektliste in ein eigenständiges, mobil bedienbares Fenster „Backup & Retention“ unter „Meine Projekte“ verlagert. Die bereits vorhandene serverseitige Richtlinien-Speicherung (3–100 Sicherungen je Projekt) bleibt unverändert. Ein einzelner Projekt-Eintrag im Fenster zeigt die Aufbewahrungszahl und „Speichern“. „Verfügbare Backups anzeigen“ ist bis zum echten Sicherungsinventar deaktiviert; es werden keine fiktiven Bestände ausgegeben. Die gewünschte Möglichkeit, einzelne Sicherungen dauerhaft von der Rotation auszunehmen, benötigt vor Aktivierung ein unabhängiges persistentes Backup-Inventar, tatsächliche Sicherungsbeweise und eine getestete Sperr-/Rotationsregel. DRA V1 und dessen Sicherungen werden nicht verändert. Keine Installation oder Wiederherstellung.

## V2 DEV 0.1.25 – Einstellungen in drei Spalten (10.10.2026)

Die drei Felder Betriebsart, parallele Leseaufträge und DRA-Arbeitsprozesse werden im Abschnitt 04 auf ausreichend breiten Ansichten nebeneinander in gleich breiten Spalten mit eigenen Überschriften dargestellt. Bei höchstens 850 px verfügbarer Breite folgt eine einspaltige Darstellung. Die Speicher- und Prüfregeln bleiben unverändert; keinerlei Freigabe realer Schreibaufträge.

## V2 DEV 0.1.26 – Einheitliche Schaltflächenrückmeldung (10.10.2026)

„Vorgaben speichern“ in der Auftragsverarbeitung heißt nur noch „Speichern“. Sämtliche aktivierten Schaltflächen des V2-Testlabors erhalten optische Hover-, gedrückt- und Tastaturfokuszustände. Beim Drücken werden sie geringfügig nach unten verschoben und abgedunkelt; deaktivierte Schaltflächen reagieren nicht. Reduzierte Animation wird über die Betriebssystemeinstellung berücksichtigt. Die Änderung betrifft nur die Oberfläche, nicht die Auftragsausführung, Sicherungen oder Schreibberechtigungen.

## V2 DEV 0.1.28 – Einklappbare Diagnose- und Einstellungsbereiche (10.10.2026)

Alle sechs vorhandenen Bereiche der bisherigen V2-Laboransicht sind nun unabhängig auf- und zuklappbar und zunächst geschlossen. Der Öffnungszustand bleibt während der laufenden Statusaktualisierung im aktuellen Browser erhalten. Unter „Meine Projekte“ lautet die frühere Schaltfläche „V1-Projekte ansehen“ nun „Projekte aus DRA V1 übernehmen“; die sichere zweistufige Vorschau und ausdrückliche Übernahme bleiben technisch identisch. Die gesamte bisherige Laboroberfläche gehört fachlich künftig unter „Diagnose & Einstellungen“, nicht zur eigentlichen noch zu gestaltenden DRA-V2-Hauptoberfläche. Keine neue Installationsfreigabe.

## V2 DEV 0.1.29 – Selektiver Projektimport (10.10.2026)

Die Schaltfläche „Projektimport“ öffnet einen Dialog mit auswählbaren DRA-V1-Projekten. „Alle auswählen“ in der Dialogüberschrift setzt alle Kontrollkästchen; einzeln abwählbar. „Importieren“ überträgt ausschließlich die ausgewählten Projektmetadaten nach V2; „Abbrechen“ verwirft die Auswahl. Die WebSocket-Route verlangt eine explizite Liste, prüft Duplikate und lehnt fremde Repositorynamen ab; V1-Token, Sicherungen und Installationen werden nicht übernommen oder verändert. Es erfolgt keine Home-Assistant-Installation und kein Neustart.

## V2 DEV 0.1.32 – Projektverwaltung (10.10.2026)

Der sechsteilige Diagnose- und Einstellungsbereich enthält nun **05 · Projektverwaltung**. Die Tabelle zeigt eine persistente, numerische Reihenfolge, Anzeigenamen, Repository, auf Anforderung geprüften Git-Status (vor einer Prüfung neutral), Einstellungen und Pfeile zur Priorisierung. Diese Reihenfolge ist die verbindliche Prioritätsreihenfolge für die spätere Projektliste und für die nur lesende Sammelupdate-Vorschau. Das erste aktive Projekt ist als Standardposition vorgesehen; die spätere DRA-V2-Hauptoberfläche ist noch nicht implementiert.

Unter der Tabelle stehen „+ Projekt hinzufügen“, „Import aus DRA-V1“ sowie „Backup & Retention“. Import aus DRA V1 bleibt selektiv und kopiert keine Zugangsdaten. Die Projektmodalität unterstützt Notiz, Anzeigename, Aktivierung und eine ausdrücklich zu bestätigende Entfernung ausschließlich aus dem V2-Projektregister. V1-Installation, GitHub-Repository und Sicherungen bleiben unverändert.

Die V2-Projekttokens liegen in einem eigenen Home-Assistant-Store „deploy_relay_v2_dev.project_read_auth“ und nicht in V1 oder im Export-Token-Store. Sie werden von der Admin-WebSocket-Schnittstelle nur durch Konfigurationsstatus und die letzten fünf Zeichen repräsentiert (in der Oberfläche grün). Für Quellprüfungen hat das konkrete Projekttoken Vorrang vor dem alten gemeinsamen V2-Lesetoken. Das vollständige Geheimnis wird nie an den Client zurückgegeben. Gespeicherte Secrets befinden sich wie die bisherigen HA-Zugangsdaten in HA-eigenem Storage; hierfür wird kein zusätzlicher kryptografischer Schutz behauptet.

Ein Repositorywechsel wird vor Speicherung über die bestehende schreibgeschützte GitHub-Quellprüfung kontrolliert, danach werden die V2-Zuordnung und die proprietären Projekttokens übertragen. Bei Token-Migrationsfehlern wird versucht, das vorherige Repository wiederherzustellen. Die Operation benötigt zusätzlich eine HA-Realabnahme. Inaktive Projekte werden von der schreibgeschützten Sammelupdate-Vorschau abgelehnt. Installation, Rotation, tatsächliche V2-Sicherungsverwaltung, Neustart und V1-Operationen bleiben gesperrt beziehungsweise unangetastet.

**Abnahmegrenze:** Die Versionskontrolle und automatisierten Tests ersetzen keine HA-Realabnahme. Eine installierbare bzw. schreibende Sammelaktualisierung ist weiterhin nicht freigegeben.

## V2 DEV 0.1.34 – Hauptansicht nach V1-Vorbild (10.10.2026)

DRA V2 DEV öffnet nun eine eigene Hauptansicht mit Kopfleiste (GESPERRT, Aktualisieren, „Diagnose & Einstellungen“), einer auf Desktop/iPad quer angeordneten Projektwahl im oberen Abschnitt, einem vierteiligen geführten Ablauf (1 Stand auswählen; 2 Vorschau prüfen; 3 Schreibzugriff; 4 Installieren), Projektinformation, Quelle & Version, Vorschau sowie Diagnose & Logs. Unterhalb 760 px stehen die Bereiche einspaltig. Das bisherige vollständige V2-Testlabor ist separat über den Schalter oben rechts unter „Diagnose & Einstellungen“ zugänglich.

Schritt 2 startet die bereits existierende schreibgeschützte V2-Quellprüfung der aktuell ausgewählten Projektregistrierung und zeigt den verifizierten Quellstand und die Anzahl der Dateiveränderungen. Dies ist KEIN Kopieren oder Ausführen der V1-Deploymentmechanik. Quell-/Versionsangaben, für die keine geprüften Daten vorliegen, werden als ungeprüft kenntlich gemacht; kein fiktives „ready“ und kein erfundener Git-Stand. Schritt 3 und 4, Backups, Restore und HA-Neustart bleiben deaktiviert. Der Status „GESPERRT“ zeigt die tatsächliche V2-Sperre. Ein laufender Test kann unabhängig vom Oberflächenwechsel weiterlaufen. DRA V1, seine Ansicht, Projekte und Sicherungen werden nicht verändert.

Offen für einen echten produktiven V2-Einsatz: eigenständige sichere Schreibfreigabe, verifizierte Backup-Transaktionen, atomare Installation/Rollback, Wiederherstellung, Restart-Steuerung und deren HA-Realabnahme. Deren Freigabe darf nicht allein aus einer UI-Übernahme abgeleitet werden.

## V2 DEV 0.1.35 – Direkte Referenzwahl in der Hauptansicht (10.10.2026)

Unter „Quelle & Version“ kann die Git-Referenz (Branch, Tag oder Commit; leer für Standardzweig) direkt in der neuen Hauptansicht angegeben werden. Schritt 2 ruft die existierende schreibgeschützte V2-Git-Prüfung für das ausgewählte registrierte Projekt und diese Referenz auf. Ergebnis, Commit und Dateidifferenz-Zähler erscheinen ohne Wechsel in das Untermenü. Die Schritte 3 und 4 bleiben aus Sicherheitsgründen gesperrt, da die eigenständige V2-Transaktionsabnahme noch aussteht.

## V2 DEV 0.1.36 – Mobile Schaltflächenanordnung (10.10.2026)

Die Kopfzeile der V2-Hauptansicht stellt bei Bildschirmbreiten bis 760 px den Status GESPERRT und die Versionsangabe gemeinsam oberhalb der beiden gleichzeilig angeordneten Schaltflächen „Aktualisieren“ und „Diagnose & Einstellungen“ dar. Die Aktionsschaltflächen dürfen dabei nicht auf zwei Zeilen umgebrochen werden; ihre Größen und Abstände wurden für Smartphonebreiten reduziert.

Im Modal „Projekteinstellungen“ erscheinen die drei unteren Aktionen „Projekt entfernen“, „Abbrechen“ und „Speichern“ nebeneinander in einer einzigen Zeile. Auch die Zwei-Schaltflächenvariante beim Hinzufügen von Projekten bleibt in einer Reihe. Für sehr kleine Displays bis 360 px gelten kompaktere Abstände und Schriftgrößen. Die zweistufige Löschbestätigung und alle Backend-Berechtigungen bleiben unverändert. Mobile Darstellung wird im nächsten HA-Realtest visuell abgenommen.

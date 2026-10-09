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

# DRA V2 DEV 0.1.14 – Referenz für zentrales privates Diagnosearchiv

Stand 09.10.2026 | Featurezweig \`feature/v2-10-inventory-operation-contract\` | **Code-/CI-Abnahme; Home-Assistant-Realabnahme ausstehend**

## Verbindliche Referenzen

Die Ausführung richtet sich nach:
- Privatrepository \`TheDaimos/Project-Log-And-Export/README.md\`
- \`docs/EXPORT_STANDARD_V1.md\` im zentralen Privatrepository, insbesondere verbindlicher DRA-V2-Identitätsvertrag vom 09.10.2026
- \`docs/SECURITY.md\` im zentralen Privatrepository.

## Unveränderliche Identität, Metadaten und Ordner

- **Anwendungs-ID:** \`deploy-relay-agent-v2\`, unveränderlich, nie neu vergeben.
- **Anzeigename:** \`Deploy Relay Agent V2\`, ein exportbezogenes Pflichtfeld, darf sich später ändern, ohne technische ID oder Archivordner zu ändern.
- **Version:** tatsächliches \`VERSION\` der laufenden V2-Integration; im Codecheckpoint \`0.1.14\`.
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

- **Festes einziges Ziel:** \`TheDaimos/Project-Log-And-Export\`, Zweig \`main\`.
- **GitHub-Berechtigungen:** eigener *Fine-grained personal access token* oder gleichwertiger eng begrenzter serverseitiger Zugang, nur für **dieses eine private Repository**: \`Contents: Read and write\`, \`Metadata: Read\`. Keine V1-GitHub-Zugangsdaten, kein V2-Quell-Lesetoken und kein historischer V2-Exporttoken.
- **Keine Token-Eingabe im DRA-Browser:** Token kommt ausschließlich aus der **Umgebungsvariable der Home-Assistant-Serverlaufzeit** \`DRA_V2_CENTRAL_EXPORT_TOKEN\`. Der Browser erhält nur \`configured\`/ \`pending\`/ Ziel-ID und später Pfad/Export-ID/Commit des erfolgreichen Uploads.
- **HA-Installation:** Ob und auf welche unterstützte Weise diese Variable in der konkreten HA-DEV-Installationsform gesetzt werden kann, ist vor einer echten Abnahme ausdrücklich zu klären. Keine unbestätigten Änderungen an HA-Konfiguration oder Home-Assistant-Startumgebung vornehmen. Wird die Variable nicht bereitgestellt, gilt \`Nicht eingerichtet\` – es erfolgt **kein Upload**.
- **Zusätzliche Privatsperre:** Vor **jedem** Upload wird die fest bekannte GitHub-Repository-API abgefragt. Muss \`private=true\`, \`full_name=TheDaimos/Project-Log-And-Export\`, \`default_branch=main\` sein; Fehler oder veränderte Sichtbarkeit **blockieren sämtliche Uploads**. Keine Weiterleitung, keine frei bestimmbaren Ziel-URLs.
- **Append-only:** GitHub Contents API wird ausschließlich mit einer **CREATE**-Anfrage ohne \`sha\` beschickt. Ein bereits existierender Pfad kann nicht überschrieben werden; HTTP 409/422 oder fehlerhafte Bestätigung gelten nicht als Erfolg.

## Geheimnisbereinigung, Wiederholung und Status

- DRA V2 übernimmt nur streng validierte, fest definierte **numerische Messfelder** (CPU/RAM/Mehrkern), keine willkürlichen JSON-Einträge, geheimen Werte, Dateipfade, Projektlisten, Tokens oder Auftragskennungen. Verdächtige Inhalte werden **vor Archivierung/Upload abgewiesen**, nicht stillschweigend unbereinigt gespeichert.
- **Lokaler sicherer Rückfall:** Vor Netzübertragung wird genau **ein bereits bereinigter** Export in der eigenen privaten HA-Speicherung \`deploy_relay_v2_dev.archive_queue\` unter \`dra-v2-dev-central-export-queue.v1\` gesichert. Misslingt der Upload, bleibt derselbe Datensatz für einen **expliziten erneuten Versuch** erhalten. Es gibt **keinen** automatischen Export in andere Repositories.
- Beim Laden nach HA-Neustart wird der gesamte gespeicherte Datensatz **einschließlich verschachtelter Messfelder** erneut strikt geprüft. Manipulierte, unvollständige oder unbekannte Versionen führen konservativ zur Ablehnung, ohne dass vorhandene Beweise gelöscht werden.
- **Status in der V2-Oberfläche:** zentraler, privater Zielhinweis, serverseitige Zugangskonfiguration, ausstehender Export, Export-/Wiederholschaltflächen, nach Erfolg genaue Export-ID, Zielpfad und Verweis auf privaten GitHub-Dateieintrag. Ohne Login ins private Repository ist der Link nicht öffentlich einsehbar.
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

**Keine echte private Archivprobe mit vertraulichen HA-Daten durchgeführt.** Ein späterer HA-Realtest benötigt eine gesondert bestätigte, serverseitige Bereitstellung des nur auf \`Project-Log-And-Export\` begrenzten GitHub-Tokens sowie einen explizit ausgelösten Export **künstlicher Daten**. DRA-V1 DEV/PUB, V2-PUB und V2-DEV \`main\` bleiben unverändert; Entwurfs-PR #2 nicht zusammenführen.

# V2-40 – Expliziter Git-Export für synthetische Messdaten (Entwurf und Sicherheitsvertrag)

Stand: 08.10.2026 · Bezug: V1 `custom_components/deploy_relay/github_export.py`, `docs/DIAGNOSTICS.md`, `docs/V2_STUFENPLAN.md`, `docs/V2_40_STATISCHE_ABNAHME_2026-10-08.md`.

## Zweck und Freigabegrenze

Der Nutzer wünscht bereits vor dem nächsten HA-Test den **Export nach Git** analog zu DRA V1. Dies ist ein **separater, ausdrücklich ausgelöster Diagnoseexport** des synthetischen V2-Messlaufs, nicht eine Berechtigung für V2-Installation, Restore oder Auftragsfortsetzung.

Die bisher freigegebenen Zustandsregeln für `deploy_relay_v2_dev`, ein einziger HA-DEV, ein Leseauftrag, begrenztes Journal, keine Leerlauf-Timer und unverändertes DRA V1 gelten vollständig weiter. PR #2 bleibt Entwurf; keine V2-PUB-Bereitstellung.

## V1-Muster, streng für V2 eingeschränkt

1. V1 benutzt einen vom normalen GitHub-Lesetoken **getrennten Fine-grained Schreibtoken**, der ausschließlich serverseitig gehalten wird. V2 verlangt einen **eigenen** Token, ohne V1-Konfigurations-/Speicherzugriff. Nur GitHub `Contents: Read and write` für dieses Repository, sonst keine Rechte.
2. V1 erzeugt eine neue JSON-Datei unter einem reservierten Diagnosepfad, `[skip ci]` im Commit, ohne Überschreiben anderer Dateien. V2: nur `.deploy-relay/diagnostics/v2-dev/YYYY-MM-DD/<UTC>-<Zufall>.json`.
3. Das V2-Ziel-Repository ist fest `TheDaimos/deploy-relay-agent-v2-dev`, der Standardbranch ist derzeit `main`. **Dieses Repository ist öffentlich**. Deshalb werden ausschließlich synthetische aggregierte Zahlen und harmlose konstante Metadaten exportiert; niemals Auftragskennungen, private Projekt-/Repository-Details, Clientdaten, Rohfehler, URLs oder lokale Pfade.
4. Der Export ist **opt-in**: Ein Administrator öffnet das V2-Testlabor, richtet den separaten Git-Token über eine maskierte Eingabe ein, startet einen synthetischen Messlauf und wählt anschließend **„Messdaten nach Git exportieren“**. Keine automatische Übertragung, keine heimlichen Wiederholungen.
5. Konfiguration in einem separaten HA-`Store` unter `deploy_relay_v2_dev.git_auth`. Der Token darf nicht im Versionsjournal `deploy_relay_v2_dev.journal`, in dessen Ereignissen, in WebSocket-Antworten, in exportierten JSON-Dateien oder im Frontend nach dem Speichern stehen. Bei Löschanforderung wird der Wert im Store auf `null` gesetzt.
6. Alle Exportdaten werden serverseitig aus einer festen Positivliste validierter numerischer Messwerte zusammengesetzt. Keine beliebige JSON-Nutzlast vom Client, kein frei wählbares Git-Repository, kein Branch, kein Dateipfad. HTTP-Fehler und ungültige Antworten liefern nur generische Meldungen, keine Antwortkörper/Token. Ein Git-API-Aufruf je bestätigtem Export, mit begrenzter Wartezeit, ohne Leerlaufaktivität.
7. Der Export ist absichtlich eine **eng begrenzte GitHub-Diagnoseschreibaktion**, keine lokale oder entfernte Deploymentschreibaktion. Das reservierte Verzeichnis liegt außerhalb aller durch DRA verwalteten Home-Assistant-Komponenten. Jeder Export erstellt eine einzigartige Datei, niemals bestehende überschreiben.
8. Nur ein gleichzeitig laufender Export. Nach erfolgreichem Commit kann die Oberfläche den Commit und einen verifizierten Link anzeigen. Ein fehlgeschlagener Upload wird nicht als Erfolg gemeldet.

## Abnahmeszenarien vor jeder HA-Änderung

- Git-URL, Repository, Branch und Pfad fest; keine Zeichenketten aus Client-Eingaben können sie beeinflussen; keine Links auf V1 oder andere Projekte.
- Nicht-Administrator darf keinerlei Konfiguration/Upload auslösen; alle Befehle mit `require_admin`.
- Authentisierung nur serverseitig; keine Token in Journal oder Export; abgelehnte Eingaben, Speicherfehler und Git-Fehler ohne Token im Fehlertext.
- Aus Exportdaten ohne Messabschluss, mit unbekannten Schlüsseln oder außerhalb begrenzter Werte wird **keine** Datei übertragen.
- Keine periodische CPU-/I/O-Arbeit und kein Export bei Hausstart, HA-Neustart oder Statusabruf.
- Nur ein neuer zusätzlicher V2-Modulpfad, weiterhin insgesamt höchstens 24 Dateien unter `custom_components/deploy_relay_v2_dev`.
- Python-/JavaScript-Syntax, vollständige Vertragstests, CI und Änderungsvergleich gegen V1 grün.
- **Erst anschließend** DRA-V1-Vorschau und ausdrückliche Benutzerfreigabe für die Installation; bis dahin kein Git-Upload aus HA-DEV.

## Offener Realtest

Nach Freigabe den Messlauf explizit starten, abschließen, Token für **das öffentliche V2-DEV-Repository** einrichten (über den HA-Server, nicht im Chat), Git-Export auslösen und neuen JSON-Pfad samt Commit prüfen. Nur anonymisierte Werte im öffentlichen JSON; kein V1-Projekt und keine privaten Quellen. Ressourcengate V2-40-50 bleibt bis zur gesonderten Messabnahme offen.

## Umsetzungsstand – V2 DEV 0.1.4

- Backend: `custom_components/deploy_relay_v2_dev/git_measurement_export.py` (eigene Tokenablage im Schlüssel `deploy_relay_v2_dev.git_auth`, separater Autorisierungspfad). Der bestehende V2-Journal-Schlüssel bleibt unverändert.
- Zwei zusätzliche, ausschließlich für Administratoren freigeschaltete V2-WebSocket-Befehle: `test/git_configure` und `test/git_export`. Die Statusantwort zeigt nur die booleschen Werte „Git verfügbar/eingerichtet“, niemals den Token.
- Bedienung im V2-DEV-Testlabor: „Git-Export einrichten“, maskierte Token-Eingabe, „Messdaten nach Git exportieren“, „Git-Zugang entfernen“ und verifizierter Link zur erzeugten JSON-Datei. Keine laufenden Abfragen bei Ruhe.
- Übertragene Felder: festes Schema/Version/Modus, UTC-Exportzeit, feste öffentliche Zielidentität und validierte Messzähler. **Keine** Auftragskennung, freie Texte, lokale Konfiguration, Rohlogs, private Projektangaben oder Token im JSON.
- GitHub Contents API: eine manuelle `PUT`-Erstellung pro Export (HTTP 201), eindeutiger Dateiname, 10-Sekunden-Zeitlimit, keine automatische Wiederholung und höchstens ein gleichzeitig laufender Git-Export. Commit-Nachricht mit `[skip ci]`.
- Die Tests verwenden ausschließlich Fake-Store/Fake-Session und laden **keine** Datei nach GitHub hoch. Die Realabnahme steht aus; bis dahin sind Einrichtung und Upload auf HA-DEV noch nicht verfügbar.

### Sicherheits-/Review-Hinweis

Das V2-DEV-Repository ist **öffentlich**. Der Export erfolgt nur auf ausdrückliches Drücken der Schaltfläche und ist eine eng begrenzte Diagnose-Gitschreibaktion, keine Deploymentmutation. Ein eigenes Fine-grained GitHub-Zugangstoken darf nur serverseitig im Home-Assistant-Konfigurationsspeicher konfiguriert werden (nicht im Chat oder im Quellcode). Für das produktive V2 ist diese Funktion ohne erneute Freigabe nicht automatisch übertragen.

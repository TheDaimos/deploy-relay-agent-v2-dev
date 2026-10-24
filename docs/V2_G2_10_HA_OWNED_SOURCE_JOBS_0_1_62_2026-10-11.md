# DRA V2 DEV 0.1.62 – G2-10: HA-eigene Quellprüfaufträge und Wiederverbindung

**Stand:** 11.10.2026  
**Zweig:** `feature/v2-10-inventory-operation-contract`  
**Status:** Implementiert und durch isolierte Verträge sowie JavaScript-/Sicherheits-CI geprüft. **HA-Realtest noch offen.**

## Ausgangslage und Ziel

Seit 0.1.61 besteht die vollständige, rein lesende Gewitterradar-Quellprüfung den HA-Realtest. Bisher steuerte aber ein einzelner WebSocket-Aufruf vom Browser den gesamten bis zu 45 Sekunden dauernden GitHub- und HA-Dateivergleich. Ein Verlust des Browserfensters konnte die Rückmeldung vom Server trennen.

**G2-10 löst den Eigentümerwechsel nur für schreibgeschützte Quellprüfungen:** Home Assistant nimmt eine neue Auftragskennung an und führt den fest gebundenen Prüfauftrag über eine von der **ConfigEntry** besessene Hintergrundaufgabe aus. Der Browser erhält die Kennung zurück, fragt den Zustand erneut ab und kann nach Schließen/Neuöffnen derselben HA-Laufzeit auch ein abgeschlossenes Ergebnis anzeigen. Die Quelle bleibt dieselbe bereits registrierte und vom Backend geprüfte Quelle.

## Änderungen

- Neue strikt lesende und begrenzte Komponente `source_preview_jobs.py`, **maximal ein aktiver Auftrag**, höchstens vier aktuelle Auftragsstände im Arbeitsspeicher, keine beliebige ausführbare Aktion, keine Dateisystemschreiber und keine Tokens in Ergebnissen. Ein erneuter Aufruf mit identischer Repository-/Referenzkombination bekommt die bestehende Kennung und startet keinen zweiten parallelen Auftrag.
- Serverseitige Registrierung ausschließlich für bekannte Projekte, validierte Git-Referenzen, bestehende SHA-gepinnte und lokal lesende `_inspect_source_preview`-Routine. Äußeres 45-Sekunden-Limit unverändert; keine neuen GitHub-Berechtigungen.
- Admin-pflichtige HA-WebSocket-Routen:
  - `deploy_relay_v2_dev/projects/source_job/start` (angenommener Auftrag oder sicherer Fehler);
  - `deploy_relay_v2_dev/projects/source_job/status` (letzter oder konkret benannter Auftrag).
- Die ältere rein lesende `projects/source_preview` bleibt während der kontrollierten Umstellung vorhanden, um andere bestehende Diagnoseabläufe nicht unbemerkt zu brechen.
- Mobile V2-Hauptseite: die zentrale Schaltfläche `1/4 · Vorschau berechnen` startet künftig nur den neuen servereigenen Auftrag. Serverstatus wird unabhängig vom ursprünglichen Anforderungsfenster abgefragt. Nach Neuöffnung wird nur ein auf dasselbe ausgewählte Projekt und denselben Ref passender Erfolg als Vorschau angezeigt. Sichtbare 12-stellige Auftragskennung erleichtert Screenshots und Logzuordnung.
- `async_unload_entry` beendet noch laufende read-only Quellprüfungen über die ConfigEntry; auf Integrationsentladung folgt niemals ein unbeaufsichtigter Schreibvorgang. Bereits abgeschlossene Ergebnisse bleiben nur während derselben HA-Laufzeit gespeichert.
- Positive Erfolgsauswertung nur bei serverintern erstelltem, commit-genauem Vorschauvertrag `dra-v2-dev-source-preview.v1` und weiterhin explizit verweigertem Besitz, Lock, Sicherung und Installation. Defekte Ergebnisse, Exceptions, Abbrüche, Ressourcenprobleme und Fremdprojekte werden konservativ zurückgewiesen.

## Realistische Sicherheits- und Leistungsgrenzen

- **Keine dauerhafte Wiederaufnahme nach Home-Assistant-Neustart.** Dieses erste G2-10-Paket speichert den Ergebnisbericht nur in einem begrenzten Runtime-Puffer. Ein HA-Neustart unterbricht aktive Leseaufträge; ein späterer Auftrag benötigt frische Commit-/Quellprüfung. Der bestehende, separat gespeicherte V2-Journalvertrag für synthetische Messungen wird nicht als funktionierende persistente Quellauftragsverwaltung ausgegeben.
- **Kein echtes serverseitiges Sammelupdate:** Noch keine gesicherte V1/V2-Zielübergabe, tatsächliche V2-eigene Sicherung, Restore, Installation, Neustart oder Selbstupdate. Stufen 2 bis 4 bleiben gesperrt.
- Browserwechsel während desselben HA-Laufs ist vom Code und isolierten Tests abgedeckt; **echter Android-/WLAN-Wechsel muss separat in HA abgenommen werden**.
- Keine Änderung an V1 DEV/PUB, V2 PUB, V2-main, WeatherRouter oder dem privaten Exportarchiv; PR #2 weiter Entwurf und nicht zusammenführen.
- Alle echten Diagnosedateien weiterhin ausschließlich im privaten Zentralarchiv `TheDaimos/Project-Log-And-Export`. Der gewöhnliche Quellprüfbericht enthält weiterhin keine Rohdateien, Token oder privaten HTTP-Antwortdaten.

## Tests und Abnahme

`tests/test_v2_source_preview_jobs.py`:
- serverseitige Fortführung nach Wegfall des aufrufenden Browsers;
- gleiche Auftragskennung bei wiederholtem Aufruf; Ablehnung eines konkurrierenden anderen Projekts;
- Auftragsabruf, reine Kopien der Ergebnisse, begrenzte Aufbewahrung;
- Fehler-, ungültige Erfolgs- und fehlende Sicherheitsflag-Fälle, die niemals Schreibberechtigung erzeugen;
- Entladung während laufender Aufgabe erzeugt `interrupted` und stoppt den Auftrag;
- ungültige Git-Referenzen/Repositorykennungen abweisen.

`tests/test_v2_countdown.js` verifiziert die zentrale Vierstufen-Bedienung über die neuen Start-/Status-Nachrichten sowie das Wiederanzeigen einer bereits fertig geprüften Quelle in einem neuen Frontend-Zustand. Zusätzliche WebSocket-Isolationsprüfungen prüfen insgesamt 34 administrative Routen. `deploy-relay.json` erlaubt ausschließlich die neue Moduldatei als Bestandteil der isolierten V2-Komponente.

**Nächste HA-Abnahme (ein Schritt):** Betreiber installiert V2 DEV 0.1.62 eigenständig über DRA V1 auf dem bekannten HA-DEV-System und testet einmal Gewitterradar mit `Vorschau berechnen`. Bestätigen, dass die Auftragskennung und am Ende das lesende Vorschauergebnis erscheinen. Ein gesonderter WLAN-/Neuöffnen-Test folgt erst nach diesem Grundtest. Keine automatische Installation oder Neustart aus dem Chat.

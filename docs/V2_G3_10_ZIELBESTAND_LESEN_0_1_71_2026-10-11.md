# DRA V2 DEV 0.1.71 – G3-10: schreibgeschützte Zielbelegung

**Datum:** 11.10.2026  
**Entwicklungszweig:** `feature/v2-10-inventory-operation-contract`  
**Gate:** G3 – Fremd-/V1-Besitz und prozessübergreifende Sperre  
**Status:** Rein lesendes Modul **CI-geprüft**: [GitHub Actions 38172938303](https://github.com/TheDaimos/deploy-relay-agent-v2-dev/actions/runs/38172938303), **SUCCESS** auf Code-Checkpoint `1e97126b5f3c2d5525a459949696e1b732a6b292`. **Kein Nachweis von Dateibesitz oder prozessübergreifender Exklusivität; keine Installationsfreigabe.** Noch keine HA-Anbindung oder HA-Realabnahme.

## Ausgangslage

G2 wurde mit Home-Assistant-Realtests zum Clientwechsel, WLAN/5G-VPN-Wechsel, unterbrochenen HA-Neustart und dem kontrollierten Wiederholversand in das private Git-Archiv abgeschlossen. DRA V2 DEV 0.1.70 erhielt zusätzlich die vom Betreiber bestätigte kompakte Darstellung des Status unter der Überschrift „Serverseitige Auftragshistorie“.

Der alte `target_ownership.py`-Vertrag erkennt nur **berechnete** Kollisionen von Manifestzielen; weder ein leerer externer Belegungsbericht noch eine erfolgreiche V1-Installation beweist exklusiven V2-Besitz.

## Neuer begrenzter Baustein: `target_presence.py`

- Erwartet nur **vom Server festgelegte** HA-Konfigurationswurzel und höchstens 32 streng normalisierte Ziele `custom_components/<name>`. Keine frei vom Browser mitgelieferten Pfade zulässig. Gesperrte V1-/V2-Verzeichnisse, Traversals und doppelte Pfade (auch durch Groß-/Kleinschreibung) werden abgelehnt.
- Öffnet die Konfigurationswurzel und ihren direkten `custom_components`-Ordner **nur lesend**, mit `O_DIRECTORY` und `O_NOFOLLOW`; verfolgt weder Symlinks noch öffnet es Projektdateien.
- Liest maximal 2048 Namen im direkten Integrationsverzeichnis. Für die fest ausgewählten Verzeichnisnamen prüft es `stat(..., follow_symlinks=False)`. Es liest **keine** Dateiinhalte, V1-Speicherdateien, Schlüssel oder Backups, erzeugt keine Dateien und verändert keine Zielbytes.
- Ein Ergebnis kennt ausschließlich `present`, `absent`, `ambiguous` (Groß-/Kleinschreibung kollidiert), `unsafe` (Symlink/nicht regulärer Ordner) oder `unavailable` (Beobachtung nicht möglich). Ein Fehler beim Elternverzeichnis oder der Verzeichnisgrenze **bricht die Beobachtung ab**, keine Freigabe.
- Jedes Ergebnis ist bewusst **`ownership=unverified`**; es gibt **keine** Aussage zur V1-Inaktivität oder zu Fremdprozessen. Auch `absent` ist nur eine augenblickliche Beobachtung und kein dauerhaftes Recht auf Anlegen.
- Für jeden positiven wie negativen Pfad bleiben `owner_identity_verified=false`, `v1_handover_verified=false`, `cross_process_lock_verified=false`, `backup_verified=false`, `source_binding_verified=false`, `handover_required=true`, `installation_enabled=false` und `parallel_installation_enabled=false`.
- Die Beobachtung ist **noch nicht** in die HA-WebSocket-Schnittstellen, die normale Benutzeroberfläche oder einen Installationspfad integriert. Dies verhindert, dass eine lokale Dateiliste bereits als Besitzabnahme missverstanden wird.

## Sicherheit und negative Tests

Die neuen isolierten Tests benutzen ausschließlich künstliche temporäre Verzeichnisse: vorhanden/nicht vorhanden, reine Dateien, symbolische Verknüpfungen, gesperrte V1-/V2-Ziele, uneindeutige Groß-/Kleinschreibung, ungültige Ziele, fehlende oder ersetzte Elternverzeichnisse, überlange Listen und während der Beobachtung verschwundene Einträge. Es gibt eine explizite Prüfung, dass keine Projektdateiinhalte gelesen werden und jede Beobachtung gesperrt bleibt.

**Dateiobergrenze:** Das isolierte V2-DEV-Installationsmanifest wurde für die **exakt eine** hinzugefügte Python-Datei von 27 auf **28** erlaubt. Der Isolationstest fixiert diese Zahl ausdrücklich, die Byteobergrenze 3 MiB und die einzige isolierte Deployment-Zielwurzel bleiben unverändert. Keine Änderung des V1-Zielpfads oder produktiven HACS-Kanals.

## G3-20 Folgebefund: aktuelle V1-Sperren reichen nicht als V2-Nachweis

Der vorhandene aktuelle DRA-V1-DEV- und V1-PUB-Quellcode wurde separat **ausschließlich lesend** geprüft. `deployment_lock` und `resource_lock` sind V1-eigene `asyncio.Lock`-Instanzen. In den geprüften V1-Installationspfaden gibt es keine V2-gemeinsam verifizierte prozessübergreifende Zielübergabe. Deshalb kann das G3-10-Verzeichnisinventar selbst bei `present` oder `absent` **niemals** einen gültigen exklusiven V2-Besitz nachweisen.

[Verbindlicher G3-20-Sperrenbefund und Übergabeblockade](V2_G3_20_V1_SPERREN_AUDIT_2026-10-11.md). Kein Ändern von DRA V1 im aktuellen Auftrag; solange keine gesondert genehmigte Kooperation vorhanden ist, bleibt V2-Installation blockiert.

## Nächste bindende G3-Gates

- **G3-20:** Vertrauensbewertung für tatsächlich unabhängig überprüfte V1-/Fremdbelegung entwerfen und serverseitig mit Herkunft/Zeit/Ziel-/Quellidentität verbinden. Das Hinzufügen eines Eigentümerlabels durch den Benutzer ist kein technischer Besitzbeleg.
- **G3-30:** Eine exklusive, prozessübergreifende Sperre und nach Neustart verifizierbaren V1→V2-Übergabevertrag klären. Ist die Mitarbeit von V1 nötig und ohne V1-Änderung nicht nachweisbar, ist V2 dauerhaft schreibgesperrt.
- **G3-40:** Negativtests zu fremden Schreibern, unklarer Belegung, Quellenwechsel, abgelaufener/inkonsistenter Beweislage und OS-Rennen. Anschließend eine separat vereinbarte rein lesende HA-DEV-Realabnahme.

**Keine automatische V2-Installation, Sicherung, Rücksicherung, Transaktion, eigener Neustart oder V1-Änderung.** V2 `main`/PUB, WeatherRouter und das private Exportarchiv bleiben unangetastet; Draft-PR #2 bleibt unmerged. Keine realen HA-Diagnosen in dieses öffentliche Entwicklungsrepository.

**C.K. – Eine Idee weiter gedacht.**

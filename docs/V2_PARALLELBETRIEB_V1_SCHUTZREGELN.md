# DRA V2 – sicherer Parallelbetrieb auf einer einzigen Home-Assistant-Instanz

> **Standnachtrag (08.10.2026):** Die historische Aussage „noch nicht installierbar“ im Konzept wurde durch die gesondert isolierte `deploy_relay_v2_dev`-Testintegration überholt: Realer Parallelbetrieb mit DRA V1 einschließlich Gewitterradar-Update und HA-Neustart wurde bestätigt. Alle Schutzregeln behalten ihre Gültigkeit. Die V2-40-Journalversion 0.1.1 ist bis zur erneuten Vorschau und Freigabe **noch nicht auf HA-DEV aktualisiert**. Siehe `docs/V2_40_STATISCHE_ABNAHME_2026-10-08.md`.

Stand: 08.10.2026. Der Projektinhaber hat nur **eine HA-DEV-Instanz** und benötigt die unverändert nutzbare DRA V1 **während** des gesamten V2-Umbaus. Eine zweite HA-VM oder ein zweiter HA-Core sind ausdrücklich **keine Voraussetzung**. Dieser Beschluss ersetzt den früheren Vorschlag einer zweiten HA-Instanz.

## Verbindliches Ziel

V1 bleibt unter `custom_components/deploy_relay` und der HA-Domäne `deploy_relay` uneingeschränkt in Betrieb. Die parallel testbare V2-Funktion wird zunächst als **schreibgeschützter, separat benannter DEV-Testbaustein** für dieselbe HA-Instanz geplant; mögliche Kennung `deploy_relay_v2_dev`. Er erhält ausschließlich neue HA-Einträge, Befehle und Speicherpfade. Der spätere produktive V2-Upgradepfad wird separat entwickelt und muss weiterhin V1-Konfigurationen korrekt migrieren.

**Noch nicht installierbar:** Der aktuelle V2-DEV-Quellstand benutzt wie V1 `custom_components/deploy_relay`, `domain: deploy_relay`, `single_config_entry: true`. Das Hinzufügen als Repository ist gefahrlos, eine Installation auf diesem gemeinsamen Pfad **nicht**. Kein realer V2-Test, bis die vollständige Isolation automatisch geprüft ist.

## Technisch geprüfte Kollisionsstellen

- Integrationsverzeichnis, `manifest.json`-Domäne, Konfigurationsablauf und Eintragskennung: `deploy_relay`.
- WebSocket: hart kodierte `deploy_relay/panel/*`-Befehle im Backend **und** in beiden JavaScript-Komponenten.
- HA-Seitenleiste: `deploy-relay`, statische URL `/deploy_relay_static`, Element `deploy-relay-panel` sowie `deploy-relay-diagnostics-panel`.
- `hass.data[DOMAIN]`, Projekt- und Neustartkennzeichen.
- Dateien unter `/config/deploy_relay`: Diagnose, Transaktionen, Sicherungen, Staging und Aufbewahrung; Teile dieser Pfade sind in `deployment.py` direkt als Zeichenfolge codiert.
- Gemeinsame **Zielprojektdateien** unter demselben HA-`/config` können selbst bei getrennten DRA-Arbeitsordnern kollidieren.

Eine reine Umbenennung der Integrationsdomäne ist **nicht ausreichend**. Das spätere V2-DEV-Testpaket muss nachweislich keine V1-Pfade/Befehle überschreiben und **darf keinerlei Mutation der Projektdateien anbieten**.

## Entwicklungs- und Testschritte

1. Einen kleinen **separaten, nur lesenden Testbaustein** im V2-DEV-Repository planen. Er darf den bereits isolierten V2-Auftragsmanager verwenden, ohne die bisherige V1-Laufzeit zu importieren, zu ersetzen oder zu registrieren.
2. Alle Testbaustein-Namen/Dateien auf `deploy_relay_v2_dev` und eigenständige WebSocket-/Oberflächenkennungen begrenzen; keine Duplikate aus dem aktiven V1-Installationsordner mit denselben Zeichenfolgen installieren.
3. Serverseitige Adminprüfung für Start/List/Get; vorerst nur synthetische oder nachweislich read-only Vorschauarbeit. **Keine** Install-/Restore-/Backup-Bereinigung/Selbstupdate-/Neustart-Befehle, keine beliebige Dateipfad- oder Funktionsauswahl durch Clients.
4. Beim Leerlauf keine periodischen Scanner, Browserzeitgeber, Dateischleifen oder zusätzlichen CPU-Arbeiter; begrenzte Ereignisse und Speicheraufbewahrung; Ressourcenverbrauch auf dem vorhandenen HA-DEV messen.
5. Reproduzierbaren Quellen-/Namensraum-Audit und Tests ergänzen: V1- und Testbaustein-Manifest, UI-IDs, WebSocket-Namen, Speicher-/Transaktionspfade und geschützte Projektziele dürfen nicht kollidieren.
6. Erst nach grünem Testlauf, nachvollziehbarem SHA und freigegebenem Rückfallweg wird eine genaue **Installations- und Klickanleitung für die vorhandene HA-DEV-Instanz** erstellt.
7. Realtest: V1 funktioniert davor, währenddessen und danach; am Handy read-only V2-Auftrag starten, Verbindung trennen, am Notebook denselben Auftrag wiederfinden; CPU/RAM und HA-Reaktionsfähigkeit beobachten.
8. Schreibtätige V2-Funktionen ausschließlich später über den separaten, ausfallsicheren V2-Upgrade-/Recoverypfad abnehmen, ohne gleichzeitige V1-Schreiboperationen gegen dieselben Ziele zuzulassen.

## Sicherheits- und Freigabestatus

**Ein HA-DEV genügt**; kein zweiter Core, keine zweite VM nötig. Bis zur vollständigen Trennungsprüfung jedoch **keine V2-Installation aus dem gegenwärtigen Repository auf derselben HA-Konfiguration**. V1-Quellrepos, laufende V1-Integration und V2-PUB bleiben unverändert.

Status: **KONZEPT AKTUALISIERT / NAMESPACES UND TECHNISCHE ISOLATION NOCH OFFEN**. Kein realer V2-Test und keine RELEASE-Freigabe erfolgt.

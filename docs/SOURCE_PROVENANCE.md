# Provenienz der öffentlichen DRA-V2-Entwicklungsbasis

Stand: 08.10.2026. **Noch keine V2-Laufzeitimplementierung.**

| Ebene | Öffentlicher Nachweis |
| --- | --- |
| Ursprüngliche, bereits veröffentlichte V1-Quelle | `TheDaimos/deploy-relay-agent-pub@0c9d7f49f080dfe77b6c3910f89d6a61ae4b8cfa` |
| Daraus erzeugte öffentliche V2-Stagingbasis | `TheDaimos/deploy-relay-agent-v2-pub@b3e09d4e43d28a5d0805591fad411d3a4a007825` |
| Neuer Entwicklungsquellstand | `TheDaimos/deploy-relay-agent-v2-dev`, neue eigenständige Git-Historie |
| Anzahl überprüfter Dateien | 52 Dateien aus der öffentlichen Stagingbasis; diese Datei und README werden für die DEV-Rolle gezielt angepasst |
| Ursprüngliche Integrationslaufzeit | `1.0.0`, unverändert und **nicht als V2 freigegeben** |
| Private DEV-Git-Historie, Diagnose-Exporte, Konfigurations- und Sicherungsdateien | Nicht übernommen |
| Rechtliche Grundlage | `GPL-3.0-only` für Software, getrennte Marken-/Logo-Rechte in `BRANDING.md` |

Die Ursprungsdateien wurden ausschließlich über **öffentliche Repositories** geladen und Git-Blob für Git-Blob verglichen. Das Übernahmeverfahren überprüfte die Gleichheit jedes gespeicherten Binär-/Textblobs mit dem öffentlichen Quell-Git-SHA. Die Entwicklungsdokumentation nennt ausdrücklich dieses Repository als **DEV**, `v2-pub` dagegen als zukünftigen Veröffentlichungskanal.

## Branding

`custom_components/deploy_relay/brand/icon.png`: `eca8b2a1261b4f60f26d9ba6d31c96c6e3c9f437` (256 × 256).

`custom_components/deploy_relay/brand/icon@2x.png`: `f1b2ae67b73d7bd408779e4e553f5c4452dc47b9` (512 × 512).

Die enthaltenen offiziellen DRA-Markengrafiken stammen aus dem öffentlichen V1-Quellpaket und wurden nicht verändert.

## Freigabestufen

Das private V1-DEV-Repository und die aktuelle V1-HACS-Auslieferung werden nicht geändert. V2-Entwicklung und -Tests finden nach der V1-Finalabnahme hier in `v2-dev` statt. Nur **explizit abgenommene** V2-Zustände werden später kontrolliert und prüfwertgesichert in `v2-pub` veröffentlicht. Keine automatische Übernahme eines Entwicklungszweigs und kein implizites HACS-Release.

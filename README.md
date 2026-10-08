# Deploy Relay Agent V2 – öffentliche Entwicklung

**Status: Entwicklungsvorbereitung, kein freigegebener V2-Installationsstand.**

Dies ist das **öffentliche Entwicklungsrepository** von Deploy Relay Agent V2, einer Home-Assistant-Integration zur sicheren Übernahme ausgewählter Git-Projektstände.

## Repository-Aufteilung

| Repository | Aufgabe |
| --- | --- |
| [deploy-relay-agent-v2-dev](https://github.com/TheDaimos/deploy-relay-agent-v2-dev) | **Entwicklung**, Quellcode, automatische Tests, Architektur und Abnahmevorbereitung |
| [deploy-relay-agent-v2-pub](https://github.com/TheDaimos/deploy-relay-agent-v2-pub) | **Veröffentlichungskanal** für später ausdrücklich freigegebene V2-Integrationspakete |
| [deploy-relay-agent-pub](https://github.com/TheDaimos/deploy-relay-agent-pub) | Bisherige öffentliche V1-HACS-Auslieferung |
| `deploy-relay-agent-dev` (privat) | Bisheriger privater V1-Referenz- und Entwicklungsstand |

## Öffentliche Ausgangsbasis

Die Ausgangsdateien stammen aus dem **bereits öffentlichen** V1-Code. Die 52 Dateien des vorbereiteten öffentlichen V2-Repositorys wurden anhand ihrer Git-Blobs in dieses neu angelegte Entwicklungsrepository übernommen. Die vollständige Herkunft ist in [SOURCE_PROVENANCE.md](docs/SOURCE_PROVENANCE.md) dokumentiert. Weder private Git-Historie noch lokale Home-Assistant-Diagnosen wurden übernommen.

Die Integration meldet weiterhin **Version 1.0.0**, weil noch keine V2-Laufzeitänderung freigegeben ist. **Nicht als HACS-V2-Release installieren.**

## Geplante Schwerpunkte

- Laufende Aufträge gehören dem Home-Assistant-Backend, nicht dem Browser.
- Sichere Wiederverbindung nach WLAN-/Mobilfunkwechsel oder Schließen der App.
- Serverseitige Warteschlangen, Sperren und Sammelupdates.
- Unveränderte Schranken für Schreibzugriff, SHA, Vorschau, Sicherung, Verifikation und Wiederherstellung.
- Ressourcen-, Mobil- und Browserlast reduzieren.
- Diagnose- und Protokollausgabe vereinheitlichen, ohne Geheimnisse zu veröffentlichen.
- Native HA-Integrationsansicht mit DRA-Logo und unabhängigem Oberflächenzugang aufwerten.

Der verbindliche Ablauf steht in [docs/V2_ROADMAP.md](docs/V2_ROADMAP.md). Vor jeder Umsetzung sind die genauen Phasen-Abnahmekriterien zu prüfen; V1 muss zunächst abgeschlossen sein.

## Automatische Prüfungen

GitHub Actions nutzt hier **öffentliche Standard-Runner** mit minimalen Berechtigungen und **ohne Artefaktupload**. Push- und PR-Prüfungen sind durch Pfadfilter und Abbruch veralteter Läufe begrenzt. Prüfungen sind keine produktive V2-Freigabe.

Sicherheits- und Beitragsregeln: [AGENTS.md](AGENTS.md), [CONTRIBUTING.md](CONTRIBUTING.md), [PUBLIC_DEVELOPMENT_POLICY.md](docs/PUBLIC_DEVELOPMENT_POLICY.md). Lizenz und offizielle Markenbilder: [LICENSE](LICENSE), [BRANDING.md](BRANDING.md).

**C.K. – Eine Idee weiter gedacht.**

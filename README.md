# Deploy Relay Agent V2 – öffentliche Entwicklung

**Status: DRA V2 DEV 0.1.54 – isolierte Home-Assistant-Testintegration; weder V2-FINAL noch HACS- oder Installationsfreigabe.**

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

Die übernommene **historische Ausgangsbasis** meldete Version 1.0.0. Der aktuelle **V2-DEV-Testlaborstand ist 0.1.54** unter `custom_components/deploy_relay_v2_dev` mit eigener Domain; die ursprüngliche V1-Komponente bleibt als öffentliche Referenz unangetastet. **Keine produktive V2-Installation, keine automatische HA-Installation und kein Neustart aus V2 freigegeben.**

## Aktueller Entwicklungsstand (11.10.2026)

Das getrennte V2-DEV-Testlabor enthält Projektverwaltung, GitHub-Lesezugänge, eine echte **schreibgeschützte** Einzelquellvorschau, gesonderte Lese-Messaufträge mit begrenztem Journal und private Diagnoseexporte ausschließlich in das vom Administrator konfigurierte zentrale Archiv. Die Bedienoberfläche nutzt eine zentrale vierstufige Deployment-Schaltfläche; nur die Vorschau ist betriebsfähig, weitere Stufen bleiben gesperrt.

Seit **0.1.54** überprüft ein rein berechnender Zielbesitzvertrag bekannte Kollisionen zwischen Projektzielwurzeln, einschließlich case-insensitiver Dopplungen. Ein kollisionsfreier Bericht beweist **keinen** exklusiven V2-Besitz und entsperrt **keine** Mutation. Referenz: [Zielbesitz-/Kollisionsvertrag](docs/V2_TARGET_OWNERSHIP_AND_CONFLICT_GATE_2026-10-11.md) und [aktuelle Projektübergabe](docs/HANDOFF_DRA_V2_DEV_0_1_53_2026-10-11.md).

Nicht vorhanden/freigegeben: tatsächliche V2-eigene Sicherungsarchive, unabhängige Wiederherstellung, transaktionale Installation, parallele Sammelinstallation oder V2-Neustartsteuerung. Die jüngsten UI-Änderungen sind noch auf HA/Android real abzunehmen.

## Geplante Schwerpunkte

- Laufende Aufträge gehören dem Home-Assistant-Backend, nicht dem Browser.
- Sichere Wiederverbindung nach WLAN-/Mobilfunkwechsel oder Schließen der App.
- Serverseitige Warteschlangen, Sperren und Sammelupdates.
- Unveränderte Schranken für Schreibzugriff, SHA, Vorschau, Sicherung, Verifikation und Wiederherstellung.
- Ressourcen-, Mobil- und Browserlast reduzieren.
- Diagnose- und Protokollausgabe vereinheitlichen, ohne Geheimnisse zu veröffentlichen.
- Native HA-Integrationsansicht mit DRA-Logo und unabhängigem Oberflächenzugang aufwerten.

Der verbindliche Ablauf steht in [docs/V2_ROADMAP.md](docs/V2_ROADMAP.md). Die gültigen Sicherheits- und Abnahmekriterien gelten weiterhin; der ursprüngliche Plan enthält ältere Vorbereitungsformulierungen. Die V1-Referenz bleibt bestehen, und neue V2-Schreibfunktionen erfordern gesonderte Abnahmen.

## Automatische Prüfungen

GitHub Actions nutzt hier **öffentliche Standard-Runner** mit minimalen Berechtigungen und **ohne Artefaktupload**. Push- und PR-Prüfungen sind durch Pfadfilter und Abbruch veralteter Läufe begrenzt. Prüfungen sind keine produktive V2-Freigabe.

Sicherheits- und Beitragsregeln: [AGENTS.md](AGENTS.md), [CONTRIBUTING.md](CONTRIBUTING.md), [PUBLIC_DEVELOPMENT_POLICY.md](docs/PUBLIC_DEVELOPMENT_POLICY.md). Lizenz und offizielle Markenbilder: [LICENSE](LICENSE), [BRANDING.md](BRANDING.md).

**C.K. – Eine Idee weiter gedacht.**

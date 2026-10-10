# DRA V2 – aktueller Projekt-Einstiegspunkt

**Stand:** 11.10.2026 – DRA V2 DEV **0.1.54** (isoliertes Home-Assistant-Testlabor, **keine V2-FINAL-/HACS-Freigabe**).

## Für jede Fortsetzung

1. Globalen Einstieg `TheDaimos/project-defaults/START_HERE.md` lesen (Daimos-Bootstrap, Erinnerungsschutz).
2. `AGENTS.md` und diese Datei im Repository lesen.
3. **Verbindliche aktuelle Chatübergabe:** [HANDOFF_DRA_V2_DEV_0_1_53_2026-10-11.md](HANDOFF_DRA_V2_DEV_0_1_53_2026-10-11.md) **vollständig lesen**; erst danach nach Bedarf `docs/V2_ROADMAP.md`, `docs/V2_B2_PREFLIGHT_BACKUP_INTEGRITY_2026-10-09.md` und die umfangreiche chronologische `docs/V2_CENTRAL_PRIVATE_DIAGNOSTICS_2026-10-09.md` öffnen.
4. **Einzig zulässiger Arbeitszweig:** `feature/v2-10-inventory-operation-contract`. **Historischer UI-Codecheckpoint 0.1.53**: `6d738aafec358d96013a763c9397a18a7ebca894` (CI `38088703225`: SUCCESS). **Neu 0.1.54**: schreibgeschützter Zielbesitz-/Kollisionsvertrag mit Tests, dokumentiert in `docs/V2_TARGET_OWNERSHIP_AND_CONFLICT_GATE_2026-10-11.md`. Neuen HEAD und aktuelle CI vor weiteren Änderungen prüfen.
5. Die V2-DEV-Oberfläche besitzt eine **einzige zentrale Deployment-Schaltfläche**, vier Statusstufen und die DRA-V1-Ladebalken-Animation. **Schreibgeschützte Einzelvorschau funktioniert**; Schreibfreigabe, echte Installation, V2-Backup und Restore, parallele Sammelinstallation und Restart-Orchestrierung sind **gesperrt/nicht abgenommen**. HA-/Android-Realabnahme des jüngsten UI-Standes noch offen.
6. **Neu 0.1.54:** Die admin-pflichtige Einzelquellvorschau enthält `target_claims`; doppelte Zielwurzeln (auch Groß-/Kleinschreibung) und projektübergreifende Kollisionen sind als rein berechnender Vertrag prüfbar. **Ein konfliktfreier Befund beweist weiterhin keinen exklusiven V2-Besitz, keinen V1-Lock und keine verifizierte echte Sicherung. Installieren und paralleles Sammelupdate bleiben gesperrt.**
7. **Schutzgrenzen:** DRA V1 DEV/PUB, V2 PUB, V2 DEV `main`, WeatherRouter und das private Exportarchiv nicht verändern; Draft-PR #2 nicht zusammenführen. Neue echte Diagnose-/HA-/Testexporte dürfen ausschließlich in das **private** `TheDaimos/Project-Log-And-Export` gelangen; niemals in dieses öffentliche Repo.
8. **Nächster Arbeitsschwerpunkt:** sichere serverseitige Auftrags-/Transaktionsarchitektur, nachweislich vollständige eigene Backups und unabhängiger Rückfall, dann schrittweise explizit freigegebene Installation und konfliktsichere parallele Sammelaktualisierung. **Keine automatische HA-Installation/kein Neustart.**

**Hinweis zur Historie:** Die ursprünglichen Formulierungen in älteren README-/Roadmap-Dateien beziehen sich auf den V2-Vorbereitungsstand; die laufende V2-DEV-Integration hat bereits Version 0.1.53, jedoch weiterhin keine Installationsfreigabe.

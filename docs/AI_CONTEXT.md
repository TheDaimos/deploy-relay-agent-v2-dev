# DRA V2 – aktueller Projekt-Einstiegspunkt

**Stand:** 11.10.2026 – DRA V2 DEV **0.1.53** (isoliertes Home-Assistant-Testlabor, **keine V2-FINAL-/HACS-Freigabe**).

## Für jede Fortsetzung

1. Globalen Einstieg `TheDaimos/project-defaults/START_HERE.md` lesen (Daimos-Bootstrap, Erinnerungsschutz).
2. `AGENTS.md` und diese Datei im Repository lesen.
3. **Verbindliche aktuelle Chatübergabe:** [HANDOFF_DRA_V2_DEV_0_1_53_2026-10-11.md](HANDOFF_DRA_V2_DEV_0_1_53_2026-10-11.md) **vollständig lesen**; erst danach nach Bedarf `docs/V2_ROADMAP.md`, `docs/V2_B2_PREFLIGHT_BACKUP_INTEGRITY_2026-10-09.md` und die umfangreiche chronologische `docs/V2_CENTRAL_PRIVATE_DIAGNOSTICS_2026-10-09.md` öffnen.
4. **Einzig zulässiger Arbeitszweig:** `feature/v2-10-inventory-operation-contract`. Zuletzt bestätigter **Codecheckpoint**: `6d738aafec358d96013a763c9397a18a7ebca894` (CI `38088703225`: SUCCESS). Die nachfolgenden reinen Dokumentationscommits nicht als neue technische Freigabe ausgeben. Aktuellen HEAD vor jeder Änderung prüfen.
5. Die V2-DEV-Oberfläche besitzt eine **einzige zentrale Deployment-Schaltfläche**, vier Statusstufen und die DRA-V1-Ladebalken-Animation. **Schreibgeschützte Einzelvorschau funktioniert**; Schreibfreigabe, echte Installation, V2-Backup und Restore, parallele Sammelinstallation und Restart-Orchestrierung sind **gesperrt/nicht abgenommen**. HA-/Android-Realabnahme des jüngsten UI-Standes noch offen.
6. **Schutzgrenzen:** DRA V1 DEV/PUB, V2 PUB, V2 DEV `main`, WeatherRouter und das private Exportarchiv nicht verändern; Draft-PR #2 nicht zusammenführen. Neue echte Diagnose-/HA-/Testexporte dürfen ausschließlich in das **private** `TheDaimos/Project-Log-And-Export` gelangen; niemals in dieses öffentliche Repo.
7. **Nächster Arbeitsschwerpunkt:** sichere serverseitige Auftrags-/Transaktionsarchitektur, nachweislich vollständige eigene Backups und unabhängiger Rückfall, dann schrittweise explizit freigegebene Installation und konfliktsichere parallele Sammelaktualisierung. **Keine automatische HA-Installation/kein Neustart.**

**Hinweis zur Historie:** Die ursprünglichen Formulierungen in älteren README-/Roadmap-Dateien beziehen sich auf den V2-Vorbereitungsstand; die laufende V2-DEV-Integration hat bereits Version 0.1.53, jedoch weiterhin keine Installationsfreigabe.

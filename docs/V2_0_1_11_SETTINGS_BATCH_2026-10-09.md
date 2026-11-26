# DRA V2 DEV 0.1.11 – Gemeinsames Paket: Einstellungsvorgaben und Sammelauswahl

Stand 09.10.2026 · **Code-/CI-Entwicklungsstand, noch keine HA-Realabnahme**.

## Im Entwicklungspaket gemeinsam umgesetzt

1. **DRA-Einstellungen** im isolierten V2-Testlabor: Auswahl `sequential` oder `controlled`, frei einstellbarer Leseauftragsgrenzwert **1–4**, Arbeitsprozessvorgabe **1–12**. Getrennter privater HA-Store `deploy_relay_v2_dev.settings` und striktes Schema `dra-v2-dev-settings.v1`. Standard `sequential`, geplanter Lesegrenzwert 2 und Prozessvorgabe 4. Laufzeitfehler oder beschädigter/unerwarteter Speicherinhalt führen zum konservativen Ladeabbruch, nicht zum Löschen. `automatic` ist sichtbar, aber ausdrücklich deaktiviert und wird serverseitig verworfen.
2. **Wichtige Trennung von Vorgabe und tatsächlicher Ausführung:** Die Einstellung ist persistiert, aber **die bisherige technische Testlaborgrenze bleibt ein aktiver Leseauftrag**. `max_mutating_jobs=0` im Testlabor, Worker-Vorgabe erzwingt weder eine echte CPU-/Affinitätsbegrenzung noch eine neue Mehrkern-Diagnosereihenfolge. Der Server weist in `settings_effective` auf diese Grenzen hin. Vor echter Aktivierung sind Scheduler-/Ressourcen- und HA-Lasttests erforderlich.
3. **Projektbezogene Sammel-Vorauswahl:** `batch_preselect: bool` je V2-Projekt; fehlendes Feld in bestehender `dra-v2-dev-projects.v1`-Datei wird **ohne Datenverlust als true** gelesen (abwärtskompatibel). Standard für neue Projekte ebenfalls true. Auswahl per Schalter „Sammelupdate: Ein/Aus“ getrennt speichern. Aus bedeutet nur „nicht automatisch angehakt“, kein Installationsverbot.
4. **Sammelauswahl-Vorschau ohne Installation:** Ein Administrator kann die vorgeschlagene Auswahl für **den aktuellen Vorgang** ändern, ohne die gespeicherten Projektstandards zu überschreiben. Der Server kontrolliert, ob jede ausgewählte Repositorykennung in der V2-Projektliste vorhanden ist und die Liste keine Doppelungen oder unzulässigen Einträge enthält. Ergebnis `dra-v2-dev-batch-preview.v1` mit `status=not_checked`, `sources_verified=false`, `installation_enabled=false`. **Es erfolgt weder ein Git-Abgleich noch ein Schreibzugriff.** Die UI darf daher keine Projekt-Updates als „aktuell“ kennzeichnen.
5. **Admin-Absicherung:** vier neue Kommandos `settings/get`, `settings/save`, `projects/preselect`, `batch/preview`, alle über dieselbe V2-spezifische und nur für Administratoren zugängliche WebSocket-Oberfläche. Insgesamt 17 Befehle; V1 und dessen Konfiguration unverändert.
6. **Bewahrung bestehender Diagnostik und V1-Schutz:** Gesamttest mit sieben Mehrkernstufen, Journal, V1-Übernahme, Git-Berichte und Rotationsplan bleiben unverändert. Öffentliche Exportdaten enthalten weder diese privaten Einstellungen noch Projektliste oder Repositorynamen. Das V2-Installationsmanifest bleibt auf `custom_components/deploy_relay_v2_dev` und höchstens 24 Dateien beschränkt.

## Abnahme und Folgeschritte

- Alle Python-Vertragstests, JavaScript-Prüfungen sowie V1-Isolation und sichere Installationsdateilisten müssen auf **dem exakten endgültigen Paket-SHA** erfolgreich sein.
- Die neue Ansicht und das Speicherverhalten werden erst nach expliziter Installationsfreigabe auf HA-DEV geprüft.
- Echte parallele Leseaufträge, aktive Worker-Begrenzung, automatische Ressourcenwahl, echte Git-Versionsprüfung und Sammelinstallation benötigen **gesonderte Runtime-Implementierung und Risikogates**; gespeicherte Vorgaben allein aktivieren diese Funktionen ausdrücklich nicht.
- Für reale V2-Installationen sind der eigene verifizierte Installations-/Vollsicherungs-/Rollback-Kern und separate Bestätigungen erforderlich. Es ist niemals erlaubt, den V1-Code automatisch als V2-Schreibfunktion zu verwenden.
- DRA V1 und V1-PUB sowie V2-PUB und V2-DEV main bleiben unverändert; Draft-PR #2 bleibt Entwurf. Kein HA-Update/Neustart/Installationsauftrag wird durch diesen Commit ausgelöst.


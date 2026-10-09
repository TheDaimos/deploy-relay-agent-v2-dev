# DRA V2 – Auftragsplanung, Parallelbetrieb und konfigurierbares CPU-Budget

Stand: 09.10.2026 · **Entwurf / zur fachlichen Abnahme**, keine neue HA-Funktion freigegeben.

## Ausgangslage und Nutzerwunsch

Der Nutzer fragte, ob Jobs nacheinander oder parallel verarbeitet werden, ob der Modus konfigurierbar sein kann und ob die Kernanzahl frei einstellbar sein soll.

**Bisheriger Iststand V2 DEV 0.1.7:** Der isolierte Auftragsverwalter lässt nur einen schreibgeschützten Testauftrag zu. Der 83-Schritte-Gesamttest läuft sequenziell (40 Sekunden Leseauftrag, 40 Sekunden CPU-/RAM-Messung, 3 Mehrkernstufen). Die Mehrkernstufen 1/2/4 laufen **nacheinander**, aber innerhalb einer Stufe arbeiten maximal vier getrennte Prozesse gleichzeitig. Der Test ist keine Freigabe für produktive parallele Installation. DRA V1 bleibt unabhängige Integration. Die bestehende Vorgabe aus `docs/V2_STUFENPLAN.md` „Nur eine globale Mutation gleichzeitig, bis messbar eine andere sichere Architektur akzeptiert ist“ bleibt gültig.

## Entwurf: drei Betriebsarten

1. **Nacheinander**: höchstens ein Auftrag aktiv; sicherer Rückfallmodus.
2. **Gesteuert parallel**: frei einstellbare Obergrenze für gleichzeitige **schreibgeschützte/als parallel sicher klassifizierte** Aufträge. Abhängige Aufträge werden automatisch seriell ausgeführt. Die Anzahl **gleichzeitiger Schreibtransaktionen** bleibt zunächst fest auf **1**.
3. **Automatisch**: zukünftiger, erst nach gesonderten HA-Realtests freizuschaltender ressourcenabhängiger Modus; begrenzt durch eine ebenfalls frei konfigurierbare Obergrenze. Bei fehlenden oder unplausiblen Daten sicher zurück auf 1 Auftrag. Kein Versprechen automatischer Rechenlastverteilung ohne geprüfte Messbasis.

**Vorgeschlagene Standardwerte bei späterer Freigabe:** konservativ 1 aktiver Auftrag bzw. optional 2 parallele schreibgeschützte Prüfungen; Benutzerauswahl 1–4 parallel sichere Aufträge. Keine stillschweigende Umstellung bereits bestehender Nutzerinstallationen. Bis dahin gilt weiterhin die echte DEV-Grenze **1 schreibgeschützter Auftrag**.

## Getrennte Einstellfelder

- **Auftragsmodus**: `sequential`, `controlled`, `automatic`.
- **Parallel sichere Aufträge**: `max_readonly_jobs` (Entwurfsbereich 1–4), strikt durch Server-Semaphore überprüft; nicht gleichbedeutend mit „4 Installationen“.
- **Schreibtransaktionen**: feste `max_mutating_jobs = 1` bis eigenständig abgenommener, ressourcen-/projektbezogener Lock- und Recovery-Vertrag nachweist, dass mehr gefahrlos möglich ist. Schreib-Lock über alle DRA-V2-Aufträge, zusätzlich pro Projekt/Zielpfad. Updates des DRA selbst stets am Ende einer Sammelaktion.
- **Max. CPU-Budget / Arbeitsprozesse**: `max_worker_processes`, benutzerseitig konfigurierbar, vorgeschlagen zunächst 1–4, später erweiterbarer Expertenbereich bis zur real zugelassenen CPU-Zuordnung (in HA-DEV zuletzt 12 logisch und 12 zugewiesen); keine frei gewählte Zahl über dem echten Limit und keinerlei Verpflichtung, alle Kerne auszulasten.
- **Optionales Kerne-Pinning** wäre eine **gesonderte Funktion** nur für die von DRA selbst gestarteten Unterprozesse; Linux-Affinität und cgroup-Quoten können die nutzbaren Kerne zusätzlich beschränken. Es gibt **keine sichere Möglichkeit**, innerhalb einer HA-Integration den RAM/CPU-Anteil sämtlicher bereits gestarteter HA-Aufgaben auf N Kerne festzulegen oder aus der Zahl der Arbeitsprozesse eine harte CPU-Quote abzuleiten.

**Zwingende begriffliche Trennung:** „maximale parallele Aufträge“ ≠ „Anzahl CPU-Kerne“ ≠ „Anzahl Arbeitsprozesse“ ≠ „tatsächliche CPU-Auslastung“.

## Ressourcen- und Sicherheitsregeln

- Schreibzugriff darf niemals durch Wechsel des Betriebsmodus, ein automatisches Profil, den Testlauf oder die Anpassung des CPU-Budgets freigegeben werden. Explizite, getrennte Benutzerfreigaben für Installation und HA-Neustart bleiben notwendig.
- **Globale Ressourcensperren:** pro Projekt/Version/Installationsziel, Git-/Dateioperationen und gemeinsamer freizugebender Zustand; inkompatible Aktionen nur nacheinander, unabhängig von eingestelltem Parallelismus. Keine parallele Mutation derselben Dateien, Registry, Integrationskonfiguration oder DRA-Installation.
- Queue mit transparenten Zuständen `queued`, `waiting_for_resource`, `running` usw.; faire Reihenfolge und keine stillen Auftragsabbrüche. Bei Neustart laufende mutierende Aufträge konservativ unterbrechen, keine automatische Wiederaufnahme oder Wiederholung; Journal muß atomare Übergänge korrekt abbilden.
- Die Anzahl wird vor jedem Start gegen `os.cpu_count()`, soweit verfügbar `os.sched_getaffinity(0)`, Administrations-/Rollenrechte, Speicher-/CPU-/Datenträgerlimits und vorhandene Aufträge geprüft. Bei Messfehlern ohne falsche Freigabe konservativ fortfahren.
- Arbeiter für CPU-lastige, synthetische Arbeit nur als begrenzte, überwachte **separate Prozesse**, nicht blockierend auf dem HA-Ereignisloop. I/O-lastige geprüfte Leseaktionen dürfen asynchron parallel sein; kein eigenständiges globales Umschalten des HA-CPU-Schedulers.
- Der Nutzer sieht Anzahl `wartend / aktiv / abgeschlossen / fehlgeschlagen`, tatsächlich verwendete Prozesszahl, ausgewählte bzw. verfügbare CPU-Kerne, CPU/RAM/E/A-Referenz und Verzögerung der HA-Ereignisschleife.
- Ein zukünftiger Git-Export soll gewählte **unbedenkliche Grenzwerte**, wirkliche Maxima, Wartedauer und Auslastung als anonymisierte Zahlen enthalten, aber keine Auftrags-IDs, Nutzdaten, Speicherpfade, Tokens oder Rohprotokolle. Öffentliches Schema dafür separat versionieren und mit strenger Positivliste validieren.
- **DRA V1 nicht ändern.** V2-PUB, V2-DEV `main`, Draft-PR #2 und V2-Schreibpfade bleiben unverändert bzw. gesperrt. Diese Planung verändert weder HA-DEV noch die funktionierende V2-DEV-0.1.7-Testoberfläche.

## Entwicklungsreihenfolge / Abnahme

1. Aktuelle V2-40-50-Grenzen CPU/RAM/E/A/HA-Reaktionszeit abschließen; Lasttest nicht als produktiven Schreibtest umdeuten.
2. Exakten Typ-/Speicher-/WebSocket-Vertrag für Admin-Einstellungen und Worker-Reservierungen schreiben. Noch keine Mutation erlauben.
3. Isolierter synthetischer Lasttest: 1, 2, 4 schreibgeschützte Aufträge mit Warteschlange, Ressourcenreservierung, Unterbrechungs-, Timeout- und Neustartpfaden; dabei DRA-V1-Lesefunktion prüfen.
4. Nach CI und ausdrücklicher Benutzerfreigabe einzelner HA-DEV-Realtest. Echte Schreibparallelität **nicht** automatisch einführen; bei fortgesetztem Bedarf späteres eigenes Architektur-/Abnahme-Gate.
5. Bedienoberfläche im V2-Testlabor und später im produktiven DRA V2, mit kleinem und mobil lesbarem Auftragsmonitor, Warnung beim hohen Kernbudget und separat freigegebenen Profilen.

**Entscheidungsstatus:** Konfiguration gewünscht; konkrete Voreinstellung und Kernbereich sind **Empfehlungen**, keine vom Nutzer bereits bestätigten Werte. Kein Auftrag zu HA-Installation/Neustart oder zur Freigabe produktiver Schreibparallelität.

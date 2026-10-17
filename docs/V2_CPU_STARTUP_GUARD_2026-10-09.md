# DRA V2 DEV 0.1.12 – CPU-Verfügbarkeit nach jedem Start prüfen

Stand: 09.10.2026 · ausschließlich V2-DEV-Featurezweig · Code-/CI-Stufe, HA-Realabnahme offen.

## Nutzerauftrag

DRA V2 muss die beim Start sichtbare Anzahl logischer Prozessorkerne erkennen, sie getrennt von der konfigurierten **Verwendete Kerne**-Vorgabe persistent merken und bei späteren Starts erneut vergleichen:

- **Weniger als konfiguriert:** Maximalzahl der vorgesehenen Arbeitsprozesse sofort auf die noch sichtbare Zahl begrenzen und sicher speichern. In der V2-Oberfläche eine **dauerhafte, bis zur Bestätigung sichtbare Warnung** anzeigen, beispielsweise: „Änderung der verfügbaren Prozessorkerne erkannt! Die Einstellung ‚Verwendete Kerne‘ wurde von 10 auf 2 reduziert. Bitte die DRA-Einstellungen kontrollieren.“
- **Mehr sichtbar:** Neue erkannte Zahl still speichern, keine automatisch höhere verwendete Zahl wählen und keine neue Warnung ausgeben.
- **Gleich oder noch oberhalb der gespeicherten Vorgabe:** Keine automatische Absenkung und keine neue Warnung.
- **Erkennung unzuverlässig oder Speicher nicht beschreibbar:** Keine Zahl raten, keine stillen Teilupdates und keine ungesicherte Konfigurationsüberschreibung.

## Messmethode / Ehrliche Grenzen

- Mit `os.cpu_count()` wird die dem Python-Prozess gemeldete Anzahl logischer CPUs ermittelt; soweit vorhanden und erfolgreich, zusätzlich `len(os.sched_getaffinity(0))`. Die kleinste valide Zahl von beiden wird verwendet. Sind beide unbekannt/ungültig, bleibt die letzte gesicherte Einstellung unberührt; die Oberfläche kann `Nicht ermittelbar` anzeigen, wenn noch nie ein valider Wert gespeichert wurde.
- Eine Änderung der CPU-Affinität oder der VM-Konfiguration ist nicht notwendigerweise ein **physischer Hardwaretausch**. Die UI spricht deshalb korrekt von einer **Änderung verfügbarer Prozessorkerne**, nicht zwingend einem Hardwaredefekt.
- Diese Sichtbarkeit ist **kein CPU-Quotennachweis** (z. B. cgroup-CPU-Zeitkontingente), keine Aussage über physische Kerne und keine Garantie für die Leistungsfähigkeit von N Arbeitsprozessen. Die vorhandene feste Mehrkern-Diagnose und der Ein-Leseauftragsschutz bleiben unverändert.
- Die geplante Maximalvorgabe bleibt auf 1–12 beschränkt. Die beim Start gemessene Verfügbarkeit darf darüber liegen; daraus folgt **keine** stillschweigende Erhöhung auf mehr als 12 oder des zuvor benutzerdefinierten Werts.
- Nach erfolgreicher Startprüfung verweigert der V2-Settings-Server eine manuelle Einstellung oberhalb der zuletzt beim Start ermittelten Kernzahl. Ein erfolgreicher manueller Speichervorgang gilt als Bestätigung und entfernt die alte Warnung.

## Persistenz und Migration

Der getrennte private Store `deploy_relay_v2_dev.settings` erhält das strenge, rückwärtskompatibel eingeführte **Schema `dra-v2-dev-settings.v2`**, darin genau vier Felder:

`schema`, `settings` (bisherige Werte), `available_cores` (zuletzt beobachteter Wert oder `null`), `hardware_warning` (streng begrenzte Warnmetadaten oder `null`).

Bestehende `dra-v2-dev-settings.v1`-Einträge bleiben lesbar und werden nach der ersten erfolgreichen Kernzahlermittlung erst dann auf v2 gespeichert; keine vorhandenen Nutzerwerte werden verworfen. Bei beschädigtem oder unbekanntem Schema konservativ nicht starten statt automatischer Rücksetzung. Bei fehlgeschlagener Persistenz wird die neue reduzierte Konfiguration weder intern als erfolgreich übernommen noch in einer ungesicherten Oberfläche bestätigt.

Die gespeicherte Warnung enthält nur die bisher beobachtete verfügbare Zahl (oder `null` beim ersten Check), die aktuell beobachtete Zahl und die frühere Maximalvorgabe. Keine Tokens, Projektlisten, Pfade oder privaten Gerätemerkmale; keine CPU-Werte im öffentlichen Git-Messbericht.

## Oberfläche

In `DRA-Einstellungen → Auftragsverarbeitung` erscheinen **„Beim Start erkannte Prozessorkerne“** und **„Verwendete Kerne (Vorgabe)“** separat. Bei Reduzierung erscheint ein klar hervorgehobener Warnhinweis mit **„Hinweis bestätigen“** (eigener Admin-WebSocket-Aufruf), der über Neustarts bestehen bleibt, solange er nicht bestätigt wird. Ein beobachteter Anstieg erzeugt keinen neuen Hinweis und verändert das gesetzte CPU-Budget nicht; eine bereits aus früherer Absenkung nicht bestätigte Warnung wird nicht still gelöscht.

## Sicherheits- und Abnahmetests

- Alte v1-Werte laden → Startprüfung → v2-Persistenz ohne Verlust.
- 12 verfügbare Kerne / 10 eingestellt → nach Neustart 2 verfügbar → auf 2 reduzieren, exakte Warnmetadaten speichern; nach weiterem Neustart bei 2 keine erneute Warnung.
- 2 → 12 sichtbar → beobachtete Verfügbarkeit aktualisieren, ursprüngliche Benutzerwahl **nicht** wiederherstellen, keine neue Warnung.
- Einmal entstandene Warnung bleibt bis zur Admin-Bestätigung erhalten; erneute echte Absenkung würde sie aktualisieren.
- Unbekannte CPUs, fehlerhafte Werte, defekter Store, manipuliertes Schema, unberechtigter WebSocket-Befehl: keine automatische Fehlfreigabe.
- Zusätzliche Prüfung der Warnungsanzeige in echtem JavaScript, alle bisherigen Projekt-/Git-/Journal-/Sicherheits- und Mehrkerntests erhalten.
- HA-Realabnahme **nur** nach Freigabe eines späteren Funktionspakets; kein unmittelbarer HA-Neustart und keine Freigabe paralleler Schreibaufträge durch diese Änderung.

**Status:** entwickelt und durch CI zu prüfen; keine neuen HA-Installationen/Restores/Backups; DRA V1, V2-PUB und Draft-PR #2 unangetastet.

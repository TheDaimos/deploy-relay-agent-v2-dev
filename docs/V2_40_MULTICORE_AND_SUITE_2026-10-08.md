# V2-40 – Mehrkern-Diagnose und kombinierter Gesamttest

Stand: 08.10.2026 · Entwicklung **V2 DEV 0.1.7**, Zweig \`feature/v2-10-inventory-operation-contract\`. **Keine HA-Installation oder Freigabe von V2-Schreiboperationen.**

## Nutzerziel

Eine gesondert startbare Mehrkern-Diagnose soll zeigen, ob auf HA-DEV echte voneinander getrennte Rechenprozesse auf mehreren logischen Kernen laufen können. Ein neuer Knopf **„Alle Tests nacheinander starten“** führt den bisherigen schreibgeschützten 40-Sekunden-Auftrag, die 40-Sekunden-CPU-/Arbeitsspeichermessung und die Mehrkern-Diagnose als **einen HA-eigenen Auftrag** nacheinander aus. Nach erfolgreichem Abschluss kann ein einzelner manueller Git-Export sämtliche Teilberichte enthalten.

## Auftragssteuerung

- Ausschließlich Administrationsbefehle \`deploy_relay_v2_dev/test/multicore\` und \`deploy_relay_v2_dev/test/all\`; gleiche isolierte HA-Domäne, gleiche V1-unabhängige Auftragsverwaltung, gleiche Grenze **max. 1 laufender Leseauftrag**.
- **Gesamttest:** 40 Lese-/Warteschritte, 40 Mess-/Speicherschritte, 3 Prozessorvergleichsstufen = **83 nachweisbare Fortschrittsschritte** in derselben Auftragskennung; die letzten 3 Schritte dauern nicht je eine Sekunde und werden in der Anzeige daher als Mehrkernprüfung bezeichnet. Einzeltests bleiben separat nutzbar.
- Kein automatischer Neustart, keine Installation, Wiederherstellung, Git-Aktion während des Testauftrags, keine periodische Messung im Leerlauf, keine eigenständige Auftragswiederaufnahme bei Neustart. Das bisherige begrenzte V2-Journal und alle Statusübergänge bleiben unverändert. Unterbrochene oder gescheiterte Gesamttests sind **nicht exportierbar**, auch wenn zwischenzeitlich Teilwerte vorliegen.
- Die schreibgeschützte Arbeit wird ausschließlich nach ausdrücklichem Klick gestartet. Der anschließend mögliche **Git-Export ist nochmals manuell auszulösen** und bleibt ein neuer Commit mit \`[skip ci]\` in das bereits reservierte öffentliche Diagnoseverzeichnis.

## Mehrkern-Diagnose – begrenzte Arbeitsprozesse

- Feste Vergleichsfolge: **1 → 2 → 4 Arbeitsprozesse**, niemals alle gleichzeitig; in der größten Vergleichsstufe maximal 4. Die Zahlen sind in dieser DEV-Stufe **nicht vom Nutzer frei wählbar**.
- Jeder Arbeitsprozess startet als kurzer, abgeschotteter Python-Interpreter \`sys.executable -I -S -c <konstanter Code>\`, ohne Home-Assistant-Module oder Projektdateien. Nur ein deterministischer synthetischer PBKDF2-Block mit **400.000 Runden je Prozess**; keine eigenen Dateien, keine Netzwerkaktivitäten, keine Konfiguration und keine Credentials im übergebenen Prozessumfeld (nur \`PYTHONHASHSEED\`).
- Bei 2/4 Prozessen steigt der **Gesamtumfang synthetischer Arbeit proportional**; protokolliert werden Anzahl Arbeitsprozesse, Gesamtzeit einschließlich Prozessstart/-verwaltung, aufsummierte CPU-Zeit der Arbeitsprozesse und Zahl der Runden. Diese Methodik untersucht gleichzeitige Abarbeitung, **keine feste Aufgabenzeit bei parallelisierter Einzelarbeit** und keinen isolierten DRA-V1-/V2-Verbrauch.
- Je Stufe höchstens **4 Sekunden** Wartezeit, danach Abbruch. Auf jedem Exit-/Abbruchpfad werden begonnene Kindprozesse beendet und eingesammelt. Unzulässige Arbeitszahlen, defekte Ausgaben, nicht startbare Prozesse sowie eine sichtbare CPU-Zuordnung mit weniger verfügbaren logischen Kernen liefern stattdessen \`unavailable\` mit leeren Messzahlen; es gibt **keine automatische Wiederholung** oder verdeckte Überlast. Diese Kennzeichnung ist weder ein negativer Leistungsbeweis noch ein ausgefallener HA-Dienst.
- CPU-Kernangaben stammen aus \`os.cpu_count()\` und ggf. \`os.sched_getaffinity(0)\`. Beide können von Cgroup-CPU-Quoten, Host-Kernzahlen oder der Proxmox-Konfiguration abweichen. Insbesondere ist die Anzeige **kein Nachweis des tatsächlichen vCPU-Kontingents oder einer uneingeschränkten Kernnutzung**.
- Das Backend speichert nur den neuesten fertigen, streng strukturierten Bericht **im Arbeitsspeicher**, nicht als neues Journal oder laufendes Hintergrundprofil.

## Öffentlicher Git-Export

Das neue feste Schema \`dra-v2-dev-git-suite.v1\` veröffentlicht einen streng begrenzten Bericht:

- \`mode\`: \`full\` oder \`multicore\`.
- \`readonly_steps\`: 40 für \`full\`, 0 für \`multicore\`.
- \`measurement\`: bei \`full\` das vollständig bereinigte bisherige CPU-/RAM-Schema \`dra-v2-dev-measurement.v2\`, sonst \`null\`.
- \`multicore\`: feste drei Stufen \`workers = 1, 2, 4\`, jeweils Status \`ok/unavailable\` und nur begrenzte numerische Daten; zusätzlich ggf. sichtbare logische CPU-Zahlen.

Es werden **keine** operation_id, Anmeldeinformationen, privaten Orte, Gerätekennungen, Projekt- und Dateipfade, Rohfehler oder Messdaten aus V1 verschickt. Der Token bleibt im separaten V2-Git-Schlüssel; das Importieren fremder freier JSON-Nutzlasten ist nicht möglich. Bestehende Messdateien \`dra-v2-dev-git-measurement.v1/v2\` bleiben weiter gültig und unangetastet. Auch der neue Bericht muss vor Veröffentlichung die ≤ 4-KiB-Begrenzung erfüllen.

## Abnahmekriterien

- Automatische Vertragstests: 83 monotone Schritte, 3 separate Mehrkernschritte, dieselbe Auftragskennung, keine zweite parallele Operation, keine Veröffentlichung bei Unterbrechung.
- Kinder starten maximal in Gruppen 1/2/4 mit \`-I -S\`, konstanter Programmquelle und reduzierter Umgebung; Test mit echten kurzlebigen Kindprozessen in CI; feste Zeitgrenzen, Einsammeln nach Fehler/Kündigung, keine Nachläufer.
- Exportschutz: identische Anzahl und Reihenfolge der drei Stufen, Prozesswerte nur in zulässigen Grenzen, kein Rohtext oder Auftragsbezeichner, vollständiger Bericht in **einer** Datei; strenge öffentliche Testkontrolle auch für bereits existierende Git-Dateien.
- CI erfolgreich auf dem maßgeblichen Commit; Installationsgruppe weiterhin ausschließlich \`custom_components/deploy_relay_v2_dev\` mit maximal 24 Dateien; **keine V1-Datei** verändert, keine V2-PUB-Veröffentlichung, PR #2 bleibt Entwurf.
- Danach **nur** V1-Quellvorschau zur Abnahme, ausdrückliche Nutzerfreigabe vor jeder Installation und gesonderte Freigabe vor HA-Neustart. Erst dann tatsächlicher Gesamttest und manueller Git-Export in HA-DEV. **V2-40-50 bleibt bis dahin OFFEN.**

## Erster HA-Realtest – 09.10.2026


### HA-Realtest V2 DEV 0.1.7 – Gesamttest und gemeinsamer Git-Export (09.10.2026)

**Nachweis:** Das öffentliche Repository enthält unter `.deploy-relay/diagnostics/v2-dev/2026-10-09/20261009T054505Z-aeb0df4f.json` den über DRA V2 DEV 0.1.7 erzeugten, gemeinsamen Report `dra-v2-dev-git-suite.v1` (UTC 05:45:05; Git-Commit `2314bbbffaea72bd795218d123d4bd36b4ce5308`). Der Nutzer meldete den Export unmittelbar nach dem Gesamttest. **Der einzelne Bericht enthält alle vorgesehenen Teilresultate**; kein automatischer Git-Upload während der Tests nachgewiesen.

| Metrik | Realwert |
| --- | ---: |
| Gesamttest-Modus | `full` |
| Schreibgeschützter Wartetest | 40 Schritte (als abgeschlossene Gesamtauswertung dokumentiert) |
| CPU-/Speichermessdauer | 40.057 ms |
| Maximale Verzögerung | 1 ms |
| Rechendurchläufe in der 20-s-Phase | 640 |
| Prozess-CPU-Basis / Arbeit / Nachlauf | 733 / 1.235 / 718 ms |
| HA-Prozess-RSS Start / Ende | 1.933.464 / 1.930.212 KiB |
| HA-Prozess-RSS-Veränderung | −3.252 KiB, ungefähr −3,18 MiB |
| Mehrkernstufe 1 | 1 Prozess, 400.000 Runden, 94 ms Wandzeit, 67 ms CPU |
| Mehrkernstufe 2 | 2 Prozesse, 800.000 Runden, 89 ms Wandzeit, 138 ms CPU |
| Mehrkernstufe 4 | 4 Prozesse, 1.600.000 Runden, 96 ms Wandzeit, 294 ms CPU |

Alle drei Mehrkernstufen meldeten `ok`; `logical_cpus_visible = 12` und `affinity_cpus_visible = 12`. Der beobachtete **aggregierte Durchsatz** gegenüber 1 Prozess beträgt ungefähr **2,11×** (2 Prozesse) und **3,92×** (4 Prozesse). Die mehrfache synthetische Arbeit wurde parallel schneller verarbeitet; die Stufen laufen jedoch nur knapp 0,1 Sekunden und sind deshalb **kein langfristiger Mehrkern- oder Stabilitätsnachweis**. Start- und Verwaltungsaufwand ist in der Wandzeit enthalten; CPU-Zuordnung/Quoten und andere HA-Aktivitäten können die Ergebnisse beeinflussen.

**Sicherheitsprüfung des öffentlichen JSON:** feste Schemaversion, nur CPU-/RAM-/Mehrkernzähler und harmlose Metadaten; keine Auftragskennung, kein Git-Token und keine Projektkonfiguration im veröffentlichten Report. DRA V1 und V2 sind weiterhin nicht unabhängig im Prozessspeicher messbar; `dra_v1_kib` / `dra_v2_kib` bleiben `null`.

**Abnahmebewertung:** Gesamttest-Realpfad, alle drei Mehrkernstufen und gemeinsamer manueller Git-Export **PASS (ein erfolgreicher Lauf)**. V2-40-50 **noch nicht final geschlossen**, weil die anschließende DRA-V1-Funktionskontrolle, längerfristige Reproduzierbarkeit, HA-Reaktionszeit und E/A-Werte für die V2-0.1.7-Änderung nicht abschließend nachgewiesen sind. Der öffentliche Export belegt den Runtimebetrieb 0.1.7, aber nicht den genauen Installations- oder Neustartablauf. Keine neue HA-Installation, Neustartfreigabe, V2-PUB-Bereitstellung oder Merge hieraus ableiten.

## V1-Funktionskontrolle nach dem ersten Gesamttest (09.10.2026)

Der Nutzer hat die DRA-V1-Sammelaktualisierung nach dem V2-0.1.7-Wechsel erneut geprüft. Fünf Projekte einschließlich V2 DEV werden als `Aktuell` mit `0 Änderung(en)` angezeigt, Schreibzugriff und Installation sind nicht freigegeben, Prüfung abgeschlossen. **V1 schreibgeschützt PASS.** Siehe `docs/V2_40_STATISCHE_ABNAHME_2026-10-08.md`. Quantitative Ressourcenabnahme V2-40-50 weiter offen.


## V2 DEV 0.1.8 – Sieben feste Mehrkernstufen (09.10.2026)

Auf ausdrücklichen Nutzerwunsch erweitert sich die **synthetische, schreibgeschützte** Mehrkern-Diagnose auf **1 → 2 → 4 → 6 → 8 → 10 → 12 Arbeitsprozesse**. Die Stufen starten streng **nacheinander**; nur innerhalb der jeweiligen Stufe arbeiten die Prozesse parallel. Maximal zwölf kurzlebige Python-Unterprozesse werden gestartet, kein dauerhafter Prozesspool und kein zusätzlicher Leerlaufverbrauch. Es gelten weiterhin 400.000 PBKDF2-Runden je Kind und eine Wartezeitgrenze von vier Sekunden je Stufe. Wird eine CPU-Affinität von weniger als der geforderten Anzahl erkannt oder läuft eine Stufe in ein Ressourcenproblem, erscheint sie als `unavailable`; es werden keine Zahlen erfunden. Bei Fehlern und Abbruch werden gestartete Kindprozesse beendet und eingesammelt. CPU-Kernzahlen beziehen sich auf die Sicht des HA-Prozesses und sind keine Garantie einer entsprechenden CPU-Quote.

Der Gesamttest umfasst **40 Auftrags-/Warteschritte + 40 CPU-/RAM-Schritte + 7 Mehrkernstufen = 87 Fortschrittsschritte**. Die sieben abschließenden Schritte sind zeitlich variabel; die Oberfläche zeigt dort `Mehrkernprüfung läuft`, nicht einen erfundenen Sekunden-Countdown. Jeder Einzeldurchlauf und der Gesamttest belegen weiterhin nur **einen** administrativ gestarteten V2-Leseauftrag. V1, V2-PUB und produktive Installations-/Restore-/Neustartpfade bleiben unangetastet.

**Öffentliche Git-Berichte:** Neue Versionen `dra-v2-dev-git-suite.v2`, `dra-v2-dev-suite.v2` und `dra-v2-dev-multicore.v2` akzeptieren ausschließlich die genaue siebenstufige Liste in fester Reihenfolge. Frühere `v1`-Gesamtexporte mit drei Stufen bleiben unverändert und werden vom öffentlichen Schutztest weiterhin anhand des `v1`-Schemas validiert. Ein Bericht muss weiterhin vollständig anonymisiert und höchstens 4096 Byte groß sein; Versand nur per gesondertem Klick.

**Abnahmegrenze:** Quellcode-/CI-Abnahme getrennt von der noch offenen HA-DEV-Realprüfung für 0.1.8. Eine Installation benötigt weiterhin eine DRA-V1-Vorschau und die ausdrückliche Nutzerfreigabe; eine HA-Neustartfreigabe ist separat. V2-40-50 bleibt offen. Die sieben festen Teststufen sind **keine** frei konfigurierbare produktive Auftragsparallelisierung und keine Erlaubnis für zwölf simultane Installationen.

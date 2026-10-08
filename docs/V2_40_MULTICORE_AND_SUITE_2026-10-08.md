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

# V2-40-50 – Speicher-Messvertrag für DRA V2 DEV 0.1.5

Stand 08.10.2026. Dieser Vertrag gilt nur für das isolierte V2-Testlabor und den ausdrücklich ausgelösten synthetischen Test.

## Messmethodik

Ein einziger bereits vorhandener 40-Sekunden-Leseauftrag sammelt vier Stichproben an definierten Phasengrenzen. Es gibt **keinen periodischen Speicherfühler** im Leerlauf und kein Verändern des Betriebssystems, von Projekten oder V1. Die maximal zwei Linux-Kernel-Pseudodateien je Stichprobe werden nur mit 16 KiB begrenzter Eingabe im Arbeiterfaden gelesen.

| Messpunkt | Zeitpunkt |
| --- | --- |
| \`start\` | unmittelbar vor der Basisphase |
| \`base_end\` | nach 10 Sekunden Basisphase |
| \`work_end\` | nach 20 Sekunden begrenzter Rechenarbeit |
| \`end\` | nach 10 Sekunden Nachlauf |

Die fünf numerischen Felder je Messpunkt sind \`total_kib\` (MemTotal), \`used_effective_kib\` (MemTotal − MemAvailable), \`free_kib\` (MemFree), \`available_kib\` (MemAvailable) und \`ha_process_rss_kib\` (VmRSS des HA-Prozesses). **Frei** und **verfügbar** sind verschiedene Größen, weil Zwischenspeicher freigegeben werden können. Alle Werte sind KiB und im öffentlichen Schema begrenzt. Nicht verfügbare Quellen erzeugen \`null\`, nicht \`0\`. Vollständige und partielle Messausfälle dürfen den ansonsten harmlosen Auftrag nicht scheitern lassen.

Der Geltungsbereich heißt \`LINUX_PROCFS_VISIBLE_TO_HA\`: Das ist kein direkter Proxmox-Messwert und nicht zwingend die physische Maschine. Zum Vergleich mit dem Proxmox-Gast müssen Zeitpunkt und Speicherkonzept explizit dokumentiert werden.

## Warum V1 und V2 nicht getrennt messbar sind

DRA V1 (\`deploy_relay\`) und DRA V2 DEV (\`deploy_relay_v2_dev\`) sind Home-Assistant-Integrationen im **gleichen Python-Prozess**. Linux hat nur Prozess-/Systemzähler; gemeinsame Bibliotheken, Referenzen, Cache und Python-Speicherreservierung können keiner Integration zuverlässig zugeordnet werden. Deshalb:

- \`component_memory.dra_v1_kib = null\`
- \`component_memory.dra_v2_kib = null\`
- \`component_memory.reason = SHARED_HA_PROCESS_CANNOT_ATTRIBUTE\`

Eine Vorher-Nachher-Differenz des HA-Prozess-RSS ist höchstens **ein unkontrollierter Prozessunterschied** und kein nachgewiesener V2-Verbrauch. Keine \`tracemalloc\`-Dauerüberwachung, keine Schätzung per Modulname und kein Eingriff in DRA V1. Eine spätere ressourcenintensive Instrumentierung erfordert einen getrennten Entwurf und eine gesonderte Freigabe.

## Git-Export und Sicherheitsgrenze

Der Export ist ein manuell betätigter Administratorbefehl mit bereits vorhandener separater V2-Git-Zugangsverwaltung. Er veröffentlicht **ausschließlich** die validierten vier Zahlenstichproben, konstante Methodenkennzeichnungen und die bestehenden anonymen CPU-/Testlaufwerte im bereits reservierten öffentlichen Pfad \`.deploy-relay/diagnostics/v2-dev\`. Kein Journal, keine Tokens, keine Auftragskennungen.

Aktueller Exportvertrag: \`dra-v2-dev-git-measurement.v2\`; alte \`v1\`-Exporte bleiben lesbar und werden von der CI weiter streng auf ihre damalige Feldmenge geprüft. Neue \`v2\`-Dateien müssen exakte Objektfelder, gültige KiB-Zahlen, \`null\`-Attribution und mathematische Konsistenz (\`used = total − available\`) erfüllen. Nicht erkannte Felder einschließlich beliebiger privater Metadaten blockieren den Upload.

## Abnahme

- Parser für plausible, fehlende und widersprüchliche Kernelwerte einschließlich Prozess-RSS.
- Exakte Probezahl und Phasenreihenfolge; vollständig fehlende Werte als \`null\`.
- Git-Writer verwirft Fremdfelder, unzulässige numerische Werte, gefälschte V1/V2-Beträge, unzulässige Quellen und Daten ohne gültiges Schema.
- Öffentliche Quellenkontrolle prüft alte und neue Git-Exportdateien getrennt nach Version.
- Bestehendes Installationsmanifest mit unverändert maximal 24 Dateien und nur \`custom_components/deploy_relay_v2_dev\` als Ziel; V1-Code und Journal unverändert.
- CI, Vorprüfung in DRA V1 und **ausdrückliche Freigabe** vor Installation. HA-Realabnahme mit einem Messlauf und anschließendem anonymen Git-Export; Ressourcenabschlussentscheidung getrennt.

Status: **Entwicklung, noch keine HA-Realabnahme / V2-40-50 OFFEN.**

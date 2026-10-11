# G2-30 · Android-Verbindungstest unter DRA V2 DEV 0.1.65

**Datum:** 11.10.2026  
**Alleiniger Entwicklungszweig:** `feature/v2-10-inventory-operation-contract`  
**Status:** Implementiert und durch isolierte Prüfungen abzusichern; **keine HA-Realabnahme und keine Installationsfreigabe**.

## Problem und Abgrenzung

Eine normale, real geprüfte Gewitterradar-Quellvorschau dauerte in V2 DEV 0.1.64 nur etwa 1,8 Sekunden. Ein kontrollierter WLAN-/App-Wechsel *während* dieser kurzen Prüfung ist auf Android kaum zuverlässig manuell reproduzierbar. Das bereits real geprüfte spätere Wiederanzeigen historischer Aufträge aus Companion App und Chrome **beweist nicht**, dass eine laufende HA-Aufgabe einen Clientverlust übersteht.

## Umsetzung – isolierter und messbarer Prüfmodus

- Die bereits bestehende, **nur für HA-Administratoren** freigegebene Schnittstelle `deploy_relay_v2_dev/projects/source_job/start` akzeptiert zusätzlich **genau einen optionalen booleschen Schalter** `connection_test`, standardmäßig `false`. Sie erhält **keine** frei wählbare Dauer und **keine** zusätzlichen Schreibfunktionen.
- Bei `connection_test=true` entsteht ein ansonsten normaler, **HA-eigener** Quellprüfauftrag mit eindeutiger Kennung. Dessen flüchtiger Status erhält das unterscheidbare Merkmal `connection_test=true`.
- Vor der eigentlichen regulären Quellprüfung pausiert **nur der neue Testauftrag exakt 30 Sekunden über `await asyncio.sleep(...)`**, also ohne Blockade der HA-Ereignisschleife. Danach läuft die **unveränderte** echte Quellprüfung einschließlich vorhandener 45-Sekunden-Grenze. Der Test bleibt ein **einziger** serverseitiger Auftrag; er wird beim Abmelden des Browserclients nicht abgebrochen.
- Derselbe Repository-/Ref-/Testmodus verwendet während eines laufenden Testauftrags dieselbe Kennung; ein konkurrierender normaler Auftrag oder ein konkurrierendes Projekt wird abgewiesen. Ein Admin kann keine längere Ausführungszeit vom Browser aus bestimmen.
- Die V2-DEV-Hauptseite zeigt eine **getrennte** Schaltfläche `G2 · Verbindungstest (30 s)` und den laufenden Status. Sie verändert weder die normale Vorschau noch die vier eigentlichen Deployment-Schritte. Selbst nach erfolgreichem Test bleibt die normale Vorschau-Freigabestufe **nicht** erreicht. Der Testbericht bleibt nur ein schreibgeschütztes Diagnoseergebnis.
- Der Auftragsdatensatz im vorhandenen HA-Store bleibt **unverändert minimal**: ID, Zustände, Zeit und erlaubte Fehlerkategorie. Kein Repository, Test-Schalter, Ref, Commit, Token oder Quellbericht wird neu persistiert. Die regulären Grenzen (ein aktiver Auftrag, vier flüchtige Ergebnisse, acht Historieneinträge) bleiben bestehen.
- Kein automatischer Git-Export; echte Exporte ausschließlich nach `TheDaimos/Project-Log-And-Export` nach ausdrücklicher Nutzerhandlung. Keine Änderungen an DRA V1, V2 PUB/main, WeatherRouter oder privaten Repositories. Kein Start von Installation, Sicherung, Restore oder HA-Neustart.

## HA-Realabnahme – **ein Bedienungsschritt je Chatantwort**

### Vorbereitung
1. Erst nach erfolgreicher CI und Prüfung der Quell-/Lokalversion durch den Betreiber 0.1.65 ausschließlich über **DRA V1** installieren, falls erforderlich. Notwendigen HA-Neustart nur nach ausdrücklicher eigener Entscheidung des Betreibers; ChatGPT nimmt ihn nicht vor.
2. Companion App und mobiler Chrome-Browser sind bereits an derselben HA-DEV-Instanz angemeldet. Gewitterradar ist im V2-Testlabor als Quelle ausgewählt. Nicht die zentrale Schaltfläche zur Schreibfreigabe verwenden.

### A – Echte Clienttrennung
1. Im V2-Hauptfenster `G2 · Verbindungstest (30 s)` einmal starten. Warten, bis eine Auftragskennung sichtbar ist.
2. **Innerhalb des 30-Sekunden-Fensters** die Companion App verlassen und im **bereits angemeldeten Chrome** die V2-Oberfläche öffnen. Dies beendet nur die bisherige Benutzeroberfläche, nicht die HA-Instanz; kein HA-Neustart.
3. Noch während des 30-Sekunden-Fensters denselben laufenden Auftrag und dessen Kennung prüfen. Wenn die Verbindung zeitlich erst nach der Pause zustande kommt: als `nicht vollständig nachgewiesen` einstufen, nicht als bestanden.
4. Mindestens 45 Sekunden nach Teststart erneut in Chrome nachsehen. Der **identische** HA-Auftrag muss jetzt entweder erfolgreich mit echter Quellprüfung abgeschlossen oder mit nachvollziehbarer Fehlerkategorie beendet sein. Eine neue Auftragskennung oder eine automatisch gestartete zweite Quellprüfung wäre ein Fehler.

### B – Separater WLAN-Ausfall (erst nach A)
Während eines **neuen** G2-Testauftrags am Android-Gerät die WLAN-Verbindung für ungefähr 5 bis 10 Sekunden deaktivieren und danach wieder aktivieren. Der HA-Server bleibt unverändert. Nach Wiederverbindung muss sich **derselbe** serverseitige Auftrag abfragen lassen; eine verpasste Anzeige allein ist kein Nachweis eines Auftragsabbruchs. Bei Netzverlust vor Bestätigung der Auftragsannahme ist der Test ungültig. **Weder Router noch HA noch Proxmox abschalten.**

### Abnahmekriterien
- Derselbe 128-Bit-Auftrag bei Beginn, Clientwechsel und nach Abschluss.
- Tatsächlicher Clientwechsel bzw. belegte WLAN-Unterbrechung **während `connection_test_wait`**; nur späteres Öffnen ist kein Unterbrechungstest.
- Ein erfolgreicher Abschluss enthält die echten unveränderten Quellprüf-Sicherheitsmerkmale `installation_enabled=false`, keine automatische Wiederholung, keine neue Schreibberechtigung.
- Historie bezeichnet alte Erfolge weiterhin ausdrücklich als „Damals erfolgreich“; kein alter Erfolg wird als neue Freigabe gewertet.
- Bei Fehlern `failed`/`interrupted` statt fingiertem Erfolg; kein Neustart oder Rollback.
- Kein automatischer echter Diagnoseexport, insbesondere keine Ablage in Quell- oder öffentlichen Repositories.

## Offene Grenzen

Dies prüft **Clientverlust**, nicht HA-Prozessverlust. Ein HA-Neustart während laufendem Auftrag bleibt eine spätere gesonderte Realabnahme. Auch der in 0.1.64 korrigierte Wiederholversand eines wartenden privaten Git-Exports ist separat abnehmen. **G2 bleibt bis zu den getrennten Realtests offen.**

**C.K. – Eine Idee weiter gedacht.**

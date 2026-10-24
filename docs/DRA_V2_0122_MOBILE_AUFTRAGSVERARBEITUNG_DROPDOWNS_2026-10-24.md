# DRA V2 DEV 0.1.122 – Auftragsverarbeitung: mobile Auswahllisten und Fokus-Schutz

**Datum:** 24.10.2026  
**Repository:** `TheDaimos/deploy-relay-agent-v2-dev`  
**Entwicklungszweig:** `feature/v2-10-inventory-operation-contract`  
**Bereich:** `04 · Auftragsverarbeitung`  
**Anlass:** Nutzerbeleg eines Android-Screenshots; Zahlenfelder schließen sich sofort oder nach 3–4 Sekunden.

## Tatsächlich implementierte Korrekturen

1. Die Eingabe `Parallele Leseaufträge` ist jetzt ein natives `select` mit den festen Werten **1, 2, 3, 4**.
2. Die Eingabe `DRA-Arbeitsprozesse` ist jetzt ein natives `select` mit den festen Werten **1 bis 12**.
3. Der Laborbildschirm ersetzt bisher bei jeder Statusaktualisierung das komplette `shadowRoot.innerHTML`; dadurch wurde das fokussierte Eingabeelement zerstört und die Android-Tastatur beziehungsweise die Auswahl automatisch geschlossen. Während eines fokussierten Einstellungs-Auswahlfelds wird der reguläre Neuaufbau deshalb zurückgestellt.
4. Ungespeicherte Einstellungen werden in `_settingsDraft` zwischengesichert und bleiben nach einer späteren Aktualisierung ausgewählt. Ein erfolgreicher Speichervorgang verwirft den Entwurf und zeigt die vom Backend bestätigten Werte.
5. Bei `blur` wird absichtlich **nicht sofort** neu gerendert, damit die unmittelbar folgende Berührung der Schaltfläche `Speichern` nicht durch den Austausch des Klickziels verloren geht.
6. Die bestehende Backend-Schnittstelle sowie die numerischen Grenzen 1–4 und 1–12 bleiben unverändert. Parallelbetrieb, CPU-Pinning, Schreibaufträge und automatische Ressourcensteuerung werden dadurch **nicht freigegeben**.

**Versionierung:** UI/Integrationskonstanten/Manifest 0.1.122.  
**Regression:** `tests/test_dra_v2_settings_dropdowns.py` ergänzt (Quellstruktur, Auswahlgrenzen, Schutz vor Formularverlust, bestehende Sperren).

## Nachweisstatus und nächste Abnahme

Der Quellcode wurde auf dem angegebenen privaten Featurezweig über GitHub gespeichert. Die neuen Tests wurden in dieser Bearbeitung **nicht ausgeführt**, und eine echte mobile Browser-Abnahme auf HA DEV VM 109 wurde **nicht durchgeführt**. Ein erfolgreicher GitHub-Commit allein beweist nicht, dass ein Hersteller-Browser sein natives Auswahlmenü in jeder Situation korrekt offen hält.

**Kontrollierte Abnahme:** ausschließlich HA DEV VM 109, DRA V2 DEV 0.1.122 auf dem angegebenen Featurezweig laden, Abschnitt 04 öffnen, sowohl bei laufender Aktualisierung als auch im Leerlauf die beiden Auswahllisten mehrfach öffnen, Auswahl ändern und `Speichern` betätigen. Danach die gespeicherten Werte nach einer Aktualisierung und nach dem erneuten Öffnen überprüfen.

**HA PROD VM 101 nicht verändern. Parallelbetrieb bleibt gesperrt.**

C.K. – Eine Idee weiter gedacht.

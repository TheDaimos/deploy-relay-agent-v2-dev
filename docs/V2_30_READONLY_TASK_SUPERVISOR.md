# V2-30 – isolierter Besitzer schreibgeschützter Vorschauaufträge

> **Aktueller Nachtrag (08.10.2026):** Der nachstehende Abschnitt „nicht importiert“ ist historisch. Der Supervisor läuft inzwischen ausschließlich in der eigenständigen, read-only V2-DEV-HA-Integration; Zweitsitzung und Browserneuladen wurden real bestätigt. Für V2-40 wurden Annahme- und Abschlussjournal ergänzt (100/100 CI), aber die gezielte HA-Neustart-Abnahme eines aktiven Auftrags ist noch offen. Keine V1- oder Schreibfreigabe. Siehe `docs/V2_40_STATISCHE_ABNAHME_2026-10-08.md`.

Stand: 08.10.2026. **Erprobungsbaustein, keine HA-Laufzeitintegration.**

## Ziel und aktueller Umfang

Das Modul `readonly_task_supervisor.py` zeigt, wie der Backend-Auftrag und sein Status unabhängig von einer anfragenden Benutzeroberfläche bleiben können. Es nimmt ausschließlich einen intern übergebenen, **schreibgeschützten Vorschauauftrag** an. Es gibt keine Installations-, Wiederherstellungs- oder beliebige Script-Ausführung und wird von `__init__.py` sowie den bestehenden WebSocket-Kommandos **nicht importiert**.

Der Auftragsbesitzer bekommt eine explizite `task_factory` übergeben; im isolierten Test ist das die asyncio-Taskerzeugung. Erst ein geprüfter Home-Assistant-Adapter darf später die von HA verwaltete Taskerzeugung bereitstellen.

## Nachgewiesene Vertragseigenschaften

- Die Startantwort enthält eine unveränderlich adressierbare Auftragskennung.
- Mehrere Wiederholungen derselben Startanforderung erzeugen **keinen** zweiten Task.
- Der Client besitzt kein Taskobjekt: Ein anderer berechtigter Aufrufer kann den Status später über das Register abrufen.
- Der Vorschauauftrag kann einfache gemessene **Phasenzähler** melden; er gibt bei laufender Arbeit keine unbelegte Gesamtprozentzahl an.
- Ausnahmen werden nur als generische Fehlerfamilie gespeichert. Ihre Rohtexte landen nicht im Auftragsstatus.
- Beim kontrollierten Beenden dürfen hier nur **schreibgeschützte** Aufgaben unterbrochen werden; unvollendete Statusdatensätze werden ausdrücklich als unterbrochen markiert.
- Die Auftragsverwaltung darf bei späterer Einbindung keinen Zugang zu Home-Assistant-Schreiboperationen allein durch ein Registerobjekt erhalten.

## Noch nicht freigegeben

- Kein Netzwerk- oder Git-Lesevorgang, keine reale Vorschau, kein dauerhaftes Journal.
- Keine Anmeldung/Autorisierung über Home Assistant: Der spätere Adapter muss Administrator und Quellberechtigung bei jedem Aufruf selbst prüfen.
- Keine Echtprüfung auf Mobilgerät, Verbindungswechsel, HA-Neustart oder Ressourcenlast.
- HA-Tasklebenszyklus, Konfigurationsentladung, Abschaltverhalten und Persistenz sind noch zu implementieren.
- **Installieren/Wiederherstellen dürfen niemals** mit den hier zulässigen schreibgeschützten Stornierungsregeln betrieben werden. Mutationen benötigen zuvor V2-40-Recovery-Gates, bekannte Transaktionsgrenzen und die vorhandenen V1-Sicherheitssperren.
- Keine Veröffentlichung nach `v2-pub`, kein Merge in die aktive HA-Laufzeit ohne separate Abnahme.

Prüfbarkeit: Standardbibliothek-Tests in `tests/test_readonly_task_supervisor.py` und `tests/test_readonly_task_failures.py`. Dies sind synthetische Aufgaben, **keine** HA-Realtests.

Status: **V2-30 DRAFT**, nicht ACCEPTED.

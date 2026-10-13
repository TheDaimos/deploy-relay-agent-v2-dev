# DRA V2 DEV 0.1.86 – Verifizierter Bestand ohne Dateiveränderungen

**Datum:** 13.10.2026
**Stand:** Code und CI bestanden; reale HA-Oberflächenabnahme noch offen.
**Entwicklungszweig:** `feature/v2-10-inventory-operation-contract`
**Geprüfter Code-Commit:** `1ba6d7e6415e560802c7963adc340916c6bc665f`
**CI:** [38443513966](https://github.com/TheDaimos/deploy-relay-agent-v2-dev/actions/runs/38443513966) – SUCCESS.

## Beobachteter Fehler

Nach erfolgreichem Dateivergleich mit 0 hinzugefügt, 0 geändert, 0 entfernt und unverändertem Bestand zeigte die bisherige Oberfläche weiterhin die orange Schaltfläche `2/4 · Installation vorbereiten`. Ein alter erfolgreicher Serverauftrag erschien gleichzeitig als aktueller `success / complete`-Auftrag. Das suggerierte eine erforderliche Installation, obwohl keine Dateien auszutauschen waren.

## Umsetzung

- Eigener, aus einem vollständig verifizierten Vorschaubericht abgeleiteter Zustand `Aktuell · Kein Update verfügbar` mit zurückhaltender blau-türkiser Darstellung. Nur aktiv bei drei vorhandenen, leeren Veränderungslisten und positiver Zahl unveränderter Dateien.
- Orange Installationsvorbereitung und `FREIGABEBEREIT` werden in diesem Zustand nicht angezeigt.
- Die Hauptschaltfläche wird inaktiv; Schaltfläche `Vorschau erneut berechnen` ist getrennt verfügbar. Kein automatischer Installationsauftrag.
- Schritt 1 zeigt geprüften Bestand, Schritte 2–4 sind als nicht erforderlich ausgezeichnet, nicht als abgeschlossene Installationsschritte. Fortschrittsbalken zeigt in diesem Zustand die abgeschlossene Quellprüfung, **nicht** eine zu 100 % durchgeführte Installation.
- Der frühere Erfolg bleibt im Audit. Sein alter `success`-Datensatz erscheint bei einer aktuellen, unveränderten Vorschau nur unter `Vorherige Installation · Historie`, nicht als aktiver Auftrag.
- Zusätzliche Client-Sperre verhindert den Aufruf der Installationsvorbereitung bei leeren Veränderungslisten; das vorhandene V2-Backend lehnt einen Installationsplan ohne Dateiveränderungen ebenfalls ab.
- Verhaltens- und Vertragstests prüfen die Null-Änderungs-Vorschau, ehemalige erfolgreiche Aufträge, erneute Statusabfrage, keine Installationsfreigabe und den Wechsel zurück zu 2/4 bei einer neuen tatsächlich geänderten Datei.
- DRA V1, V2 main, Test-Repo und andere Integrationen unverändert.

## Eine kurze HA-Realabnahme

1. DEV `0.1.86` über das bewährte DRA V1 einspielen und HA einmal neu starten.
2. Unter `Test-Repo-DRA-V2` eine schreibgeschützte Vorschau ausführen, nachdem die zuletzt getesteten Dateien unverändert sind.
3. Bei `0 hinzugefügt / 0 geändert / 0 entfernt / 2 unverändert` **blau-türkise** Anzeige `Aktuell · Kein Update verfügbar` statt `2/4` erwarten.
4. Kontrollieren: keine Installationsvorbereitung, alte Auftragskennung nur in der Historie, getrennte Schaltfläche `Vorschau erneut berechnen`.
5. **Keine Teststand-Erhöhung oder Installation nur für diese Anzeige nötig.** Falls eine Datei zwischenzeitlich geändert wurde, wird weiterhin regulär 2/4 angezeigt.

Issue/Projektstatus nicht als abgeschlossen melden, bevor der Anwender die tatsächliche HA-Darstellung bestätigt.

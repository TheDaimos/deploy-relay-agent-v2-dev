# DRA V2 DEV 0.1.10 – Rückmeldung für Sicherungsrichtlinien

Datum: 2026-10-09

## Änderung
- In der Projekttabelle heißt die Herkunft importierter Einträge nun **DRA V1** statt „Aus V1“.
- Nach erfolgreicher WebSocket-Antwort `projects/retention` wird je Repository der serverseitig bestätigte Sicherungswert vermerkt.
- Solange Wert und Bestätigung übereinstimmen, trägt der Knopf die Aufschrift **Gespeichert** und einen grünen Hintergrund.
- Bei Änderung der Eingabe wechselt der Knopf wieder auf **Speichern**; bei fehlgeschlagener Übernahme wird keine grüne Bestätigung gesetzt.
- Die Rückmeldung bleibt innerhalb der aktuellen Panel-Sitzung erhalten, auch wenn die Oberfläche neu gerendert wird; ein kompletter Browser-Neustart lädt den Status neu und zeigt ohne erneuten Speichervorgang die normale Schaltfläche.
- Keine Änderung an V1-Integration, tatsächlicher Sicherungsrotation, Backups oder Schreibfreigabe.

## Abnahme
Version `0.1.10` in `manifest.json` und `const.py`. Realtest auf Home Assistant noch offen. Projektwert speichern, danach grüne Bestätigung prüfen; Wert ändern, normale Schaltfläche prüfen; fehlschlagende Serveraktion darf keinen Erfolg anzeigen.

**C.K. – Eine Idee weiter gedacht.**

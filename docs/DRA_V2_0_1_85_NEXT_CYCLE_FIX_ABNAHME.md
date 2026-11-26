# DRA V2 DEV 0.1.85 – Freigabe des nächsten Deployment-Durchlaufs nach 4/4

**Stand:** 13.10.2026. Code implementiert, CI erfolgreich, HA-Realabnahme steht aus.
**Zweig:** `feature/v2-10-inventory-operation-contract`
**Code-Checkpoint:** `b0d589c84066becd099215a8c21278c284bc0196`
**CI:** [38436050042](https://github.com/TheDaimos/deploy-relay-agent-v2-dev/actions/runs/38436050042) – SUCCESS.

## Fehler (0.1.84)

Nach erfolgreich abgeschlossenem Serverauftrag blieb im Browser ein `success / complete`-Datensatz hinterlegt. Die Anzeige priorisierte diesen alten 4/4-Status stets vor dem nächsten Prüfdurchlauf. Auch wenn GitHub einen neuen Quellcommit meldete oder `Test 2` den isolierten Teststand erfolgreich erhöhte, blieb die Hauptschaltfläche bei 4/4 und blockierte die Vorschau.

## Korrektur (0.1.85)

- Alte Serveraufträge und Audit-Ereignisse bleiben erhalten; nur ihre Wirkung auf die **aktuelle** Schrittanzeige wird für den nächsten Durchlauf beendet.
- Nach erfolgreichem `Tests → Test 2 → Teststand um +1 erhöhen` wird die alte 4/4-Anzeige für das isolierte Testprojekt freigegeben. Dabei keine Installation und keine neue Autorisierung.
- `Quelle & Version → Aktualisieren`: Erkennt abweichenden Git-Commit auch bei bereits abgeschlossenem Serverauftrag; verwirft alte, unpassende Vorschau und Freigabe; wechselt wieder auf 1/4.
- Eine separate Schaltfläche `Neue Vorschau für dieses Projekt berechnen` ist nun auch beim **unmittelbaren** 4/4-Erfolg verfügbar, nicht nur beim historischen Erfolg nach HA-Neustart.
- Beim ausdrücklichen Start einer neuen regulären Quellprüfung wird die vorherige Abschlussanzeige als **historisch** behandelt. G2 löst diese Umstellung ausdrücklich nicht aus.
- Spätere Statusabfragen können die alte 4/4-Anzeige nicht wieder als aktiven Durchlauf einschalten. Ein **neuer** serverseitiger Auftrag mit neuer Auftragskennung kann anschließend selbstverständlich wieder 4/4 erreichen.
- Automatische Verhaltenstests simulieren: `4/4 success → neuer Git HEAD → Aktualisieren → 1/4 → Serverstatus alter Erfolg → weiterhin 1/4 → neue schreibgeschützte Vorschau → 2/4` sowie `4/4 success → Git-Teststand +1 → 1/4`.
- Bestehende Schutzmechanismen für Zielpfade, Installationsfreigabe, Adminrechte und reale GitHub-Berechtigungen unverändert. Keine Änderung an DRA V1 oder V2 main.

## Gebündelte HA-Abnahme (ein Durchlauf)

1. DRA V2 DEV 0.1.85 über DRA V1 installieren, Home Assistant einmal neu starten und Versionsgleichheit kontrollieren.
2. `TheDaimos/Test-Repo-DRA-V2` wählen. Falls noch alter 4/4-Abschluss angezeigt wird, ist die neue Schaltfläche `Neue Vorschau für dieses Projekt berechnen` verfügbar.
3. Bei Bedarf über `Tests → Test 2` einmal den Teststand der **festen Testdatei** erhöhen (nur nach ausdrücklicher Bestätigung; bestehende Schreibberechtigung erforderlich).
4. `Quelle & Version → Aktualisieren`: aktuellen Git-Commit prüfen. Die ältere Vorschau und 4/4-Sperre müssen danach verschwunden sein.
5. **Nur die schreibgeschützte Vorschau** auslösen: Erwartet eine geänderte Testdatei, sofern noch nicht installiert. 2/4 muss erreichbar sein.
6. Nur wenn erforderlich, anschließend genau einen realen Testinstallationsdurchlauf mit ausdrücklicher Bestätigung durchführen. Erneut 4/4 prüfen. Keine zusätzlichen Tests, keine produktiven Repositories.

**Realabnahme noch offen.** CI grün ist noch kein Beleg der Funktion auf HA.

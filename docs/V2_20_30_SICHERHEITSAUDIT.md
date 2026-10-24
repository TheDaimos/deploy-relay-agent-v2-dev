# V2-20/30 – Sicherheitsaudit des isolierten Auftragsmodells

Stand: 08.10.2026. Arbeitszweig `feature/v2-10-inventory-operation-contract`.
Prüfumfang: `operation_model.py`, `operation_registry.py`, die zugehörigen Vertragstests.
Dies ist **keine Home-Assistant-Laufzeitabnahme** und noch kein V2-Operationsmanager.

## Ergänzte Schutzregeln

1. Nur Operationstyp, interne Projektkennung, exakte Git-SHA und Diagnosekennung sind beim Anlegen eines Auftragsdatensatzes zulässig. Auftrags-ID, Erstellungszeit, Status, Ergebnis, Fortschritt, Start- und Endzeit sowie Neustartkennzeichen werden intern vergeben; sie können nicht über zusätzliche Konstruktorargumente vorgegeben werden.
2. Die Zustandsmaschine entfernt beim Wiederanlauf den reinen Wartezustand als aktive Arbeitsphase. Ein fehlgeschlagener oder stornierter Auftrag darf nicht den erfolgreichen Endzustand `complete` behaupten.
3. Fortschrittszähler und Einzelzähler erhalten numerische Obergrenzen. Ein gemessener Teilabschnitt kann nicht allein den Abschluss der Gesamtoperation vortäuschen; 100 % Gesamtfortschritt gehört zum erfolgreichen Abschluss.
4. Auftragskennungen werden vor allen Registerzugriffen geprüft. Ungültige oder nicht passende Kennungen lösen einen definierten Vertragsfehler aus, statt unkontrollierte Python-Ausnahmen zu verursachen.
5. Der Registerfilter `active_only` ist nur als echtes `bool` zulässig. Idempotente Wiederholungen müssen zum ursprünglichen Typ, Projekt, Quellstand **und Diagnosekontext** passen.
6. Ausgaben bleiben explizite, unabhängige Feldkopien. Keine Rohfehler, Passwörter, frei ergänzbare Kontextdaten, Dateipfade oder privaten Repositoryadressen ausgeben. Die Anzahl historischer Einträge ist beschränkt.
7. Die Registrierung vergibt **keine** Schreibrechte und startet keine Aufgaben. Laufende Mutationen werden weiterhin nicht allein anhand einer Zustandsmeldung freigegeben.

## Neue Prüffälle

- Versuche, von außen Status, Zeitstempel, Prozentwerte, Auftragskennung, Fehlertyp oder Neustartbedarf vorzugeben.
- Warte-/Wiederanlauf und falsche Erfolgsphase.
- Grenzen bei Fortschritts- und Ergebniszählern.
- Kennungsprüfung bei Abruf, Statuswechsel, Fortschritt und Stornierung.
- Konflikte bei Idempotenzbezug und Kontextwechsel sowie parallele identische Anfragen.
- Ende, begrenzte Aufbewahrung, erneute Anfrage und sichere Ergebnis-Kopien.

## Noch offene Sicherheitsfragen

- Direkte Python-Objektreferenzen sind interne mutable Dataclasses; spätere HA-Adapter dürfen sie niemals an Clients oder fremde Komponenten herausgeben. API-Grenze ist das erzeugte `snapshot()`.
- Eine Git-SHA im Modell ist **kein Beweis**, dass sie zur aktuell freigegebenen Quelle passt. Vor jedem schreibenden Task muss eine separate serverseitige Autorisierungs-/Quellprüfung stattfinden.
- Der Registereintrag ist **kein tatsächlicher HA-Task**. Er ist speicherbasiert; Clientverlust, Home-Assistant-Unload, Neustart, Journal und sichere Transaktionswiederherstellung müssen einzeln getestet und erst später aktiviert werden.
- Der endgültige Idempotenzumfang muss den authentifizierten Kontext und Freigabezustand berücksichtigen. Ein Hash der Anfragekennung ersetzt keine Berechtigungsprüfung.
- Die vorhandenen `deployment_lock`-/`resource_lock`-Regeln aus V1 müssen beim realen Auftragsmanager weitergelten. Eine separate Registerkapazität ersetzt keine Ressourcen-/Dateisperre.
- Reale HA-Leistungsmessungen und vollständige V1-Finalabnahme stehen aus.

**Gate:** Quell- und Vertragstests gehören zur Vorbereitung. V2-20 und V2-30 erst nach vollständiger fachlicher/HA-bezogener Abnahme als ACCEPTED kennzeichnen. Kein automatischer Transfer nach `v2-pub`.

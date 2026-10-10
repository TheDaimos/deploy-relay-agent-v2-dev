# V2 – Projekteinstellung „Sammelupdate“

Stand: 2026-10-08. Nur **DRA V2**; **kein Umbau an DRA V1**.

## Ziel

Jedes in DRA V2 konfigurierte Projekt bekommt in seinen **Projekteinstellungen** einen Schalter:

**„Bei Sammelaktualisierungen vorauswählen“ – Ein / Aus**

- **Ein:** Dieses Projekt wird beim Öffnen einer neuen Sammelprüfung beziehungsweise Sammelinstallation automatisch angehakt.
- **Aus:** Dieses Projekt wird bei der Vorauswahl **nicht angehakt**.
- **Wichtig:** „Aus“ ist **kein Installationsverbot**. Ein Administrator kann das Projekt für einen einzelnen Sammelvorgang bewusst manuell anhaken. Die gespeicherte Voreinstellung bleibt dabei unverändert.
- Der Schalter bleibt über einen HA-Neustart erhalten und wird je Projekt gespeichert, nicht als globale Einstellung.
- Der Schalter gilt für **Sammelprüfung und Sammelinstallation**. Einzelprüfung/-installation bleiben davon unabhängig.
- Die Sammelinstallation darf nur tatsächlich vom Administrator bestätigte Projekte berücksichtigen, nicht eine eventuell veraltete automatische Vorauswahl.

## Festgelegte Kompatibilität

Bestehende Projekte ohne gespeicherte V2-Einstellung werden wie bisher standardmäßig **vorausgewählt**. Damit werden sie bei Einführung der neuen Einstellung nicht still aus Sammelvorgängen entfernt. Neue Projekte dürfen im Dialog ausdrücklich auf „Aus“ gestellt werden; insbesondere ist dies für **DRA V2 DEV** während der parallelen Entwicklung zu empfehlen.

Technischer Vorschlag: optionaler, streng boolescher Subentry-Wert `batch_preselect`, fehlender Wert = `true`. Keine automatische Mutation bestehender V1-Konfigurationen allein beim Lesen; Migration und Persistenz in V2 gesondert prüfen.

## Bedienung

In Home Assistant → Geräte & Dienste → Deploy Relay Agent → jeweiliges **Projekt** → Zahnrad:

`Sammelupdate: Ein / Aus`

In der späteren V2-Sammelansicht kennt der Browser eine gespeicherte Vorauswahl je Projekt. Manuell gesetzte Häkchen gelten jeweils nur für den aktuellen Vorgang und dürfen beim Zeichnen der Oberfläche nicht unerwartet zurückgesetzt werden.

## Prüffälle vor Abnahme

1. Bestehendes Projekt ohne Feld: weiterhin vorausgewählt.
2. Schalter „Aus“: kein Häkchen bei neuer Sammelprüfung/Installation.
3. Trotz „Aus“ bewusstes manuelles Anhaken: Teilnahme am einen ausdrücklich bestätigten Sammelvorgang möglich.
4. Schalter „Ein“: bei neuem Sammelvorgang wieder vorausgewählt.
5. Persistenz über HA-Neustart und erneutes Öffnen der Oberfläche.
6. Zwei Projekte mit unterschiedlichen Einstellungen beeinflussen sich nicht.
7. Änderung während einer bereits laufenden Sammelinstallation darf die eingefrorene Auswahlliste nicht heimlich verändern.
8. Serverseitiger V2-Sammelmanager validiert die tatsächliche bestätigte Projektliste; unberechtigte oder ungültige Subentries werden abgelehnt.
9. Keine Änderung des bisherigen V1-Sammelupdate-Verhaltens.

**Umsetzungsgate:** Projekt-Optionen/UI innerhalb der V2-Oberflächenstufe; Auswahlvertrag und Einfrieren der Liste spätestens bei V2-90/V2-100 (Backend-Sammelaufträge). Vorher nicht unkontrolliert in die V1-Runtime einhängen. V1-/V2-PUB-Repositories bleiben unverändert.

## Teilimplementierung in V2 DEV 0.1.11 (09.10.2026)

Der gespeicherte Schalter `batch_preselect` pro V2-Projekt ist mit abwärtskompatiblem Standard `true` implementiert. Die Sammelansicht übernimmt Häkchen zunächst aus den Projektstandards, erlaubt manuelle Auswahl nur für den Vorgang und erzeugt über die Admin-API eine unveränderliche, nur lesende Vorschau. **Keine** Git-Quellversionsprüfung und **keine** Installation; jedes Projekt wird ausdrücklich `not_checked` angezeigt. Die restlichen Backend-/Schreibgates dieses Dokuments sind noch offen.

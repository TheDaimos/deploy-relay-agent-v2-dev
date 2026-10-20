# DRA V2 0.1.116 DEV – Sammelupdate als gespeicherte Startauswahl

**Datum:** 20.10.2026  
**Repository:** `TheDaimos/deploy-relay-agent-v2-dev` (privat)  
**Zweig:** ausschließlich `feature/v2-10-inventory-operation-contract`

## Tatsächlicher Anwenderbefund

Der Benutzer hat das virtuelle „Sammelupdate“ bewusst auf **Position 1** der Projektauswahl verschoben. Auf einem anderen Gerät zeigte DRA V2 beim Öffnen trotzdem ein Einzelprojekt als Standard. Dies ist **zusätzlich** zu dem bereits in 0.1.115 adressierten Fehler der nicht automatisch angezeigten, auf HA bereits vorbereiteten Sammelprüfübersicht.

## Codebefund und Ursache

Der serverseitige Katalog persistiert `picker_batch_position`. Der Frontend-Aufbau `_pickerEntries()` berücksichtigte diese Zahl nur für die **Reihenfolge der Auswahlzeilen**. Die Initialisierung hielt jedoch `_mainBatchMode=false`, bevorzugte gegebenenfalls eine Einzelprojekt-Sitzung und fiel bei leerer Einzelprojektauswahl auf das erste aktive Einzelprojekt zurück. Somit bedeutete „Sammelupdate auf Position 1“ fälschlicherweise nicht „Sammelupdate als Startansicht“.

## Umgesetzte Änderung

Bei der **frischen Initialisierung** wird ein gespeichertes `picker_batch_position===0` nun als Startansicht „Sammelupdate“ interpretiert. Die lokale Vorauswahl übernimmt aktive, vorgewählte Projekte aus dem Katalog; das eigene DRA-V2-Selbstupdate bleibt weiterhin bewusst abzuwählen beziehungsweise **ausdrücklich für den einzelnen Sammellauf auszuwählen**, statt automatisch vorgemerkt zu werden. Ein gezielt ausgewähltes Einzelprojekt wird auf späteren Statusaktualisierungen **nicht** durch die gespeicherte Position überschrieben.

Der Rückfall auf die Einzelprojektquelle und dessen automatische Quellenprüfung wird bei aktivem Sammelmodus unterdrückt. Der bereits vorbereitete HA-Sammelauftrag wird dabei **nicht** automatisch neu vorbereitet, bestätigt oder gestartet. Die ausdrücklich bestätigte Geräteübernahme aus 0.1.115 bleibt getrennt bestehen.

**Codecommit:** `37ba24007ad7251b163df383008cf63f3de00c35`.

Die sichtbare Version, Python-Konstante und Manifest lauten synchron **0.1.116 DEV**. Bestehende JavaScript-Testvorgaben und ergänzende Startauswahl-Vertragstests wurden an den neuen Stand angepasst.

**Letzter Testcommit:** `a3d44873df793d6255548e28ee90d3355d580db9`.

## Grenzen der Prüfung

GitHub-Tests sind keine HA-Realabnahme. Die tatsächliche Startauswahl auf Notebook, iPad und Handy ist erst mit einer bewusst kontrolliert installierten 0.1.116 DEV auf HA DEV nachweisbar. Die erneute Bestätigung der bestehenden vorbereiteten Prüfübersicht darf weder beim Seitenaufruf noch beim Gerätewechsel automatisch gesetzt werden. Keine DRA-V1-, WeatherRouter- oder Gewitterradar-Änderungen; keine Installation oder Neustart ausgelöst.

**Realprüfungen nach grüner CI:** Sammelupdate serverseitig auf Position 1 speichern, auf einem neuen Gerät öffnen, Sammelupdate als Startansicht prüfen, gezielt auf ein Einzelprojekt wechseln, Status aktualisieren und sicherstellen, dass die Auswahl erhalten bleibt. Anschließend den vorbereiteten HA-Sammelauftrag ohne erneute Vorbereitungs- oder Installationsanforderung übernehmen.

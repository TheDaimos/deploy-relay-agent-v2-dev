# V2-DEV-Testlabor auf dem vorhandenen HA-DEV

> **Standnachtrag (08.10.2026):** Das zuvor geplante isolierte Testlabor wurde mittlerweile auf dem einzigen HA-DEV erfolgreich installiert und zusammen mit DRA V1 real geprüft. Der untenstehende ursprüngliche Installationsplan bleibt als Sicherheits- und Rückfallreferenz erhalten, ist aber **kein aktueller Installationsstatus**. Die nun vorbereitete Version 0.1.1 mit V2-40-Journal benötigt vor jeglichem HA-Update erneut Vorschau und ausdrückliche Freigabe. Siehe `docs/V2_40_STATISCHE_ABNAHME_2026-10-08.md`.

Stand 08.10.2026. **Technischer Kandidat – vor einer Installation automatische Prüfungen und Freigabe erforderlich.**

## Warum dieses Paket anders ist

Der Nutzer betreibt nur **eine** HA-DEV-Instanz und muss DRA V1 jederzeit weiterverwenden können. Das V2-DEV-Repository enthält zwar die V1-Integrationskopie für die spätere Migration, aber diese Kopie **darf niemals** mit dem Testpaket nach HA gelangen.

Deshalb ist das DRA-Projektmanifest `deploy-relay.json` so begrenzt, dass nur `custom_components/deploy_relay_v2_dev` als neuer Ordner installiert wird. Der vorhandene Ordner `custom_components/deploy_relay` und die laufende V1 bleiben unberührt.

Das neue Testlabor nutzt die Domäne `deploy_relay_v2_dev`, eigene WebSocket-Befehle `deploy_relay_v2_dev/test/*`, eine eigene Seitenleiste `dra-v2-dev-lab`, statische URL `/dra_v2_dev_static` und ein eigenes JavaScript-Element. Es schreibt keine DRA-eigenen Backups, Logs, Journale oder Projektdateien. Nur Home Assistant legt bei der einmaligen Einrichtung regulär einen getrennten Konfigurationseintrag an; DRA V1 kann beim Installieren dieses neuen Ordners wie üblich seine eigenen Installations-/Diagnosedaten führen.

## Was der erste Test macht

Ein Administrator kann im eigenen Testlabor einen **20 Sekunden dauernden, rein simulierten Vorschauauftrag** starten. Der Auftrag führt ausschließlich `asyncio.sleep(1)` mit 20 bekannten Zählschritten aus und hält seinen Zustand im Speicher der Testintegration. Ein zweiter Administrator-Client kann denselben Auftrag abrufen, nachdem der erste Browser geschlossen wurde. Nur während eines laufenden Auftrags fragt die Oberfläche den Status etwa alle 1,5 Sekunden ab. Im Leerlauf keine Abfragen und keine Hintergrundaufgaben.

Das ist noch **keine echte DRA-Projektvorschau**, kein Repositoryzugriff und keine V2-Installationsfunktion. Im Testlabor gibt es ausdrücklich **keine Installation, Wiederherstellung, Sammelaktualisierung, Löschung oder HA-Neustartaktion**. Beim Entladen der Testintegration wird ein aktiver schreibgeschützter Auftrag gestoppt; nach vollständigem HA-Neustart werden solche Testaufträge noch nicht wiederhergestellt.

## Gesonderte Freigabeschranken

1. DRA-Projektmanifest per V1-Schema-Parser und Zielpfadprüfung validieren; genau ein einziger Zielordner ist erlaubt.
2. Python- und JavaScript-Syntax sowie alle automatischen Vertragstests einschließlich Kollisionstest grün.
3. Prüfen, dass weder V1-Hauptzweig noch V2-PUB oder V2-Hauptzweig verändert wurden.
4. Prüfen, dass in der DRA-V1-Projektkonfiguration für V2 **ausschließlich der explizit freigegebene V2-DEV-Zweig und die richtige unveränderliche SHA** gewählt werden. Der Hauptzweig enthält möglicherweise eine veraltete oder keine `deploy-relay.json`.
5. **Vorschau zuerst ansehen**: einzig erlaubtes Installationsziel `custom_components/deploy_relay_v2_dev`, kein `custom_components/deploy_relay`. Ist ein anderer Pfad in der Vorschau, Abbruch.
6. Erst nach ausdrücklicher Freigabe Installations-Test auf HA-DEV; sicherstellen, dass DRA V1 weiterhin normal bedienbar bleibt. Die Installation des Testlabors benötigt zum Einlesen der neuen Integration normalerweise einen HA-Neustart.
7. Nach Neustart Testlabor unter HA → Geräte und Dienste als eigene Integration hinzufügen, dann beide Seitenleisten getrennt prüfen.
8. Mobilgerät starten → Fenster schließen/Verbindung trennen → Notebook öffnen: derselbe Testauftrag sichtbar. V1 muss vorher/während/nachher unverändert funktionieren.
9. Bei jedem unerwarteten Verhalten Test sofort beenden; V1 und seine bestehende Installation nicht verändern.

## Rollbackplan

Der **einzige** gezielt eingerichtete Integrationsordner ist `custom_components/deploy_relay_v2_dev`. Vor späteren Experimenten den eigenständigen V2-Test-ConfigEntry entfernen, DRA V1 unverändert lassen und ausschließlich die separate Testintegration entfernen; normale Home-Assistant-Neustartregeln beachten. Keine automatische V2-Reparatur oder Löschung bestehender V1-Dateien.

Dieser Stand ist nicht V2-PUB, nicht HACS und nicht für produktive Installation freigegeben.

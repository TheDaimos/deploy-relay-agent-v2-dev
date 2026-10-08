# DRA V2 – Schutzregeln für den Parallelbetrieb mit V1

Stand: 2026-10-08 · Entwicklungsstand: ausschließlich DEV.

## Ausgangslage

Die öffentliche V1-Integration und der aktuelle V2-Entwicklungsstand verwenden derzeit beide dieselbe Home-Assistant-Domäne `deploy_relay`, denselben Quellcodepfad `custom_components/deploy_relay/` und `single_config_entry=true`. Der V2-Quellstand kennzeichnet sich weiterhin als Version 1.0.0; ein isoliertes V2-Einsatzpaket existiert **noch nicht**.

**Konsequenz:** V1 und V2 können in dieser Form **nicht unabhängig nebeneinander auf derselben Home-Assistant-Konfiguration installiert werden**. Ein Hinzufügen des öffentlichen V2-Repositorys als reine Quellenreferenz ist keine V2-Installation. Eine Installation/Aktualisierung in denselben Integrationspfad könnte dagegen den dortigen V1-Code ersetzen.

## Verbindlicher sicherer Testweg

1. **V1 bleibt unangetastet** auf der bereits genutzten HA-Instanz. Keine V2-Quellen dort installieren, zur Aktualisierung auswählen oder über HACS als neue Integrationsdateien einspielen.
2. V2 für Realtests ausschließlich auf einer **getrennten HA-Instanz mit eigenem `/config`-Dateisystem** installieren. Bei vorhandenem V1 auf der Entwicklungsinstanz muss vor dem V2-Test eine weitere isolierte Testinstanz oder ein technisch sauber getrennter Integrations-Namensraum eingerichtet werden.
3. Nicht einfach eine zweite Config Entry mit gleicher Domäne anlegen: `single_config_entry` und gleiche Dateipfade verhindern keine Quellcodekollision.
4. Vor dem ersten Realtest ein vollständig geprüftes V2-Testpaket mit klarer DEV-Versionskennung, eindeutigem Git-SHA, verifizierbarem Installationsweg und Rollbackpunkt erstellen. **Bis dahin keine V2-Installation** empfehlen.
5. V2-PUB bleibt ausschließlich Veröffentlichungsziel; weder V1-PUB noch private V1-Entwicklung noch laufende V1-HA-Instanzen dürfen durch diesen Test verändert werden.
6. Keine Daten-/Dateisystemfreigaben, Tokens, Config-Verzeichnisse oder Backup-/Journaldaten zwischen HA-Test und HA-V1 gemeinsam beschreibbar bereitstellen. Sicherung und Recovery auf der Testinstanz gesondert prüfen.
7. Vor realen Tests prüfen: ursprüngliche V1-Instanz unverändert startbar/bedienbar; V2 ist isoliert; Trennung der Integrationspfade und Speicherorte nachgewiesen; exakte SHAs dokumentiert.
8. Eine zukünftige `deploy_relay_v2`-Parallel-Integration auf **derselben** HA-Instanz wäre ein eigener Umbau. Dazu müssten Domäne, Konfigurations-/Speicherpfade, WebSocket-Kommandos, Seitenleiste, statische Dateien, Sicherungen, Manifest- und Updateziele vollständig kollisionsfrei geprüft werden. Eine reine Umbenennung des Verzeichnisnamens reicht nicht.

## Einordnung des aktuellen Repositorys

- `deploy-relay-agent-v2-dev` enthält aktuell `custom_components/deploy_relay/manifest.json`.
- Der DEV-Zweig enthält noch **keine** für DRA standardmäßig erwartete Projektdatei `deploy-relay.json` und keine `hacs.json`.
- Das Fehlen dieser Dateien **garantiert nicht**, dass eine Drittsoftware keine Installation/Überschreibung versucht. Die Sicherheitsregel ist daher organisatorisch und technisch eindeutig: keine Installation auf einer HA-Instanz, auf der V1 weiterlaufen soll.

## Abnahme

Ein V2-Realtest wird erst freigegeben, wenn die Zielinstanz und ihr eigener Konfigurationspfad ausdrücklich bestätigt sind und der Testkandidat überprüft wurde. GitHub-Actions-Grün allein ist kein Installationsnachweis.

**Status: ISOLATION PLAN – verbindliche Betriebsschranke; kein V2-Teststand freigegeben.**

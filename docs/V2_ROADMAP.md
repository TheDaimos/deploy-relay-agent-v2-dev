# DRA V2 – Öffentlicher Entwicklungsplan

Stand: 08.10.2026. Status: Vorbereitung und öffentliche Ausgangsbasis; keine V2-Freigabe.

## Leitregeln

Zuerst V1 vollständig und unabhängig real abnehmen und den Rückfallstand festhalten. V1 ist die Referenz. Kein Auftrag darf bei Schließen des Browsers oder Verlust der Clientverbindung seinen serverseitigen Zustand verlieren. Die bestehenden Schreibsperren, Commitprüfungen, Sicherungen, Verifikationen, Rückfall- und Wiederherstellungsregeln dürfen nicht abgeschwächt werden.

## Verbindliche Reihenfolge der Arbeit

1. V1-Freigabe und prüfbare öffentliche V2-Referenz, Messwerte.
2. Vollständige Bestandsaufnahme der Git-, Vorschau-, Sicherungs-, Installations- und Diagnosepfade.
3. Serverseitiges Auftragsmodell mit eindeutiger Kennung, Zustand, Journal, Warteschlange und Sperren.
4. Schreibgeschützte Aufträge und Wiederverbindung implementieren und abnehmen.
5. Installations- und Wiederherstellungsaufträge mit unveränderten Sicherheitsgarantien.
6. Sammelaufträge vollständig serverseitig; DRA-Selbstupdate kontrolliert zuletzt.
7. Gemeinsames redigiertes Diagnosemodell mit Warteschlangen-, Sperr- und Ressourcenmessungen.
8. Mobilfreundliche, ressourcenschonende Benutzeroberfläche mit echtem Fortschritt; HA-Integrationsansicht und offizielles Logo.
9. Ressourcenprüfung zu CPU, RAM, Datenträgern, Haupt-Ereignisschleife und Akkulaufzeit.
10. Migration und reale HA-/Android-Abnahme einschließlich Netzwerkwechsel, Neustart und sicherem Rückfall.
11. Veröffentlichungsprüfung, HACS/Hassfest und gesonderte Freigabe des stabilen Auslieferungskanals.

Keine Stufe überspringen. CI-grün ist nicht gleich Realabnahme. Die einzelnen Stufen erhalten vor Implementierung prüfbare Teilpunkte, Dokumentation, exakte Quellstände und Abnahme.

## Sofortige Grenzen

Die Ausgangsbasis trägt weiterhin V1.0.0. Es gibt noch keine V2-Auftragsroutinen, kein freigegebenes V2-Paket und keinen automatischen Veröffentlichungsworkflow. Das bestehende öffentliche V1-HACS-Repository bleibt unverändert.

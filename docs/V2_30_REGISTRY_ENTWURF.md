# V2-30 – vorbereiteter Auftragsregister-Entwurf

Status: **isolierter Entwurf / nicht mit Home Assistant verbunden**.

`operation_registry.py` verwaltet Auftragsdatensätze in einer begrenzten, rein speicherbasierten Registrierung. Die Datei ist ohne Home-Assistant-Imports prüfbar und wird gegenwärtig **nicht** durch den bestehenden DRA-Code aufgerufen.

## Eingebaute Verträge

- Eindeutige `operation_id` für Einträge; `list` und `get` liefern ausschließlich neu gebaute JSON-kompatible Snapshots statt veränderbarer Referenzen.
- Eine gleichzeitige mutierende Auftragsbeschreibung global. Erst nach terminalem Abschluss kann eine weitere Mutation eingetragen werden. Die Registrierung erteilt **keine** Ausführungsberechtigung.
- Konservatives Limit für gleichzeitig vorgemerkte schreibgeschützte Operationen; configurable mit gesetzten Obergrenzen.
- Idempotente Anmeldeversuche über eine begrenzte Anforderungskennung, die vor Speicherung gehasht wird. Wiederholung desselben Typs/Projekts/Commits gibt denselben Datensatz zurück. Wiederverwendung der Kennung mit anderem Inhalt wird abgelehnt.
- Abschlüsse bleiben nur in begrenzter Anzahl erhalten; alte Kennungen und zugehörige Zuordnungen werden gemeinsam entfernt.
- Ein Stornierungswunsch an einen bereits laufenden Auftrag ist **nur eine Statusanforderung**; er beendet keinen Task und führt keine unsichere Unterbrechung einer Mutation aus.
- Kein eigenständiges GitHub-, Dateisystem-, HA- oder Netzverhalten. Kein Start von `asyncio.create_task` und keine WebSocket-Routen.

## Noch fehlende Voraussetzungen vor V2-30-Abnahme

1. Aktuellen V2-10-Ist-Befund und V2-20-Modellvertrag vollständig prüfen; laufende V1-Referenzmessung weiterhin offen dokumentieren.
2. Den Registerdienst HA-konform an den Lebenszyklus eines Config Entry anbinden und mit einer **explizit vom HA-System besessenen Taskverwaltung** verbinden. Der bloße Auftragsdatensatz ist keine ausführbare Operation.
3. Schreibfreigabe, Identität und wiederholte Autorisierung im laufenden Backend erzwingen, statt dem Auftragsregister Schreibrechte zuzuschreiben.
4. Konsistente Persistenz einschließlich atomarem Journal, Startup Recovery und Unload-Verhalten entwerfen und testen. Dies ist Gate V2-40.
5. Rennen zwischen Registrierung, Start, Ende, Wiederverbindung und Cancellation in simulierten und realen HA-Tests abdecken.
6. Fehler-/Idempotenz-Timeouts, Lösch- und Begrenzungsstrategie auf konkrete reale Last messen.
7. Read-only Preview als erste wirkliche Backendoperation umstellen; Install/Restore erst nach expliziter Sicherheits-/Recoveryabnahme.

**Verbot:** Den isolierten Registry-Entwurf ohne diese Gates als funktionierenden serverseitigen Auftragsmanager bezeichnen oder in eine laufende Home-Assistant-Instanz automatisch aktivieren.

# DRA V2 DEV 0.1.87 – Abschlussaktionen nach erfolgreicher Installation

**Stand:** 14.10.2026. Implementiert und CI-grün. Realabnahme wird mit dem nächsten echten Projektupdate gebündelt.
**Code-Checkpoint:** `8e44830c8c7254e08b087f8672c065eca429d403`
**CI:** [38522060619](https://github.com/TheDaimos/deploy-relay-agent-v2-dev/actions/runs/38522060619) – SUCCESS.
**Zweig:** `feature/v2-10-inventory-operation-contract`

## Umsetzung

- V1-Engine entscheidet weiterhin anhand der tatsächlich installierten und verifizierten Zielpfade über die Nachaktion.
- Ausschließlich sichere statische Frontenddateien (z.B. `custom_components/<integration>/frontend/*.js/css` oder `www/*`) → `frontend_reload_possible=true`, `restart_required=false` → **Oberfläche aktualisieren** (normaler Browser-Neuladevorgang). Kein HA-Neustart.
- Python-, gemischte oder unbekannte Änderungen → `restart_required=true` → **Home Assistant neu starten**. Bei explizit gemeldetem `integration_reload` wird konservativ ein HA-Neustart angeboten, da V2 keinen allgemeinen Integrations-Neuladevorgang garantiert.
- Bereits abgeschlossene Updates ohne Nachaktionsbedarf → **Keine weitere Aktion erforderlich**.
- Abschlussaktionen nur bei aktueller, erfolgreich abgeschlossener V2-Installation mit passender Oberfläche/Python-Version; keine Startaktion bei einer schreibgeschützten Vorschau oder bei einem historischen Auditdatensatz.
- HA-Neustart: zuerst Schaltfläche, dann ausdrückliche Sicherheitsabfrage mit **Abbrechen** oder **Ja, Home Assistant neu starten**. Keine automatische Aktion.
- Serverroute `deployment/restart` ausschließlich für Administratoren und mit `confirm=true`, konkreter 32-stelliger Auftragskennung, `success/complete` und nachgewiesenem `restart_required=true`. Vor Aufruf werden laufende V2-Installationsaufträge ausgeschlossen. Ein laufzeitgebundener Neustartschutz verhindert Doppelanforderungen. Der Neustart nutzt ausschließlich den HA-eigenen Dienst `homeassistant.restart`.
- Kein V1-Repository, kein V2 `main`, kein anderer Produktcode verändert.

## Automatisierte Tests

- Die echte HA-WebSocket-Neustartfunktion wird als unveränderter Funktionskörper gegen ein isoliertes, synthetisches HA-Dienstobjekt ausgeführt: fehlende Bestätigung, Fehlerstatus, falsche Phase, kein Neustartbedarf, laufende Installation und ungültige Kennung dürfen **keinen** Aufruf erzeugen.
- Positiver Fall: genau ein `homeassistant.restart`-Aufruf, zweiter Versuch geblockt. Simulierter Dienstfehler setzt die Sperre zurück.
- Browser-Verhalten: Frontend-only zeigt ausschließlich **Oberfläche aktualisieren**, Backendupdate ausschließlich Neustartschaltfläche; erst explizite zweite Bestätigung sendet den Restart-WebSocket-Aufruf.
- Der ganze bestehende CI-Vertrag bleibt grün.

## Gebündelte Realabnahme beim ersten echten Projektupdate

1. 0.1.87 DEV über DRA V1 installieren und Home Assistant einmal neu starten.
2. Das ohnehin geplante erste echte Projektupdate in DRA V2 per neuer SHA-Vorschau, Installation und Audit vollständig abschließen.
3. Nach 4/4 das angezeigte Nachaktionsangebot mit dem tatsächlichen Installationsinhalt vergleichen.
4. Wenn HA-Neustart benötigt wird: Sicherheitsabfrage öffnen, zuerst **Abbrechen** prüfen; anschließend erst nach bewusster Bestätigung den HA-Neustart durchführen. Kein gesondertes synthetisches Installationspaket dafür erzeugen.
5. Bei einem späteren natürlichen Frontend-only-Update die Oberflächenaktualisierung kontrollieren. Dafür nicht künstlich weitere Testinstallationen erzeugen.

**Offen:** Realer HA-Neustart per neuer V2-Oberfläche und Browseraktualisierung sind bis zum Anwendernachweis nicht als bestanden zu deklarieren.

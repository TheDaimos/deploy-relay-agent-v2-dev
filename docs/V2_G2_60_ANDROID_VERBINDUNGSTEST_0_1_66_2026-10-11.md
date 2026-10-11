# DRA V2 DEV 0.1.66 – G2-60 Android-Verbindungstest und Laufzeitabgleich

**Datum:** 11.10.2026  
**Verbindlicher Entwicklungszweig:** `feature/v2-10-inventory-operation-contract`  
**Status:** Änderung implementiert; CI und HA-Realabnahme getrennt bewerten. **Keine Schreib-, Installations- oder Neustartfreigabe durch V2.**

## Anlass

Bei der ersten HA-Erprobung von 0.1.65 erschien bereits die neue G2-30-Schaltfläche, aber der Auftrag startete nicht. Die Oberfläche meldete lediglich „Quellprüfung nicht startbar“. Ein während dieser Sitzung neu an das private Zentralarchiv übertragener Diagnoseexport meldete in den Anwendungs-/Laufzeitversionsfeldern **0.1.64** und die letzte früher erfolgreich beendete Quellprüfung. Der Export enthält keinen neuen G2-Auftragsnachweis. Damit ist eine Abweichung zwischen der bereitgestellten neuen Oberfläche und der vom Bericht angegebenen Python-Laufzeit **beobachtet**, die Ursache jedoch nicht endgültig nachgewiesen. Möglich bleiben insbesondere ein alter Backend-Stand oder ein gesonderter Berichtszustand; kein unbelegter Backend-Fehler behaupten.

## Änderung 0.1.66

1. **Testfenster fest 60 Sekunden:** Nur bei explizitem Admin-Parameter `connection_test=true` wartet der HA-eigene, schreibgeschützte Quellauftrag über `await asyncio.sleep(60)` vor der unveränderten tatsächlichen Quellprüfung. **Normale** Vorschauen und ihre 45-Sekunden-Prüfgrenze bleiben unverändert. Weder der Browser noch der Benutzer bestimmen die Dauer.
2. **Laufzeitabgleich vor Teststart:** Die DEV-Oberfläche liest die bereits bestehende administrative `deploy_relay_v2_dev/test/state`-Antwort, die `version` direkt aus der laufenden Python-Konstante liefert. Sie zeigt `Aktive Python-Version` an. Der spezielle Testknopf ist nur bedienbar, wenn **0.1.66** zurückgemeldet wurde. Bei abweichender oder nicht ermittelbarer Version wird **kein** neuer G2-Quellauftrag angefordert.
3. **Bei Fehlern sichtbare, bereinigte Rückmeldung:** Nicht bestätigte Startanforderungen werden ohne Geheimnisse als fehlgeschlagene Annahme angezeigt, inklusive zuvor geprüfter Python-Laufzeitkennung. Es wird **keine** Ursache wie Netzwerkfehler, HA-Reload oder Tokenfehler ohne Nachweis behauptet.
4. **Sicherheitsgrenzen unverändert:** Der G2-Test erlaubt keine Dateimutation, Sicherung, Wiederherstellung, Installation, Selbstaktualisierung, V1/V2-Übernahme oder HA-Neustart. Auch ein erfolgreiches G2-Prüfergebnis schaltet die reguläre Deployment-Stufe 2 **nicht** frei. Serverseitige Auftragsidentität bleibt erhalten, maximal ein aktiver Leseauftrag, persistente Historie weiterhin nur minimal.
5. **Versionspaar:** `manifest.json` und `const.py` beide `0.1.66`. Neue reale Diagnosen ausschließlich ins private `TheDaimos/Project-Log-And-Export`, niemals als Rohdaten in das öffentliche Code-Repository.

## Abnahmefolge (je Chatantwort höchstens ein konkreter HA-Schritt)

- **Vor Ausführung:** isolierte CI einschließlich Python-Vertragstests, Syntax, JavaScript-UI-Test und Nichtveröffentlichung prüfen. Falls erfolgreich, Betreiber installiert **0.1.66 über DRA V1** und startet Home Assistant wie üblich anschließend vollständig neu. ChatGPT nimmt weder Installation noch Neustart vor.
- **Sichtprüfung:** In V2 DEV muss neben `G2 · Verbindungstest (60 s)` die **aktive Python-Version 0.1.66** angezeigt werden. Bei abweichender Version **nicht** den Test erzwingen, sondern nur die angezeigte Version melden.
- **Clientwechsel:** G2-Test für Gewitterradar einmal starten, Kennung notieren, innerhalb der ersten 60 Sekunden von Companion App zu Chrome wechseln. Der andere Client zeigt **dieselbe** serverseitige Auftragskennung, bei Rückkehr folgt die echte Quellprüfung und ein ehrlicher Terminalzustand.
- **Netzunterbrechung separat:** Bei einem weiteren G2-Test auf Android WLAN erst **nach bestätigter Auftragskennung** für wenige Sekunden deaktivieren, anschließend aktivieren. Keine HA-/Proxmox-/Router-Unterbrechung. Dasselbe laufende HA-Auftragsobjekt muss über die wiederhergestellte Verbindung weiter abrufbar sein.
- **HA-Neustart während laufendem Auftrag und Exportwarteschlangen-Wiederholung** bleiben getrennte, noch offene Tests; niemals implizit als bestanden deklarieren.

## HA-Realtest – Zwischenbefund vom 11.10.2026

- Nach der vom Betreiber ausgeführten Aktualisierung und dem HA-Neustart meldete die V2-Oberfläche die **aktive Python-Version 0.1.66** und „Laufzeit kompatibel“. Die Versionsabweichung aus dem ersten 0.1.65-Versuch wurde in diesem Lauf **nicht** mehr beobachtet.
- Der **G2-Testauftrag über 60 Sekunden** wurde tatsächlich angenommen. Die Companion App zeigte einen laufenden HA-Auftrag mit Kennung und Test-Wartestatus. Die anschließend im direkten Chrome-Zugriff angezeigte Auftragshistorie enthielt denselben Auftrag als abgeschlossenes **Fehlerergebnis**. Damit sind Testannahme und ehrliche Rückmeldung des HA-eigenen Auftrags belegt.
- Der ausdrücklich vom Betreiber ausgelöste **private Git-Export** zeigte für diesen Versuch die erlaubte Fehlerklasse `manifest_target_protected` auf der Stufe `manifest`. Die im **privaten** Export benannte Quellwahl war das geschützte **DRA-V1-DEV-Projekt**, nicht die für G2 geplante bekannte, ungeschützte Gewitterradar-Quelle. Der Schutz greift damit **erwartungsgemäß**; es handelt sich **nicht** um einen nachgewiesenen Defekt der G2-Auftragsverwaltung.
- Die Aufnahmen aus Companion App und Chrome unterstützen die Wiederanzeige des serverseitig verwalteten Auftrags über zwei Clients. Ein erfolgreicher **Quellprüfungsabschluss** für den neuen G2-Test fehlt noch. Die tatsächliche Netzwerkunterbrechung über WLAN wurde **nicht** durchgeführt und bleibt separat offen.
- Bei Wiederholung **Gewitterradar ausdrücklich in V2 auswählen**, dann erneut einen G2-60-Test starten und vor Ablauf der Wartezeit den Client wechseln. Kein Upgrade, keine neue Sicherheitsfreigabe und kein Neustart dafür erforderlich.

**Abnahme:** 0.1.66 aktive Laufzeit, G2-Start, serverseitige Historisierung und geschützte Zielverweigerung bestätigt. Vollständiger G2-60-End-to-End-Erfolg mit Gewitterradar **ausstehend**.

## HA-Realabnahme: Companion App → Chrome mit Gewitterradar erfolgreich

**11.10.2026, nach der ersten geschützten DRA-V1-DEV-Testquelle:**

- Gewitterradar war im V2-DEV-Projektwähler tatsächlich ausgewählt. Die aktive serverseitige Python-Version wurde mit **0.1.66** angezeigt, der fest auf 60 Sekunden begrenzte, rein lesende G2-Auftrag startete erfolgreich.
- Auf den Screenshots der Companion App erscheint die neue Auftragskennung als laufend in der **60-Sekunden-Wartephase**; anschließend wurde die **getrennte Chrome-Sitzung** derselben HA-Instanz geöffnet. Deren Deployment-Oberfläche zeigte während des Tests denselben laufenden Auftrag, und die serverseitige Auftragshistorie zeigte ihn zunächst mit dem Status **„Begonnen“** und später **„Damals erfolgreich“**, **unter identischer Auftragskennung**. Es wurde **keine zweite G2-Auftragskennung** erzeugt.
- Der exakt nach Ablauf der Wartephase stattfindende echte Quellvergleich schloss um **17:37:57 UTC** erfolgreich ab. Sein privater Git-Diagnoseexport vom 11.10.2026, **17:38:15 UTC**, weist **Version 0.1.66**, die Quelle **Gewitterradar**, `sources_verified=true`, `status=success`, `stage=target_claims`, `reason=none`, `installation_enabled=false` und **1.520 ms Prüfdauer** aus. Der Bericht enthält alle acht erlaubten Prüfphasen; die feste vorgeschaltete 60-Sekunden-Wartephase gehört **nicht** zu dieser eigentlichen Prüfdauer.
- Eine kurz zuvor abgeschlossene andere Gewitterradar-Quellprüfung erscheint getrennt in der Loganzeige, wurde jedoch **nicht** mit dem laufenden G2-Auftrag verwechselt.
- Die Browseranzeige „Quellstand noch nicht geprüft“ ist bei dem **separaten G2-Diagnosemodus** kein Gegenbeleg: Ein bestandener Verbindungstest darf die normale Deployment-Quellfreigabestufe nicht automatisch setzen. Die echte Quellprüfung ist dennoch nachweislich erfolgreich und schreibgeschützt abgeschlossen.
- Ein erneuter Login in Home Assistant, automatischer Neustart, selbstständige Dateimutationen oder Installationsfreigabe waren dafür **nicht** notwendig.

**Abnahme G2-60-A:** **BESTANDEN** – serverseitige Fortführung und identische Auftragskennung über Clientwechsel Companion App → Chrome, mit anschließend erfolgreichem unverändertem Quellvergleich.

**Noch gesondert offen:** Test G2-60-B (gezielte WLAN-Unterbrechung nach bestätigtem Auftragsstart), Auftragsverhalten beim tatsächlichen HA-Neustart und die Wiederholung eines zuvor fehlgeschlagenen privaten Exportauftrags. Der Clientwechsel beweist **nicht** die Behandlung eines Netzverlusts oder eines gestoppten HA-Prozesses.

**Datenschutz:** Nur diese bereinigte Bewertung und erlaubte, unkritische Kennzahlen werden im Entwicklungsrepository festgehalten. Keine privaten Exportdateien, Rohberichte, Git-Tokens, lokalen Zugriffsadressen oder individuellen Auftrags-/Exportkennungen übernehmen. Originaldiagnosen bleiben ausschließlich im privaten `TheDaimos/Project-Log-And-Export`.

## G2-60-B – WLAN → 5G mit VPN in realer HA-Umgebung (11.10.2026)

**Stand: Netzwechsel und erfolgreiche Quellprüfung bestätigt; terminale Historienzuordnung noch nicht direkt gezeigt.**

- Der Betreiber startete mit **Gewitterradar** einen neuen, serverseitig verantworteten, ausschließlich lesenden G2-Auftrag über die Companion App im WLAN. Der Startbildschirm zeigte die laufende 60-Sekunden-Wartephase und eine eindeutige Auftragskennung.
- Bei **abgeschaltetem WLAN** war im weiteren Screenshot das Android-Gerät mit **5G und aktivem VPN** verbunden. Die DRA-V2-Ansicht zeigte weiterhin **dieselbe laufende Auftragskennung**. Dies belegt die Wiederabfrage des serverseitigen Auftrags über einen anderen Netzwerkpfad, nicht die Ununterbrochenheit einer konkreten WebSocket-Verbindung.
- Anschließend meldete die HA-Diagnose für Gewitterradar eine erfolgreiche echte Quellprüfung. Der gezielt ausgelöste private Git-Diagnoseexport (11.10.2026, **17:48:38 UTC**) bestätigt für die aktive **0.1.66**: `status=success`, `stage=target_claims`, `reason=none`, `sources_verified=true`, `installation_enabled=false`; alle acht zulässigen Prüfschritte erfolgreich; reine Quellprüfdauer **1.364 ms**. Die vorherige 60-Sekunden-Wartephase ist nicht in dieser Prüfdauer enthalten.
- **Präzise Beweisgrenze:** Die bisherigen Screenshots zeigen die identische Auftragskennung vor und nach dem Wechsel, die Quell-Diagnose jedoch **nicht die G2-Auftragskennung**. Ein historischer Endstatus „Damals erfolgreich“ für genau diesen Auftrag ist auf den vorliegenden Aufnahmen noch **nicht direkt lesbar**. Diesen letzten Abgleich deshalb nicht ohne zusätzlichen Nachweis als durchgeführt ausweisen.
- Weder automatische Wiederinstallation, Wiederholung des Auftrags noch Schreibfreigabe sind nachgewiesen. Ein HA-Prozessneustart war nicht Teil des Tests. Der erfolgreiche Clientwechsel G2-60-A bleibt davon unabhängig abgenommen.

**G2-60-B Teilabnahme:** Wiederverbindung über **WLAN → 5G/VPN** mit gleichbleibender laufender Auftragskennung und erfolgreich durchlaufener Quellprüfung **bestanden**. **Formal vollständiger End-to-End-Nachweis unter exakt derselben Auftragskennung** bis zum terminalen Historieneintrag steht noch aus; dazu reicht die Anzeige „Damals erfolgreich“ der genannten Kennung, ohne erneuten Test oder Export.

**Datenschutz:** Diese Notiz enthält nur bereinigte Testmerkmale, keine privaten JSON-Diagnosen, Tokens, Quellpfade, Adressen oder Auftragskennungen. Alle Rohdaten verbleiben ausschließlich im privaten Zentralarchiv.

## CI / Realnachweise

**Isolierte GitHub-CI erfolgreich:** [Run 38158437838](https://github.com/TheDaimos/deploy-relay-agent-v2-dev/actions/runs/38158437838) zum Featurezweig-Checkpoint `efeb9f3c9c729fb46bb85760b0df90a390fb6aea`: Python-Vertragstests, Python-/JavaScript-Syntax, Node-Bedienungstests und keine Artefaktveröffentlichung jeweils erfolgreich. Nachfolgende Änderungen betrafen nur dieses Dokument und den bereinigten AI-Kontext. **HA-Realabnahme des Clientwechsels erfolgreich; WLAN→5G/VPN-Verbindung und Quellprüfung bestätigt, terminaler Historienabgleich der genauen G2-Auftragskennung noch offen; HA-Neustartfall offen.** Ein in Git vorhandenes 0.1.66-Manifest beweist **nicht**, dass diese Python-Version bereits auf dem HA-Server läuft.

**C.K. – Eine Idee weiter gedacht.**

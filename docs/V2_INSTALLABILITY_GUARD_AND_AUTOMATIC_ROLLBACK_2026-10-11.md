# DRA V2 – Installierbarkeitsprüfung, automatische Rückfallsicherung und Wiederherstellungswächter

**Anforderung:** 11.10.2026, Projektinhaber  
**Bezug:** G3 (exklusiver Zielbesitz), G4 (echt geprüfte, vollständige V2-Sicherung), G5 (schreibende Einzeltransaktion).  
**Stand:** VERBINDLICHER DESIGNVERTRAG, **keine Implementierung und keine Freigabe** für Installationen, Rückfall oder Home-Assistant-Neustart. Zuletzt veröffentlichter DEV-Quellstand: 0.1.63; die HA-Realabnahmen von 0.1.62/0.1.63 stehen noch aus.

## Ziel der Nutzeranforderung

DRA V2 soll vor einer Installation **sicher erkennen, ob das Update überhaupt installierbar ist**, bei nachweislichem Fehler nach Schreibbeginn **automatisch den früheren Zustand wiederherstellen**, und die Wiederherstellung mit einem unabhängigen Daten- und Zustandsnachweis bestätigen.

**Kernregel:** Ein Netzwerk- oder Browserabbruch ist niemals ein Beweis für einen fehlerhaften HA-Updateauftrag und darf keinen automatischen Rückfall auslösen. Eine bereits geschriebene, aber noch nicht als funktionsfähig bestätigte Version gilt als `unverified`, nicht als `success`.

## 1. Strikte Unterscheidung nach Mutationsgrenze

### A – Noch keine Veränderung vorgenommen

Installation nicht starten, wenn eine der folgenden Bedingungen fehlt: registriertes und unverändert gewähltes Projekt, Repository und SHA-gepinnter Quell-Commit; zulässiges Deployment-Manifest und überprüfter Git-Dateibaum; freier Speicher/Platzreserve; vollständiger und konsistenter Zielbestand; keine nicht erlaubten Pfade, Symlinks, Hardlinks oder geänderte Dateien; eindeutige V1/V2-Zielübergabe; durchgängige exklusive Sperre; verifizierte **V2-eigene** Sicherung der Originalbytes; vollständig bereitgestelltes Stagingpaket; explizite Administratorfreigabe mit unveränderter Projekt-/Quell-/Zielkennung.

**Aktion:** `blocked_preflight` mit festgelegtem Fehlergrund, **null veränderte Zielbytes**, keine Wiederherstellung erforderlich. Nur wenn das nachweisbar stimmt, darf „keine Änderungen“ angezeigt werden.

### B – Schreibtransaktion begonnen

Mögliche Fehler: Teilkopie oder Festplatten-I/O, Prüfsumme/Datenintegrität, ungültiges Ziel nach erneuter Bestandsaufnahme, unerwartete fremde Mutation, unvollständiger Commit/Dateisatz, Programmabbruch.

**Aktion:** keine weiteren Updates; gespeicherte Transaktionsphase und Sperre prüfen; automatische Wiederherstellung **ausschließlich** aus der vollständig persistierten, unmittelbar vorab validierten Sicherung und nur innerhalb eines nachweislich exklusiv kontrollierten Ziels. Anschließend ursprüngliche Dateimenge und alle Datei-Bytes/Hashes erneut unabhängig prüfen. Bei bestätigter Übereinstimmung `rollback_verified`; sonst `recovery_required` und keine falsche Erfolgsmeldung.

### C – Dateien installiert, aber noch nicht funktional abgenommen

Getrennte technische Nachprüfung: richtiger Dateisatz und Prüfsummen; HA/Integration nach einem erforderlichen und vom Administrator separat genehmigten Neustart; zutreffende ConfigEntry-Zustände; fest begrenzte, fachlich dokumentierte Bereitstellungs-/Wartephase; ausdrückliche, projektspezifisch überprüfbare Funktionssignale, wo vorhanden.

**Keine** Aussage „fehlgeschlagen“ allein wegen `SETUP_IN_PROGRESS`, `SETUP_RETRY`, kurzer Startverzögerung, Netzverlust oder ausgebliebenem Frontend-Status. Negative Funktionssignale nur als `failed` einstufen, wenn die Prüfbedingungen tatsächlich ausführbar und der Fehler eindeutig sind. Sonst `verification_pending` oder `recovery_required` statt unbegründeten automatischen Rückfalls.

Wenn eine verlässlich eindeutige Funktionsstörung nach dem Schreibvorgang erkannt wird, Rückfall wie B nur dann automatisch, wenn HA und die Rückfall-Engine erreichbar, Sicherung intakt, Eigentum und Sperre unverändert und die Recovery-Strategie projektspezifisch nachweisbar sind.

### D – Home Assistant selbst nicht mehr erreichbar / nicht mehr startfähig

Die DRA-V2-Integration läuft **innerhalb** des betroffenen HA-Prozesses. Ist dieser ausgefallen, darf weder die UI noch die interne Instanz als aktiver Wiederherstellungswächter behauptet werden. Ein wirklich automatischer Rückfall aus diesem Zustand erfordert später einen **unabhängigen, außerhalb des betroffenen HA-Prozesses laufenden Wiederherstellungswächter** (eigener, explizit genehmigter Sicherheits- und Berechtigungsvertrag; DRA V2 soll nicht heimlich den Supervisor oder das Dateisystem privilegiert fernsteuern).

Bis zur eigens abgenommenen unabhängigen Recovery: gesonderter Zustand `external_recovery_required`, unveränderte Sicherungsartefakte und zugängliche, redigierte Wiederherstellungsanweisungen. **Keine** automatische HA-Neustartkaskade.

## 2. Verpflichtender Zustandsvertrag

`preview_verified → preflight_passed → backup_persisted → backup_readback_verified → staging_verified → commit_pending → applying → file_verification → functional_verification → success`

Fehlerpfade:
- Vor `applying`: `blocked_preflight`, keine Zielmutation, **kein** Rückfall.
- Nach belegter Mutation: `rollback_pending → rollback_running → rollback_verification → rollback_verified`.
- Fehlende Belege, unklarer Besitz, beschädigte Sicherung oder ausfallender Prozess: `recovery_required` / `external_recovery_required`. Stets fail-closed.
- `verification_pending` ist explizit **kein** Erfolg und darf kein weiteres Update derselben Zielgruppe freigeben.

Für jede Transition werden mindestens gespeichert: eindeutige Auftragskennung, festes Projekt-/Quell-/Ziel-Identitätsbündel im geschützten serverseitigen Transaktionskontext, Phase, Fehlerfamilie, Speicherbestätigung und Speicher-/Sicherungsevidenz. Nach einem Crash ist anhand des Journals und des tatsächlichen Dateibestandes zu unterscheiden, ob eine Mutation begann; kein blindes Zurücksetzen oder Weiterarbeiten.

*Die vorhandene `source_job_history.py` erfasst nur **schreibgeschützte** Quellprüfungen; sie darf keinesfalls als vollständiges Schreibtransaktionsjournal ausgegeben oder dafür wiederverwendet werden.*

## 3. Rückfall ist keine simple Kopieraktion

Ein rollbackfähiger Stand muss **exakt** die ursprüngliche Menge der verwalteten Dateien mit allen Originalbytes wiederherstellen. Unabhängige Nachprüfung darf nicht nur eine Versionsnummer vergleichen. Nicht zum Eigentumsbereich gehörende Dateien dürfen weder überschrieben noch entfernt werden. Restore muss die eigene Sicherung erhalten und vor einer Recovery-Aktion den gegenwärtigen beschädigten Zustand separat sichern können, soweit technisch möglich und ohne die ursprüngliche, geprüfte Sicherung zu gefährden.

Keine ungeschützten Verzeichnisersetzungen, keine Annahme, dass `os.replace` befüllte Zielverzeichnisse zuverlässig austauscht, keine nicht bewiesenen Rollback-Versprechen bei einem ausgefallenen HA-Prozess.

## 4. Mobile Benutzeroberfläche / Nachvollziehbarkeit

Die bestehende **eine zentrale Deployment-Schaltfläche** und die V1-inspirierte Fortschrittsleiste bleiben bestehen. Stufe 1 zeigt vor Freigabe eine eindeutige **Installierbarkeit**:
- „Bereit – geprüfte Voraussetzungen“ nur bei vollständigen G3-/G4-/G5-Gates;
- „Gesperrt – keine Änderungen“ bei Preflight-Fehler;
- „Wiederherstellung läuft“ bei bereits gestarteter Mutation;
- „Früheren Zustand wiederhergestellt und geprüft“ **nur** nach unabhängiger Byte-/Dateimengenprüfung;
- „Manuelle Wiederherstellung erforderlich“ bei fehlender Berechtigung/Sicherung/Recovery;
- „Funktionsprüfung ausstehend“ statt unbegründeter Erfolgs- oder Fehlermeldung.

Unter der kleinen `Logs`-Schaltfläche werden Zeitpunkte, Statuswechsel, Projekt- und Prüfkennung, Redaktions-Gründe und erlaubte CPU-/I/O-Metadaten nachvollziehbar. Vollständige Repositorynamen **nur im ausdrücklich freigegebenen privaten Zentralarchiv `TheDaimos/Project-Log-And-Export`**; keine Rohdateiinhalte, vollständigen Tokens oder unbereinigten HA-Logs. Der Bericht dokumentiert klar, **warum ein Rückfall ausgelöst oder abgelehnt wurde**.

## 5. Abnahmegates vor echter Freischaltung

1. Reine Zustandsmaschine, Invarianten und negativer Testkatalog ohne Dateischreiben.
2. Nachweisbare V1/V2-Exklusivsperre, Transaktionsjournal und wirklich vollständige V2-eigene Sicherungen.
3. Tests gegen künstliche Dateisysteme mit Teilwrites, Platzmangel, Hash-Mismatch, unterbrochener Restore, Power-Cut/Prozessabbruch und veränderter Quell-/Zielidentität.
4. Freigabepflichtige HA-DEV-Realtests einschließlich vollständigem Dateinachweis, gezielter Fehlersimulation und getrenntem dokumentiertem Rückfalltest.
5. Externe Prozessausfall-Recovery erst als eigene Architektur, mit gesonderter Zustimmung und Tests. Bis dahin ein ehrlich ausgegebener `external_recovery_required`-Zustand.

**Unverändert gesperrt:** DRA V2-Installation, Sicherung, Wiederherstellung, Sammelinstallation, HA-Neustart und Selbstupdate. DRA V1 DEV/PUB, V2 PUB/main, WeatherRouter und das private Exportarchiv bleiben unberührt. Entwicklungsarbeit ausschließlich auf `feature/v2-10-inventory-operation-contract`. Draft-PR #2 wird nicht zusammengeführt.

## Verweise

- `docs/V2_GATES_NACH_SOURCE_PREVIEW_REALABNAHME_2026-10-11.md` – bereits abgestimmte Reihenfolge G2–G5.
- `docs/V2_B2_PREFLIGHT_BACKUP_INTEGRITY_2026-10-09.md` – existierender SHA-gebundener Quell- und rein mathematischer Sicherungsvertrag.
- Offizielle Home-Assistant-Dokumentation: `https://developers.home-assistant.io/docs/config_entries_index/` und `https://developers.home-assistant.io/docs/integration_setup_failures/` (Installations-/Einrichtungsstatus, Wiederholversuche); `https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-entry-unloading/` (Integrationslebenszyklus).

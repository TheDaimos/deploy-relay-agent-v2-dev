# DRA V2 – G3-20: V1-Sperrenprüfung und Übergabeblockade

**Datum:** 11.10.2026  
**Status:** Rein lesender Quellcode-Audit, **kein exklusiver Besitz oder übergreifender Schreibschutz abgenommen**. Keine Änderung an DRA V1, DRA V2 PUB/main oder dem privaten Archiv.

## Geprüfte aktuelle Referenzen

Quellcode von `TheDaimos/deploy-relay-agent-dev`, Zweig `deploy/dev`, und `TheDaimos/deploy-relay-agent-pub`, Zweig `main`, wurde **nur gelesen**. Der isolierte V2-DEV-Zweig enthält zusätzlich eine historische V1-Referenz mit demselben Laufzeitvertrag.

In `custom_components/deploy_relay/__init__.py` erzeugt `DeployRelayRuntimeData`:

- `deployment_lock: asyncio.Lock = field(default_factory=asyncio.Lock)`
- `resource_lock: asyncio.Lock = field(default_factory=asyncio.Lock)`
- Startmodus `DeploymentMode.LOCKED`; die Locks werden pro V1-Laufzeitinstanz erzeugt und nicht als gemeinsamer V2-Vertrag bereitgestellt.

Die geprüften V1-DEV-Installations-/Restore-Schnittstellen in `custom_components/deploy_relay/websocket_api.py` benutzen diese Locks mit `async with runtime.deployment_lock` und `resource_lock.acquire()`, unter anderem im Bereich der Installations- und Wiederherstellungsaufträge. In den gezielt geprüften Quelltexten `__init__.py`, `websocket_api.py` und `deployment.py` wurden keine gemeinsam verifizierbaren `fcntl.flock`-, `lockf`-, `portalocker`- oder expliziten V2-Handover-Verträge gefunden.

**Beweisgrenze:** Dieser konkrete Code-Audit beweist nicht, dass im gesamten Home-Assistant-Prozess keinerlei andere Schutzmaßnahmen existieren oder welcher Zustand gerade auf der laufenden HA-Instanz gilt. Er beweist jedoch, dass die geprüften sichtbaren V1-`asyncio.Lock`-Objekte **keine gemeinsam mit V2 teilbare, prozessübergreifende Exklusivsperre** darstellen. Der Umstand, dass V1 standardmäßig `LOCKED` startet, ist keine dauerhafte verifizierte Besitzübergabe.

## Verbindliche Entscheidung für G3

Das neue G3-10-Modul `target_presence.py` kann nur **Anwesenheit und potenziell unsichere Zielwurzeln lesen**, aber keinen Inhaber und keine Fremdschreibberechtigung positiv bestätigen. Auch bei exakt einer gefundenen unauffälligen Zielwurzel bleibt das Ergebnis:

```text
owner_identity_verified = false
v1_handover_verified = false
cross_process_lock_verified = false
backup_verified = false
handover_required = true
installation_enabled = false
parallel_installation_enabled = false
```

Diese Bits dürfen weder vom Browser noch von einer händischen Quittierung umgeschrieben werden. Eine leere Fremdbelegungsliste und ein erfolgreicher Git-Dateivergleich sind ebenfalls kein positiver Besitzbeweis. Quellen-/Ziel-/Projektwechsel würden jede spätere Bindung invalidieren.

## Beabsichtigter, noch nicht freigegebener Übergabevertrag

Für eine echte Schreibfreigabe wäre künftig ein **von beiden Beteiligten nachweisbar respektierter, atomarer, prozessübergreifender Ausschluss** nötig, einschließlich aktiver V1-Aufträge, Versions-/Zielidentität, Abbruch, HA-Neustart, Verlust der Besitzerinstanz und erneuter Prüfung unmittelbar vor der ersten Mutation. V2 darf keine vermeintliche V1-Sperrdatei anlegen und daraus allein ableiten, V1 werde sie beachten. Auch eine bloße V1-Zustandsabfrage `LOCKED` ist wegen später möglicher V1-Freigaben und Rennen nicht ausreichend.

Solange ein kompatibler technischer Sperr-/Übergabevertrag nicht tatsächlich existiert und unabhängig geprüft wurde, ist die einzig zulässige G3-Entscheidung **BLOCKIERT**. Die hierfür möglicherweise notwendigen Änderungen in `TheDaimos/deploy-relay-agent-dev` oder `TheDaimos/deploy-relay-agent-pub` sind **außerhalb des aktuellen Entwicklungsauftrags ausdrücklich untersagt** und müssten später gesondert durch den Betreiber autorisiert werden. Der stabile DRA V1 bleibt bis dahin ungestört nutzbar.

## Nächster zulässiger Arbeitsschritt ohne V1-Modifikation

- G3-10 ist technisch durch isolierte negative synthetische Zielinventartests abgenommen; **keine HA-Anbindung/Installation und kein realer Besitznachweis**.
- G3-20 bleibt ein dokumentierter, konservativer Negativvertrag; als nächstes kann ausschließlich eine **schreibgeschützte, administrative Anzeige** mit Herkunft/Zeit, konservativen Unsicherheitszuständen und eigenen Grenzen geplant werden.
- Positivpfade für V1/V2-Handover und gemeinsam verwendbare Schreibsperre dürfen **nicht** simuliert oder als sicher behauptet werden. Nach ausdrücklicher zusätzlicher Nutzerfreigabe müsste der Vertrag für beide Laufzeiten entwickelt und separat real abgenommen werden.
- G4 (unabhängige vollständig geprüfte V2-Sicherung) kann **getrennt** vorbereitet werden; G5 (echte Schreibtransaktion) ist bis zum belegten G3- und G4-Erfolg blockiert.

## Nicht verändert

Keine Commits zu DRA V1, DRA V2 PUB/main, WeatherRouter oder privatem Diagnosearchiv. Kein Merge von Draft-PR #2. Keine echte Home-Assistant-Installation oder Neustart durch die Entwicklung. **Keine** Freigabe für V2-Projektinstallationen.

**C.K. – Eine Idee weiter gedacht.**

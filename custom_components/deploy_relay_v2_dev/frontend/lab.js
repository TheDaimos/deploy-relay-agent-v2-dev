/* Separate DRA V2 DEV read-only lab. No V1 custom element or URLs. */
class DRAV2DevLabPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._operation = null;
    this._measurement = null;
    this._gitConfigured = false;
    this._gitAvailable = false;
    this._gitSetup = false;
    this._gitBusy = false;
    this._gitStatus = "";
    this._lastExport = null;
    this._busy = false;
    this._timer = null;
    this._error = "";
  }

  set hass(value) {
    this._hass = value;
    if (this.isConnected && !this._loaded) {
      this._loaded = true;
      this._refresh();
    }
  }

  connectedCallback() {
    this._render();
    if (this._hass && !this._loaded) {
      this._loaded = true;
      this._refresh();
    }
  }

  disconnectedCallback() {
    if (this._timer !== null) clearTimeout(this._timer);
    this._timer = null;
    this._loaded = false;
  }

  _active() {
    return this._operation && !["success", "failed", "interrupted", "cancelled", "recovery_required"].includes(this._operation.status);
  }

  _schedule() {
    if (this._timer !== null) clearTimeout(this._timer);
    this._timer = null;
    if (this.isConnected && this._active()) {
      this._timer = setTimeout(() => { this._refresh(); }, 1500);
    }
  }

  async _refresh() {
    if (!this._hass || this._busy) return;
    this._busy = true;
    try {
      const data = await this._hass.callWS({ type: "deploy_relay_v2_dev/test/state" });
      this._operation = (data.operations || [])[0] || null;
      this._measurement = data.measurement || null;
      this._gitConfigured = data.git_configured === true;
      this._gitAvailable = data.git_available === true;
      this._error = "";
    } catch (_error) {
      this._error = "Status konnte nicht geladen werden. Verbindung prüfen.";
    } finally {
      this._busy = false;
      if (this.isConnected) this._render();
      this._schedule();
    }
  }

  async _start() {
    if (!this._hass || this._busy || this._active()) return;
    this._busy = true;
    this._render();
    try {
      const requestId = "request-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2) + "-" + Math.random().toString(36).slice(2);
      this._operation = await this._hass.callWS({
        type: "deploy_relay_v2_dev/test/start",
        request_id: requestId,
      });
      this._error = "";
    } catch (_error) {
      this._error = "Test konnte nicht gestartet werden.";
    } finally {
      this._busy = false;
      if (this.isConnected) this._render();
      this._schedule();
    }
  }

  async _measure() {
    if (!this._hass || this._busy || this._active()) return;
    this._busy = true;
    this._render();
    try {
      const requestId = "measurement-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2) + "-" + Math.random().toString(36).slice(2);
      this._operation = await this._hass.callWS({
        type: "deploy_relay_v2_dev/test/measure",
        request_id: requestId,
      });
      this._measurement = null;
      this._lastExport = null;
      this._error = "";
    } catch (_error) {
      this._error = "Messlauf konnte nicht gestartet werden.";
    } finally {
      this._busy = false;
      if (this.isConnected) this._render();
      this._schedule();
    }
  }

  async _configureGit(clear = false) {
    if (!this._hass || this._gitBusy || !this._gitAvailable) return;
    const input = this.shadowRoot?.querySelector("#git-token");
    const token = clear ? "" : String(input?.value || "").trim();
    if (input) input.value = "";
    if (!clear && !token) { this._gitStatus = "Bitte einen eigenen GitHub-Schreibtoken eingeben."; this._render(); return; }
    this._gitBusy = true;
    this._gitSetup = false;
    this._gitStatus = "Git-Zugang wird gespeichert …";
    this._render();
    try {
      const response = await this._hass.callWS({
        type: "deploy_relay_v2_dev/test/git_configure", token, clear,
      });
      this._gitConfigured = response.configured === true;
      this._gitStatus = clear ? "Git-Zugang entfernt." : "Git-Zugang eingerichtet.";
      this._lastExport = null;
    } catch (_error) {
      this._gitStatus = "Git-Zugang konnte nicht geändert werden."; 
    } finally {
      this._gitBusy = false;
      if (this.isConnected) this._render();
    }
  }

  async _exportGit() {
    if (!this._hass || this._gitBusy || this._busy || this._active()) return;
    if (!this._gitConfigured) { this._gitSetup = true; this._render(); return; }
    this._gitBusy = true;
    this._gitStatus = "Messdaten werden nach Git exportiert …";
    this._lastExport = null;
    this._render();
    try {
      const result = await this._hass.callWS({ type: "deploy_relay_v2_dev/test/git_export" });
      const url = String(result.file_url || "");
      const sha = String(result.commit_sha || "");
      if (!/^https:\/\/github\.com\/TheDaimos\/deploy-relay-agent-v2-dev\/blob\/main\/\.deploy-relay\/diagnostics\/v2-dev\/[0-9]{4}-[0-9]{2}-[0-9]{2}\/[0-9TZ-]+-[0-9a-f]{8}\.json$/.test(url) || !/^[0-9a-f]{40}$/.test(sha)) {
        throw new Error("invalid confirmation");
      }
      this._lastExport = { file_url: url, commit_sha: sha };
      this._gitStatus = "Export abgeschlossen · Commit " + sha.slice(0, 12);
    } catch (_error) {
      this._gitStatus = "Git-Export fehlgeschlagen. Zugang und Repository prüfen."; 
    } finally {
      this._gitBusy = false;
      if (this.isConnected) this._render();
    }
  }
  _render() {
    const s = this.shadowRoot;
    const op = this._operation;
    const busy = this._busy || this._active() || this._gitBusy;
    const data = this._measurement;
    const valid = data && op && data.operation_id === op.operation_id &&
      data.schema === "dra-v2-dev-measurement.v1" &&
      ["base_process_cpu_ms", "work_process_cpu_ms", "after_process_cpu_ms",
       "max_wakeup_delay_ms", "elapsed_ms", "synthetic_hashes"]
        .every(k => Number.isInteger(data[k]) && data[k] >= 0);
    const processRate = (cpuMs, duration) =>
      (100 * cpuMs / (1000 * duration)).toFixed(2) + " % eines CPU-Kerns";
    const report = valid ? `
      <p><strong>Messlauf abgeschlossen (Prozesswerte):</strong></p>
      <p>CPU-Basis (10 s): ${processRate(data.base_process_cpu_ms, 10)} ·
         CPU-Arbeitsphase (20 s): ${processRate(data.work_process_cpu_ms, 20)} ·
         CPU-Nachlauf (10 s): ${processRate(data.after_process_cpu_ms, 10)}</p>
      <p>Max. Verzögerung der Zeitsteuerung: ${data.max_wakeup_delay_ms} ms;
         Gesamtdauer: ${data.elapsed_ms} ms;
         synthetische Hash-Durchläufe: ${data.synthetic_hashes}</p>
      <p class="note">CPU-Werte gelten für den gesamten Home-Assistant-Prozess
      und sind KEIN isolierter DRA-Verbrauch. RAM und Datenträgerlast bitte
      separat in Proxmox beurteilen. Keine echten Projektdateien verarbeitet.</p>
    ` : "";
    const states = {
      queued: "Wartet", waiting_for_resource: "Wartet auf Ressourcen",
      running: "Läuft unabhängig vom Browser",
      success: "Erfolgreich abgeschlossen",
      failed: "Fehlgeschlagen", interrupted: "Durch Beenden oder Neustart unterbrochen",
      cancelled: "Abgebrochen", recovery_required: "Prüfung erforderlich",
      cancel_requested: "Beenden angefordert",
    };
    const label = op ? (states[op.status] || "Unbekannt") : "Noch kein Test gestartet";
    const progress = op && Number.isInteger(op.phase_percent) ? op.phase_percent + " % der Testschritte" : "Noch keine Messung";
    const safeId = op && /^[0-9a-f]{32}$/.test(op.operation_id) ? op.operation_id : "—";
    s.innerHTML = `
      <style>
        :host { display:block; min-height:100%; color:var(--primary-text-color, #f2f2f2); background:var(--primary-background-color, #111); font-family:var(--paper-font-body1_-_font-family, sans-serif); }
        main { margin:auto; max-width:720px; padding:24px 18px 56px; }
        h1 { font-size:24px; margin:0 0 12px; }
        article { background:var(--card-background-color,#202020); border:1px solid var(--divider-color,#555); border-radius:14px; padding:20px; margin-top:18px; }
        p { line-height:1.5; }
        .note { color:var(--secondary-text-color,#bbb); }
        .safe { font-weight:bold; color:var(--success-color,#68ba8c); }
        button { background:var(--primary-color,#396a96); color:#fff; border:0; border-radius:8px; padding:12px 16px; margin-right:8px; margin-top:10px; font:inherit; cursor:pointer; }
        button:disabled { opacity:.5; cursor:default; }
        code { overflow-wrap:anywhere; }
        .error { color:var(--error-color,#f55); }
        input.git-token { box-sizing:border-box; width:100%; min-height:40px; background:var(--primary-background-color,#151515); color:inherit; border:1px solid var(--divider-color,#555); border-radius:8px; padding:8px; }
        .git-link { display:inline-block; padding:12px 0; color:var(--primary-color,#65b4d2); overflow-wrap:anywhere; }
      </style>
      <main>
        <h1>DRA V2 DEV · Testlabor</h1>
        <p class="safe">Getrennt von DRA V1 · Nur schreibgeschützter Testbetrieb</p>
        <p>Dieser Test liest keine Projektdateien und führt keine Installation, Wiederherstellung oder Neustarts aus.</p>
        <article>
          <strong>Schreibgeschützter 40-Sekunden-Test</strong>
          <p>Starte einen 40-Sekunden-Test. Schließe dann diese Ansicht auf dem Smartphone. Öffne dieses Testlabor auf dem Notebook und prüfe, ob derselbe Auftrag noch läuft oder abgeschlossen ist.</p>
          <p><strong>Status:</strong> ${label}</p>
          <p><strong>Fortschritt:</strong> ${progress}</p>
          <p class="note"><strong>Auftragskennung:</strong> <code>${safeId}</code></p>
          ${this._error ? `<p class="error">${this._error}</p>` : ""}
          <button id="start" ${busy ? "disabled" : ""}>Testauftrag starten</button>
          <button id="measure" ${busy ? "disabled" : ""}>Messlauf starten (40 s)</button>
          <p class="note">Messlauf: 10 Sekunden Basis, 20 Sekunden begrenzte Rechenarbeit
          außerhalb der HA-Ereignisschleife, 10 Sekunden Nachlauf. Maximal ein Auftrag gleichzeitig.</p>
          ${report}
          <button id="refresh" ${this._busy ? "disabled" : ""}>Status aktualisieren</button>
        </article>
        <article>
          <strong>Messdaten nach Git exportieren</strong>
          <p class="note">Wie bei DRA V1: separater GitHub-Schreibtoken und ein neues JSON-Dokument pro Export.
          Das Zielrepository ist öffentlich. Übertragen werden ausschließlich anonyme Messzahlen, keine Projektdateien oder Auftragskennungen.</p>
          <p>Git-Zugang: ${this._gitConfigured ? "Bereit" : "Nicht eingerichtet"}</p>
          ${this._gitSetup ? `<label>Separater GitHub-Schreibtoken (nur V2-DEV-Repository)
          <input class="git-token" id="git-token" type="password" autocomplete="off" spellcheck="false" placeholder="Fine-grained Token" /></label>
          <button id="git-save" ${this._gitBusy ? "disabled" : ""}>Zugang speichern</button>
          <button id="git-cancel">Abbrechen</button>` : ""}
          <button id="git-setup" ${this._gitBusy || !this._gitAvailable ? "disabled" : ""}>Git-Export einrichten</button>
          <button id="git-export" ${this._gitBusy || busy || !valid || op?.status !== "success" || !this._gitAvailable ? "disabled" : ""}>Messdaten nach Git exportieren</button>
          ${this._gitConfigured ? `<button id="git-remove" ${this._gitBusy ? "disabled" : ""}>Git-Zugang entfernen</button>` : ""}
          <p class="note">${this._gitStatus}</p>
          ${this._lastExport ? `<a class="git-link" href="${this._lastExport.file_url}" target="_blank" rel="noopener noreferrer">Export in GitHub öffnen</a>` : ""}
        </article>
        <p class="note">Während eines laufenden Tests wird der Status etwa alle 1,5 Sekunden aktualisiert. Im Leerlauf erfolgt keine regelmäßige Abfrage. Nach einem Home-Assistant-Neustart bleiben abgeschlossene Aufträge im begrenzten Verlauf abrufbar. Vorher laufende Testaufträge erscheinen als unterbrochen und werden nicht neu gestartet.</p>
      </main>
    `;
    s.querySelector("#start")?.addEventListener("click", () => this._start());
    s.querySelector("#measure")?.addEventListener("click", () => this._measure());
    s.querySelector("#refresh")?.addEventListener("click", () => this._refresh());
    s.querySelector("#git-setup")?.addEventListener("click", () => { this._gitSetup = true; this._render(); });
    s.querySelector("#git-save")?.addEventListener("click", () => this._configureGit(false));
    s.querySelector("#git-remove")?.addEventListener("click", () => this._configureGit(true));
    s.querySelector("#git-cancel")?.addEventListener("click", () => { this._gitSetup = false; this._render(); });
    s.querySelector("#git-export")?.addEventListener("click", () => this._exportGit());
  }
}
if (!customElements.get("dra-v2-dev-lab-panel")) {
  customElements.define("dra-v2-dev-lab-panel", DRAV2DevLabPanel);
}

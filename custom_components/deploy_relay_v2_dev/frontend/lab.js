/* Separate DRA V2 DEV read-only lab. No V1 custom element or URLs. */
class DRAV2DevLabPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._operation = null;
    this._measurement = null;
    this._suite = null;
    this._projects = [];
    this._settings = {mode:"sequential",max_readonly_jobs:2,max_worker_processes:4};
    this._settingsBusy = false;
    this._settingsMessage = "";
    this._batchSelection = null;
    this._batchPreview = null;
    this._batchBusy = false;
    this._batchMessage = "";
    this._projectBusy = false;
    this._projectSaved = new Map();
    this._projectMessage = "";
    this._v1Candidates = null;
    this._gitConfigured = false;
    this._gitAvailable = false;
    this._gitSetup = false;
    this._gitBusy = false;
    this._gitStatus = "";
    this._lastExport = null;
    this._busy = false;
    this._timer = null;
    this._countdownTimer = null;
    this._countdownId = null;
    this._countdownStep = -1;
    this._countdownAt = null;
    this._countdownShown = null;
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
    if (this._countdownTimer !== null) clearTimeout(this._countdownTimer);
    this._countdownTimer = null;
    this._loaded = false;
  }

  _active() {
    return this._operation && !["success", "failed", "interrupted", "cancelled", "recovery_required"].includes(this._operation.status);
  }


  _observeCountdown(op) {
    if (!op || !/^[0-9a-f]{32}$/.test(op.operation_id)) {
      this._countdownId = null;
      this._countdownStep = -1;
      this._countdownAt = null;
      this._countdownShown = null;
      return;
    }
    if (op.operation_id !== this._countdownId) {
      this._countdownId = op.operation_id;
      this._countdownStep = -1;
      this._countdownAt = null;
      this._countdownShown = null;
    }
    if (op.status !== "running") return;
    const step = Number.isInteger(op.current_index) &&
      op.current_index >= 0 && op.current_index <= op.total_count &&
      (op.total_count === 40 || op.total_count === 87) ? op.current_index : 0;
    if (step !== this._countdownStep) {
      this._countdownStep = step;
      this._countdownAt = Date.now();
    }
  }

  _remainingText() {
    const op = this._operation;
    if (!op) return "—";
    if (op.status === "success") return "0 Sekunden – abgeschlossen";
    if (op.status === "queued" || op.status === "waiting_for_resource") {
      return "Start wird vorbereitet";
    }
    if (op.status !== "running") return "Auftrag beendet";
    if (op.total_count === 7) return "Mehrkernprüfung läuft";
    if (op.total_count !== 40 && op.total_count !== 87) return "Fortschritt wird abgerufen";
    if (op.total_count === 87 && op.current_index >= 80) return "Mehrkernprüfung läuft";
    const step = Number.isInteger(op.current_index) &&
      op.current_index >= 0 && op.current_index <= op.total_count ?
      op.current_index : 0;
    if (this._countdownAt === null) return "Noch ca. " + (op.total_count === 87 ? 80 : 40) + " Sekunden";
    const elapsed = Math.floor(Math.max(0, Date.now() - this._countdownAt) / 1000);
    // Never claim 0 while the backend still reports "running".
    const predicted = Math.max(1, (op.total_count === 87 ? 80 : 40) - step - elapsed);
    // Do not jump backwards on delayed progress messages.
    this._countdownShown = Number.isInteger(this._countdownShown) ?
      Math.min(this._countdownShown, predicted) : predicted;
    return "Noch ca. " + this._countdownShown + (this._countdownShown === 1 ? " Sekunde" : " Sekunden");
  }

  _syncCountdownTimer() {
    if (!this.isConnected || this._operation?.status !== "running") {
      if (this._countdownTimer !== null) clearTimeout(this._countdownTimer);
      this._countdownTimer = null;
      return;
    }
    if (this._countdownTimer === null) {
      this._countdownTimer = setTimeout(() => {
        this._countdownTimer = null;
        const element = this.shadowRoot?.querySelector("#remaining");
        if (element) element.textContent = this._remainingText();
        this._syncCountdownTimer();
      }, 1000);
    }
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
      this._observeCountdown(this._operation);
      this._measurement = data.measurement || null;
      this._suite = data.suite || null;
      this._projects = Array.isArray(data.projects) ? data.projects : [];
      this._settings = data.settings || this._settings;
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
      this._observeCountdown(this._operation);
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
      this._observeCountdown(this._operation);
      this._measurement = null;
      this._suite = null;
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

  async _runSequence(kind) {
    if (!this._hass || this._busy || this._active() || this._gitBusy) return;
    this._busy = true;
    this._render();
    try {
      const requestId = "readtest-" + Date.now().toString(36) + "-" +
        Math.random().toString(36).slice(2) + "-" + Math.random().toString(36).slice(2);
      const route = kind === "full" ? "all" : "multicore";
      this._operation = await this._hass.callWS({
        type: "deploy_relay_v2_dev/test/" + route, request_id: requestId,
      });
      this._observeCountdown(this._operation);
      this._suite = null;
      this._measurement = null;
      this._lastExport = null;
      this._error = "";
    } catch (_error) {
      this._error = "Mehrkern- oder Gesamttest konnte nicht gestartet werden.";
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
  _escapeProject(value) {
    return String(value ?? "").replace(/[&<>"\x27]/g, ch => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;",
      "\"": "&quot;", "\x27": "&#39;",
    })[ch]);
  }

  async _projectAction(route, values = {}) {
    if (!this._hass || this._projectBusy) return;
    this._projectBusy = true;
    this._projectMessage = "Projektverwaltung wird aktualisiert …";
    this._render();
    try {
      const result = await this._hass.callWS({
        type: "deploy_relay_v2_dev/projects/" + route, ...values,
      });
      if (route === "v1_preview") {
        this._v1Candidates = Array.isArray(result.candidates) ? result.candidates : [];
        this._projectMessage = this._v1Candidates.length + " Projekte gefunden. Übernahme ausdrücklich bestätigen."; 
      } else {
        this._projects = Array.isArray(result.projects) ? result.projects : [];
        if (route === "preselect") {
          const record = this._projects.find(p => p.repository === values.repository);
          if (!record || record.batch_preselect !== values.enabled) throw new Error("Vorauswahl nicht bestätigt");
        }
        if (route === "retention") {
          const saved = this._projects.find(project => project.repository === values.repository);
          if (!saved || saved.backup_retention !== values.backup_retention) {
            throw new Error("Sicherungsrichtlinie wurde nicht bestätigt");
          }
          this._projectSaved.set(saved.repository, saved.backup_retention);
        }
        this._v1Candidates = null;
        this._batchSelection = null;
        this._batchPreview = null;
        this._projectMessage = route === "preselect" ? "Sammelupdate-Vorauswahl gespeichert." : route === "import_v1" ?
          result.added + " Projekte übernommen, " + result.already_present + " bereits vorhanden." :
          route === "add" ? "Projekt separat in V2 vorgemerkt." : "Sicherungsrichtlinie gespeichert."; 
      }
    } catch (_error) {
      this._projectMessage = "Aktion nicht möglich; Eingaben und Berechtigung prüfen."; 
    } finally {
      this._projectBusy = false;
      if (this.isConnected) this._render();
    }
  }

  _addProject() {
    const repo = this.shadowRoot?.querySelector("#project-repo")?.value || "";
    const name = this.shadowRoot?.querySelector("#project-name")?.value || "";
    return this._projectAction("add", { repository: repo, name });
  }

  _retention(button) {
    const repo = button?.dataset?.repo;
    const input = button?.closest("tr")?.querySelector("input");
    const n = Number(input?.value);
    if (!Number.isInteger(n) || n < 3 || n > 100) {
      this._projectMessage = "Sicherungen: erlaubt sind 3 bis 100 je Projekt.";
      this._render();
      return;
    }
    this._projectSaved.delete(repo);
    return this._projectAction("retention", { repository: repo, backup_retention: n });
  }
  async _saveSettings() {
    if (!this._hass || this._settingsBusy) return;
    const root = this.shadowRoot;
    const mode = root?.querySelector("#settings-mode")?.value;
    const readonly = Number(root?.querySelector("#settings-readonly")?.value);
    const workers = Number(root?.querySelector("#settings-workers")?.value);
    if (!["sequential", "controlled"].includes(mode) || !Number.isInteger(readonly) ||
        readonly < 1 || readonly > 4 || !Number.isInteger(workers) || workers < 1 || workers > 12) {
      this._settingsMessage = "Eingaben prüfen: Aufträge 1–4, Arbeitsprozesse 1–12.";
      this._render(); return;
    }
    this._settingsBusy = true;
    try {
      const result = await this._hass.callWS({type:"deploy_relay_v2_dev/settings/save",
        mode, max_readonly_jobs:readonly, max_worker_processes:workers});
      this._settings = result.settings;
      this._settingsMessage = "Vorgaben gespeichert; Parallelbetrieb noch nicht freigegeben.";
    } catch (_error) {
      this._settingsMessage = "Vorgaben konnten nicht gespeichert werden.";
    } finally { this._settingsBusy = false; if (this.isConnected) this._render(); }
  }

  _togglePreselect(button) {
    return this._projectAction("preselect", {repository:button.dataset.repo,
      enabled:button.dataset.enabled === "true"});
  }

  async _previewBatch() {
    if (!this._hass || this._batchBusy) return;
    const inputs = [...(this.shadowRoot?.querySelectorAll(".batch-choice") || [])];
    const repositories = inputs.filter(x => x.checked).map(x => x.dataset.repo);
    this._batchSelection = repositories;
    this._batchBusy = true;
    try {
      const snapshot = await this._hass.callWS({type:"deploy_relay_v2_dev/batch/preview", repositories});
      this._batchPreview = snapshot;
      this._batchMessage = snapshot.count + " Projekte zur Leseprüfung vorgemerkt.";
    } catch (_error) {
      this._batchPreview = null;
      this._batchMessage = "Auswahl ungültig; keine Aktion gestartet.";
    } finally { this._batchBusy = false; if (this.isConnected) this._render(); }
  }
  _render() {
    const s = this.shadowRoot;
    const projectRows = this._projects.map(p => { const saved = this._projectSaved.get(p.repository) === p.backup_retention; return `<tr><td>${this._escapeProject(p.name)}<div class="note">${this._escapeProject(p.repository)}</div></td><td>${p.origin === "v1_import" ? "DRA V1" : "Manuell"}</td><td><input class="retention" type="number" min="3" max="100" value="${Number.isInteger(p.backup_retention) ? p.backup_retention : 10}" aria-label="Sicherungen" /><button class="retention-save ${saved ? "retention-saved" : ""}" data-repo="${this._escapeProject(p.repository)}" ${this._projectBusy ? "disabled" : ""}>${saved ? "Gespeichert" : "Speichern"}</button><button class="preselect-toggle" data-repo="${this._escapeProject(p.repository)}" data-enabled="${p.batch_preselect === false}" ${this._projectBusy ? "disabled" : ""}>Sammelupdate: ${p.batch_preselect === false ? "Aus" : "Ein"}</button></td></tr>`; }).join("");
    const batchRows = this._projects.map(p => {
      const checked = this._batchSelection === null ? p.batch_preselect !== false : this._batchSelection.includes(p.repository);
      return `<label class="batch-line"><input type="checkbox" class="batch-choice" data-repo="${this._escapeProject(p.repository)}" ${checked ? "checked" : ""} /> ${this._escapeProject(p.name)}</label>`;
    }).join("");
    const batchReport = Array.isArray(this._batchPreview?.selected) ?
      this._batchPreview.selected.map(p => `<li>${this._escapeProject(p.name)}: Quellstand nicht geprüft</li>`).join("") : "";
    const previewRows = Array.isArray(this._v1Candidates) ? this._v1Candidates.map(p => `<li>${this._escapeProject(p.name)} – ${this._escapeProject(p.repository)}</li>`).join("") : "";
    const op = this._operation;
    const busy = this._busy || this._active() || this._gitBusy;
    const suite = this._suite && op && this._suite.operation_id === op.operation_id ? this._suite : null;
    const data = suite?.mode === "full" ? suite.measurement : this._measurement;
    const valid = data && op && data.operation_id === op.operation_id &&
      data.schema === "dra-v2-dev-measurement.v2" &&
      ["base_process_cpu_ms", "work_process_cpu_ms", "after_process_cpu_ms",
       "max_wakeup_delay_ms", "elapsed_ms", "synthetic_hashes"]
        .every(k => Number.isInteger(data[k]) && data[k] >= 0);
    const validSuite = suite?.schema === "dra-v2-dev-suite.v2" &&
      ["full", "multicore"].includes(suite.mode) &&
      suite.multicore?.schema === "dra-v2-dev-multicore.v2" &&
      Array.isArray(suite.multicore.levels) && suite.multicore.levels.length === 7;
    const processRate = (cpuMs, duration) =>
      (100 * cpuMs / (1000 * duration)).toFixed(2) + " % eines CPU-Kerns";
    const memory = valid ? data.memory : null;
    const kib = value => Number.isInteger(value) && value >= 0 ? (value / 1024).toFixed(1) + " MiB" : "Nicht verfügbar";
    const memoryRow = (label, key) => {
      const m = memory?.snapshots?.[key];
      if (!m) return "";
      return `<tr><th>${label}</th><td>${kib(m.total_kib)}</td><td>${kib(m.used_effective_kib)}</td><td>${kib(m.free_kib)}</td><td>${kib(m.available_kib)}</td><td>${kib(m.ha_process_rss_kib)}</td></tr>`;
    };
    const memoryReport = memory?.schema === "dra-v2-dev-memory.v1" ? `
      <p><strong>Arbeitsspeicher des HA-Linux-Umfelds</strong></p>
      <div class="table-wrap"><table><thead><tr><th>Messpunkt</th><th>Gesamt</th><th>Belegt (effektiv)</th><th>Frei</th><th>Verfügbar</th><th>HA-Prozess (RSS)</th></tr></thead><tbody>
      ${memoryRow("Start", "start")}${memoryRow("Nach Basis", "base_end")}${memoryRow("Nach Last", "work_end")}${memoryRow("Ende", "end")}
      </tbody></table></div>
      <p class="note">„Belegt“ = Gesamt minus verfügbar. „Frei“ ist ohne Zwischenspeicher. Die Werte stammen aus der Linux-Sicht von Home Assistant, nicht direkt aus Proxmox.</p>
      <p class="note"><strong>DRA V1: nicht einzeln messbar · DRA V2: nicht einzeln messbar.</strong> Beide Integrationen teilen sich denselben Home-Assistant-Prozess. Ein genauer Speicherverbrauch pro Integration lässt sich daraus nicht seriös bestimmen.</p>
    ` : "";
    const baseline = validSuite ? suite.multicore.levels[0] : null;
    const baselineRate = baseline?.status === "ok" && Number.isInteger(baseline.wall_ms) && baseline.wall_ms > 0 &&
      Number.isInteger(baseline.iterations_total) ? baseline.iterations_total / baseline.wall_ms : null;
    const multiRows = validSuite ? suite.multicore.levels.map(level => {
      const workers = [1, 2, 4, 6, 8, 10, 12].includes(level.workers) ? level.workers : "—";
      const ok = level.status === "ok";
      const millis = ok && Number.isInteger(level.wall_ms) ? level.wall_ms + " ms" : "Nicht verfügbar";
      const cpuTime = ok && Number.isInteger(level.aggregate_worker_cpu_ms) ?
        level.aggregate_worker_cpu_ms + " ms" : "—";
      const hashes = ok && Number.isInteger(level.iterations_total) ? level.iterations_total : "—";
      const rate = ok && Number.isInteger(level.wall_ms) && level.wall_ms > 0 &&
        Number.isInteger(level.iterations_total) ? level.iterations_total / level.wall_ms : null;
      const throughput = rate !== null ? Math.round(rate * 1000).toLocaleString("de-DE") + " Runden/s" : "—";
      const factor = rate !== null && baselineRate !== null && baselineRate > 0 ?
        (rate / baselineRate).toFixed(2).replace(".", ",") + "×" : "—";
      return `<tr><th>${workers} Prozess(e)</th><td>${ok ? "Gemessen" : "Nicht verfügbar"}</td><td>${millis}</td><td>${cpuTime}</td><td>${hashes}</td><td>${throughput}</td><td>${factor}</td></tr>`;
    }).join("") : "";
    const multicoreReport = validSuite ? `
      <p><strong>Mehrkern-Diagnose:</strong> ${suite.mode === "full" ? "Gesamttest" : "Einzeltest"}</p>
      <p>Vom HA-Prozess sichtbare logische Kerne: ${
        Number.isInteger(suite.multicore.logical_cpus_visible) ?
        suite.multicore.logical_cpus_visible : "Nicht verfügbar"
      }; laut CPU-Zuordnung: ${
        Number.isInteger(suite.multicore.affinity_cpus_visible) ?
        suite.multicore.affinity_cpus_visible : "Nicht verfügbar"
      }</p>
      <div class="table-wrap"><table><thead><tr><th>Arbeitsprozesse</th><th>Status</th><th>Gesamtdauer</th><th>CPU-Zeit</th><th>Rechenschritte</th><th>Durchsatz</th><th>Vergleich</th></tr></thead>
      <tbody>${multiRows}</tbody></table></div>
      <p class="note">Die sieben Stufen 1, 2, 4, 6, 8, 10 und 12 laufen nacheinander.
      Es laufen nie mehr als zwölf kurzlebige Arbeitsprozesse gleichzeitig. Die Werte enthalten
      auch Start- und Verwaltungsaufwand. Das Verhältnis bezieht sich auf den
      Durchsatz des Ein-Prozess-Laufs, nicht auf die Kernzahl oder den isolierten
      Verbrauch einzelner HA-Integrationen.</p>
    ` : "";
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
      ${memoryReport}
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
        .table-wrap { overflow-x:auto; max-width:100%; }
        table { border-collapse:collapse; width:100%; font-size:12px; }
        th, td { padding:8px; border-bottom:1px solid var(--divider-color,#555); text-align:left; white-space:nowrap; }

        input.retention { width:64px; margin-right:6px; }
        .batch-line { display:block; padding:8px 0; border-bottom:1px solid var(--divider-color,#555); }
        .batch-line input { min-width:20px; min-height:20px; }
        button.retention-saved { background:#247d42; color:#fff; }
        input.project-text { box-sizing:border-box; width:100%; min-height:40px; background:var(--primary-background-color,#151515); color:inherit; border:1px solid var(--divider-color,#555); border-radius:8px; padding:8px; margin:5px 0; }
        input.git-token { box-sizing:border-box; width:100%; min-height:40px; background:var(--primary-background-color,#151515); color:inherit; border:1px solid var(--divider-color,#555); border-radius:8px; padding:8px; }
        .git-link { display:inline-block; padding:12px 0; color:var(--primary-color,#65b4d2); overflow-wrap:anywhere; }
        .countdown { font-size:19px; font-weight:700; font-variant-numeric:tabular-nums; }
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
          <p><strong>Restzeit:</strong> <span class="countdown" id="remaining">${this._remainingText()}</span></p>
          <p class="note"><strong>Auftragskennung:</strong> <code>${safeId}</code></p>
          ${this._error ? `<p class="error">${this._error}</p>` : ""}
          <button id="start" ${busy ? "disabled" : ""}>Testauftrag starten</button>
          <button id="measure" ${busy ? "disabled" : ""}>Messlauf starten (40 s)</button>
          <button id="multicore" ${busy ? "disabled" : ""}>Mehrkern-Diagnose (1 / 2 / 4 / 6 / 8 / 10 / 12)</button>
          <button id="all" ${busy ? "disabled" : ""}>Alle Tests nacheinander starten</button>
          <p class="note">Gesamttest: erst 40 Sekunden Auftragsprüfung, dann 40 Sekunden CPU-/Speichermessung,
          anschließend nacheinander 1, 2, 4, 6, 8, 10 und 12 getrennte Arbeitsprozesse. Ein Auftrag, ein Git-Export.</p>
          <p class="note">Messlauf: 10 Sekunden Basis, 20 Sekunden begrenzte Rechenarbeit
          außerhalb der HA-Ereignisschleife, 10 Sekunden Nachlauf. Maximal ein Auftrag gleichzeitig.</p>
          ${report}
          ${multicoreReport}
          <button id="refresh" ${this._busy ? "disabled" : ""}>Status aktualisieren</button>
        </article>
        <article>
          <strong>DRA-Einstellungen · Auftragsverarbeitung</strong>
          <p class="note">Gespeicherte Planungsvorgaben. Die aktive Testlabor-Sperre bleibt bei
          einem Leseauftrag und null Schreibaufträgen. Dies begrenzt derzeit keine echten Prozessorkerne.</p>
          <label>Betriebsart
            <select id="settings-mode" class="project-text">
              <option value="sequential" ${this._settings.mode === "sequential" ? "selected" : ""}>Nacheinander</option>
              <option value="controlled" ${this._settings.mode === "controlled" ? "selected" : ""}>Gesteuert parallel (noch in Entwicklung)</option>
              <option value="automatic" disabled>Automatisch (noch nicht verfügbar)</option>
            </select>
          </label>
          <label>Parallele Leseaufträge (spätere Obergrenze 1–4)
            <input id="settings-readonly" class="project-text" type="number" min="1" max="4" value="${this._settings.max_readonly_jobs}" />
          </label>
          <label>DRA-Arbeitsprozesse (spätere Obergrenze 1–12)
            <input id="settings-workers" class="project-text" type="number" min="1" max="12" value="${this._settings.max_worker_processes}" />
          </label>
          <button id="settings-save" ${this._settingsBusy ? "disabled" : ""}>Vorgaben speichern</button>
          <p class="note">${this._escapeProject(this._settingsMessage)}</p>
          <p class="note">Die separate feste Mehrkern-Diagnose bleibt unverändert. Kein
          Schreibzugriff, kein CPU-Pinning und keine automatische Ressourcensteuerung.</p>
        </article>

        <article>
          <strong>Meine Projekte · V2-Entwicklung</strong>
          <p class="note">Projektmetadaten getrennt von DRA V1 verwalten. V1 bleibt unverändert.
          Übernahme kopiert weder Git-Zugangsdaten noch Installationsstände oder Sicherungsdateien.</p>
          <button id="project-preview" ${this._projectBusy ? "disabled" : ""}>V1-Projekte ansehen</button>
          ${this._v1Candidates !== null ? `<p>${this._v1Candidates.length} V1-Projekte gefunden:</p><ul>${previewRows}</ul>
          <button id="project-import" ${this._projectBusy || this._v1Candidates.length === 0 ? "disabled" : ""}>Diese Projekte in V2 übernehmen</button>
          <button id="project-cancel">Übernahme abbrechen</button>` : ""}
          <p><strong>Neues Projekt hinterlegen</strong></p>
          <label>GitHub-Repository (Eigentümer/Repository)<input id="project-repo" class="project-text" placeholder="TheDaimos/projekt-dev" autocomplete="off" /></label>
          <label>Anzeigename (optional)<input id="project-name" class="project-text" placeholder="Mein Projekt" autocomplete="off" /></label>
          <button id="project-add" ${this._projectBusy ? "disabled" : ""}>Projekt vormerken</button>
          <p class="note">${this._escapeProject(this._projectMessage)}</p>
          ${this._projects.length ? `<div class="table-wrap"><table><thead><tr><th>Projekt</th><th>Herkunft</th><th>Sicherungen behalten</th></tr></thead>
          <tbody>${projectRows}</tbody></table></div>` : `<p class="note">Noch keine Projekte in V2 hinterlegt.</p>`}
          <p class="note"><strong>Backup-Richtlinie:</strong> 10 gesicherte Stände je Projekt, individuell 3–100.
          Neue Einträge sind zunächst ungeprüft. Installation, tatsächliche Sicherung,
          Rotation und Wiederherstellung bleiben bis zur separaten Transaktionsabnahme gesperrt.</p>
        </article>
        <article>
          <strong>Sammelaktualisierung · Auswahl vorbereiten</strong>
          <p class="note">Die gespeicherte Vorauswahl wird nur beim Öffnen dieser
          Ansicht verwendet. Häkchen gelten für den aktuellen Vorgang.</p>
          ${this._projects.length ? batchRows : "<p>Bitte erst Projekte anlegen oder aus V1 übernehmen.</p>"}
          <button id="batch-preview" ${this._batchBusy || this._projects.length === 0 ? "disabled" : ""}>Auswahl prüfen (ohne Installation)</button>
          <p class="note">${this._escapeProject(this._batchMessage)}</p>
          ${this._batchPreview ? `<p>${this._batchPreview.count} Projekte ausgewählt. Git-Stand
          noch nicht überprüft; keine Installation möglich.</p><ul>${batchReport}</ul>` : ""}
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
          <button id="git-export" ${this._gitBusy || busy || (!valid && !validSuite) || op?.status !== "success" || !this._gitAvailable ? "disabled" : ""}>Messdaten nach Git exportieren</button>
          ${this._gitConfigured ? `<button id="git-remove" ${this._gitBusy ? "disabled" : ""}>Git-Zugang entfernen</button>` : ""}
          <p class="note">${this._gitStatus}</p>
          ${this._lastExport ? `<a class="git-link" href="${this._lastExport.file_url}" target="_blank" rel="noopener noreferrer">Export in GitHub öffnen</a>` : ""}
        </article>
        <p class="note">Während eines laufenden Tests wird der Status etwa alle 1,5 Sekunden aktualisiert. Im Leerlauf erfolgt keine regelmäßige Abfrage. Nach einem Home-Assistant-Neustart bleiben abgeschlossene Aufträge im begrenzten Verlauf abrufbar. Vorher laufende Testaufträge erscheinen als unterbrochen und werden nicht neu gestartet.</p>
      </main>
    `;
    s.querySelector("#start")?.addEventListener("click", () => this._start());
    s.querySelector("#measure")?.addEventListener("click", () => this._measure());
    s.querySelector("#multicore")?.addEventListener("click", () => this._runSequence("multicore"));
    s.querySelector("#all")?.addEventListener("click", () => this._runSequence("full"));
    s.querySelector("#refresh")?.addEventListener("click", () => this._refresh());
    s.querySelector("#git-setup")?.addEventListener("click", () => { this._gitSetup = true; this._render(); });
    s.querySelector("#git-save")?.addEventListener("click", () => this._configureGit(false));
    s.querySelector("#git-remove")?.addEventListener("click", () => this._configureGit(true));
    s.querySelector("#git-cancel")?.addEventListener("click", () => { this._gitSetup = false; this._render(); });
    s.querySelector("#git-export")?.addEventListener("click", () => this._exportGit());
    s.querySelector("#settings-save")?.addEventListener("click", () => this._saveSettings());
    s.querySelector("#batch-preview")?.addEventListener("click", () => this._previewBatch());
    s.querySelectorAll(".preselect-toggle")?.forEach(button => button.addEventListener("click", () => this._togglePreselect(button)));
    s.querySelector("#project-preview")?.addEventListener("click", () => this._projectAction("v1_preview"));
    s.querySelector("#project-import")?.addEventListener("click", () => this._projectAction("import_v1"));
    s.querySelector("#project-cancel")?.addEventListener("click", () => { this._v1Candidates = null; this._render(); });
    s.querySelector("#project-add")?.addEventListener("click", () => this._addProject());
    s.querySelectorAll(".retention-save")?.forEach(button => {
      button.addEventListener("click", () => this._retention(button));
      button.closest("tr")?.querySelector("input.retention")?.addEventListener("input", () => {
        this._projectSaved.delete(button.dataset.repo);
        button.classList.remove("retention-saved");
        button.textContent = "Speichern";
      });
    });
    this._syncCountdownTimer();
  }
}
if (!customElements.get("dra-v2-dev-lab-panel")) {
  customElements.define("dra-v2-dev-lab-panel", DRAV2DevLabPanel);
}

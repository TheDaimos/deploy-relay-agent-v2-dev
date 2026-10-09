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
    this._cpuStatus = {available_cores:null,warning:null};
    this._cpuBusy = false;
    this._batchSelection = null;
    this._batchPreview = null;
    this._batchBusy = false;
    this._batchMessage = "";
    this._projectBusy = false;
    this._projectSaved = new Map();
    this._projectMessage = "";
    this._sourceBusy = false;
    this._sourceMessage = "";
    this._sourcePreview = null;
    this._gitReadConfigured = false;
    this._gitReadBusy = false;
    this._gitReadMessage = "";
    this._v1Candidates = null;
    this._gitConfigured = false;
    this._centralExport = {configured:false,repository_configured:false,server_token_available:false,pending:false,repository:null};
    this._archiveBusy = false;
    this._gitDialogOpen = false;
    this._diagnosticsExportReady = false;
    this._archiveMessage = "";
    this._archiveCheckState = "idle";
    this._downloadBusy = false;
    this._downloadStatus = "";
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
      this._cpuStatus = data.cpu_status || this._cpuStatus;
      this._gitConfigured = data.git_configured === true;
      this._centralExport = data.central_export || this._centralExport;
      this._diagnosticsExportReady = data.diagnostics_export_ready === true;
      if (this._archiveCheckState === "idle" && this._centralExport.configured) {
        // Stored on HA, but not necessarily reverified this browser session.
        this._archiveCheckState = "stored";
      }
      this._gitReadConfigured = data.git_read_configured === true;
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
  _openGitDialog() {
    this._gitDialogOpen = true;
    this._archiveMessage = "";
    this._render();
    this.shadowRoot?.querySelector("#git-dialog-repo")?.focus?.();
  }

  _closeGitDialog() {
    if (this._archiveBusy || this._gitBusy) return;
    const input = this.shadowRoot?.querySelector("#git-dialog-token");
    if (input) input.value = "";
    this._gitDialogOpen = false;
    this._render();
  }

  async _configureArchiveDialog() {
    if (!this._hass || this._archiveBusy || this._gitBusy) return;
    const repository = this.shadowRoot?.querySelector("#git-dialog-repo")?.value?.trim() || "";
    const secretInput = this.shadowRoot?.querySelector("#git-dialog-token");
    const token = secretInput?.value || "";
    // Clear the transient secret BEFORE calling HA or painting the status.
    if (secretInput) secretInput.value = "";
    const validRepo = /^[A-Za-z0-9-]{1,39}\/[A-Za-z0-9_.-]{1,100}$/.test(repository);
    const reuse = !token && this._centralExport.configured === true &&
      repository === this._centralExport.repository;
    if (!validRepo || (!reuse && (token.length < 10 || token.length > 512))) {
      this._archiveCheckState = "error";
      this._archiveMessage = reuse ? "Gespeicherten Zugang prüfen." :
        "Repository und GitHub-Token prüfen. Ein vorhandener Token muss für dasselbe Repository nicht erneut eingegeben werden.";
      this._render();
      return;
    }
    this._archiveBusy = true;
    this._archiveCheckState = "checking";
    this._archiveMessage = reuse ?
      "Gespeicherte Verbindung wird erneut geprüft …" :
      "Privates Repository und GitHub-Zugang werden geprüft …";
    this._render();
    try {
      const result = await this._hass.callWS(reuse ? {
        type:"deploy_relay_v2_dev/archive_repository/check",
      } : {
        type:"deploy_relay_v2_dev/archive_repository/configure", repository, token,
      });
      if (!result || result.repository !== repository || result.configured !== true ||
          result.repository_configured !== true || result.server_token_available !== true ||
          (reuse && result.verified_private_read !== true)) {
        throw new Error("archive validation failed");
      }
      this._centralExport = result;
      this._gitConfigured = true;
      this._archiveCheckState = "success";
      this._archiveMessage = reuse ?
        "Verbindung erfolgreich geprüft: Privates Repository erreichbar. Schreibberechtigung wird beim Export überprüft." :
        "Zugang gespeichert und privates Repository erfolgreich geprüft. Der Token bleibt serverseitig hinterlegt.";
    } catch (_error) {
      this._archiveCheckState = "error";
      this._archiveMessage =
        "Prüfung fehlgeschlagen: Repository, privater Zugriff oder GitHub-Berechtigung kontrollieren. Bereits gespeicherte Einstellungen bleiben erhalten.";
    } finally {
      this._archiveBusy = false;
      if (this.isConnected) this._render();
    }
  }

  async _clearArchiveDialog() {
    if (!this._hass || this._archiveBusy || this._gitBusy) return;
    this._archiveBusy = true;
    this._archiveMessage = "Exportzugang wird entfernt …";
    this._render();
    try {
      const result = await this._hass.callWS({
        type:"deploy_relay_v2_dev/archive_repository/clear",
      });
      this._centralExport = result;
      this._gitConfigured = result.configured === true;
      this._archiveMessage = "Repository und serverseitiger Zugang entfernt. JSON-Download bleibt verfügbar.";
      this._archiveCheckState = "idle";
    } catch (_error) {
      this._archiveMessage = "Entfernen nicht möglich. Möglicherweise wartet ein Export auf Wiederholung.";
    } finally {
      this._archiveBusy = false;
      if (this.isConnected) this._render();
    }
  }

  async _downloadJSON() {
    if (!this._hass || this._downloadBusy || this._busy || this._active()) return;
    this._downloadBusy = true;
    this._downloadStatus = "Bereinigte Diagnose für lokalen Download wird erstellt …";
    try {
      const result = await this._hass.callWS({
        type:"deploy_relay_v2_dev/test/download_json",
      });
      if (!result || result.application_id !== "deploy-relay-agent-v2" ||
          result.mime_type !== "application/json" ||
          !/^20[0-9]{2}-[0-9]{2}-[0-9T-]+Z__deploy-relay-agent-v2__0\.1\.[0-9]{1,3}__diagnostics__[0-9a-f]{32}\.json$/.test(result.filename) ||
          !/^[0-9a-f]{32}$/.test(result.export_id) ||
          !result.filename.endsWith("__" + result.export_id + ".json") ||
          typeof result.content !== "string" || result.content.length > 8192) {
        throw new Error("invalid download");
      }
      const payload = JSON.parse(result.content);
      if (payload?.application?.id !== result.application_id ||
          payload?.export?.exportId !== result.export_id) {
        throw new Error("invalid diagnostic metadata");
      }
      const file = new Blob([result.content], {type:"application/json;charset=utf-8"});
      const objectUrl = URL.createObjectURL(file);
      try {
        const link = document.createElement("a");
        link.href = objectUrl;
        link.download = result.filename;
        link.click();
      } finally {
        setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
      }
      this._downloadStatus = "JSON-Download gestartet: " + result.filename;
    } catch (_error) {
      this._downloadStatus = "JSON-Download fehlgeschlagen. Diagnoseverfügbarkeit prüfen.";
    } finally {
      this._downloadBusy = false;
      if (this.isConnected) this._render();
    }
  }

  async _exportGit(retry=false) {
    if (!this._hass || this._gitBusy || this._busy || this._active()) return;
    this._gitBusy = true;
    this._gitStatus = retry ?
      "Erneute private Übertragung des gespeicherten Exports läuft …" :
      "Bereinigter Diagnoseexport in das gewählte private Repository läuft …";
    this._lastExport = null;
    this._render();
    try {
      const result = await this._hass.callWS({
        type: retry ? "deploy_relay_v2_dev/test/git_retry" : "deploy_relay_v2_dev/test/git_export"
      });
      const path = String(result.path || "");
      const eid = String(result.export_id || "");
      const sha = String(result.commit_sha || "");
      const repository = String(result.repository || "");
      const branch = String(result.branch || "");
      const expected = /^exports\/deploy-relay-agent-v2\/[0-9]{4}-[0-9]{2}\/diagnostics\/[0-9T-]+Z__deploy-relay-agent-v2__0\.1\.[0-9]{1,3}__diagnostics__[0-9a-f]{32}\.json$/;
      if (repository !== this._centralExport.repository ||
          !/^[A-Za-z0-9][A-Za-z0-9_.\/-]{0,99}$/.test(branch) ||
          !expected.test(path) ||
          !/^[0-9a-f]{32}$/.test(eid) || !/^[0-9a-f]{40}$/.test(sha) ||
          !path.endsWith("__" + eid + ".json") ||
          !String(result.file_url || "").startsWith("https://github.com/" + repository + "/blob/")) {
        throw new Error("invalid private archive confirmation");
      }
      this._lastExport = {file_url:result.file_url, path, export_id:eid, commit_sha:sha};
      this._centralExport = {...this._centralExport, pending:false};
      this._gitStatus = "Privater Export erfolgreich · Export-ID " + eid + " · " + path;
    } catch (_error) {
      this._gitStatus = retry ?
        "Wiederholung fehlgeschlagen. Der bereinigte Export bleibt lokal erhalten." :
        "GitHub-Export fehlgeschlagen. Kein öffentliches Ersatzziel. JSON kann unabhängig heruntergeladen werden.";
      // A failed request does not necessarily mean an export was queued.
      // The server status is the authority; never create a fictional pending flag.
      try {
        const status = await this._hass.callWS({type:"deploy_relay_v2_dev/test/state"});
        this._centralExport = status.central_export || this._centralExport;
        this._gitConfigured = this._centralExport.configured === true;
        this._diagnosticsExportReady = status.diagnostics_export_ready === true;
      } catch (_ignored) { /* Keep last known status, show error above. */ }
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
        if (route === "import_v1" || route === "add") {
          this._batchSelection = null;
          this._batchPreview = null;
        }
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



  async _configureGitRead(clear=false) {
    if (!this._hass || this._gitReadBusy) return;
    const token = clear ? null : this.shadowRoot?.querySelector("#source-read-token")?.value?.trim();
    if (!clear && (!token || token.length < 10 || token.length > 512)) {
      this._gitReadMessage = "Bitte einen gültigen GitHub-Lesezugang eingeben.";
      this._render();
      return;
    }
    this._gitReadBusy = true;
    try {
      const result = await this._hass.callWS(clear ? {
        type:"deploy_relay_v2_dev/git_read/clear",
      } : {
        type:"deploy_relay_v2_dev/git_read/configure", token,
      });
      this._gitReadConfigured = result.configured === true;
      this._gitReadMessage = clear ?
        "V2-Lesezugang entfernt. Private Quellen sind nicht mehr prüfbar." :
        "Separater V2-GitHub-Lesezugang gespeichert.";
    } catch (_error) {
      this._gitReadMessage = "GitHub-Lesezugang konnte nicht geändert werden.";
    } finally {
      this._gitReadBusy = false;
      if (this.isConnected) this._render();
    }
  }

  async _sourceCheck(button) {
    if (!button || !this._hass || this._sourceBusy) return;
    const repository = button.dataset.repo;
    const ref = this.shadowRoot?.querySelector("#source-ref")?.value?.trim() || "";
    this._sourceBusy = true;
    this._sourcePreview = null;
    this._sourceMessage = "GitHub-Quelle und vorhandene Dateien werden schreibgeschützt geprüft …";
    this._render();
    try {
      const report = await this._hass.callWS({
        type:"deploy_relay_v2_dev/projects/source_preview", repository, ref,
      });
      if (!report || report.repository?.toLowerCase() !== repository.toLowerCase() ||
          report.installation_enabled !== false || report.sources_verified !== true) {
        throw new Error("ungueltiges Quellpruefungsergebnis");
      }
      this._sourcePreview = report;
      this._sourceMessage = "Quellprüfung abgeschlossen. Keine Installation freigegeben.";
    } catch (_error) {
      this._sourceMessage = "Quelle nicht erreichbar oder sicherheitstechnisch nicht prüfbar. Kein Update als aktuell bestätigt.";
    } finally {
      this._sourceBusy = false;
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
      this._cpuStatus = result.cpu_status || this._cpuStatus;
      this._settingsMessage = "Vorgaben gespeichert; Parallelbetrieb noch nicht freigegeben.";
    } catch (_error) {
      this._settingsMessage = "Vorgaben konnten nicht gespeichert werden.";
    } finally { this._settingsBusy = false; if (this.isConnected) this._render(); }
  }

  async _ackCpuWarning() {
    if (!this._hass || this._cpuBusy) return;
    this._cpuBusy = true;
    try {
      const result = await this._hass.callWS({
        type:"deploy_relay_v2_dev/settings/ack_cpu_warning",
      });
      this._cpuStatus = result.cpu_status;
      this._settingsMessage = "Hinweis bestätigt. Neue Reduzierungen werden weiterhin gemeldet.";
    } catch (_error) {
      this._settingsMessage = "CPU-Hinweis konnte nicht bestätigt werden.";
    } finally {
      this._cpuBusy = false;
      if (this.isConnected) this._render();
    }
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
    // The HA test status can refresh while this dialog is open. Preserve the
    // unsent secret only in the transient password input, never component state.
    const unsentToken = this._gitDialogOpen ?
      s?.querySelector("#git-dialog-token")?.value || "" : "";
    const previousRepo = this._gitDialogOpen ?
      s?.querySelector("#git-dialog-repo")?.value : null;
    // Unmounted inputs return undefined. Assigning that to an HTML input.value
    // turns it into the literal text "undefined" (seen on Android/desktop).
    const unsentRepository = typeof previousRepo === "string" ? previousRepo : null;
    const projectRows = this._projects.map(p => { const saved = this._projectSaved.get(p.repository) === p.backup_retention; return `<tr><td>${this._escapeProject(p.name)}<div class="note">${this._escapeProject(p.repository)}</div></td><td>${p.origin === "v1_import" ? "DRA V1" : "Manuell"}</td><td><input class="retention" type="number" min="3" max="100" value="${Number.isInteger(p.backup_retention) ? p.backup_retention : 10}" aria-label="Sicherungen" /><button class="retention-save ${saved ? "retention-saved" : ""}" data-repo="${this._escapeProject(p.repository)}" ${this._projectBusy ? "disabled" : ""}>${saved ? "Gespeichert" : "Speichern"}</button><button class="preselect-toggle" data-repo="${this._escapeProject(p.repository)}" data-enabled="${p.batch_preselect === false}" ${this._projectBusy ? "disabled" : ""}>Sammelupdate: ${p.batch_preselect === false ? "Aus" : "Ein"}</button><button class="source-check" data-repo="${this._escapeProject(p.repository)}" ${this._sourceBusy ? "disabled" : ""}>Git-Quelle prüfen</button></td></tr>`; }).join("");
    const batchRows = this._projects.map(p => {
      const checked = this._batchSelection === null ? p.batch_preselect !== false : this._batchSelection.includes(p.repository);
      return `<label class="batch-line"><input type="checkbox" class="batch-choice" data-repo="${this._escapeProject(p.repository)}" ${checked ? "checked" : ""} /> ${this._escapeProject(p.name)}</label>`;
    }).join("");
    const batchReport = Array.isArray(this._batchPreview?.selected) ?
      this._batchPreview.selected.map(p => `<li>${this._escapeProject(p.name)}: Quellstand nicht geprüft</li>`).join("") : "";
    const sourceReport = this._sourcePreview;
    const sourceList = (files, limit=25) => {
      if (!Array.isArray(files) || !files.length) return "<li>Keine</li>";
      const sample = files.slice(0, limit).map(name => `<li>${this._escapeProject(name)}</li>`).join("");
      const more = files.length > limit ? `<li>… und ${files.length-limit} weitere</li>` : "";
      return sample + more;
    };
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
        main { margin:auto; width:100%; max-width:1600px; box-sizing:border-box; padding:24px clamp(12px,2.5vw,36px) 56px; }
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
        .warning-cpu { border:2px solid var(--warning-color,#d6a13a); border-radius:10px; padding:12px; margin:12px 0; }
        .warning-cpu p { margin:8px 0; }
        .batch-line { display:block; padding:8px 0; border-bottom:1px solid var(--divider-color,#555); }
        .batch-line input { min-width:20px; min-height:20px; }
        button.retention-saved { background:#247d42; color:#fff; }
        input.project-text { box-sizing:border-box; width:100%; min-height:40px; background:var(--primary-background-color,#151515); color:inherit; border:1px solid var(--divider-color,#555); border-radius:8px; padding:8px; margin:5px 0; }
        input.git-token { box-sizing:border-box; width:100%; min-height:40px; background:var(--primary-background-color,#151515); color:inherit; border:1px solid var(--divider-color,#555); border-radius:8px; padding:8px; }
        .git-main-actions { display:flex; flex-wrap:wrap; align-items:center; gap:8px; }
         .git-main-actions button { margin-top:6px; }
         .diagnostic-results { overflow:hidden; }
         @media (min-width:1000px) {
           .git-main-actions { gap:12px; }
           .git-main-actions button { min-width:165px; }
           .diagnostic-results table { font-size:13px; }
         }
         @media (max-width:600px) {
           main { padding:12px 10px 32px; }
           article { padding:14px; margin-top:12px; }
           .git-main-actions { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); }
           .git-main-actions button { min-width:0; width:100%; margin:0; padding:12px 6px; font-size:13px; }
           .git-main-actions button:first-child { grid-column:1 / -1; }
           button { max-width:100%; }
         }
        .git-main-actions button { margin-right:0; }
        .git-dialog-backdrop { position:fixed; inset:0; z-index:2147483644; display:flex;
          align-items:center; justify-content:center; padding:12px; box-sizing:border-box;
          background:rgba(0,0,0,.78); }
        .git-dialog { width:min(100%,560px); max-height:92dvh; overflow:auto; box-sizing:border-box;
          background:var(--card-background-color,#222); border:1px solid var(--divider-color,#555);
          border-radius:14px; padding:18px; box-shadow:0 14px 38px #0009; }
        .git-dialog header { display:flex; align-items:center; justify-content:space-between; gap:12px; }
        .git-dialog button.git-check-success { background:var(--success-color,#2e994e);
          color:#fff; border-color:var(--success-color,#2e994e); }
        .git-dialog button.git-check-error { background:var(--error-color,#c62828);
          color:#fff; border-color:var(--error-color,#c62828); }
        .git-check-feedback { margin:10px 0; padding:8px 10px; border-radius:8px;
          background:var(--secondary-background-color,#2b2b2b); }
        .git-check-feedback.success { border-left:4px solid var(--success-color,#2e994e); }
        .git-check-feedback.error { border-left:4px solid var(--error-color,#c62828); }
        .git-check-feedback.pending { border-left:4px solid var(--warning-color,#ce9332); }
        .git-dialog header h2 { font-size:19px; margin:0; }
        .git-dialog header button { min-width:40px; margin:0; }
        .git-dialog .dialog-actions { display:flex; flex-wrap:wrap; align-items:center; gap:6px; }
        .git-dialog .dialog-actions button { margin:0; }
        .git-dialog label { display:block; margin-top:12px; }
        .git-dialog .critical { color:var(--warning-color,#f0bb53); }
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
        </article>
        <article>
          <strong>Diagnoseexport</strong>
          <p class="note">Lokale JSON-Datei oder Export in dein selbst eingerichtetes privates GitHub-Repository.</p>
          <div class="git-main-actions">
            <button id="refresh" ${this._busy ? "disabled" : ""}>Status aktualisieren</button>
            <button id="json-download" ${this._downloadBusy || busy ||
              !this._diagnosticsExportReady ? "disabled" : ""}>JSON herunterladen</button>
            <button id="git-export" ${this._gitBusy || busy ||
              !this._gitAvailable || !this._gitConfigured ||
              this._centralExport.pending || !this._diagnosticsExportReady ? "disabled" : ""}>
              Git-Export
            </button>
            <button id="git-dialog-open">Export-Einstellungen</button>
          </div>
          <p class="note"><strong>Repository:</strong>
            ${this._centralExport.repository ?
              this._escapeProject(this._centralExport.repository) : "Nicht eingerichtet"}
            · <strong>Token:</strong>
            ${this._centralExport.token_suffix &&
              /^[A-Za-z0-9_-]{5}$/.test(this._centralExport.token_suffix) ?
              "•••••" + this._escapeProject(this._centralExport.token_suffix) :
              this._centralExport.server_token_available ? "Serverseitig vorhanden" : "Nicht eingerichtet"}
          </p>
          ${!this._diagnosticsExportReady ? `<p class="note">Für den Export zuerst einen
          CPU/RAM- oder Mehrkern-Diagnosetest erfolgreich abschließen.</p>` : ""}
          ${this._centralExport.pending ? `<p class="note">Ein Export wartet auf Wiederholung –
          unter „Export-Einstellungen“ fortsetzen.</p>` : ""}
          ${this._downloadStatus ? `<p class="note">${this._escapeProject(this._downloadStatus)}</p>` : ""}
          ${this._gitStatus ? `<p class="note">${this._escapeProject(this._gitStatus)}</p>` : ""}
          ${this._lastExport ? `<p><strong>Export-ID:</strong> ${this._escapeProject(this._lastExport.export_id)}
            · <strong>Zielpfad:</strong> ${this._escapeProject(this._lastExport.path)}</p>` : ""}
        </article>
        <article class="diagnostic-results">
          <strong>Messergebnisse und Auswertung</strong>
          <p class="note">Ausführliche Messwerte und Mehrkern-Ergebnisse erscheinen hier nach dem Test.</p>
          ${report}
          ${multicoreReport}
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
          <p class="note"><strong>Beim Start erkannte Prozessorkerne:</strong>
          ${Number.isInteger(this._cpuStatus.available_cores) ? this._cpuStatus.available_cores : "Nicht ermittelbar"}.
          <strong>Verwendete Kerne (Vorgabe):</strong> ${this._settings.max_worker_processes}.
          Die Zahl beschreibt sichtbare logische Kerne, keine garantierte CPU-Quote.</p>
          ${this._cpuStatus.warning?.code === "cpu_limit_reduced" ? `
            <div class="warning-cpu" role="alert">
              <strong>${this._cpuStatus.warning.previous_available !== null ? "Änderung der verfügbaren Prozessorkerne erkannt!" : "Weniger Prozessorkerne als eingestellt verfügbar!"}</strong>
              <p>Die Einstellung „Verwendete Kerne“ wurde von
              ${this._cpuStatus.warning.reduced_from} auf
              ${this._cpuStatus.warning.available_cores} reduziert.
              Bitte die DRA-Einstellungen kontrollieren.</p>
              <button id="cpu-warning-ack" ${this._cpuBusy ? "disabled" : ""}>Hinweis bestätigen</button>
            </div>` : ""}
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
          <p><strong>Privater GitHub-Lesezugang für V2</strong></p>
          <p class="note">Optional für private Projekt-Repositories. Nur einen
          eigenen GitHub-Token mit möglichst minimalem Leserecht auf die
          benötigten Repositories verwenden. Niemals V1-Zugangsdaten oder
          den separaten Git-Diagnoseexport-Zugang wiederverwenden.</p>
          <label>V2-Lesetoken (wird nicht wieder angezeigt)
            <input id="source-read-token" class="project-text" type="password"
            autocomplete="new-password" placeholder="Separater GitHub-Token" /></label>
          <button id="git-read-save" ${this._gitReadBusy ? "disabled" : ""}>Lesezugang speichern</button>
          <button id="git-read-clear" ${!this._gitReadConfigured || this._gitReadBusy ? "disabled" : ""}>Lesezugang entfernen</button>
          <p class="note">V2-Lesezugang: ${this._gitReadConfigured ? "eingerichtet" : "nicht eingerichtet"}.
          ${this._escapeProject(this._gitReadMessage)}</p>
          <p><strong>GitHub-Quellprüfung (nur lesend)</strong></p>
          <label>Quellzweig (optional; leer = Standardzweig)
            <input id="source-ref" class="project-text" placeholder="deploy/dev" autocomplete="off" /></label>
          <p class="note">Über „Git-Quelle prüfen“ beim jeweiligen Projekt wird die
          öffentliche GitHub-Quelle geprüft. Keine V1-Zugangsdaten, keine Installation.
          Private Repositories benötigen den separat eingerichteten V2-Lesezugang.</p>
          <p class="note">${this._escapeProject(this._sourceMessage)}</p>
          ${sourceReport ? `<div class="source-report"><strong>Prüfung: ${this._escapeProject(sourceReport.repository)}</strong>
            <p>Quellzweig: ${this._escapeProject(sourceReport.source_ref)}
            · Commit: ${this._escapeProject(sourceReport.source_commit?.slice(0,12))}</p>
            <p>Hinzugefügt: ${sourceReport.add.length} · Geändert: ${sourceReport.change.length}
            · Zu entfernen: ${sourceReport.remove.length} · Unverändert: ${sourceReport.unchanged_count}</p>
            <p><strong>Hinzugefügt</strong></p><ul>${sourceList(sourceReport.add)}</ul>
            <p><strong>Geändert</strong></p><ul>${sourceList(sourceReport.change)}</ul>
            <p><strong>Bei einer späteren Installation zu entfernen</strong></p><ul>${sourceList(sourceReport.remove)}</ul>
            <p class="note">Nur Vorschau – Installation gesperrt. Projektübernahme
            und unabhängige Sicherung müssen vor jedem Schreibauftrag geprüft werden.</p></div>` : ""}
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

        ${this._gitDialogOpen ? `
          <div class="git-dialog-backdrop">
            <section class="git-dialog" id="git-export-dialog"
                     role="dialog" aria-modal="true" aria-labelledby="git-dialog-title">
              <header>
                <h2 id="git-dialog-title">Git-Export-Einstellungen</h2>
                <button id="git-dialog-close" aria-label="Schließen"
                        ${this._archiveBusy || this._gitBusy ? "disabled" : ""}>✕</button>
              </header>
              <p class="note">Privates GitHub-Repository und eigenen Fine-grained-Token
              mit Contents: Lesen und Schreiben sowie Metadata: Lesen einrichten.
              Es gibt kein Standardrepository.</p>
              <label for="git-dialog-repo">Repository (Eigentümer/Repository)</label>
              <input id="git-dialog-repo" class="project-text" type="text"
                     placeholder="Eigentümer/Privates-Repository" autocomplete="off"
                     value="${this._escapeProject(this._centralExport.repository || "")}"
                     ${this._archiveBusy || this._centralExport.pending ? "readonly" : ""} />
              <label for="git-dialog-token">GitHub-Token
                ${this._centralExport.configured ? "– bereits gespeichert, für erneute Prüfung nicht nötig" :
                  "(wird nach dem Speichern nicht mehr angezeigt)"}</label>
              <input id="git-dialog-token" class="git-token" type="password"
                     autocomplete="off" spellcheck="false"
                     placeholder="${this._centralExport.configured ? "Nur bei Tokenänderung eingeben" : "Fine-grained GitHub-Token"}"
                     ${this._archiveBusy ? "disabled" : ""} />
              <p class="note">Der Schlüssel wird nur zur Einrichtung an Home Assistant
              übertragen, dort getrennt geschützt gespeichert und nicht an
              die Oberfläche zurückgesendet. Nutze eine verschlüsselte HA-Verbindung.</p>
              <div class="dialog-actions">
                <button id="git-dialog-save"
                        class="${["success", "stored"].includes(this._archiveCheckState) ? "git-check-success" :
                          this._archiveCheckState === "error" ? "git-check-error" : ""}"
                        ${this._archiveBusy || this._gitBusy ? "disabled" : ""}>
                  ${this._archiveCheckState === "success" ? "✓ Zugang geprüft" :
                    this._archiveCheckState === "stored" ? "✓ Gespeichert · prüfen" :
                    this._archiveCheckState === "error" ? "✕ Prüfung fehlgeschlagen" :
                    this._archiveBusy ? "Prüfung läuft …" : "Speichern & prüfen"}
                </button>
                <button id="git-dialog-clear"
                        ${this._archiveBusy || this._gitBusy || this._centralExport.pending ||
                          !this._centralExport.repository_configured ? "disabled" : ""}>
                  Zugang entfernen
                </button>
              </div>
              <p class="note"><strong>Gespeichertes Repository:</strong>
                ${this._centralExport.repository ? this._escapeProject(this._centralExport.repository) : "Nicht eingerichtet"}.
                <strong>Token-Endung:</strong>
                ${this._centralExport.token_suffix && /^[A-Za-z0-9_-]{5}$/.test(this._centralExport.token_suffix) ?
                  "•••••" + this._escapeProject(this._centralExport.token_suffix) :
                  this._centralExport.server_token_available ? "Serverseitig eingerichtet" : "Nicht eingerichtet"}.
              </p>
              <p class="git-check-feedback ${["success", "stored"].includes(this._archiveCheckState) ? "success" :
                 this._archiveCheckState === "error" ? "error" :
                 this._archiveBusy ? "pending" : ""}" role="status">
                ${this._escapeProject(this._archiveMessage ||
                 (this._centralExport.configured ?
                   "Zugang dauerhaft auf Home Assistant gespeichert. Erneut prüfen ohne Token-Eingabe möglich." :
                   "Noch kein GitHub-Zugang eingerichtet."))}
              </p>
              <div class="dialog-actions">
                <button id="git-retry" ${this._gitBusy || !this._centralExport.pending ||
                  !this._gitConfigured || !this._gitAvailable ? "disabled" : ""}>
                  Übertragung wiederholen
                </button>
                <button id="git-dialog-dismiss" ${this._archiveBusy || this._gitBusy ? "disabled" : ""}>
                  Schließen
                </button>
              </div>
              ${this._centralExport.pending ? `<p class="critical">Ein Export wartet auf Wiederholung.
              Das Ziel darf nicht gewechselt werden; der Token kann für einen erneuten Versuch aktualisiert werden.</p>` : ""}
              <p class="note">${this._escapeProject(this._gitStatus)}</p>
              ${this._lastExport ? `<p><strong>Export-ID:</strong> ${this._escapeProject(this._lastExport.export_id)}
              <strong>Zielpfad:</strong> ${this._escapeProject(this._lastExport.path)}</p>
              <a class="git-link" href="${this._lastExport.file_url}" target="_blank"
                 rel="noopener noreferrer">Privaten Export öffnen</a>` : ""}
            </section>
          </div>` : ""}
        <p class="note">Während eines laufenden Tests wird der Status etwa alle 1,5 Sekunden aktualisiert. Im Leerlauf erfolgt keine regelmäßige Abfrage. Nach einem Home-Assistant-Neustart bleiben abgeschlossene Aufträge im begrenzten Verlauf abrufbar. Vorher laufende Testaufträge erscheinen als unterbrochen und werden nicht neu gestartet.</p>
      </main>
    `;
    s.querySelector("#start")?.addEventListener("click", () => this._start());
    s.querySelector("#measure")?.addEventListener("click", () => this._measure());
    s.querySelector("#multicore")?.addEventListener("click", () => this._runSequence("multicore"));
    s.querySelector("#all")?.addEventListener("click", () => this._runSequence("full"));
    s.querySelector("#refresh")?.addEventListener("click", () => this._refresh());
    s.querySelector("#json-download")?.addEventListener("click", () => this._downloadJSON());
    s.querySelector("#git-dialog-open")?.addEventListener("click", () => this._openGitDialog());
    s.querySelector("#git-export")?.addEventListener("click", () => this._exportGit(false));
    s.querySelector("#git-dialog-close")?.addEventListener("click", () => this._closeGitDialog());
    s.querySelector("#git-dialog-dismiss")?.addEventListener("click", () => this._closeGitDialog());
    s.querySelector("#git-dialog-save")?.addEventListener("click", () => this._configureArchiveDialog());
    s.querySelector("#git-dialog-clear")?.addEventListener("click", () => this._clearArchiveDialog());
    s.querySelector("#git-retry")?.addEventListener("click", () => this._exportGit(true));
    s.querySelector("#settings-save")?.addEventListener("click", () => this._saveSettings());
    s.querySelector("#cpu-warning-ack")?.addEventListener("click", () => this._ackCpuWarning());
    s.querySelector("#batch-preview")?.addEventListener("click", () => this._previewBatch());
    s.querySelectorAll(".batch-choice")?.forEach(input => input.addEventListener("change", () => {
      this._batchSelection = [...s.querySelectorAll(".batch-choice")].filter(x => x.checked).map(x => x.dataset.repo);
      this._batchPreview = null;
      this._batchMessage = "Auswahl geändert – Vorschau erneut prüfen.";
    }));
    s.querySelectorAll(".preselect-toggle")?.forEach(button => button.addEventListener("click", () => this._togglePreselect(button)));
    s.querySelectorAll(".source-check")?.forEach(button => button.addEventListener("click", () => this._sourceCheck(button)));
    s.querySelector("#git-read-save")?.addEventListener("click", () => this._configureGitRead(false));
    s.querySelector("#git-read-clear")?.addEventListener("click", () => this._configureGitRead(true));
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
    if (this._gitDialogOpen) {
      const repoInput = s.querySelector("#git-dialog-repo");
      const tokenInput = s.querySelector("#git-dialog-token");
      if (repoInput && typeof unsentRepository === "string") repoInput.value = unsentRepository;
      if (tokenInput && unsentToken) tokenInput.value = unsentToken;
      s.querySelector("#git-export-dialog")?.addEventListener("keydown", event => {
        if (event.key === "Escape") this._closeGitDialog();
      });
    }
    this._syncCountdownTimer();
  }
}
if (!customElements.get("dra-v2-dev-lab-panel")) {
  customElements.define("dra-v2-dev-lab-panel", DRAV2DevLabPanel);
}

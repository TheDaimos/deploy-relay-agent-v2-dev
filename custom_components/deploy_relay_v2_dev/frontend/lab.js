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
    this._expandedSections = new Set();
    this._view = "main";
    this._selectedMainRepo = null;
    this._mainSourceRef = "";
    this._settingsMessage = "";
    this._cpuStatus = {available_cores:null,warning:null};
    this._cpuBusy = false;
    this._batchSelection = null;
    this._batchDialogOpen = false;
    this._batchPreview = null;
    this._batchBusy = false;
    this._batchMessage = "";
    this._projectBusy = false;
    this._projectSettingsRepo = null;
    this._projectDeleteConfirm = false;
    this._projectDialogOpen = false;
    this._projectSaved = new Map();
    this._backupDialogOpen = false;
    this._projectMessage = "";
    this._sourceBusy = false;
    this._sourceRepository = null;
    this._sourceMessage = "";
    this._sourcePreview = null;
    this._sourceChecks = new Map();
    this._connectionBusy = false;
    this._checkAllBusy = false;
    this._checkAllProgress = "";
    this._highlightMovedRepo = null;
    this._scrollToMovedProject = false;
    this._gitReadConfigured = false;
    this._gitReadBusy = false;
    this._gitReadMessage = "";
    this._v1Candidates = null;
    this._importDialogOpen = false;
    this._importSelection = [];
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
    if (!this._hass || this._projectBusy || this._checkAllBusy) return;
    this._projectBusy = true;
    this._projectMessage = "Projektverwaltung wird aktualisiert …";
    this._render();
    try {
      const result = await this._hass.callWS({
        type: "deploy_relay_v2_dev/projects/" + route, ...values,
      });
      if (route === "v1_preview") {
        this._v1Candidates = Array.isArray(result.candidates) ? result.candidates : [];
        this._importSelection = [];
        this._importDialogOpen = true;
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
        this._importDialogOpen = false;
        this._importSelection = [];
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
    const ref = this._view === "main" ? this._mainSourceRef.trim() : (this.shadowRoot?.querySelector("#source-ref")?.value?.trim() || "");
    this._sourceRepository = repository;
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

  async _checkProjectConnection(repository, fromBulk = false) {
    if (!this._hass || this._connectionBusy || this._projectBusy ||
        this._sourceBusy || (this._checkAllBusy && !fromBulk)) return;
    const record = this._projects.find(p=>p.repository===repository);
    if (!record) return;
    const entered = this.shadowRoot?.querySelector("#manage-repository");
    if (this._projectSettingsRepo === repository && entered &&
        entered.value.trim().toLowerCase() !== repository.toLowerCase()) {
      this._sourceChecks.set(repository, {status:"failure", message:"Geänderte Repositoryadresse zuerst speichern."});
      this._render();
      return;
    }
    this._connectionBusy = true;
    this._sourceChecks.set(repository, {status:"checking",message:"Verbindung wird geprüft …"});
    this._render();
    try {
      const report = await this._hass.callWS({
        type:"deploy_relay_v2_dev/projects/connection_check",repository
      });
      if (!report || report.repository?.toLowerCase() !== repository.toLowerCase()) {
        throw new Error("invalid response");
      }
      if (report.connected === true) {
        const visibility = report.private ? "Privates Repository" : "Öffentliches Repository";
        const auth = report.authenticated ? "mit Token" : "ohne Token";
        const rights = report.advertised_push === true ? " · GitHub meldet Schreibberechtigung (nicht getestet)" :
          report.advertised_push === false ? " · GitHub meldet nur Lesezugriff" : "";
        this._sourceChecks.set(repository, {status:"success",
          message:"Verbindung erfolgreich · " + visibility + " · " + auth + rights});
      } else {
        this._sourceChecks.set(repository, {status:"failure",
          message:"Verbindung fehlgeschlagen · " + (report.reason || "Repository oder Token prüfen.")});
      }
    } catch (_error) {
      this._sourceChecks.set(repository, {status:"failure",
        message:"Verbindung fehlgeschlagen · Zugriff oder GitHub-Erreichbarkeit prüfen."});
    } finally {
      this._connectionBusy = false;
      if (this.isConnected) this._render();
    }
  }
  async _checkAllProjectConnections() {
    if (!this._hass || this._checkAllBusy || this._connectionBusy ||
        this._projectBusy || this._sourceBusy || this._gitReadBusy) return;
    const repositories = this._projects.map(p => p.repository);
    if (!repositories.length) return;
    this._checkAllBusy = true;
    this._checkAllProgress = `Verbindungsprüfung: 0 von ${repositories.length} Projekten geprüft.`;
    this._render();
    let checked = 0;
    let online = 0;
    let offline = 0;
    try {
      for (const repository of repositories) {
        await this._checkProjectConnection(repository, true);
        const status = this._sourceChecks.get(repository)?.status;
        if (status === "success") online++;
        else offline++;
        checked++;
        this._checkAllProgress = `Verbindungsprüfung: ${checked} von ${repositories.length} · ${online} online, ${offline} offline.`;
        if (this.isConnected) this._render();
      }
      this._checkAllProgress = `Prüfung abgeschlossen: ${online} online, ${offline} offline.`;
    } finally {
      this._checkAllBusy = false;
      if (this.isConnected) this._render();
    }
  }
  _openProjectDialog() {
    this._projectDialogOpen = true;
    this._render();
  }
  _closeProjectDialog() {
    if (this._projectBusy || this._sourceBusy || this._gitReadBusy || this._checkAllBusy) return;
    this._projectDialogOpen = false;
    this._highlightMovedRepo = null;
    this._render();
  }
  _selectProjectRow(repo) {
    if (!this._projectDialogOpen ||
        !this._projects.some(p => p.repository === repo)) return;
    if (this._highlightMovedRepo === repo) return;
    this._highlightMovedRepo = repo;
    // Free selection is visual only: it neither reorders nor edits the project.
    this._scrollToMovedProject = false;
    this._render();
  }
  _openProjectSettings(repo) {
    if (this._projectBusy || this._checkAllBusy) return;
    this._projectSettingsRepo = repo;
    this._projectDeleteConfirm = false;
    this._render();
  }
  _closeProjectSettings() {
    this._projectSettingsRepo = null;
    this._projectDeleteConfirm = false;
    this._render();
  }
  async _manageProject(action, extras = {}) {
    if (!this._hass || this._projectBusy || this._checkAllBusy || !this._projectSettingsRepo && action !== "move") return;
    this._projectBusy = true;
    this._projectMessage = "Projektverwaltung wird gespeichert …";
    const repo = extras.repository || this._projectSettingsRepo;
    try {
      const result = await this._hass.callWS({
        type:"deploy_relay_v2_dev/projects/manage", action, repository:repo, ...extras
      });
      this._projects = result.projects;
      if (action === "move") {
        this._highlightMovedRepo = repo;
        this._scrollToMovedProject = true;
        this._projectMessage = "Reihenfolge gespeichert. Verschobenes Projekt hervorgehoben.";
      } else {
        this._sourceChecks.delete(repo);
        if (extras.new_repository) this._sourceChecks.delete(extras.new_repository);
        if (action === "remove" || action === "configure") this._highlightMovedRepo = null;
        this._projectMessage = "Projektverwaltung gespeichert.";
      }
      if (action !== "move") this._projectSettingsRepo = null;
      this._projectDeleteConfirm = false;
    } catch (_error) {
      this._projectMessage = "Projektaktion fehlgeschlagen. Keine Änderung gespeichert.";
    } finally {
      this._projectBusy = false;
      if (this.isConnected) this._render();
    }
  }
  async _saveProjectToken() {
    if (this._checkAllBusy) return;
    const token = this.shadowRoot.querySelector("#manage-token")?.value || "";
    if (!token || !this._projectSettingsRepo || !this._hass || this._projectBusy) return;
    this._projectBusy = true;
    try {
      const result = await this._hass.callWS({type:"deploy_relay_v2_dev/projects/token",
        repository:this._projectSettingsRepo,token});
      this._projects = result.projects;
      this._sourceChecks.delete(this._projectSettingsRepo);
      this._projectMessage = "Projekttoken gespeichert. Verbindung erneut prüfen.";
    } catch (_error) {
      this._projectMessage = "Projekttoken konnte nicht gespeichert werden.";
    } finally {
      this._projectBusy = false;
      this._render();
    }
  }
  _saveProjectSettings() {
    const s = this.shadowRoot;
    const previous = this._projectSettingsRepo;
    const repository = s.querySelector("#manage-repository")?.value.trim() || "";
    const name = s.querySelector("#manage-name")?.value.trim() || "";
    const note = s.querySelector("#manage-note")?.value || "";
    const active = s.querySelector("#manage-active")?.checked === true;
    const access_mode = s.querySelector("#manage-access-mode")?.value || "read_only";
    return this._manageProject("configure", {repository:previous, new_repository:repository, name, note, active, access_mode});
  }
  _cancelProjectImport() {
    if (this._projectBusy) return;
    this._importDialogOpen = false;
    this._v1Candidates = null;
    this._importSelection = [];
    this._projectMessage = "";
    this._render();
  }
  _submitProjectImport() {
    if (!this._importSelection.length) return;
    return this._projectAction("import_v1", {repositories:[...this._importSelection]});
  }
  _addProject() {
    const repo = this.shadowRoot?.querySelector("#project-repo")?.value || "";
    const name = this.shadowRoot?.querySelector("#project-name")?.value || "";
    return this._projectAction("add", { repository: repo, name });
  }

  _openBackupDialog() {
    this._backupDialogOpen = true;
    this._render();
  }
  _closeBackupDialog() {
    if (this._projectBusy) return;
    this._backupDialogOpen = false;
    this._render();
  }
  _retention(button) {
    const repo = button?.dataset?.repo;
    const input = button?.closest(".backup-entry")?.querySelector("input.retention");
    const n = Number(input?.value);
    if (!Number.isInteger(n) || n < 3 || n > 100) {
      this._projectMessage = "Sicherungen: erlaubt sind 3 bis 100 je Projekt.";
      this._render();
      return;
    }
    this._projectSaved.delete(repo);
    return this._projectAction("retention", {repository:repo, backup_retention:n});
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

  _openBatchDialog() {
    if (this._batchBusy) return;
    this._batchSelection = this._projects.filter(p => p.batch_preselect !== false).map(p => p.repository);
    this._batchMessage = "";
    this._batchDialogOpen = true;
    this._render();
  }
  _cancelBatchDialog() {
    if (this._batchBusy) return;
    this._batchDialogOpen = false;
    this._batchSelection = null;
    this._batchMessage = "";
    this._render();
  }
  async _saveBatchDialog() {
    if (!this._hass || this._batchBusy || !this._batchDialogOpen) return;
    const chosen = new Set(this._batchSelection || []);
    this._batchBusy = true;
    this._batchMessage = "Auswahl wird gespeichert …";
    this._render();
    try {
      for (const project of [...this._projects]) {
        const enabled = chosen.has(project.repository);
        if (project.batch_preselect === enabled) continue;
        const result = await this._hass.callWS({
          type:"deploy_relay_v2_dev/projects/preselect", repository:project.repository, enabled,
        });
        if (!Array.isArray(result.projects)) throw new Error("not confirmed");
        this._projects = result.projects;
        if (!this._projects.some(p => p.repository === project.repository && p.batch_preselect === enabled))
          throw new Error("not confirmed");
      }
      this._batchDialogOpen = false;
      this._batchSelection = null;
      this._batchMessage = "Sammelupdate-Auswahl gespeichert.";
    } catch (_error) {
      this._batchMessage = "Speicherung nicht vollständig. Bitte Auswahl prüfen und erneut speichern.";
    } finally {
      this._batchBusy = false;
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
    const settingsDraft = this._projectSettingsRepo && s?.querySelector("#manage-repository") ?
      { repository:s.querySelector("#manage-repository").value,
        name:s.querySelector("#manage-name").value,
        note:s.querySelector("#manage-note").value,
        active:s.querySelector("#manage-active").checked,
        accessMode:s.querySelector("#manage-access-mode")?.value || "read_only",
        token:s.querySelector("#manage-token")?.value || "" } : null;
    const unsentToken = this._gitDialogOpen ?
      s?.querySelector("#git-dialog-token")?.value || "" : "";
    const previousRepo = this._gitDialogOpen ?
      s?.querySelector("#git-dialog-repo")?.value : null;
    // Unmounted inputs return undefined. Assigning that to an HTML input.value
    // turns it into the literal text "undefined" (seen on Android/desktop).
    const unsentRepository = typeof previousRepo === "string" ? previousRepo : null;
    const activeMainProjects = this._projects.filter(p => p.active !== false);
    const mainProject = activeMainProjects.find(p => p.repository === this._selectedMainRepo) || activeMainProjects[0] || null;
    // Consistent, resolution-independent 24x24 vector icons: never emoji or icon fonts.
    const iconSvg = (body, size=22) => `<svg class="project-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" focusable="false" aria-hidden="true">${body}</svg>`;
    const gearIcon = iconSvg('<path d="M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"/><circle cx="12" cy="12" r="3"/>');
    const upIcon = iconSvg('<path d="M12 19V5"/><path d="m5 12 7-7 7 7"/>');
    const downIcon = iconSvg('<path d="M12 5v14"/><path d="m5 12 7 7 7-7"/>');
    const pendingIcon = iconSvg('<circle cx="12" cy="12" r="9"/><path d="M9.8 9a2.5 2.5 0 0 1 4.4 1.6c0 1.7-2.2 2.1-2.2 3.4"/><path d="M12 17h.01"/>', 18);
    const onlineIcon = iconSvg('<circle cx="12" cy="12" r="10"/><path d="m16 9-5.5 5.5L8 12"/>', 18);
    const failureIcon = iconSvg('<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/>', 18);
    const plusIcon = iconSvg('<circle cx="12" cy="12" r="10"/><path d="M8 12h8"/><path d="M12 8v8"/>', 20);
    const importIcon = iconSvg('<path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 17v3h14v-3"/>', 20);
    const checkAllIcon = iconSvg('<circle cx="12" cy="12" r="9"/><path d="M8 12l2.5 2.5L16 9"/><path d="M3 4h4M4 3v4"/>', 20);
    const backupIcon = iconSvg('<rect x="2" y="3" width="20" height="5" rx="1"/><path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8"/><path d="M10 12h4"/>', 20);
    const closeIcon = iconSvg('<path d="M18 6 6 18M6 6l12 12"/>', 20);
    // Unique gradient IDs per project prevent SVG-definition collisions.
    const metalSvg = (svg, kind, index) => {
      const id = `dra-metal-${kind}-${index}`;
      const gradient = `<defs><linearGradient id="${id}" x1="0%" y1="0%" x2="85%" y2="100%">
        <stop offset="0%" stop-color="#ffffff"/>
        <stop offset="20%" stop-color="#d8f4ff"/>
        <stop offset="44%" stop-color="#85a6b6"/>
        <stop offset="57%" stop-color="#e0f6ff"/>
        <stop offset="77%" stop-color="#668a9b"/>
        <stop offset="100%" stop-color="#e0ecf2"/>
      </linearGradient></defs>`;
      return svg.replace('stroke="currentColor"', `stroke="url(#${id})"`)
        .replace('</svg>', gradient + '</svg>');
    };
    const projectRows = this._projects.map((p,i) => {
      const test = this._sourceChecks.get(p.repository);
      const state = test?.status || "unverified";
      const label = state === "success" ? "Online" : state === "failure" ? "Offline" :
        state === "checking" ? "Prüft …" : "Prüfen";
      const icon = state === "success" ? onlineIcon : state === "failure" ? failureIcon : pendingIcon;
      const selected = this._highlightMovedRepo?.toLowerCase() === p.repository.toLowerCase();
      return `<tr class="project-row connection-${state}${selected ? " recently-moved" : ""}" data-project-repo="${this._escapeProject(p.repository)}" tabindex="0" aria-current="${selected ? "true" : "false"}" aria-label="Projekt ${this._escapeProject(p.name)} markieren"><td>${i+1}</td>
        <td class="${p.active === false ? "project-entry-inactive" : ""}"><strong>${this._escapeProject(p.name)}</strong><div class="note">${this._escapeProject(p.repository)}</div>
          ${p.active === false ? '<span class="project-inactive-label" aria-label="Projekt inaktiv">Inaktiv</span>' : ""}</td>
        <td><button class="source-check ${state}" data-repo="${this._escapeProject(p.repository)}"
          ${this._connectionBusy || this._checkAllBusy || this._projectBusy ? "disabled" : ""} aria-label="GitHub-Verbindung für ${this._escapeProject(p.name)} prüfen" title="Verbindung prüfen">${icon}<span class="project-status-label">${label}</span></button></td>
        <td><button class="project-settings-open project-metal-button" data-repo="${this._escapeProject(p.repository)}" ${this._checkAllBusy ? "disabled" : ""} aria-label="Einstellungen für ${this._escapeProject(p.name)}" title="Projekteinstellungen">${metalSvg(gearIcon,"settings",i)}</button></td>
        <td><button class="project-move project-metal-button" data-repo="${this._escapeProject(p.repository)}" data-direction="-1" ${i===0 || this._projectBusy || this._checkAllBusy ? "disabled" : ""} aria-label="${this._escapeProject(p.name)} nach oben verschieben" title="Nach oben">${metalSvg(upIcon,"up",i)}</button>
        <button class="project-move project-metal-button" data-repo="${this._escapeProject(p.repository)}" data-direction="1" ${i===this._projects.length-1 || this._projectBusy || this._checkAllBusy ? "disabled" : ""} aria-label="${this._escapeProject(p.name)} nach unten verschieben" title="Nach unten">${metalSvg(downIcon,"down",i)}</button></td></tr>`;
    }).join("");
    const managed = this._projects.find(p => p.repository === this._projectSettingsRepo);
    const batchRows = this._projects.map(p => {
      const checked = this._batchSelection === null ? p.batch_preselect !== false : this._batchSelection.includes(p.repository);
      return `<label class="batch-line"><input type="checkbox" class="batch-choice" data-repo="${this._escapeProject(p.repository)}" ${checked && p.active !== false ? "checked" : ""} ${p.active === false ? "disabled" : ""}/> ${this._escapeProject(p.name)} ${p.active === false ? "(inaktiv)" : ""}</label>`;
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
    const importRows = Array.isArray(this._v1Candidates) ? this._v1Candidates.map(p => `<label class="batch-line"><input type="checkbox" class="import-choice" data-repo="${this._escapeProject(p.repository)}" ${this._importSelection.includes(p.repository) ? "checked" : ""} /> <strong>${this._escapeProject(p.name)}</strong><span class="note"> · ${this._escapeProject(p.repository)}</span></label>`).join("") : "";
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
    const previousProjectScroll = s.querySelector("#project-management-scroll")?.scrollTop ?? 0;
    s.innerHTML = `
      <style>
        :host { display:block; min-height:100%; color:var(--primary-text-color, #f2f2f2); background:var(--primary-background-color, #111); font-family:var(--paper-font-body1_-_font-family, sans-serif); }
        main { margin:auto; width:100%; max-width:none; box-sizing:border-box; padding:24px clamp(12px,2.5vw,36px) 56px; }
        [hidden] {display:none !important;}
        .dra-head {display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;border-bottom:1px solid var(--divider-color,#555);padding-bottom:12px}
        .dra-head strong {font-size:20px}.dra-head button {margin:2px}
        .dra-actions {display:flex;gap:8px;align-items:center;flex-wrap:wrap}
        .dra-lock {border:1px solid #b08022;color:#f0ba40;border-radius:15px;padding:6px 10px}
        .dra-projectbar {display:flex;gap:12px;align-items:end;flex-wrap:wrap}
        .dra-projectbar label {flex:1;min-width:210px}
        .dra-projectbar select {display:block;width:100%;min-height:44px;padding:8px;border-radius:8px;background:var(--primary-background-color,#111);color:inherit;border:1px solid var(--divider-color,#555)}
        .dra-main-grid {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
        .dra-main-grid article {margin-top:12px}
        .dra-steps {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}
        .dra-steps button {margin:0;background:#233943;border:1px solid #396a96;padding:10px 4px}
        .dra-steps button.current {background:#14516a;border-color:#14a8dc;font-weight:700}
        .dra-warning {border:1px solid #987323;background:rgba(160,110,10,.12);border-radius:10px;padding:14px;margin-top:14px}
        @media(max-width:760px){.dra-main-grid{grid-template-columns:1fr}.dra-steps{grid-template-columns:repeat(2,minmax(0,1fr))}}
        h1 { font-size:24px; margin:0 0 12px; }
        article { background:var(--card-background-color,#202020); border:1px solid var(--divider-color,#555); border-radius:14px; padding:20px; margin-top:18px; }
        p { line-height:1.5; }
        .note { color:var(--secondary-text-color,#bbb); }
        .safe { font-weight:bold; color:var(--success-color,#68ba8c); }
        button { background:var(--primary-color,#396a96); color:#fff; border:0; border-radius:8px; padding:12px 16px; margin-right:8px; margin-top:10px; font:inherit; cursor:pointer; }
        button:disabled { opacity:.5; cursor:default; }
        button { position:relative; touch-action:manipulation; transition:transform .12s ease,filter .12s ease,box-shadow .12s ease; }
        button:not(:disabled):hover { filter:brightness(1.12); box-shadow:0 2px 7px rgba(0,0,0,.24); }
        button:not(:disabled):active { transform:translateY(2px) scale(.975); filter:brightness(.78); box-shadow:inset 0 2px 7px rgba(0,0,0,.42); }
        button:focus-visible { outline:3px solid var(--accent-color,#f1c45e); outline-offset:3px; }
        button:disabled { transform:none; box-shadow:none; }
        @media (prefers-reduced-motion:reduce) { button { transition:none; } }
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
        /* Fixed modal header; only the body below it scrolls. */
        .project-management-dialog {
          width:min(100%,1080px); display:flex; flex-direction:column;
          overflow:hidden; max-height:92dvh;
        }
        .project-management-dialog .project-management-scroll {
          min-height:0; flex:1 1 auto; overflow-y:auto; overflow-x:hidden;
          overscroll-behavior:contain; padding:12px 4px 0 0;
          scrollbar-gutter:stable;
        }
        .project-management-dialog .project-management-table { table-layout:auto; }
        .project-management-dialog .project-management-table td:first-child { min-width:0; width:42px; }
        .project-management-dialog .project-management-table td:nth-child(2) { overflow-wrap:anywhere; }
        .project-management-dialog header {
          position:relative; top:auto; z-index:1; flex:0 0 auto;
          background:var(--card-background-color,#222); padding-bottom:12px;
          border-bottom:1px solid var(--divider-color,#555);
        }
        @media (max-width:760px) {
          .project-management-dialog { width:100%; max-height:94dvh; padding:14px; }
          .project-management-dialog header h2 { font-size:17px; }
          .project-management-dialog .project-management-table td:first-child { width:auto; }
          .project-management-dialog .project-actions {gap:6px;}
          .project-management-dialog .project-actions button {margin:0;}
        }
        .project-management-dialog .project-management-footer { justify-content:flex-end; margin-top:18px; }
        .project-management-dialog .project-management-footer button { min-width:130px; }
        .git-dialog button.git-check-success { background:var(--success-color,#2e994e);
          color:#fff; border-color:var(--success-color,#2e994e); }
        .git-dialog button.git-check-error { background:var(--error-color,#c62828);
          color:#fff; border-color:var(--error-color,#c62828); }
        .git-saved-details p { margin:5px 0; overflow-wrap:anywhere; }
        .git-check-feedback { margin:10px 0; padding:8px 10px; border-radius:8px;
          background:var(--secondary-background-color,#2b2b2b); }
        .git-check-feedback.success { border-left:4px solid var(--success-color,#2e994e); }
        .git-check-feedback.error { border-left:4px solid var(--error-color,#c62828); }
        .git-check-feedback.pending { border-left:4px solid var(--warning-color,#ce9332); }
        .git-dialog header h2 { font-size:19px; margin:0; }
        .git-dialog header button { min-width:40px; margin:0; }
        .git-dialog .dialog-actions { display:flex; flex-wrap:wrap; align-items:center; gap:6px; }
        .git-dialog .dialog-actions button { margin:0; }
        /* Project dialog: keep all primary actions in one clearly aligned row. */
        .git-dialog .manage-dialog-actions {
          display:grid; grid-template-columns:repeat(2,minmax(0,1fr));
          align-items:stretch; gap:6px; width:100%; margin-top:12px;
        }
        .git-dialog .manage-dialog-actions.has-remove {
          grid-template-columns:minmax(0,1.5fr) repeat(2,minmax(0,1fr));
        }
        .git-dialog .manage-dialog-actions button {
          box-sizing:border-box; min-width:0; width:100%; margin:0;
          padding:11px 5px; font-size:clamp(10px,2.8vw,14px);
          line-height:1.2; white-space:nowrap; overflow:visible;
        }
        @media (max-width:760px) {
          /* Status information above; both top-right actions side by side. */
          .dra-head { display:block; }
          .dra-head > div:first-child { margin-bottom:12px; }
          .dra-actions {
            display:grid; width:100%; min-width:0; gap:8px;
            grid-template-columns:minmax(0,.85fr) minmax(0,1.35fr);
            align-items:center;
          }
          .dra-actions .dra-lock {grid-column:1; justify-self:start; white-space:nowrap;}
          .dra-actions > .note {grid-column:2; justify-self:start; white-space:nowrap;}
          .dra-actions #dra-refresh {grid-column:1;}
          .dra-actions #dra-toggle {grid-column:2;}
          .dra-actions button {
            box-sizing:border-box; display:block; width:100%; min-width:0;
            margin:0; padding:11px 5px; font-size:clamp(11px,2.8vw,14px);
            line-height:1.2; white-space:nowrap; text-align:center;
          }
        }
        @media (max-width:360px) {
          .git-dialog {padding:14px;}
          .git-dialog .manage-dialog-actions {gap:4px;}
          .git-dialog .manage-dialog-actions button {padding:10px 3px;font-size:10px;}
          .dra-actions {gap:5px;}
          .dra-actions button {font-size:11px;padding:10px 3px;}
        }

        .git-dialog label { display:block; margin-top:12px; }
        .git-dialog .critical { color:var(--warning-color,#f0bb53); }
        .git-link { display:inline-block; padding:12px 0; color:var(--primary-color,#65b4d2); overflow-wrap:anywhere; }
        .countdown { font-size:19px; font-weight:700; font-variant-numeric:tabular-nums; }

         .source-inline { margin-top:12px; padding:10px; border:1px solid var(--divider-color,#555); border-left:3px solid var(--primary-color,#396a96); border-radius:8px; white-space:normal; overflow-wrap:anywhere; }
         .source-inline p { margin:5px 0; }
         .project-actions { display:flex; gap:8px; flex-wrap:wrap; margin-top:14px; }
         .project-management-table th,.project-management-table td { white-space:normal; vertical-align:middle; }
         .project-management-table .success { color:var(--success-color,#6c6); }
         .project-management-table .error { color:var(--error-color,#e55); }
         button.danger { background:var(--error-color,#b33); }
         #manage-note { display:block; box-sizing:border-box; width:100%; min-height:80px; background:var(--primary-background-color,#151515); color:inherit; border:1px solid var(--divider-color,#555); border-radius:8px; padding:8px; margin:5px 0; resize:vertical; }
         .project-management-table .source-check { margin:0; white-space:nowrap; }
         .project-management-table .source-check.success { background:#28743b; color:white; }
         .project-management-table .source-check.error { background:#a43838; color:white; }
         .project-management-table .project-move, .project-management-table .project-settings-open { min-width:38px; padding:8px; }
         /* Explicit connectivity statuses, no source-manifest failure mislabelled as offline. */
         .project-management-table .source-check {
           display:inline-flex; align-items:center; justify-content:center; gap:6px;
           min-width:132px; font-size:13px; font-weight:600; padding:9px 8px;
           color:#f5f7f9; border:1px solid transparent; border-radius:8px;
         }
         .project-management-table .source-check.unverified {
           background:#39434c; color:#fff; border-color:#65737e;
         }
         .project-management-table .source-check.checking {
           background:#455765; color:#fff; border-color:#7b92a3;
         }
         .project-management-table .source-check.success {
           background:#237640; color:#fff; border-color:#62bd7e;
         }
         .project-management-table .source-check.failure {
           background:#a3333b; color:#fff; border-color:#e77378;
         }
         .project-management-table .project-icon { display:block; flex:none; }
         .project-management-table .project-settings-open,
         .project-management-table .project-move {
           display:inline-flex; align-items:center; justify-content:center;
           min-width:38px; min-height:38px; padding:8px;
         }
         .project-management-table td:nth-child(5) {
           white-space:nowrap; min-width:90px;
         }
         /* Token suffix at left, declared access mode at far right on the same row. */
         .project-token-summary {
           display:flex; align-items:center; justify-content:space-between;
           width:100%; min-width:0; gap:12px; margin:10px 0 12px;
         }
         .project-token-info {flex:1 1 auto; min-width:0; overflow-wrap:anywhere;}
         .project-token-summary .safe strong {color:var(--success-color,#43d568);font-weight:800;}
         .project-token-access {
           display:flex; align-items:center; justify-content:flex-end;
           flex:0 0 auto; gap:7px; min-width:0;
         }
         .project-token-access label {margin:0; white-space:nowrap;font-size:13px;}
         .project-token-access select.project-text {
           box-sizing:border-box; flex:none; width:135px;
           min-height:36px; margin:0; padding:6px 8px; font-size:13px;
         }
         .project-access-help {font-size:12px;}
         @media (max-width:560px) {
           .project-token-summary {gap:8px;align-items:center;}
           .project-token-info {font-size:12px;line-height:1.4;}
           .project-token-access {flex-direction:column;align-items:flex-end;gap:3px;}
           .project-token-access label {font-size:12px;}
           .project-token-access select.project-text {width:126px;min-height:36px;}
         }
         @media (max-width:350px) {
           .project-token-summary {flex-wrap:wrap;}
           .project-token-access {margin-left:auto;}
         }
         .project-token-actions {display:flex; gap:8px; flex-wrap:wrap; margin-top:10px;}
         .project-token-actions button {margin:0; white-space:nowrap;}
         select.project-text {
           display:block; box-sizing:border-box; width:100%; min-height:42px;
           background:var(--primary-background-color,#151515); color:inherit;
           border:1px solid var(--divider-color,#555); border-radius:8px;
           padding:8px; margin:5px 0;
         }
         .connection-feedback { padding:10px 12px; border:1px solid; border-radius:8px; font-weight:600; overflow-wrap:anywhere; }
         .connection-feedback.success { color:#c3f5d0; border-color:#45b876; background:#143822; }
         .connection-feedback.failure { color:#ffd8d8; border-color:#df7272; background:#481e22; }
         .connection-feedback.checking { color:#fff; border-color:#8ba2b2; background:#324652; }

         .project-card td { vertical-align:top; }
         .project-card td:first-child { min-width:180px; white-space:normal; overflow-wrap:anywhere; }
         .project-card td button { margin:4px; white-space:nowrap; }
         @media (max-width:760px) {
           /* A project is one compact two-row card, not five vertically stacked table cells. */
           .project-card .table-wrap { overflow-x:visible; }
           .project-card table, .project-card tbody { display:block; width:100%; box-sizing:border-box; }
           .project-card thead { display:none; }
           .project-card tr {
             display:grid; width:100%; box-sizing:border-box;
             grid-template-columns:28px minmax(0,1fr) 42px 90px;
             grid-template-areas:"number project project project" "status status settings order";
             align-items:center; gap:9px 7px;
             border:1px solid var(--divider-color,#555);
             border-radius:10px; margin-bottom:9px; padding:10px;
           }
           .project-card td {
             display:block; width:auto; min-width:0 !important; box-sizing:border-box;
             border:0; padding:0; white-space:normal; overflow-wrap:anywhere;
           }
           .project-card td::before { content:none !important; display:none !important; }
           .project-card td:nth-child(1) {
             grid-area:number; text-align:center; font-weight:700;
             color:var(--secondary-text-color,#bbb);
           }
           .project-card td:nth-child(2) { grid-area:project; }
           .project-card td:nth-child(2) strong { display:block; }
           .project-card td:nth-child(2) .note { font-size:12px; overflow-wrap:anywhere; }
           .project-card td:nth-child(3) { grid-area:status; }
           .project-card td:nth-child(4) { grid-area:settings; }
           .project-card td:nth-child(5) {
             grid-area:order; display:flex; gap:4px; align-items:center;
           }
           .project-card td button {
             box-sizing:border-box; margin:0; min-height:38px;
             padding:8px 5px; white-space:nowrap; max-width:100%;
           }
           .project-card td:nth-child(3) button {
             display:block; width:100%; min-width:0; font-size:clamp(10px,2.9vw,13px);
           }
           .project-card td:nth-child(4) button { width:40px; }
           .project-card td:nth-child(5) button {
             flex:1 1 0; min-width:0; padding:8px 3px;
           }
           .project-management-table .source-check.note {
             background:var(--secondary-background-color,#414b53);
             border:1px solid var(--divider-color,#555); color:var(--primary-text-color,#fff);
           }
         }
         /* The entire card expresses Git reachability; the selection glow is independent. */
         .project-management-dialog.project-card .project-row {
           transition: background .25s ease, border-color .25s ease, box-shadow .25s ease;
         }
         .project-management-dialog.project-card .project-row.connection-unverified,
         .project-management-dialog.project-card .project-row.connection-checking {
           background:linear-gradient(125deg,rgba(60,76,92,.14),rgba(20,26,32,.04));
           box-shadow:inset 3px 0 0 rgba(126,149,171,.35);
         }
         .project-management-dialog.project-card .project-row.connection-success {
           background:linear-gradient(120deg,rgba(26,117,72,.23),rgba(19,71,55,.13) 54%,rgba(20,37,34,.05));
           box-shadow:inset 3px 0 0 #47b877, inset 0 0 28px rgba(26,146,84,.075);
         }
         .project-management-dialog.project-card .project-row.connection-failure {
           background:linear-gradient(120deg,rgba(154,47,63,.23),rgba(99,38,49,.13) 54%,rgba(38,25,30,.05));
           box-shadow:inset 3px 0 0 #df6876, inset 0 0 28px rgba(171,40,58,.075);
         }
         .project-management-dialog.project-card .project-row {cursor:pointer;}
         .project-management-dialog.project-card .project-row:focus-visible {
           outline:2px solid #f1c76d; outline-offset:2px;
         }
         .project-management-dialog.project-card .project-row.recently-moved {
           position:relative;
           border-color:#efc66a;
           outline:2px solid rgba(245,192,75,.7);
           outline-offset:1px;
           box-shadow:inset 4px 0 0 #f2c869, 0 0 0 3px rgba(238,179,55,.17),
             0 0 24px rgba(245,185,48,.21);
           animation:project-moved-glow .8s ease-out both;
         }
         @keyframes project-moved-glow {
           0% {filter:brightness(1.4);transform:scale(.992);}
           55% {filter:brightness(1.12);transform:scale(1.006);}
           100% {filter:brightness(1);transform:scale(1);}
         }
         @media (prefers-reduced-motion:reduce) {
           .project-management-dialog.project-card .project-row {transition:none;}
           .project-management-dialog.project-card .project-row.recently-moved {animation:none;}
         }
         .project-management-dialog .project-management-table .source-check {
           width:154px; max-width:100%; min-width:0; min-height:44px; height:44px;
           display:inline-flex; justify-content:center; align-items:center;
           padding:8px 6px; gap:7px; text-align:center; flex-wrap:nowrap;
           font-variant-numeric:tabular-nums;
         }
         .project-management-dialog .project-management-table .source-check .project-status-label {
           text-align:center; white-space:nowrap; line-height:1.15; font-weight:650;
         }
         @media (max-width:760px) {
           .project-management-dialog .project-management-table td:nth-child(3) button.source-check {
             width:154px; max-width:100%; min-width:0; height:44px;
             display:inline-flex; justify-content:center; align-items:center;
             padding:7px 5px; text-align:center;
           }
           .project-management-dialog.project-card .project-row.connection-success {
             border-color:rgba(71,184,119,.6);
           }
           .project-management-dialog.project-card .project-row.connection-failure {
             border-color:rgba(223,104,118,.6);
           }
         }
         /* DRA V2 icon system: resolution-independent vectors and light-touch surfaces. */
         .project-management-dialog .project-icon {display:block;flex:none;vector-effect:non-scaling-stroke;}
         .project-management-dialog .project-management-table .source-check {
           box-sizing:border-box; display:inline-flex; width:auto; max-width:100%;
           min-width:0; height:42px; min-height:42px; margin:0; padding:8px 12px;
           align-items:center; justify-content:flex-start; gap:7px;
           white-space:nowrap; text-align:left; font-size:12px; font-weight:600;
           border-radius:10px; box-shadow:none;
         }
         .project-management-dialog .project-management-table .source-check.unverified {
           background:#2b343b; color:#e3eaf0; border:1px solid #657783;
         }
         .project-management-dialog .project-management-table .source-check.checking {
           background:#31424e; color:#e7f3fa; border:1px solid #69889d;
         }
         .project-management-dialog .project-management-table .source-check.success {
           background:#174b2f; color:#dcffe8; border:1px solid #419765;
         }
         .project-management-dialog .project-management-table .source-check.failure {
           background:#5a252b; color:#ffe0e0; border:1px solid #ae4b58;
         }
         .project-management-dialog .project-management-table .project-settings-open,
         .project-management-dialog .project-management-table .project-move {
           box-sizing:border-box; display:inline-flex; width:42px; height:42px;
           min-width:42px; min-height:42px; padding:9px; margin:0;
           justify-content:center; align-items:center; color:#cbeaf5;
           background:#263a45; border:1px solid #44606d; border-radius:10px;
           box-shadow:none;
         }
         .project-management-dialog .project-management-table .project-settings-open {
           color:#91daf6; border-color:#52788b; background:#253c49;
         }
         .project-management-dialog .project-management-table .project-move:disabled {
           color:#8e9aa2; background:#212b31; border-color:#394751; opacity:.44;
         }
         .project-management-dialog .project-management-table button:not(:disabled):hover {
           filter:brightness(1.18); box-shadow:0 1px 8px #0005;
         }
         .project-management-dialog .project-management-table button:not(:disabled):active {
           transform:translateY(2px) scale(.95); filter:brightness(.8);
         }
         .project-management-dialog .project-actions {display:flex;flex-wrap:wrap;gap:8px;margin-top:14px;}
         .project-management-dialog .project-actions .project-action-primary {
           box-sizing:border-box; display:inline-flex; gap:8px; align-items:center;
           justify-content:center; margin:0; padding:10px 12px; min-height:42px;
           background:#263e4b; color:#e3f6ff; border:1px solid #52788b;
           border-radius:10px; font-size:13px; font-weight:600;
           white-space:nowrap; box-shadow:none;
         }
         .project-management-dialog .project-actions .project-action-primary .project-icon {width:20px;height:20px;}
         .project-management-dialog #project-check-all {
           background:linear-gradient(150deg,#244858,#1a3545); border-color:#5894a8;
           color:#e5faff;
         }
         .project-management-dialog .project-check-all-feedback {
           margin:9px 0 2px; color:var(--secondary-text-color,#c0ccd1);
           font-size:13px; font-weight:600; min-height:1.2em;
         }
         .project-management-dialog .project-check-all-feedback:empty {
           margin:0; min-height:0;
         }

         .project-management-dialog #project-management-close {
           box-sizing:border-box; width:44px; height:44px; min-width:44px;
           display:inline-flex; align-items:center; justify-content:center;
           background:#263a45; border:1px solid #52788b;
           padding:10px; border-radius:12px;
         }
         .project-management-dialog .project-management-footer button {
           display:inline-flex; align-items:center; justify-content:center; gap:7px;
           background:#263a45; color:#e3f6ff; border:1px solid #52788b;
           font-size:13px; padding:10px 12px; min-height:42px;
         }
         @media (max-width:760px) {
           .project-management-dialog .project-card tr,
           .project-management-dialog.project-card tr {
             gap:7px 6px; margin-bottom:7px; padding:9px;
             grid-template-columns:24px minmax(0,1fr) 42px 90px;
           }
           .project-management-dialog .project-management-table td:nth-child(3) button {
             display:inline-flex; width:auto; max-width:100%;
             min-width:0; height:42px; padding:7px 9px; font-size:12px;
           }
           .project-management-dialog .project-management-table td:nth-child(4) button,
           .project-management-dialog .project-management-table td:nth-child(5) button {
             display:inline-flex; width:42px; height:42px; flex:0 0 42px;
             min-width:42px; padding:8px; margin:0;
           }
           .project-management-dialog .project-management-table td:nth-child(5) {
             min-width:0; gap:5px; display:flex; justify-content:flex-end;
           }
           .project-management-dialog .project-management-table .project-icon {
             width:20px; height:20px;
           }
           .project-management-dialog .project-management-table .source-check .project-icon {
             width:18px; height:18px;
           }
           .project-management-dialog .project-actions {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px;}
           .project-management-dialog .project-actions .project-action-primary {
             width:100%; min-width:0; padding:10px 7px; font-size:clamp(11px,3vw,13px);
             white-space:normal; text-align:center;
           }
           .project-management-dialog #backup-dialog-open {grid-column:1 / -1;}
           .project-management-dialog #project-check-all {grid-column:1 / -1;}
         }
         /* Metallic surfaces: brushed steel, beveled edges, reflected light and depth. */
         .project-management-dialog .project-management-table button.project-metal-button {
           position:relative; isolation:isolate; overflow:hidden;
           background:
             linear-gradient(162deg,rgba(252,255,255,.22) 0%,rgba(202,233,247,.085) 11%,transparent 43%),
             linear-gradient(143deg,#526d7e 0%,#344e5c 20%,#172e3a 48%,#385263 73%,#142631 100%);
           border:1px solid #748fa0; border-radius:10px;
           color:#e4f5fe;
           box-shadow:inset 0 1px 0 rgba(255,255,255,.57),
             inset 1px 0 0 rgba(228,246,255,.19),
             inset 0 -2px 3px rgba(1,10,18,.65),
             0 2px 6px rgba(0,0,0,.4),0 0 0 1px rgba(9,21,28,.47);
           transition:transform .14s ease,filter .14s ease,box-shadow .14s ease;
         }
         .project-management-dialog .project-management-table button.project-metal-button::before {
           content:""; position:absolute; pointer-events:none; inset:1px 3px auto;
           height:43%; border-radius:9px 9px 45% 45%;
           background:linear-gradient(180deg,rgba(255,255,255,.3),rgba(255,255,255,.07) 36%,transparent);
           opacity:.77; z-index:0;
         }
         .project-management-dialog .project-management-table button.project-metal-button::after {
           content:""; position:absolute; pointer-events:none;
           top:-30%; left:-48%; width:58%; height:165%; transform:skewX(-25deg);
           background:linear-gradient(90deg,transparent,rgba(255,255,255,.15),transparent);
           opacity:.66; z-index:0;
         }
         .project-management-dialog .project-management-table button.project-metal-button .project-icon {
           position:relative; z-index:1; stroke-width:1.9;
           filter:drop-shadow(0 1px 1px rgba(0,8,16,.95))
             drop-shadow(0 -1px .65px rgba(240,252,255,.3));
         }
         .project-management-dialog .project-management-table button.project-metal-button:not(:disabled):hover {
           filter:brightness(1.18);
           box-shadow:inset 0 1px 0 rgba(255,255,255,.84),
             inset 0 -2px 3px rgba(0,8,16,.6),0 3px 10px rgba(1,14,25,.55),
             0 0 8px rgba(139,209,241,.25);
         }
         .project-management-dialog .project-management-table button.project-metal-button:not(:disabled):active {
           transform:translateY(2px) scale(.975); filter:brightness(.83);
           box-shadow:inset 0 3px 6px rgba(0,5,13,.85),
             inset 0 -1px 0 rgba(207,235,249,.18),0 1px 2px rgba(0,0,0,.35);
         }
         .project-management-dialog .project-management-table button.project-metal-button:focus-visible {
           outline:2px solid #f1c76d; outline-offset:3px;
         }
         .project-management-dialog .project-management-table button.project-metal-button:disabled {
           background:linear-gradient(155deg,#2e383e,#1a252b 65%,#222b30);
           border-color:#40505a; opacity:.48; filter:saturate(.25);
           box-shadow:inset 0 1px 0 rgba(255,255,255,.1),
             inset 0 2px 4px rgba(0,0,0,.44);
           cursor:default; transform:none;
         }
         .project-management-dialog .project-management-table button.project-metal-button:disabled::after {opacity:0;}
         /* Inactive state is an overlay in the top-right project header, never an extra line. */
         .project-management-dialog .project-management-table td.project-entry-inactive {
           position:relative; padding-right:76px;
         }
         .project-management-dialog .project-management-table .project-inactive-label {
           position:absolute; top:2px; right:8px;
           display:inline-flex; align-items:center; justify-content:center;
           white-space:nowrap; margin:0; padding:3px 7px;
           font-size:12px; line-height:1.2; font-weight:800; letter-spacing:.015em;
           color:#ff8998; border:1px solid rgba(234,104,124,.52);
           border-radius:7px; background:linear-gradient(145deg,rgba(125,32,51,.36),rgba(85,22,37,.13));
           text-shadow:0 1px 1px rgba(15,0,0,.48);
         }
         @media (max-width:760px) {
           .project-management-dialog .project-management-table td.project-entry-inactive {
             padding-right:71px;
           }
           .project-management-dialog .project-management-table .project-inactive-label {
             top:0; right:0; font-size:11px; padding:3px 6px;
           }
         }
         @media(prefers-reduced-motion:reduce) {
           .project-management-dialog .project-management-table button.project-metal-button {transition:none;}
         }
         .batch-options { max-height:55vh; overflow:auto; }
         .backup-dialog { width:min(100%,760px); }
         .backup-entry { border:1px solid var(--divider-color,#555); border-radius:10px; margin:10px 0; padding:12px; }
         .backup-entry label { margin-top:8px; }
         .settings-fields { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; align-items:end; }
         .settings-fields > label { display:flex; flex-direction:column; gap:6px; min-width:0; }
         .settings-fields .project-text { margin:0; width:100%; }
         @media (max-width:850px) { .settings-fields { grid-template-columns:1fr; } }
         .section-body[hidden] { display:none !important; }
         .section-toggle-title { margin:0 !important; padding:0 !important; border-bottom:none !important; }
         .section-toggle { display:flex; align-items:center; justify-content:space-between; gap:12px; width:100%; margin:0; padding:4px 2px 12px; text-align:left; color:inherit; background:transparent; font-weight:700; font-size:inherit; border-radius:4px; }
         .section-toggle:hover { background:var(--secondary-background-color,rgba(128,128,128,.08)); }
         .section-body { border-top:1px solid var(--divider-color,#555); padding-top:12px; }
         .section-toggle[aria-expanded="false"] { padding-bottom:4px; }
         .section-card:has(.section-toggle[aria-expanded="false"]) { padding-bottom:14px; }
         .section-card { min-width:0; border:1px solid var(--divider-color,#555); box-shadow:0 2px 12px rgba(0,0,0,.08); }
         .section-card h2 { font-size:18px; margin:0 0 12px; padding-bottom:12px; border-bottom:1px solid var(--divider-color,#555); }
         .inner-panel { border:1px solid var(--divider-color,#555); background:var(--secondary-background-color,rgba(127,127,127,.07)); border-radius:10px; padding:12px 14px; margin-top:14px; }
         .inner-panel h3 { font-size:15px; margin:0 0 8px; }
         .inner-panel p { margin:9px 0; }
         .dashboard-grid, .administration-grid { display:grid; grid-template-columns:minmax(0,1fr); gap:16px; align-items:start; }
         .dashboard-grid > article, .administration-grid > article { margin-top:16px; min-width:0; }
         .export-card { border-top:3px solid var(--primary-color,#396a96); }
         .status-panel { border-left:3px solid var(--primary-color,#396a96); }
         @media (min-width:1100px) {
           .dashboard-grid { grid-template-columns:minmax(0,1.15fr) minmax(370px,.85fr); }
           .administration-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
           .project-card { grid-row:span 2; }
         }
         @media (max-width:600px) {
           .dashboard-grid, .administration-grid { gap:0; }
           .inner-panel { padding:10px; }
           .section-card h2 { font-size:17px; }
         }
      </style>
      <main>
        <header class="dra-head">
          <div><strong>DEPLOY RELAY AGENT V2</strong><div class="note">Sicheres Deployment für Git-Projekte</div></div>
          <div class="dra-actions"><span class="dra-lock">GESPERRT</span><span class="note">V2 DEV</span>
          <button id="dra-refresh">Aktualisieren</button>
          <button id="dra-toggle">${this._view === "main" ? "Diagnose & Einstellungen" : "Hauptmenü"}</button></div>
        </header>
        <section id="dra-main-view" ${this._view==="main"?"":"hidden"}>
          <article class="dra-projectbar"><label><strong>Projekt</strong>
          <select id="dra-select">${activeMainProjects.map(p=>`<option value="${this._escapeProject(p.repository)}" ${mainProject?.repository===p.repository?"selected":""}>${this._escapeProject(p.name)}</option>`).join("")}</select>
          </label><button id="dra-project-manage">Projektverwaltung</button>
          <button disabled>Sicherungen</button></article>
          <div class="dra-warning"><strong>Gesperrter Betrieb</strong><div>Deployment-Schreibzugriffe sind deaktiviert. Vorschau und Diagnose bleiben verfügbar.</div></div>
          <article><h2>Geführter Ablauf</h2><p class="note">Orientierung am bewährten DRA-V1-Aufbau.</p>
          <div class="dra-steps"><button id="dra-step1" class="current">1 · Stand auswählen</button><button id="dra-step2" class="${this._sourceRepository === mainProject?.repository && this._sourcePreview ? "current" : ""}">2 · Vorschau prüfen</button>
          <button disabled>3 · Schreibzugriff</button><button disabled>4 · Installieren</button></div></article>
          <div class="dra-main-grid">
          <article><h2>${mainProject ? this._escapeProject(mainProject.name) : "Kein aktives Projekt"}</h2>
          <p>Repository: ${mainProject ? this._escapeProject(mainProject.repository) : "—"}</p>
          <p>Manifest: deploy-relay.json</p><p>Status: Registrierung vorhanden; Quelle noch nicht geprüft</p>
          <p>GitHub-Zugang: ${mainProject?.token_configured ? "Projekttoken vorhanden" : "Kein Projekttoken"}</p>
          <button id="dra-settings-project" ${!mainProject?"disabled":""}>Projekt / Token verwalten</button></article>
          <article><h2>Quelle & Version</h2><div class="dra-warning">Empfohlenes Deployment konnte noch nicht sicher bestimmt werden.</div>
          <p>Ausgewählt: ${mainProject ? this._escapeProject(mainProject.repository) : "—"}</p>
          <p>Quellstand: ${this._sourceRepository === mainProject?.repository && this._sourcePreview ? this._escapeProject(this._sourcePreview.source_commit?.slice(0,12)) : "Noch nicht geprüft"}</p>
          <label>Git-Referenz (Branch, Tag oder Commit; leer = Standardzweig)
          <input id="dra-main-ref" class="project-text" placeholder="z. B. deploy/dev" value="${this._escapeProject(this._mainSourceRef)}" autocomplete="off" /></label>
          <button id="dra-source" ${!mainProject?"disabled":""}>Erweiterte Quellenauswahl</button></article></div>
          <article><h2>Vorschau</h2><button id="dra-preview" ${!mainProject?"disabled":""}>2 · Vorschau vorbereiten</button>
          <button disabled>3 · Schreibzugriff freigeben</button><button disabled>0 Änderungen installieren</button>
          <p class="note" role="status">${this._sourceRepository === mainProject?.repository ? this._escapeProject(this._sourceMessage) : "Noch keine Vorschau berechnet."}</p>
          ${this._sourceRepository === mainProject?.repository && this._sourcePreview ? `<p>Commit: ${this._escapeProject(this._sourcePreview.source_commit?.slice(0,12))} · Hinzugefügt: ${this._sourcePreview.add.length} · Geändert: ${this._sourcePreview.change.length} · Entfernt: ${this._sourcePreview.remove.length} · Unverändert: ${this._sourcePreview.unchanged_count}</p>` : ""}</article>
          <article><h2>Diagnose & Logs</h2><p><strong>Letzter Teststatus:</strong> ${label} · ${progress}</p><p><strong>Diagnoseexport:</strong> ${this._diagnosticsExportReady ? "Verfügbar" : "Noch kein freigegebener Messlauf"}</p><p class="note">Teststeuerung, Projektverwaltung und Git-Export bleiben im Untermenü erreichbar.</p>
          <button id="dra-open-diagnostics">Diagnose & Einstellungen öffnen</button></article>
        </section>
        <section id="dra-settings-view" ${this._view==="settings"?"":"hidden"}>
        <h1>DRA V2 DEV · Diagnose & Einstellungen</h1>
        <p class="safe">Getrennt von DRA V1 · Nur schreibgeschützter Testbetrieb</p>
        <p>Dieser Test liest keine Projektdateien und führt keine Installation, Wiederherstellung oder Neustarts aus.</p>
        <div class="dashboard-grid">
        <article class="section-card test-card">
          <h2 class="section-toggle-title"><button class="section-toggle" data-section="1" aria-expanded="${this._expandedSections.has('1')}" aria-controls="section-body-1"><span>01 · Teststeuerung</span><span aria-hidden="true">${this._expandedSections.has('1') ? "▾" : "▸"}</span></button></h2><div id="section-body-1" class="section-body" ${this._expandedSections.has('1') ? "" : "hidden"}>
          <p>Starte eine CPU-/RAM-Messung, die Mehrkern-Diagnose oder den Gesamttest. Die Aufträge laufen unabhängig vom geöffneten Browser weiter.</p>
          <div class="inner-panel status-panel"><h3>Aktueller Auftrag</h3>
          <p><strong>Status:</strong> ${label}</p>
          <p><strong>Fortschritt:</strong> ${progress}</p>
          <p><strong>Restzeit:</strong> <span class="countdown" id="remaining">${this._remainingText()}</span></p>
          <p class="note"><strong>Auftragskennung:</strong> <code>${safeId}</code></p>
          ${this._error ? `<p class="error">${this._error}</p>` : ""}
          <button id="refresh" ${this._busy ? "disabled" : ""}>Status aktualisieren</button>
          </div><div class="inner-panel"><h3>Testarten</h3>
          <button id="measure" ${busy ? "disabled" : ""}>Messlauf starten (40 s)</button>
          <button id="multicore" ${busy ? "disabled" : ""}>Mehrkern-Diagnose (1 / 2 / 4 / 6 / 8 / 10 / 12)</button>
          <button id="all" ${busy ? "disabled" : ""}>Alle Tests nacheinander starten</button>
          <p class="note">Gesamttest: erst 40 Sekunden Auftragsprüfung, dann 40 Sekunden CPU-/Speichermessung,
          anschließend nacheinander 1, 2, 4, 6, 8, 10 und 12 getrennte Arbeitsprozesse. Ein Auftrag, ein Git-Export.</p>
          <p class="note">Messlauf: 10 Sekunden Basis, 20 Sekunden begrenzte Rechenarbeit
          außerhalb der HA-Ereignisschleife, 10 Sekunden Nachlauf. Maximal ein Auftrag gleichzeitig.</p>
          </div>
          </div>
        </article>
        <article class="section-card export-card">
          <h2 class="section-toggle-title"><button class="section-toggle" data-section="2" aria-expanded="${this._expandedSections.has('2')}" aria-controls="section-body-2"><span>02 · Diagnoseexport</span><span aria-hidden="true">${this._expandedSections.has('2') ? "▾" : "▸"}</span></button></h2><div id="section-body-2" class="section-body" ${this._expandedSections.has('2') ? "" : "hidden"}>
          <p class="note">Lokale JSON-Datei oder Export in dein selbst eingerichtetes privates GitHub-Repository.</p>
          <div class="git-main-actions">
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
          </div>
        </article>
        </div>
        <article class="diagnostic-results section-card">
          <h2 class="section-toggle-title"><button class="section-toggle" data-section="3" aria-expanded="${this._expandedSections.has('3')}" aria-controls="section-body-3"><span>03 · Messergebnisse und Auswertung</span><span aria-hidden="true">${this._expandedSections.has('3') ? "▾" : "▸"}</span></button></h2><div id="section-body-3" class="section-body" ${this._expandedSections.has('3') ? "" : "hidden"}>
          <p class="note">Ausführliche Messwerte und Mehrkern-Ergebnisse erscheinen hier nach dem Test.</p>
          ${report}
          ${multicoreReport}
          </div>
        </article>
        <div class="administration-grid">
        <article class="section-card">
          <h2 class="section-toggle-title"><button class="section-toggle" data-section="4" aria-expanded="${this._expandedSections.has('4')}" aria-controls="section-body-4"><span>04 · Auftragsverarbeitung</span><span aria-hidden="true">${this._expandedSections.has('4') ? "▾" : "▸"}</span></button></h2><div id="section-body-4" class="section-body" ${this._expandedSections.has('4') ? "" : "hidden"}>
          <p class="note">Gespeicherte Planungsvorgaben. Die aktive Testlabor-Sperre bleibt bei
          einem Leseauftrag und null Schreibaufträgen. Dies begrenzt derzeit keine echten Prozessorkerne.</p>
          <div class="settings-fields">
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
          </div>
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
          <button id="settings-save" ${this._settingsBusy ? "disabled" : ""}>Speichern</button>
          <p class="note">${this._escapeProject(this._settingsMessage)}</p>
          <p class="note">Die separate feste Mehrkern-Diagnose bleibt unverändert. Kein
          Schreibzugriff, kein CPU-Pinning und keine automatische Ressourcensteuerung.</p>
          </div>
        </article>

        <article class="section-card">
          <h2 class="section-toggle-title"><button class="section-toggle" data-section="5" aria-expanded="${this._expandedSections.has('5')}" aria-controls="section-body-5"><span>05 · Sammelaktualisierung</span><span aria-hidden="true">${this._expandedSections.has('5') ? "▾" : "▸"}</span></button></h2><div id="section-body-5" class="section-body" ${this._expandedSections.has('5') ? "" : "hidden"}>
          <p class="note">Projektvorauswahl für spätere Sammelaktualisierungen. Keine Installation.</p>
          <button id="batch-open" ${this._projects.length === 0 ? "disabled" : ""}>Projektauswahl bearbeiten</button>
          <p class="note">${this._projects.filter(p => p.active !== false && p.batch_preselect !== false).length} von ${this._projects.filter(p => p.active !== false).length} aktiven Projekten ausgewählt.</p>
          <p class="note" role="status">${this._escapeProject(this._batchDialogOpen ? "" : this._batchMessage)}</p>
          </div>
        </article>

        </div>
        </section>
        ${this._projectDialogOpen ? `
          <div class="git-dialog-backdrop" id="project-management-backdrop">
            <section class="git-dialog project-management-dialog project-card"
              id="project-management-dialog" role="dialog" aria-modal="true"
              aria-labelledby="project-management-title" tabindex="-1">
              <header>
                <h2 id="project-management-title">Projektverwaltung</h2>
                <button id="project-management-close" aria-label="Projektverwaltung schließen"
                  ${this._projectBusy || this._sourceBusy || this._gitReadBusy || this._checkAllBusy ? "disabled" : ""}>${closeIcon}</button>
              </header>
              <div class="project-management-scroll" id="project-management-scroll">
              <p class="note">Reihenfolge: Anzeige, Standardprojekt und Priorität der späteren Sammelaktualisierung. Git-Status nur nach expliziter Prüfung.</p>
          ${this._projects.length ? `<div class="table-wrap"><table class="project-management-table"><thead><tr><th>Nr.</th><th>Projekt</th><th>Git-Status</th><th>Einstellungen</th><th>Reihenfolge</th></tr></thead><tbody>${projectRows}</tbody></table></div>` : '<p class="note">Noch keine Projekte in V2 hinterlegt.</p>'}
          <div class="project-actions">
            <button id="project-add-open" class="project-action-primary" ${this._checkAllBusy ? "disabled" : ""}>${plusIcon}<span>Projekt hinzufügen</span></button>
            <button id="project-preview" class="project-action-primary" ${this._projectBusy || this._checkAllBusy ? "disabled" : ""}>${importIcon}<span>Import aus DRA-V1</span></button>
            <button id="backup-dialog-open" class="project-action-primary" ${this._checkAllBusy ? "disabled" : ""}>${backupIcon}<span>Backup &amp; Retention</span></button>
            <button id="project-check-all" class="project-action-primary"
              ${this._checkAllBusy || this._connectionBusy || this._projectBusy || this._sourceBusy || this._gitReadBusy || !this._projects.length ? "disabled" : ""}>
              ${checkAllIcon}<span>${this._checkAllBusy ? "Prüfung läuft …" : "Alle Projekte prüfen"}</span>
            </button>
          </div>
          <p class="project-check-all-feedback" role="status" aria-live="polite">${this._escapeProject(this._checkAllProgress)}</p>
          <p class="note" role="status">${this._escapeProject(this._projectMessage)}</p>
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

              <div class="dialog-actions project-management-footer">
                <button id="project-management-dismiss"
                  ${this._projectBusy || this._sourceBusy || this._gitReadBusy ? "disabled" : ""}>${closeIcon}<span>Schließen</span></button>
              </div>
              </div>
            </section>
          </div>` : ""}
        ${(managed || this._projectSettingsRepo === "__new__") ? `
          <div class="git-dialog-backdrop"><section class="git-dialog" role="dialog" aria-modal="true" aria-labelledby="manage-project-title">
            <header><h2 id="manage-project-title">${managed ? "Projekteinstellungen" : "Projekt hinzufügen"}</h2>
            <button id="manage-close" aria-label="Schließen">✕</button></header>
            <label>GitHub-Repository (Eigentümer/Repository)
              <input id="manage-repository" class="project-text" value="${this._escapeProject(managed?.repository || "")}" autocomplete="off" /></label>
            <p class="note">Ein geändertes Repository wird vor dem Speichern schreibgeschützt geprüft. Schlägt die Prüfung fehl, bleibt das bisherige Repository erhalten.</p>
            <label>GitHub-Token <input id="manage-token" class="project-text" type="password" autocomplete="new-password" placeholder="Neuen Token eingeben (optional)" /></label>
            <div class="project-token-summary">
              <div class="project-token-info note">Gespeicherter Token: ${managed?.token_configured && managed?.token_suffix ?
                `•••••<span class="safe"><strong>${this._escapeProject(managed.token_suffix)}</strong></span>` : "Nicht eingerichtet"}</div>
              <div class="project-token-access">
                <label for="manage-access-mode">Zugriffsart:</label>
                <select id="manage-access-mode" class="project-text" title="Informative Zugriffsart; ändert keine GitHub-Berechtigungen">
                  <option value="read_only" ${managed?.access_mode !== "read_write" ? "selected" : ""}>Read-Only</option>
                  <option value="read_write" ${managed?.access_mode === "read_write" ? "selected" : ""}>Read-Write</option>
                </select>
              </div>
            </div>
            <div class="project-token-actions">
              <button id="manage-token-save" ${!managed || this._projectBusy ? "disabled" : ""}>Token speichern</button>
              <button id="manage-connection-check" ${!managed || this._connectionBusy || this._projectBusy ? "disabled" : ""}>Verbindung prüfen</button>
            </div>
            ${managed && this._sourceChecks.get(managed.repository) ? `<p class="connection-feedback ${this._sourceChecks.get(managed.repository).status}" role="status">${this._escapeProject(this._sourceChecks.get(managed.repository).message)}</p>` : '<p class="note" role="status">Verbindung noch nicht geprüft.</p>'}
            <p class="note">Die Verbindungsprüfung verwendet den bereits gespeicherten Token. Eine neue Eingabe bitte zuvor speichern.</p>
            <p class="note">Der Token bleibt serverseitig. Leer lassen, um den bisherigen Token beizubehalten.</p>
            <p class="note project-access-help">Zugriffsart ist nur eine Angabe zur Übersicht; die GitHub-Berechtigungen bleiben unverändert. Änderungen werden mit „Speichern“ übernommen.</p>
            <label>Notiz <textarea id="manage-note" class="project-text" rows="3">${this._escapeProject(managed?.note || "")}</textarea></label>
            <label>Anzeigename (optional) <input id="manage-name" class="project-text" value="${this._escapeProject(managed?.name || "")}" /></label>
            <label><input id="manage-active" type="checkbox" ${managed?.active !== false ? "checked" : ""} /> Projekt aktiv</label>
            <div class="dialog-actions manage-dialog-actions ${managed ? "has-remove" : ""}">
              ${managed ? '<button id="manage-remove-start" class="danger">Projekt entfernen</button>' : ""}
              <button id="manage-cancel">Abbrechen</button>
              <button id="manage-save">Speichern</button>
            </div>
            ${this._projectDeleteConfirm ? `<div class="warning-cpu" role="alert"><strong>Projekt wirklich entfernen?</strong>
              <p>Nur die Registrierung in DRA V2 wird entfernt. V1, GitHub und installierte Anwendungen bleiben unangetastet.</p>
              <button id="manage-remove-cancel">Abbrechen</button>
              <button id="manage-remove-confirm" class="danger">Ja, Projekt entfernen</button></div>` : ""}
          </section></div>` : ""}
        ${this._importDialogOpen ? `
          <div class="git-dialog-backdrop">
            <section class="git-dialog" id="project-import-dialog" role="dialog" aria-modal="true" aria-labelledby="project-import-title">
              <header>
                <h2 id="project-import-title">Projektimport · DRA V1</h2>
                <button id="project-import-all" ${this._projectBusy ? "disabled" : ""}>Alle auswählen</button>
              </header>
              <p class="note">Nur ausgewählte Projektinformationen werden übernommen. Keine Tokens, Sicherungen oder Installationen.</p>
              <div class="batch-options">${importRows || '<p class="note">Keine Projekte verfügbar.</p>'}</div>
              <p class="note" role="status">${this._escapeProject(this._projectMessage)}</p>
              <div class="dialog-actions">
                <button id="project-import" ${this._projectBusy || !this._importSelection.length ? "disabled" : ""}>Importieren</button>
                <button id="project-cancel" ${this._projectBusy ? "disabled" : ""}>Abbrechen</button>
              </div>
            </section>
          </div>` : ""}
        ${this._backupDialogOpen ? `
          <div class="git-dialog-backdrop">
            <section class="git-dialog backup-dialog" id="backup-dialog" role="dialog"
              aria-modal="true" aria-labelledby="backup-title">
              <header><h2 id="backup-title">Backup &amp; Retention</h2>
                <button id="backup-close" ${this._projectBusy ? "disabled" : ""} aria-label="Schließen">✕</button>
              </header>
              <p class="note">Anzahl aufzubewahrender Sicherungen pro Projekt (3–100).
                Diese Vorgabe erstellt, löscht oder verändert derzeit keine Sicherungen.</p>
              ${this._projects.map(p => {
                const saved = this._projectSaved.get(p.repository) === p.backup_retention;
                return `<div class="backup-entry">
                  <strong>${this._escapeProject(p.name)}</strong>
                  <div class="note">${this._escapeProject(p.repository)}</div>
                  <label>Letzte Sicherungen behalten
                    <input class="retention" type="number" min="3" max="100"
                      value="${p.backup_retention}" aria-label="Aufbewahrungszahl ${this._escapeProject(p.name)}" />
                  </label>
                  <button class="retention-save ${saved ? "retention-saved" : ""}"
                    data-repo="${this._escapeProject(p.repository)}"
                    ${this._projectBusy ? "disabled" : ""}>${saved ? "Gespeichert" : "Speichern"}</button>
                  <button disabled title="Erst nach Einführung echter V2-Sicherungen verfügbar">Verfügbare Backups anzeigen</button>
                </div>`;
              }).join("")}
              <p class="note">Backup-Liste und dauerhaftes Festschreiben folgen erst mit der
                geprüften V2-Sicherungsverwaltung. V1-Sicherungen bleiben unangetastet.</p>
              <p class="note" role="status">${this._escapeProject(this._projectMessage)}</p>
              <div class="dialog-actions"><button id="backup-dismiss" ${this._projectBusy ? "disabled" : ""}>Schließen</button></div>
            </section>
          </div>` : ""}
        ${this._batchDialogOpen ? `
          <div class="git-dialog-backdrop">
            <section class="git-dialog" id="batch-dialog" role="dialog" aria-modal="true" aria-labelledby="batch-title">
              <header><h2 id="batch-title">Sammelaktualisierung · Projekte</h2>
              <button id="batch-close" aria-label="Schließen" ${this._batchBusy ? "disabled" : ""}>✕</button></header>
              <p class="note">Projekte durch Häkchen auswählen. Erst „Speichern“ übernimmt die Auswahl.</p>
              <div class="batch-options">${batchRows}</div>
              <p class="note" role="status">${this._escapeProject(this._batchMessage)}</p>
              <div class="dialog-actions">
                <button id="batch-save" ${this._batchBusy ? "disabled" : ""}>Speichern</button>
                <button id="batch-cancel" ${this._batchBusy ? "disabled" : ""}>Abbrechen</button>
              </div>
            </section>
          </div>` : ""}
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
              <div class="note git-saved-details">
                <p><strong>Gespeichertes Repository:</strong> ${this._centralExport.repository ?
                  this._escapeProject(this._centralExport.repository) : "Nicht eingerichtet"}</p>
                <p><strong>Token-Endung:</strong> ${this._centralExport.token_suffix &&
                  /^[A-Za-z0-9_-]{5}$/.test(this._centralExport.token_suffix) ?
                  "•••••" + this._escapeProject(this._centralExport.token_suffix) :
                  this._centralExport.server_token_available ? "Serverseitig eingerichtet" : "Nicht eingerichtet"}</p>
              </div>
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
    s.querySelector("#dra-toggle")?.addEventListener("click",()=>{this._view=this._view==="main"?"settings":"main";this._render();});
    s.querySelector("#dra-refresh")?.addEventListener("click",()=>this._refresh());
    s.querySelector("#dra-select")?.addEventListener("change",e=>{this._selectedMainRepo=e.target.value;this._sourcePreview=null;this._render();});
    s.querySelector("#dra-main-ref")?.addEventListener("input",e=>{this._mainSourceRef=e.target.value;});
    s.querySelector("#dra-project-manage")?.addEventListener("click",()=>this._openProjectDialog());
    s.querySelector("#dra-settings-project")?.addEventListener("click",()=>{if(mainProject){this._projectDialogOpen=true;this._openProjectSettings(mainProject.repository);}});
    for(const id of ["dra-preview","dra-step2"]){s.querySelector("#"+id)?.addEventListener("click",()=>{if(mainProject)this._sourceCheck({dataset:{repo:mainProject.repository}});});}
    s.querySelector("#dra-source")?.addEventListener("click",()=>this._openProjectDialog());
    s.querySelector("#dra-step1")?.addEventListener("click",()=>s.querySelector("#dra-select")?.focus());
    s.querySelector("#dra-open-diagnostics")?.addEventListener("click",()=>{this._view="settings";this._render();});
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
    s.querySelectorAll(".section-toggle").forEach(button => button.addEventListener("click", () => {
      const id = button.dataset.section;
      if (this._expandedSections.has(id)) this._expandedSections.delete(id);
      else this._expandedSections.add(id);
      this._render();
    }));
    s.querySelector("#settings-save")?.addEventListener("click", () => this._saveSettings());
    s.querySelector("#cpu-warning-ack")?.addEventListener("click", () => this._ackCpuWarning());
    s.querySelector("#backup-dialog-open")?.addEventListener("click", () => this._openBackupDialog());
    s.querySelector("#backup-close")?.addEventListener("click", () => this._closeBackupDialog());
    s.querySelector("#backup-dismiss")?.addEventListener("click", () => this._closeBackupDialog());
    s.querySelector("#batch-open")?.addEventListener("click", () => this._openBatchDialog());
    s.querySelector("#batch-close")?.addEventListener("click", () => this._cancelBatchDialog());
    s.querySelector("#batch-cancel")?.addEventListener("click", () => this._cancelBatchDialog());
    s.querySelector("#batch-save")?.addEventListener("click", () => this._saveBatchDialog());
    s.querySelectorAll(".batch-choice")?.forEach(input => input.addEventListener("change", () => {
      this._batchSelection = [...s.querySelectorAll(".batch-choice")].filter(x => x.checked).map(x => x.dataset.repo);

    }));
    s.querySelectorAll(".source-check")?.forEach(button => button.addEventListener("click", () => this._checkProjectConnection(button.dataset.repo)));
    s.querySelector("#project-check-all")?.addEventListener("click", () => this._checkAllProjectConnections());
    s.querySelector("#git-read-save")?.addEventListener("click", () => this._configureGitRead(false));
    s.querySelector("#git-read-clear")?.addEventListener("click", () => this._configureGitRead(true));
    s.querySelector("#project-preview")?.addEventListener("click", () => this._projectAction("v1_preview"));
    s.querySelector("#project-import")?.addEventListener("click", () => this._submitProjectImport());
    s.querySelector("#project-cancel")?.addEventListener("click", () => this._cancelProjectImport());
    s.querySelector("#project-import-all")?.addEventListener("click", () => {
      this._importSelection = (this._v1Candidates || []).map(p => p.repository);
      this._render();
    });
    s.querySelectorAll(".import-choice").forEach(input => input.addEventListener("change", () => {
      this._importSelection = [...s.querySelectorAll(".import-choice")].filter(x => x.checked).map(x => x.dataset.repo);
      this._render();
    }));
    s.querySelector("#project-management-close")?.addEventListener("click",()=>this._closeProjectDialog());
    s.querySelector("#project-management-dismiss")?.addEventListener("click",()=>this._closeProjectDialog());
    s.querySelector("#project-management-dialog")?.addEventListener("keydown",event=>{
      if(event.key === "Escape" && !this._projectBusy && !this._sourceBusy && !this._gitReadBusy) {
        event.preventDefault();
        this._closeProjectDialog();
      }
    });
    s.querySelector("#project-add-open")?.addEventListener("click", () => this._openProjectSettings("__new__"));
    s.querySelectorAll(".project-settings-open").forEach(b => b.addEventListener("click", () => this._openProjectSettings(b.dataset.repo)));
    s.querySelectorAll(".project-move").forEach(b => b.addEventListener("click", () => this._manageProject("move", {repository:b.dataset.repo,direction:Number(b.dataset.direction)})));
    // Tap/click anywhere in a row except its interactive controls to select it.
    s.querySelectorAll(".project-row").forEach(row => {
      const select = event => {
        if (event.target?.closest?.("button, a, input, select, textarea, label")) return;
        this._selectProjectRow(row.dataset.projectRepo);
      };
      row.addEventListener("click", select);
      row.addEventListener("keydown", event => {
        if (event.target !== row || (event.key !== "Enter" && event.key !== " ")) return;
        event.preventDefault();
        this._selectProjectRow(row.dataset.projectRepo);
      });
    });

    if (settingsDraft && s.querySelector("#manage-repository")) {
      s.querySelector("#manage-repository").value = settingsDraft.repository;
      s.querySelector("#manage-name").value = settingsDraft.name;
      s.querySelector("#manage-note").value = settingsDraft.note;
      s.querySelector("#manage-active").checked = settingsDraft.active;
      s.querySelector("#manage-access-mode").value = settingsDraft.accessMode;
      s.querySelector("#manage-token").value = settingsDraft.token;
    }
    s.querySelector("#manage-token-save")?.addEventListener("click", () => this._saveProjectToken());
    s.querySelector("#manage-connection-check")?.addEventListener("click", () => this._checkProjectConnection(this._projectSettingsRepo));
    s.querySelector("#manage-close")?.addEventListener("click", () => this._closeProjectSettings());
    s.querySelector("#manage-cancel")?.addEventListener("click", () => this._closeProjectSettings());
    s.querySelector("#manage-save")?.addEventListener("click", () => {
      if (this._projectSettingsRepo === "__new__") {
        const repo = s.querySelector("#manage-repository")?.value.trim();
        const name = s.querySelector("#manage-name")?.value.trim() || "";
        const note = s.querySelector("#manage-note")?.value || "";
        const active = s.querySelector("#manage-active")?.checked === true;
        const access_mode = s.querySelector("#manage-access-mode")?.value || "read_only";
        this._projectAction("add", {repository:repo,name,note,active,access_mode});
        this._projectSettingsRepo = null;
      } else this._saveProjectSettings();
    });
    s.querySelector("#manage-remove-start")?.addEventListener("click", () => { this._projectDeleteConfirm=true;this._render(); });
    s.querySelector("#manage-remove-cancel")?.addEventListener("click", () => { this._projectDeleteConfirm=false;this._render(); });
    s.querySelector("#manage-remove-confirm")?.addEventListener("click", () => this._manageProject("remove", {confirmed:true}));
    s.querySelector("#project-add")?.addEventListener("click", () => this._addProject());
    s.querySelectorAll(".retention-save")?.forEach(button => {
      button.addEventListener("click", () => this._retention(button));
      button.closest(".backup-entry")?.querySelector("input.retention")?.addEventListener("input", () => {
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
    const projectScroll = s.querySelector("#project-management-scroll");
    if (projectScroll) {
      projectScroll.scrollTop = previousProjectScroll;
      if (this._scrollToMovedProject) {
        const movedRow = [...projectScroll.querySelectorAll(".project-row")]
          .find(row => row.dataset.projectRepo === this._highlightMovedRepo);
        movedRow?.scrollIntoView({block:"nearest", behavior:"smooth"});
      }
    }
    this._scrollToMovedProject = false;
    this._syncCountdownTimer();
  }
}
if (!customElements.get("dra-v2-dev-lab-panel")) {
  customElements.define("dra-v2-dev-lab-panel", DRAV2DevLabPanel);
}

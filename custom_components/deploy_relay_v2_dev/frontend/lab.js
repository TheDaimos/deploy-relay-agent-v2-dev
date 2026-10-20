/* Separate DRA V2 DEV read-only lab. No V1 custom element or URLs. */
// Build identity of this actually loaded JavaScript, independent of the HA Python version.
const DRA_V2_UI_VERSION = "0.1.118";
const G2_TEST_PYTHON_VERSION = DRA_V2_UI_VERSION;
class DRAV2DevLabPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._operation = null;
    this._measurement = null;
    this._suite = null;
    this._projects = [];
    this._pickerBatchPosition = null; // Synthetic UI row, never a Git project.
    this._settings = {mode:"sequential",max_readonly_jobs:2,max_worker_processes:4};
    this._settingsBusy = false;
    this._expandedSections = new Set();
    this._view = "main";
    this._viewHistoryKey = "dra-v2-" + Math.random().toString(36).slice(2);
    this._viewHistoryActive = false;
    this._boundHistoryPop = event => this._onHistoryPop(event);
    this._selectedMainRepo = null;
    this._projectPickerOpen = false;
    this._mainBatchMode = false;
    this._mainBatchBusy = false;
    this._mainBatchPreview = null;
    this._mainBatchMessage = "";
    this._mainBatchSelectionOpen = false;
    this._batchRunSelected = null;
    this._manualSourceRef = false;
    this._batchPreparation = null;
    this._batchChallenge = null;
    this._batchReviewOpen = false;
    this._batchReviewChecked = false;
    this._batchReviewDigest = null;
    this._batchStatus = null;
    this._batchStartUncertain = false;
    this._batchStatusError = false;
    this._pickerBatchMessage = "";
    this._mainSourceRef = "";
    this._sourceChoices = null;
    this._sourceChoicesBusy = false;
    this._sourceChoicesMessage = "";
    this._sourceAdvancedOpen = false; // Only the user opens the advanced source section.
    this._sourceChoicesLoadedFor = null;
    this._automaticSourceCheckFor = null;
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
    this._v2SettingsOpen = false;
    this._v2AdvancedOpen = false;
    this._v2SourceRef = "";
    this._projectSaved = new Map();
    this._backupDialogOpen = false;
    this._projectMessage = "";
    this._sourceBusy = false;
    this._sourceRepository = null;
    this._sourceMessage = "";
    this._sourceHeadBusy = false;
    this._sourceHead = null;
    this._sourceHeadMessage = "";
    this._sourcePreview = null;
    this._previewDetailsOpen = false;
    this._previewFileFilter = "all";
    this._previewFileSearch = "";
    this._deploymentPreviewRef = null;
    this._installPreparation = null;
    // Local, ephemeral display identity, not an authentication credential.
    this._controllerId = Array.from({length:4},()=>
      Math.floor(Math.random()*0x100000000).toString(16).padStart(8,"0")).join("");
    this._controllerStatus = null;
    this._controllerBusy = false;
    this._controllerTimer = null;
    this._installJobId = null;
    this._installJob = null;
    this._installJobs = [];
    this._installProjectNames = {};
    this._restartSummary = null;
    this._deferredRestartDialogOpen = false;
    this._deferredRestartBusy = false;
    this._deferredRestartMessage = "";
    this._installStatusKnown = false;
    this._installStatusError = false;
    this._observerLastJobId = null;
    this._dismissedHistoricalProject = null;
    // Old server receipts remain visible in Audit but must not lock a new deployment.
    this._supersededCompletionIds = new Set();
    this._installBusy = false;
    this._installSubmissionActive = false;
    this._installStartUncertain = null;
    this._installMessage = "";
    this._restartDialogOpen = false;
    this._restartBusy = false;
    this._restartMessage = "";
    this._installTimer = null;
    this._installPolling = false;
    this._sourceJobId = null;
    this._sourceConnectionTest = false;
    this._testsOpen = false;
    this._testFileCount = 5;
    this._testDelaySeconds = 20;
    this._testVersionBusy = false;
    this._testVersionConfirm = false;
    this._testVersionResult = "";
    // Only the admin-only HA test/state endpoint can confirm the running Python version.
    this._serverVersion = null;
    this._sourceJobTimer = null;
    this._sourceJobPolling = false;
    this._sourceJobRestored = false;
    this._sourceSyncTick = 0;
    this._sourceJobRetryMs = 1200;
    this._sourceJobHistory = [];
    this._sourceJobHistoryStatus = "";
    this._deploymentLogsOpen = false;
    this._auditOpen = false;
    this._auditLevel = "all";
    this._auditProject = "all";
    this._auditKind = "all";
    this._auditPhase = "all";
    this._auditSearch = "";
    this._installAuditRecords = [];
    this._auditStatus = "";
    this._auditExportBusy = false;
    this._deploymentLogsBusy = false;
    this._historyRefreshBusy = false;
    this._historyRefreshStatus = "Nicht geprüft";
    this._historyRefreshDetail = "Noch keine aktuellen Serverdaten abgefragt.";
    this._historyRefreshTone = "idle";
    this._logsNotesOpen = false;
    this._deploymentLogs = [];
    this._logFilter = "all";
    this._logSearch = "";
    this._deploymentLogCount = 0;
    this._deploymentLogsStatus = "";
    this._deploymentLogsConfirm = false;
    this._g2RetryTestOpen = false;
    this._g2RetryTestConfirm = false;
    this._sourceChecks = new Map();
    this._connectionBusy = false;
    this._draftConnectionCheck = null;
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
      // Read HA write jobs independently from the project's initial state.
      void this._pollInstallation();
    }
  }

  connectedCallback() {
    if (typeof window !== "undefined") {
      window.addEventListener("popstate", this._boundHistoryPop);
    }
    this._render();
    if (this._hass && !this._loaded) {
      this._loaded = true;
      this._refresh();
      void this._pollInstallation();
    } else if (this._hass && this._loaded) {
      // Reattached mobile panel: reload server job regardless of old browser timers.
      this._refresh();
      this._pollSourceJob();
      void this._pollInstallation();
    }
  }

  disconnectedCallback() {
    if (this._installTimer !== null) clearTimeout(this._installTimer);
    this._installTimer = null;
    if (this._sourceJobTimer !== null) clearTimeout(this._sourceJobTimer);
    this._sourceJobTimer = null;
    if (this._controllerTimer !== null) clearTimeout(this._controllerTimer);
    this._controllerTimer = null;
    if (typeof window !== "undefined") {
      window.removeEventListener("popstate", this._boundHistoryPop);
    }
    this._viewHistoryActive = false;
    if (this._timer !== null) clearTimeout(this._timer);
    this._timer = null;
    if (this._countdownTimer !== null) clearTimeout(this._countdownTimer);
    this._countdownTimer = null;
    this._loaded = false;
  }

  _onHistoryPop(event) {
    // A native Android back action goes to the immediately preceding history
    // entry. If the settings subview was open, that entry is the DRA main view.
    if (!this.isConnected || typeof window === "undefined") return;
    const marker = event?.state?.dra_v2_dev_view;
    if (marker === this._viewHistoryKey) {
      this._viewHistoryActive = true;
      if (this._view !== "settings") {
        this._view = "settings";
        this._render();
      }
    } else if (this._viewHistoryActive || this._view === "settings") {
      this._viewHistoryActive = false;
      this._view = "main";
      this._render();
    }
  }

  _navigateMainView(nextView) {
    if (nextView !== "main" && nextView !== "settings") return;
    if (this._view === nextView) return;
    if (nextView === "settings") {
      if (typeof window !== "undefined") {
        try {
          const previous = window.history.state;
          const state = previous && typeof previous === "object" && !Array.isArray(previous)
            ? {...previous} : {};
          state.dra_v2_dev_view = this._viewHistoryKey;
          // Same URL: creates one native back step without changing the HA route.
          window.history.pushState(state, "", window.location.href);
          this._viewHistoryActive = true;
        } catch (_error) {
          // Browsers without a usable History API retain the visible UI toggle.
          this._viewHistoryActive = false;
        }
      }
      this._view = "settings";
      this._render();
      return;
    }
    // The onscreen "Hauptmenü" button must consume the same history entry as
    // the Android hardware back key; never leave a phantom extra back step.
    const shouldConsume = this._viewHistoryActive && typeof window !== "undefined" &&
      window.history.state?.dra_v2_dev_view === this._viewHistoryKey;
    this._viewHistoryActive = false;
    this._view = "main";
    this._render();
    if (shouldConsume) window.history.back();
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

  _scheduleControllerHeartbeat() {
    if (this._controllerTimer !== null) clearTimeout(this._controllerTimer);
    this._controllerTimer = null;
    if (!this.isConnected || !this._selectedMainRepo) return;
    this._controllerTimer = setTimeout(async () => {
      const repository = this._selectedMainRepo;
      if (this.isConnected && repository) {
        await this._syncController(repository);
        await this._restoreServerPreparation(repository);
      }
    }, 10000);
  }

  async _syncController(repository = this._selectedMainRepo, takeOver = false) {
    if (!repository || !this._hass || this._controllerBusy ||
        this._serverVersion !== DRA_V2_UI_VERSION) return false;
    this._controllerBusy = true;
    try {
      const response = await this._hass.callWS({
        type:"deploy_relay_v2_dev/deployment/control",
        repository, client_id:this._controllerId, take_over:takeOver,
      });
      if (this._selectedMainRepo !== repository ||
          response?.schema !== "dra-v2-controller.v1") return false;
      this._controllerStatus = response;
      return response.controller === true;
    } catch (_error) {
      this._controllerStatus = null;
      return false;
    } finally {
      this._controllerBusy = false;
      if (this.isConnected) this._render();
      this._scheduleControllerHeartbeat();
    }
  }

  async _restoreServerPreparation(repository = this._selectedMainRepo) {
    if (!repository || !this._hass || this._installBusy ||
        this._serverVersion !== DRA_V2_UI_VERSION) return;
    try {
      const response = await this._hass.callWS({
        type:"deploy_relay_v2_dev/deployment/prepared_status", repository,
      });
      if (this._selectedMainRepo !== repository ||
          response?.schema !== "dra-v2-prepared-status.v1") return;
      const prepared = response.preparation;
      if (!prepared) {
        if (this._installPreparation?.repository === repository) this._installPreparation = null;
        return;
      }
      if (prepared.schema !== "dra-v2-install-preparation.v1" ||
          prepared.repository !== repository ||
          prepared.confirmation_required !== true ||
          !/^[a-f0-9]{32}$/.test(prepared.challenge || "") ||
          !/^[a-f0-9]{40}$/.test(prepared.source_commit || "")) return;
      // A pending old main-branch approval must not overwrite the explicit
      // project-owned deploy/dev recommendation on every HA status poll.
      // The old challenge remains on HA until expiry; no write is triggered.
      const expected = this._sourceChoicesLoadedFor === repository &&
        this._sourceChoices?.recommended?.explicit && !this._manualSourceRef
        ? this._sourceChoices.recommended.ref : null;
      if (expected && prepared.source_ref !== expected) {
        this._installPreparation = null;
        this._sourceMessage = "Ältere Vorbereitung für " + prepared.source_ref +
          " nicht übernommen. Empfohlene Quelle: " + expected +
          ". Neue Quellprüfung erforderlich.";
        return;
      }
      this._installPreparation = prepared;
      this._sourceRepository = repository;
      this._mainSourceRef = prepared.source_ref;
      this._installMessage = "Vorbereitung auf Home Assistant vorhanden · auf diesem Gerät fortsetzbar.";
      // Recover the read-only report separately. Never manufacture verified data.
      await this._pollSourceJob(true);
    } catch (_error) {
      // A disconnected client must not revoke an HA-owned preparation.
    } finally {
      if (this.isConnected) this._render();
    }
  }

  async _prepareInstallation(project) {
    if (!this._hass || !project || project.active === false ||
        !this._sourcePreview || this._installBusy ||
        this._sourceRepository !== project.repository ||
        this._deploymentPreviewRef !== this._mainSourceRef.trim() ||
        this._serverVersion !== DRA_V2_UI_VERSION) return;
    if (Array.isArray(this._sourcePreview.add) &&
        Array.isArray(this._sourcePreview.change) &&
        Array.isArray(this._sourcePreview.remove) &&
        this._sourcePreview.add.length + this._sourcePreview.change.length +
        this._sourcePreview.remove.length === 0) return;
    if (!await this._syncController(project.repository)) {
      this._installMessage = "Bedienung auf einem anderen Gerät aktiv. Sitzung erst übernehmen.";
      this._render();
      return;
    }
    this._installBusy = true;
    this._installPreparation = null;
    this._installMessage = "Die V1-Engine prüft die Dateien erneut …";
    this._render();
    try {
      const result = await this._hass.callWS({
        type:"deploy_relay_v2_dev/deployment/prepare",
        test_delay_seconds:project.repository==="TheDaimos/Test-Repo-DRA-V2" ? this._testDelaySeconds : 0,
        repository:project.repository,
        ref:this._sourcePreview.source_ref,
        commit:this._sourcePreview.source_commit,
        client_id:this._controllerId,
      });
      if (result?.schema !== "dra-v2-install-preparation.v1" ||
          result?.confirmation_required !== true ||
          !/^[0-9a-f]{32}$/.test(result.challenge || "") ||
          result.repository !== project.repository ||
          result.source_commit !== this._sourcePreview.source_commit) {
        throw Error("unexpected preparation");
      }
      this._installPreparation = result;
      this._installStartUncertain = null;
      this._installMessage = "Vorbereitung abgeschlossen. Noch wurden keine Dateien geändert.";
    } catch (_error) {
      this._installMessage = "Vorbereitung fehlgeschlagen. Keine Dateien wurden geändert.";
    } finally {
      this._installBusy = false;
      if (this.isConnected) this._render();
    }
  }

  _releaseCompletedDeployment(project) {
    // A completed operation is audit history, never a new installation approval.
    // Keep the server receipt but stop using it as the active stepper state.
    if (!project) return;
    if (this._installJob?.project_key === project.project_id &&
        this._installJob?.status === "success" &&
        /^[a-f0-9]{32}$/.test(this._installJob.operation_id || "")) {
      this._supersededCompletionIds.add(this._installJob.operation_id);
    }
    this._dismissedHistoricalProject = project.project_id;
    this._installPreparation = null;
    this._installStartUncertain = null;
    this._installMessage = "";
    this._restartDialogOpen = false;
    this._restartMessage = "";
  }

  async _increaseTestVersion() {
    if (this._testVersionBusy || !this._testVersionConfirm ||
        !this._hass || this._serverVersion !== DRA_V2_UI_VERSION) return;
    this._testVersionBusy = true;
    this._testVersionResult = "Teststand wird ausschließlich im Test-Repository erhöht …";
    this._render();
    try {
      const result = await this._hass.callWS({
        type:"deploy_relay_v2_dev/test/version/increment",confirm:true,
        file_count:this._testFileCount,
      });
      if (result?.schema !== "dra-v2-test-version.v1" ||
          result.repository !== "TheDaimos/Test-Repo-DRA-V2" ||
          !Number.isInteger(result.before) || result.after !== result.before + 1 ||
          !/^[a-f0-9]{40}$/.test(result.commit || "")) throw Error("invalid receipt");
      this._testVersionResult = result.file_count + " Testdateien · Git-Teststand " + result.before + " → " + result.after +
        " · Commit " + result.commit.slice(0,12) + ". Neue Vorschau kann gestartet werden.";
      // The isolated test repository now has a new commit. A previous 4/4
      // result must never disable its next source inspection.
      const selected = this._projects.find(p=>p.repository===this._selectedMainRepo);
      if (selected?.repository === result.repository) {
        this._releaseCompletedDeployment(selected);
        this._sourcePreview = null;
        this._deploymentPreviewRef = null;
        this._sourceHead = null;
        this._sourceHeadMessage = "Teststand erhöht. Git-Quellstand aktualisieren oder neue Vorschau berechnen.";
      }
    } catch (_error) {
      this._testVersionResult = "Git-Teststand konnte nicht erhöht werden. Token-Schreibrecht und Testdatei prüfen.";
    } finally {
      this._testVersionBusy = false;
      this._testVersionConfirm = false;
      if (this.isConnected) this._render();
    }
  }

  async _confirmInstallation() {
    const prepared = this._installPreparation;
    const project = this._projects.find(p=>p.repository===this._selectedMainRepo);
    if (!this._hass || !prepared || !project || this._installBusy ||
        this._installStartUncertain || project.active === false ||
        this._sourceRepository !== prepared.repository ||
        prepared.source_ref !== this._mainSourceRef.trim() ||
        !/^[a-f0-9]{32}$/.test(prepared.challenge || "")) return;
    if (!await this._syncController(project.repository)) {
      this._installMessage = "Bedienung auf einem anderen Gerät aktiv. Sitzung erst übernehmen.";
      this._render();
      return;
    }
    const seenJobIds = this._installJobs.map(job=>job.operation_id);
    this._restartDialogOpen = false;
    this._restartMessage = "";
    this._installBusy = true;
    this._installSubmissionActive = true;
    this._installMessage = "Der Auftrag wird an Home Assistant übergeben …";
    this._render();
    try {
      const receipt = await this._hass.callWS({
        type:"deploy_relay_v2_dev/deployment/start",
        challenge:prepared.challenge, repository:prepared.repository,
        commit:prepared.source_commit, confirm:true,
        client_id:this._controllerId,
      });
      if (receipt?.schema !== "dra-v2-install-start.v1" ||
          !/^[a-f0-9]{32}$/.test(receipt.job?.operation_id || "")) throw Error("invalid receipt");
      this._installPreparation = null;
      this._installStartUncertain = null;
      this._installJobId = receipt.job.operation_id;
      this._installJob = receipt.job;
      await this._pollInstallation();
    } catch (_error) {
      // A lost WebSocket receipt does not mean HA rejected the write.
      // Never send a second installation request to resolve uncertainty.
      const attempt = {
        project_key:project.project_id,
        source_commit:prepared.source_commit,
        seen_ids:seenJobIds,
      };
      this._installStartUncertain = attempt;
      let recovered = null;
      try {
        const status = await this._hass.callWS({
          type:"deploy_relay_v2_dev/deployment/status",
        });
        if (status?.schema === "dra-v2-install-status.v1" &&
            Array.isArray(status.jobs)) {
          this._installJobs = status.jobs;
          recovered = status.jobs.find(job =>
            /^[a-f0-9]{32}$/.test(job?.operation_id || "") &&
            job.project_key === attempt.project_key &&
            job.source_commit === attempt.source_commit &&
            !attempt.seen_ids.includes(job.operation_id)) || null;
        }
      } catch (_statusError) {
        // Unknown status: do not infer that the server rejected the write.
      }
      if (recovered) {
        this._installPreparation = null;
        this._installStartUncertain = null;
        this._installJob = recovered;
        this._installJobId = recovered.operation_id;
        this._installMessage = "Auftrag auf Home Assistant gefunden. Installation wurde nicht erneut gestartet.";
      } else {
        // Re-checking the pending plan is read-only. Still inhibit retry:
        // server-side admission may have succeeded just before disconnect.
        const code = typeof _error?.code === "string" ? _error.code : "";
        const reasons = {
          controller_required:"Server hat die Bedienungsfreigabe abgelehnt.",
          confirmation_failed:"Server hat die Installationsfreigabe als ungültig oder abgelaufen abgelehnt.",
          not_permitted:"Server hat die Installationsberechtigung abgelehnt.",
          restart_pending:"Ein Home-Assistant-Neustart steht bereits aus.",
        };
        this._installMessage = (reasons[code] || "Auftragsannahme nicht bestätigt.") +
          " Serverstatus und Audit prüfen; Installation nicht erneut starten.";
      }
    } finally {
      this._installBusy = false;
      this._installSubmissionActive = false;
      if (this.isConnected) this._render();
    }
  }

  _refreshFrontendAfterInstallation() {
    const job = this._installJob;
    if (!job || job.status !== "success" || job.phase !== "complete" ||
        job.restart_required || job.frontend_reload_possible !== true ||
        this._serverVersion !== DRA_V2_UI_VERSION ||
        this._supersededCompletionIds.has(job.operation_id)) return;
    // A normal browser reload re-fetches frontend resources without restarting HA.
    // The V2 panel itself is registered without static cache headers.
    window.location.reload();
  }

  async _requestHomeAssistantRestart() {
    const job = this._installJob;
    if (!this._hass || this._restartBusy || !this._restartDialogOpen ||
        this._serverVersion !== DRA_V2_UI_VERSION ||
        !job || job.status !== "success" || job.phase !== "complete" ||
        job.restart_required !== true ||
        this._supersededCompletionIds.has(job.operation_id)) return;
    this._restartBusy = true;
    this._restartMessage = "Home-Assistant-Neustart wird angefordert …";
    this._render();
    try {
      const receipt = await this._hass.callWS({
        type:"deploy_relay_v2_dev/deployment/restart",
        operation_id:job.operation_id,confirm:true,
        client_id:this._controllerId,
      });
      if (receipt?.schema !== "dra-v2-restart-request.v1" ||
          receipt.operation_id !== job.operation_id ||
          receipt.restart_requested !== true) throw Error("invalid restart receipt");
      this._restartDialogOpen = false;
      this._restartMessage = "Home-Assistant-Neustart angefordert. Verbindung wird vorübergehend unterbrochen.";
    } catch (_error) {
      // The connection may be interrupted during the actual restart.
      // Do not silently send a second request or claim it definitely failed.
      this._restartMessage = "Keine Bestätigung erhalten. Möglicherweise startet Home Assistant bereits. Bitte Status abwarten; nicht erneut bestätigen.";
      this._restartDialogOpen = false;
    } finally {
      this._restartBusy = false;
      if (this.isConnected) this._render();
    }
  }

  async _confirmDeferredRestart() {
    const summary = this._restartSummary;
    const operationId = summary?.operation_id;
    if (!this._deferredRestartDialogOpen || this._deferredRestartBusy ||
        !this._hass || this._installStatusError ||
        this._serverVersion !== DRA_V2_UI_VERSION ||
        !summary?.required || summary.restart_requested ||
        !/^[0-9a-f]{32}$/.test(operationId || "") ||
        this._installJobs.some(job=>["queued","running","waiting_for_resource","cancel_requested"].includes(job.status))) return;
    this._deferredRestartBusy = true;
    this._deferredRestartMessage = "Gemeinsamer Home-Assistant-Neustart wird angefordert …";
    this._render();
    try {
      const receipt = await this._hass.callWS({
        type:"deploy_relay_v2_dev/deployment/restart",
        operation_id:operationId,confirm:true,client_id:this._controllerId,
      });
      if (receipt?.schema !== "dra-v2-restart-request.v1" ||
          receipt.operation_id !== operationId ||
          receipt.restart_requested !== true) throw Error("invalid restart receipt");
      this._deferredRestartDialogOpen = false;
      this._deferredRestartMessage = "Neustart angefordert. Keine zweite Anfrage senden.";
    } catch (_error) {
      this._deferredRestartDialogOpen = false;
      this._deferredRestartMessage = "Keine sichere Neustartbestätigung. Home-Assistant-Status abwarten, nicht erneut auslösen.";
    } finally {
      this._deferredRestartBusy = false;
      if (this.isConnected) this._render();
    }
  }

  async _pollInstallation() {
    // Read-only observer channel must work even when project discovery or
    // the general /test/state request has not yet completed on this device.
    if (!this._hass || this._installPolling) return;
    this._installPolling = true;
    if (this._installTimer !== null) clearTimeout(this._installTimer);
    this._installTimer = null;
    try {
      const response = await this._hass.callWS({
        type:"deploy_relay_v2_dev/deployment/status",
      });
      if (response?.schema !== "dra-v2-install-status.v1") throw Error("bad job response");
      this._installStatusKnown = true;
      this._installStatusError = false;
      try {
        const batch=await this._hass.callWS({type:"deploy_relay_v2_dev/batch/status"});
        if(batch?.schema==="dra-v2-batch-status.v1" && Array.isArray(batch.items)) {
          if (this._batchReviewDigest && batch.review_digest &&
              batch.review_digest !== this._batchReviewDigest) {
            this._batchReviewChecked=false;
            this._batchReviewOpen=false;
            this._batchChallenge=null;
            this._batchPreparation=null;
          }
          this._batchStatus=batch; this._batchStatusError=false;
          if(["queued","running","success","stopped","interrupted"].includes(batch.status)){
            this._batchChallenge=null;this._batchStartUncertain=false;
          }
        } else this._batchStatusError=true;
      } catch(_batchError){this._batchStatusError=true;}
      this._restartSummary = response.restart_summary?.schema === "dra-v2-restart-summary.v1"
        && Array.isArray(response.restart_summary.items)
        && Number.isInteger(response.restart_summary.count)
        && response.restart_summary.items.every(item=>
          /^[0-9a-f]{32}$/.test(item?.operation_id || "") &&
          typeof item.project_key === "string")
          ? response.restart_summary : null;
      this._installProjectNames = response.project_names &&
        typeof response.project_names === "object" && !Array.isArray(response.project_names)
          ? response.project_names : {};
      // The HA server owns all jobs. Browser changes or selecting another
      // project never hide the other projects' active installations.
      this._installJobs = Array.isArray(response.jobs)
        ? response.jobs.filter(j=>/^[a-f0-9]{32}$/.test(j?.operation_id || "")).slice(0,12)
        : response.job ? [response.job] : [];
      const activeJobs = this._installJobs.filter(j=>
        ["queued","running","waiting_for_resource","cancel_requested"].includes(j.status));
      if (activeJobs.length) this._observerLastJobId = activeJobs[0].operation_id;
      const chosenProject = this._projects.find(p=>p.repository===this._selectedMainRepo)
        || this._projects.find(p=>p.active!==false);
      const job = this._installJobs.find(j=>j.project_key===chosenProject?.project_id) || null;
      if (job && /^[a-f0-9]{32}$/.test(job.operation_id || "")) {
        this._installJobId = job.operation_id;
        this._installJob = job;
        if (this._installStartUncertain &&
            job.project_key === this._installStartUncertain.project_key &&
            job.source_commit === this._installStartUncertain.source_commit &&
            !this._installStartUncertain.seen_ids.includes(job.operation_id)) {
          this._installPreparation = null;
          this._installStartUncertain = null;
        }
        if (job.status === "success") {
          this._installMessage = job.restart_required ?
            "Update erfolgreich. Home-Assistant-Neustart erforderlich." :
            job.frontend_reload_possible ?
              "Update erfolgreich. Die Oberfläche kann jetzt aktualisiert werden." :
              "Update erfolgreich installiert und geprüft. Keine weitere Aktion erforderlich.";
        } else if (job.status === "recovery_required") {
          this._installMessage = "Wiederherstellung erforderlich. Keine weiteren Updates starten.";
        } else if (job.status === "failed" || job.status === "interrupted") {
          this._installMessage = "Update fehlgeschlagen oder unterbrochen. Transaktionsprotokoll prüfen.";
        } else {
          this._installMessage = "Serverseitig aktiv: " + (job.phase || "Vorbereitung");
        }
      } else {
        this._installJob = null;
        this._installJobId = null;
      }
    } catch (_error) {
      this._installStatusError = true;
      this._installMessage = "Serverstatus nicht abrufbar; ein laufendes Update wird dadurch nicht abgebrochen.";
    } finally {
      // Poll independently of a selected project and independently of the
      // HA state refresh loop. Never submit or repeat a write operation here.
      if (this.isConnected) {
        const busy = this._installJobs.some(j=>
          ["queued","running","waiting_for_resource","cancel_requested"].includes(j.status));
        this._installTimer = setTimeout(()=>this._pollInstallation(),
          this._installStatusError ? 4800 : busy ? 1500 : 10000);
      }
      this._installPolling = false;
      if (this.isConnected) this._render();
    }
  }

  async _refresh() {
    if (!this._hass || this._busy) return;
    this._busy = true;
    try {
      const data = await this._hass.callWS({ type: "deploy_relay_v2_dev/test/state" });
      this._serverVersion = typeof data.version === "string" &&
        /^\d+\.\d+\.\d+$/.test(data.version) ? data.version : null;
      this._operation = (data.operations || [])[0] || null;
      this._observeCountdown(this._operation);
      this._measurement = data.measurement || null;
      this._suite = data.suite || null;
      this._projects = Array.isArray(data.projects) ? data.projects : [];
      this._pickerBatchPosition = Number.isInteger(data.picker_batch_position)
        ? data.picker_batch_position : this._projects.length;
      this._settings = data.settings || this._settings;
      this._cpuStatus = data.cpu_status || this._cpuStatus;
      this._gitConfigured = data.git_configured === true;
      this._centralExport = data.central_export || this._centralExport;
      this._diagnosticsExportReady = data.diagnostics_export_ready === true;
      if (Number.isInteger(data.deployment_log_count) && data.deployment_log_count >= 0 && data.deployment_log_count <= 8)
        this._deploymentLogCount = data.deployment_log_count;
      if (this._archiveCheckState === "idle" && this._centralExport.configured) {
        // Stored on HA, but not necessarily reverified this browser session.
        this._archiveCheckState = "stored";
      }
      this._gitReadConfigured = data.git_read_configured === true;
      // The saved picker order is the default view on a fresh device.
      // Position zero means the synthetic Sammelupdate row is first.
      // Do not change an explicit selection later or auto-authorize a batch.
      if (!this._selectedMainRepo && !this._mainBatchMode &&
          this._pickerBatchPosition === 0) {
        this._mainBatchMode = true;
        this._batchRunSelected = new Set(this._projects
          .filter(p=>p.active!==false && p.batch_preselect!==false &&
            !this._isOwnBatchUpdate(p)).map(p=>p.repository));
      }
      // On a freshly opened device, prefer the single HA-held prepared session
      // over an arbitrary first project; never silently override user selection.
      if (!this._selectedMainRepo && !this._mainBatchMode && this._serverVersion === DRA_V2_UI_VERSION) {
        try {
          const active = await this._hass.callWS({
            type:"deploy_relay_v2_dev/deployment/sessions",
          });
          if (active?.schema === "dra-v2-sessions.v1" &&
              Array.isArray(active.sessions) && active.sessions.length <= 32) {
            const prepared = active.sessions.filter(item=>item.prepared === true &&
              this._projects.some(project => project.active !== false &&
                project.repository === item.repository));
            if (prepared.length === 1) this._selectedMainRepo = prepared[0].repository;
          }
        } catch (_error) {
          // A transient session discovery error does not break ordinary V2.
        }
      }
      if (this._serverVersion === DRA_V2_UI_VERSION) {
        await this._pollInstallation();
        // Completed V2 audit records persist across HA restarts; load only as history.
        await this._refreshInstallAudit();
      }
      this._gitAvailable = data.git_available === true;
      this._error = "";
      // Reconcile the latest HA-owned read job on every state refresh.
      // A second device must see jobs started or completed elsewhere.
      const sourceSyncDue = !this._sourceJobRestored || (++this._sourceSyncTick % 4 === 0);
      this._sourceJobRestored = true;
      if (sourceSyncDue && !this._sourceJobPolling) await this._pollSourceJob(true);
      if (sourceSyncDue && this._selectedMainRepo) {
        await this._syncController(this._selectedMainRepo);
        await this._restoreServerPreparation(this._selectedMainRepo);
      }
    } catch (_error) {
      // Never continue presenting a previously verified HA version as current
      // when the actual server cannot be reached.
      this._serverVersion = null;
      this._error = "Status konnte nicht geladen werden. Verbindung prüfen.";
    } finally {
      this._busy = false;
      if (this.isConnected) this._render();
      const current = this._selectedMainRepo || this._projects.find(p=>p.active !== false)?.repository;
      if (current && !this._mainBatchMode && this._serverVersion === DRA_V2_UI_VERSION &&
          this._sourceChoicesLoadedFor !== current && !this._sourceChoicesBusy) {
        this._selectedMainRepo = current;
        void this._loadSourceChoices();
      }
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

  _formatHistoryTime(value) {
    if (typeof value !== "string" || !value.trim()) return "Zeit unbekannt";
    // Server timestamps remain UTC; render history consistently in German local time.
    const parsed = new Date(value);
    if (!Number.isFinite(parsed.getTime())) return "Zeit unbekannt";
    return new Intl.DateTimeFormat("de-DE", {
      timeZone: "Europe/Berlin", day: "2-digit", month: "2-digit", year: "numeric",
      hour: "2-digit", minute: "2-digit", second: "2-digit",
      timeZoneName: "short",
    }).format(parsed);
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
      // A successfully saved secret must not remain in the input across re-renders.
      const readTokenInput = this.shadowRoot?.querySelector("#source-read-token");
      if (readTokenInput) readTokenInput.value = "";
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

  async _toggleDeploymentLogs() {
    if (this._deploymentLogsBusy) return;
    this._deploymentLogsOpen = !this._deploymentLogsOpen;
    this._deploymentLogsConfirm = false;
    this._render();
    if (this._deploymentLogsOpen) {
      this._historyRefreshStatus = "Wird geladen …";
      this._historyRefreshDetail = "Quellprotokolle und Auftragshistorie werden geladen.";
      this._historyRefreshTone = "busy";
      if (this.isConnected) this._render();
      const logsOk = await this._refreshDeploymentLogs();
      const historyOk = await this._refreshSourceJobHistory();
      this._setHistoryRefreshResult(logsOk && historyOk);
    }
  }

  _setHistoryRefreshResult(ok) {
    this._historyRefreshStatus = ok ? "Aktualisiert" : "Abruf fehlgeschlagen";
    this._historyRefreshDetail = ok
      ? "Quellprotokolle und Auftragshistorie erfolgreich vom Server geladen."
      : "Quellprotokolle oder Auftragshistorie konnten nicht geladen werden. Bitte erneut versuchen.";
    this._historyRefreshTone = ok ? "success" : "error";
    if (this.isConnected) this._render();
  }

  async _refreshHistoryManually() {
    if (!this._hass || !this._deploymentLogsOpen ||
        this._historyRefreshBusy || this._deploymentLogsBusy) return;
    this._historyRefreshBusy = true;
    this._historyRefreshStatus = "Wird aktualisiert …";
    this._historyRefreshDetail = "Quellprotokolle und Auftragshistorie werden aktualisiert.";
    this._historyRefreshTone = "busy";
    if (this.isConnected) this._render();
    try {
      const [logsOk, historyOk] = await Promise.all([
        this._refreshDeploymentLogs(),
        this._refreshSourceJobHistory(),
      ]);
      this._setHistoryRefreshResult(logsOk && historyOk);
    } catch (_error) {
      this._setHistoryRefreshResult(false);
    } finally {
      this._historyRefreshBusy = false;
      if (this.isConnected) this._render();
    }
  }

  async _refreshInstallAudit() {
    if (!this._hass) return false;
    try {
      const result = await this._hass.callWS({type:"deploy_relay_v2_dev/deployment/audit"});
      if (result?.schema !== "dra-v2-deployment-audit.v1" ||
          !Array.isArray(result.records) || result.records.length > 256 ||
          result.count !== result.records.length) throw Error("invalid audit");
      this._installAuditRecords = result.records;
      this._auditStatus = result.count + " echte Installationsereignisse geladen.";
      return true;
    } catch (_error) {
      this._installAuditRecords = [];
      this._auditStatus = "Installationsergebnisse derzeit nicht abrufbar.";
      return false;
    } finally {
      if (this.isConnected) this._render();
    }
  }
  async _exportAuditToGit() {
    if (!this._hass || this._auditExportBusy ||
        (this._installAuditRecords.length === 0 && !this._centralExport.pending)) return;
    if (this._centralExport.configured !== true ||
        this._centralExport.repository !== "TheDaimos/Project-Log-And-Export") {
      this._auditStatus = "Bitte zuerst das private zentrale Git-Archiv einrichten.";
      this._render();
      return;
    }
    this._auditExportBusy = true;
    this._auditStatus = "Bereinigter Audit-Bericht wird privat exportiert …";
    this._render();
    try {
      const response = await this._hass.callWS({
        type:"deploy_relay_v2_dev/deployment/audit/export",
      });
      if (response?.repository !== "TheDaimos/Project-Log-And-Export" ||
          !/^[a-f0-9]{32}$/.test(response.export_id || "") ||
          !/^[a-f0-9]{40}$/.test(response.commit_sha || "") ||
          !String(response.path || "").startsWith("exports/deploy-relay-agent-v2/") ||
          !String(response.file_url || "").startsWith("https://github.com/" + this._centralExport.repository + "/blob/")) {
        throw Error("invalid audit export receipt");
      }
      this._centralExport = {...this._centralExport,pending:false};
      this._auditStatus = response.pending_retried ?
        "Ausstehender privater Bericht erneut erfolgreich übertragen. Audit bei Bedarf erneut exportieren." :
        "Audit erfolgreich in das private Git-Archiv übertragen · " + response.export_id;
    } catch (_error) {
      this._auditStatus = "Privater Audit-Export nicht bestätigt. Keine weitere Installation erforderlich; Export später erneut versuchen.";
    } finally {
      this._auditExportBusy = false;
      this._render();
    }
  }

  _downloadAuditJSON() {
    if (!this._installAuditRecords.length) return;
    const payload = JSON.stringify({
      schema:"dra-v2-deployment-audit-export.v1",
      created_at:new Date().toISOString(),
      records:this._installAuditRecords,
    },null,2);
    const blob = new Blob([payload],{type:"application/json;charset=utf-8"});
    const url = URL.createObjectURL(blob);
    try {
      const link = document.createElement("a");
      link.href = url;
      link.download = "dra-v2-audit-" + new Date().toISOString().slice(0,10) + ".json";
      link.click();
    } finally {
      setTimeout(() => URL.revokeObjectURL(url),1000);
    }
    this._auditStatus = "Audit-JSON-Download gestartet.";
    this._render();
  }
  async _refreshDeploymentLogs() {
    if (!this._hass || this._deploymentLogsBusy) return false;
    this._deploymentLogsBusy = true;
    this._deploymentLogsStatus = "Diagnose wird geladen …";
    this._render();
    try {
      const result = await this._hass.callWS({type:"deploy_relay_v2_dev/deployment/logs"});
      if (result?.schema !== "dra-v2-dev-deployment-logs.v1" ||
          result.installation_enabled !== false || !Array.isArray(result.records) ||
          result.records.length > 8 || result.count !== result.records.length) throw new Error("invalid deployment logs");
      this._deploymentLogs = result.records;
      this._deploymentLogCount = result.count;
      this._deploymentLogsStatus = result.records.length ?
        "Letzte Quellprüfungen (ohne Repositorynamen oder Zugangsdaten)." :
        "Noch keine Quellprüfung protokolliert. Zuerst die Vorschau ausführen.";
      return true;
    } catch (_error) {
      this._deploymentLogs = [];
      this._deploymentLogsStatus = "Protokolle derzeit nicht abrufbar.";
      return false;
    } finally {
      this._deploymentLogsBusy = false;
      if (this.isConnected) this._render();
    }
  }

  async _refreshSourceJobHistory() {
    if (!this._hass) return false;
    try {
      const result = await this._hass.callWS({
        type:"deploy_relay_v2_dev/projects/source_job/history",
      });
      if (result?.schema !== "dra-v2-source-job-history-result.v1" ||
          result.installation_enabled !== false ||
          result.resume_allowed !== false ||
          result.source_preview_saved !== false ||
          !Array.isArray(result.records) || result.records.length > 8 ||
          result.records.some(record =>
            !/^[a-f0-9]{32}$/.test(record.operation_id || "") ||
            !["queued","success","failed","interrupted"].includes(record.status) ||
            record.installation_enabled !== false ||
            record.resume_allowed !== false ||
            record.source_preview_saved !== false)) {
        throw new Error("invalid source history");
      }
      this._sourceJobHistory = result.records;
      this._sourceJobHistoryStatus = result.records.length ?
        "Gespeicherte Auftragszustände; alte Ergebnisse sind nicht erneut freigegeben." :
        "Noch keine gespeicherte Auftragshistorie.";
      if (this.isConnected) this._render();
      return true;
    } catch (_error) {
      this._sourceJobHistory = [];
      this._sourceJobHistoryStatus = "Auftragshistorie derzeit nicht abrufbar.";
      if (this.isConnected) this._render();
      return false;
    }
  }

  async _clearDeploymentLogs() {
    if (!this._hass || this._deploymentLogsBusy || !this._deploymentLogsConfirm ||
        !this._deploymentLogs.length) return;
    const expected = this._deploymentLogs[0]?.run_id;
    if (!/^[a-f0-9]{32}$/.test(expected || "")) return;
    this._deploymentLogsBusy = true;
    this._deploymentLogsStatus = "Temporäre Protokolle werden geleert …";
    this._render();
    try {
      const report = await this._hass.callWS({
        type:"deploy_relay_v2_dev/deployment/logs/clear",
        confirm:true, expected_run_id:expected,
      });
      if (report?.remaining !== 0 || report.archive_unchanged !== true ||
          report.installation_enabled !== false ||
          !Number.isInteger(report.cleared) || report.cleared < 1 ||
          report.cleared > 8) throw new Error("invalid clear receipt");
      this._deploymentLogs = [];
      this._deploymentLogCount = 0;
      this._deploymentLogsConfirm = false;
      this._deploymentLogsStatus = "Temporäre Logs geleert. Private Git-Exporte bleiben erhalten.";
    } catch (_error) {
      this._deploymentLogsStatus = "Protokolle konnten nicht geleert werden. Bitte erneut laden.";
      this._deploymentLogsConfirm = false;
    } finally {
      this._deploymentLogsBusy = false;
      if (this.isConnected) this._render();
    }
  }

  async _deploymentLogsAction(kind) {
    if (!this._hass || this._deploymentLogsBusy ||
        (!this._deploymentLogs.length && !(kind === "git" && this._centralExport.pending)) ||
        !["git","json","copy","g2_prepare"].includes(kind)) return;
    if (kind === "g2_prepare" && (!this._g2RetryTestConfirm ||
        this._centralExport.pending)) return;
    if ((kind === "git" || kind === "g2_prepare") &&
        (this._centralExport.configured !== true ||
        this._centralExport.repository !== "TheDaimos/Project-Log-And-Export")) {
      this._deploymentLogsStatus = "Privates Project-Log-And-Export unter Diagnose & Einstellungen einrichten.";
      this._render();
      return;
    }
    this._deploymentLogsBusy = true;
    this._deploymentLogsStatus = kind === "g2_prepare"
      ? "G2 prüft das private Archiv und bereitet den Bericht nur lokal vor …"
      : kind === "git" ? "Privater Git-Export läuft …"
      : "Bereinigtes JSON wird erstellt …";
    this._render();
    try {
      const result = await this._hass.callWS({
        type: kind === "git" || kind === "g2_prepare"
          ? "deploy_relay_v2_dev/deployment/logs/export"
          : "deploy_relay_v2_dev/deployment/logs/download",
        ...(kind === "g2_prepare" ? {g2_prepare:true,g2_confirm:true} : {}),
      });
      if (kind === "g2_prepare") {
        if (result?.pending_prepared !== true || result.pending !== true ||
            !/^[0-9a-f]{32}$/.test(result.export_id || "")) {
          throw new Error("G2 export queue not confirmed");
        }
        this._centralExport = {...this._centralExport,pending:true};
        this._g2RetryTestConfirm = false;
        this._deploymentLogsStatus =
          "G2-Test: Bereinigter Diagnosebericht mit Export-ID " + result.export_id +
          " nur lokal gesichert. Jetzt „Gespeicherten Git-Export erneut senden“ auswählen.";
      } else if (kind === "git") {
        const eid = result?.export_id;
        if (result.repository !== this._centralExport.repository ||
            !/^[0-9a-f]{32}$/.test(eid || "") ||
            !/^[0-9a-f]{40}$/.test(result.commit_sha || "") ||
            !/^exports\/deploy-relay-agent-v2\/[0-9]{4}-[0-9]{2}\/diagnostics\/.+__diagnostics__[0-9a-f]{32}\.json$/.test(result.path || "") ||
            !String(result.file_url || "").startsWith("https://github.com/" + result.repository + "/blob/") ||
            typeof result.pending_retried !== "boolean") {
          throw new Error("unconfirmed private export");
        }
        this._deploymentLogsStatus = result.pending_retried ?
          "Zuvor gesicherten Export erneut nach Git übertragen · ID " + eid +
          ". Für das aktuelle Prüfprotokoll Export nach Git erneut wählen." :
          "Aktuelles Prüfprotokoll privat exportiert · Export-ID " + eid;
        this._centralExport = {...this._centralExport, pending:false};
      } else {
        if (!result || result.application_id !== "deploy-relay-agent-v2" ||
            result.mime_type !== "application/json" ||
            !/^[0-9a-f]{32}$/.test(result.export_id || "") ||
            typeof result.content !== "string" || result.content.length > 8192 ||
            !/^20[0-9]{2}-[0-9]{2}-[0-9T-]+Z__deploy-relay-agent-v2__0\.1\.[0-9]{1,3}__diagnostics__[0-9a-f]{32}\.json$/.test(result.filename || "")) {
          throw new Error("invalid local diagnostic");
        }
        const parsed = JSON.parse(result.content);
        if (parsed?.application?.id !== result.application_id ||
            parsed?.export?.exportId !== result.export_id ||
            parsed?.snapshot?.schema !== "dra-v2-dev-git-source-diagnostic.v1") {
          throw new Error("invalid diagnostic payload");
        }
        if (kind === "json") {
          const blob = new Blob([result.content], {type:"application/json;charset=utf-8"});
          const url = URL.createObjectURL(blob);
          try {
            const link = document.createElement("a");
            link.href = url;
            link.download = result.filename;
            link.click();
          } finally {
            setTimeout(() => URL.revokeObjectURL(url), 1000);
          }
          this._deploymentLogsStatus = "JSON-Download gestartet.";
        } else {
          // The clipboard can be unavailable without HTTPS/gesture permissions.
          if (navigator.clipboard?.writeText) {
            await navigator.clipboard.writeText(result.content);
          } else {
            const field = document.createElement("textarea");
            field.value = result.content;
            field.style.position = "fixed"; field.style.opacity = "0";
            document.body.appendChild(field);
            try {
              field.select();
              if (!document.execCommand("copy")) throw new Error("clipboard denied");
            } finally {
              field.remove();
            }
          }
          this._deploymentLogsStatus = "Bereinigtes JSON in die Zwischenablage kopiert.";
        }
      }
    } catch (_error) {
      this._deploymentLogsStatus = kind === "g2_prepare"
        ? "G2-Testvorbereitung nicht bestätigt. Vorhandene Daten bitte unverändert lassen."
        : kind === "git" ?
        "Git-Übertragung fehlgeschlagen. Ein vorbereiteter Bericht bleibt lokal erhalten. " +
        "Erneut tippen, um ihn zuerst zu senden. JSON-Download bleibt verfügbar." :
        "JSON oder Zwischenablage nicht verfügbar. Bitte erneut versuchen.";
    } finally {
      this._deploymentLogsBusy = false;
      if (this.isConnected) this._render();
    }
  }

  _scheduleSourceJobPoll() {
    if (this._sourceJobTimer !== null) clearTimeout(this._sourceJobTimer);
    this._sourceJobTimer = null;
    if (this.isConnected && this._sourceBusy) {
      this._sourceJobTimer = setTimeout(() => this._pollSourceJob(), this._sourceJobRetryMs);
    }
  }

  async _pollSourceJob(latest = false) {
    if (!this._hass || this._sourceJobPolling) return;
    this._sourceJobPolling = true;
    try {
      const data = await this._hass.callWS({
        type:"deploy_relay_v2_dev/projects/source_job/status",
        ...(!latest && this._sourceJobId ? {operation_id:this._sourceJobId} : {}),
      });
      if (!data || data.schema !== "dra-v2-source-preview-job-status.v1" ||
          data.installation_enabled !== false) throw new Error("invalid source job status");
      this._sourceJobRetryMs = 1200;
      const job = data.job;
      if (!job) {
        const missingId = this._sourceJobId;
        this._sourceJobId = null;
        this._sourceBusy = false;
        if (missingId) {
          this._sourcePreview = null;
          this._deploymentPreviewRef = null;
          this._sourceMessage = "Alter Auftrag nicht mehr aktiv. Nach HA-Neustart ist eine neue Quellprüfung erforderlich.";
        }
        await this._refreshSourceJobHistory();
        return;
      }
      if (job.schema !== "dra-v2-source-preview-job.v1" ||
          job.installation_enabled !== false ||
          !/^[a-f0-9]{32}$/.test(job.operation_id || "") ||
          !["queued","running","success","failed","interrupted"].includes(job.status) ||
          typeof job.repository !== "string" || typeof job.ref !== "string") {
        throw new Error("invalid source job");
      }
      // Only locally started jobs own this browser reference. Remote discovery
      // must not pin future checks to an unrelated completed operation.
      if (!this._sourceJobId) this._sourceJobId = job.operation_id;
      if (!latest && this._sourceJobId !== job.operation_id) throw new Error("different source job");
      if (typeof job.connection_test !== "undefined" &&
          typeof job.connection_test !== "boolean") throw new Error("invalid test mode");
      this._sourceConnectionTest = job.connection_test === true;
      if (!this._selectedMainRepo &&
          this._projects.some(project => project.repository.toLowerCase() === job.repository.toLowerCase())) {
        this._selectedMainRepo = job.repository;
        this._mainSourceRef = job.ref;
      }
      const currentRepo = this._view === "main" ?
        (this._selectedMainRepo || this._projects.find(p=>p.active !== false)?.repository) :
        this._sourceRepository;
      const currentRef = this._view === "main" ? this._mainSourceRef.trim() :
        (this.shadowRoot?.querySelector("#source-ref")?.value?.trim() || "");
      const matches = currentRepo?.toLowerCase() === job.repository.toLowerCase() &&
        currentRef === job.ref;
      const serverRunning = job.status === "queued" || job.status === "running";
      this._sourceBusy = serverRunning && (matches || (!latest && !!this._sourceJobId));
      if (matches) {
        this._sourceRepository = job.repository;
        const identity = job.operation_id.slice(0, 12);
        if (this._sourceBusy) {
          this._sourceMessage = this._sourceConnectionTest
            ? (job.stage === "connection_test_wait"
              ? "G2-Verbindungstest · HA hält den Leseauftrag 60 Sekunden offen · Auftrag " + identity
              : "G2-Verbindungstest · HA führt die echte Quellprüfung aus · Auftrag " + identity)
            : "HA prüft die Quelle serverseitig · Auftrag " + identity;
        } else if (job.status === "success" &&
            job.result?.sources_verified === true &&
            job.result?.installation_enabled === false &&
            job.result?.repository?.toLowerCase() === job.repository.toLowerCase()) {
          this._sourcePreview = job.result;
          if (this._view === "main") {
            const changed = ["add","change","remove"].reduce((n,k)=>
              n + (Array.isArray(job.result[k]) ? job.result[k].length : 0),0);
            this._sourceHeadMessage = changed === 0
              ? "Aktuell · Keine relevanten Dateiänderungen"
              : "Änderungen vorhanden · " + changed + " betroffene Dateien";
          }
          this._deploymentPreviewRef = this._view === "main" ? job.ref : null;
          this._sourceMessage = (this._sourceConnectionTest
            ? "G2-Verbindungstest abgeschlossen · Auftrag "
            : "Quellprüfung abgeschlossen · Auftrag ") + identity +
            ". Installation weiterhin gesperrt.";
        } else {
          this._sourcePreview = null;
          this._deploymentPreviewRef = null;
          this._sourceHeadMessage = "Prüfung unvollständig · Dateistand nicht bestätigt";
          this._sourceMessage = "Quellprüfung konnte nicht abgeschlossen werden · Auftrag "
            identity + ". Details unter Logs.";
        }
      }
      if (!matches && latest && serverRunning && this._view === "main") {
        this._sourceMessage = "Ein anderes Projekt wird auf Home Assistant geprüft: " +
          job.repository + ". Dieser Browser startet keinen zusätzlichen Prüfauftrag.";
      }
      if (!this._sourceBusy && this._deploymentLogsOpen) await this._refreshDeploymentLogs();
    } catch (_error) {
      // Losing a browser connection never cancels the HA-owned job.
      this._sourceMessage = "Verbindung zur Auftragsanzeige unterbrochen. HA-Auftrag bleibt unabhängig.";
      this._sourceBusy = true;
      this._sourceJobRetryMs = Math.min(10000, this._sourceJobRetryMs * 2);
    } finally {
      this._sourceJobPolling = false;
      if (this.isConnected) this._render();
      this._scheduleSourceJobPoll();
    }
  }

  async _loadSourceChoices() {
    const repository = this._selectedMainRepo;
    if (this._mainBatchMode || !repository || this._sourceChoicesBusy || !this._hass) return;
    this._sourceChoicesBusy = true;
    this._sourceChoicesMessage = "Git-Zweige und Tags werden geladen …";
    this._sourceChoicesRetryCount = this._sourceChoicesRetryCount || 0;
    this._render();
    try {
      const result = await this._hass.callWS({
        type:"deploy_relay_v2_dev/projects/source_choices", repository,
      });
      if (result?.schema !== "dra-v2-source-choices.v1" ||
          result.repository !== repository || !Array.isArray(result.choices) ||
          result.choices.length > 200 || typeof result.default_ref !== "string" ||
          !result.recommended || typeof result.recommended.ref !== "string" ||
          !/^[a-f0-9]{40}$/.test(result.recommended.commit || "") ||
          result.choices.some(choice => !["branch","tag"].includes(choice.kind) ||
            typeof choice.ref !== "string" || !/^[a-f0-9]{40}$/.test(choice.commit))) {
        throw new Error("invalid source choices");
      }
      if (this._selectedMainRepo !== repository || this._mainBatchMode) return;
      this._sourceChoices = result;
      this._sourceChoicesRetryCount = 0;
      this._sourceHeadMessage = "";
      this._sourceChoicesLoadedFor = repository;
      // Server jobs may have restored "main" before the project preference
      // arrived. It is a default, not a manual selection. Never override a
      // deliberate reference or a prepared/running installation.
      const selectedIsDefault = !this._mainSourceRef.trim() ||
        this._mainSourceRef.trim() === result.default_ref;
      const activeInstall = this._installJobs.some(job=>
        job.project_key === this._projects.find(p=>p.repository===repository)?.project_id &&
        ["queued","running","waiting_for_resource","cancel_requested"].includes(job.status));
      const oldDefaultPrepared = this._installPreparation?.repository === repository &&
        this._installPreparation.source_ref === result.default_ref &&
        result.recommended.ref !== result.default_ref;
      if (result.recommended.explicit && selectedIsDefault &&
          !this._manualSourceRef && (!this._installPreparation || oldDefaultPrepared) &&
          !activeInstall) {
        const refChanged = this._mainSourceRef.trim() !== result.recommended.ref;
        this._mainSourceRef = result.recommended.ref;
        // A previous HA preparation for main cannot authorize deploy/dev.
        // It may remain on the server until expiry but is never presented as
        // a valid approval for the newly recommended branch.
        if (oldDefaultPrepared) this._installPreparation = null;
        if (refChanged || oldDefaultPrepared) {
          this._automaticSourceCheckFor = null;
          this._sourcePreview = null;
          this._sourceHead = null;
          this._deploymentPreviewRef = null;
        }
        this._sourceMessage = refChanged
          ? "Empfohlener Entwicklungszweig " + result.recommended.ref +
            " übernommen. Quellprüfung wird neu durchgeführt."
          : "Empfohlener Entwicklungszweig bestätigt.";
      }
      await this._syncController(repository);
      await this._restoreServerPreparation(repository);
      if (this._selectedMainRepo === repository && !this._installPreparation && this._automaticSourceCheckFor !== repository) {
        this._automaticSourceCheckFor = repository;
        // Full read-only inventory comparison, not merely a commit check.
        void this._sourceCheck({dataset:{repo:repository}}, false, true);
      }
      this._sourceChoicesMessage = result.limited
        ? "GitHub zeigt maximal 100 Zweige und 100 Tags. Weitere Referenzen manuell eingeben."
        : "Git-Zweige und Tags geladen. Auswahl verändert noch keine Dateien.";
    } catch (_error) {
      if (this._selectedMainRepo !== repository || this._mainBatchMode) return;
      if (_error?.code === "busy") {
        this._sourceChoicesMessage = "Quellprüfung läuft; Zweige werden anschließend erneut abgefragt.";
        this._sourceHeadMessage = "Quellenabruf momentan belegt – GitHub-Ausfall nicht bestätigt.";
        const retries = this._sourceChoicesRetryCount || 0;
        if (retries < 5 && this.isConnected) {
          this._sourceChoicesRetryCount = retries + 1;
          setTimeout(() => {
            if (this.isConnected && this._selectedMainRepo === repository &&
                !this._sourceChoicesBusy) void this._loadSourceChoices();
          }, 2000 + retries * 1500);
        }
        return;
      }
      this._sourceChoices = null;
      this._sourceChoicesLoadedFor = repository;
      this._sourceChoicesMessage = "Quellenauswahl nicht verfügbar. Manuelle Eingabe bleibt möglich.";
      this._sourceHeadMessage = "Automatische Prüfung nicht möglich · GitHub-Quelle konnte nicht geladen werden.";
    } finally {
      this._sourceChoicesBusy = false;
      if (this.isConnected) this._render();
    }
  }

  _applySourceChoice(ref) {
    if (typeof ref !== "string" || ref.length > 100) return;
    this._manualSourceRef = true;
    this._mainSourceRef = ref;
    this._sourcePreview = null;
    this._sourceHead = null;
    this._sourceHeadMessage = "";
    this._deploymentPreviewRef = null;
    this._sourceMessage = "Git-Referenz ausgewählt. Quelle aktualisieren und Vorschau neu berechnen.";
    this._render();
  }

  async _refreshSourceHead() {
    const project = this._projects.find(p=>p.repository===this._selectedMainRepo);
    if (!this._hass || !project || this._mainBatchMode || this._sourceHeadBusy ||
        this._sourceBusy || this._installBusy || this._installPreparation ||
        this._serverVersion !== DRA_V2_UI_VERSION) return;
    this._sourceHeadBusy = true;
    this._sourceHeadMessage = "Neuester Git-Commit wird abgefragt …";
    this._render();
    try {
      const ref = this._mainSourceRef.trim();
      const result = await this._hass.callWS({
        type:"deploy_relay_v2_dev/projects/source_head",
        repository:project.repository,ref,
      });
      if (result?.schema !== "dra-v2-source-head.v1" ||
          result.repository !== project.repository || !/^[a-f0-9]{40}$/.test(result.commit || "") ||
          typeof result.ref !== "string") throw Error("invalid source head");
      // Do not apply a response if project/ref changed while awaiting GitHub.
      if (this._selectedMainRepo !== project.repository ||
          this._mainSourceRef.trim() !== ref) return;
      const previous = this._sourcePreview?.repository === project.repository
        ? this._sourcePreview : null;
      const priorHead = this._sourceHead?.repository === project.repository &&
        this._sourceHead?.ref === result.ref ? this._sourceHead.commit : null;
      const installedCommit = this._installJob?.project_key === project.project_id
        ? this._installJob.source_commit : null;
      const knownCommit = previous?.source_commit || priorHead || installedCommit;
      this._sourceHead = result;
      if (knownCommit && knownCommit !== result.commit) {
        this._releaseCompletedDeployment(project);
        this._sourcePreview = null;
        this._deploymentPreviewRef = null;
        this._sourceHeadMessage = "Neuer Git-Commit erkannt: " + result.commit.slice(0,12) +
          ". Alte Vorschau ungültig – neuen Durchlauf mit Vorschau beginnen.";
      } else {
        this._sourceHeadMessage = knownCommit === result.commit
          ? "Git-Quelle unverändert (" + result.commit.slice(0,12) +
            "). Bestehende Vorschau bleibt gültig."
          : "Aktueller Git-Commit: " + result.commit.slice(0,12) +
            ". Für Dateivergleich neue Vorschau berechnen.";
      }
    } catch (_error) {
      this._sourceHeadMessage = "Git-Quellstand nicht abrufbar. Keine Installationsfreigabe erteilt.";
    } finally {
      this._sourceHeadBusy = false;
      this._render();
    }
  }

  async _sourceCheck(button, connectionTest = false, automatic = false) {
    if (!button || !this._hass || this._sourceBusy) return;
    if (connectionTest && this._serverVersion !== G2_TEST_PYTHON_VERSION) {
      this._sourceMessage = "G2-Test nicht startbar: Python-Laufzeit " +
        (this._serverVersion || "nicht ermittelt") + ", benötigt " +
        G2_TEST_PYTHON_VERSION + ". Keine Quellprüfung gestartet.";
      this._render();
      return;
    }
    const repository = button.dataset.repo;
    // A new ordinary preview explicitly begins the next cycle; G2 never does.
    if (!connectionTest && !automatic && this._view === "main") {
      const selected = this._projects.find(p=>p.repository===repository);
      this._releaseCompletedDeployment(selected);
    }
    const ref = this._view === "main" ? this._mainSourceRef.trim() :
      (this.shadowRoot?.querySelector("#source-ref")?.value?.trim() || "");
    this._sourceRepository = repository;
    this._sourceBusy = true;
    this._sourcePreview = null;
    this._sourceHead = null;
    this._sourceHeadMessage = "";
    this._deploymentPreviewRef = null;
    this._sourceJobId = null;
    this._sourceConnectionTest = connectionTest === true;
    this._sourceMessage = this._sourceConnectionTest
      ? "G2-Verbindungstest wird vorbereitet (60 Sekunden) …"
      : "HA startet die schreibgeschützte Quellprüfung …";
    this._render();
    try {
      const job = await this._hass.callWS({
        type:"deploy_relay_v2_dev/projects/source_job/start", repository, ref,
        connection_test: this._sourceConnectionTest,
      });
      if (job?.schema !== "dra-v2-source-preview-job.v1" ||
          job.installation_enabled !== false ||
          !/^[a-f0-9]{32}$/.test(job.operation_id || "")) {
        throw new Error("invalid source job admission");
      }
      this._sourceJobId = job.operation_id;
      await this._pollSourceJob();
    } catch (_error) {
      this._sourceMessage = this._sourceConnectionTest
        ? "G2-Teststart vom HA-Server nicht bestätigt (Python-Laufzeit " +
          (this._serverVersion || "unbekannt") + "). Keine Freigabe."
        : "Quellprüfung nicht startbar. Die Installation bleibt gesperrt.";
      this._sourceBusy = false;
    } finally {
      if (this.isConnected) this._render();
    }
  }

  async _checkDraftProjectConnection() {
    // A just-entered repository and optional token are checked before storage.
    // The token is a local variable, never persistent state or visible feedback.
    if (!this._hass || this._connectionBusy || this._projectBusy ||
        this._sourceBusy || this._checkAllBusy) return;
    const input = this.shadowRoot?.querySelector("#manage-repository");
    const secretInput = this.shadowRoot?.querySelector("#manage-token");
    const repository = input?.value.trim() || "";
    const token = secretInput?.value || "";
    const managed = this._projects.find(p=>p.repository===this._projectSettingsRepo);
    if (!repository || !/^[A-Za-z0-9_.-]{1,100}\/[A-Za-z0-9_.-]{1,100}$/.test(repository)) {
      this._draftConnectionCheck = {repository,status:"failure",
        message:"Bitte zuerst eine gültige Repositoryadresse eingeben."};
      this._render();
      return;
    }
    if (managed && managed.repository.toLowerCase()===repository.toLowerCase() && !token) {
      await this._checkProjectConnection(managed.repository);
      return;
    }
    this._connectionBusy = true;
    this._draftConnectionCheck = {repository,status:"checking",message:"Verbindung wird geprüft …"};
    this._render();
    try {
      const response = await this._hass.callWS({
        type:"deploy_relay_v2_dev/projects/connection_check",
        repository,draft:true,...(token ? {token} : {}),
      });
      if (!response || response.repository?.toLowerCase()!==repository.toLowerCase()) {
        throw Error("unexpected repository identity");
      }
      const message = response.connected === true ?
        "Verbindung erfolgreich · " +
          (response.private ? "Privates" : "Öffentliches") + " Repository · " +
          (response.authenticated ? "Token geprüft" : "ohne Token erreichbar") :
        "Verbindung fehlgeschlagen · " +
          (response.reason || "Repository oder Token prüfen.");
      this._draftConnectionCheck = {repository,
        status:response.connected === true ? "success" : "failure",message};
    } catch (_error) {
      this._draftConnectionCheck = {repository,status:"failure",
        message:"Verbindung nicht bestätigt. Repository, Token oder GitHub-Erreichbarkeit prüfen."};
    } finally {
      this._connectionBusy = false;
      if (this.isConnected) this._render();
    }
  }

  async _saveNewProject() {
    if (!this._hass || this._projectBusy || this._projectSettingsRepo !== "__new__") return;
    const root=this.shadowRoot;
    const repository=root?.querySelector("#manage-repository")?.value.trim() || "";
    const name=root?.querySelector("#manage-name")?.value.trim() || "";
    const note=root?.querySelector("#manage-note")?.value || "";
    const active=root?.querySelector("#manage-active")?.checked === true;
    const access_mode=root?.querySelector("#manage-access-mode")?.value || "read_only";
    const token=root?.querySelector("#manage-token")?.value || "";
    this._projectBusy=true;
    this._projectMessage="Projekt wird gespeichert …";
    this._render();
    let registered=false;
    try {
      const created=await this._hass.callWS({
        type:"deploy_relay_v2_dev/projects/add",
        repository,name,note,active,access_mode,
      });
      if (!Array.isArray(created?.projects) ||
          !created.projects.some(p=>p.repository.toLowerCase()===repository.toLowerCase())) {
        throw Error("project was not confirmed");
      }
      registered=true;
      this._projects=created.projects;
      if (token) {
        const saved=await this._hass.callWS({
          type:"deploy_relay_v2_dev/projects/token",repository,token,
        });
        if (!Array.isArray(saved?.projects)) throw Error("token save not confirmed");
        this._projects=saved.projects;
      }
      this._draftConnectionCheck=null;
      this._projectSettingsRepo=null;
      this._batchSelection=null;
      this._batchPreview=null;
      this._projectMessage=token ?
        "Projekt und GitHub-Token gespeichert." : "Projekt gespeichert.";
    } catch (_error) {
      this._projectMessage=registered ?
        "Projekt gespeichert, Token konnte nicht bestätigt werden. In den Projekteinstellungen erneut speichern." :
        "Projekt konnte nicht angelegt werden. Eingaben prüfen.";
      if (registered) this._projectSettingsRepo=repository;
    } finally {
      this._projectBusy=false;
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
      if (report.connected === true && report.read_verified === true) {
        const visibility = report.private ? "Privates Repository" : "Öffentliches Repository";
        const auth = report.authenticated ? "mit Token" : "ohne Token";
        const rights = report.advertised_push === true ? " · GitHub meldet Schreibberechtigung (nicht getestet)" :
          report.advertised_push === false ? " · GitHub meldet nur Lesezugriff" : "";
        this._sourceChecks.set(repository, {status:"success",access_level:report.access_level === "RW" ? "RW" : "RO",
          message:"Lesezugriff bestätigt · " + visibility + " · " + auth + rights});
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
        this._checkAllProgress = `Verbindungsprüfung: ${checked} von ${repositories.length} · ${online} geprüft, ${offline} fehlgeschlagen.`;
        if (this.isConnected) this._render();
      }
      this._checkAllProgress = `Prüfung abgeschlossen: ${online} mit Lesezugriff, ${offline} fehlgeschlagen.`;
    } finally {
      this._checkAllBusy = false;
      if (this.isConnected) this._render();
    }
  }
  _openProjectPicker() {
    if (this._view !== "main") return;
    this._projectPickerOpen = true;
    this._render();
    this.shadowRoot?.querySelector("#dra-picker-dialog")?.focus();
  }
  _closeProjectPicker() {
    this._projectPickerOpen = false;
    this._render();
    if (!this._mainBatchMode) void this._loadSourceChoices();
    this.shadowRoot?.querySelector("#dra-project-picker-open")?.focus();
  }
  _chooseMainProject(repository) {
    if (!this._projectPickerOpen) return;
    if (!this._projects.some(p => p.repository === repository && p.active !== false)) return;
    this._selectedMainRepo = repository;
    this._controllerStatus = null;
    this._mainSourceRef = "";
    this._manualSourceRef = false;
    this._sourceChoices = null;
    this._sourceChoicesLoadedFor = null;
    this._automaticSourceCheckFor = null;
    this._sourceAdvancedOpen = false;
    this._sourceChoicesMessage = "";
    this._deploymentPreviewRef = null;
    this._mainBatchMode = false;
    this._mainBatchSelectionOpen = false;
    this._batchRunSelected = null;
    this._mainBatchPreview = null;
    this._mainBatchMessage = "";
    this._sourcePreview = null;
    this._projectPickerOpen = false;
    this._sourceHeadMessage = "Empfohlene Quelle wird automatisch geprüft …";
    this._render();
    void this._loadSourceChoices();
    this.shadowRoot?.querySelector("#dra-project-picker-open")?.focus();
  }
  _pickerEntries() {
    const entries = this._projects.map(project => ({kind:"project",project}));
    const position = Number.isInteger(this._pickerBatchPosition)
      ? Math.max(0,Math.min(this._pickerBatchPosition,entries.length))
      : entries.length;
    entries.splice(position,0,{kind:"batch"});
    return entries;
  }
  _movePickerEntry(repository,direction) {
    const entries = this._pickerEntries();
    const index = entries.findIndex(e => e.kind === "batch"
      ? repository === "__batch_picker__" : e.project.repository === repository);
    const neighbor = entries[index+direction];
    if (index < 0 || !neighbor || this._projectBusy || this._checkAllBusy) return;
    if (repository === "__batch_picker__")
      return this._manageProject("move_batch",{repository:"__batch_picker__",direction});
    // Crossing the virtual row moves that row only; project priority remains stable.
    if (neighbor.kind === "batch")
      return this._manageProject("move_batch",{repository:"__batch_picker__",direction:-direction});
    return this._manageProject("move",{repository,direction});
  }
  _isBatchSelfUpdate(project) {
    const repo = String(project?.repository || "").toLowerCase();
    const id = String(project?.project_id || "").toLowerCase();
    return ["thedaimos/deploy-relay-agent-dev",
            "thedaimos/deploy-relay-agent-v2-dev"].includes(repo) ||
      ["deploy_relay","deploy_relay_v2_dev","deploy_relay_agent_v2_dev"].includes(id);
  }
  _isOwnBatchUpdate(project) {
    return ["deploy_relay_v2_dev","deploy_relay_agent_v2_dev"]
      .includes(String(project?.project_id||"").toLowerCase()) ||
      String(project?.repository||"").toLowerCase() === "thedaimos/deploy-relay-agent-v2-dev";
  }
  _batchEligibleProjects() {
    // Match the proven V1 self-update-last model. V2 runs last of all.
    return this._projects.filter(p=>p.active!==false);
  }
  _mainBatchProjects() {
    // Per-run selection never writes catalog batch_preselect flags.
    return this._batchEligibleProjects().filter(p=>this._batchRunSelected && typeof this._batchRunSelected.has === "function"
      ? this._batchRunSelected.has(p.repository)
      : p.batch_preselect!==false);
  }
  _toggleBatchRunProject(repository, checked) {
    if (!this._mainBatchMode || this._mainBatchBusy ||
        !this._batchEligibleProjects().some(p=>p.repository===repository) ||
        ["prepared","queued","running"].includes(this._batchStatus?.status)) return;
    if (!(this._batchRunSelected && typeof this._batchRunSelected.has === "function"))
      this._batchRunSelected = new Set(this._mainBatchProjects().map(p=>p.repository));
    if (checked && !this._batchRunSelected.has(repository) &&
        this._batchRunSelected.size>=8) {
      this._mainBatchMessage = "Maximal 8 Projekte pro Sammelinstallation.";
      this._render(); return;
    }
    if (checked) this._batchRunSelected.add(repository);
    else this._batchRunSelected.delete(repository);
    this._mainBatchPreview=null;
    this._batchPreparation=null;
    this._batchChallenge=null;
    this._batchReviewOpen=false;
    this._batchReviewChecked=false;
    this._batchReviewDigest=null;
    this._mainBatchMessage=this._mainBatchProjects().length
      +" Projekte für diesen Durchlauf ausgewählt. Quellstände erneut prüfen."
      + (this._mainBatchProjects().some(p=>this._isOwnBatchUpdate(p))
        ? " DRA V2 wird zwingend als letztes Projekt installiert; HA-Neustart danach erforderlich."
        : "");
    this._render();
  }
  _openPickerBatch() {
    if (!this._projectPickerOpen || this._mainBatchBusy) return;
    // DRA V1 may be preselected; DRA V2 self-update requires an explicit
    // per-run opt-in and always executes at the very end.
    this._batchRunSelected = new Set(this._batchEligibleProjects()
      .filter(p=>p.batch_preselect!==false && !this._isOwnBatchUpdate(p))
      .map(p=>p.repository));
    const selected = this._mainBatchProjects();
    if (!this._batchEligibleProjects().length) {
      this._pickerBatchMessage = "Keine zulässigen Projekte aktiv. Bitte zuerst andere Projekte hinzufügen.";
      this._render();
      return;
    }
    this._mainBatchMode = true;
    this._mainBatchSelectionOpen = true;
    this._sourceHeadMessage = "";
    this._deploymentPreviewRef = null;
    this._mainBatchPreview = null;
    this._mainBatchMessage = selected.length +
      " Projekte vorausgewählt. Auswahlkästchen für diesen Durchlauf frei änderbar.";
    this._sourcePreview = null;
    this._projectPickerOpen = false;
    this._pickerBatchMessage = "";
    this._render();
    this.shadowRoot?.querySelector("#dra-project-picker-open")?.focus();
  }
  async _previewMainBatch() {
    if (!this._mainBatchMode || !this._hass || this._mainBatchBusy) return;
    const selected = this._mainBatchProjects();
    if (!selected.length) {
      this._mainBatchPreview = null;
      this._mainBatchMessage = "Kein aktives Projekt für das Sammelupdate ausgewählt.";
      this._render();
      return;
    }
    this._mainBatchBusy = true;
    this._mainBatchMessage = "Sammelupdate-Auswahl wird schreibgeschützt geprüft …";
    this._render();
    try {
      const repos = selected.map(p => p.repository);
      const result = await this._hass.callWS({
        type:"deploy_relay_v2_dev/batch/preview", repositories:repos
      });
      if (result?.schema !== "dra-v2-dev-batch-preview.v1" ||
          result.installation_enabled !== false || result.sources_verified !== false ||
          result.count !== repos.length || !Array.isArray(result.selected) ||
          result.selected.length !== repos.length ||
          result.selected.some((p,i) => p.repository?.toLowerCase() !== repos[i].toLowerCase())) {
        throw new Error("batch identity mismatch");
      }
      this._mainBatchPreview = result;
      this._mainBatchMessage = result.count + " Projekte bestätigt. Quellstände noch nicht geprüft. Installation gesperrt.";
    } catch (_error) {
      this._mainBatchPreview = null;
      this._mainBatchMessage = "Sammelupdate-Vorschau nicht bestätigt. Keine Installation.";
    } finally {
      this._mainBatchBusy = false;
      if (this.isConnected) this._render();
    }
  }
  _validateBatchReview(preparation, repositories = null) {
    if (!preparation || preparation.schema !== "dra-v2-batch-status.v1" ||
        !["prepared","up_to_date"].includes(preparation.status) ||
        !Array.isArray(preparation.items) || preparation.items.length < 1 ||
        preparation.items.length > 8 ||
        !/^[a-f0-9]{64}$/.test(preparation.review_digest || "") ||
        preparation.items.some(item =>
          typeof item?.repository !== "string" ||
          !/^[a-f0-9]{40}$/.test(item.source_commit || "") ||
          typeof item.source_ref !== "string" || !item.source_ref.trim() ||
          !["verified_pair","source_only","unknown"].includes(item.version_status) ||
          (item.installed_version !== null && typeof item.installed_version !== "string") ||
          (item.new_version !== null && typeof item.new_version !== "string") ||
          !["prepared","up_to_date"].includes(item.status))) return false;
    return repositories === null ||
      (repositories.length === preparation.items.length &&
       repositories.every(repository =>
         preparation.items.some(item => item.repository === repository)));
  }

  _openBatchReview() {
    const snapshot = this._batchPreparation || this._batchStatus;
    if (!this._mainBatchMode || !this._validateBatchReview(snapshot) ||
        snapshot.status !== "prepared" || !this._batchChallenge) return;
    if (this._batchReviewDigest !== snapshot.review_digest)
      this._batchReviewChecked = false;
    this._batchReviewDigest = snapshot.review_digest;
    this._batchReviewOpen = true;
    this._render();
  }

  async _prepareMainBatch() {
    if (!this._mainBatchMode || !this._hass || this._mainBatchBusy ||
        this._serverVersion !== DRA_V2_UI_VERSION) return;
    const repositories = this._mainBatchProjects().map(p=>p.repository);
    if (!repositories.length || repositories.length>8) {
      this._mainBatchMessage="Bitte 1 bis 8 aktive Projekte auswählen."; this._render(); return;
    }
    this._mainBatchBusy=true;
    this._mainBatchMessage="Home Assistant überprüft alle festen Quellstände und Zielpfade …";
    this._render();
    try {
      const result=await this._hass.callWS({
        type:"deploy_relay_v2_dev/batch/prepare",repositories,client_id:this._controllerId,
      });
      if(result?.schema!=="dra-v2-batch-preparation.v1" ||
         !this._validateBatchReview(result.preparation,repositories)) throw Error("invalid batch");
      this._batchPreparation=result.preparation;
      this._batchStatus=result.preparation;
      this._batchChallenge=/^[a-f0-9]{32}$/.test(result.challenge||"")?result.challenge:null;
      this._batchReviewDigest=result.preparation.review_digest;
      this._batchReviewChecked=false;
      this._batchReviewOpen=!!this._batchChallenge;
      this._batchStartUncertain=false;
      this._mainBatchMessage=this._batchChallenge
        ?"Feste Quellstände vorbereitet. Ausdrückliche Installationbestätigung erforderlich."
        :"Alle ausgewählten Projekte bereits aktuell.";
    } catch (_error) {
      this._batchPreparation=null; this._batchChallenge=null;
      this._batchReviewOpen=false;this._batchReviewChecked=false;
      const known = {
        batch_timed_out:"Zeitüberschreitung bei der Quellprüfung",
        batch_source_invalid:"GitHub-Referenz, Manifest oder Quellenprüfung fehlgeschlagen",
        batch_target_conflict:"Zielkonflikt oder unvollständige Transaktion",
        batch_source_unavailable:"GitHub-Quelle nicht erreichbar",
        batch_preflight_failed:"Serverseitige Vorbereitung fehlgeschlagen",
        invalid_selection:"Ungültige Projektauswahl",
        busy:"Andere HA-Quellprüfung läuft",
      };
      const reason = known[_error?.code] || "HA hat die Vorbereitung nicht bestätigt";
      this._mainBatchMessage = reason + ". Keine Installation gestartet.";
      // A failed read-only preparation cannot start an installation. Query the
      // HA-owned state, not an old local approval, before allowing another try.
      try {
        const snapshot = await this._hass.callWS({type:"deploy_relay_v2_dev/batch/status"});
        if (snapshot?.schema==="dra-v2-batch-status.v1") {
          this._batchStatus=snapshot;
          const name=this._projects.find(p=>p.project_id===snapshot.project_key)?.name ||
            snapshot.project_key || "unbekanntes Projekt";
          const phases={
            source_reference:"GitHub-Zweig, Zugriff oder Empfehlung",
            manifest:"Installationsmanifest",
            inventory:"Git-Dateibestand",
            local_comparison:"Dateivergleich mit Home Assistant",
            version_detection:"Versionsprüfung",
            batch_planning:"Sammelplanung",
          };
          if(snapshot.status==="failed") this._mainBatchMessage=
            "Sammelvorbereitung angehalten: "+name+" · "+
            (phases[snapshot.check_stage]||"Quellprüfung")+
            " · "+(snapshot.error_code||"preflight_failed")+
            ". Es wurde keine Installation gestartet.";
        }
      } catch (_ignore) {}
    } finally { this._mainBatchBusy=false; if(this.isConnected)this._render(); }
  }

  async _takeOverMainBatch() {
    if (!this._hass || this._mainBatchBusy ||
        !window.confirm("Sammelvorbereitung auf dieses Gerät übernehmen? Noch keine Installation.")) return;
    this._mainBatchBusy=true;
    try {
      const r=await this._hass.callWS({
        type:"deploy_relay_v2_dev/batch/takeover",client_id:this._controllerId,confirm:true,
      });
      if(r?.schema!=="dra-v2-batch-preparation.v1" ||
         !/^[a-f0-9]{32}$/.test(r.challenge||"") ||
         !this._validateBatchReview(r.preparation))throw Error("invalid takeover");
      // Takeover is of the HA-owned batch, not of the previously selected
      // individual project. Restore the batch screen before opening its review.
      this._mainBatchMode=true;
      this._mainBatchSelectionOpen=false;
      this._batchRunSelected=new Set(r.preparation.items.map(item=>item.repository));
      this._batchStatus=r.preparation;
      this._batchStatusError=false;
      this._batchChallenge=r.challenge;
      this._batchPreparation=r.preparation;
      this._batchReviewDigest=r.preparation.review_digest;
      this._batchReviewChecked=false;
      this._batchReviewOpen=true;
      this._mainBatchMessage="Sammelvorbereitung übernommen. Installation separat bestätigen.";
    } catch(_error){this._mainBatchMessage="Übernahme nicht bestätigt. HA-Status prüfen.";}
    finally {this._mainBatchBusy=false;if(this.isConnected)this._render();}
  }

  async _discardBatchReview() {
    if (!this._hass || this._mainBatchBusy || !this._batchReviewOpen ||
        !this._batchChallenge || this._batchPreparation?.status !== "prepared") return;
    this._mainBatchBusy=true;
    this._mainBatchMessage="Home Assistant verwirft die vorherige Vorbereitung …";
    this._render();
    try {
      const receipt=await this._hass.callWS({
        type:"deploy_relay_v2_dev/batch/discard",
        challenge:this._batchChallenge,client_id:this._controllerId,confirm:true,
      });
      if(receipt?.schema!=="dra-v2-batch-discard.v1" ||
         receipt.status!=="cancelled") throw Error("discard not acknowledged");
      this._batchChallenge=null;
      this._batchPreparation=null;
      this._batchStatus={schema:"dra-v2-batch-status.v1",status:"cancelled",items:[]};
      this._batchReviewDigest=null;
      this._batchReviewChecked=false;
      this._batchReviewOpen=false;
      this._mainBatchMessage="Vorbereitung verworfen. Auswahl kann verändert und erneut geprüft werden.";
    } catch (_error) {
      this._mainBatchMessage="Verwerfen nicht bestätigt. Keine neue Vorbereitung beginnen; HA-Status prüfen.";
    } finally {
      this._mainBatchBusy=false;
      if(this.isConnected)this._render();
    }
  }

  async _startMainBatch() {
    if (!this._hass || !this._mainBatchMode || this._mainBatchBusy ||
        this._batchStatusError || this._batchStartUncertain || !this._batchReviewOpen ||
        !this._batchReviewChecked ||
        !this._validateBatchReview(this._batchPreparation) ||
        this._batchPreparation.status !== "prepared" ||
        this._batchReviewDigest !== this._batchPreparation.review_digest ||
        this._batchStatus?.review_digest !== this._batchReviewDigest ||
        !/^[a-f0-9]{32}$/.test(this._batchChallenge||"") ||
        !window.confirm("Sammelinstallation auf Home Assistant starten? Bei Fehler werden weitere Projekte angehalten. Jeder Teilauftrag nutzt V1-Sicherung und Rückfall."
          + (this._batchPreparation?.items?.some(item=>
               ["deploy_relay_v2_dev","deploy_relay_agent_v2_dev"].includes(item.project_key))
             ? " DRA V2 wird unbedingt zuletzt aktualisiert. Danach ist ein HA-Neustart notwendig."
             : "")))return;
    this._mainBatchBusy=true;
    this._batchStartUncertain=true;
    this._mainBatchMessage="Sammelauftrag wird Home Assistant zur einmaligen Annahme übermittelt …";
    this._render();
    try {
      const receipt=await this._hass.callWS({
        type:"deploy_relay_v2_dev/batch/start",challenge:this._batchChallenge,
        client_id:this._controllerId,confirm:true,
        review_digest:this._batchReviewDigest,review_confirm:true,
      });
      if(receipt?.schema!=="dra-v2-batch-start.v1" ||
         !/^[a-f0-9]{32}$/.test(receipt.batch_id||""))throw Error("invalid receipt");
      this._batchChallenge=null;
      this._batchReviewOpen=false;
      this._batchReviewChecked=false;
      this._batchStartUncertain=false;
      this._mainBatchMessage="Sammelauftrag auf Home Assistant angenommen.";
      await this._pollInstallation();
    }catch(_error){
      this._batchReviewOpen=false;
      this._batchReviewChecked=false;
      this._mainBatchMessage="Auftragsannahme unklar. Nicht erneut starten; Serverstatus/Audit prüfen.";
    }finally{this._mainBatchBusy=false;if(this.isConnected)this._render();}
  }

  _openV2Settings() {
    if (!this._projectDialogOpen || this._checkAllBusy || this._gitReadBusy) return;
    this._v2SettingsOpen = true;
    this._render();
    this.shadowRoot?.querySelector("#project-v2-settings-dialog")?.focus();
  }
  _closeV2Settings() {
    if (this._gitReadBusy || this._sourceBusy) return;
    this._v2SettingsOpen = false;
    this._render();
    this.shadowRoot?.querySelector("#project-v2-settings-open")?.focus();
  }
  _openProjectDialog() {
    this._projectDialogOpen = true;
    this._render();
  }
  _closeProjectDialog() {
    if (this._projectBusy || this._sourceBusy || this._gitReadBusy || this._checkAllBusy) return;
    this._projectDialogOpen = false;
    this._v2SettingsOpen = false;
    this._highlightMovedRepo = null;
    this._render();
  }
  _selectProjectRow(repo) {
    if (!this._projectDialogOpen ||
        repo !== "__batch_picker__" && !this._projects.some(p => p.repository === repo)) return;
    if (this._highlightMovedRepo === repo) return;
    this._highlightMovedRepo = repo;
    // Free selection is visual only: it neither reorders nor edits the project.
    this._scrollToMovedProject = false;
    this._render();
  }
  _openProjectSettings(repo) {
    if (this._projectBusy || this._checkAllBusy) return;
    this._draftConnectionCheck = null;
    this._projectSettingsRepo = repo;
    this._projectDeleteConfirm = false;
    this._render();
  }
  _closeProjectSettings() {
    this._draftConnectionCheck = null;
    this._projectSettingsRepo = null;
    this._projectDeleteConfirm = false;
    this._render();
  }
  async _manageProject(action, extras = {}) {
    if (!this._hass || this._projectBusy || this._checkAllBusy || !this._projectSettingsRepo && !["move","move_batch"].includes(action)) return;
    this._projectBusy = true;
    this._projectMessage = "Projektverwaltung wird gespeichert …";
    const repo = extras.repository || this._projectSettingsRepo;
    try {
      const result = await this._hass.callWS({
        type:"deploy_relay_v2_dev/projects/manage", action, repository:repo, ...extras
      });
      this._projects = result.projects;
      if (Number.isInteger(result.picker_batch_position))
        this._pickerBatchPosition = result.picker_batch_position;
      if (action === "move" || action === "move_batch") {
        this._highlightMovedRepo = repo;
        this._scrollToMovedProject = true;
        this._projectMessage = "Reihenfolge gespeichert. Verschobenes Projekt hervorgehoben.";
      } else {
        this._sourceChecks.delete(repo);
        if (extras.new_repository) this._sourceChecks.delete(extras.new_repository);
        if (action === "remove" || action === "configure") this._highlightMovedRepo = null;
        this._projectMessage = "Projektverwaltung gespeichert.";
      }
      if (action !== "move" && action !== "move_batch") this._projectSettingsRepo = null;
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
    const batchReviewScroll = s?.querySelector(".dra-batch-review-table-wrap")?.scrollLeft ?? 0;
    const batchReviewTop = s?.querySelector(".dra-batch-review-table-wrap")?.scrollTop ?? 0;
    const batchDialogTop = s?.querySelector("#dra-batch-review-dialog")?.scrollTop ?? 0;
    // Retain open mobile project details while HA polling rebuilds the shadow DOM.
    const expandedMobileProjects = new Set([...s.querySelectorAll(".dra-review-mobile-card[open]")]
      .map(node => node.dataset.projectKey));
    const mobileReviewCards = (this._batchPreparation?.items || []).map(item => {
      const name = this._projects.find(p => p.project_id === item.project_key)?.name || item.project_key;
      const oldVersion = item.installed_version || "Nicht ermittelbar";
      const newVersion = item.new_version || "Nicht ermittelbar";
      const fullCommit = /^[a-f0-9]{40}$/.test(item.source_commit || "") ? item.source_commit : "";
      const shortCommit = fullCommit ? fullCommit.slice(0,12) : "Nicht geprüft";
      const statusLabel = item.status === "up_to_date" ? "Aktuell · keine Installation" : "Zur Installation vorbereitet";
      // Never infer changes from a version string: use the HA-verified file inventory.
      const added = Number.isInteger(item.add) && item.add > 0 ? item.add : 0;
      const changed = Number.isInteger(item.change) && item.change > 0 ? item.change : 0;
      const removed = Number.isInteger(item.remove) && item.remove > 0 ? item.remove : 0;
      const hasChanges = added + changed + removed > 0;
      const minimalChanges = [
        added ? `<span class="dra-review-mini-count dra-review-add" title="Hinzugefügt: ${added}">+${added}</span>` : "",
        changed ? `<span class="dra-review-mini-count dra-review-edit" title="Geändert: ${changed}">~${changed}</span>` : "",
        removed ? `<span class="dra-review-mini-count dra-review-remove" title="Entfernt: ${removed}">−${removed}</span>` : "",
      ].filter(Boolean).join("");
      return `<details class="dra-review-mobile-card ${hasChanges ? "has-changes" : "is-current"}"
        data-project-key="${this._escapeProject(item.project_key)}"
        ${expandedMobileProjects.has(item.project_key) ? "open" : ""}>
        <summary aria-label="${this._escapeProject(name)} · Einzelheiten anzeigen">
          <strong class="dra-review-mobile-project">${this._escapeProject(name)}</strong>
          <span class="dra-review-mobile-version-line"><span class="dra-review-mobile-versions">${this._escapeProject(oldVersion)} <b aria-hidden="true">→</b> ${this._escapeProject(newVersion)}</span><span class="dra-review-mobile-changes">${minimalChanges || (item.status === "up_to_date" ? '<span class="dra-review-mini-current">Aktuell</span>' : '<span class="dra-review-mini-current">Keine Dateiänderungen</span>')}</span></span>
          <span class="dra-review-mobile-hash">Commit <code title="${this._escapeProject(fullCommit)}">${this._escapeProject(shortCommit)}</code></span>
          <span class="dra-review-mobile-chevron" aria-hidden="true">⌄</span>
        </summary>
        <div class="dra-review-mobile-detail-list">
          <div><span>Repository</span><strong>${this._escapeProject(item.repository)}</strong></div>
          <div><span>Git-Referenz</span><code>${this._escapeProject(item.source_ref)}</code></div>
          <div><span>Vollständiger Commit</span><code class="dra-review-full-commit">${this._escapeProject(fullCommit || "Nicht geprüft")}</code></div>
          ${fullCommit ? `<button type="button" class="dra-review-copy-commit" data-commit="${this._escapeProject(fullCommit)}">Vollständigen Commit kopieren</button>` : ""}
          <div><span>Status</span><strong>${this._escapeProject(statusLabel)}</strong></div>
          <div><span>Dateiänderungen</span><strong class="dra-review-counts">
            <span class="${item.add ? "dra-review-add" : ""}">+${item.add}</span> ·
            <span class="${item.change ? "dra-review-edit" : ""}">~${item.change}</span> ·
            <span class="${item.remove ? "dra-review-remove" : ""}">−${item.remove}</span>
          </strong></div>
        </div>
      </details>`;
    }).join("");
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
    const mainBatchProjects = this._mainBatchProjects();
    const batchActiveProjects = this._projects.filter(p=>p.active!==false);
    const mainPreviewVerified = !this._mainBatchMode && !this._sourceConnectionTest &&
      !!mainProject &&
      this._sourceRepository === mainProject.repository &&
      this._deploymentPreviewRef === this._mainSourceRef.trim() &&
      this._sourcePreview?.sources_verified === true &&
      this._sourcePreview?.installation_enabled === false;
    // A fully verified, unchanged file inventory is not an installable update.
    // Require actual lists, rather than interpreting a missing field as empty.
    const previewNoChanges = mainPreviewVerified &&
      Array.isArray(this._sourcePreview?.add) &&
      Array.isArray(this._sourcePreview?.change) &&
      Array.isArray(this._sourcePreview?.remove) &&
      this._sourcePreview.add.length === 0 &&
      this._sourcePreview.change.length === 0 &&
      this._sourcePreview.remove.length === 0 &&
      Number.isInteger(this._sourcePreview.unchanged_count) &&
      this._sourcePreview.unchanged_count > 0;
    const previewFiles = mainPreviewVerified ? [
      ...((this._sourcePreview.add || []).map(path => ({path, status:"add", label:"Hinzugefügt"}))),
      ...((this._sourcePreview.change || []).map(path => ({path, status:"change", label:"Geändert"}))),
      ...((this._sourcePreview.remove || []).map(path => ({path, status:"remove", label:"Entfernt"}))),
    ].filter(entry => typeof entry.path === "string") : [];
    const visiblePreviewFiles = previewFiles.filter(entry =>
      (this._previewFileFilter === "all" || entry.status === this._previewFileFilter) &&
      entry.path.toLocaleLowerCase("de-DE").includes(this._previewFileSearch.toLocaleLowerCase("de-DE"))
    );
    const visibleLogs = this._deploymentLogs.filter(record => {
      if (this._logFilter !== "all" && record.status !== this._logFilter) return false;
      return [record.captured_at,record.status,record.stage,record.reason,record.project_ref,record.run_id]
        .filter(Boolean).join(" ").toLocaleLowerCase("de-DE").includes(this._logSearch.toLocaleLowerCase("de-DE"));
    });
    const installedAuditRows = this._installAuditRecords.map(event => ({
      record: {captured_at:event.captured_at,run_id:event.operation_id,
        project_ref:event.project_key,reason:event.status,status:event.status},
      stage:event.stage,elapsed:event.elapsed_ms,final:true,installation:true,
    }));
    const auditRows = [...installedAuditRows, ...this._deploymentLogs.flatMap(record => {
      const steps = Array.isArray(record.steps) ? record.steps : [];
      return [{record, stage:record.stage || "complete", elapsed:record.duration_ms, final:true},
        ...steps.map(step => ({record, stage:step.stage || "unknown",elapsed:step.elapsed_ms,final:false}))];
    })];
    const auditStages = [...new Set(auditRows.map(row => row.stage))].sort();
    const auditProjects = [...new Set(auditRows.map(row => row.record.project_ref).filter(Boolean))].sort();
    const auditError = status => ["failed", "recovery_required", "interrupted"].includes(status);
    const auditLevel = row => row.installation
      ? (auditError(row.record.status) ? "ERROR" : "INFO")
      : row.final ? (row.record.status === "success" ? "INFO" : "ERROR") : "DEBUG";
    const filteredAuditRows = auditRows.filter(row => {
      const level = auditLevel(row);
      if (this._auditLevel !== "all" && level !== this._auditLevel) return false;
      if (this._auditProject !== "all" && row.record.project_ref !== this._auditProject) return false;
      if (this._auditKind !== "all" &&
          (row.installation ? "installation" : "source") !== this._auditKind) return false;
      if (this._auditPhase !== "all" && row.stage !== this._auditPhase) return false;
      return [row.record.captured_at,row.record.run_id,row.record.project_ref,row.record.reason,
        row.stage,level].filter(Boolean).join(" ").toLocaleLowerCase("de-DE")
        .includes(this._auditSearch.toLocaleLowerCase("de-DE"));
    });
    const installStageLabels = {
      queued:"Auftrag angenommen", running:"Auftrag gestartet",
      staging:"Dateien werden vorbereitet", backup:"Sicherung läuft",
      install:"Dateien werden installiert", verify_install:"Dateiprüfung läuft",
      rollback:"Rückfallverfahren läuft", success:"Erfolgreich abgeschlossen",
      failed:"Installation fehlgeschlagen",
      recovery_required:"Wiederherstellung erforderlich",
      interrupted:"Auftrag unterbrochen",
    };
    const diagnosticStageLabels = {
      admission:"Annahme", repository:"Repository", commit:"Quellcommit",
      manifest:"Manifest", tree:"Git-Dateibaum", local_inventory:"HA-Dateibestand",
      comparison:"Dateivergleich", target_claims:"Zielbesitz",
    };
    const diagnosticReasonLabels = {
      none:"Kein Fehler", source_unavailable:"Quelle nicht verfügbar",
      repository_access:"Repositoryzugriff", commit_unavailable:"Commit nicht erreichbar",
      manifest_invalid:"Manifest nicht prüfbar (unbekannte Ursache)",
      manifest_resource_limit:"Deklarierter Manifest-Grenzwert ungültig",
      manifest_remote_authentication:"GitHub HTTP 401 (Anmeldung)",
      manifest_remote_forbidden:"GitHub HTTP 403 (Zugriff oder Anfragegrenze)",
      manifest_remote_not_found:"Deployment-Manifest über GitHub HTTP 404 nicht gefunden",
      manifest_remote_rate_limited:"GitHub HTTP 429 (Anfragegrenze)",
      manifest_remote_http:"GitHub-Abruf des Manifests fehlgeschlagen",
      manifest_transport_invalid:"GitHub-Antwort für Manifest nicht verifizierbar",
      manifest_response_too_large:"GitHub-Manifestantwort zu groß",
      manifest_json_invalid:"GitHub-Manifestantwort ist kein gültiges JSON",
      manifest_size_invalid:"Manifestdatei zu groß oder leer",
      manifest_encoding_invalid:"Manifestkodierung ungültig",
      manifest_content_integrity:"Manifestdatei weicht von Git-Prüfsumme ab",
      manifest_schema_invalid:"Unbekannte Manifest-Strukturversion",
      manifest_identity_invalid:"Manifest-Projekt- oder Repositoryzuordnung ungültig",
      manifest_source_unsupported:"Manifest-Quellmodus nicht unterstützt",
      manifest_policy_invalid:"Manifest-Sicherheitsvorgaben unzulässig",
      manifest_groups_invalid:"Manifest-Dateigruppen ungültig",
      manifest_target_protected:"Manifest-Ziel geschützt",
      tree_invalid:"Git-Dateibaum ungültig", local_inventory_invalid:"HA-Dateibestand nicht prüfbar",
      compare_invalid:"Dateivergleich nicht prüfbar", target_claim_invalid:"Zielbesitz nicht prüfbar",
      tree_remote_authentication:"GitHub-Anmeldung zurückgewiesen",
      tree_remote_forbidden:"GitHub HTTP 403 (Zugriff oder Anfragegrenze)",
      tree_remote_not_found:"Git-Dateibaum nicht gefunden",
      tree_remote_rate_limited:"GitHub-Anfragegrenze erreicht",
      tree_remote_http:"GitHub-Anfrage fehlgeschlagen",
      tree_transport_invalid:"GitHub-Antwort nicht verifizierbar",
      tree_response_too_large:"GitHub-Antwort zu groß",
      tree_json_invalid:"GitHub-Antwort ungültig",
      tree_incomplete:"Git-Dateibaum unvollständig",
      tree_entry_limit:"Zu viele Git-Baumeinträge",
      tree_path_invalid:"Ungültiger Quellpfad",
      tree_entry_invalid:"Git-Dateieintrag ungültig",
      tree_file_invalid:"Dateigröße oder Git-Prüfsumme ungültig",
      tree_source_empty:"Installationsquelle leer",
      tree_budget_exceeded:"Prüfgrenze der Quelldateien überschritten",
      timeout:"Zeitüberschreitung", unexpected_error:"Unerwarteter Fehler",
    };
    const runtimeVersionKnown = typeof this._serverVersion === "string";
    const versionMismatch = runtimeVersionKnown &&
      this._serverVersion !== DRA_V2_UI_VERSION;
    const uiVersionLabel = "V" + DRA_V2_UI_VERSION + " DEV";
    const runtimeVersionLabel = runtimeVersionKnown
      ? "V" + this._serverVersion + " DEV" : "Noch nicht ermittelt";
    const runtimeVersionState = versionMismatch ? "mismatch" :
      runtimeVersionKnown ? "matched" : "pending";
    const deploymentBusy = this._mainBatchMode
      ? this._mainBatchBusy || ["inspecting_sources","preparing"].includes(this._batchStatus?.status)
      : (this._sourceBusy || this._installBusy);
    const installActive = !!this._installJob &&
      this._installJob.project_key === mainProject?.project_id &&
      ["queued","running","waiting_for_resource","cancel_requested"].includes(this._installJob.status);
    const runningJobs = this._installJobs.filter(j=>
      ["queued","running","waiting_for_resource","cancel_requested"].includes(j.status));
    const observedJobs = runningJobs.length ? runningJobs :
      this._observerLastJobId ? this._installJobs.filter(j=>
        j.operation_id === this._observerLastJobId).slice(0,1) : [];
    const observerPhase = {
      queued:"In Warteschlange", waiting_for_resource:"Wartet auf Ressourcen",
      running:"In Ausführung", staging:"Dateien bereitstellen", backup:"Sicherung",
      apply:"Installation", verify:"Installationsprüfung",
      rollback:"Wiederherstellung", complete:"Abgeschlossen",
    };
    const observerJobName = job => {
      const configured = this._projects.find(p=>p.project_id===job.project_key);
      return this._installProjectNames[job.project_key] || configured?.name ||
        job.project_key || "Unbekanntes Projekt";
    };
    const observerVisible = observedJobs.length > 0 ||
      !this._installStatusKnown || this._installStatusError;

    // The server's terminal receipt, not a mutable preview, determines completion.
    const jobBelongsToProject = !!mainProject &&
      this._installJob?.project_key === mainProject.project_id;
    const installFinished = jobBelongsToProject &&
      this._installJob?.status === "success" && this._installJob?.phase === "complete" &&
      !this._supersededCompletionIds.has(this._installJob?.operation_id);
    const lastStoredSuccess = !jobBelongsToProject && !!mainProject &&
      this._installAuditRecords.find(event => event.project_key === mainProject.project_id &&
        event.stage === "success" && event.status === "success") || null;
    const archivedFinish = !!lastStoredSuccess &&
      this._dismissedHistoricalProject !== mainProject?.project_id && !mainPreviewVerified &&
      !installActive && !this._installBusy;
    const upToDate = previewNoChanges && !this._installPreparation &&
      !installActive && !this._installBusy && !this._installSubmissionActive;
    const displayFinished = !upToDate && (installFinished || archivedFinish);
    const postInstallJob = !upToDate && installFinished && !this._mainBatchMode &&
      this._serverVersion === DRA_V2_UI_VERSION ? this._installJob : null;
    const installFailed = jobBelongsToProject &&
      ["failed","recovery_required","interrupted","cancelled"].includes(this._installJob?.status);
    // A freshly opened device may not hold the preview in browser memory.
    // The HA-held, time-limited V1 preparation is the authoritative plan.
    // HA's exact-commit prepared plan is authoritative across browser sessions.
    // A stale/new local read-only preview must not mask an existing valid plan.
    const preparedInstall = this._installPreparation && !this._mainBatchMode &&
      this._installPreparation.repository === mainProject?.repository &&
      this._installPreparation.source_ref === this._mainSourceRef.trim() &&
      /^[a-f0-9]{32}$/.test(this._installPreparation.challenge || "")
        ? this._installPreparation : null;
    // Batch is an independent HA-owned workflow, not a read-only picker
    // preview. Its primary button MUST advance through prepare/start.
    const batchState = this._batchStatus?.status || "idle";
    const batchPrepared = batchState === "prepared" && this._batchStatus?.confirmation_required === true;
    const batchRunning = ["queued","running"].includes(batchState);
    const batchFinished = batchState === "success";
    const batchFailed = ["failed","stopped","interrupted"].includes(batchState);
    const deploymentStage = this._mainBatchMode
      ? batchFinished ? 4 : batchRunning ? 3 : batchPrepared ? 2 : 1
      : upToDate ? 1 : displayFinished ? 4 :
        (this._installSubmissionActive || installActive || installFailed) ? 3 :
        (preparedInstall || mainPreviewVerified) ? 2 : 1;
    const deploymentCanPreview = this._mainBatchMode
      ? mainBatchProjects.length > 0 && !!this._hass
      : !!mainProject && !!this._hass;
    const deploymentButtonText = this._mainBatchMode
      ? deploymentBusy ? "1/4 · Sammelvorbereitung läuft auf Home Assistant …"
        : batchFinished ? "4/4 · Sammelinstallation abgeschlossen"
        : batchFailed ? "1/4 · Vorbereitung/Installation fehlgeschlagen – Details prüfen"
        : batchRunning ? "3/4 · Sammelinstallation läuft auf Home Assistant …"
        : batchPrepared ? this._batchChallenge
          ? "2/4 · Versionen, Referenzen und Commits prüfen"
          : "2/4 · Sammelvorbereitung auf diesem Gerät übernehmen"
        : batchState === "up_to_date" ? "Aktuell · Kein Sammelupdate erforderlich"
        : "1/4 · Sammelinstallation prüfen und vorbereiten"
      : upToDate ? "Aktuell · Kein Update verfügbar" :
      installFinished ? "4/4 · Abschluss – erfolgreich installiert" :
      archivedFinish ? "4/4 · Letzter Abschluss (gespeichert)" :
      installFailed ? "3/4 · Update fehlgeschlagen – Audit prüfen" :
      installActive ? "3/4 · Update läuft …" :
      this._installSubmissionActive ? "3/4 · Auftrag wird an Home Assistant übergeben …" :
      deploymentBusy
      ? "1/4 · " + (this._mainBatchMode ? "Projektauswahl wird geprüft …" : "Vorschau wird berechnet …")
      : preparedInstall ? "2/4 · Installation vorbereitet"
      : mainPreviewVerified ? "2/4 · Installation vorbereiten"
      : this._mainBatchMode ? "Sammelupdate · Quellenauswahl prüfen"
      : "1/4 · Vorschau berechnen";
    const deploymentStatus = upToDate
      ? "Dateivergleich abgeschlossen: 0 hinzugefügt · 0 geändert · 0 entfernt · " +
        this._sourcePreview.unchanged_count +
        " unverändert. Keine Installation erforderlich."
      : this._mainBatchMode
      ? this._mainBatchMessage || "Projektauswahl prüfen, dann feste Quellstände serverseitig vorbereiten."
      : mainPreviewVerified
        ? this._installMessage || "Quellprüfung abgeschlossen. Die V1-Engine kann das Update vorbereiten."
        : this._sourceRepository === mainProject?.repository && this._sourceMessage
          ? this._sourceMessage : "Noch keine Vorschau berechnet.";
    // Consistent, resolution-independent 24x24 vector icons: never emoji or icon fonts.
    const iconSvg = (body, size=22) => `<svg class="project-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" focusable="false" aria-hidden="true">${body}</svg>`;
    const deploymentIcons = [
      iconSvg('<circle cx="11" cy="11" r="7"/><path d="m16 16 5 5"/>',21),
      iconSvg('<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/><path d="m9 12 2 2 4-4"/>',21),
      iconSvg('<path d="M12 3v12m-5-5 5 5 5-5"/><path d="M4 17v4h16v-4"/>',21),
      iconSvg('<path d="M20 6 9 17l-5-5"/>',21),
    ];

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
    const projectRows = this._pickerEntries().map((entry,i) => {
      if (entry.kind === "batch") {
        const selected = this._highlightMovedRepo === "__batch_picker__";
        return `<tr class="project-row project-batch-picker-row${selected ? " recently-moved" : ""}"
           data-project-repo="__batch_picker__" tabindex="0" aria-current="${selected}"
           aria-label="Sammelupdate markieren"><td>${i+1}</td>
          <td><strong>Sammelupdate</strong><div class="note">${this._mainBatchProjects().length} aktivierte Projekte · gemeinsame Auswahl</div></td>
          <td><span class="project-batch-status">Gruppenauswahl</span></td>
          <td><button class="project-batch-settings-open project-settings-open-style project-metal-button" title="Sammelupdate-Auswahl bearbeiten"
                aria-label="Sammelupdate-Auswahl bearbeiten" ${this._batchBusy ? "disabled" : ""}>${metalSvg(gearIcon,"batch",i)}</button></td>
          <td><button class="project-move project-metal-button" data-repo="__batch_picker__" data-direction="-1"
              ${i===0 || this._projectBusy || this._checkAllBusy ? "disabled" : ""}
              aria-label="Sammelupdate nach oben verschieben" title="Nach oben">${metalSvg(upIcon,"batch-up",i)}</button>
            <button class="project-move project-metal-button" data-repo="__batch_picker__" data-direction="1"
              ${i===this._projects.length || this._projectBusy || this._checkAllBusy ? "disabled" : ""}
              aria-label="Sammelupdate nach unten verschieben" title="Nach unten">${metalSvg(downIcon,"batch-down",i)}</button></td></tr>`;
      }
      const p = entry.project;
      const test = this._sourceChecks.get(p.repository);
      const state = test?.status || "unverified";
      const label = state === "success" ? (test.access_level === "RW" ? "RW" : "RO") : state === "failure" ? "X" :
        state === "checking" ? "…" : "?";
      const icon = state === "success" ? onlineIcon : state === "failure" ? failureIcon : pendingIcon;
      const selected = this._highlightMovedRepo?.toLowerCase() === p.repository.toLowerCase();
      return `<tr class="project-row connection-${state}${selected ? " recently-moved" : ""}" data-project-repo="${this._escapeProject(p.repository)}" tabindex="0" aria-current="${selected ? "true" : "false"}" aria-label="Projekt ${this._escapeProject(p.name)} markieren"><td>${i+1}</td>
        <td class="${p.active === false ? "project-entry-inactive" : ""}"><strong>${this._escapeProject(p.name)}</strong><div class="note">${this._escapeProject(p.repository)}</div>
          ${p.active === false ? '<span class="project-inactive-label" aria-label="Projekt inaktiv">Inaktiv</span>' : ""}</td>
        <td><button class="source-check ${state}" data-repo="${this._escapeProject(p.repository)}"
          ${this._connectionBusy || this._checkAllBusy || this._projectBusy ? "disabled" : ""} aria-label="GitHub-Verbindung für ${this._escapeProject(p.name)} prüfen" title="Verbindung prüfen">${icon}<span class="project-status-label">${label}</span></button></td>
        <td><button class="project-settings-open project-settings-open-style project-metal-button" data-repo="${this._escapeProject(p.repository)}" ${this._checkAllBusy ? "disabled" : ""} aria-label="Einstellungen für ${this._escapeProject(p.name)}" title="Projekteinstellungen">${metalSvg(gearIcon,"settings",i)}</button></td>
        <td><button class="project-move project-metal-button" data-repo="${this._escapeProject(p.repository)}" data-direction="-1" ${i===0 || this._projectBusy || this._checkAllBusy ? "disabled" : ""} aria-label="${this._escapeProject(p.name)} nach oben verschieben" title="Nach oben">${metalSvg(upIcon,"up",i)}</button>
        <button class="project-move project-metal-button" data-repo="${this._escapeProject(p.repository)}" data-direction="1" ${i===this._projects.length || this._projectBusy || this._checkAllBusy ? "disabled" : ""} aria-label="${this._escapeProject(p.name)} nach unten verschieben" title="Nach unten">${metalSvg(downIcon,"down",i)}</button></td></tr>`;
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
    // HA can scroll the panel through an ancestor outside shadow DOM.
    // Replacing the entire shadow tree must not jump the viewport to the top.
    const pageScrollPositions = [];
    for (let node = this; node; node = node.parentNode || node.host) {
      if (typeof node.scrollTop === "number" && node.scrollTop > 0)
        pageScrollPositions.push([node, node.scrollTop, node.scrollLeft]);
    }
    const documentScroller = document.scrollingElement;
    if (documentScroller && documentScroller.scrollTop > 0 &&
        !pageScrollPositions.some(([node]) => node === documentScroller))
      pageScrollPositions.push([documentScroller, documentScroller.scrollTop, documentScroller.scrollLeft]);
    const previousProjectScroll = s.querySelector("#project-management-scroll")?.scrollTop ?? 0;
    const previousV2SettingsScroll = s.querySelector(".project-v2-settings-scroll")?.scrollTop ?? 0;
    const pendingV2ReadToken = s.querySelector("#source-read-token")?.value || "";
    s.innerHTML = `
      <style>
        :host { display:block; min-height:100%; color:var(--primary-text-color, #f2f2f2); background:var(--primary-background-color, #111); font-family:var(--paper-font-body1_-_font-family, sans-serif); }
        main { margin:auto; width:100%; max-width:none; box-sizing:border-box; padding:24px clamp(12px,2.5vw,36px) 56px; }
        [hidden] {display:none !important;}
        .dra-head {display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;border-bottom:1px solid var(--divider-color,#555);padding-bottom:12px}
        .dra-head strong {font-size:20px}.dra-head button {margin:2px}
        .dra-actions {display:flex;gap:8px;align-items:center;flex-wrap:wrap}
        .dra-lock {border:1px solid #b08022;color:#f0ba40;border-radius:15px;padding:6px 10px}
        .dra-version {display:flex;flex-direction:column;min-width:0;gap:2px;
          padding:7px 12px;border:1px solid #547184;border-radius:14px;
          background:linear-gradient(135deg,rgba(38,70,87,.4),rgba(16,33,44,.32));}
        .dra-version-heading {font-size:11px;color:#b0c6d3;line-height:1.2;}
        .dra-version-number {font-size:15px !important;font-weight:700;color:#f0f5f8;
          line-height:1.3;letter-spacing:.012em;white-space:nowrap;}
        .dra-runtime-version {font-size:11px;line-height:1.35;color:#c0d1db;}
        .dra-version.mismatch {border-color:#be8a3b;background:rgba(140,89,27,.18);}
        .dra-version.mismatch .dra-runtime-version {color:#f6d19a;font-weight:700;}
        .dra-version.pending .dra-runtime-version {color:#9eabb5;}
        @media(max-width:600px) {
          .dra-version {padding:6px 10px;}
          .dra-version-number {font-size:14px !important;}
        }
        .dra-projectbar {display:flex;gap:12px;align-items:end;flex-wrap:wrap}
        .dra-projectbar label {flex:1;min-width:210px}
        .dra-projectbar select {display:block;width:100%;min-height:44px;padding:8px;border-radius:8px;background:var(--primary-background-color,#111);color:inherit;border:1px solid var(--divider-color,#555)}
        /* Native Android select replacement: framed, scalable, accessible project picker. */
        .dra-project-picker-field {flex:1 1 250px;min-width:0;display:flex;flex-direction:column;gap:7px;}
        .dra-project-picker-trigger {
          display:flex;align-items:center;justify-content:space-between;gap:12px;
          box-sizing:border-box;width:100%;min-height:54px;margin:0;padding:10px 14px;
          background:linear-gradient(165deg,#283946 0%,#111c27 65%,#0d1821 100%);
          color:var(--primary-text-color,#fff);
          border:1px solid #698b9e;border-radius:12px;
          box-shadow:inset 0 1px 0 rgba(229,248,255,.25),inset 0 -2px 4px #0006,
            0 2px 9px rgba(0,0,0,.3);
          text-align:left;transition:filter .14s,transform .14s;
        }
        .dra-project-picker-trigger:hover:not(:disabled) {filter:brightness(1.17);}
        .dra-project-picker-trigger:active:not(:disabled) {transform:translateY(2px);filter:brightness(.86);}
        .dra-project-picker-trigger:focus-visible {outline:2px solid #e2c071;outline-offset:3px;}
        .dra-project-picker-current {display:flex;flex-direction:column;min-width:0;gap:2px;}
        .dra-project-picker-current-name {font-size:15px;font-weight:700;line-height:1.25;overflow-wrap:anywhere;}
        .dra-project-picker-current-repo {font-size:12px;color:#abbcc8;line-height:1.3;overflow-wrap:anywhere;}
        .dra-project-picker-trigger svg {flex:none;color:#b7e3f6;}
        .dra-picker-dialog {
          display:flex;flex-direction:column;overflow:hidden;width:min(100%,620px);
          padding:18px;max-height:92dvh;
          background:linear-gradient(150deg,#252e35,#181e24 50%,#121a22);
          border:1px solid #7597a9;border-radius:18px;
          box-shadow:inset 0 1px 0 rgba(232,249,255,.28),inset 0 0 1px #bcefff,
            0 20px 50px #000c,0 0 0 1px #0007;
        }
        .dra-picker-dialog .dra-picker-header {
          flex:0 0 auto;display:flex;justify-content:space-between;align-items:center;gap:16px;
          padding:0 0 15px;border-bottom:1px solid #638093;
        }
        .dra-picker-header h2 {margin:0 0 3px;font-size:21px;}
        .dra-picker-header p {margin:0;font-size:12px;}
        .dra-picker-header button {
          display:flex;justify-content:center;align-items:center;
          flex:none;width:43px;height:43px;min-width:43px;margin:0;padding:9px;
          border-radius:12px;border:1px solid #658a9c;
          background:linear-gradient(145deg,#355465,#1b303c);
          color:#e0f5ff;
        }
        .dra-picker-list {
          flex:1 1 auto;min-height:0;overflow-y:auto;overscroll-behavior:contain;
          scrollbar-gutter:stable;
        }
        .dra-picker-entry {
          box-sizing:border-box;display:flex;align-items:center;gap:13px;width:100%;
          padding:15px 12px;margin:0;background:transparent;
          color:#e8eff5;border:0;border-bottom:1px solid #43535f;
          text-align:left;min-height:79px;border-radius:0;transition:background .16s;
        }
        .dra-picker-entry:hover:not(:disabled) {background:rgba(79,133,163,.18);}
        .dra-picker-entry:active:not(:disabled) {background:rgba(46,106,135,.38);}
        .dra-picker-entry:focus-visible {outline:2px solid #e2c071;outline-offset:-3px;}
        .dra-picker-entry.selected {
          background:linear-gradient(95deg,rgba(38,120,98,.24),rgba(51,93,124,.12));
          box-shadow:inset 3px 0 0 #69cda9;
        }
        .dra-picker-entry:disabled {opacity:.55;cursor:not-allowed;}
        .dra-picker-entry-number {width:24px;flex:none;text-align:center;font-size:13px;color:#c1cbd4;}
        .dra-picker-entry-content {display:flex;flex:1 1 auto;min-width:0;flex-direction:column;gap:4px;}
        .dra-picker-entry-content strong {font-size:15px;overflow-wrap:anywhere;}
        .dra-picker-entry-repository {font-size:12px;color:#a7b4be;overflow-wrap:anywhere;}
        .dra-picker-check {flex:none;display:flex;color:#9eafbc;}
        .dra-picker-entry.selected .dra-picker-check {color:#8ce7c4;}
        .dra-picker-entry.dra-picker-batch-entry {
          border-left:3px solid #7bafcb;
          background:linear-gradient(115deg,rgba(46,105,139,.20),rgba(23,42,59,.16));
        }
        .dra-picker-entry.dra-picker-batch-entry.selected {
          border-left-color:#72d7b4;
          background:linear-gradient(95deg,rgba(29,111,86,.24),rgba(35,74,99,.2));
          box-shadow:inset 3px 0 0 #69cda9;
        }

        .dra-picker-inactive {font-size:11px;color:#ff8c9a;font-weight:800;}
        .dra-picker-footer {flex:0 0 auto;padding-top:10px;}
        .dra-picker-divider {
          height:1px;margin-bottom:10px;
          background:linear-gradient(90deg,transparent,#91acbf 12%,#91acbf 88%,transparent);
        }
        .dra-picker-batch {
          box-sizing:border-box;display:flex;align-items:center;gap:12px;
          margin:0;width:100%;padding:12px 14px;text-align:left;
          color:#e8f9ff;border:1px solid #628ba0;border-radius:11px;
          background:linear-gradient(140deg,#264858,#173142 65%,#122a38);
          box-shadow:inset 0 1px 0 rgba(242,252,255,.2),0 2px 7px #0005;
        }
        .dra-picker-batch>svg {flex:none;}
        .dra-picker-batch span {flex:1;display:flex;flex-direction:column;gap:3px;}
        .dra-picker-batch small {font-size:11px;font-weight:400;color:#c2d3dc;}
        .dra-picker-batch:hover:not(:disabled) {filter:brightness(1.18);}
        .dra-picker-batch:active:not(:disabled) {transform:translateY(2px);filter:brightness(.83);}
        .dra-picker-batch:focus-visible {outline:2px solid #e2c071;outline-offset:2px;}
        .dra-picker-batch-message {margin:8px 0 0;font-size:12px;color:#f0c3ad;}
        .dra-picker-batch-message:empty {display:none;}
        .dra-main-batch-card {border-color:#587f94;box-shadow:inset 3px 0 0 #62a4c2;}
        .dra-main-batch-list {display:flex;flex-direction:column;max-height:40vh;overflow:auto;
          border:1px solid #445c69;border-radius:10px;padding:0 12px;margin-top:12px;}
        .dra-main-batch-entry {display:grid;grid-template-columns:28px minmax(0,1fr);column-gap:10px;
          padding:10px 0;border-bottom:1px solid #3d505b;align-items:center;}
        .dra-main-batch-entry:last-child {border:0;}
        .dra-main-batch-entry > .note {grid-column:2;font-size:12px;overflow-wrap:anywhere;}

        @media(max-width:760px) {
          .dra-picker-dialog {width:100%;max-height:93dvh;padding:15px;}
          .dra-picker-entry {min-height:75px;padding:13px 8px;gap:8px;}
          .dra-picker-header h2 {font-size:18px;}
          .dra-project-picker-field {width:100%;}
        }
        /* One-button deployment workflow; V1-inspired moving progress strip. */
        .dra-source-title {display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;}
        .dra-source-title h2 {margin:0;}
        .dra-source-actions {display:flex;align-items:center;flex-wrap:wrap;gap:8px;}
        .dra-source-actions button {margin:0;min-height:34px;padding:6px 12px;}
        .dra-source-badge {font-size:12px;font-weight:700;padding:6px 10px;border-radius:20px;
          border:1px solid #a37b35;background:rgba(148,105,33,.12);color:#e9cf93;}
        .dra-source-badge.verified {border-color:#44996a;background:rgba(26,120,70,.13);color:#a4edbd;}
        .dra-source-badge.changed {border-color:#bb8d32;background:rgba(167,119,28,.18);color:#f5d18c;}
        .dra-source-info {border:1px solid #687c8a;border-radius:12px;padding:16px;
          margin-top:16px;background:linear-gradient(140deg,rgba(47,70,80,.16),rgba(17,28,37,.16));}
        .dra-source-info.verified {border-color:#4eac6e;
          background:linear-gradient(140deg,rgba(31,111,61,.18),rgba(17,30,24,.12));}
        .dra-source-info.changed {border-color:#b58b31;
          background:linear-gradient(140deg,rgba(132,87,20,.2),rgba(29,27,18,.12));}
        .dra-source-info > strong {display:block;font-size:17px;margin-bottom:12px;}
        .dra-source-meta {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;}
        .dra-source-meta > div {display:flex;flex-direction:column;gap:4px;min-width:0;}
        .dra-source-meta strong {font-size:14px;overflow-wrap:anywhere;}
        .dra-source-extra {border-top:1px solid #42515b;margin-top:14px;padding-top:12px;}
        .dra-source-extra summary {cursor:pointer;font-weight:700;min-height:25px;}
        .dra-source-extra label {display:block;margin-top:13px;}
        .dra-source-extra input.project-text {box-sizing:border-box;width:100%;}
        .dra-global-observer {margin:14px 0;border:1px solid #477a98;border-radius:13px;
          padding:14px 17px;background:linear-gradient(110deg,rgba(28,72,98,.23),rgba(15,45,57,.10));
          color:#d9f2ff;display:grid;gap:11px;}
        .dra-global-observer.is-stale {border-color:#a48246;color:#f1dbaa;
          background:linear-gradient(110deg,rgba(110,76,25,.19),rgba(58,43,24,.08));}
        .dra-global-observer.is-complete {border-color:#43846c;color:#c0f1d9;
          background:linear-gradient(110deg,rgba(23,93,63,.20),rgba(13,50,37,.08));}
        .dra-global-observer.is-failed {border-color:#ab676a;color:#fbd1d0;}
        .dra-observer-top {display:flex;gap:10px;align-items:baseline;justify-content:space-between;flex-wrap:wrap;}
        .dra-observer-top strong {font-size:15px;font-weight:780;}
        .dra-observer-note {font-size:12px;line-height:1.5;opacity:.84;}
        .dra-observer-item {display:grid;gap:7px;padding:9px 12px;border-radius:9px;
          background:rgba(9,19,27,.25);border:1px solid rgba(145,197,225,.15);}
        .dra-observer-line {display:flex;align-items:baseline;justify-content:space-between;
          gap:7px 16px;flex-wrap:wrap;}
        .dra-observer-line strong {font-size:14px;}
        .dra-observer-line span {font-size:12px;}
        .dra-observer-meter {height:5px;background:rgba(128,172,198,.17);
          border-radius:9px;overflow:hidden;}
        .dra-observer-meter>span {height:100%;display:block;min-width:0;
          border-radius:9px;background:linear-gradient(90deg,#389ac4,#7cdbc5);
          transition:width .25s ease;}
        @media (max-width:680px) {.dra-global-observer {padding:11px 12px;}
          .dra-observer-top strong {font-size:14px;}}
        .dra-deployment-panel {border-color:#425968;}
        .dra-deployment-panel h2 {margin:0 0 14px;}
        .dra-deployment-heading {display:flex;align-items:center;justify-content:space-between;
          gap:12px;min-width:0;margin:0 0 14px;}
        .dra-deployment-heading h2 {margin:0;}
        .dra-controller-chip {display:flex;align-items:center;gap:9px;min-width:0;max-width:100%;
          padding:7px 12px;border:1px solid #947239;border-radius:12px;
          background:linear-gradient(115deg,rgba(126,91,29,.15),rgba(52,43,29,.07));
          color:#e8cc91;font-size:12px;line-height:1.35;}
        .dra-controller-chip.is-controller {border-color:#4d967c;color:#b0efd2;
          background:linear-gradient(115deg,rgba(35,115,83,.20),rgba(22,70,59,.08));}
        .dra-controller-chip.is-observer {border-color:#4784aa;color:#b9e3ff;
          background:linear-gradient(115deg,rgba(34,91,138,.19),rgba(19,61,93,.07));}
        .dra-controller-dot {width:8px;height:8px;flex:none;border-radius:50%;
          background:currentColor;box-shadow:0 0 0 3px rgba(255,255,255,.06);}
        .dra-controller-copy {display:flex;align-items:baseline;flex-wrap:wrap;gap:4px 10px;min-width:0;}
        .dra-controller-copy strong {font-size:12px;font-weight:750;letter-spacing:.01em;}
        .dra-controller-chip button {margin-left:auto;flex:none;border-radius:9px;padding:7px 11px;
          border:1px solid currentColor;color:inherit;background:rgba(255,255,255,.04);
          font:inherit;font-weight:700;cursor:pointer;}
        .dra-deployment-heading {flex-wrap:wrap;}
        .dra-deployment-heading .dra-controller-chip {margin-right:auto;}
        @media (max-width:720px) {
          .dra-deployment-heading {gap:9px;}
          .dra-deployment-heading .dra-controller-chip {order:3;flex:1 1 100%;box-sizing:border-box;}
          .dra-controller-copy {align-items:flex-start;flex-direction:column;gap:1px;}
        }
        .dra-logs-heading-buttons {display:flex;align-items:center;gap:7px;flex:none;}
        .dra-logs-clear-pill {font:inherit;font-size:12px;font-weight:700;
          min-height:34px;border-radius:20px;padding:6px 10px;
          border:1px solid #6a7380;background:rgba(97,108,119,.11);color:#c6cdd5;}
        .dra-logs-clear-pill:focus-visible {outline:2px solid #e8c779;outline-offset:3px;}
        .dra-logs-confirm {margin:0 0 12px;padding:10px;border:1px solid #8d7044;
          border-radius:10px;line-height:1.4;}
        .dra-logs-confirm-buttons {display:flex;flex-wrap:wrap;gap:8px;margin-top:9px;}
        .dra-logs-confirm-buttons button {min-height:42px;flex:1 1 125px;}
        .dra-logs-pill {font:inherit;font-size:12px;font-weight:700;
          padding:6px 13px;min-height:34px;flex:none;border-radius:20px;
          border:1px solid #a37b35;background:rgba(148,105,33,.12);color:#e9cf93;}
        .dra-logs-pill[aria-expanded="true"] {border-color:#e5bc6c;background:rgba(169,124,44,.2);}
        .dra-logs-pill:focus-visible {outline:2px solid #e8c779;outline-offset:3px;}
        .dra-logs-panel {margin:0 0 14px;padding:12px;border:1px solid #5c6570;
          background:rgba(29,41,52,.55);border-radius:12px;}
        .dra-logs-actions {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px;}
        .dra-logs-actions button {box-sizing:border-box;min-width:0;min-height:42px;margin:0;
          padding:8px 5px;font-size:12px;overflow-wrap:anywhere;}
        .dra-logs-actions button:disabled {opacity:.45;cursor:not-allowed;}
        .dra-logs-events {max-height:250px;overflow-y:auto;font-size:12px;margin-top:11px;
          overflow-wrap:anywhere;}
        .dra-logs-event {padding:9px 0;border-top:1px solid #455864;}
        .dra-logs-event strong {display:block;margin-bottom:4px;}
        .dra-audit-heading {display:flex;flex-wrap:wrap;justify-content:space-between;gap:8px;
          padding:10px 12px;border-left:3px solid #d7b778;background:#243340;border-radius:7px;}
        .dra-audit-heading strong {color:#f4d99c;font-size:15px;}
        .dra-audit-filters {display:flex;flex-wrap:wrap;gap:12px;align-items:end;margin:14px 0;}
        .dra-audit-filters label {display:flex;flex-direction:column;gap:5px;font-size:12px;color:#bed2df;}
        .dra-audit-filters select,.dra-audit-filters input {min-height:38px;color:#eef5f8;background:#14232d;
          border:1px solid #60798a;border-radius:7px;padding:7px;}
        .dra-audit-search {flex:1;min-width:170px;}
        .dra-audit-scroll {max-height:420px;overflow:auto;border:1px solid #415b6d;border-radius:9px;}
        .dra-audit-table {width:100%;min-width:800px;border-collapse:collapse;font-size:12px;}
        .dra-audit-table th {position:sticky;top:0;background:#304555;color:#f5dca6;z-index:1;
          text-align:left;padding:11px 9px;border-bottom:2px solid #b99758;}
        .dra-audit-table td {padding:10px 9px;border-bottom:1px solid #344c5c;vertical-align:top;}
        .dra-audit-table tbody tr:nth-child(even) {background:#1e303c;}
        .dra-audit-table tbody tr:nth-child(odd) {background:#172731;}
        .dra-audit-table tr.dra-audit-success .dra-audit-level {color:#9ce3b6;}
        .dra-audit-table tr.dra-audit-failed .dra-audit-level {color:#ffa9a9;}
        .dra-audit-table tr.dra-audit-debug .dra-audit-level {color:#8dc8ed;}
        .dra-audit-table details {min-width:90px;}
        .dra-audit-table details div {padding:4px 0;overflow-wrap:anywhere;}
        .dra-audit-table summary {cursor:pointer;color:#f0cc8e;}
        /* G2 history refresh: premium gold-on-slate control, inside logs only. */
        .dra-history-heading {display:flex;align-items:center;justify-content:space-between;
          gap:12px;min-width:0;flex-wrap:nowrap;margin:0 0 8px;}
        .dra-history-heading-title {display:flex;flex:1 1 0;min-width:0;
          flex-direction:column;align-items:flex-start;gap:5px;}
        .dra-history-heading-title > strong {font-size:13px;line-height:1.4;
          letter-spacing:.015em;color:#f2f5f7;overflow-wrap:normal;}
        .dra-history-refresh {box-sizing:border-box;display:inline-flex;align-items:center;
          justify-content:center;gap:9px;margin:0;padding:9px 14px;min-height:44px;
          min-width:142px;flex:none;border:1px solid #ba9651;border-radius:13px;
          background:linear-gradient(138deg,#56452b,#342d23 56%,#242c32);
          color:#ffe3a8;font:inherit;font-size:13px;font-weight:700;line-height:1.2;
          letter-spacing:.012em;cursor:pointer;
          box-shadow:inset 0 1px 0 #fff3,0 3px 11px #0006;
          transition:background .18s ease,box-shadow .18s ease,border-color .18s ease,transform .18s ease;}
        .dra-history-refresh svg {flex:none;width:18px;height:18px;
          stroke:currentColor;stroke-width:2;fill:none;stroke-linecap:round;stroke-linejoin:round;}
        .dra-history-refresh:hover:not(:disabled) {border-color:#efc879;
          background:linear-gradient(138deg,#6c5430,#403526 56%,#29353c);
          box-shadow:inset 0 1px 0 #fff4,0 4px 14px #0008;}
        .dra-history-refresh:active:not(:disabled) {transform:translateY(1px);box-shadow:inset 0 1px 2px #0008;}
        .dra-history-refresh:focus-visible {outline:3px solid #ffe5a8;outline-offset:3px;}
        .dra-history-refresh:disabled {opacity:.78;cursor:progress;}
        .dra-history-refresh.is-loading svg {animation:dra-history-spin 1s linear infinite;}
        .dra-history-refresh-status {font-size:12px;line-height:1.4;
          margin:0;color:#b4c0c9;overflow-wrap:anywhere;}
        .dra-history-refresh-status.success {color:#a9e7c1;}
        .dra-history-refresh-status.busy {color:#e7c78e;}
        .dra-history-refresh-status.error {color:#f0b6ae;}
        @keyframes dra-history-spin {to{transform:rotate(360deg);}}
        @media(max-width:420px) {
          .dra-history-heading {gap:8px;}
          .dra-history-refresh {min-width:132px;padding:9px 11px;}
          .dra-history-heading-title > strong {font-size:12px;}
        }
        @media(prefers-reduced-motion:reduce) {
          .dra-history-refresh {transition:none;}
          .dra-history-refresh.is-loading svg {animation:none;}
        }
        /* Clear section boundaries, distinct job cards and compact technical notes. */
        .dra-g2-retry-test {margin-top:12px;padding:0 12px 11px;
          border:1px solid #5e7180;border-radius:12px;background:#1e2a35;}
        .dra-g2-retry-test summary {min-height:44px;display:list-item;
          padding:12px 2px;cursor:pointer;color:#e3c994;font-size:13px;font-weight:650;}
        .dra-g2-retry-test summary:focus-visible {outline:2px solid #ecd098;outline-offset:2px;}
        .dra-g2-retry-test button {min-height:44px;margin:6px 9px 3px 0;
          padding:8px 12px;border:1px solid #b29159;border-radius:11px;
          background:#302f2a;color:#f0d7a7;font:inherit;font-size:13px;font-weight:700;}
        .dra-g2-retry-test button:disabled {opacity:.55;}
        .dra-g2-retry-test .note {font-size:12px;line-height:1.55;}
        .dra-history-section {border-top:1px solid rgba(203,165,100,.55);
          margin-top:18px;padding-top:16px;}
        .dra-history-list {box-sizing:border-box;max-height:310px;min-height:0;
          overflow-y:auto;overscroll-behavior:contain;margin-top:10px;
          padding:4px 4px 5px 2px;scrollbar-color:#788591 #1a2530;}
        .dra-history-item {box-sizing:border-box;display:flex;flex-direction:column;
          gap:6px;position:relative;margin:0 2px 9px;padding:12px 13px;
          border:1px solid #516474;border-left:3px solid #8aa6b7;border-radius:12px;
          background:linear-gradient(125deg,rgba(43,58,69,.92),rgba(27,39,49,.9));
          box-shadow:inset 0 1px 0 rgba(255,255,255,.045),0 2px 6px #0003;}
        .dra-history-item:last-child {margin-bottom:0;}
        .dra-history-item.success {border-left-color:#65b98b;}
        .dra-history-item.failed {border-left-color:#d38281;}
        .dra-history-item.interrupted {border-left-color:#d8a767;}
        .dra-history-item.queued {border-left-color:#80b6d7;}
        .dra-history-item-head {display:flex;align-items:center;justify-content:space-between;
          gap:9px;min-width:0;flex-wrap:wrap;}
        .dra-history-item-head strong {font-size:13px;font-weight:750;color:#edf5fa;
          overflow-wrap:anywhere;line-height:1.4;}
        .dra-history-state {padding:4px 8px;flex:none;border-radius:999px;
          border:1px solid #678b77;background:rgba(39,104,66,.23);
          color:#bdebcf;font-size:11px;font-weight:700;}
        .dra-history-item.failed .dra-history-state {border-color:#9e6265;
          background:rgba(117,47,57,.18);color:#f2bdc2;}
        .dra-history-item.interrupted .dra-history-state {border-color:#b18a5c;
          background:rgba(125,84,34,.16);color:#f6d19c;}
        .dra-history-item.queued .dra-history-state {border-color:#648daa;
          background:rgba(40,88,119,.15);color:#bbddf4;}
        .dra-history-item-time {font-size:12px;color:#becbd4;
          overflow-wrap:anywhere;line-height:1.45;}
        .dra-history-scroll-hint {margin:7px 0 0;font-size:11px;color:#a9bac6;}
        .dra-logs-notes {box-sizing:border-box;margin-top:17px;border:1px solid #536475;
          border-radius:12px;background:linear-gradient(120deg,rgba(37,50,59,.8),rgba(25,37,47,.82));}
        .dra-logs-notes summary {padding:13px 14px;min-height:44px;box-sizing:border-box;
          color:#d6e2e9;font-size:13px;font-weight:700;line-height:1.45;cursor:pointer;}
        .dra-logs-notes summary::marker {color:#dfbc79;}
        .dra-logs-notes summary:focus-visible {outline:2px solid #f0cd86;outline-offset:3px;}
        .dra-logs-notes[open] {border-color:#ad925f;}
        .dra-logs-notes[open] summary {border-bottom:1px solid #52606e;color:#f0d6a2;}
        .dra-logs-notes-content {padding:3px 14px 12px;}
        .dra-logs-notes-content p {margin:10px 0 0;}
        @media(max-width:420px) {
          .dra-history-item {padding:11px 10px;}
          .dra-history-list {max-height:300px;}
        }
        .dra-logs-panel .note {font-size:12px;line-height:1.45;}
        @media (max-width:420px) {.dra-logs-actions {grid-template-columns:1fr;}
          .dra-deployment-heading h2 {font-size:17px;}}

        .dra-batch-review-dialog {max-width:min(1260px,calc(100vw - 24px));
          width:100%;max-height:min(92vh,980px);overflow:auto;box-sizing:border-box;}
        .dra-batch-review-table-wrap {margin:16px 0;overflow:auto;border:1px solid #496172;
          border-radius:10px;max-height:56vh;}
        /* More specific than the later generic .git-dialog width:560px rule. */
        .git-dialog.dra-batch-review-dialog {
          width:min(1520px,calc(100vw - 32px));
          max-width:calc(100vw - 32px);
          min-width:0;
        }
        @media(max-width:640px) {
          .git-dialog.dra-batch-review-dialog {width:calc(100vw - 16px);max-width:calc(100vw - 16px);}
        }
        .dra-batch-review-table {width:100%;border-collapse:collapse;text-align:left;
          min-width:810px;font-size:13px;}
        .dra-batch-review-table th,.dra-batch-review-table td {vertical-align:top;
          padding:12px;border-bottom:1px solid #344b58;}
        .dra-batch-review-table thead th {position:sticky;top:0;z-index:1;
          background:#263845;color:#d8ecf5;}
        .dra-batch-review-table td code {overflow-wrap:anywhere;word-break:break-all;
          font-size:12px;color:#ddf5fd;}
        .dra-batch-review-table tbody th {color:#e3eef5;font-weight:720;min-width:130px;}
        .dra-batch-review-table tbody .note {margin-top:3px;color:#aebfca;}
        .dra-review-arrow {font-size:19px;color:#83d8e4;text-align:center;}
        .dra-review-unknown {background:rgba(142,91,24,.09);}
        .dra-review-counts {white-space:nowrap;margin-top:4px;font-variant-numeric:tabular-nums;}
        .dra-review-add {color:#68dda3;font-weight:750;}
        .dra-review-remove {color:#ff8a8a;font-weight:750;}
        .dra-review-edit {color:#f3c879;font-weight:750;}
        /* Mobile review: readable disclosure cards instead of cropped desktop columns. */
        .dra-batch-review-mobile-list {display:none;}
        @media(max-width:900px) {
          .dra-batch-review-table-wrap {display:none;}
          .dra-batch-review-mobile-list {display:grid;gap:8px;margin:12px 0;min-width:0;}
          .dra-review-mobile-card {min-width:0;border:1px solid #456578;border-radius:10px;
            background:#1e2429;overflow:hidden;}
          .dra-review-mobile-card.is-current {border-color:#4a6860;}
          .dra-review-mobile-card.has-changes {border-left:4px solid #47b8ca;}
          .dra-review-mobile-card.is-current {border-left:4px solid #51646b;}
          .dra-review-mobile-version-line {grid-column:1;display:flex;gap:5px 9px;align-items:baseline;flex-wrap:wrap;min-width:0;}
          .dra-review-mobile-changes {display:inline-flex;align-items:center;flex-wrap:wrap;gap:5px;}
          .dra-review-mini-count {display:inline-block;padding:2px 6px;border:1px solid currentColor;
            border-radius:6px;font-size:12px;font-weight:800;font-variant-numeric:tabular-nums;line-height:1.25;}
          .dra-review-mini-count.dra-review-add {color:#77e7ae;background:rgba(36,143,87,.18);}
          .dra-review-mini-count.dra-review-edit {color:#ffe082;background:rgba(167,120,15,.21);}
          .dra-review-mini-count.dra-review-remove {color:#ff667f;background:rgba(173,40,65,.19);}
          .dra-review-mini-current {font-size:12px;color:#b7c8cf;font-weight:600;}
          .dra-review-mobile-card summary {display:grid;grid-template-columns:minmax(0,1fr) 22px;
            align-items:center;gap:4px 8px;list-style:none;cursor:pointer;padding:11px 12px;
            min-height:68px;}
          .dra-review-mobile-card summary::-webkit-details-marker {display:none;}
          .dra-review-mobile-card summary:focus-visible {outline:2px solid #92cbdc;outline-offset:-2px;}
          .dra-review-mobile-project {grid-column:1;font-size:14px;line-height:1.35;overflow-wrap:anywhere;}
          .dra-review-mobile-versions {font-size:13px;line-height:1.35;overflow-wrap:anywhere;}
          .dra-review-mobile-versions b {color:#83d8e4;margin:0 6px;}
          .dra-review-mobile-hash {grid-column:1;font-size:12px;color:#b4cbd6;}
          .dra-review-mobile-hash code {color:#e1f5fd;font-size:12px;}
          .dra-review-mobile-chevron {grid-column:2;grid-row:1 / span 3;align-self:center;
            color:#9ad7e9;font-size:24px;text-align:center;transition:transform .16s;}
          .dra-review-mobile-card[open] .dra-review-mobile-chevron {transform:rotate(180deg);}
          .dra-review-mobile-detail-list {display:grid;gap:10px;padding:12px;
            border-top:1px solid #456070;background:rgba(13,25,34,.45);}
          .dra-review-mobile-detail-list > div {display:grid;gap:2px;min-width:0;}
          .dra-review-mobile-detail-list > div > span:first-child {font-size:11px;color:#aebfca;}
          .dra-review-mobile-detail-list strong,.dra-review-mobile-detail-list code {
            font-size:12px;line-height:1.45;overflow-wrap:anywhere;word-break:break-word;}
          .dra-review-full-commit {user-select:text;word-break:break-all !important;}
          .dra-review-copy-commit {justify-self:start;padding:8px 12px;min-height:40px;
            font-size:12px;border:1px solid #518da6;border-radius:8px;background:#1e566d;color:#eefbff;}
          .dra-batch-review-dialog .dra-batch-review-warning {padding:9px 11px;font-size:12px;}
          .dra-batch-review-dialog .dra-batch-review-actions {position:sticky;bottom:0;z-index:2;
            padding:9px 0 2px;background:var(--primary-background-color,#1d1d1d);}
          .dra-batch-review-dialog .dra-batch-review-actions button {font-size:12px;line-height:1.3;}
          .dra-batch-review-dialog > .note code {overflow-wrap:anywhere;word-break:break-all;}
        }
        .dra-batch-review-warning {background:#45331b;color:#f9d7a5;
          border:1px solid #ab7b32;border-radius:9px;padding:12px;font-size:13px;}
        .dra-batch-review-ack {display:flex;gap:12px;align-items:flex-start;margin:12px 0;
          padding:13px;border:1px solid #658b9d;border-radius:10px;line-height:1.5;}
        .dra-batch-review-ack input {width:20px;height:20px;flex:none;accent-color:#0097c4;}
        .dra-batch-review-actions {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;}
        .dra-batch-review-actions button {min-width:0;min-height:44px;padding:8px 10px;white-space:normal;}
        @media(max-width:640px){
          .dra-batch-review-dialog {max-height:94vh;}
          .dra-batch-review-table-wrap {max-height:50vh;}
          .dra-batch-review-actions {grid-template-columns:repeat(2,minmax(0,1fr));}
          .dra-batch-review-actions button:last-child {grid-column:1/-1;}
          .dra-batch-review-actions button {width:100%;}
        }
        @media(max-width:380px) { .dra-batch-review-actions {grid-template-columns:1fr;} .dra-batch-review-actions button:last-child {grid-column:auto;} }
        .dra-deploy-action {box-sizing:border-box;width:100%;margin:0;padding:17px 18px;
          min-height:79px;border-radius:14px;display:flex;gap:12px;align-items:center;justify-content:center;
          text-align:center;font-size:clamp(16px,2vw,21px);font-weight:800;letter-spacing:.005em;
          color:#f1fbff;border:1px solid #00abcf;
          background:linear-gradient(145deg,#088cb4,#067da5 55%,#095b83);
          box-shadow:inset 0 1px 0 rgba(244,255,255,.32),0 3px 10px #001b2c70;}
        .dra-deploy-action .project-icon {flex:none;}
        .dra-deploy-action.stage-2 {color:#ffdfb0;border-color:#da8c29;
          background:linear-gradient(145deg,#73501f,#704716 60%,#58391d);
          box-shadow:inset 0 1px 0 rgba(255,237,200,.2),0 3px 9px #0005;}
        .dra-deploy-action.stage-2:disabled {opacity:1;cursor:not-allowed;transform:none;}
        .dra-deploy-action.up-to-date {color:#d2f5fb;border-color:#3e99ae;
          background:linear-gradient(145deg,#20495a,#205160 58%,#183b4d);
          box-shadow:inset 0 1px 0 rgba(225,251,255,.17),0 3px 8px #0004;}
        .dra-deploy-action.up-to-date:disabled {opacity:1;cursor:default;transform:none;}
        .dra-up-to-date-note {margin-top:11px;padding:11px 14px;border:1px solid #427b89;
          border-radius:10px;background:rgba(27,90,110,.16);color:#c7e9ed;font-size:13px;}
        .dra-up-to-date-repeat {margin-top:9px;min-height:35px;}
        .dra-history-only {margin-top:10px;padding:9px 12px;border:1px solid #425361;
          border-radius:9px;color:#acb8c1;background:#1d2831;font-size:12px;}
        .dra-history-only summary {cursor:pointer;font-weight:650;}
        .dra-history-only p {margin:8px 0 0;overflow-wrap:anywhere;}
        .dra-deploy-action.is-busy {opacity:1;border-color:#56bfdc;cursor:progress;}
        .dra-deploy-action.is-busy .project-icon {animation:dra-deploy-spin 1.15s linear infinite;}
        .dra-deploy-action.is-busy {overflow:hidden;}
        .dra-deploy-action.is-busy::after {
          content:"";position:absolute;inset:0;transform:translateX(-110%);
          background:linear-gradient(90deg,transparent,rgba(255,255,255,.28),transparent);
          animation:dra-deploy-sheen 1.15s ease-in-out infinite;pointer-events:none;
        }
        @keyframes dra-deploy-sheen {55%,100% {transform:translateX(110%);}}
        @keyframes dra-deploy-spin {to {transform:rotate(360deg);}}
        .dra-deploy-progress {overflow:hidden;position:relative;margin:17px 0 15px;height:4px;
          border-radius:99px;border:1px solid #456272;
          background:linear-gradient(180deg,#07141e,#273d49 54%,#101f2b);
          box-shadow:inset 0 1px 3px #000b,0 1px 0 #b8dce01c;}
        .dra-deploy-progress-fill {height:100%;width:0%;position:relative;border-radius:inherit;
          background:linear-gradient(90deg,#158db8,#39d6ed 52%,#1677ac);
          box-shadow:0 0 7px #32d0ecaa;transition:width .32s ease;}
        .dra-deploy-progress.verified .dra-deploy-progress-fill {width:25%;}
        .dra-deploy-progress.up-to-date .dra-deploy-progress-fill {width:25%;
          background:linear-gradient(90deg,#397d90,#63b7c4);box-shadow:none;}
        .dra-deploy-progress.completed .dra-deploy-progress-fill {width:100%;
          background:linear-gradient(90deg,#267d54,#44d99b 55%,#7ce0aa);}
        .dra-deploy-progress.failed .dra-deploy-progress-fill {width:75%;
          background:linear-gradient(90deg,#a84049,#e76c65);}
        .dra-deploy-progress.running .dra-deploy-progress-fill {
          width:42%;animation:dra-v1-loader-sweep 1.05s ease-in-out infinite;
          background:linear-gradient(90deg,transparent,#39d7f3 28%,#c1faff 55%,#1b9ec6);
        }
        @keyframes dra-v1-loader-sweep {
          0% {transform:translateX(-110%);}
          55% {transform:translateX(85%);}
          100% {transform:translateX(245%);}
        }
        .dra-deploy-steps {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;}
        .dra-deploy-step {box-sizing:border-box;display:flex;align-items:center;justify-content:center;
          flex-direction:column;gap:7px;min-height:77px;padding:10px 5px;text-align:center;
          border:1px solid #44535b;border-radius:10px;color:#a3aeb8;
          background:linear-gradient(140deg,#26313a,#1c252e);font-size:12px;font-weight:700;}
        .dra-deploy-step svg {flex:none;}
        .dra-deploy-step.blue.current {border-color:#0eaed8;color:#c7f6ff;background:rgba(0,145,188,.16);}
        .dra-deploy-step.orange.current {border-color:#c48838;color:#ffd7a4;background:rgba(160,99,24,.14);}
        .dra-deploy-step.blue.done {border-color:#4fba8a;color:#abe6c6;background:rgba(29,113,76,.17);}
        .dra-deploy-step.orange.pending {border-color:#806c4b;color:#c2aa86;}
        .dra-deploy-step.red.pending {border-color:#70464a;color:#ae858a;}
        .dra-deploy-step.green.pending {border-color:#4a6657;color:#92b39d;}
        .dra-deploy-step.green.current {border-color:#48bd86;color:#b6f6d5;background:rgba(24,116,75,.28);}
        .dra-deploy-step.current-review {border-color:#4b9cac;color:#c1e8ee;
          background:rgba(33,95,112,.2);}
        .dra-deploy-step.not-required {border-color:#3d4e58;color:#8799a4;
          background:linear-gradient(140deg,#212b34,#1b252d);}
        .dra-deploy-step.done {border-color:#4fba8a;color:#abe6c6;background:rgba(29,113,76,.17);}
        .dra-deploy-step.red.failed {border-color:#e16c72;color:#ffc1c2;background:rgba(145,36,45,.25);}
        .dra-deploy-action.stage-4 {border-color:#45ba83;color:#d6ffe9;
          background:linear-gradient(135deg,#155b40,#1e7650);}
        .dra-deploy-action.stage-3.has-error {border-color:#dc6c70;color:#fff0f0;
          background:linear-gradient(135deg,#713037,#4f2027);}
        .project-management-dialog .project-management-table button.project-settings-open-style {
          width:48px;height:48px;min-width:48px;min-height:48px;max-width:48px;
          margin:0;padding:8px;display:inline-flex;align-items:center;justify-content:center;
        }
        .dra-tests-panel {margin-top:12px;border:1px solid #455f6c;
          border-radius:12px;background:linear-gradient(145deg,#1a2830,#17232b);}
        .dra-tests-expander>summary {cursor:pointer;padding:15px 18px;display:flex;
          flex-wrap:wrap;justify-content:space-between;gap:8px;align-items:center;
          color:#f0d39f;font-size:14px;font-weight:700;}
        .dra-tests-expander>summary .note {font-size:11px;font-weight:400;}
        .dra-tests-content {padding:0 18px 16px;}
        .dra-test-item {padding:13px;border:1px solid #425c6c;border-radius:9px;
          background:#20313d;}
        .dra-test-item-heading {display:flex;flex-wrap:wrap;justify-content:space-between;gap:8px;
          color:#f3d69f;}
        .dra-test-item .note {line-height:1.55;}
        .dra-test-actions {display:flex;flex-wrap:wrap;align-items:center;gap:12px;margin:10px 0;}
        .dra-test-actions button {min-height:42px;}
        .dra-test-result {padding:10px;border-left:3px solid #55bdd5;background:#162936;
          border-radius:5px;overflow-wrap:anywhere;}
        .dra-deployment-runtime {display:flex;flex-wrap:wrap;gap:6px;align-items:center;
          margin:12px 0 6px;color:#acbdc9;font-size:12px;}
        .dra-deployment-runtime .runtime-ok {color:#8dd9b1;}
        .dra-deployment-runtime .runtime-warning {color:#f4bd79;}
        .dra-deployment-status {margin:14px 0 7px;font-size:13px;}
        .dra-deployment-result {margin-top:12px;padding:12px;border:1px solid #426f63;
          background:rgba(24,88,65,.13);border-radius:10px;display:flex;flex-direction:column;gap:5px;font-size:13px;}
        .dra-deployment-hint {font-size:12px;margin:15px 0 0;}
        .dra-post-install {margin:12px 0;padding:15px;border:1px solid #536c76;
          border-radius:11px;background:linear-gradient(145deg,#1d3039,#1b2831);}
        .dra-post-install>strong {display:block;color:#ccece1;margin-bottom:7px;}
        .dra-post-install .note {display:block;margin:6px 0 12px;}
        .dra-post-install button {min-height:42px;padding:9px 15px;border-radius:8px;}
        .dra-post-install .dra-frontend-refresh {border:1px solid #42a8bd;color:#ddf9ff;
          background:linear-gradient(145deg,#187995,#18546b);}
        .dra-post-install .dra-ha-restart {border:1px solid #c88f36;color:#ffe2b3;
          background:linear-gradient(145deg,#795122,#5e3f21);}
        .dra-restart-confirm {margin-top:12px;border:1px solid #bd914f;
          border-radius:9px;background:#392c22;padding:13px;}
        .dra-restart-confirm p {color:#ffe6c7;margin:5px 0 12px;}
        .dra-restart-buttons {display:flex;flex-wrap:wrap;gap:9px;}
        .dra-restart-confirm .dra-restart-cancel {border:1px solid #67818e;background:#273943;color:#e5eff3;}
        .dra-restart-message {margin:10px 0 0;color:#d4e9f1;font-size:13px;}
        @media(max-width:600px){
          .dra-deploy-steps {grid-template-columns:repeat(2,minmax(0,1fr));}
          .dra-source-meta {grid-template-columns:repeat(2,minmax(0,1fr));}
          .dra-deploy-action {min-height:76px;padding:14px 12px;}
        }
        @media(prefers-reduced-motion:reduce){
          .dra-deploy-action.is-busy .project-icon {animation:none;}
          .dra-deploy-action.is-busy::after {animation:none;display:none;}
          .dra-deploy-progress.running .dra-deploy-progress-fill {animation:none;width:40%;}
          .dra-deploy-progress-fill {transition:none;}
        }
        .dra-warning {border:1px solid #987323;background:rgba(160,110,10,.12);border-radius:10px;padding:14px;margin-top:14px}
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
        /* Compact batch control and V2 system card, styled consistently with project rows. */
        .project-management-dialog .project-batch-picker-row {
          background:linear-gradient(95deg,rgba(38,77,105,.30),rgba(28,41,54,.22));
          border-left:3px solid #78aac6;
        }
        .project-management-dialog .project-batch-status {
          display:inline-flex;align-items:center;color:#b8d8e7;min-height:33px;
          padding:5px 8px;border:1px solid #607a8c;border-radius:8px;font-size:12px;
          background:rgba(36,71,90,.2);
        }
        .project-batch-card,.project-v2-card {box-sizing:border-box;margin-top:14px;border-radius:12px;
          border:1px solid #536d7b;background:linear-gradient(120deg,rgba(46,73,90,.27),rgba(22,29,36,.17));
          box-shadow:inset 3px 0 0 #6594ac,inset 0 1px 0 rgba(225,243,255,.07);}
        .project-batch-card {padding:12px 14px;}
        .project-batch-head,.project-v2-card {display:flex;align-items:center;gap:13px;}
        .project-batch-icon {display:flex;flex:none;color:#c7eaf7;}
        .project-batch-text,.project-v2-details {display:flex;flex:1 1 auto;min-width:0;flex-direction:column;gap:4px;}
        .project-batch-text strong,.project-v2-details strong {font-size:15px;}
        .project-batch-text .note,.project-v2-details .note {font-size:12px;overflow-wrap:anywhere;}
        .project-batch-count {font-size:12px;color:#bde5d8;font-weight:600;}
        .project-batch-edit {display:inline-flex;align-items:center;justify-content:center;gap:7px;
          flex:none;min-height:42px;margin:0;padding:9px 11px;white-space:nowrap;
          border:1px solid #7095a6;border-radius:10px;
          background:linear-gradient(155deg,#355667,#1c3340);color:#e9f7ff;font-weight:600;}
        .project-batch-card > p.note {margin:8px 0 0;}
        .project-batch-card > p.note:empty {display:none;}
        .project-v2-card {padding:11px 13px;border-color:#6d8e9d;box-shadow:inset 3px 0 0 #7db3ce,inset 0 1px 0 rgba(227,247,255,.13);}
        .project-v2-status {font-size:12px;font-weight:700;border:1px solid;padding:7px 9px;
          border-radius:8px;white-space:nowrap;}
        .project-v2-status.configured {color:#c5efdb;border-color:#4d9d79;background:rgba(19,103,64,.24);}
        .project-v2-status.unconfigured {color:#d6dce3;border-color:#6a7d8c;background:rgba(81,96,108,.19);}
        .project-v2-settings-button {display:inline-flex;align-items:center;justify-content:center;flex:none;
          width:44px;height:44px;min-width:44px;margin:0;padding:8px;
          background:linear-gradient(155deg,#526d7e,#203744 56%,#142632);
          border:1px solid #829dad;border-radius:10px;
          box-shadow:inset 0 1px 0 rgba(255,255,255,.55),inset 0 -2px 3px rgba(0,0,0,.6),0 2px 5px #0006;
          color:#d6f5ff;}
        .project-v2-settings-button .project-icon {filter:drop-shadow(0 1px 2px #000a);}
        .project-v2-settings-button:not(:disabled):hover,.project-batch-edit:not(:disabled):hover {filter:brightness(1.18);}
        .project-v2-settings-button:not(:disabled):active,.project-batch-edit:not(:disabled):active {transform:translateY(2px) scale(.97);filter:brightness(.83);}
        .project-v2-settings-dialog {box-sizing:border-box;display:flex;flex-direction:column;overflow:hidden;
          width:min(100%,690px);max-height:92dvh;border:1px solid #7197aa;
          box-shadow:0 20px 55px #000a,inset 0 1px 0 #dff4ff30;}
        .project-v2-settings-dialog > header {display:flex;align-items:center;justify-content:space-between;
          gap:12px;flex:0 0 auto;padding-bottom:12px;border-bottom:1px solid #567281;}
        .project-v2-settings-dialog > header h2 {font-size:19px;margin:0 0 4px;}
        .project-v2-settings-dialog > header p {margin:0;}
        .project-v2-settings-dialog > header button {margin:0;min-width:43px;width:43px;height:43px;
          display:inline-flex;align-items:center;justify-content:center;padding:8px;flex:none;}
        .project-v2-settings-scroll {box-sizing:border-box;flex:1 1 auto;min-height:0;overflow-y:auto;
          overflow-x:hidden;overscroll-behavior:contain;padding:12px 3px 0 0;scrollbar-gutter:stable;}
        .project-v2-settings-scroll h3 {margin:11px 0 8px;font-size:16px;}
        .v2-token-buttons {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;margin:11px 0;}
        .v2-token-buttons button {width:100%;min-width:0;margin:0;padding:10px 8px;
          min-height:42px;white-space:normal;font-weight:600;line-height:1.25;font-size:13px;}
        .v2-token-buttons button:not(:disabled):active {transform:translateY(2px) scale(.98);filter:brightness(.83);}
        .v2-source-advanced {border:1px solid #455865;border-radius:10px;padding:9px 12px;margin-top:13px;}
        .v2-source-advanced summary {cursor:pointer;font-weight:600;color:#c6e3f0;min-height:25px;}
        .v2-source-advanced label {margin-top:14px;}
        .v2-source-advanced > .note {margin:9px 0;}
        @media(max-width:410px) {
          .v2-token-buttons {gap:7px;}
          .v2-token-buttons button {font-size:12px;padding:9px 5px;}
        }

        .project-v2-settings-scroll label {display:block;}
        .project-v2-settings-scroll .project-text {width:100%;box-sizing:border-box;}
        @media(max-width:760px) {
          .project-batch-head {flex-wrap:wrap;gap:9px;}
          .project-batch-edit {width:100%;}
          .project-v2-card {flex-wrap:wrap;gap:9px;}
          .project-v2-details {flex-basis:calc(100% - 60px);}
          .project-v2-status {order:3;font-size:11px;}
          .project-v2-settings-button {margin-left:auto;}
          .project-v2-settings-dialog {max-height:94dvh;padding:14px;}
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
        .project-access-legend > summary {
          list-style:none; display:flex; justify-content:space-between; align-items:center;
          gap:12px; cursor:pointer; padding:8px 2px;
        }
        .project-access-legend > summary::-webkit-details-marker {display:none;}
        .project-access-chevron {display:inline-block; transition:transform .15s ease;}
        .project-access-legend[open] .project-access-chevron {transform:rotate(180deg);}
        /* The access level itself is a compact badge; the button remains a usable test target. */
        .project-management-dialog .project-management-table button.source-check {
          width:56px !important; min-width:56px !important; max-width:56px !important;
          height:42px !important; min-height:42px !important; padding:0 !important;
          display:flex !important; align-items:center !important; justify-content:center !important;
          border-radius:22px !important; gap:0 !important;
          box-sizing:border-box; text-align:center !important;
          background:linear-gradient(155deg,#487c68 0%,#274b42 32%,#122f30 54%,#315e50 100%) !important;
          border:1px solid #6eaa94 !important;
          box-shadow:inset 0 1px 0 rgba(230,255,247,.42),inset 0 -2px 4px rgba(0,0,0,.48),0 2px 5px rgba(0,0,0,.44) !important;
          color:#e3fff3 !important;
        }
        .project-management-dialog .project-management-table button.source-check.failure {
          background:linear-gradient(155deg,#854545,#47292d,#2a181f) !important;
          border-color:#c37a80 !important;color:#fff1f1 !important;
        }
        .project-management-dialog .project-management-table button.source-check.unverified,
        .project-management-dialog .project-management-table button.source-check.checking {
          background:linear-gradient(155deg,#5e6975,#33404d,#1e2934) !important;
          border-color:#8193a3 !important;color:#f2f6fc !important;
        }
        .project-management-dialog .project-management-table button.source-check .project-icon {
          display:none;
        }
        .project-management-dialog .project-management-table button.source-check .project-status-label {
          font-size:13px; line-height:1.2; font-weight:750; display:block; width:100%;
          text-align:center !important; margin:0 !important; padding:0 !important;
        }
        /* Wide notebook / iPad landscape: show source and execution side by side.
           Mobile and narrow split views retain their original single column. */
        @media (min-width: 1150px) {
          #dra-main-view {
            display:grid;
            grid-template-columns:minmax(0, 0.92fr) minmax(0, 1.08fr);
            grid-template-areas:"project deployment" "source deployment" "tests tests";
            gap:12px;
            align-items:start;
          }
          #dra-main-view[hidden] {display:none;}
          #dra-main-view > .dra-projectbar {grid-area:project;min-width:0;margin:0;}
          #dra-main-view > .dra-source-card {grid-area:source;min-width:0;margin:0;}
          #dra-main-view > .dra-deployment-panel {grid-area:deployment;min-width:0;margin:0;}
          #dra-main-view > .dra-tests-panel {grid-area:tests;min-width:0;margin:0;}
          #dra-main-view .dra-project-picker-field {min-width:0;}
          #dra-main-view .dra-project-picker-trigger {min-width:0;}
          #dra-main-view .dra-deploy-steps {gap:5px;}
          #dra-main-view .dra-deploy-step {min-height:62px;padding:8px 3px;}
        }
        /* Compact batch status, expandable for a full six-project audit. */
        .dra-batch-observer-details {margin-top:6px;}
        .dra-batch-observer-details summary {cursor:pointer;font-weight:600;}
        .dra-batch-observer-grid {display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:5px 12px;margin-top:8px;}
        .dra-batch-observer-grid > div {margin:0;overflow-wrap:anywhere;}
      </style>
      <main>
        <header class="dra-head">
          <div><strong>DEPLOY RELAY AGENT V2</strong><div class="note">Sicheres Deployment für Git-Projekte</div></div>
          <div class="dra-actions">
          <span class="dra-lock">${mainPreviewVerified && !previewNoChanges && mainProject?.active !== false &&
            this._serverVersion === DRA_V2_UI_VERSION ? "FREIGABEBEREIT" : "GESPERRT"}</span>
          <div id="dra-version" class="dra-version ${runtimeVersionState}"
            aria-label="Versionsübersicht: Oberfläche ${uiVersionLabel}; HA-Laufzeit ${runtimeVersionLabel}">
            <span class="dra-version-heading">Oberfläche</span>
            <strong class="dra-version-number">${uiVersionLabel}</strong>
            <span class="dra-runtime-version" role="status" aria-live="polite">
              ${versionMismatch ? "Abweichung · " : ""}HA-Laufzeit: ${runtimeVersionLabel}
            </span>
          </div>
          <button id="dra-refresh">Aktualisieren</button>
          <button id="dra-toggle">${this._view === "main" ? "Diagnose & Einstellungen" : "Hauptmenü"}</button></div>
        </header>
        ${observerVisible ? `<section class="dra-global-observer ${this._installStatusError ? "is-stale" :
          observedJobs.length && observedJobs.every(j=>j.status==="success") ? "is-complete" :
          observedJobs.some(j=>["failed","interrupted","recovery_required"].includes(j.status)) ? "is-failed" : ""}"
          aria-label="Serverseitiger Installationsstatus" role="status" aria-live="polite">
          <div class="dra-observer-top">
            <strong>${this._installStatusError
              ? "Installationsstatus · Verbindung unterbrochen"
              : observedJobs.length
                ? observedJobs.some(j=>["queued","running","waiting_for_resource","cancel_requested"].includes(j.status))
                  ? "Installation auf Home Assistant läuft"
                  : "Installationsauftrag abgeschlossen"
                : "Installationsstatus wird abgerufen"}</strong>
            <span class="dra-observer-note">${this._installStatusError
              ? "Letzter bekannter Stand · nicht aktuell"
              : observedJobs.length ? "Serverseitig bestätigt · unabhängig vom Bediengerät"
              : "Verbindung mit der Auftragsverwaltung wird geprüft"}</span>
          </div>
          ${observedJobs.map(job=>{
            const exact = job.progress_exact === true && Number.isInteger(job.progress_percent) &&
              job.progress_percent >= 0 && job.progress_percent <= 100;
            const name = observerJobName(job);
            const phase = observerPhase[job.phase] || observerPhase[job.status] ||
              job.phase || job.status || "Unbekannt";
            const testPacing = job.project_key==="test_repo_dra_v2" &&
              job.phase==="preflight" && Number.isInteger(job.current_index) &&
              Number.isInteger(job.total_count) && job.total_count > 0;
            const testProgress = testPacing
              ? " · Testdatei " + Math.min(job.current_index+1,job.total_count) +
                " von " + job.total_count : "";
            const finished = job.status==="success" ? "Erfolgreich abgeschlossen" :
              ["failed","interrupted","recovery_required"].includes(job.status) ?
                "Fehler / Prüfung erforderlich" : phase;
            return `<div class="dra-observer-item">
              <div class="dra-observer-line">
                <strong>${this._escapeProject(name)}</strong>
                <span>${this._escapeProject(finished)}${testProgress}${exact ? " · " + job.progress_percent + " %" : ""}</span>
              </div>
              <div class="dra-observer-meter" aria-hidden="true"><span style="width:${exact ? job.progress_percent : 0}%"></span></div>
              <div class="dra-observer-note">Auftrag ${this._escapeProject((job.operation_id || "").slice(0,12))}
                · ${this._installStatusError ? "Verbindungsabbruch – Serverstatus offen" :
                  job.status==="success" ? "Abschluss serverseitig bestätigt" :
                  "Status wird automatisch aktualisiert"}${!exact && job.status!=="success" ?
                  " · keine verlässliche Prozentangabe" : ""}</div>
            </div>`;
          }).join("")}
        </section>` : ""}
        ${this._restartSummary?.required ? `<section class="dra-global-observer" role="status"
          aria-label="Ausstehender Home-Assistant-Neustart">
          <div class="dra-observer-top"><strong>HA-Neustart vorgemerkt · ${this._restartSummary.count} ${this._restartSummary.count===1?"Update":"Updates"}</strong>
            <span class="dra-observer-note">Installationen abgeschlossen · gemeinsamer Neustart möglich</span>
          </div>
          <p class="dra-observer-note">${this._restartSummary.items.map(item=>
            this._escapeProject(this._installProjectNames[item.project_key] || item.project_key)).join(" · ")}</p>
          <p class="dra-observer-note">Weitere unabhängige Aktualisierungen dürfen vorher installiert werden.
            Bei fachlichen Abhängigkeiten kann ein früherer Neustart erforderlich sein.</p>
          ${this._restartSummary.restart_requested ? `<strong>Neustart wurde bereits angefordert.</strong>` :
            this._deferredRestartDialogOpen ? `<div class="dra-restart-confirm">
              <strong>Home Assistant jetzt einmalig neu starten?</strong>
              <p>Alle aktiven Installationen müssen zuvor abgeschlossen sein.</p>
              <button type="button" id="dra-deferred-restart-cancel"
                ${this._deferredRestartBusy?"disabled":""}>Abbrechen</button>
              <button type="button" id="dra-deferred-restart-confirm"
                ${this._deferredRestartBusy || this._installStatusError || !this._restartSummary.operation_id || runningJobs.length?"disabled":""}>Ja, Home Assistant neu starten</button>
            </div>` :
            `<button type="button" id="dra-deferred-restart-open"
              ${this._installStatusError || !this._restartSummary.operation_id || runningJobs.length?"disabled":""}>Gemeinsamen HA-Neustart ausführen</button>`}
          ${this._deferredRestartMessage ? `<p role="status">${this._escapeProject(this._deferredRestartMessage)}</p>` : ""}
        </section>` : ""}
        ${this._batchStatus && ["inspecting_sources","preparing","prepared","failed","queued","running","success","stopped","interrupted"].includes(this._batchStatus.status) ?
          `<section class="dra-global-observer" role="status" aria-label="Geräteübergreifender Sammelauftrag">
            <div class="dra-observer-top"><strong>Sammelauftrag · ${this._escapeProject(this._batchStatus.status)}</strong>
              <span class="dra-observer-note">${this._batchStatus.current} von ${this._batchStatus.total}
                ${this._batchStatus.status === "preparing" ? "Quellen geprüft" : "Teilaufträgen abgeschlossen"}</span>
            </div>
            ${this._batchStatus.items.length ? `<details class="dra-batch-observer-details">
              <summary>Projektstatus anzeigen (${this._batchStatus.items.length})</summary>
              <div class="dra-batch-observer-grid">
                ${this._batchStatus.items.map(item => `<div class="dra-observer-note">
                  <strong>${this._escapeProject(this._installProjectNames[item.project_key] || item.project_key)}</strong>
                  · ${this._escapeProject(item.status)}
                  ${item.operation_id ? " · Auftrag " + this._escapeProject(item.operation_id.slice(0,12)) : ""}
                </div>`).join("")}
              </div>
            </details>` : ""}
            ${this._batchStatus.status==="prepared" && !this._batchReviewOpen ?
              `<button type="button" id="dra-batch-review-handoff"
                ${this._mainBatchBusy || this._batchStatusError ? "disabled" : ""}>
                Prüfübersicht auf diesem Gerät übernehmen
              </button>` : ""}
            ${this._batchStatusError ? "<p>Statusabfrage unterbrochen – serverseitiger Auftrag bleibt bestehen.</p>" : ""}
          </section>` : ""}
        <section id="dra-main-view" ${this._view==="main"?"":"hidden"}>
          <article class="dra-projectbar">
            <div class="dra-project-picker-field">
              <strong id="dra-project-label">Projekt</strong>
              <button id="dra-project-picker-open" class="dra-project-picker-trigger"
                aria-haspopup="dialog" aria-label="Projekt auswählen" aria-expanded="${this._projectPickerOpen}"
                ${!this._projects.length ? "disabled" : ""}>
                <span class="dra-project-picker-current">
                  <span class="dra-project-picker-current-name">${this._mainBatchMode ? "Sammelupdate" : mainProject ? this._escapeProject(mainProject.name) : "Kein aktives Projekt"}</span>
                  <span class="dra-project-picker-current-repo">${this._mainBatchMode ? this._escapeProject(mainBatchProjects.length + " aktivierte Projekte · gemeinsam ausgewählt") : mainProject ? this._escapeProject(mainProject.repository) : "Projektverwaltung öffnen, um Projekte zu aktivieren"}</span>
                </span>
                <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor"
                  stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <path d="m6 9 6 6 6-6"/>
                </svg>
              </button>
            </div>
            <button id="dra-project-manage">Projektverwaltung</button>
            <button disabled>Sicherungen</button>
          </article>

          <article class="dra-source-card">
            <div class="dra-source-title">
              <h2>Quelle & Version</h2>
              <div class="dra-source-actions">
                <button type="button" id="dra-source-refresh" ${this._mainBatchMode ||
                  !mainProject || this._sourceHeadBusy || deploymentBusy || !!this._installPreparation ||
                  this._serverVersion !== DRA_V2_UI_VERSION ? "disabled" : ""}>
                  ${this._sourceHeadBusy ? "Prüfe …" : "Aktualisieren"}
                </button>
              <span class="dra-source-badge ${mainPreviewVerified ? (previewNoChanges ? "verified" : "changed") : "unverified"}">
                ${mainPreviewVerified ? (previewNoChanges ? "Aktuell" : "Änderungen vorhanden") : this._mainBatchMode ? "Mehrere Projekte" : "Prüfung ausstehend"}
              </span></div>
            </div>
            ${!this._mainBatchMode && this._sourceHeadMessage ? `<p class="note" role="status">${this._escapeProject(this._sourceHeadMessage)}</p>` : ""}
            ${this._mainBatchMode ? `
              <div class="dra-source-info">
                <strong>Sammelupdate · ${mainBatchProjects.length} von ${this._batchEligibleProjects().length} installierbaren Projekten</strong>
                <p class="note">Nur die ausgewählten Projekte werden in diesem Durchlauf geprüft.
                  Die gespeicherte Vorauswahl bleibt unverändert. DRA V1 und DRA V2
                  werden nach allen anderen Projekten in dieser Reihenfolge installiert.
                  DRA V2 muss für diesen Lauf bewusst ausgewählt werden.</p>
                <details class="dra-source-extra" id="dra-main-batch-selection"
                  ${this._mainBatchSelectionOpen ? "open" : ""}>
                  <summary>Projekte für diesen Lauf auswählen (${mainBatchProjects.length})</summary>
                  <div class="dra-main-batch-list">${batchActiveProjects.length
                    ? batchActiveProjects.map(p => {
                        const selfUpdate = this._isBatchSelfUpdate(p);
                        const checked = mainBatchProjects.some(x=>x.repository===p.repository);
                        const locked = ["prepared","queued","running"].includes(this._batchStatus?.status) ||
                          this._mainBatchBusy;
                        return `<label class="dra-main-batch-entry"
                            ${selfUpdate ? 'title="Eigenaktualisierung wird durch Home Assistant zuletzt installiert"' : ""}>
                          <input type="checkbox" class="dra-batch-run-choice"
                            data-repo="${this._escapeProject(p.repository)}"
                            ${checked ? "checked" : ""}
                            ${locked ? "disabled" : ""}
                            aria-label="${this._escapeProject(p.name)} für diesen Sammellauf auswählen">
                          <strong>${this._escapeProject(p.name)}</strong>
                          <span class="note">${this._escapeProject(p.repository)}
                            ${selfUpdate ? " · Eigenaktualisierung · zuletzt" : ""}</span>
                        </label>`;
                      }).join("")
                    : '<p class="note">Keine aktiven Projekte vorhanden.</p>'}</div>
                  <p class="note">${mainBatchProjects.length} Projekt${mainBatchProjects.length===1?"":"e"} ausgewählt.
                    Maximal 8 pro Durchlauf. Während einer vorbereiteten oder laufenden
                    Installation bleibt die Auswahl unverändert.</p>
                </details>
              </div>` : `
              <div class="dra-source-info ${mainPreviewVerified ? (previewNoChanges ? "verified" : "changed") : ""}">
                <strong>${mainPreviewVerified ? (previewNoChanges ? "Aktueller Installationsstand" : "Änderungen zum installierten Stand") : "Quellstand noch nicht geprüft"}</strong>
                <div class="dra-source-meta">
                  <div><span class="note">Projekt</span><strong>${mainProject ? this._escapeProject(mainProject.name) : "Kein aktives Projekt"}</strong></div>
                  <div><span class="note">Ausgewählt · Art</span><strong>${this._sourceChoices?.choices?.find(x=>x.ref===this._mainSourceRef.trim())?.kind || "branch"}</strong></div>
                  <div><span class="note">Ausgewählt · Ref</span><strong>${mainPreviewVerified
                    ? this._escapeProject(this._sourcePreview.source_ref || "Standardzweig")
                    : this._escapeProject(this._mainSourceRef.trim() || "Standardzweig")}</strong></div>
                  <div><span class="note">Ausgewählt · Commit</span><strong>${mainPreviewVerified
                    ? this._escapeProject(this._sourcePreview.source_commit?.slice(0,12) || "—")
                    : this._sourceChoices?.choices?.find(x=>x.ref===this._mainSourceRef.trim())?.commit?.slice(0,12) || "Noch nicht geprüft"}</strong></div>
                </div>
              </div>
              <details class="dra-source-extra" id="dra-source-advanced" ${this._sourceAdvancedOpen ? "open" : ""}>
                <summary>Erweiterte Quellenauswahl</summary>
                ${this._sourceChoices?.recommended ? `<p class="note"><strong>Empfohlene Quelle:
                  ${this._escapeProject(this._sourceChoices.recommended.channel)} ·
                  ${this._escapeProject(this._sourceChoices.recommended.ref)} ·
                  ${this._sourceChoices.recommended.commit.slice(0,12)}</strong>
                  ${this._sourceChoices.recommended.explicit ? "(Projektvorgabe)" : "(Standardzweig, keine Projektvorgabe)"}
                  <button type="button" id="dra-use-recommended">Empfehlung übernehmen</button></p>` : ""}
                <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:end;margin:10px 0">
                  <label for="dra-main-choice" style="flex:1;min-width:220px">Git-Zweig oder Tag
                    <select id="dra-main-choice" class="project-text" ${this._sourceChoices && this._sourceChoices.repository === mainProject?.repository ? "" : "disabled"}>
                      <option value="">${this._sourceChoices ? "Quelle auswählen …" : "Zuerst Zweige laden"}</option>
                      ${(this._sourceChoices && this._sourceChoices.repository === mainProject?.repository ? this._sourceChoices.choices : []).map(choice =>
                        `<option value="${this._escapeProject(choice.ref)}" ${this._mainSourceRef === choice.ref ? "selected" : ""}>
                          ${choice.kind === "branch" ? "Zweig" : "Tag"} · ${this._escapeProject(choice.ref)}
                          ${choice.ref === this._sourceChoices.default_ref ? "(Standard)" : ""} · ${choice.commit.slice(0,12)}
                        </option>`).join("")}
                    </select>
                  </label>
                  <button type="button" id="dra-load-source-choices" ${this._sourceChoicesBusy ? "disabled" : ""}>
                    ${this._sourceChoicesBusy ? "Lade …" : "Git-Zweige laden"}
                  </button>
                </div>
                <p class="note">${this._escapeProject(this._sourceChoicesMessage)}</p>
                <label for="dra-main-ref">Git-Referenz (Branch, Tag oder Commit; leer = Standardzweig)
                  <input id="dra-main-ref" class="project-text" placeholder="z. B. deploy/dev"
                    value="${this._escapeProject(this._mainSourceRef)}" autocomplete="off"/>
                </label>
                <p class="note">Eine andere Referenz setzt die bisherige Vorschau zurück.</p>
              </details>`}
          </article>
          <article class="dra-deployment-panel">
            ${this._mainBatchMode && this._batchStatus?.status === "failed" ? `<div class="dra-batch-top-error" role="alert" style="border:1px solid #b36a39;border-radius:8px;padding:10px;margin-bottom:10px;background:rgba(135,70,32,.14)">
              <strong>Sammelvorbereitung fehlgeschlagen – keine Installation gestartet</strong>
              <p style="margin:5px 0 0">Projekt: ${this._escapeProject(this._projects.find(p=>p.project_id===this._batchStatus.project_key)?.name || this._batchStatus.project_key || "Unbekannt")} ·
              Prüfschritt: ${this._escapeProject(this._batchStatus.check_stage || "Unbekannt")} ·
              Fehler: ${this._escapeProject(this._batchStatus.error_code || "Unbekannt")}</p>
              <p style="margin:5px 0 0" class="note">Die ausführliche Eingrenzung steht weiter unten im selben Abschnitt.</p>
            </div>` : ""}
            <div class="dra-deployment-heading">
              <h2>Deployment</h2>
              ${mainProject ? `<div class="dra-controller-chip ${this._controllerStatus?.controller === true ? "is-controller" :
                this._controllerStatus?.occupied === true ? "is-observer" : "is-pending"}"
                role="status" aria-live="polite" title="Geräteübergreifende Bedienung">
                <span class="dra-controller-dot" aria-hidden="true"></span>
                <span class="dra-controller-copy"><strong>Geräteübergreifende Bedienung</strong>
                <span>${this._controllerStatus?.controller === true
                  ? "Dieses Gerät steuert den Vorgang."
                  : this._controllerStatus?.occupied === true
                    ? "Anderes Gerät steuert · Beobachtung"
                    : "Bedienungsstatus wird ermittelt"}</span></span>
                ${this._controllerStatus?.occupied === true
                  ? `<button type="button" id="dra-take-control"
                       ${this._controllerBusy ? "disabled" : ""}>Übernehmen</button>`
                  : ""}
              </div>` : ""}
              <div class="dra-logs-heading-buttons">
                ${this._deploymentLogCount > 0 ? `<button id="dra-deployment-logs-clear"
                  class="dra-logs-clear-pill" ${this._deploymentLogsBusy ? "disabled" : ""}
                  aria-label="Temporäre Deployment-Protokolle leeren">Leeren</button>` : ""}
                <button id="dra-deployment-logs-toggle" class="dra-logs-pill"
                  aria-controls="dra-deployment-logs-panel"
                  aria-expanded="${this._deploymentLogsOpen}">Logs</button>
                <button type="button" id="dra-audit-toggle" class="dra-logs-pill"
                  aria-controls="dra-audit-panel" aria-expanded="${this._auditOpen}">Audit</button>
              </div>
            </div>
            ${this._auditOpen ? `
              <section class="dra-logs-panel dra-audit-panel" id="dra-audit-panel" aria-label="Audit – detaillierter Prüfverlauf">
                <div class="dra-audit-heading"><strong>Audit · Prüfphasen und Ereignisse</strong>
                  <span class="note">Serverseitig verfügbare Quellprüfungen und ihre Phasen · keine erfundenen Installationsereignisse</span></div>
                <div class="dra-audit-filters">
                  <label>Stufe <select id="dra-audit-level">
                    ${[["all","Alle Stufen"],["INFO","INFO"],["DEBUG","DEBUG"],["ERROR","ERROR"]].map(([value,label]) =>
                      `<option value="${value}" ${this._auditLevel === value ? "selected" : ""}>${label}</option>`).join("")}
                  </select></label>
                  <label>Projekt <select id="dra-audit-project">
                    <option value="all">Alle Projekte</option>
                    ${auditProjects.map(project => `<option value="${this._escapeProject(project)}"
                      ${this._auditProject === project ? "selected" : ""}>${this._escapeProject(project)}</option>`).join("")}
                  </select></label>
                  <label>Vorgang <select id="dra-audit-kind">
                    <option value="all">Alle Vorgänge</option>
                    <option value="source" ${this._auditKind === "source" ? "selected" : ""}>Quellprüfung</option>
                    <option value="installation" ${this._auditKind === "installation" ? "selected" : ""}>Installation</option>
                  </select></label>
                  <label>Phase <select id="dra-audit-phase">
                    <option value="all">Alle Phasen</option>
                    ${auditStages.map(stage => `<option value="${this._escapeProject(stage)}"
                      ${this._auditPhase === stage ? "selected" : ""}>${this._escapeProject(diagnosticStageLabels[stage] || stage)}</option>`).join("")}
                  </select></label>
                  <label class="dra-audit-search">Suche <input id="dra-audit-search" type="search"
                    placeholder="Kennung, Phase, Ursache …" value="${this._escapeProject(this._auditSearch)}"/></label>
                  <button type="button" id="dra-audit-refresh" ${this._deploymentLogsBusy ? "disabled" : ""}>Aktualisieren</button>
                  <button type="button" id="dra-audit-git" ${this._auditExportBusy ||
                    (!this._installAuditRecords.length && !this._centralExport.pending) ||
                    this._centralExport.configured !== true ||
                    this._centralExport.repository !== "TheDaimos/Project-Log-And-Export"
                    ? "disabled" : ""}>Export nach Git</button>
                  <button type="button" id="dra-audit-json" ${!this._installAuditRecords.length ? "disabled" : ""}>Audit als JSON</button>
                </div>
                <div class="dra-audit-scroll">
                  <table class="dra-audit-table">
                    <thead><tr><th>Zeit (MESZ/MEZ)</th><th>Stufe</th><th>Vorgang</th>
                      <th>Phase</th><th>Meldung / Ursache</th><th>Laufzeit</th><th>Details</th></tr></thead>
                    <tbody>${filteredAuditRows.length ? filteredAuditRows.map(row => `
                      <tr class="dra-audit-${auditLevel(row) === "ERROR" ? "failed" : auditLevel(row) === "DEBUG" ? "debug" : "success"}">
                        <td>${this._escapeProject(this._formatHistoryTime(row.record.captured_at))}</td>
                        <td><span class="dra-audit-level">${auditLevel(row)}</span></td>
                        <td>${row.installation ? "Installation" : "Quellprüfung"}</td><td>${this._escapeProject(diagnosticStageLabels[row.stage] || row.stage)}</td>
                        <td>${row.installation ? this._escapeProject(installStageLabels[row.stage] || row.stage) : row.final ? this._escapeProject(diagnosticReasonLabels[row.record.reason] || row.record.reason || "Abgeschlossen") : "Prüfschritt"}</td>
                        <td>${Number.isFinite(row.elapsed) ? row.elapsed + " ms" : "—"}</td>
                        <td><details><summary>Details</summary>
                          <div>Prüfkennung: ${this._escapeProject(row.record.run_id || "—")}</div>
                          <div>Projektkennung: ${this._escapeProject(row.record.project_ref || "—")}</div>
                          <div>Phase: ${this._escapeProject(row.stage)}</div>
                          <div>Status: ${this._escapeProject(row.record.status || "—")}</div>
                          <div>CPU-Zeit des HA-Prozesses: ${Number.isInteger(row.record.process_cpu_ms) ? row.record.process_cpu_ms + " ms" : "—"}</div>
                        </details></td></tr>`).join("") :
                        '<tr><td colspan="7">Keine passenden Ereignisse vorhanden.</td></tr>'}</tbody>
                  </table>
                </div>
                <p class="note">Bei Installationsereignissen zeigt die Laufzeit die seit Auftragsbeginn vergangene Zeit.</p>
                <p class="note" role="status" aria-live="polite">${filteredAuditRows.length} von ${auditRows.length} verfügbaren Prüfeinträgen ·
                  ${this._escapeProject(this._auditStatus)}</p>
              </section>` : ""}
            ${this._deploymentLogsOpen ? `
              <section class="dra-logs-panel" id="dra-deployment-logs-panel"
                aria-label="Bereinigte Deployment-Protokolle">
                ${this._deploymentLogsConfirm ? `
                  <div class="dra-logs-confirm" role="group" aria-label="Loglöschung bestätigen">
                    Nur die letzten temporären V2-Protokolle leeren? Bereits
                    exportierte Dateien im privaten Git-Archiv bleiben unverändert.
                    <div class="dra-logs-confirm-buttons">
                      <button id="dra-logs-clear-confirm" ${this._deploymentLogsBusy ? "disabled" : ""}>Ja, leeren</button>
                      <button id="dra-logs-clear-cancel" ${this._deploymentLogsBusy ? "disabled" : ""}>Abbrechen</button>
                    </div>
                  </div>` : ""}
                <div class="dra-logs-actions">
                  <button id="dra-logs-git" ${(!this._deploymentLogs.length && !this._centralExport.pending) || this._deploymentLogsBusy || !this._centralExport.configured || this._centralExport.repository !== "TheDaimos/Project-Log-And-Export" ? "disabled" : ""}>${this._centralExport.pending ? "Gespeicherten Git-Export erneut senden" : "Export nach Git"}</button>
                  <button id="dra-logs-json" ${!this._deploymentLogs.length || this._deploymentLogsBusy ? "disabled" : ""}>JSON herunterladen</button>
                  <button id="dra-logs-copy" ${!this._deploymentLogs.length || this._deploymentLogsBusy ? "disabled" : ""}>Zwischenablage</button>
                </div>
                <details class="dra-g2-retry-test" id="dra-g2-retry-test"
                  ${this._g2RetryTestOpen ? "open" : ""}>
                  <summary>G2 – Wiederholversand sicher prüfen</summary>
                  <p class="note">Nur im DEV-Testlabor: Ein echter, bereinigter Prüfbericht wird
                    zuerst lokal zurückgestellt, ohne an Git übertragen zu werden.
                    Erst ein späterer ausdrücklicher Klick auf „Gespeicherten Git-Export erneut senden“
                    sendet exakt diesen Bericht an das eingestellte private Archiv.</p>
                  ${this._centralExport.pending ?
                    `<p class="note">Ein Bericht wartet bereits. Keinen weiteren vorbereiten.
                       Für die Übertragung oben „Gespeicherten Git-Export erneut senden“ verwenden.</p>`
                    : this._g2RetryTestConfirm ? `
                      <p class="note">Sicherheitsbestätigung: Nur aktuelle bereinigte Diagnose
                        in der lokalen HA-Warteschlange speichern? Es erfolgt jetzt kein Git-Upload.</p>
                      <button type="button" id="dra-g2-retry-yes"
                        ${this._deploymentLogsBusy ? "disabled" : ""}>Ja, lokal zurückstellen</button>
                      <button type="button" id="dra-g2-retry-no"
                        ${this._deploymentLogsBusy ? "disabled" : ""}>Abbrechen</button>`
                    : `<button type="button" id="dra-g2-retry-prepare"
                       ${this._deploymentLogsBusy || !this._deploymentLogs.length ||
                         this._centralExport.configured !== true ||
                         this._centralExport.repository !== "TheDaimos/Project-Log-And-Export"
                         ? "disabled" : ""}>G2-Test vorbereiten</button>`}
                </details>
                <p class="note" role="status" aria-live="polite">${this._escapeProject(this._deploymentLogsStatus)}</p>
                <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:12px">
                  <label>Ergebnis <select id="dra-log-filter">
                    <option value="all" ${this._logFilter === "all" ? "selected" : ""}>Alle Ergebnisse</option>
                    <option value="success" ${this._logFilter === "success" ? "selected" : ""}>Erfolgreich</option>
                    <option value="failed" ${this._logFilter === "failed" ? "selected" : ""}>Fehlgeschlagen</option>
                  </select></label>
                  <label>Protokolle durchsuchen <input id="dra-log-search" type="search"
                    placeholder="Zeit, Phase, Ursache oder Kennung" value="${this._escapeProject(this._logSearch)}"/></label>
                </div>
                <div class="dra-logs-events" style="overflow:auto;max-height:340px">
                  <table style="width:100%;min-width:650px;border-collapse:collapse;text-align:left">
                    <thead><tr><th>Zeit (Deutschland)</th><th>Ergebnis</th><th>Phase</th><th>Ursache</th><th>Dauer</th><th>Details</th></tr></thead>
                    <tbody>${visibleLogs.length ? visibleLogs.map(record => `
                      <tr><td>${this._escapeProject(this._formatHistoryTime(record.captured_at))}</td>
                        <td>${record.status === "success" ? "Erfolgreich" : "Fehlgeschlagen"}</td>
                        <td>${this._escapeProject(diagnosticStageLabels[record.stage] || record.stage || "—")}</td>
                        <td>${this._escapeProject(diagnosticReasonLabels[record.reason] || record.reason || "—")}</td>
                        <td>${Number.isInteger(record.duration_ms) ? record.duration_ms + " ms" : "—"}</td>
                        <td><details><summary>Details</summary>
                          <div>Projektkennung: ${this._escapeProject(record.project_ref || "—")}</div>
                          <div>Prüfkennung: ${this._escapeProject(record.run_id || "—")}</div>
                          <div>HA-Prozess-CPU: ${Number.isInteger(record.process_cpu_ms) ? record.process_cpu_ms + " ms" : "—"}</div>
                          <div>CPU-Kerne: ${this._escapeProject(record.resources?.available_cores ?? "—")}</div>
                          <div>Arbeitsprozesse eingestellt: ${this._escapeProject(record.resources?.configured_worker_processes ?? "—")}</div>
                        </details></td></tr>`).join("") : '<tr><td colspan="6">Keine passenden Protokolle.</td></tr>'}</tbody>
                  </table>
                </div>
                <p class="note">${visibleLogs.length} von ${this._deploymentLogs.length} Protokollen angezeigt.</p>
                <div class="dra-history-section" aria-label="Serverseitige Auftragshistorie">
                  <div class="dra-history-heading">
                    <div class="dra-history-heading-title">
                      <strong>Serverseitige Auftragshistorie</strong>
                      <span class="dra-history-refresh-status ${this._historyRefreshTone}"
                        role="status" aria-live="polite" aria-atomic="true"
                        title="${this._escapeProject(this._historyRefreshDetail)}"
                        aria-label="${this._escapeProject(this._historyRefreshDetail)}"
                      >${this._escapeProject(this._historyRefreshStatus)}</span>
                    </div>
                    <button type="button" id="dra-history-refresh"
                      class="dra-history-refresh ${this._historyRefreshBusy ? "is-loading" : ""}"
                      aria-label="Quellprotokolle und Auftragshistorie aktualisieren"
                      aria-busy="${this._historyRefreshBusy}"
                      ${this._historyRefreshBusy || this._deploymentLogsBusy ? "disabled" : ""}>
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M20 7v5h-5M4 17v-5h5"></path>
                        <path d="M5.6 9.3A7.6 7.6 0 0 1 19.1 7L20 12M4 12l.9 5a7.6 7.6 0 0 0 13.5-2.3"></path>
                      </svg>
                      <span>${this._historyRefreshBusy ? "Wird aktualisiert …" : "Aktualisieren"}</span>
                    </button>
                  </div>
                  <div class="dra-history-list" role="list" aria-label="Gespeicherte Aufträge; innerhalb der Liste scrollen">
                    ${this._sourceJobHistory.length === 0
                      ? `<p class="note">${this._escapeProject(this._sourceJobHistoryStatus || "Noch keine gespeicherten Aufträge.")}</p>`
                      : ""}
                    ${this._sourceJobHistory.map(item => `
                      <div class="dra-history-item ${item.status}" role="listitem">
                        <div class="dra-history-item-head">
                          <strong>Auftrag ${this._escapeProject(item.operation_id.slice(0,12))}</strong>
                          <span class="dra-history-state">${item.status === "success" ? "Damals erfolgreich" :
                            item.status === "failed" ? "Prüfung gescheitert" :
                            item.status === "interrupted" ? "Unterbrochen" : "Begonnen"}</span>
                        </div>
                        <span class="dra-history-item-time">${this._escapeProject(this._formatHistoryTime(item.finished_at || item.created_at))}</span>
                      </div>`).join("")}
                  </div>
                  ${this._sourceJobHistory.length > 3
                    ? `<p class="dra-history-scroll-hint">Weitere Aufträge durch Wischen innerhalb der Liste anzeigen · ${this._sourceJobHistory.length} gespeichert.</p>`
                    : ""}
                </div>
                <details class="dra-logs-notes" id="dra-logs-notes" ${this._logsNotesOpen ? "open" : ""}>
                  <summary>Hinweise zu Protokollen und Datenschutz</summary>
                  <div class="dra-logs-notes-content">
                    <p class="note">Gespeicherte Auftragszustände: Alte Prüfergebnisse werden niemals erneut freigegeben.</p>
                    <p class="note">Die Historie enthält weder Projektdateien noch Repositorynamen.
                      Nach HA-Neustart ist immer eine neue Quellprüfung erforderlich.</p>
                    <p class="note">Repositorynamen werden nur dem ausdrücklich freigegebenen privaten Git-Export beigefügt.
                      Projektkennungen gelten für die aktuelle HA-Laufzeit; Prüfkennungen werden auch im Export gespeichert.
                      CPU-Zeit gilt für den gesamten Home-Assistant-Prozess, nicht isoliert für DRA V2.
                      Eingestellte Arbeitsprozesse sind keine tatsächlich gestarteten Prozesse.
                      Nur bereinigte Quellprüfungen; kein Schreibzugriff. Git-Export ausschließlich zum eingestellten privaten Archiv.</p>
                  </div>
                </details>
              </section>` : ""}
            <button id="dra-preview" class="dra-deploy-action stage-${deploymentStage}
              ${!this._mainBatchMode && upToDate ? "up-to-date" : ""}
              ${deploymentBusy ? "is-busy" : ""} ${this._mainBatchMode ? batchFailed ? "has-error" : "" : installFailed ? "has-error" : ""}"
              data-stage="${deploymentStage}"
              ${this._mainBatchMode
                ? deploymentBusy || !deploymentCanPreview ||
                  this._serverVersion !== DRA_V2_UI_VERSION ||
                  deploymentStage >= 3 || batchState === "up_to_date" ||
                  (deploymentStage === 2 && this._batchStartUncertain)
                : upToDate || deploymentBusy || !deploymentCanPreview || deploymentStage >= 3 ||
                  (deploymentStage === 2 && (!mainProject || mainProject.active === false ||
                  this._serverVersion !== DRA_V2_UI_VERSION || !!preparedInstall)) ? "disabled" : ""}
              aria-label="${deploymentButtonText}">
              ${deploymentBusy
                ? iconSvg('<path d="M12 3a9 9 0 1 0 9 9"/>',25)
                : (!this._mainBatchMode && upToDate) ? deploymentIcons[3] : deploymentIcons[deploymentStage-1]}
              <span>${deploymentButtonText}</span>
            </button>
            ${upToDate ? `<div class="dra-up-to-date-note" role="status">
              <strong>Bereits auf dem aktuellen Stand.</strong>
              <div>Der Dateivergleich hat keine Änderungen festgestellt.
                ${this._escapeProject(this._sourcePreview.unchanged_count)} Dateien unverändert.
                Es ist keine Installation erforderlich.</div>
              <button type="button" class="dra-up-to-date-repeat" id="dra-up-to-date-recheck"
                ${deploymentBusy ? "disabled" : ""}>Vorschau erneut berechnen</button>
            </div>` : ""}
            ${preparedInstall ? `
              <div class="dra-deployment-result" role="group" aria-label="Installation bestätigen">
                <strong>V1-Engine · Installation ausdrücklich bestätigen</strong>
                <span>Commit: ${this._escapeProject(preparedInstall.source_commit)}</span>
                <span>Dateien: ${preparedInstall.add} hinzugefügt · ${preparedInstall.change} geändert · ${preparedInstall.remove} entfernt</span>
                <span class="note">Sicherung, Installation, Prüfung und Rückfall erfolgen nach dem bewährten V1-Verfahren.</span>
                ${this._installStartUncertain ? `<span class="note" role="alert">Auftragsstatus nicht bestätigt. Bitte Audit und Serverstatus prüfen; kein zweiter Installationsversuch.</span>` : ""}
                <button type="button" id="dra-install-confirm" ${deploymentBusy || this._installStartUncertain || this._controllerStatus?.controller !== true ? "disabled" : ""}>Ja, Update installieren</button>
                <button type="button" id="dra-install-cancel" ${deploymentBusy ? "disabled" : ""}>Abbrechen</button>
              </div>` : ""}
            ${runningJobs.length ? `<div class="dra-deployment-result" role="status">
              <strong>Parallele serverseitige Updates: ${runningJobs.length} von maximal 4</strong>
              ${runningJobs.map(j=>`<span>Projekt ${this._escapeProject(j.project_key)}
                · ${this._escapeProject(j.phase)} · ${this._escapeProject(j.status)}</span>`).join("")}
              <span class="note">Anderes Projekt auswählen, um dort unabhängig weiterzuarbeiten.</span>
            </div>` : ""}
            ${archivedFinish ? `<div class="dra-deployment-result" role="status">
              <strong>Letzte Installation erfolgreich abgeschlossen (gespeicherte Audit-Historie)</strong>
              <span>Auftragskennung: ${this._escapeProject(lastStoredSuccess.operation_id)}</span>
              <span>Zeit: ${this._escapeProject(this._formatHistoryTime(lastStoredSuccess.captured_at))}</span>
              <span class="note">Historischer Abschluss – keine aktuelle Quellprüfung, keine neue Freigabe.
                Für weitere Aktualisierungen stets eine neue Vorschau starten.</span>
              <span class="note">Eine neue Quellprüfung startet keine Installation.</span>
            </div>` : ""}
            ${(installFinished || archivedFinish) && mainProject ? `
              <button type="button" id="dra-next-deployment-preview"
                ${deploymentBusy ? "disabled" : ""}>Neue Vorschau für dieses Projekt berechnen</button>` : ""}
            ${upToDate && jobBelongsToProject && this._installJob?.status === "success"
              ? `<details class="dra-history-only"><summary>Vorherige Installation · Historie</summary>
                  <p>Auftrag: ${this._escapeProject(this._installJob.operation_id)}</p>
                  <p>Erfolgreich abgeschlossen; kein Bestandteil der aktuellen, unveränderten Vorschau.</p>
                </details>` : ""}
            ${this._installJob && !upToDate ? `<div class="dra-deployment-result" role="status">
              <strong>Serverseitiger Auftrag: ${this._escapeProject(this._installJob.status)}</strong>
              <span>Schritt: ${this._escapeProject(this._installJob.phase)}</span>
              <span>Auftragskennung: ${this._escapeProject(this._installJob.operation_id)}</span>
              <span>${this._escapeProject(this._installMessage)}</span>
            </div>` : ""}
            ${postInstallJob ? `<section class="dra-post-install" aria-label="Aktion nach erfolgreichem Update">
              <strong>Update erfolgreich installiert und geprüft</strong>
              ${postInstallJob.restart_required === true ? `
                <span class="note">Python- oder andere Backenddateien wurden aktualisiert.
                  Die Änderungen werden erst nach einem Home-Assistant-Neustart wirksam.</span>
                <button type="button" id="dra-ha-restart-open" class="dra-ha-restart"
                  ${this._restartBusy || runningJobs.length ? "disabled" : ""}>
                  Home Assistant neu starten</button>
                ${this._restartDialogOpen ? `<div class="dra-restart-confirm" role="group"
                  aria-label="Sicherheitsabfrage für Home-Assistant-Neustart">
                  <strong>Home Assistant wirklich neu starten?</strong>
                  <p>Home Assistant ist während des Neustarts vorübergehend nicht erreichbar.
                    Noch laufende Installationsaufträge verhindern den Neustart.</p>
                  <div class="dra-restart-buttons">
                    <button type="button" id="dra-ha-restart-cancel" class="dra-restart-cancel"
                      ${this._restartBusy ? "disabled" : ""}>Abbrechen</button>
                    <button type="button" id="dra-ha-restart-confirm" class="dra-ha-restart"
                      ${this._restartBusy ? "disabled" : ""}>Ja, Home Assistant neu starten</button>
                  </div>
                </div>` : ""}`
                : postInstallJob.frontend_reload_possible === true ? `
                <span class="note">Nur Frontenddateien wurden aktualisiert.
                  Home Assistant muss nicht neu gestartet werden.</span>
                <button type="button" id="dra-frontend-refresh" class="dra-frontend-refresh">
                  Oberfläche aktualisieren</button>`
                : `<span class="note">Keine weitere Aktion erforderlich.</span>`}
              ${this._restartMessage ? `<p class="dra-restart-message" role="status">
                ${this._escapeProject(this._restartMessage)}</p>` : ""}
            </section>` : ""}
            <div class="dra-deploy-progress ${this._mainBatchMode
              ? batchFinished ? "completed" : batchFailed ? "failed"
                : batchRunning || deploymentBusy ? "running" : batchPrepared ? "verified" : "idle"
              : upToDate ? "up-to-date" : displayFinished ? "completed" : installFailed ? "failed" : deploymentBusy || installActive ? "running" : mainPreviewVerified ? "verified" : "idle"}"
              role="progressbar" aria-label="Deployment-Fortschritt"
              aria-valuemin="0" aria-valuemax="4"
              aria-valuenow="${this._mainBatchMode
                ? batchFinished ? 4 : batchRunning ? 3 : batchPrepared ? 2 : 1
                : upToDate ? 1 : displayFinished ? 4 : this._installSubmissionActive || installActive || installFailed ? 3 : mainPreviewVerified ? 1 : 0}">
              <div class="dra-deploy-progress-fill"></div>
            </div>
            <div class="dra-deploy-steps" role="list" aria-label="Vier Schritte des Deployments">
              ${[
                ["Vorschau","Vorschau",deploymentIcons[0],"blue"],
                ["Freigabe","Freigabe",deploymentIcons[1],"orange"],
                ["Update","Update",deploymentIcons[2],"red"],
                ["Abschluss","Abschluss",deploymentIcons[3],"green"],
              ].map((item,i) => `<div class="dra-deploy-step ${item[3]} ${upToDate ?
                (i === 0 ? "current-review" : "not-required") :
                i+1 === deploymentStage ? installFailed ? "failed" : "current" : i+1 < deploymentStage ? "done" : "pending"}"
                role="listitem" aria-label="Schritt ${i+1}: ${item[1]}, ${upToDate ?
                  (i === 0 ? "geprüft, keine Änderungen" : "nicht erforderlich") :
                  i+1 === deploymentStage ? deploymentStage===2 ? "noch gesperrt" : "aktuell" : i+1 < deploymentStage ? "abgeschlossen" : "ausstehend"}">
                ${item[2]}<span>${i+1}. ${item[0]}</span></div>`).join("")}
            </div>
            <p class="dra-deployment-runtime note" aria-label="Laufzeitstatus">
              <span>Python-Laufzeit: ${this._escapeProject(this._serverVersion || "nicht ermittelt")}</span>
              <span class="${this._serverVersion === DRA_V2_UI_VERSION ? "runtime-ok" : "runtime-warning"}">
                ${this._serverVersion === DRA_V2_UI_VERSION
                  ? "· Oberfläche und Laufzeit stimmen überein"
                  : "· Versionsabgleich erforderlich"}
              </span>
            </p>
            <p class="dra-deployment-status note" role="status" aria-live="polite">
              ${this._escapeProject(this._mainBatchMode
                ? deploymentStatus : upToDate ? deploymentStatus : this._installMessage || deploymentStatus)}
            </p>
            ${mainPreviewVerified ? `<div class="dra-deployment-result">
              <strong>Schreibgeschützte Vorschau</strong>
              <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,270px),1fr));gap:12px;margin:10px 0">
                <div style="border:1px solid var(--divider-color,#52636b);border-radius:9px;padding:12px">
                  <strong>Dateivergleich</strong>
                  <div>Hinzugefügt: ${this._sourcePreview.add?.length ?? 0} · Geändert: ${this._sourcePreview.change?.length ?? 0} ·
                    Entfernt: ${this._sourcePreview.remove?.length ?? 0} · Unverändert: ${this._sourcePreview.unchanged_count ?? 0}</div>
                </div>
                <div style="border:1px solid ${this._sourcePreview.version_guard?.warning ? "#ae792b" : "var(--divider-color,#52636b)"};border-radius:9px;padding:12px">
                  <strong>Versions- und Regressionsprüfung</strong>
                  <div>Git-Quelle: <b>${this._escapeProject(this._sourcePreview.version_guard?.source_version || "Nicht ermittelt")}</b></div>
                  <div>Lokal installiert: <b>${this._escapeProject(this._sourcePreview.version_guard?.local_version || "Nicht ermittelt")}</b></div>
                  <div class="note">Erkannt über: ${this._escapeProject(this._sourcePreview.version_guard?.marker || "Kein gemeinsamer Versionsmarker")}</div>
                  <div role="status">${this._sourcePreview.version_guard?.regression ? "⚠ Rückschritt erkannt – ältere Git-Version" :
                    this._sourcePreview.version_guard?.reason === "same_version_with_file_changes" ? "⚠ Gleiche Version, aber geänderte Dateien" :
                    this._sourcePreview.version_guard?.reason === "no_common_version_marker_with_removals" ? "⚠ Versionsvergleich nicht möglich; Löschungen vorhanden" :
                    this._sourcePreview.version_guard?.status === "upgrade" ? "Aktualisierung erkannt" :
                    this._sourcePreview.version_guard?.status === "same" ? "Versionsstand identisch" :
                    "Versionsreihenfolge nicht ermittelbar"}</div>
                </div>
              </div>
              <span class="note">Keine Schreib- oder Installationsfreigabe.</span>
              <details id="dra-preview-details" ${this._previewDetailsOpen ? "open" : ""}>
                <summary>Details der Vorschau · Dateiliste, Filter und Suche</summary>
                <div class="dra-preview-controls" style="display:flex;gap:10px;flex-wrap:wrap;margin:12px 0">
                  <label for="dra-preview-status">Dateistatus
                    <select id="dra-preview-status">
                      ${[["all","Alle Veränderungen"],["add","Hinzugefügt"],["change","Geändert"],["remove","Entfernt"]].map(([value,label])=>
                        `<option value="${value}" ${this._previewFileFilter === value ? "selected" : ""}>${label}</option>`).join("")}
                    </select>
                  </label>
                  <label for="dra-preview-search">Dateien suchen
                    <input id="dra-preview-search" type="search" placeholder="Dateiname oder Pfad" value="${this._escapeProject(this._previewFileSearch)}" />
                  </label>
                </div>
                <div style="overflow-x:auto;max-height:320px;overflow-y:auto">
                  <table style="width:100%;border-collapse:collapse">
                    <thead><tr><th scope="col">Status</th><th scope="col">Dateipfad relativ zu /config</th></tr></thead>
                    <tbody>${visiblePreviewFiles.length ? visiblePreviewFiles.map(entry =>
                      `<tr><td>${this._escapeProject(entry.label)}</td><td style="overflow-wrap:anywhere">${this._escapeProject(entry.path)}</td></tr>`).join("") :
                      `<tr><td colspan="2">Keine passenden Dateiveränderungen.</td></tr>`}</tbody>
                  </table>
                </div>
                <p class="note">${visiblePreviewFiles.length} von ${previewFiles.length} veränderten Dateien angezeigt · ${this._sourcePreview.unchanged_count ?? 0} unverändert (nur Anzahl verfügbar).</p>
              </details>
            </div>` : this._mainBatchPreview && (!this._batchStatus || ["idle","failed"].includes(this._batchStatus.status)) ? `<div class="dra-deployment-result">
              <strong>Gruppenauswahl bestätigt: ${this._mainBatchPreview.count} Projekte</strong>
              <span class="note">Die Quellstände sind noch nicht geprüft. Installation gesperrt.</span>
            </div>` : ""}
            ${this._mainBatchMode ? `<section class="dra-deployment-result" role="group"
              aria-label="Serverseitiges Sammelupdate">
              <strong>Sammelupdate · serverseitige Installation</strong>
              ${["inspecting_sources","preparing"].includes(this._batchStatus?.status) ? `<p role="status">Home Assistant prüft
                ${this._batchStatus.current || 0} von ${this._batchStatus.total || 0}
                Projekten. Aktuell: ${this._escapeProject(this._batchStatus.project_key || "wird ermittelt")}.
                Der Auftrag läuft auf dem Server weiter.</p>` : ""}
              ${this._batchStatus?.status === "failed" ? `<div class="dra-deployment-result" role="alert"
                style="border-color:#b36a39;background:rgba(135,70,32,.16);padding:14px;">
                <strong>Quellenprüfung angehalten – keine Installation gestartet</strong>
                <p><strong>Projekt:</strong> ${this._escapeProject(
                  this._projects.find(p=>p.project_id===this._batchStatus.project_key)?.name ||
                  this._batchStatus.project_key || "Nicht ermittelt")}</p>
                <p><strong>Prüfschritt:</strong> ${this._escapeProject(({
                  source_reference:"GitHub-Referenz / Lesezugriff / Kanalempfehlung",
                  manifest:"Installationsmanifest",
                  inventory:"Quell-Dateibestand",
                  local_comparison:"Lokaler Dateivergleich",
                  version_detection:"Installierte / neue Version",
                  batch_planning:"Installationsplanung",
                })[this._batchStatus.check_stage] || "Nicht ermittelt")}</p>
                <p><strong>Fehlerkategorie:</strong> ${this._escapeProject(
                  this._batchStatus.error_code || "preflight_failed")}</p>
                ${this._batchStatus.error_detail ? `<p><strong>Weitere Eingrenzung:</strong>
                  ${this._escapeProject(({
                    github_http_authentication:"GitHub meldet 401 – Token ungültig oder abgelaufen",
                    github_http_forbidden:"GitHub meldet 403 – Zugriff verweigert oder Rate begrenzt",
                    github_http_not_found:"GitHub meldet 404 – Quelle nicht gefunden oder privater Zugriff fehlt",
                    github_http_rate_limited:"GitHub meldet 429 – Abfragegrenze erreicht",
                    "invalid deployment recommendation":"Projekt-Empfehlungsdatei fachlich ungültig",
                    "invalid recommendation blob":"Integritätsprüfung der Empfehlung fehlgeschlagen",
                    "invalid recommendation format":"Format der Empfehlung nicht gültig",
                    "invalid recommended reference":"Empfohlener Git-Zweig oder Tag ungültig",
                    "missing default branch":"GitHub liefert keinen Standardzweig",
                    "repository mismatch":"Repository-Identität stimmt nicht überein",
                    "invalid source entry":"GitHub liefert einen ungültigen Zweig-/Tag-Eintrag",
                    "GitHub response could not be verified":"GitHub-Antwort nicht verifizierbar",
                    "invalid GitHub JSON":"GitHub-Antwort nicht als gültige JSON-Daten lesbar",
                    inventory_file_limit:"Die Quelle enthält mehr Dateien als das Manifest erlaubt",
                    inventory_byte_limit:"Die Quelle überschreitet das festgelegte Größenlimit",
                    inventory_duplicate_paths:"Doppelte Dateipfade in der Quelle",
                    inventory_directory_cycle:"Unzulässiger oder doppelter Quellordner",
                    inventory_unsafe_path:"Unsicherer Quellpfad",
                    inventory_read_unavailable:"GitHub-Dateibestand konnte nicht vollständig verifiziert werden",
                  })[this._batchStatus.error_detail] || "Quellprüfung konnte nicht verifiziert werden")}</p>` : ""}
                <p class="note">Diese Angaben stammen aus dem lesbaren Home-Assistant-Auftragsstatus.
                  Ein zusätzlicher Protokollexport ist dafür nicht notwendig. Andere ausgewählte
                  Projekte wurden ebenfalls nicht installiert.</p>
              </div>` : ""}
              ${this._batchStatus?.status === "prepared" ? `<p>Feste Commits und Dateiänderungen sind vorbereitet.
                Nur eine ausdrückliche Freigabe kann den Auftrag starten.</p>` : ""}
              ${this._batchStatus?.items?.length ? this._batchStatus.items.map(item => `
                <span>${this._escapeProject(this._projects.find(p=>p.project_id===item.project_key)?.name || item.project_key)}
                  · ${this._escapeProject(item.source_ref)} · ${this._escapeProject(item.source_commit.slice(0,12))}
                  · +${item.add} ~${item.change} −${item.remove}
                  · ${this._escapeProject(item.status)}
                </span>`).join("") : ""}
              <p class="note">Die große Schaltfläche oberhalb steuert alle Schritte:
                Quellprüfung und Vorbereitung → ausdrückliche Bestätigung → serverseitige Installation.
                Es gibt keinen zweiten, versteckten Vorbereitungsweg.</p>
              ${this._batchStatus?.status==="prepared" && !this._batchChallenge ?
                `<button type="button" id="dra-batch-install-takeover"
                  ${this._mainBatchBusy?"disabled":""}>Vorbereitung auf diesem Gerät übernehmen</button>` : ""}
              ${this._batchChallenge && this._batchStatus?.status==="prepared" ?
                `<p class="note"><strong>Verbindliche Prüfübersicht erforderlich:</strong>
                  Installierte Version, neue Version, Git-Zweig und vollständige Commit-Kennung
                  müssen vor der Installation im Zwischenfenster bestätigt werden.</p>` : ""}
              ${this._batchStartUncertain ? `<p role="alert">Auftragsannahme unklar.
                Keine zweite Installationsanforderung senden; HA-Status/Audit prüfen.</p>` : ""}
              <p class="note">Teilinstallationen erfolgen nacheinander durch Home Assistant.
                Bei Fehlern stoppt die Reihenfolge. Bereits erfolgreiche Teilupdates
                werden nicht automatisch zurückgesetzt. Bekannte Abhängigkeiten
                müssen bei der Reihenfolge berücksichtigt werden.</p>
            </section>` : ""}
            <p class="dra-deployment-hint note">
              Einzelupdates nutzen die V1-Installationsengine. Schreiben erfordert einen freigegebenen Projektzugang
              und eine separate Bestätigung. Sammelinstallationen nutzen ebenfalls die V1-Engine; DRA-Selbstupdates erfolgen zuletzt.
            </p>
          </article>
          <article class="dra-tests-panel">
            <details class="dra-tests-expander" id="dra-tests-expander" ${this._testsOpen ? "open" : ""}>
              <summary><span>Tests · Entwicklungsdiagnose</span><span class="note">Technische Prüfungen ohne Installation</span></summary>
              <div class="dra-tests-content">
                <div class="dra-test-item">
                  <div class="dra-test-item-heading"><strong>G2 · Sichere Wiederverbindung (60 s)</strong>
                    <span class="note">Serverseitiger, rein lesender Prüfauftrag</span></div>
                  <p class="note">Prüft, ob ein Auftrag auch bei geschlossenem oder getrenntem Browser auf
                    Home Assistant weiterläuft und nach der Wiederverbindung wiedergefunden wird.
                    Kein Schreibzugriff, keine Installation und kein Neustart.</p>
                  <div class="dra-test-actions">
                    <button type="button" id="dra-g2-connection-test"
                      ${this._mainBatchMode || deploymentBusy || !mainProject || !this._hass ||
                        this._serverVersion !== G2_TEST_PYTHON_VERSION ? "disabled" : ""}>
                      G2-Verbindungstest starten (60 s)</button>
                    <span class="note">Projekt: ${mainProject ? this._escapeProject(mainProject.name) : "Kein Projekt ausgewählt"}</span>
                  </div>
                  ${this._sourceConnectionTest ? `<p class="dra-test-result" role="status">
                    <strong>G2:</strong> ${this._escapeProject(this._sourceMessage || "Prüfung läuft …")}
                  </p>` : ""}
                </div>
                <div class="dra-test-item" style="margin-top:12px">
                  <div class="dra-test-item-heading"><strong>Test 2 · Testdateien vorbereiten</strong>
                    <span class="note">Nur isoliertes Test-Repository</span></div>
                  <p class="note">Erzeugt einen gemeinsamen Git-Commit mit der gewählten Anzahl synthetischer Dateien. Ändert <code>teststand</code> in
                    <code>TheDaimos/Test-Repo-DRA-V2 · main · payload/teststatus.json</code>.
                    Kein automatisches Deployment, kein HA-Neustart. Der GitHub-Token dieses Testprojekts
                    benötigt tatsächliche Schreibberechtigung; die hinterlegte Zugriffsart ist keine Freigabe.</p>
                  <div class="dra-test-actions"><label>Testdateien <button type="button" id="dra-test-file-minus" ${this._testFileCount<=1 || this._testVersionBusy?"disabled":""}>−</button> <strong>${this._testFileCount}</strong> <button type="button" id="dra-test-file-plus" ${this._testFileCount>=7 || this._testVersionBusy?"disabled":""}>+</button></label>
                    <label>Sekunden je Datei <select id="dra-test-delay" ${this._testVersionBusy?"disabled":""}>${[10,20,30,60].map(s=>`<option value="${s}" ${this._testDelaySeconds===s?"selected":""}>${s} Sekunden</option>`).join("")}</select></label></div>
                  <p class="note">Geplante Testdauer: ${this._testFileCount * this._testDelaySeconds} Sekunden. Die künstliche Wartezeit läuft ausschließlich auf Home Assistant und ausschließlich bei diesem Testprojekt.</p>
                  <label class="dra-test-confirm"><input type="checkbox" id="dra-test-version-confirm"
                    ${this._testVersionConfirm ? "checked" : ""} ${this._testVersionBusy ? "disabled" : ""}/>
                    Ich bestätige die Änderung ausschließlich im isolierten Git-Testprojekt.</label>
                  <div class="dra-test-actions">
                    <button type="button" id="dra-test-version-increment"
                      ${!this._testVersionConfirm || this._testVersionBusy ||
                        this._serverVersion !== DRA_V2_UI_VERSION ? "disabled" : ""}>
                      ${this._testVersionBusy ? "Testdateien werden vorbereitet …" : "Testdateien vorbereiten"}</button>
                  </div>
                  <p class="dra-test-result note" role="status" aria-live="polite">
                    ${this._escapeProject(this._testVersionResult || "Bereit zur ausdrücklich bestätigten Git-Teständerung.")}</p>
                </div>
              </div>
            </details>
          </article>
        </section>
        <section id="dra-settings-view" ${this._view==="settings"?"":"hidden"}>
        <h1>DRA V2 DEV · Diagnose & Einstellungen</h1>
        <p class="safe">Eigenständiger DRA-V2-Testbereich · Installationen nur nach ausdrücklicher Freigabe</p>
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

        </div>
        <p class="note">Während eines laufenden Tests wird der Status etwa alle 1,5 Sekunden aktualisiert. Im Leerlauf erfolgt keine regelmäßige Abfrage. Nach einem Home-Assistant-Neustart bleiben abgeschlossene Aufträge im begrenzten Verlauf abrufbar. Vorher laufende Testaufträge erscheinen als unterbrochen und werden nicht neu gestartet.</p>
        </section>
        ${this._batchReviewOpen && this._mainBatchMode && this._batchPreparation?.status==="prepared" ?
          `<div class="git-dialog-backdrop" id="dra-batch-review-backdrop">
            <section class="git-dialog dra-batch-review-dialog" role="dialog" aria-modal="true"
              aria-labelledby="dra-batch-review-title" tabindex="-1" id="dra-batch-review-dialog">
              <header class="dra-picker-header">
                <div>
                  <h2 id="dra-batch-review-title">Sammelupdate · verbindliche Prüfübersicht</h2>
                  <p class="note">Home Assistant hat alle Quellstände auf feste Commits geprüft.
                    Diese Zeilen gelten ausschließlich für diesen vorbereiteten Durchlauf.</p>
                </div>
                <button type="button" id="dra-batch-review-close" title="Übersicht schließen"
                  aria-label="Prüfübersicht schließen">${closeIcon}</button>
              </header>
              <div class="dra-batch-review-mobile-list" aria-label="Kompakte Projektübersicht">${mobileReviewCards}</div>
              <div class="dra-batch-review-table-wrap">
                <table class="dra-batch-review-table">
                  <thead><tr>
                    <th scope="col">Projekt</th>
                    <th scope="col">Installierte Version</th>
                    <th scope="col" aria-label="Versionsvergleich">→</th>
                    <th scope="col">Neue Version</th>
                    <th scope="col">Commit (40 Zeichen)</th>
                    <th scope="col">Ausgewählt · Ref</th>
                    <th scope="col">Änderungen</th>
                  </tr></thead>
                  <tbody>${this._batchPreparation.items.map(item=>{
                    const name=this._projects.find(p=>p.project_id===item.project_key)?.name ||
                      item.project_key;
                    const oldVersion=item.installed_version || "Nicht ermittelbar";
                    const newVersion=item.new_version || "Nicht ermittelbar";
                    const missing=item.version_status!=="verified_pair";
                    const label=item.status==="up_to_date"?"Aktuell · keine Installation":
                      "Zur Installation vorbereitet";
                    return `<tr class="${missing?"dra-review-unknown":""}">
                      <th scope="row">${this._escapeProject(name)}
                        <div class="note">${this._escapeProject(item.repository)}</div></th>
                      <td>${this._escapeProject(oldVersion)}</td><td class="dra-review-arrow">→</td>
                      <td><strong>${this._escapeProject(newVersion)}</strong></td>
                      <td><code>${this._escapeProject(item.source_commit)}</code></td>
                      <td><code>${this._escapeProject(item.source_ref)}</code></td>
                      <td>${this._escapeProject(label)}
                        <div class="dra-review-counts"><span class="${item.add ? "dra-review-add" : ""}">+${item.add}</span> · <span class="${item.change ? "dra-review-edit" : ""}">~${item.change}</span> · <span class="${item.remove ? "dra-review-remove" : ""}">−${item.remove}</span></div></td>
                    </tr>`;
                  }).join("")}</tbody>
                </table>
              </div>
              ${this._batchPreparation.items.some(item=>item.version_status!=="verified_pair")
                ? `<p class="dra-batch-review-warning" role="status">
                  Mindestens eine Versionsangabe konnte nicht vollständig aus geprüften
                  lokalen und Git-Dateien ermittelt werden. Es werden keine Versionsnummern
                  geschätzt. Prüfe die Quelle und den Commit besonders sorgfältig.</p>` : ""}
              <p class="note">Prüfkennung: <code>${this._escapeProject(this._batchPreparation.review_digest)}</code></p>
              <label class="dra-batch-review-ack">
                <input type="checkbox" id="dra-batch-review-checked"
                  ${this._batchReviewChecked?"checked":""}>
                Ich habe alle Projekte, installierten und neuen Versionen,
                Git-Referenzen und vollständigen Commits geprüft. Die angegebenen
                Quellstände dürfen installiert werden.
              </label>
              <div class="dra-batch-review-actions">
                <button type="button" id="dra-batch-review-cancel">Schließen · nichts installieren</button>
                <button type="button" id="dra-batch-review-discard"
                  ${this._mainBatchBusy?"disabled":""}>Vorbereitung verwerfen · Auswahl ändern</button>
                <button type="button" id="dra-batch-review-approve"
                  ${!this._batchReviewChecked || this._batchStartUncertain ||
                     this._mainBatchBusy || this._batchStatusError ||
                     this._batchStatus?.review_digest!==this._batchReviewDigest
                     ? "disabled" : ""}>
                  Geprüfte Sammelinstallation bestätigen</button>
              </div>
            </section>
          </div>` : ""}
        ${this._projectPickerOpen ? `
          <div class="git-dialog-backdrop" id="dra-picker-backdrop">
            <section class="git-dialog dra-picker-dialog" id="dra-picker-dialog"
              role="dialog" aria-modal="true" aria-labelledby="dra-picker-title" tabindex="-1">
              <header class="dra-picker-header">
                <div>
                  <h2 id="dra-picker-title">Projekt auswählen</h2>
                  <p class="note">Gewünschtes Projekt für die Hauptansicht auswählen.</p>
                </div>
                <button id="dra-picker-close" aria-label="Projektauswahl schließen" title="Schließen">
                  ${closeIcon}
                </button>
              </header>
              <div class="dra-picker-list" role="list" aria-label="Registrierte Projekte">
                ${this._pickerEntries().map((entry,i) => {
                  if (entry.kind === "batch") {
                    const selected = this._mainBatchMode;
                    return `<button type="button" id="dra-picker-batch"
                      class="dra-picker-entry dra-picker-batch-entry ${selected ? "selected" : ""}"
                      aria-current="${selected}" aria-label="Sammelupdate als Projektauswahl">
                      <span class="dra-picker-entry-number">${i+1}</span>
                      <span class="dra-picker-entry-content">
                        <strong>Sammelupdate</strong>
                        <span class="dra-picker-entry-repository">${this._mainBatchProjects().length} aktivierte Projekte gemeinsam auswählen · Installation gesperrt</span>
                      </span>
                      <span class="dra-picker-check" aria-hidden="true">
                        ${selected ? iconSvg('<circle cx="12" cy="12" r="9"/><path d="m8 12 2.5 2.5L16 9"/>',22) :
                          iconSvg('<circle cx="12" cy="12" r="9"/>',22)}
                      </span>
                    </button>`;
                  }
                  const p = entry.project;
                  const inactive = p.active === false;
                  const current = !this._mainBatchMode && mainProject?.repository === p.repository;
                  return `<button type="button" class="dra-picker-entry ${current ? "selected" : ""}"
                    data-repo="${this._escapeProject(p.repository)}" ${inactive ? "disabled" : ""}
                    aria-current="${current ? "true" : "false"}"
                    aria-label="${this._escapeProject(p.name)}${inactive ? ", inaktiv" : ""}">
                    <span class="dra-picker-entry-number">${i+1}</span>
                    <span class="dra-picker-entry-content">
                      <strong>${this._escapeProject(p.name)}</strong>
                      <span class="dra-picker-entry-repository">${this._escapeProject(p.repository)}</span>
                    </span>
                    ${inactive ? '<span class="dra-picker-inactive">Inaktiv</span>' : ""}
                    <span class="dra-picker-check" aria-hidden="true">
                      ${current ? iconSvg('<circle cx="12" cy="12" r="9"/><path d="m8 12 2.5 2.5L16 9"/>',22) :
                        iconSvg('<circle cx="12" cy="12" r="9"/>',22)}
                    </span>
                  </button>`;
                }).join("")}
              </div>
              <p class="dra-picker-batch-message" role="status">${this._escapeProject(this._pickerBatchMessage)}</p>

            </section>
          </div>` : ""}
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
              <p class="note">Reihenfolge: Anzeige, Standardprojekt und Priorität der späteren Sammelaktualisierung. GitHub-Zugriff nur nach Prüfung.</p>
              <details class="dra-source-extra project-access-legend"><summary><span>GitHub-Zugriffsrechte <span aria-hidden="true">ⓘ</span></span><span>Legende <span class="project-access-chevron" aria-hidden="true">⌄</span></span></summary><p class="note">RW = Lesezugriff bestätigt, Schreibrecht von GitHub gemeldet (nicht praktisch getestet). RO = Lesezugriff bestätigt. ? = ungeprüft. X = Zugriff fehlgeschlagen.</p></details>
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
          <section class="project-batch-card" aria-labelledby="project-batch-title">
            <div class="project-batch-head">
              <span class="project-batch-icon">${iconSvg('<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18"/><path d="m9 15 2 2 4-4"/>',22)}</span>
              <div class="project-batch-text">
                <strong id="project-batch-title">Sammelaktualisierung</strong>
                <span class="note">Projektvorauswahl für spätere Sammelaktualisierungen · keine Installation</span>
                <span class="project-batch-count">${this._projects.filter(p => p.active !== false && p.batch_preselect !== false).length} von ${this._projects.filter(p => p.active !== false).length} aktiven Projekten ausgewählt</span>
              </div>
              <button id="batch-open" class="project-batch-edit" ${this._projects.length === 0 || this._batchBusy || this._checkAllBusy ? "disabled" : ""}>
                ${iconSvg('<path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L9 17l-4 1 1-4Z"/>',19)}
                <span>Auswahl bearbeiten</span>
              </button>
            </div>
            <p class="note" role="status">${this._escapeProject(this._batchDialogOpen ? "" : this._batchMessage)}</p>
          </section>
          <div class="project-v2-card">
            <div class="project-v2-details">
              <strong>Deploy Relay Agent V2</strong>
              <span class="note">Zentrale Einstellungen · GitHub-Lesezugang · Quellprüfung</span>
            </div>
            <div class="project-v2-status ${this._gitReadConfigured ? "configured" : "unconfigured"}">
              ${this._gitReadConfigured ? "Lesezugang eingerichtet" : "Lesezugang nicht eingerichtet"}
            </div>
            <button id="project-v2-settings-open" class="project-v2-settings-button"
              title="V2-Einstellungen öffnen" aria-label="Einstellungen für Deploy Relay Agent V2 öffnen"
              ${this._checkAllBusy || this._gitReadBusy ? "disabled" : ""}>${metalSvg(gearIcon,"v2",0)}</button>
          </div>
              <div class="dialog-actions project-management-footer">
                <button id="project-management-dismiss"
                  ${this._projectBusy || this._sourceBusy || this._gitReadBusy ? "disabled" : ""}>${closeIcon}<span>Schließen</span></button>
              </div>
              </div>
            </section>
          </div>` : ""}
        ${this._v2SettingsOpen ? `
          <div class="git-dialog-backdrop" id="project-v2-settings-backdrop">
            <section class="git-dialog project-v2-settings-dialog" id="project-v2-settings-dialog"
              role="dialog" aria-modal="true" aria-labelledby="project-v2-settings-title" tabindex="-1">
              <header>
                <div><h2 id="project-v2-settings-title">Deploy Relay Agent V2 · Einstellungen</h2>
                  <p class="note">Zentrale GitHub-Zugänge und schreibgeschützte Quellprüfung</p></div>
                <button id="project-v2-settings-close" aria-label="V2-Einstellungen schließen"
                  ${this._gitReadBusy || this._sourceBusy ? "disabled" : ""}>${closeIcon}</button>
              </header>
              <div class="project-v2-settings-scroll">
                <h3>Privater GitHub-Lesezugang für V2</h3>
          <p class="note">Optional für private Projekt-Repositories. Nur einen
          eigenen GitHub-Token mit möglichst minimalem Leserecht auf die
          benötigten Repositories verwenden. Niemals V1-Zugangsdaten oder
          den separaten Git-Diagnoseexport-Zugang wiederverwenden.</p>
          <label>V2-Lesetoken (wird nicht wieder angezeigt)
            <input id="source-read-token" class="project-text" type="password"
            autocomplete="new-password" placeholder="Separater GitHub-Token" /></label>
          <div class="v2-token-buttons">
            <button id="git-read-save" ${this._gitReadBusy ? "disabled" : ""}>Lesezugang speichern</button>
            <button id="git-read-clear" ${!this._gitReadConfigured || this._gitReadBusy ? "disabled" : ""}>Lesezugang entfernen</button>
          </div>
          <p class="note">V2-Lesezugang: ${this._gitReadConfigured ? "eingerichtet" : "nicht eingerichtet"}.
          ${this._escapeProject(this._gitReadMessage)}</p>
          <details id="v2-source-advanced" class="v2-source-advanced" ${this._v2AdvancedOpen ? "open" : ""}>
          <summary>Erweiterte Quellprüfung (optional)</summary>
          <label>Quellzweig (optional; leer = Standardzweig)
            <input id="source-ref" class="project-text" placeholder="deploy/dev" value="${this._escapeProject(this._v2SourceRef)}" autocomplete="off" /></label>
          <p class="note">Die Referenz gilt nur für die schreibgeschützte Quellprüfung. Die Quellwahl im Hauptmenü bleibt davon unabhängig.</p>
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
          </details>


                <div class="dialog-actions">
                  <button id="project-v2-settings-dismiss" ${this._gitReadBusy || this._sourceBusy ? "disabled" : ""}>Schließen</button>
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
                <select id="manage-access-mode" class="project-text" title="Angabe zu GitHub-Token-Berechtigungen, keine lokale Installationsfreigabe">
                  <option value="read_only" ${managed?.access_mode !== "read_write" ? "selected" : ""}>Read-Only</option>
                  <option value="read_write" ${managed?.access_mode === "read_write" ? "selected" : ""}>Read-Write</option>
                </select>
              </div>
            </div>
            <div class="project-token-actions">
              <button id="manage-token-save" ${!managed || this._projectBusy ? "disabled" : ""}>Token speichern</button>
              <button id="manage-connection-check" ${this._connectionBusy || this._projectBusy ? "disabled" : ""}>Verbindung prüfen</button>
            </div>
            ${this._draftConnectionCheck ? `<p id="manage-connection-feedback" class="connection-feedback ${this._draftConnectionCheck.status}" role="status">${this._escapeProject(this._draftConnectionCheck.message)}</p>` :
              managed && this._sourceChecks.get(managed.repository) ? `<p id="manage-connection-feedback" class="connection-feedback ${this._sourceChecks.get(managed.repository).status}" role="status">${this._escapeProject(this._sourceChecks.get(managed.repository).message)}</p>` :
              '<p id="manage-connection-feedback" class="note" role="status">Verbindung noch nicht geprüft.</p>'}
            <p class="note">Die Verbindungsprüfung funktioniert auch vor dem Speichern. Ein neu eingegebener Token wird ausschließlich für diese Prüfung verwendet und dabei nicht gespeichert.</p>
            <p class="note">Der Token bleibt serverseitig. Leer lassen, um den bisherigen Token beizubehalten.</p>
            <p class="note project-access-help">Die Zugriffsart ist ausschließlich eine Angabe über die GitHub-Token-Berechtigungen. Die lokale Installation erfordert unabhängig davon eine gesonderte Sicherheitsbestätigung.</p>
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

      </main>
    `;
    s.querySelector("#dra-toggle")?.addEventListener("click",()=>this._navigateMainView(this._view==="main"?"settings":"main"));
    s.querySelector("#dra-refresh")?.addEventListener("click",()=>this._refresh());
    s.querySelector("#dra-source-refresh")?.addEventListener("click",()=>this._refreshSourceHead());
    s.querySelector("#dra-project-picker-open")?.addEventListener("click",()=>this._openProjectPicker());
    s.querySelector("#dra-picker-close")?.addEventListener("click",()=>this._closeProjectPicker());
    s.querySelector("#dra-picker-dialog")?.addEventListener("keydown",event=>{
      if(event.key === "Escape") {event.preventDefault();this._closeProjectPicker();}
    });
    s.querySelectorAll(".dra-picker-entry").forEach(button=>
      button.addEventListener("click",()=>this._chooseMainProject(button.dataset.repo)));
    s.querySelector("#dra-picker-batch")?.addEventListener("click",()=>this._openPickerBatch());
    s.querySelector("#dra-main-batch-selection")?.addEventListener("toggle",e=>{
      // Ignore delayed events emitted by a former, detached render tree.
      if (e.currentTarget === this.shadowRoot?.querySelector("#dra-main-batch-selection"))
        this._mainBatchSelectionOpen = e.currentTarget.open;
    });
    s.querySelectorAll(".dra-batch-run-choice").forEach(input=>
      input.addEventListener("change",e=>this._toggleBatchRunProject(
        e.currentTarget.dataset.repo,e.currentTarget.checked)));
    s.querySelector("#dra-load-source-choices")?.addEventListener("click",()=>this._loadSourceChoices());
    s.querySelector("#dra-source-advanced > summary")?.addEventListener("click",()=>{
      // Update before native <details> activation so all later re-renders retain
      // the user choice, rather than opening automatically after every scan.
      this._sourceAdvancedOpen = !this.shadowRoot.querySelector("#dra-source-advanced").open;
    });
    s.querySelector("#dra-use-recommended")?.addEventListener("click",()=>{
      const ref=this._sourceChoices?.recommended?.ref;
      if (ref) this._applySourceChoice(ref);
    });
    s.querySelector("#dra-main-choice")?.addEventListener("change",e=>{
      if (e.target.value) this._applySourceChoice(e.target.value);
    });
    s.querySelector("#dra-main-ref")?.addEventListener("input",e=>{
      this._manualSourceRef = true;
      this._mainSourceRef=e.target.value;
      // Source previews are bound to the exact requested reference.
      this._sourcePreview=null;
      this._deploymentPreviewRef=null;
      this._sourceMessage="Referenz geändert. Vorschau erneut berechnen.";
    });
    s.querySelector("#dra-main-ref")?.addEventListener("change",()=>this._render());
    s.querySelector("#dra-project-manage")?.addEventListener("click",()=>this._openProjectDialog());
    s.querySelector("#dra-deployment-logs-toggle")?.addEventListener("click",()=>this._toggleDeploymentLogs());
    s.querySelector("#dra-history-refresh")?.addEventListener("click",()=>this._refreshHistoryManually());
    s.querySelector("#dra-logs-notes")?.addEventListener("toggle",e=>{
      this._logsNotesOpen = e.currentTarget.open;
    });
    s.querySelector("#dra-deployment-logs-clear")?.addEventListener("click",()=>{
      this._deploymentLogsOpen = true;
      this._deploymentLogsConfirm = true;
      this._render();
    });
    s.querySelector("#dra-logs-clear-cancel")?.addEventListener("click",()=>{
      this._deploymentLogsConfirm = false;
      this._render();
    });
    s.querySelector("#dra-logs-clear-confirm")?.addEventListener("click",()=>this._clearDeploymentLogs());
    s.querySelector("#dra-logs-json")?.addEventListener("click",()=>this._deploymentLogsAction("json"));
    s.querySelector("#dra-logs-git")?.addEventListener("click",()=>this._deploymentLogsAction("git"));
    s.querySelector("#dra-g2-retry-test")?.addEventListener("toggle",e=>{
      this._g2RetryTestOpen = e.currentTarget.open;
    });
    s.querySelector("#dra-g2-retry-prepare")?.addEventListener("click",()=>{
      if (this._deploymentLogsBusy || this._centralExport.pending) return;
      this._g2RetryTestConfirm=true; this._render();
    });
    s.querySelector("#dra-g2-retry-no")?.addEventListener("click",()=>{
      this._g2RetryTestConfirm=false; this._render();
    });
    s.querySelector("#dra-g2-retry-yes")?.addEventListener("click",()=>{
      this._deploymentLogsAction("g2_prepare");
    });
    s.querySelector("#dra-logs-copy")?.addEventListener("click",()=>this._deploymentLogsAction("copy"));
    s.querySelector("#dra-tests-expander")?.addEventListener("toggle",e=>{
      this._testsOpen = e.currentTarget.open;
    });
    s.querySelector("#dra-test-file-minus")?.addEventListener("click",()=>{this._testFileCount=Math.max(1,this._testFileCount-1);this._render();});
    s.querySelector("#dra-test-file-plus")?.addEventListener("click",()=>{this._testFileCount=Math.min(7,this._testFileCount+1);this._render();});
    s.querySelector("#dra-test-delay")?.addEventListener("change",e=>{this._testDelaySeconds=Number(e.currentTarget.value);this._render();});
    s.querySelector("#dra-test-version-confirm")?.addEventListener("change",e=>{
      this._testVersionConfirm = e.currentTarget.checked;
      const submit = this.shadowRoot?.querySelector("#dra-test-version-increment");
      if (submit) submit.disabled = !this._testVersionConfirm || this._testVersionBusy ||
        this._serverVersion !== DRA_V2_UI_VERSION;
    });
    s.querySelector("#dra-test-version-increment")?.addEventListener("click",()=>this._increaseTestVersion());
    s.querySelector("#dra-g2-connection-test")?.addEventListener("click",()=>{
      if (deploymentBusy || this._mainBatchMode || !mainProject ||
          this._serverVersion !== G2_TEST_PYTHON_VERSION) return;
      this._sourceCheck({dataset:{repo:mainProject.repository}}, true);
    });
    s.querySelector("#dra-frontend-refresh")?.addEventListener("click",()=>{
      if (postInstallJob?.frontend_reload_possible === true &&
          postInstallJob?.restart_required !== true) this._refreshFrontendAfterInstallation();
    });
    s.querySelector("#dra-deferred-restart-open")?.addEventListener("click",()=>{
      this._deferredRestartDialogOpen = true;
      this._render();
    });
    s.querySelector("#dra-deferred-restart-cancel")?.addEventListener("click",()=>{
      this._deferredRestartDialogOpen = false;
      this._render();
    });
    s.querySelector("#dra-deferred-restart-confirm")?.addEventListener("click",()=>this._confirmDeferredRestart());
    s.querySelector("#dra-ha-restart-open")?.addEventListener("click",()=>{
      if (!postInstallJob || postInstallJob.restart_required !== true || this._restartBusy ||
          runningJobs.length) return;
      this._restartDialogOpen = true;
      this._restartMessage = "";
      this._render();
    });
    s.querySelector("#dra-ha-restart-cancel")?.addEventListener("click",()=>{
      if (this._restartBusy) return;
      this._restartDialogOpen = false;
      this._render();
    });
    s.querySelector("#dra-ha-restart-confirm")?.addEventListener("click",()=>{
      if (postInstallJob?.restart_required === true && !runningJobs.length)
        this._requestHomeAssistantRestart();
    });
    s.querySelector("#dra-up-to-date-recheck")?.addEventListener("click",()=>{
      if (mainProject && !deploymentBusy) this._sourceCheck({dataset:{repo:mainProject.repository}});
    });
    s.querySelector("#dra-next-deployment-preview")?.addEventListener("click",()=>{
      if (!mainProject || deploymentBusy) return;
      this._sourceCheck({dataset:{repo:mainProject.repository}});
    });
    s.querySelector("#dra-take-control")?.addEventListener("click",async ()=>{
      if (!mainProject || this._controllerBusy ||
          !window.confirm("Bedienung dieses Projekts auf diesem Gerät übernehmen? Eine laufende Installation bleibt unverändert.")) return;
      if (await this._syncController(mainProject.repository, true)) {
        await this._restoreServerPreparation(mainProject.repository);
        this._installMessage = "Bedienung übernommen. Installation nur nach ausdrücklicher Bestätigung.";
      }
      this._render();
    });
    const closeReview=()=>{
      if (this._mainBatchBusy) return;
      this._batchReviewOpen=false;
      this._batchReviewChecked=false;
      this._render();
    };
    s.querySelector("#dra-batch-review-close")?.addEventListener("click",closeReview);
    s.querySelector("#dra-batch-review-cancel")?.addEventListener("click",closeReview);
    s.querySelector("#dra-batch-review-discard")?.addEventListener("click",()=>this._discardBatchReview());
    s.querySelector("#dra-batch-review-checked")?.addEventListener("change",e=>{
      this._batchReviewChecked=e.currentTarget.checked === true;
      const confirmButton=this.shadowRoot?.querySelector("#dra-batch-review-approve");
      if(confirmButton) confirmButton.disabled=!this._batchReviewChecked ||
        this._mainBatchBusy || this._batchStartUncertain || this._batchStatusError ||
        this._batchStatus?.review_digest !== this._batchReviewDigest;
    });
    s.querySelectorAll(".dra-review-copy-commit").forEach(button => button.addEventListener("click", async () => {
      const commit = button.dataset.commit;
      if (!/^[a-f0-9]{40}$/.test(commit || "")) return;
      try {
        if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(commit);
        else {
          const field = document.createElement("textarea");
          field.value = commit; field.style.position="fixed"; field.style.opacity="0";
          document.body.appendChild(field);
          try { field.select(); if (!document.execCommand("copy")) throw Error("copy failed"); }
          finally { field.remove(); }
        }
        button.textContent = "Commit kopiert";
      } catch (_error) { button.textContent = "Kopieren nicht möglich"; }
    }));
    s.querySelector("#dra-batch-review-approve")?.addEventListener("click",()=>this._startMainBatch());
    s.querySelector("#dra-batch-install-prepare")?.addEventListener("click",()=>this._prepareMainBatch());
    s.querySelector("#dra-batch-install-takeover")?.addEventListener("click",()=>this._takeOverMainBatch());
    s.querySelector("#dra-batch-review-handoff")?.addEventListener("click",()=>this._takeOverMainBatch());
    s.querySelector("#dra-batch-install-confirm")?.addEventListener("click",()=>this._startMainBatch());
    s.querySelector("#dra-preview")?.addEventListener("click",()=>{
      if (deploymentBusy) return;
      if (this._mainBatchMode) {
        if (deploymentStage === 1) void this._prepareMainBatch();
        else if (deploymentStage === 2) {
          if (this._batchChallenge) this._openBatchReview();
          else void this._takeOverMainBatch();
        }
      } else if (deploymentStage === 1 && mainProject) {
        this._sourceCheck({dataset:{repo:mainProject.repository}});
      } else if (deploymentStage === 2 && mainProject && !preparedInstall) {
        this._prepareInstallation(mainProject);
      }
    });
    s.querySelector("#dra-preview-details")?.addEventListener("toggle", event => {
      this._previewDetailsOpen = event.currentTarget.open;
    });
    s.querySelector("#dra-preview-status")?.addEventListener("change", event => {
      this._previewFileFilter = event.currentTarget.value;
      this._previewDetailsOpen = true;
      this._render();
    });
    s.querySelector("#dra-preview-search")?.addEventListener("input", event => {
      this._previewFileSearch = event.currentTarget.value;
      this._previewDetailsOpen = true;
      const position = event.currentTarget.selectionStart;
      this._render();
      const field = this.shadowRoot?.querySelector("#dra-preview-search");
      field?.focus();
      if (typeof position === "number") field?.setSelectionRange(position,position);
    });
    s.querySelector("#dra-audit-toggle")?.addEventListener("click", async () => {
      this._auditOpen = !this._auditOpen;
      this._render();
      if (this._auditOpen) await Promise.all([this._refreshDeploymentLogs(),this._refreshInstallAudit()]);
    });
    s.querySelector("#dra-audit-refresh")?.addEventListener("click", () => Promise.all([this._refreshDeploymentLogs(),this._refreshInstallAudit()]));
    s.querySelector("#dra-audit-json")?.addEventListener("click",()=>this._downloadAuditJSON());
    s.querySelector("#dra-audit-git")?.addEventListener("click",()=>this._exportAuditToGit());
    for (const [id,key] of [["dra-audit-level","_auditLevel"],["dra-audit-phase","_auditPhase"],["dra-audit-project","_auditProject"],["dra-audit-kind","_auditKind"]]) {
      s.querySelector("#"+id)?.addEventListener("change", event => {
        this[key] = event.currentTarget.value;
        this._render();
      });
    }
    s.querySelector("#dra-audit-search")?.addEventListener("input", event => {
      this._auditSearch = event.currentTarget.value;
      const caret = event.currentTarget.selectionStart;
      this._render();
      const field = this.shadowRoot?.querySelector("#dra-audit-search");
      field?.focus();
      if (typeof caret === "number") field?.setSelectionRange(caret,caret);
    });
    s.querySelector("#dra-log-filter")?.addEventListener("change", event => {
      this._logFilter = event.currentTarget.value;
      this._render();
    });
    s.querySelector("#dra-log-search")?.addEventListener("input", event => {
      this._logSearch = event.currentTarget.value;
      const position = event.currentTarget.selectionStart;
      this._render();
      const field = this.shadowRoot?.querySelector("#dra-log-search");
      field?.focus();
      if (typeof position === "number") field?.setSelectionRange(position,position);
    });
    s.querySelector("#dra-install-confirm")?.addEventListener("click",()=>this._confirmInstallation());
    s.querySelector("#dra-install-cancel")?.addEventListener("click",()=>{
      this._installPreparation = null;
      this._installMessage = "Vorbereitung verworfen. Es wurden keine Dateien geändert.";
      this._render();
    });
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
    s.querySelector("#project-v2-settings-open")?.addEventListener("click", () => this._openV2Settings());
    s.querySelector("#project-v2-settings-close")?.addEventListener("click", () => this._closeV2Settings());
    s.querySelector("#project-v2-settings-dismiss")?.addEventListener("click", () => this._closeV2Settings());
    s.querySelector("#project-v2-settings-dialog")?.addEventListener("keydown", event => {
      if (event.key === "Escape" && !this._gitReadBusy && !this._sourceBusy) {
        event.preventDefault(); this._closeV2Settings();
      }
    });
    s.querySelector("#source-ref")?.addEventListener("input", event => {this._v2SourceRef = event.target.value;});
    s.querySelector("#v2-source-advanced")?.addEventListener("toggle", event => {this._v2AdvancedOpen = event.target.open;});
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
    s.querySelectorAll(".project-move").forEach(b => b.addEventListener("click", () => this._movePickerEntry(b.dataset.repo,Number(b.dataset.direction))));
    s.querySelector(".project-batch-settings-open")?.addEventListener("click",() => this._openBatchDialog());
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
    s.querySelector("#manage-connection-check")?.addEventListener("click", () => this._checkDraftProjectConnection());
    for (const id of ["#manage-repository", "#manage-token"]) {
      s.querySelector(id)?.addEventListener("input", () => {
        this._draftConnectionCheck = null;
        const feedback = this.shadowRoot?.querySelector("#manage-connection-feedback");
        if (feedback) {
          feedback.className = "note";
          feedback.textContent = "Eingabe geändert · Verbindung erneut prüfen.";
        }
      });
    }
    s.querySelector("#manage-close")?.addEventListener("click", () => this._closeProjectSettings());
    s.querySelector("#manage-cancel")?.addEventListener("click", () => this._closeProjectSettings());
    s.querySelector("#manage-save")?.addEventListener("click", () => {
      if (this._projectSettingsRepo === "__new__") {
        this._saveNewProject();
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
    const batchReviewTable = s.querySelector(".dra-batch-review-table-wrap");
    if (batchReviewTable) {
      batchReviewTable.scrollLeft = batchReviewScroll;
      batchReviewTable.scrollTop = batchReviewTop;
    }
    const batchDialog = s.querySelector("#dra-batch-review-dialog");
    if (batchDialog) batchDialog.scrollTop = batchDialogTop;
    const v2SettingsScroll = s.querySelector(".project-v2-settings-scroll");
    if (v2SettingsScroll) v2SettingsScroll.scrollTop = previousV2SettingsScroll;
    const v2ReadInput = s.querySelector("#source-read-token");
    if (v2ReadInput) v2ReadInput.value = pendingV2ReadToken;
    const projectScroll = s.querySelector("#project-management-scroll");
    if (projectScroll) {
      projectScroll.scrollTop = previousProjectScroll;
      if (this._scrollToMovedProject) {
        const movedRow = [...projectScroll.querySelectorAll(".project-row")]
          .find(row => row.dataset.projectRepo === this._highlightMovedRepo);
        movedRow?.scrollIntoView({block:"nearest", behavior:"smooth"});
      }
    }
    for (const [node, top, left] of pageScrollPositions) {
      if (node.isConnected) { node.scrollTop = top; node.scrollLeft = left; }
    }
    this._scrollToMovedProject = false;
    this._syncCountdownTimer();
  }
}
if (!customElements.get("dra-v2-dev-lab-panel")) {
  customElements.define("dra-v2-dev-lab-panel", DRAV2DevLabPanel);
}

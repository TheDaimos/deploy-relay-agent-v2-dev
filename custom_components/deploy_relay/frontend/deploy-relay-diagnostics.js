const TEXT = {
  de: {
    title: "Diagnose & Logs",
    subtitle: "Strukturierte, bereinigte Deploy-Relay-Diagnose",
    refresh: "Logs aktualisieren",
    supportText: "Für Support kopieren",
    supportJson: "JSON kopieren",
    downloadJson: "JSON herunterladen",
    exportGit: "Diagnose nach Git exportieren",
    gitSetup: "Git-Export einrichten",
    gitManage: "Git-Zugang verwalten",
    exportGitRunning: "⏳ Exportiere …",
    exportGitDone: "✓ Export fertig",
    exportGitFailed: "Export fehlgeschlagen",
    exportGitCommit: "Git-Commit",
    gitConfigureTitle: "Git-Export einrichten",
    gitToken: "GitHub-Schreibtoken",
    gitTokenHint: "Separater Fine-grained Token nur für dieses Repository mit Contents: Read and write. Der normale Deploy-Relay-Lesetoken bleibt unverändert.",
    gitReservedPath: "Zielordner",
    saveToken: "Token speichern",
    saveAndExport: "Speichern & exportieren",
    removeToken: "Export-Token entfernen",
    cancel: "Abbrechen",
    gitConfigured: "Git-Export eingerichtet",
    gitNotConfigured: "Git-Export noch nicht eingerichtet",
    gitExported: "Diagnose nach Git exportiert",
    openGitHub: "In GitHub öffnen",
    clear: "Logs leeren",
    confirmClear: "Deploy-Relay-Diagnoselogs wirklich leeren?",
    allLevels: "Alle Level",
    allOperations: "Alle Vorgänge",
    search: "Logs durchsuchen …",
    events: "Ereignisse",
    warnings: "Warnungen",
    errors: "Fehler",
    errorHistory: "Fehlerhistorie",
    errorFamilies: "Fehlerfamilien",
    occurrences: "Vorkommen",
    variants: "Varianten",
    firstSeen: "Erstmals",
    lastSeen: "Zuletzt",
    drVersions: "Deploy-Relay-Versionen",
    signatureStable: "Signatur stabil",
    signatureChanged: "Signatur verändert",
    exactVariants: "Exakte Varianten",
    latest: "Letztes Ereignis",
    time: "Zeit",
    level: "Level",
    operation: "Vorgang",
    phase: "Phase",
    message: "Meldung",
    duration: "Dauer",
    run: "Vorgangs-ID",
    details: "Details",
    noLogs: "Noch keine passenden Diagnoseereignisse.",
    copied: "In Zwischenablage kopiert.",
    downloaded: "JSON-Datei erstellt.",
    cleared: "Diagnoselogs geleert.",
    projectScope: "Dieses Projekt",
    allScope: "Alle Projekte",
    persistence: "Persistenz",
    rotation: "Rotation",
    loading: "Lade Diagnose …",
  },
  en: {
    title: "Diagnostics & Logs",
    subtitle: "Structured, redacted Deploy Relay diagnostics",
    refresh: "Refresh logs",
    supportText: "Copy for support",
    supportJson: "Copy JSON",
    downloadJson: "Download JSON",
    exportGit: "Export diagnostics to Git",
    gitSetup: "Configure Git export",
    gitManage: "Manage Git access",
    exportGitRunning: "⏳ Exporting …",
    exportGitDone: "✓ Export complete",
    exportGitFailed: "Export failed",
    exportGitCommit: "Git commit",
    gitConfigureTitle: "Configure Git export",
    gitToken: "GitHub write token",
    gitTokenHint: "Separate fine-grained token for this repository with Contents: Read and write. The normal Deploy Relay read token remains unchanged.",
    gitReservedPath: "Target folder",
    saveToken: "Save token",
    saveAndExport: "Save & export",
    removeToken: "Remove export token",
    cancel: "Cancel",
    gitConfigured: "Git export configured",
    gitNotConfigured: "Git export not configured",
    gitExported: "Diagnostics exported to Git",
    openGitHub: "Open in GitHub",
    clear: "Clear logs",
    confirmClear: "Really clear Deploy Relay diagnostic logs?",
    allLevels: "All levels",
    allOperations: "All operations",
    search: "Search logs …",
    events: "Events",
    warnings: "Warnings",
    errors: "Errors",
    errorHistory: "Error history",
    errorFamilies: "Error families",
    occurrences: "Occurrences",
    variants: "Variants",
    firstSeen: "First seen",
    lastSeen: "Last seen",
    drVersions: "Deploy Relay versions",
    signatureStable: "Signature stable",
    signatureChanged: "Signature changed",
    exactVariants: "Exact variants",
    latest: "Latest event",
    time: "Time",
    level: "Level",
    operation: "Operation",
    phase: "Phase",
    message: "Message",
    duration: "Duration",
    run: "Run ID",
    details: "Details",
    noLogs: "No matching diagnostic events yet.",
    copied: "Copied to clipboard.",
    downloaded: "JSON file created.",
    cleared: "Diagnostic logs cleared.",
    projectScope: "This project",
    allScope: "All projects",
    persistence: "Persistence",
    rotation: "Rotation",
    loading: "Loading diagnostics …",
  },
};

const esc = (value) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

const pretty = (value) => JSON.stringify(value, null, 2);

const copyText = async (value) => {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(value);
      return;
    } catch (_err) {
      // Local Home Assistant is often opened over plain HTTP. Fall back below.
    }
  }

  const textarea = document.createElement("textarea");
  textarea.value = value;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  const copied = document.execCommand("copy");
  textarea.remove();
  if (!copied) {
    throw new Error("Clipboard copy is not available in this browser context");
  }
};

class DeployRelayDiagnosticsPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._project = null;
    this._events = [];
    this._stats = null;
    this._errorHistory = [];
    this._level = "ALL";
    this._operation = "ALL";
    this._scope = "project";
    this._search = "";
    this._loading = false;
    this._status = "";
    this._error = "";
    this._loadedOnce = false;
    this._showGitDialog = false;
    this._gitToken = "";
    this._gitExportAfterSave = false;
    this._gitConfiguredOverride = null;
    this._lastGitExport = null;
    this._gitExportState = "idle";
    this._loadSerial = 0;
  }

  set hass(value) {
    this._hass = value;
    this._render();
    if (value && !this._loadedOnce) {
      this._loadedOnce = true;
      this._loadLogs();
    }
  }

  set project(value) {
    const oldId = this._project?.subentry_id;
    this._project = value;
    if (oldId !== value?.subentry_id) {
      this._events = [];
      this._loadedOnce = false;
      this._gitConfiguredOverride = null;
      this._lastGitExport = null;
      this._gitExportState = "idle";
      this._render();
      if (this._hass) {
        this._loadedOnce = true;
        this._loadLogs();
      }
    } else {
      this._render();
    }
  }

  _t(key) {
    const lang = this._hass?.language?.toLowerCase?.().startsWith("de") ? "de" : "en";
    return TEXT[lang][key] ?? key;
  }

  async _call(message) {
    if (!this._hass) throw new Error("Home Assistant connection unavailable");
    return this._hass.callWS(message);
  }

  _projectId() {
    if (this._scope !== "project") return "";
    return this._project?.project_id || "";
  }

  _gitConfigured() {
    if (this._gitConfiguredOverride !== null) {
      return this._gitConfiguredOverride;
    }
    return Boolean(this._project?.git_export_configured);
  }

  async _loadLogs() {
    if (!this._hass) return;
    const loadSerial = ++this._loadSerial;
    this._loading = true;
    this._error = "";
    this._render();
    try {
      const response = await this._call({
        type: "deploy_relay/panel/logs",
        limit: 3000,
        project_id: this._projectId(),
      });
      if (loadSerial !== this._loadSerial) return;
      this._events = response.events || [];
      this._stats = response.stats || null;
      this._errorHistory = response.error_history || [];
    } catch (err) {
      if (loadSerial !== this._loadSerial) return;
      this._error = err?.message || String(err);
    } finally {
      if (loadSerial === this._loadSerial) {
        this._loading = false;
        this._render();
      }
    }
  }

  _filteredEvents() {
    const search = this._search.trim().toLowerCase();
    return this._events
      .filter((event) => {
        if (this._level !== "ALL" && event.level !== this._level) return false;
        if (this._operation !== "ALL" && event.operation !== this._operation) return false;
        if (!search) return true;
        const haystack = [
          event.timestamp,
          event.level,
          event.operation,
          event.phase,
          event.run_id,
          event.project_id,
          event.repository,
          event.message,
          JSON.stringify(event.details || {}),
          JSON.stringify(event.exception || {}),
        ].join(" ").toLowerCase();
        return haystack.includes(search);
      })
      .reverse();
  }

  _operations() {
    return [...new Set(this._events.map((event) => event.operation).filter(Boolean))]
      .sort((a, b) => a.localeCompare(b));
  }

  async _supportBundle() {
    return this._call({
      type: "deploy_relay/panel/support_bundle",
      subentry_id:
        this._scope === "project" && this._project?.subentry_id
          ? this._project.subentry_id
          : "",
      limit: 3000,
    });
  }

  async _copySupport(mode) {
    this._status = "";
    this._error = "";
    this._render();
    try {
      const bundle = await this._supportBundle();
      const value = mode === "json" ? pretty(bundle.json) : bundle.text;
      await copyText(value);
      this._status = this._t("copied");
    } catch (err) {
      this._error = err?.message || String(err);
    }
    this._render();
  }

  async _downloadJson() {
    this._status = "";
    this._error = "";
    this._render();
    try {
      const bundle = await this._supportBundle();
      const blob = new Blob([pretty(bundle.json)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const stamp = new Date().toISOString().replaceAll(":", "-");
      anchor.href = url;
      anchor.download = `deploy-relay-diagnostics-${stamp}.json`;
      anchor.click();
      URL.revokeObjectURL(url);
      this._status = this._t("downloaded");
    } catch (err) {
      this._error = err?.message || String(err);
    }
    this._render();
  }

  _openGitDialog(exportAfterSave) {
    if (!this._project) return;
    this._gitExportAfterSave = Boolean(exportAfterSave);
    this._gitToken = "";
    this._showGitDialog = true;
    this._error = "";
    this._render();
  }

  async _configureGitExport({ clear = false } = {}) {
    if (!this._project?.subentry_id) return;
    const token = this._gitToken.trim();
    if (!clear && !token) return;

    this._loading = true;
    this._error = "";
    this._status = "";
    this._render();

    try {
      await this._call({
        type: "deploy_relay/panel/configure_git_export",
        subentry_id: this._project.subentry_id,
        github_token: clear ? "" : token,
        clear,
      });
      this._gitConfiguredOverride = !clear;
      this._showGitDialog = false;
      this._gitToken = "";
      this._status = clear ? this._t("gitNotConfigured") : this._t("gitConfigured");

      const exportAfter = this._gitExportAfterSave && !clear;
      this._gitExportAfterSave = false;
      if (exportAfter) {
        await this._exportGit();
        return;
      }
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _exportGit() {
    if (!this._project?.subentry_id) return;
    if (!this._gitConfigured()) {
      this._openGitDialog(true);
      return;
    }

    this._loading = true;
    this._gitExportState = "running";
    this._error = "";
    this._status = "";
    this._lastGitExport = null;
    this._render();

    try {
      const result = await this._call({
        type: "deploy_relay/panel/export_git",
        subentry_id: this._project.subentry_id,
        limit: 3000,
      });
      this._lastGitExport = result;
      this._gitExportState = "success";
      const commit = String(result.commit_sha || "").slice(0, 12);
      this._status = commit
        ? `${this._t("gitExported")} · ${this._t("exportGitCommit")}: ${commit}`
        : this._t("gitExported");
      await this._loadLogs();
      return;
    } catch (err) {
      this._gitExportState = "error";
      this._error = err?.message || String(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _clearLogs() {
    if (!window.confirm(this._t("confirmClear"))) return;
    this._loading = true;
    this._render();
    try {
      await this._call({ type: "deploy_relay/panel/clear_logs" });
      this._status = this._t("cleared");
      await this._loadLogs();
      return;
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  _render() {
    if (!this.shadowRoot) return;
    const events = this._filteredEvents();
    const operations = this._operations();
    const stats = this._stats || {};
    const latest = stats.latest_timestamp || "—";
    const gitConfigured = this._gitConfigured();
    const gitExportLabel =
      this._gitExportState === "running"
        ? this._t("exportGitRunning")
        : this._gitExportState === "success"
          ? this._t("exportGitDone")
          : this._gitExportState === "error"
            ? this._t("exportGitFailed")
            : gitConfigured
              ? this._t("exportGit")
              : this._t("gitSetup");
    const gitExportClass =
      this._gitExportState === "success"
        ? "success"
        : this._gitExportState === "error"
          ? "error"
          : this._gitExportState === "running"
            ? "running"
            : "";

    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; margin-top:16px; min-width:0; max-width:100%; overflow-x:hidden; container-type:inline-size; }
        * { box-sizing:border-box; }
        .card {
          background: var(--card-background-color);
          border: 1px solid var(--divider-color);
          border-radius: 14px;
          padding: 18px;
          box-shadow: var(--ha-card-box-shadow, none);
          min-width:0;
          max-width:100%;
          overflow:hidden;
        }
        h2 { margin:0; font-size:18px; }
        .subtitle { color:var(--secondary-text-color); font-size:13px; margin-top:4px; }
        .head { display:flex; justify-content:space-between; gap:12px; align-items:flex-start; flex-wrap:wrap; min-width:0; }
        .actions, .filters { display:flex; gap:8px; flex-wrap:wrap; align-items:center; min-width:0; max-width:100%; }
        button, select, input { font:inherit; }
        button {
          border:1px solid var(--divider-color); border-radius:9px; padding:9px 12px;
          background:var(--secondary-background-color); color:var(--primary-text-color); cursor:pointer;
        }
        button.primary { background:var(--primary-color); color:var(--text-primary-color, #fff); border-color:var(--primary-color); }
        button.logs-refresh {
          min-width:168px;
          display:inline-flex;
          align-items:center;
          justify-content:center;
          gap:8px;
        }
        button.logs-refresh:disabled { opacity:1; cursor:wait; }
        .load-spinner {
          width:14px;
          height:14px;
          border:2px solid currentColor;
          border-right-color:transparent;
          border-radius:50%;
          flex:0 0 auto;
          animation:diag-spin .8s linear infinite;
        }
        .load-spinner.idle {
          visibility:hidden;
          animation:none;
        }
        @keyframes diag-spin { to { transform:rotate(360deg); } }
        button.danger { color:var(--error-color); }
        button.git-export.success {
          background:var(--success-color,#2e7d32);
          color:var(--text-primary-color,#fff);
          border-color:var(--success-color,#2e7d32);
          font-weight:700;
        }
        button.git-export.error {
          background:transparent;
          color:var(--error-color);
          border-color:var(--error-color);
          font-weight:700;
        }
        button.git-export.running {
          background:var(--secondary-background-color);
          color:var(--primary-text-color);
          border-color:var(--primary-color);
          font-weight:700;
        }
        button:disabled { opacity:.5; cursor:default; }
        button.git-export.running:disabled { opacity:1; }
        select, input {
          min-height:40px; border:1px solid var(--divider-color); border-radius:9px;
          padding:8px 10px; color:var(--primary-text-color); background:var(--primary-background-color);
        }
        input { min-width:260px; flex:1; }
        .stats {
          display:grid; grid-template-columns:repeat(4,minmax(110px,1fr));
          gap:10px; margin:16px 0;
        }
        .stat { border:1px solid var(--divider-color); border-radius:10px; padding:11px; text-align:center; }
        .stat b { display:block; font-size:21px; }
        .stat span { color:var(--secondary-text-color); font-size:12px; }
        .filters { margin:12px 0; }
        .history { margin:16px 0; }
        .history h3 { margin:0 0 10px; font-size:16px; }
        .history-wrap { overflow:auto; border:1px solid var(--divider-color); border-radius:10px; }
        .fingerprint { font-family:var(--code-font-family,monospace); font-size:11px; white-space:nowrap; }
        .history-status { font-weight:700; white-space:nowrap; }
        .history-status.changed { color:var(--warning-color,#f3b200); }
        .history-status.stable { color:var(--success-color,#2e7d32); }
        .variant-list { display:grid; gap:8px; margin-top:8px; }
        .variant-item { border-left:3px solid var(--divider-color); padding-left:9px; }
        .message { padding:10px 12px; border-radius:9px; margin:10px 0; overflow-wrap:anywhere; }
        .status { border:1px solid var(--success-color,#2e7d32); color:var(--success-color,#2e7d32); }
        .error { border:1px solid var(--error-color); color:var(--error-color); }
        .git-state {
          display:flex; gap:10px; align-items:center; flex-wrap:wrap;
          color:var(--secondary-text-color); font-size:12px; margin:10px 0 2px;
        }
        .git-state strong { color:var(--primary-text-color); }
        .git-state .git-manage { padding:5px 9px; min-height:0; font-size:12px; }
        .table-wrap { overflow:auto; max-width:100%; max-height:62vh; overscroll-behavior-inline:contain; border:1px solid var(--divider-color); border-radius:10px; }
        table { width:100%; min-width:720px; border-collapse:collapse; font-size:12px; }
        th,td { padding:9px 10px; border-bottom:1px solid var(--divider-color); text-align:left; vertical-align:top; }
        th { position:sticky; top:0; background:var(--card-background-color); z-index:2; }
        td.time, td.run { white-space:nowrap; font-family:var(--code-font-family,monospace); }
        td.run { max-width:190px; overflow:hidden; text-overflow:ellipsis; }
        .level { font-weight:700; white-space:nowrap; }
        .level.ERROR { color:var(--error-color); }
        .level.WARNING { color:var(--warning-color,#f3b200); }
        .level.INFO { color:var(--info-color,var(--primary-color)); }
        .level.DEBUG { color:var(--secondary-text-color); }
        details { max-width:520px; }
        pre {
          white-space:pre-wrap; overflow-wrap:anywhere; max-height:360px; overflow:auto;
          background:var(--secondary-background-color); padding:10px; border-radius:8px;
          font-family:var(--code-font-family,monospace); font-size:11px;
        }
        .meta { color:var(--secondary-text-color); font-size:11px; margin-top:10px; display:flex; gap:18px; flex-wrap:wrap; }
        .empty { color:var(--secondary-text-color); padding:18px; }
        .modal-backdrop {
          position:fixed; inset:0; z-index:110; display:grid; place-items:center;
          padding:20px; background:rgba(0,0,0,.55);
        }
        .modal {
          width:min(620px,100%); background:var(--card-background-color);
          border:1px solid var(--divider-color); border-radius:16px; padding:20px;
          box-shadow:0 18px 60px rgba(0,0,0,.35);
        }
        .modal h2 { margin:0 0 16px; }
        .field { display:grid; gap:6px; margin-bottom:14px; }
        .field input { width:100%; }
        .field small { color:var(--secondary-text-color); }
        .modal-actions { display:flex; justify-content:flex-end; gap:10px; flex-wrap:wrap; margin-top:18px; }
        a { color:var(--primary-color); }
        @container (max-width:760px) {
          .stats { grid-template-columns:repeat(2,minmax(0,1fr)); }
          .card { padding:12px; }
          input { min-width:0; width:100%; }
          .actions {
            display:grid;
            grid-template-columns:repeat(2,minmax(0,1fr));
            width:100%;
          }
          .actions button { width:100%; min-width:0; white-space:normal; }
          .filters { display:grid; grid-template-columns:1fr; width:100%; }
          .filters select, .filters input { width:100%; min-width:0; }
          .git-state, .meta { min-width:0; max-width:100%; overflow-wrap:anywhere; }
          .history-wrap, .table-wrap { width:100%; max-width:100%; }
          .modal-actions button { flex:1; }
        }
        @container (max-width:560px) {
          .actions { grid-template-columns:1fr; }
          .log-table, .history-table { min-width:0; display:block; }
          .log-table thead, .history-table thead { display:none; }
          .log-table tbody, .log-table tr, .log-table td,
          .history-table tbody, .history-table tr, .history-table td {
            display:block;
            width:100%;
          }
          .log-table tr, .history-table tr {
            padding:8px 10px;
            border-bottom:1px solid var(--divider-color);
          }
          .log-table td, .history-table td {
            display:grid;
            grid-template-columns:78px minmax(0,1fr);
            gap:8px;
            padding:5px 0;
            border:0;
            white-space:normal;
            overflow-wrap:anywhere;
          }
          .log-table td::before, .history-table td::before {
            content:attr(data-label);
            color:var(--secondary-text-color);
            font-weight:700;
          }
          .history-table td.empty { display:block; padding:14px 0; }
          .history-table td.empty::before { content:none; }
          .log-table td.time, .log-table td.run { white-space:normal; }
          .log-table td.run { max-width:none; overflow:visible; text-overflow:clip; }
        }
      </style>

      <section class="card">
        <div class="head">
          <div>
            <h2>${esc(this._t("title"))}</h2>
            <div class="subtitle">${esc(this._t("subtitle"))}</div>
          </div>
          <div class="actions">
            <button
              class="primary logs-refresh"
              id="logs-refresh"
              ${this._loading ? "disabled" : ""}
              aria-busy="${this._loading ? "true" : "false"}"
            ><span class="load-spinner ${this._loading ? "" : "idle"}" aria-hidden="true"></span><span>${esc(this._t("refresh"))}</span></button>
            <button id="support-text">${esc(this._t("supportText"))}</button>
            <button id="download-json">${esc(this._t("downloadJson"))}</button>
            <button
              class="primary git-export ${gitExportClass}"
              id="export-git"
              ${this._project && this._gitExportState !== "running" ? "" : "disabled"}
              aria-live="polite"
            >${esc(gitExportLabel)}</button>
            <button id="support-json">${esc(this._t("supportJson"))}</button>
            <button class="danger" id="clear-logs">${esc(this._t("clear"))}</button>
          </div>
        </div>

        <div class="git-state">
          <strong>${esc(gitConfigured ? this._t("gitConfigured") : this._t("gitNotConfigured"))}</strong>
          ${this._project ? `
            <span>${esc(this._project.repository || "")}</span>
            <span>${esc(this._project.git_export_branch || "")}</span>
            <span>${esc(this._project.git_export_root || ".deploy-relay/diagnostics")}</span>
            ${gitConfigured ? `<button class="git-manage" id="git-manage">${esc(this._t("gitManage"))}</button>` : ""}
          ` : ""}
        </div>

        ${this._status ? `<div class="message status">
          ${esc(this._status)}
          ${this._lastGitExport?.file_url ? ` · <a href="${esc(this._lastGitExport.file_url)}" target="_blank" rel="noopener">${esc(this._t("openGitHub"))}</a>` : ""}
        </div>` : ""}
        ${this._error ? `<div class="message error">${esc(this._error)}</div>` : ""}

        <div class="stats">
          <div class="stat"><b>${esc(stats.event_count ?? 0)}</b><span>${esc(this._t("events"))}</span></div>
          <div class="stat"><b>${esc(stats.warning_count ?? 0)}</b><span>${esc(this._t("warnings"))}</span></div>
          <div class="stat"><b>${esc(stats.error_count ?? 0)}</b><span>${esc(this._t("errors"))}</span></div>
          <div class="stat"><b style="font-size:12px">${esc(latest)}</b><span>${esc(this._t("latest"))}</span></div>
        </div>

        <div class="history">
          <h3>${esc(this._t("errorHistory"))}</h3>
          <div class="history-wrap">
          <table class="history-table">
              <thead>
                <tr>
                  <th>Typ / ID</th>
                  <th>${esc(this._t("occurrences"))}</th>
                  <th>${esc(this._t("variants"))}</th>
                  <th>${esc(this._t("firstSeen"))}</th>
                  <th>${esc(this._t("lastSeen"))}</th>
                  <th>${esc(this._t("drVersions"))}</th>
                  <th>Status</th>
                  <th>${esc(this._t("details"))}</th>
                </tr>
              </thead>
              <tbody>
                ${this._errorHistory.map((family) => `
                  <tr>
                    <td data-label="Typ / ID">
                      <strong>${esc(family.exception_type || "Exception")}</strong><br>
                      <span class="fingerprint">${esc(family.family_fingerprint || "—")}</span>
                    </td>
                    <td data-label="${esc(this._t("occurrences"))}">${esc(family.occurrences ?? 0)}</td>
                    <td data-label="${esc(this._t("variants"))}">${esc(family.variant_count ?? 0)}</td>
                    <td data-label="${esc(this._t("firstSeen"))}">
                      ${esc(family.first_seen || "—")}<br>
                      <small>DR ${esc(family.first_deploy_relay_version || "—")}</small>
                    </td>
                    <td data-label="${esc(this._t("lastSeen"))}">
                      ${esc(family.last_seen || "—")}<br>
                      <small>DR ${esc(family.last_deploy_relay_version || "—")}</small>
                    </td>
                    <td data-label="${esc(this._t("drVersions"))}">${esc((family.deploy_relay_versions || []).join(", ") || "—")}</td>
                    <td data-label="Status" class="history-status ${family.changed_signature ? "changed" : "stable"}">
                      ${esc(family.changed_signature ? this._t("signatureChanged") : this._t("signatureStable"))}
                    </td>
                    <td data-label="${esc(this._t("details"))}">
                      <details>
                        <summary>${esc(this._t("exactVariants"))}</summary>
                        <div class="variant-list">
                          ${(family.variants || []).map((variant) => `
                            <div class="variant-item">
                              <div class="fingerprint">${esc(variant.fingerprint || "—")}</div>
                              <div>
                                ${esc(this._t("occurrences"))}: ${esc(variant.occurrences ?? 0)} ·
                                ${esc(this._t("firstSeen"))}: ${esc(variant.first_seen || "—")} ·
                                ${esc(this._t("lastSeen"))}: ${esc(variant.last_seen || "—")}
                              </div>
                              <div>DR: ${esc((variant.deploy_relay_versions || []).join(", ") || "—")}</div>
                              ${variant.stack_signature?.length ? `
                                <pre>${esc(variant.stack_signature.join("\n"))}</pre>
                              ` : ""}
                            </div>
                          `).join("")}
                        </div>
                      </details>
                    </td>
                  </tr>
                `).join("") || `
                  <tr><td colspan="8" class="empty" data-label="">${esc(this._t("noLogs"))}</td></tr>
                `}
              </tbody>
            </table>
          </div>
        </div>

        <div class="filters">
          <select id="scope">
            <option value="project" ${this._scope === "project" ? "selected" : ""}>${esc(this._t("projectScope"))}</option>
            <option value="all" ${this._scope === "all" ? "selected" : ""}>${esc(this._t("allScope"))}</option>
          </select>
          <select id="level">
            <option value="ALL">${esc(this._t("allLevels"))}</option>
            ${["DEBUG","INFO","WARNING","ERROR"].map((level) =>
              `<option value="${level}" ${this._level === level ? "selected" : ""}>${level}</option>`
            ).join("")}
          </select>
          <select id="operation">
            <option value="ALL">${esc(this._t("allOperations"))}</option>
            ${operations.map((operation) =>
              `<option value="${esc(operation)}" ${this._operation === operation ? "selected" : ""}>${esc(operation)}</option>`
            ).join("")}
          </select>
          <input id="log-search" type="text" placeholder="${esc(this._t("search"))}" value="${esc(this._search)}">
        </div>

        <div class="table-wrap">
          <table class="log-table">
            <thead>
              <tr>
                <th>${esc(this._t("time"))}</th>
                <th>${esc(this._t("level"))}</th>
                <th>${esc(this._t("operation"))}</th>
                <th>${esc(this._t("phase"))}</th>
                <th>${esc(this._t("message"))}</th>
                <th>${esc(this._t("duration"))}</th>
                <th>${esc(this._t("run"))}</th>
                <th>${esc(this._t("details"))}</th>
              </tr>
            </thead>
            <tbody>
              ${events.map((event) => `
                <tr>
                  <td class="time" data-label="${esc(this._t("time"))}">${esc(event.timestamp)}</td>
                  <td class="level ${esc(event.level)}" data-label="${esc(this._t("level"))}">${esc(event.level)}</td>
                  <td data-label="${esc(this._t("operation"))}">${esc(event.operation || event.component || "—")}</td>
                  <td data-label="${esc(this._t("phase"))}">${esc(event.phase || "—")}</td>
                  <td data-label="${esc(this._t("message"))}">${esc(event.message)}</td>
                  <td data-label="${esc(this._t("duration"))}">${event.duration_ms == null ? "—" : esc(Number(event.duration_ms).toFixed(3) + " ms")}</td>
                  <td class="run" data-label="${esc(this._t("run"))}" title="${esc(event.run_id || "")}">${esc(event.run_id || "—")}</td>
                  <td data-label="${esc(this._t("details"))}">
                    ${event.details || event.exception ? `
                      <details>
                        <summary>${esc(this._t("details"))}</summary>
                        <pre>${esc(pretty({ details: event.details, exception: event.exception }))}</pre>
                      </details>
                    ` : "—"}
                  </td>
                </tr>
              `).join("") || `<tr><td colspan="8" class="empty">${esc(this._t("noLogs"))}</td></tr>`}
            </tbody>
          </table>
        </div>

        <div class="meta">
          <span>${esc(this._t("persistence"))}: ${esc(stats.persistence || "—")}</span>
          <span>${esc(this._t("rotation"))}: ${esc(stats.rotation_files ?? "—")} × ${esc(stats.rotation_bytes ?? "—")} B</span>
        </div>
      </section>

      ${this._showGitDialog ? `
        <div class="modal-backdrop">
          <div class="modal" role="dialog" aria-modal="true">
            <h2>${esc(this._t("gitConfigureTitle"))}</h2>
            <div class="field">
              <label for="git-token">${esc(this._t("gitToken"))}</label>
              <input id="git-token" type="password" autocomplete="off" value="${esc(this._gitToken)}">
              <small>${esc(this._t("gitTokenHint"))}</small>
            </div>
            <div class="field">
              <label>${esc(this._t("gitReservedPath"))}</label>
              <input type="text" readonly value="${esc(this._project?.git_export_root || ".deploy-relay/diagnostics")}">
            </div>
            <div class="modal-actions">
              ${gitConfigured ? `<button class="danger" id="git-remove">${esc(this._t("removeToken"))}</button>` : ""}
              <button id="git-cancel">${esc(this._t("cancel"))}</button>
              <button class="primary" id="git-save">${esc(this._gitExportAfterSave ? this._t("saveAndExport") : this._t("saveToken"))}</button>
            </div>
          </div>
        </div>
      ` : ""}
    `;

    this._bind();
  }

  _bind() {
    this.shadowRoot.querySelector("#logs-refresh")?.addEventListener("click", () => this._loadLogs());
    this.shadowRoot.querySelector("#support-text")?.addEventListener("click", () => this._copySupport("text"));
    this.shadowRoot.querySelector("#support-json")?.addEventListener("click", () => this._copySupport("json"));
    this.shadowRoot.querySelector("#download-json")?.addEventListener("click", () => this._downloadJson());
    this.shadowRoot.querySelector("#export-git")?.addEventListener("click", () => this._exportGit());
    this.shadowRoot.querySelector("#git-manage")?.addEventListener("click", () => this._openGitDialog(false));
    this.shadowRoot.querySelector("#clear-logs")?.addEventListener("click", () => this._clearLogs());

    this.shadowRoot.querySelector("#git-token")?.addEventListener("input", (event) => {
      this._gitToken = event.target.value;
    });
    this.shadowRoot.querySelector("#git-cancel")?.addEventListener("click", () => {
      this._showGitDialog = false;
      this._gitToken = "";
      this._gitExportAfterSave = false;
      this._render();
    });
    this.shadowRoot.querySelector("#git-save")?.addEventListener("click", () => this._configureGitExport());
    this.shadowRoot.querySelector("#git-remove")?.addEventListener("click", () => this._configureGitExport({ clear: true }));

    this.shadowRoot.querySelector("#scope")?.addEventListener("change", async (event) => {
      this._scope = event.target.value;
      await this._loadLogs();
    });
    this.shadowRoot.querySelector("#level")?.addEventListener("change", (event) => {
      this._level = event.target.value;
      this._render();
    });
    this.shadowRoot.querySelector("#operation")?.addEventListener("change", (event) => {
      this._operation = event.target.value;
      this._render();
    });
    this.shadowRoot.querySelector("#log-search")?.addEventListener("input", (event) => {
      this._search = event.target.value;
      this._render();
    });
  }
}

if (!customElements.get("deploy-relay-diagnostics-panel")) {
  customElements.define("deploy-relay-diagnostics-panel", DeployRelayDiagnosticsPanel);
}

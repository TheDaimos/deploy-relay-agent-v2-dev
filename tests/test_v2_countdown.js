/* Small, real JavaScript behavior check. No HA instance and no network. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

let now = 100000;
let nextId = 1;
const callbacks = new Map();
const cancelled = [];
const shadow = () => {
  const remaining = { textContent: "" };
  const repo = { value: "", focus() {} };
  const token = { value: "" };
  return {
    remaining, repo, token,
    innerHTML: "",
    querySelector(selector) {
      if (selector === "#remaining") return remaining;
      if (selector === "#git-dialog-repo") return repo;
      if (selector === "#git-dialog-token") return token;
      return null;
    },
    querySelectorAll() { return []; },
  };
};
class FakeElement {
  constructor() { this.shadowRoot = shadow(); this.isConnected = true; }
  attachShadow() { return this.shadowRoot; }
}
const elements = new Map();
const downloads = [];
const urls = [];
const mockDocument = {
  createElement(tag) {
    assert.equal(tag, "a");
    return {
      href: "", download: "",
      click() { downloads.push({filename:this.download, url:this.href}); },
    };
  },
};
const mockURL = {
  createObjectURL(blob) {
    assert(blob instanceof Blob);
    urls.push(blob);
    return "blob:local-dra-v2";
  },
  revokeObjectURL(_id) {},
};
const historyListeners = new Map();
const historyEntries = [{state:{ha_route:"dra-v2-dev-lab"}}];
let historyIndex = 0;
let historyPushed = 0;
const mockWindow = {
  location:{href:"https://homeassistant.test/dra-v2-dev-lab"},
  history:{
    get state() {return historyEntries[historyIndex].state;},
    pushState(state, unused, url) {
      assert.equal(url,mockWindow.location.href,"DRA must never change the HA route");
      historyEntries.splice(historyIndex+1);
      historyEntries.push({state});
      historyIndex++;
      historyPushed++;
    },
    back() {
      if (historyIndex < 1) return;
      historyIndex--;
      for (const fn of historyListeners.get("popstate") || [])
        fn({state:this.state});
    },
    forward() {
      if (historyIndex >= historyEntries.length-1) return;
      historyIndex++;
      for (const fn of historyListeners.get("popstate") || [])
        fn({state:this.state});
    },
  },
  addEventListener(type, fn) {
    const listeners = historyListeners.get(type) || new Set();
    listeners.add(fn);
    historyListeners.set(type,listeners);
  },
  removeEventListener(type, fn) {
    historyListeners.get(type)?.delete(fn);
  },
};
const ctx = {
  window:mockWindow,
  HTMLElement: FakeElement,
  Blob, document:mockDocument, URL:mockURL,
  customElements: { get: n => elements.get(n), define: (n, x) => elements.set(n, x) },
  Date: class extends Date { static now() { return now; } },
  setTimeout(cb, ms) {
    assert(ms === 1000 || ms === 1500);
    const id = nextId++;
    callbacks.set(id, { cb, ms });
    return id;
  },
  clearTimeout(id) { callbacks.delete(id); cancelled.push(id); },
};
vm.runInNewContext(
  fs.readFileSync("custom_components/deploy_relay_v2_dev/frontend/lab.js", "utf8"),
  ctx,
);
const Panel = elements.get("dra-v2-dev-lab-panel");
const panel = new Panel();
const opId = "a".repeat(32);
const sample = (status, idx = null) => ({
  operation_id: opId, status,
  current_index: idx, total_count: 40, phase_percent: idx === null ? null : idx * 2,
});

const tick = () => {
  const item = callbacks.get(panel._countdownTimer);
  assert(item, "active countdown must schedule one timer");
  callbacks.delete(panel._countdownTimer);
  now += 1000;
  item.cb();
};
panel._operation = sample("queued");
panel._observeCountdown(panel._operation);
panel._render();
assert.equal(panel._remainingText(), "Start wird vorbereitet");
assert.equal(panel._countdownTimer, null, "queued has no ticking timer");

panel._operation = sample("running", 5);
panel._observeCountdown(panel._operation);
panel._render();
assert.equal(panel._remainingText(), "Noch ca. 35 Sekunden");
assert.notEqual(panel._countdownTimer, null);
tick();
assert.equal(panel.shadowRoot.remaining.textContent, "Noch ca. 34 Sekunden");
const activeTimer = panel._countdownTimer;
panel._operation = sample("running", 5);
panel._observeCountdown(panel._operation); // identical backend snapshot must not reset clock
assert.equal(panel._remainingText(), "Noch ca. 34 Sekunden");
panel._render();
assert.equal(panel._countdownTimer, activeTimer, "re-render must not spawn extra timer");
now += 1000;
panel._operation = sample("running", 7);
panel._observeCountdown(panel._operation);
assert.equal(panel._remainingText(), "Noch ca. 33 Sekunden");
panel._operation = sample("running", 40);
panel._observeCountdown(panel._operation);
panel._render();
now += 9000;
assert.equal(panel._remainingText(), "Noch ca. 1 Sekunde");
panel._operation = sample("success", 40);
panel._observeCountdown(panel._operation);
panel._render();
assert.equal(panel._remainingText(), "0 Sekunden – abgeschlossen");
assert.equal(panel._countdownTimer, null);

panel._operation = { ...sample("running", 1), operation_id: "b".repeat(32) };
panel._observeCountdown(panel._operation);
panel._render();
assert.equal(panel._remainingText(), "Noch ca. 39 Sekunden");

panel._operation = { ...sample("running", 80), operation_id: "c".repeat(32), total_count: 87 };
panel._observeCountdown(panel._operation);
panel._render();
assert.equal(panel._remainingText(), "Mehrkernprüfung läuft");
panel._operation = { ...sample("running", 2), operation_id: "d".repeat(32), total_count: 7 };
panel._observeCountdown(panel._operation);
panel._render();
assert.equal(panel._remainingText(), "Mehrkernprüfung läuft");
panel._cpuStatus = {
  available_cores: 2,
  warning: {code:"cpu_limit_reduced", previous_available:12,
            available_cores:2, reduced_from:10},
};
panel._settings.max_worker_processes = 2;
panel._render();
assert(panel.shadowRoot.innerHTML.includes("Änderung der verfügbaren Prozessorkerne erkannt"));
assert(panel.shadowRoot.innerHTML.includes("Hinweis bestätigen"));
assert(panel.shadowRoot.innerHTML.includes("auf\n              2 reduziert"));
panel._cpuStatus = {available_cores:12, warning:null};
panel._render();
assert(!panel.shadowRoot.innerHTML.includes("Hinweis bestätigen"),
       "higher core visibility must not produce a warning");
assert(panel.shadowRoot.innerHTML.includes("Beim Start erkannte Prozessorkerne"));

panel.disconnectedCallback();
assert.equal(panel._countdownTimer, null, "detach must cancel all live countdown work");
assert.equal(panel._timer, null);
console.log("V2 countdown behavior PASS: backend anchor, ticking, re-sync, completion, detach");
// Independent JSON download must stay available without any GitHub target.
panel._operation = sample("success", 40);
panel._centralExport = {
  configured:false, repository_configured:false, repository:null,
  server_token_available:false, pending:false,
};
const id = "a".repeat(32);
const filename = "2026-10-09T11-00-00Z__deploy-relay-agent-v2__0.1.14__diagnostics__" + id + ".json";
const json = JSON.stringify({
  application:{id:"deploy-relay-agent-v2"},
  export:{exportId:id},
});
panel._hass = {
  async callWS(message) {
    assert.equal(message.type, "deploy_relay_v2_dev/test/download_json");
    return {
      filename, content:json, export_id:id,
      application_id:"deploy-relay-agent-v2", mime_type:"application/json",
    };
  },
};
panel._render();
assert(panel.shadowRoot.innerHTML.includes("JSON herunterladen"));
assert(panel.shadowRoot.innerHTML.includes("Git-Export"));
panel._downloadJSON().then(() => {
  assert.equal(downloads.length, 1);
  assert.equal(downloads[0].filename, filename);
  assert.equal(downloads[0].url, "blob:local-dra-v2");
  assert.equal(urls.length, 1);
  assert.equal(panel._downloadStatus, "JSON-Download gestartet: " + filename);
  assert.equal(panel._centralExport.repository, null);

// Main Git button is disabled without configured credentials, even with diagnostics.
panel._diagnosticsExportReady = true;
panel._gitAvailable = true;
panel._render();
assert(/id="git-export"[^>]*disabled/.test(panel.shadowRoot.innerHTML));
assert(panel.shadowRoot.innerHTML.includes('id="git-dialog-open"'));
panel._openGitDialog();
assert.equal(panel._gitDialogOpen, true);
assert(panel.shadowRoot.innerHTML.includes('role="dialog"'));
assert(panel.shadowRoot.innerHTML.includes("Es gibt kein Standardrepository."));
assert(panel.shadowRoot.innerHTML.includes("GitHub-Token"));
assert(panel.shadowRoot.innerHTML.includes("Speichern & prüfen"));
assert(!panel.shadowRoot.innerHTML.includes("github_pat_SECRET"));
panel.shadowRoot.token.value = "github_pat_SECRET";
panel.shadowRoot.repo.value = undefined; // real input missing after DOM remount
panel._render();
assert(!panel.shadowRoot.innerHTML.includes('value="undefined"'),
       "missing input must never overwrite remembered repository");
assert.equal(panel.shadowRoot.token.value, "github_pat_SECRET",
             "periodic HA refresh must preserve only transient unsent input");
panel._closeGitDialog();
assert.equal(panel._gitDialogOpen, false);
assert.equal(panel.shadowRoot.token.value, "", "closing discards unsent secret");
panel._openGitDialog();
panel.shadowRoot.repo.value = "MyPrivate/Archive";
panel.shadowRoot.token.value = "github_pat_FAKE_READ_WRITE";
let credentialRequests = 0;
panel._hass = {
  async callWS(msg) {
    credentialRequests++;
    assert.equal(msg.type, "deploy_relay_v2_dev/archive_repository/configure");
    assert.equal(msg.repository, "MyPrivate/Archive");
    assert.equal(msg.token, "github_pat_FAKE_READ_WRITE");
    return {
      configured: true, repository_configured: true,
      server_token_available: true, pending: false,
      repository: "MyPrivate/Archive", token_suffix: "WRITE",
    };
  },
};
Promise.resolve(panel._configureArchiveDialog()).then(async () => {
  assert.equal(credentialRequests, 1);
  assert.equal(panel.shadowRoot.token.value, "");
  assert.equal(panel._centralExport.repository, "MyPrivate/Archive");
  assert.equal(panel._centralExport.token_suffix, "WRITE");
  assert.equal(panel._gitConfigured, true);
  assert(panel.shadowRoot.innerHTML.includes("git-check-success"));
  assert(panel.shadowRoot.innerHTML.includes("•••••WRITE"));
  assert(!panel.shadowRoot.innerHTML.includes("github_pat_FAKE_READ_WRITE"));
  panel._closeGitDialog();
  assert.equal(panel._gitDialogOpen, false);
  panel._render();
  assert(!/id="git-export"[^>]*disabled/.test(panel.shadowRoot.innerHTML),
         "configured Git and completed diagnostic must enable export");
  assert(panel.shadowRoot.innerHTML.includes("MyPrivate/Archive"));
  assert(panel.shadowRoot.innerHTML.includes("•••••WRITE"));
  // The saved token is reused after closing and reopening the dialog.
  panel.shadowRoot.repo.value = undefined;
  panel._openGitDialog();
  assert(panel.shadowRoot.innerHTML.includes('value="MyPrivate/Archive"'));
  panel.shadowRoot.repo.value = "MyPrivate/Archive";
  panel.shadowRoot.token.value = "";
  panel._hass = {
    async callWS(msg) {
      assert.equal(msg.type, "deploy_relay_v2_dev/archive_repository/check");
      assert.equal(Object.hasOwn(msg, "token"), false);
      return {
        ...panel._centralExport, verified_private_read: true, branch: "main",
        write_verified: false,
      };
    },
  };
  await panel._configureArchiveDialog();
  assert(panel.shadowRoot.innerHTML.includes("✓ Zugang geprüft"));
  assert(panel.shadowRoot.innerHTML.includes("git-check-success"));
  // Failed verification must be explicit and red, keeping saved settings.
  panel.shadowRoot.repo.value = "MyPrivate/Archive";
  panel._hass = { async callWS() { throw new Error("synthetic 403"); } };
  await panel._configureArchiveDialog();
  assert(panel.shadowRoot.innerHTML.includes("git-check-error"));
  assert(panel.shadowRoot.innerHTML.includes("Prüfung fehlgeschlagen"));
  assert.equal(panel._centralExport.repository, "MyPrivate/Archive");
  console.log("DRA V2 archive main action, stored suffix and dialog verify PASS");
}).catch(error => {
  console.error(error);
  process.exitCode = 1;
});

  console.log("DRA V2 JSON download without GitHub PASS");
}).catch(error => {
  console.error(error);
  process.exitCode = 1;
});



(async () => {
  const testPanel = new Panel();
  const original = [
    {repository:"TheDaimos/alpha",name:"Alpha",active:true},
    {repository:"TheDaimos/bravo",name:"Bravo",active:true},
  ];
  testPanel._projects = original;
  testPanel._projectDialogOpen = true;
  testPanel._sourceChecks.set("TheDaimos/bravo", {status:"success",message:"Online"});
  testPanel._hass = {
    async callWS({type,action,repository,direction}) {
      assert.equal(type,"deploy_relay_v2_dev/projects/manage");
      assert.equal(action,"move");
      assert.equal(repository,"TheDaimos/bravo");
      assert.equal(direction,-1);
      return {projects:[original[1],original[0]]};
    },
  };
  await testPanel._manageProject("move",{repository:"TheDaimos/bravo",direction:-1});
  assert.equal(testPanel._projects[0].repository,"TheDaimos/bravo");
  assert.equal(testPanel._highlightMovedRepo,"TheDaimos/bravo");
  assert.equal(testPanel._projectDialogOpen,true);
  assert.equal(testPanel._sourceChecks.get("TheDaimos/bravo").status,"success");
  assert.match(testPanel.shadowRoot.innerHTML,/class="project-row connection-success recently-moved"/);
  assert.match(testPanel.shadowRoot.innerHTML,/>Online<\/span>/);
  assert.match(testPanel.shadowRoot.innerHTML,/>Prüfen<\/span>/);
  assert.match(testPanel.shadowRoot.innerHTML, /class="project-status-label"/);
  console.log("DRA V2 project priority selection and connection statuses PASS");
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});

(async () => {
  const bulkPanel = new Panel();
  bulkPanel._projectDialogOpen = true;
  bulkPanel._projects = [
    {repository:"TheDaimos/alpha",name:"Alpha",active:true},
    {repository:"TheDaimos/private",name:"Private",active:false},
    {repository:"TheDaimos/third",name:"Third",active:true},
  ];
  let running=0, maxRunning=0;
  const processed=[];
  bulkPanel._hass = {
    async callWS({type,repository}) {
      assert.equal(type,"deploy_relay_v2_dev/projects/connection_check");
      running++;
      maxRunning=Math.max(maxRunning,running);
      processed.push(repository);
      await Promise.resolve();
      running--;
      if (repository==="TheDaimos/private")
        return {repository,connected:false,reason:"Access denied"};
      return {repository,connected:true,private:false,authenticated:true,
              advertised_push:null,write_tested:false};
    },
  };
  const check=bulkPanel._checkAllProjectConnections();
  assert.equal(bulkPanel._checkAllBusy,true);
  assert.match(bulkPanel.shadowRoot.innerHTML, /id="project-check-all"[^>]*disabled/);
  await bulkPanel._checkAllProjectConnections(); // duplicate requests must be ignored
  await check;
  assert.equal(maxRunning,1,"Only one Github request may run at a time");
  assert.deepEqual(processed,["TheDaimos/alpha","TheDaimos/private","TheDaimos/third"]);
  assert.equal(bulkPanel._sourceChecks.get("TheDaimos/alpha").status,"success");
  assert.equal(bulkPanel._sourceChecks.get("TheDaimos/private").status,"failure");
  assert.equal(bulkPanel._sourceChecks.get("TheDaimos/third").status,"success");
  assert.equal(bulkPanel._checkAllBusy,false);
  assert.equal(bulkPanel._checkAllProgress,"Prüfung abgeschlossen: 2 online, 1 offline.");
  assert.match(bulkPanel.shadowRoot.innerHTML, /Alle Projekte prüfen/);
  console.log("DRA V2 sequential all-project Git connection check PASS");
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});

(() => {
  const metalPanel = new Panel();
  metalPanel._projectDialogOpen = true;
  metalPanel._projects = [
    {name:"Inactive project",repository:"TheDaimos/inactive",active:false},
    {name:"Active project",repository:"TheDaimos/active",active:true},
  ];
  metalPanel._render();
  const html = metalPanel.shadowRoot.innerHTML;
  assert.match(html, /<span class="project-inactive-label" aria-label="Projekt inaktiv">Inaktiv<\/span>/);
  assert.match(html, /<td class="project-entry-inactive">/);
  assert.equal((html.match(/aria-label="Projekt inaktiv">Inaktiv<\/span>/g)||[]).length,1);
  assert.doesNotMatch(html, /Status: <strong>Inaktiv/);
  assert.equal((html.match(/project-inactive-label/g)||[]).length >= 1,true);
  assert.match(html, /class="project-settings-open project-metal-button"/);
  assert.match(html, /class="project-move project-metal-button"/);
  assert.match(html, /<linearGradient id="dra-metal-settings-0"/);
  assert.match(html, /<linearGradient id="dra-metal-up-0"/);
  assert.match(html, /<linearGradient id="dra-metal-down-0"/);
  assert.match(html, /<linearGradient id="dra-metal-settings-1"/);
  assert.match(html, /stroke="url\(#dra-metal-settings-0\)"/);
  assert.match(html, /stroke="url\(#dra-metal-settings-1\)"/);
  console.log("DRA V2 metal icon gradient and inactive card render PASS");
})();

(() => {
  const selectionPanel = new Panel();
  selectionPanel._projectDialogOpen = true;
  selectionPanel._projects = [
    {name:"Project One",repository:"TheDaimos/one",active:true,access_mode:"read_only"},
    {name:"Project Two",repository:"TheDaimos/two",active:false,access_mode:"read_write"},
  ];
  selectionPanel._selectProjectRow("TheDaimos/two");
  assert.equal(selectionPanel._highlightMovedRepo,"TheDaimos/two");
  assert.equal(selectionPanel._projects[0].repository,"TheDaimos/one","Selecting does not reorder");
  assert.equal(selectionPanel._scrollToMovedProject,false);
  assert.match(selectionPanel.shadowRoot.innerHTML,/connection-unverified recently-moved/);
  assert.match(selectionPanel.shadowRoot.innerHTML,/aria-current="true"/);
  selectionPanel._selectProjectRow("TheDaimos/one");
  assert.equal(selectionPanel._highlightMovedRepo,"TheDaimos/one");
  selectionPanel._projectSettingsRepo = "TheDaimos/two";
  selectionPanel._render();
  const html = selectionPanel.shadowRoot.innerHTML;
  const summary = html.indexOf('class="project-token-summary"');
  const tokenLabel = html.indexOf("Gespeicherter Token:",summary);
  const access = html.indexOf('id="manage-access-mode"',summary);
  const tokenActions = html.indexOf('class="project-token-actions"',summary);
  assert(summary >= 0 && tokenLabel > summary && access > tokenLabel && tokenActions > access,
    "Access dropdown is right next to token hint in the same row");
  assert.match(html, /<option value="read_write" selected>Read-Write<\/option>/);
  assert.equal((html.match(/id="manage-access-mode"/g)||[]).length,1);
  console.log("DRA V2 selectable project rows and inline token access dropdown PASS");
})();

(() => {
  const pickerPanel = new Panel();
  pickerPanel._view = "main";
  pickerPanel._projects = [
    {name:"First",repository:"TheDaimos/first",active:true,batch_preselect:true},
    {name:"Inactive",repository:"TheDaimos/inactive",active:false,batch_preselect:false},
    {name:"Second",repository:"TheDaimos/second",active:true,batch_preselect:true},
  ];
  pickerPanel._render();
  assert.match(pickerPanel.shadowRoot.innerHTML,/id="dra-project-picker-open"/);
  assert.doesNotMatch(pickerPanel.shadowRoot.innerHTML,/id="dra-select"/);
  pickerPanel._openProjectPicker();
  assert.equal(pickerPanel._projectPickerOpen,true);
  const chooser = pickerPanel.shadowRoot.innerHTML;
  assert.match(chooser,/id="dra-picker-dialog"/);
  assert.match(chooser,/id="dra-picker-batch"/);
  assert.match(chooser,/dra-picker-divider/);
  assert.match(chooser,/TheDaimos\/first/);
  assert.match(chooser,/TheDaimos\/second/);
  assert.match(chooser,/data-repo="TheDaimos\/inactive" disabled/);
  assert.match(chooser,/class="dra-picker-entry selected"/);
  pickerPanel._chooseMainProject("TheDaimos/inactive");
  assert.equal(pickerPanel._projectPickerOpen,true,"inactive item cannot be selected");
  pickerPanel._chooseMainProject("TheDaimos/second");
  assert.equal(pickerPanel._projectPickerOpen,false);
  assert.equal(pickerPanel._selectedMainRepo,"TheDaimos/second");
  assert.match(pickerPanel.shadowRoot.innerHTML,/dra-project-picker-current-name">Second/);
  pickerPanel._openProjectPicker();
  pickerPanel._openPickerBatch();
  assert.equal(pickerPanel._projectPickerOpen,false);
  assert.equal(pickerPanel._batchDialogOpen,true);
  assert.match(pickerPanel.shadowRoot.innerHTML,/id="batch-dialog"/);
  assert.match(pickerPanel.shadowRoot.innerHTML,/Sammelaktualisierung · Projekte/);
  pickerPanel._cancelBatchDialog();
  assert.equal(pickerPanel._batchDialogOpen,false);
  console.log("DRA V2 custom project picker and safe batch-selection action PASS");
})();

(() => {
  const mainPanel = new Panel();
  mainPanel._view = "main";
  mainPanel._projects = [{repository:"TheDaimos/example",name:"Example",active:true}];
  mainPanel._render();
  const mainStart = mainPanel.shadowRoot.innerHTML.indexOf('id="dra-main-view"');
  const settingsStart = mainPanel.shadowRoot.innerHTML.indexOf('id="dra-settings-view"');
  const mainContent = mainPanel.shadowRoot.innerHTML.slice(mainStart,settingsStart);
  const settingsContent = mainPanel.shadowRoot.innerHTML.slice(settingsStart);
  assert.match(mainContent,/Geführter Ablauf/);
  assert.match(mainContent,/Quelle &amp; Version|Quelle & Version/);
  assert.match(mainContent,/id="dra-preview"/);
  assert.match(mainContent,/id="dra-project-manage"/);
  assert.doesNotMatch(mainContent,/id="dra-settings-project"/);
  assert.doesNotMatch(mainContent,/Diagnose & Logs/);
  assert.doesNotMatch(mainContent,/id="dra-open-diagnostics"/);
  assert.doesNotMatch(mainContent,/Während eines laufenden Tests wird/);
  assert.match(settingsContent,/Während eines laufenden Tests wird/);
  console.log("DRA V2 focused main view and diagnostics-only notes PASS");
})();

(() => {
  const p = new Panel();
  p._view = "main";
  p._projects = [
    {repository:"TheDaimos/alpha",name:"Alpha",active:true,batch_preselect:true},
    {repository:"TheDaimos/beta",name:"Beta",active:true,batch_preselect:false},
  ];
  p._projectDialogOpen = true;
  p._render();
  const projectHTML = p.shadowRoot.innerHTML;
  const management = projectHTML.indexOf('id="project-management-dialog"');
  const checkAll = projectHTML.indexOf('id="project-check-all"',management);
  const batch = projectHTML.indexOf('id="project-batch-title"',management);
  const v2Card = projectHTML.indexOf('class="project-v2-card"',management);
  const footer = projectHTML.indexOf('id="project-management-dismiss"',management);
  assert(management>=0 && checkAll<batch && batch<v2Card && v2Card<footer);
  assert.match(projectHTML,/1 von 2 aktiven Projekten ausgewählt/);
  assert.match(projectHTML,/id="project-v2-settings-open"/);
  assert.doesNotMatch(projectHTML,/<h3>Privater GitHub-Lesezugang für V2<\/h3>/);
  p._openV2Settings();
  assert.equal(p._v2SettingsOpen,true);
  const settingHTML = p.shadowRoot.innerHTML;
  assert.match(settingHTML,/id="project-v2-settings-dialog"/);
  assert.match(settingHTML,/id="source-read-token"/);
  assert.match(settingHTML,/id="git-read-save"/);
  assert.match(settingHTML,/GitHub-Quellprüfung/);
  assert.match(settingHTML,/Backup-Richtlinie/);
  assert.equal((settingHTML.match(/id="source-read-token"/g)||[]).length,1);
  p._closeV2Settings();
  assert.equal(p._v2SettingsOpen,false);
  p._openBatchDialog();
  assert.match(p.shadowRoot.innerHTML,/id="batch-dialog"/);
  assert.equal(p._batchSelection.length,1);
  p._cancelBatchDialog();
  console.log("DRA V2 management batch card and compact settings modal PASS");
})();

(() => {
  const navigationPanel = new Panel();
  navigationPanel.connectedCallback(); // Registers browser / native Back listener.
  assert.equal(navigationPanel._view,"main");
  const oldIndex = historyIndex;
  const oldPushes = historyPushed;
  navigationPanel._navigateMainView("settings");
  assert.equal(historyIndex,oldIndex+1);
  assert.equal(historyPushed,oldPushes+1);
  assert.equal(navigationPanel._view,"settings");
  assert.equal(historyEntries[historyIndex].state.ha_route,"dra-v2-dev-lab",
    "Preserve HA router history metadata");
  assert.equal(historyEntries[historyIndex].state.dra_v2_dev_view,
               navigationPanel._viewHistoryKey);
  assert.match(navigationPanel.shadowRoot.innerHTML,/id="dra-settings-view"/);
  mockWindow.history.back(); // Android native Back
  assert.equal(navigationPanel._view,"main");
  assert.equal(navigationPanel._viewHistoryActive,false);
  assert.equal(historyIndex,oldIndex);
  assert.match(navigationPanel.shadowRoot.innerHTML,/id="dra-main-view"/);
  // Home Assistant remains the next normal destination after returning to main.
  assert.equal(mockWindow.history.state.ha_route,"dra-v2-dev-lab");

  navigationPanel._navigateMainView("settings");
  navigationPanel._navigateMainView("main"); // "Hauptmenü" UI button
  assert.equal(navigationPanel._view,"main");
  assert.equal(historyIndex,oldIndex,"UI Back must consume own duplicate history entry");
  mockWindow.history.forward();
  assert.equal(navigationPanel._view,"settings","Browser forward may reopen settings");
  mockWindow.history.back();
  assert.equal(navigationPanel._view,"main");

  navigationPanel.disconnectedCallback();
  assert.equal(historyListeners.get("popstate")?.size || 0,0,
    "Global popstate event listeners must be removed on panel unmount");
  console.log("DRA V2 Android native Back / on-screen Main / forward history PASS");
})();

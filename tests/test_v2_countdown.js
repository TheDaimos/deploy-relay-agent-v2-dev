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
    assert([1000, 1200, 1500, 2400, 4800, 9600, 10000].includes(ms));
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

(function testBatchSourceFailureVisibleWithoutExport() {
  const p=new Panel();
  p._view="main";
  p._mainBatchMode=true;
  p._projects=[{
    project_id:"weather_router_private_extensions",
    name:"WeatherRouter Private Extensions",
    repository:"TheDaimos/weather-router-extensions-dev",
    active:true,
  }];
  p._batchRunSelected=new Set([p._projects[0].repository]);
  p._batchStatus={
    schema:"dra-v2-batch-status.v1",
    status:"failed",project_key:"weather_router_private_extensions",
    check_stage:"source_reference",error_code:"source_invalid",
    error_detail:"github_http_forbidden",items:[],
  };
  p._render();
  const view=p.shadowRoot.innerHTML;
  assert.match(view,/Quellenprüfung angehalten/);
  assert.match(view,/WeatherRouter Private Extensions/);
  assert.match(view,/GitHub-Referenz/);
  assert.match(view,/GitHub meldet 403/);
  assert.match(view,/Ein zusätzlicher Protokollexport ist dafür nicht notwendig/);
  console.log("DRA V2 HA batch source failure explained without external Git logs PASS");
})();



(async function testGuidedBatchActuallyAdvancesWithHALockedPreparation() {
  const p=new Panel();
  p._view="main";p._mainBatchMode=true;
  p._serverVersion="0.1.112";p._selectedMainRepo="TheDaimos/gewitterradar";
  p._projects=[
    {project_id:"gewitterradar",name:"Gewitterradar",repository:"TheDaimos/gewitterradar",active:true,batch_preselect:true},
    {project_id:"weather_router",name:"WeatherRouter",repository:"TheDaimos/weather-router-dev",active:true,batch_preselect:true},
  ];
  p._batchRunSelected=new Set(p._projects.map(x=>x.repository));
  const ws=[];
  p._hass={callWS:async request=>{
    ws.push(request.type);
    assert.equal(request.type,"deploy_relay_v2_dev/batch/prepare");
    assert.deepEqual([...request.repositories],["TheDaimos/gewitterradar","TheDaimos/weather-router-dev"]);
    assert.equal(request.client_id.length,32);
    return {
      schema:"dra-v2-batch-preparation.v1",challenge:"a".repeat(32),
      preparation:{schema:"dra-v2-batch-status.v1",status:"prepared",
        confirmation_required:true,review_digest:"f".repeat(64),
        items:request.repositories.map((repository,i)=>({
          repository,project_key:i===0?"gewitterradar":"weather_router",
          source_ref:"deploy/dev",source_commit:"b".repeat(40),
          installed_version:i===0?"4.11.88":"0.10.150",
          new_version:i===0?"4.11.94":"0.10.152",
          version_status:"verified_pair",version_marker:"BUILD_VERSION",
          add:1,change:0,remove:0,status:"prepared",
        })),current:0,total:2}
    };
  }};
  p._render();
  assert.match(p.shadowRoot.innerHTML,/1\/4 · Sammelinstallation prüfen und vorbereiten/);
  assert.match(p.shadowRoot.innerHTML,/id="dra-preview"/);
  await p._prepareMainBatch();
  assert.deepEqual(ws,["deploy_relay_v2_dev/batch/prepare"]);
  assert.equal(p._batchStatus.status,"prepared");
  assert.equal(p._batchChallenge,"a".repeat(32));
  assert.match(p.shadowRoot.innerHTML,/2\/4 · Versionen, Referenzen und Commits prüfen/);
  assert.match(p.shadowRoot.innerHTML,/Installierte Version/);
  assert.match(p.shadowRoot.innerHTML,/4\.11\.88/);
  assert.match(p.shadowRoot.innerHTML,/4\.11\.94/);
  assert.match(p.shadowRoot.innerHTML,/deploy\/dev/);
  assert.match(p.shadowRoot.innerHTML,/Prüfkennung/);
  assert.match(p.shadowRoot.innerHTML,/Dateiänderungen sind vorbereitet/);
  p._mainBatchPreview={count:2};
  p._render();
  assert.doesNotMatch(p.shadowRoot.innerHTML,/Die Quellstände sind noch nicht geprüft/,
    "a server-verified batch must not display the obsolete selection-only lock");
  console.log("DRA V2 guided batch advances from step 1 to HA-prepared step 2 PASS");
})().catch(e=>{console.error(e);process.exitCode=1;});

(async function testBatchReviewRejectsUnseenOrStaleCommitAndRequiresSignedHAReceipt() {
  const p=new Panel();
  p._mainBatchMode=true;p._view="main";p._serverVersion="0.1.112";
  p._projects=[{repository:"TheDaimos/gewitterradar",
    project_id:"gewitterradar",name:"Gewitterradar",active:true}];
  const row={repository:"TheDaimos/gewitterradar",project_key:"gewitterradar",
    source_ref:"deploy/dev",source_commit:"a".repeat(40),
    installed_version:"4.11.88",new_version:"4.11.94",
    version_status:"verified_pair",version_marker:"BUILD_VERSION",
    add:1,change:0,remove:0,status:"prepared"};
  const prep={schema:"dra-v2-batch-status.v1",status:"prepared",
    confirmation_required:true,review_digest:"c".repeat(64),items:[row]};
  p._batchStatus=prep;p._batchPreparation=prep;
  p._batchChallenge="b".repeat(32);p._batchReviewDigest=prep.review_digest;
  p._batchReviewOpen=true;p._batchReviewChecked=false;
  let count=0, sent=null;
  p._hass={callWS:async req=>{
    count++;sent=req;
    return {schema:"dra-v2-batch-start.v1",batch_id:"d".repeat(32),status:"queued"};
  }};
  p._pollInstallation=async()=>{};
  p._render();
  assert.match(p.shadowRoot.innerHTML,/4\.11\.88/);
  assert.match(p.shadowRoot.innerHTML,/4\.11\.94/);
  assert.match(p.shadowRoot.innerHTML,/a{40}/);
  assert.match(p.shadowRoot.innerHTML,/deploy\/dev/);
  assert.match(p.shadowRoot.innerHTML,/id="dra-batch-review-approve"\s+disabled/);
  await p._startMainBatch();
  assert.equal(count,0,"No installation until review checkbox selected");
  p._batchReviewChecked=true;
  p._batchReviewDigest="f".repeat(64);
  await p._startMainBatch();
  assert.equal(count,0,"A stale review digest must reject install");
  p._batchReviewDigest=prep.review_digest;
  const oldConfirm=mockWindow.confirm;
  mockWindow.confirm=()=>true;
  try {await p._startMainBatch();}
  finally {mockWindow.confirm=oldConfirm;}
  assert.equal(count,1);
  assert.equal(sent.type,"deploy_relay_v2_dev/batch/start");
  assert.equal(sent.review_confirm,true);
  assert.equal(sent.review_digest,"c".repeat(64));
  assert.equal(sent.challenge,"b".repeat(32));
  assert.equal(p._batchChallenge,null);
  console.log("DRA V2 review modal blocks unreviewed/stale commit and signs exact HA batch PASS");
})().catch(e=>{console.error(e);process.exitCode=1;});

(async function testStaleMainPreparationCannotUndoWeatherRouterRecommendation() {
  const p=new Panel();
  const repo="TheDaimos/weather-router-dev";
  p._selectedMainRepo=repo;p._view="main";p._serverVersion="0.1.112";
  p._projects=[{project_id:"weather_router",repository:repo,name:"WeatherRouter",active:true}];
  const prepared={schema:"dra-v2-install-preparation.v1",repository:repo,
    project_id:"weather_router",confirmation_required:true,
    source_ref:"main",source_commit:"c".repeat(40),challenge:"d".repeat(32)};
  p._installPreparation=prepared;p._mainSourceRef="main";
  p._hass={callWS:async req=>{
    if(req.type==="deploy_relay_v2_dev/projects/source_choices")
      return {schema:"dra-v2-source-choices.v1",repository:repo,
        default_ref:"main",recommended:{kind:"branch",ref:"deploy/dev",
          commit:"b".repeat(40),channel:"dev",explicit:true},
        choices:[{kind:"branch",ref:"main",commit:"c".repeat(40)},
          {kind:"branch",ref:"deploy/dev",commit:"b".repeat(40)}]};
    if(req.type==="deploy_relay_v2_dev/deployment/prepared_status")
      return {schema:"dra-v2-prepared-status.v1",preparation:prepared};
    throw Error("unexpected route "+req.type);
  }};
  p._syncController=async()=>true;
  p._sourceCheck=()=>{};
  p._pollSourceJob=async()=>{};
  await p._loadSourceChoices();
  assert.equal(p._mainSourceRef,"deploy/dev");
  assert.equal(p._installPreparation,null);
  await p._restoreServerPreparation(repo);
  assert.equal(p._mainSourceRef,"deploy/dev");
  assert.equal(p._installPreparation,null);
  p._manualSourceRef=true;p._mainSourceRef="main";
  await p._restoreServerPreparation(repo);
  assert.equal(p._mainSourceRef,"main");
  assert.equal(p._installPreparation?.source_ref,"main");
  console.log("DRA V2 old main-branch HA approval cannot override recommended deploy/dev PASS");
})().catch(e=>{console.error(e);process.exitCode=1;});


(function testBatchRunSelectionAndPersistentExpansion() {
  const p=new Panel();
  p._view="main";p._mainBatchMode=true;p._mainBatchSelectionOpen=true;
  p._projects=[
    {project_id:"deploy_relay",name:"DRA V1",
      repository:"TheDaimos/deploy-relay-agent-dev",active:true,batch_preselect:true},
    {project_id:"deploy_relay_agent_v2_dev",name:"DRA V2",
      repository:"TheDaimos/deploy-relay-agent-v2-dev",active:true,batch_preselect:true},
    {project_id:"weather_router",name:"WeatherRouter",
      repository:"TheDaimos/weather-router-dev",active:true,batch_preselect:true},
    {project_id:"gewitterradar",name:"Gewitterradar",
      repository:"TheDaimos/gewitterradar",active:true,batch_preselect:true},
  ];
  // V1 can be preselected, V2 self-update requires explicit opt-in.
  p._batchRunSelected=new Set(p._batchEligibleProjects()
    .filter(x=>!p._isOwnBatchUpdate(x)).map(x=>x.repository));
  assert.deepEqual(p._mainBatchProjects().map(x=>x.name),["DRA V1","WeatherRouter","Gewitterradar"]);
  p._render();
  assert.match(p.shadowRoot.innerHTML,/id="dra-main-batch-selection"\s+open/);
  assert.match(p.shadowRoot.innerHTML,/Eigenaktualisierung · zuletzt/);
  assert.match(p.shadowRoot.innerHTML,/Sammelupdate · 3 von 4 installierbaren Projekten/);
  p._toggleBatchRunProject("TheDaimos/weather-router-dev",false);
  assert.deepEqual(p._mainBatchProjects().map(x=>x.name),["DRA V1","Gewitterradar"]);
  assert.equal(p._projects[2].batch_preselect,true,"temporary choice must not change catalog");
  assert.match(p.shadowRoot.innerHTML,/id="dra-main-batch-selection"\s+open/);
  p._render();
  p._render();
  assert.match(p.shadowRoot.innerHTML,/id="dra-main-batch-selection"\s+open/);
  assert.equal(p._batchRunSelected.has("TheDaimos/weather-router-dev"),false);
  p._toggleBatchRunProject("TheDaimos/deploy-relay-agent-v2-dev",true);
  assert.deepEqual(p._mainBatchProjects().map(x=>x.name),["DRA V1","DRA V2","Gewitterradar"]);
  p._batchStatus={status:"prepared"};
  p._toggleBatchRunProject("TheDaimos/weather-router-dev",true);
  assert.equal(p._batchRunSelected.has("TheDaimos/weather-router-dev"),false,
    "prepared plan selection must be immutable");
  console.log("DRA V2 batch permits V1 and optional own update without losing per-run selection PASS");
})();

(async function testPreferredBranchOverridesAutomaticMainButNotManualChoice() {
  const p=new Panel();
  p._view="main";p._selectedMainRepo="TheDaimos/weather-router-dev";
  p._mainSourceRef="main";
  p._projects=[{project_id:"weather_router",name:"WeatherRouter",
    repository:"TheDaimos/weather-router-dev",active:true}];
  p._hass={async callWS(request){
    assert.equal(request.type,"deploy_relay_v2_dev/projects/source_choices");
    return {schema:"dra-v2-source-choices.v1",repository:request.repository,
      default_ref:"main",recommended:{kind:"branch",ref:"deploy/dev",explicit:true,
        channel:"dev",commit:"a".repeat(40)},
      choices:[{kind:"branch",ref:"main",commit:"b".repeat(40)},
        {kind:"branch",ref:"deploy/dev",commit:"a".repeat(40)}]};
  }};
  p._syncController=async()=>true;
  p._restoreServerPreparation=async()=>{};
  let scans=0;
  p._sourceCheck=()=>{scans++};
  await p._loadSourceChoices();
  assert.equal(p._mainSourceRef,"deploy/dev");
  assert.equal(scans,1);
  p._applySourceChoice("main");
  assert.equal(p._manualSourceRef,true);
  await p._loadSourceChoices();
  assert.equal(p._mainSourceRef,"main",
    "deliberately chosen main must never be overwritten");
  console.log("DRA V2 WeatherRouter development-branch default and explicit manual override PASS");
})().catch(e=>{console.error(e);process.exitCode=1;});


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
  testPanel._sourceChecks.set("TheDaimos/bravo", {status:"success",access_level:"RW",message:"Lesezugriff bestätigt"});
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
  assert.match(testPanel.shadowRoot.innerHTML,/>RW<\/span>/);
  assert.match(testPanel.shadowRoot.innerHTML,/>\?<\/span>/);
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
      return {repository,connected:true,read_verified:true,access_level:"RO",private:false,authenticated:true,
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
  assert.equal(bulkPanel._checkAllProgress,"Prüfung abgeschlossen: 2 mit Lesezugriff, 1 fehlgeschlagen.");
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
  assert.match(html, /class="project-settings-open project-settings-open-style project-metal-button"/);
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
  assert.match(chooser,/dra-picker-batch-entry/);
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
  assert.equal(pickerPanel._mainBatchMode,true);
  assert.equal(pickerPanel._batchDialogOpen,false,"Picker must not reopen preselection editor");
  assert.match(pickerPanel.shadowRoot.innerHTML,/Sammelupdate · 2 von 2 installierbaren Projekten/);
  assert.match(pickerPanel.shadowRoot.innerHTML,/dra-main-batch-entry/);
  assert.match(pickerPanel.shadowRoot.innerHTML,/data-stage="1"/);
  pickerPanel._openProjectPicker();
  pickerPanel._chooseMainProject("TheDaimos/first");
  assert.equal(pickerPanel._mainBatchMode,false);
  assert.equal(pickerPanel._selectedMainRepo,"TheDaimos/first");
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
  assert.doesNotMatch(mainContent,/<h2>Geführter Ablauf<\/h2>/);
  assert.match(mainContent,/<h2>Deployment<\/h2>/);
  assert.match(mainContent,/dra-deploy-progress/);
  assert.match(mainContent,/dra-deploy-steps/);
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
  assert.match(settingHTML,/Erweiterte Quellprüfung/);
  assert.doesNotMatch(settingHTML,/Backup-Richtlinie/);
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

(async () => {
  const batch = new Panel();
  batch._view = "main";
  batch._projects = [
    {name:"Alpha",repository:"TheDaimos/alpha",active:true,batch_preselect:true},
    {name:"Not Selected",repository:"TheDaimos/unselected",active:true,batch_preselect:false},
    {name:"Inactive",repository:"TheDaimos/inactive",active:false,batch_preselect:true},
    {name:"Gamma",repository:"TheDaimos/gamma",active:true,batch_preselect:true},
  ];
  let actualRequests = 0;
  batch._hass = {
    async callWS(request) {
      actualRequests++;
      assert.equal(request.type,"deploy_relay_v2_dev/batch/preview");
      assert.deepEqual([...request.repositories],["TheDaimos/alpha","TheDaimos/gamma"]);
      return {
        schema:"dra-v2-dev-batch-preview.v1",
        selected:[
          {repository:"TheDaimos/alpha",name:"Alpha",status:"not_checked"},
          {repository:"TheDaimos/gamma",name:"Gamma",status:"not_checked"},
        ],
        count:2,installation_enabled:false,sources_verified:false,
      };
    },
  };
  batch._openProjectPicker();
  batch._openPickerBatch();
  assert.equal(batch._mainBatchMode,true);
  assert.match(batch.shadowRoot.innerHTML,/Sammelupdate · 2 von 3 installierbaren Projekten/);
  assert.match(batch.shadowRoot.innerHTML,/data-repo="TheDaimos\/unselected"/);
  await batch._previewMainBatch();
  assert.equal(actualRequests,1);
  assert.equal(batch._mainBatchPreview.count,2);
  assert.match(batch._mainBatchMessage,/Quellstände noch nicht geprüft/);
  assert.match(batch.shadowRoot.innerHTML,/Gruppenauswahl bestätigt: 2 Projekte/);
  assert.match(batch.shadowRoot.innerHTML,/data-stage="1"/);
  assert.equal(batch._batchDialogOpen,false);
  console.log("DRA V2 collective read-only batch identity preview PASS");
})().catch(error => {console.error(error);process.exitCode=1;});

(() => {
  const blank = new Panel();
  blank._view = "main";
  blank._projects = [{name:"Inactive",repository:"TheDaimos/inactive",active:false,batch_preselect:true}];
  blank._openProjectPicker();
  blank._openPickerBatch();
  assert.equal(blank._projectPickerOpen,true);
  assert.equal(blank._mainBatchMode,false);
  assert.match(blank.shadowRoot.innerHTML,/Keine zulässigen Projekte aktiv/);
  console.log("DRA V2 empty batch set remains in picker PASS");
})();

(async () => {
  const movable = new Panel();
  movable._view = "main";
  movable._projectDialogOpen = true;
  movable._projects = [
    {name:"Alpha",repository:"TheDaimos/alpha",active:true,batch_preselect:true},
    {name:"Beta",repository:"TheDaimos/beta",active:true,batch_preselect:true},
  ];
  movable._pickerBatchPosition = 2;
  const requests = [];
  movable._hass = {async callWS(request) {
    requests.push(request);
    assert.equal(request.type,"deploy_relay_v2_dev/projects/manage");
    assert.equal(request.action,"move_batch");
    assert.equal(request.repository,"__batch_picker__");
    assert.equal(request.direction,-1);
    return {projects:movable._projects,picker_batch_position:1,installation_enabled:false};
  }};
  const entriesBefore = movable._pickerEntries();
  assert.deepEqual(entriesBefore.map(e=>e.kind),["project","project","batch"]);
  await movable._movePickerEntry("__batch_picker__",-1);
  assert.equal(movable._pickerBatchPosition,1);
  assert.deepEqual(movable._pickerEntries().map(e=>e.kind),["project","batch","project"]);
  assert.equal(movable._projects[0].repository,"TheDaimos/alpha");
  assert.equal(movable._projects[1].repository,"TheDaimos/beta");
  assert.equal(movable._highlightMovedRepo,"__batch_picker__");
  assert.match(movable.shadowRoot.innerHTML,/project-batch-picker-row recently-moved/);
  // Moving a real project toward the neighboring virtual row swaps only the virtual row.
  await movable._movePickerEntry("TheDaimos/alpha",1);
  assert.equal(requests.length,2);
  movable._projectPickerOpen = true;
  movable._view = "main";
  movable._render();
  const picker = movable.shadowRoot.innerHTML;
  const alphaAt = picker.indexOf('data-repo="TheDaimos/alpha"');
  const batchAt = picker.indexOf('id="dra-picker-batch"');
  const betaAt = picker.indexOf('data-repo="TheDaimos/beta"');
  assert(alphaAt >= 0 && batchAt > alphaAt && betaAt > batchAt);
  assert.equal((picker.match(/id="dra-picker-batch"/g)||[]).length,1);
  console.log("DRA V2 virtual Sammelupdate row movement and shared main picker order PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});

(async () => {
  const deployment = new Panel();
  deployment._view = "main";
  deployment._projects = [{repository:"TheDaimos/example",name:"Example",active:true}];
  let previewCount=0;
  deployment._hass = { async callWS(request) {
    previewCount++;
    if (request.type === "deploy_relay_v2_dev/projects/source_job/start") {
      assert.equal(request.repository,"TheDaimos/example");
      assert.equal(request.ref,"deploy/dev");
      await Promise.resolve(); // let the interim loading state be inspected
      return {
        schema:"dra-v2-source-preview-job.v1",operation_id:"a".repeat(32),
        repository:"TheDaimos/example",ref:"deploy/dev",status:"queued",
        installation_enabled:false,
      };
    }
    assert.equal(request.type,"deploy_relay_v2_dev/projects/source_job/status");
    assert.equal(request.operation_id,"a".repeat(32));
    return {
      schema:"dra-v2-source-preview-job-status.v1",installation_enabled:false,
      job:{
        schema:"dra-v2-source-preview-job.v1",operation_id:"a".repeat(32),
        repository:"TheDaimos/example",ref:"deploy/dev",status:"success",
        installation_enabled:false,
        result:{
          repository:"TheDaimos/example",installation_enabled:false,sources_verified:true,
          source_commit:"f".repeat(40),source_ref:"deploy/dev",
          add:[{path:"added"}],change:[],remove:[],unchanged_count:12,
        },
      },
    };
  }};
  deployment._mainSourceRef="deploy/dev";
  deployment._render();
  let view=deployment.shadowRoot.innerHTML;
  assert.match(view,/data-stage="1"/);
  assert.match(view,/1\/4 · Vorschau berechnen/);
  assert.match(view,/dra-deploy-progress idle/);
  assert.doesNotMatch(view,/3 · Installation vorbereiten<\/button>/);
  const running=deployment._sourceCheck({dataset:{repo:"TheDaimos/example"}});
  assert.match(deployment.shadowRoot.innerHTML,/dra-deploy-progress running/);
  assert.match(deployment.shadowRoot.innerHTML,/Vorschau wird berechnet/);
  await running;
  assert.equal(previewCount,2);
  assert.equal(deployment._deploymentPreviewRef,"deploy/dev");
  view=deployment.shadowRoot.innerHTML;
  assert.match(view,/data-stage="2"/);
  assert.match(view,/2\/4 · Installation vorbereiten/);
  assert.match(view,/dra-deploy-progress verified/);
  assert.match(view,/dra-deploy-step orange current/);
  assert.match(view,/Hinzugefügt: 1/);
  assert.match(view,/id="dra-preview"[^>]*disabled/);
  assert.equal((view.match(/id="dra-preview"/g)||[]).length,1);
  deployment._mainSourceRef="main";
  deployment._deploymentPreviewRef=null;
  deployment._sourcePreview=null;
  deployment._render();
  assert.match(deployment.shadowRoot.innerHTML,/data-stage="1"/);
  assert.equal(previewCount,2,"A reference change must not write or auto-install");
  console.log("DRA V2 unified 4-step Deployment button and true preview progress PASS");
})().catch(error => {console.error(error);process.exitCode=1;});

(async () => {
  const probe = new Panel();
  probe._view = "main";
  probe._serverVersion = "0.1.112";
  probe._projects = [{repository:"TheDaimos/gewitterradar",name:"Gewitterradar",active:true}];
  probe._mainSourceRef = "";
  const calls = [];
  probe._hass = {async callWS(request) {
    calls.push(request);
    if (request.type === "deploy_relay_v2_dev/projects/source_job/start") {
      assert.equal(request.connection_test,true);
      return {
        schema:"dra-v2-source-preview-job.v1",operation_id:"e".repeat(32),
        repository:request.repository,ref:"",status:"queued",
        connection_test:true,installation_enabled:false,
      };
    }
    assert.equal(request.type,"deploy_relay_v2_dev/projects/source_job/status");
    return {
      schema:"dra-v2-source-preview-job-status.v1",installation_enabled:false,
      job:{
        schema:"dra-v2-source-preview-job.v1",operation_id:"e".repeat(32),
        repository:"TheDaimos/gewitterradar",ref:"",
        status:"success",connection_test:true,installation_enabled:false,
        result:{repository:"TheDaimos/gewitterradar",
          sources_verified:true,installation_enabled:false,
          source_commit:"f".repeat(40),add:[],change:[],remove:[],unchanged_count:12},
      },
    };
  }};
  probe._render();
  assert.match(probe.shadowRoot.innerHTML,/id="dra-tests-expander"/);
  assert.match(probe.shadowRoot.innerHTML,/id="dra-g2-connection-test"/);
  assert.match(probe.shadowRoot.innerHTML,/Python-Laufzeit:/);
  // Older backend must reject the special test before any WS start call.
  probe._serverVersion = "0.1.64";
  probe._render();
  assert.match(probe.shadowRoot.innerHTML,/Versionsabgleich erforderlich/);
  assert.match(probe.shadowRoot.innerHTML,/id="dra-g2-connection-test"[^>]*disabled/);
  await probe._sourceCheck({dataset:{repo:"TheDaimos/gewitterradar"}},true);
  assert.equal(calls.length,0);
  assert.match(probe._sourceMessage,/Python-Laufzeit 0.1.64/);
  probe._serverVersion = "0.1.112";
  probe._render();
  assert.match(probe.shadowRoot.innerHTML,/Oberfläche und Laufzeit stimmen überein/);
  await probe._sourceCheck({dataset:{repo:"TheDaimos/gewitterradar"}},true);
  assert.equal(calls.length,2);
  assert.equal(probe._sourceConnectionTest,true);
  assert.match(probe._sourceMessage,/G2-Verbindungstest abgeschlossen/);
  assert.match(probe.shadowRoot.innerHTML,/data-stage="1"/,
    "a diagnostic connection test must never advance the deployment gate");
  assert.match(probe.shadowRoot.innerHTML,/Installation weiterhin gesperrt/);
  console.log("DRA V2 G2 fixed reconnect test is read-only and not a deployment preview PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});

(async () => {
  const panel = new Panel();
  panel._view = "main";
  panel._serverVersion = "0.1.112";
  panel._projects = [{repository:"TheDaimos/example",project_id:"example",
                      name:"Example",active:true,access_mode:"read_write"}];
  panel._selectedMainRepo = "TheDaimos/example";
  panel._sourceRepository = "TheDaimos/example";
  panel._mainSourceRef = "deploy/dev";
  panel._deploymentPreviewRef = "deploy/dev";
  panel._sourcePreview = {
    repository:"TheDaimos/example",sources_verified:true,
    installation_enabled:false,source_ref:"deploy/dev",
    source_commit:"a".repeat(40),add:[{path:"main.py"}],change:[],remove:[],
    unchanged_count:0,
  };
  const calls = [];
  panel._hass = {async callWS(request) {
    calls.push(request.type);
    if (request.type === "deploy_relay_v2_dev/deployment/control") {
      assert.equal(request.repository,"TheDaimos/example");
      assert.match(request.client_id,/^[0-9a-f]{32}$/);
      return {schema:"dra-v2-controller.v1",controller:true,occupied:false};
    }
    if (request.type === "deploy_relay_v2_dev/deployment/prepare") {
      assert.equal(request.commit,"a".repeat(40));
      return {schema:"dra-v2-install-preparation.v1",
              challenge:"b".repeat(32),confirmation_required:true,
              repository:"TheDaimos/example",source_ref:"deploy/dev",
              source_commit:"a".repeat(40),add:1,change:0,remove:0};
    }
    if (request.type === "deploy_relay_v2_dev/deployment/start") {
      assert.equal(request.confirm,true);
      assert.equal(request.challenge,"b".repeat(32));
      return {schema:"dra-v2-install-start.v1",job:{
        operation_id:"c".repeat(32),project_key:"example",
        source_commit:"a".repeat(40),status:"running",phase:"staging"}};
    }
    assert.equal(request.type,"deploy_relay_v2_dev/deployment/status");
    assert.equal(request.operation_id,undefined,
      "the HA status endpoint returns all parallel jobs without a browser cursor");
    const done={
      operation_id:"c".repeat(32),project_key:"example",
      source_commit:"a".repeat(40),status:"success",phase:"complete",
      restart_required:true};
    return {schema:"dra-v2-install-status.v1",job:done,jobs:[done]};
  }};
  panel._render();
  assert.match(panel.shadowRoot.innerHTML,/data-stage="2"/);
  assert.doesNotMatch(panel.shadowRoot.innerHTML,/id="dra-preview"[^>]*disabled/);
  await panel._prepareInstallation(panel._projects[0]);
  panel._render();
  assert.match(panel.shadowRoot.innerHTML,/id="dra-install-confirm"/);
  assert.deepEqual(calls,["deploy_relay_v2_dev/deployment/control",
    "deploy_relay_v2_dev/deployment/prepare"],
    "preparing must never start a write");
  await panel._confirmInstallation();
  panel._render();
  assert.equal(panel._installJob.status,"success");
  assert.match(panel.shadowRoot.innerHTML,/data-stage="4"/);
  assert.match(panel.shadowRoot.innerHTML,/Home-Assistant-Neustart erforderlich/);
  assert.deepEqual(calls,[
    "deploy_relay_v2_dev/deployment/control",
    "deploy_relay_v2_dev/deployment/prepare",
    "deploy_relay_v2_dev/deployment/control",
    "deploy_relay_v2_dev/deployment/start",
    "deploy_relay_v2_dev/deployment/status",
    "deploy_relay_v2_dev/batch/status",
  ]);
  console.log("DRA V2 stage-2 one-time confirmation and server result PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});

(async () => {
  const panel = new Panel();
  panel._serverVersion = "0.1.112";
  panel._projects = [
    {repository:"TheDaimos/alpha",name:"Alpha",project_id:"alpha",
     access_mode:"read_write",active:true},
    {repository:"TheDaimos/beta",name:"Beta",project_id:"beta",
     access_mode:"read_write",active:true}
  ];
  panel._selectedMainRepo="TheDaimos/alpha";
  const alpha={operation_id:"a".repeat(32),project_key:"alpha",
    status:"running",phase:"backup",source_commit:"a".repeat(40)};
  const beta={operation_id:"b".repeat(32),project_key:"beta",
    status:"running",phase:"install",source_commit:"b".repeat(40)};
  panel._hass={async callWS(request) {
    assert.equal(request.type,"deploy_relay_v2_dev/deployment/status");
    assert.equal(request.operation_id,undefined);
    return {schema:"dra-v2-install-status.v1",job:beta,jobs:[beta,alpha]};
  }};
  await panel._pollInstallation();
  assert.equal(panel._installJob.project_key,"alpha");
  assert.match(panel.shadowRoot.innerHTML,/Parallele serverseitige Updates: 2 von maximal 4/);
  assert.match(panel.shadowRoot.innerHTML,/Projekt alpha/);
  assert.match(panel.shadowRoot.innerHTML,/Projekt beta/);
  panel._selectedMainRepo="TheDaimos/beta";
  await panel._pollInstallation();
  assert.equal(panel._installJob.project_key,"beta");
  assert.match(panel.shadowRoot.innerHTML,/data-stage="3"/);
  panel.disconnectedCallback();
  console.log("DRA V2 parallel job status survives switching selected projects PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});

(async () => {
  const panel = new Panel();
  panel._projectSettingsRepo = "__new__";
  panel._projectDialogOpen = true;
  const repository = "TheDaimos/Test-Repo-DRA-V2";
  const exampleSecret = "ghp_TEST_VALUE_NOT_A_REAL_SECRET_123456789";
  const fields = {
    "#manage-repository":{value:repository,addEventListener(){}},
    "#manage-token":{value:exampleSecret,addEventListener(){}},
    "#manage-name":{value:"DRA V2 Testprojekt"},
    "#manage-note":{value:"Nur künstliche Testdateien"},
    "#manage-active":{checked:true},
    "#manage-access-mode":{value:"read_write"},
    "#manage-connection-feedback":{textContent:"",className:"note"},
  };
  const orig = panel.shadowRoot.querySelector.bind(panel.shadowRoot);
  panel.shadowRoot.querySelector = q => fields[q] || orig(q);
  const requests=[];
  panel._hass={async callWS(request) {
    requests.push(request);
    if(request.type === "deploy_relay_v2_dev/projects/connection_check") {
      assert.equal(request.draft,true);
      assert.equal(request.repository,repository);
      assert.equal(request.token,exampleSecret);
      return {connected:true,repository,private:false,authenticated:true,
        advertised_push:null,write_tested:false};
    }
    if(request.type === "deploy_relay_v2_dev/projects/add") {
      assert.equal(request.token,undefined,
        "repository save must not mix the secret into public project metadata");
      return {projects:[{repository,project_id:"test_repo_dra_v2",name:request.name,
        active:true,access_mode:"read_write"}]};
    }
    assert.equal(request.type,"deploy_relay_v2_dev/projects/token");
    assert.equal(request.repository,repository);
    assert.equal(request.token,exampleSecret);
    return {projects:[{repository,project_id:"test_repo_dra_v2",name:"DRA V2 Testprojekt",
      active:true,access_mode:"read_write",token_configured:true,token_suffix:"56789"}]};
  }};
  await panel._checkDraftProjectConnection();
  assert.equal(requests.length,1,
    "draft connection check must run before any project or token save");
  assert.equal(panel._projects.length,0);
  assert.equal(panel._draftConnectionCheck.status,"success");
  assert.doesNotMatch(panel._draftConnectionCheck.message,/TEST_VALUE|123456789/);
  assert.match(panel.shadowRoot.innerHTML,/Verbindung erfolgreich/);
  assert.doesNotMatch(panel.shadowRoot.innerHTML,/ghp_TEST_VALUE/);
  await panel._saveNewProject();
  assert.deepEqual(requests.map(x=>x.type),[
    "deploy_relay_v2_dev/projects/connection_check",
    "deploy_relay_v2_dev/projects/add",
    "deploy_relay_v2_dev/projects/token"
  ]);
  assert.equal(panel._projectSettingsRepo,null);
  assert.equal(panel._projects[0].token_configured,true);
  assert.doesNotMatch(panel._projectMessage,/ghp_TEST_VALUE/);

  const publicPanel = new Panel();
  publicPanel._projectSettingsRepo="__new__";
  const publicFields = {
    "#manage-repository":{value:"TheDaimos/Test-Repo-DRA-V2",addEventListener(){}},
    "#manage-token":{value:"",addEventListener(){}},
    "#manage-name":{value:"DRA V2 Testprojekt"},
    "#manage-note":{value:""},
    "#manage-active":{checked:true},
    "#manage-access-mode":{value:"read_only"},
  };
  publicPanel.shadowRoot.querySelector=q=>publicFields[q] || null;
  const seen=[];
  publicPanel._hass={async callWS(req) {
    seen.push(req);
    return {connected:true,repository:req.repository,private:false,
      authenticated:false,write_tested:false};
  }};
  await publicPanel._checkDraftProjectConnection();
  assert.equal(seen[0].token,undefined,
    "public repository must be checkable without any token");
  assert.equal(publicPanel._draftConnectionCheck.status,"success");
  console.log("DRA V2 check new repository and optional transient token BEFORE saving PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});

(async () => {
  const versions = new Panel();
  versions._sourceJobRestored = true;
  versions._render();
  // At initial load no HA version may be claimed before the admin state reply.
  assert.match(versions.shadowRoot.innerHTML,/id="dra-version" class="dra-version pending"/);
  assert.match(versions.shadowRoot.innerHTML,/Oberfläche/);
  assert.match(versions.shadowRoot.innerHTML,/V0\.1\.112 DEV/);
  assert.match(versions.shadowRoot.innerHTML,/HA-Laufzeit: Noch nicht ermittelt/);
  assert.doesNotMatch(versions.shadowRoot.innerHTML,/HA-Laufzeit: V0\.1\.112 DEV/);

  const requests = [];
  versions._hass = {async callWS(request) {
    requests.push(request.type);
    if (request.type === "deploy_relay_v2_dev/deployment/status") {
      return {schema:"dra-v2-install-status.v1",job:null};
    }
    return {version:"0.1.112",operations:[],projects:[]};
  }};
  await versions._refresh();
  assert.deepEqual(requests,[
    "deploy_relay_v2_dev/test/state",
    "deploy_relay_v2_dev/deployment/sessions",
    "deploy_relay_v2_dev/deployment/status",
    "deploy_relay_v2_dev/batch/status",
    "deploy_relay_v2_dev/deployment/audit"
  ]);
  assert.match(versions.shadowRoot.innerHTML,/id="dra-version" class="dra-version matched"/);
  assert.match(versions.shadowRoot.innerHTML,/HA-Laufzeit: V0\.1\.112 DEV/);
  assert.doesNotMatch(versions.shadowRoot.innerHTML,/Abweichung ·/);

  versions._hass = {async callWS() {return {version:"0.1.71",operations:[],projects:[]};}};
  await versions._refresh();
  assert.match(versions.shadowRoot.innerHTML,/id="dra-version" class="dra-version mismatch"/);
  assert.match(versions.shadowRoot.innerHTML,/Abweichung · HA-Laufzeit: V0\.1\.71 DEV/);
  assert.match(versions.shadowRoot.innerHTML,/class="dra-version-number">V0\.1\.112 DEV/);
  assert.match(versions.shadowRoot.innerHTML,/aria-label="Versionsübersicht:/);

  versions._hass = {async callWS() {throw new Error("backend offline");}};
  await versions._refresh();
  assert.equal(versions._serverVersion,null);
  assert.match(versions.shadowRoot.innerHTML,/id="dra-version" class="dra-version pending"/);
  assert.match(versions.shadowRoot.innerHTML,/HA-Laufzeit: Noch nicht ermittelt/);
  assert.doesNotMatch(versions.shadowRoot.innerHTML,/HA-Laufzeit: V0\.1\.71 DEV/);
  console.log("DRA V2 header versions distinguish loaded frontend, real backend and offline state PASS");
})().catch(error => {console.error(error);process.exitCode=1;});

(async () => {
  const recovered = new Panel();
  const project = {repository:"TheDaimos/gewitterradar",name:"Gewitterradar",active:true};
  const id = "b".repeat(32);
  const requested = [];
  recovered._view = "main";
  recovered._hass = {async callWS(query) {
    requested.push(query.type);
    if (query.type === "deploy_relay_v2_dev/test/state") {
      return {projects:[project],operations:[],settings:{mode:"sequential"}};
    }
    if (query.type === "deploy_relay_v2_dev/deployment/status")
      return {schema:"dra-v2-install-status.v1",job:null};
    assert.equal(query.type,"deploy_relay_v2_dev/projects/source_job/status");
    return {
      schema:"dra-v2-source-preview-job-status.v1",installation_enabled:false,
      job: {
        schema:"dra-v2-source-preview-job.v1",operation_id:id,
        repository:project.repository,ref:"",status:"success",
        installation_enabled:false,result:{
          repository:project.repository,installation_enabled:false,sources_verified:true,
          source_commit:"f".repeat(40),add:[],change:[],remove:[],
          unchanged_count:12,
        },
      },
    };
  }};
  await recovered._refresh();
  assert.equal(recovered._selectedMainRepo,project.repository);
  assert.equal(recovered._sourceJobId,id);
  assert.equal(recovered._sourcePreview.sources_verified,true);
  assert.equal(recovered._deploymentPreviewRef,"");
  assert.match(recovered.shadowRoot.innerHTML,/Aktuell · Kein Update verfügbar/);
  assert.deepEqual(requested,[
    "deploy_relay_v2_dev/test/state",
    "deploy_relay_v2_dev/projects/source_job/status",
  ]);
  assert.doesNotMatch(recovered.shadowRoot.innerHTML,/3\/4 · Update/);
  console.log("DRA V2 HA-owned preview reappears after new browser panel session PASS");
})().catch(error => {console.error(error);process.exitCode=1;});

(async () => {
  const historic = new Panel();
  const id = "c".repeat(32);
  historic._deploymentLogsOpen = true;
  historic._hass = {async callWS(message) {
    assert.equal(message.type,"deploy_relay_v2_dev/projects/source_job/history");
    return {
      schema:"dra-v2-source-job-history-result.v1",
      installation_enabled:false,resume_allowed:false,source_preview_saved:false,
      records:[{
        operation_id:id,status:"success",
        created_at:"2026-10-11T12:12:00+00:00",
        finished_at:"2026-10-11T12:13:00+00:00",
        reason:null,installation_enabled:false,
        resume_allowed:false,source_preview_saved:false,
      }],
    };
  }};
  await historic._refreshSourceJobHistory();
  assert.equal(historic._sourceJobHistory[0].operation_id,id);
  assert.match(historic.shadowRoot.innerHTML,/Serverseitige Auftragshistorie/);
  assert.match(historic.shadowRoot.innerHTML,/Damals erfolgreich/);
  assert.match(historic.shadowRoot.innerHTML,/Nach HA-Neustart ist immer eine neue Quellprüfung erforderlich/);
  assert.doesNotMatch(historic.shadowRoot.innerHTML,/source_preview_saved:true/);
  console.log("DRA V2 durable metadata is shown without re-authorizing preview PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});

(async () => {
  const panel = new Panel();
  panel._deploymentLogsOpen = true;
  panel._deploymentLogs = [{status:"success",run_id:"e".repeat(32)}];
  const requests = [];
  let resumeLogs, resumeHistory;
  panel._hass = {async callWS(request) {
    requests.push(request.type);
    if (request.type === "deploy_relay_v2_dev/deployment/logs") {
      return new Promise(resolve => {resumeLogs=()=>resolve({
        schema:"dra-v2-dev-deployment-logs.v1",installation_enabled:false,
        records:[{status:"success",run_id:"f".repeat(32)}],count:1,
      });});
    }
    assert.equal(request.type,"deploy_relay_v2_dev/projects/source_job/history");
    return new Promise(resolve => {resumeHistory=()=>resolve({
      schema:"dra-v2-source-job-history-result.v1",
      installation_enabled:false,resume_allowed:false,source_preview_saved:false,
      records:[{operation_id:"a".repeat(32),status:"success",installation_enabled:false,
        resume_allowed:false,source_preview_saved:false,created_at:"2026-10-11T17:30:00Z",
        finished_at:"2026-10-11T17:31:00Z",reason:null}],
    });});
  }};
  panel._render();
  assert.match(panel.shadowRoot.innerHTML,/id="dra-history-refresh"/);
  assert.match(panel.shadowRoot.innerHTML,/Quellprotokolle und Auftragshistorie aktualisieren/);
  assert.match(panel.shadowRoot.innerHTML,/dra-history-refresh:focus-visible/);
  assert.match(panel.shadowRoot.innerHTML,/prefers-reduced-motion:reduce/);
  const current = panel._refreshHistoryManually();
  assert.equal(panel._historyRefreshBusy,true);
  assert.match(panel.shadowRoot.innerHTML,/Wird aktualisiert/);
  assert.match(panel.shadowRoot.innerHTML,/id="dra-history-refresh"[^>]*aria-busy="true"[^>]*disabled/);
  assert.match(panel.shadowRoot.innerHTML,/aria-live="polite"/);
  await panel._refreshHistoryManually();
  assert.equal(requests.length,2,"rapid double-tap must not duplicate read requests");
  assert.deepEqual(requests.sort(),[
    "deploy_relay_v2_dev/deployment/logs",
    "deploy_relay_v2_dev/projects/source_job/history",
  ]);
  resumeLogs();
  resumeHistory();
  await current;
  assert.equal(panel._historyRefreshBusy,false);
  assert.equal(panel._sourceJobHistory[0].status,"success");
  assert.equal(panel._deploymentLogs[0].run_id,"f".repeat(32));
  assert.equal(panel._historyRefreshStatus,"Aktualisiert");
  assert.equal(panel._historyRefreshTone,"success");
  assert.match(panel.shadowRoot.innerHTML,/class="dra-history-refresh-status success"/);
  assert.match(panel.shadowRoot.innerHTML,/aria-atomic="true"/);
  assert.match(panel.shadowRoot.innerHTML,/Quellprotokolle und Auftragshistorie erfolgreich vom Server geladen/);
  assert.match(panel.shadowRoot.innerHTML,/Damals erfolgreich/);
  assert.match(panel.shadowRoot.innerHTML,/Aktualisieren/);
  assert.doesNotMatch(panel.shadowRoot.innerHTML,/data-stage="2"/,
    "refreshing history must not authorize deployment");
  assert.equal(requests.length,2,"history refresh only reads the two allowlisted endpoints");
  console.log("DRA V2 premium manual logs/history refresh, busy and read-only gates PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});

(async () => {
  const panel = new Panel();
  panel._deploymentLogsOpen = true;
  let calls = 0;
  panel._hass = {async callWS(request) {
    calls++;
    assert(["deploy_relay_v2_dev/deployment/logs",
      "deploy_relay_v2_dev/projects/source_job/history"].includes(request.type));
    throw new Error("temporary mobile connection lost");
  }};
  await panel._refreshHistoryManually();
  assert.equal(calls,2);
  assert.equal(panel._historyRefreshBusy,false);
  assert.equal(panel._historyRefreshStatus,"Abruf fehlgeschlagen");
  assert.equal(panel._historyRefreshTone,"error");
  assert.match(panel.shadowRoot.innerHTML,/Bitte erneut versuchen/);
  assert.match(panel.shadowRoot.innerHTML,/erneut versuchen/);
  assert.doesNotMatch(panel.shadowRoot.innerHTML,/data-stage="2"/);
  console.log("DRA V2 manual history refresh failure remains fail-closed PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});

(async () => {
  const readable = new Panel();
  readable._view = "main";
  readable._deploymentLogsOpen = true;
  readable._sourceJobHistory = [
    {operation_id:"a".repeat(32),status:"success",
      created_at:"2026-10-11T10:00:00Z",finished_at:"2026-10-11T10:01:00Z"},
    {operation_id:"b".repeat(32),status:"failed",
      created_at:"2026-10-11T11:00:00Z",finished_at:"2026-10-11T11:01:00Z"},
    {operation_id:"c".repeat(32),status:"interrupted",
      created_at:"2026-10-11T12:00:00Z",finished_at:"2026-10-11T12:01:00Z"},
    {operation_id:"d".repeat(32),status:"queued",
      created_at:"2026-10-11T13:00:00Z",finished_at:null},
  ];
  readable._render();
  let html = readable.shadowRoot.innerHTML;
  assert.match(html,/\.dra-history-section \{border-top:1px solid/);
  assert.match(html,/\.dra-history-item \{/);
  assert.match(html,/dra-history-list" role="list"/);
  assert.match(html,/class="dra-history-heading-title"/);
  assert.match(html,/class="dra-history-refresh-status idle"/);
  assert.match(html,/Nicht geprüft/);
  assert.match(html,/\.dra-history-heading \{display:flex;align-items:center;justify-content:space-between;/);
  assert.match(html,/flex-wrap:nowrap;margin:0 0 8px/);
  const visibleHistory = html.slice(html.indexOf('class="dra-history-section"'),
    html.indexOf('<details class="dra-logs-notes"'));
  assert.doesNotMatch(visibleHistory,/Gespeicherte Auftragszustände; alte Ergebnisse sind nicht erneut freigegeben/);
  assert.doesNotMatch(visibleHistory,/Protokolle und Auftragshistorie sind aktuell/);
  assert.match(html,/Alte Prüfergebnisse werden niemals erneut freigegeben/);
  assert((html.match(/class="dra-history-item (?:success|failed|interrupted|queued)" role="listitem"/g)||[]).length >= 4,
    "all four records must render as separate accessible cards");
  for(const status of ["success","failed","interrupted","queued"]) {
    assert.match(html,new RegExp('class="dra-history-item '+status+'" role="listitem"'));
  }
  assert.match(html,/Weitere Aufträge durch Wischen innerhalb der Liste anzeigen/);
  assert.match(html,/id="dra-history-refresh"/);
  assert.match(html,/id="dra-logs-notes"\s*>/,"technical notes should be closed by default");
  assert.match(html,/<summary>Hinweise zu Protokollen und Datenschutz<\/summary>/);
  assert.match(html,/Nach HA-Neustart ist immer eine neue Quellprüfung erforderlich/);
  assert.match(html,/CPU-Zeit gilt für den gesamten Home-Assistant-Prozess/);
  assert.match(html,/Git-Export ausschließlich zum eingestellten privaten Archiv/);
  readable._logsNotesOpen=true;
  readable._render();
  html=readable.shadowRoot.innerHTML;
  assert.match(html,/id="dra-logs-notes" open>/,
    "disclosure state must survive normal rerenders");
  assert.doesNotMatch(html,/data-stage="2"/,
    "display-only changes may not unlock deployment");
  console.log("DRA V2 separated accessible job cards and compact disclosure PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});

(async () => {
  const g2 = new Panel();
  g2._deploymentLogsOpen = true;
  g2._g2RetryTestOpen = true;
  g2._deploymentLogs=[{run_id:"e".repeat(32),status:"success"}];
  g2._centralExport={configured:true,repository:"TheDaimos/Project-Log-And-Export",
    pending:false,server_token_available:true};
  const sent = [];
  g2._hass={async callWS(req) {
    sent.push(req);
    assert.equal(req.type,"deploy_relay_v2_dev/deployment/logs/export");
    if(req.g2_prepare === true) {
      assert.equal(req.g2_confirm,true);
      return {pending_prepared:true,pending:true,export_id:"a".repeat(32)};
    }
    assert.equal(req.g2_prepare,undefined);
    return {
      repository:"TheDaimos/Project-Log-And-Export",
      export_id:"a".repeat(32),
      commit_sha:"b".repeat(40),
      branch:"main",
      path:"exports/deploy-relay-agent-v2/2026-10/diagnostics/safe__diagnostics__"+"a".repeat(32)+".json",
      file_url:"https://github.com/TheDaimos/Project-Log-And-Export/blob/main/exports/deploy-relay-agent-v2/2026-10/diagnostics/safe__diagnostics__"+"a".repeat(32)+".json",
      pending_retried:true,
    };
  }};
  g2._render();
  assert.match(g2.shadowRoot.innerHTML,/G2 – Wiederholversand sicher prüfen/);
  assert.match(g2.shadowRoot.innerHTML,/G2-Test vorbereiten/);
  assert.match(g2.shadowRoot.innerHTML,/id="dra-g2-retry-test"\s+open/);
  await g2._deploymentLogsAction("g2_prepare");
  assert.equal(sent.length,0,"unconfirmed G2 action must not reach HA");
  g2._g2RetryTestConfirm=true;
  g2._render();
  assert.match(g2.shadowRoot.innerHTML,/Ja, lokal zurückstellen/);
  await g2._deploymentLogsAction("g2_prepare");
  assert.equal(sent.length,1);
  assert.equal(g2._centralExport.pending,true);
  assert.match(g2._deploymentLogsStatus,/nur lokal gesichert/);
  assert.match(g2.shadowRoot.innerHTML,/Gespeicherten Git-Export erneut senden/);
  assert.doesNotMatch(g2.shadowRoot.innerHTML,/id="dra-g2-retry-yes"/);
  // HA restart: transient source log cache gone, persisted queue still present.
  g2._deploymentLogs=[];
  g2._render();
  assert.match(g2.shadowRoot.innerHTML,
    /id="dra-logs-git"[^>]*>Gespeicherten Git-Export erneut senden/);
  assert.doesNotMatch(g2.shadowRoot.innerHTML,
    /id="dra-logs-git"[^>]*disabled/);
  await g2._deploymentLogsAction("git");
  assert.equal(sent.length,2);
  assert.equal(g2._centralExport.pending,false);
  assert.match(g2._deploymentLogsStatus,/Zuvor gesicherten Export erneut/);
  assert.match(g2._deploymentLogsStatus,/aktuelle Prüfprotokoll Export nach Git erneut wählen/);
  assert.doesNotMatch(g2.shadowRoot.innerHTML,/data-stage="2"/);
  console.log("DRA V2 G2 admin two-step local-only queue and explicit retry UI PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});

(async () => {
  const retry = new Panel();
  retry._sourceBusy = true;
  retry._sourceJobId = "d".repeat(32);
  retry._hass = {async callWS(_request) {throw new Error("temporary mobile connection drop");}};
  await retry._pollSourceJob();
  assert.equal(retry._sourceBusy,true);
  assert.equal(retry._sourceJobRetryMs,2400);
  assert.equal(callbacks.get(retry._sourceJobTimer).ms,2400);
  assert.match(retry._sourceMessage,/unabhängig/);
  clearTimeout(retry._sourceJobTimer);
  console.log("DRA V2 reconnect polls with backoff without cancelling server work PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});

(async () => {
  const grouped = new Panel();
  grouped._view="main";
  grouped._mainBatchMode=true;
  grouped._projects=[{name:"Alpha",repository:"TheDaimos/alpha",active:true,batch_preselect:true}];
  grouped._hass={ async callWS(request) {
    assert.equal(request.type,"deploy_relay_v2_dev/batch/preview");
    return {
      schema:"dra-v2-dev-batch-preview.v1",count:1,
      selected:[{repository:"TheDaimos/alpha"}],
      installation_enabled:false,sources_verified:false,
    };
  }};
  grouped._render();
  assert.match(grouped.shadowRoot.innerHTML,/1\/4 · Sammelinstallation prüfen und vorbereiten/);
  await grouped._previewMainBatch();
  assert.match(grouped.shadowRoot.innerHTML,/Gruppenauswahl bestätigt/);
  assert.match(grouped.shadowRoot.innerHTML,/data-stage="1"/);
  assert.doesNotMatch(grouped.shadowRoot.innerHTML,/data-stage="2"/);
  console.log("DRA V2 unverified group preview does not unlock write step PASS");
})().catch(error => {console.error(error);process.exitCode=1;});

(async () => {
  // Regression: a successful 4/4 MUST NOT trap the next teststand at 4/4.
  const p=new Panel();
  p._view="main";p._serverVersion="0.1.112";
  const project={repository:"TheDaimos/Test-Repo-DRA-V2",project_id:"test_repo_dra_v2",name:"Test",active:true};
  p._projects=[project];p._selectedMainRepo=project.repository;
  p._mainSourceRef="main";p._deploymentPreviewRef="main";p._sourceRepository=project.repository;
  const original="1".repeat(40), updated="2".repeat(40), operation="3".repeat(32);
  p._sourcePreview={repository:project.repository,source_ref:"main",source_commit:original,
    sources_verified:true,installation_enabled:false,add:[],change:["dra_v2_testprojekt/teststatus.json"],remove:[],unchanged_count:1};
  const oldJob={operation_id:operation,project_key:project.project_id,source_commit:original,
    status:"success",phase:"complete",restart_required:false};
  p._installJob=oldJob;p._installJobs=[oldJob];
  const sent=[];
  p._hass={async callWS(req){
    sent.push(req.type);
    if(req.type==="deploy_relay_v2_dev/projects/source_head") return {
      schema:"dra-v2-source-head.v1",repository:project.repository,ref:"main",commit:updated};
    if(req.type==="deploy_relay_v2_dev/deployment/status")return {
      schema:"dra-v2-install-status.v1",job:oldJob,jobs:[oldJob]};
    if(req.type==="deploy_relay_v2_dev/projects/source_job/start") return {
      schema:"dra-v2-source-preview-job.v1",operation_id:"4".repeat(32),installation_enabled:false};
    if(req.type==="deploy_relay_v2_dev/projects/source_job/status")return {
      schema:"dra-v2-source-preview-job-status.v1",installation_enabled:false,job:{
        schema:"dra-v2-source-preview-job.v1",operation_id:"4".repeat(32),
        repository:project.repository,ref:"main",status:"success",connection_test:false,
        installation_enabled:false,result:{repository:project.repository,source_ref:"main",
          source_commit:updated,sources_verified:true,installation_enabled:false,
          add:[],change:["dra_v2_testprojekt/teststatus.json"],remove:[],unchanged_count:1}}};
    throw Error("unexpected WS: "+req.type);
  }};
  p._render();
  assert.match(p.shadowRoot.innerHTML,/data-stage="4"/);
  assert.match(p.shadowRoot.innerHTML,/id="dra-next-deployment-preview"/);
  await p._refreshSourceHead();
  assert.equal(p._sourcePreview,null,"changed HEAD invalidates the old preview");
  assert.match(p._sourceHeadMessage,/Neuer Git-Commit erkannt/);
  assert.match(p.shadowRoot.innerHTML,/data-stage="1"/,"new commit reopens step 1");
  assert.doesNotMatch(p.shadowRoot.innerHTML,/id="dra-preview"[^>]*disabled/);
  await p._pollInstallation();
  assert.match(p.shadowRoot.innerHTML,/data-stage="1"/,
    "server polling the old success must not relock the stepper");
  await p._sourceCheck({dataset:{repo:project.repository}});
  assert.match(p.shadowRoot.innerHTML,/data-stage="2"/,
    "new commit source preview must permit step 2");
  assert.equal(p._sourcePreview.source_commit,updated);
  assert(!sent.includes("deploy_relay_v2_dev/deployment/start"),
    "refresh and preview must never trigger installation");
  console.log("DRA V2 completed cycle releases next Git HEAD preview without reinstall PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});

(async () => {
  // Teststand +1 writes only Git; it also releases an otherwise stuck 4/4.
  const p=new Panel();
  p._view="main";p._serverVersion="0.1.112";p._testVersionConfirm=true;
  const project={repository:"TheDaimos/Test-Repo-DRA-V2",project_id:"test_repo_dra_v2",
    name:"Test",active:true};
  p._projects=[project];p._selectedMainRepo=project.repository;
  p._installJob={operation_id:"a".repeat(32),project_key:project.project_id,
    source_commit:"b".repeat(40),status:"success",phase:"complete"};
  p._sourcePreview={repository:project.repository,source_commit:"b".repeat(40),
    sources_verified:true,installation_enabled:false};
  const sent=[];
  p._hass={async callWS(req){
    sent.push(req.type);assert.equal(req.confirm,true);
    return {schema:"dra-v2-test-version.v1",repository:project.repository,
      before:3,after:4,commit:"c".repeat(40)};
  }};
  p._render();
  assert.match(p.shadowRoot.innerHTML,/data-stage="4"/);
  await p._increaseTestVersion();
  assert.match(p.shadowRoot.innerHTML,/data-stage="1"/,
    "teststand +1 must release the old 4/4");
  assert.equal(p._sourcePreview,null);
  assert.deepEqual(sent,["deploy_relay_v2_dev/test/version/increment"]);
  console.log("DRA V2 teststand bump clears completed display without deployment PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});

(async () => {
  // A verified zero-change inventory is informational, not step-2 authorisation.
  const p = new Panel();
  p._view="main";p._serverVersion="0.1.112";
  const project={repository:"TheDaimos/Test-Repo-DRA-V2",project_id:"test_repo_dra_v2",name:"Test",active:true};
  p._projects=[project];p._selectedMainRepo=project.repository;
  p._sourceRepository=project.repository;
  p._mainSourceRef="main";p._deploymentPreviewRef="main";
  const oldJob={operation_id:"a".repeat(32),project_key:project.project_id,
    source_commit:"b".repeat(40),status:"success",phase:"complete"};
  p._installJob=oldJob;p._installJobs=[oldJob];
  p._sourcePreview={repository:project.repository,source_ref:"main",
    source_commit:"b".repeat(40),sources_verified:true,installation_enabled:false,
    add:[],change:[],remove:[],unchanged_count:2};
  const calls=[];
  p._hass={async callWS(req) {
    calls.push(req.type);
    if(req.type==="deploy_relay_v2_dev/deployment/status")return {
      schema:"dra-v2-install-status.v1",job:oldJob,jobs:[oldJob]};
    throw Error("No-change deployment may not prepare or start an installation");
  }};
  p._render();
  let html=p.shadowRoot.innerHTML;
  assert.match(html,/Aktuell · Kein Update verfügbar/);
  assert.match(html,/Bereits auf dem aktuellen Stand/);
  assert.match(html,/class="dra-deploy-action stage-1\s+up-to-date/);
  assert.match(html,/id="dra-preview"[^>]*disabled/);
  assert.match(html,/id="dra-up-to-date-recheck"/);
  assert.match(html,/Vorherige Installation · Historie/);
  assert.doesNotMatch(html,/Serverseitiger Auftrag: success/);
  assert.doesNotMatch(html,/2\/4 · Installation vorbereiten/);
  assert.doesNotMatch(html,/FREIGABEBEREIT/);
  assert.doesNotMatch(html,/id="dra-install-confirm"/);
  assert.match(html,/Schritt 2: Freigabe, nicht erforderlich/);
  await p._prepareInstallation(project);
  assert.deepEqual(calls,[],"no-change state must never call preparation endpoint");
  await p._pollInstallation();
  assert.match(p.shadowRoot.innerHTML,/Aktuell · Kein Update verfügbar/,
    "old successful server receipt must not override no-change state");
  p._sourcePreview={...p._sourcePreview,source_commit:"c".repeat(40),
    change:["dra_v2_testprojekt/teststatus.json"],unchanged_count:1};
  p._releaseCompletedDeployment(project);
  p._render();
  assert.match(p.shadowRoot.innerHTML,/data-stage="2"/);
  assert.match(p.shadowRoot.innerHTML,/2\/4 · Installation vorbereiten/);
  assert.doesNotMatch(p.shadowRoot.innerHTML,/class="dra-deploy-action stage-2\s+up-to-date/);
  console.log("DRA V2 no-op preview gives neutral current state and never unlocks install PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});

(async () => {
  // Post-install lifecycle comes from the verified HA server receipt, not
  // from the repository name or an arbitrary UI preview.
  const project={repository:"TheDaimos/gewitterradar",project_id:"gewitterradar",name:"Gewitterradar",active:true};
  const createPanel=(flags) => {
    const p=new Panel();
    p._view="main";p._serverVersion="0.1.112";
    p._projects=[project];p._selectedMainRepo=project.repository;
    const job={operation_id:"7".repeat(32),project_key:project.project_id,
      source_commit:"8".repeat(40),status:"success",phase:"complete",...flags};
    p._installJob=job;p._installJobs=[job];
    return p;
  };
  const frontend=createPanel({restart_required:false,frontend_reload_possible:true});
  frontend._render();
  assert.match(frontend.shadowRoot.innerHTML,/id="dra-frontend-refresh"/);
  assert.doesNotMatch(frontend.shadowRoot.innerHTML,/id="dra-ha-restart-open"/);
  let reloads=0;
  mockWindow.location.reload=()=>{reloads++};
  frontend._refreshFrontendAfterInstallation();
  assert.equal(reloads,1);
  frontend._installJob.restart_required=true;
  frontend._refreshFrontendAfterInstallation();
  assert.equal(reloads,1,"backend changes must never be treated as frontend-only");

  const restart=createPanel({restart_required:true,frontend_reload_possible:false});
  const req=[];
  restart._hass={async callWS(payload) {
    req.push(payload);
    assert.equal(payload.type,"deploy_relay_v2_dev/deployment/restart");
    assert.equal(payload.confirm,true);
    return {schema:"dra-v2-restart-request.v1",
      operation_id:payload.operation_id,restart_requested:true};
  }};
  restart._render();
  assert.match(restart.shadowRoot.innerHTML,/id="dra-ha-restart-open"/);
  assert.doesNotMatch(restart.shadowRoot.innerHTML,/id="dra-frontend-refresh"/);
  assert.doesNotMatch(restart.shadowRoot.innerHTML,/id="dra-ha-restart-confirm"/);
  await restart._requestHomeAssistantRestart();
  assert.equal(req.length,0,"a single click may only open confirmation, never restart");
  restart._restartDialogOpen=true;
  restart._render();
  assert.match(restart.shadowRoot.innerHTML,/Home Assistant wirklich neu starten/);
  assert.match(restart.shadowRoot.innerHTML,/id="dra-ha-restart-cancel"/);
  assert.match(restart.shadowRoot.innerHTML,/id="dra-ha-restart-confirm"/);
  await restart._requestHomeAssistantRestart();
  assert.equal(req.length,1);
  assert.equal(req[0].operation_id,"7".repeat(32));
  assert.match(restart._restartMessage,/Neustart angefordert/);
  await restart._requestHomeAssistantRestart();
  assert.equal(req.length,1,"no duplicate restart after confirmation");
  delete mockWindow.location.reload;
  console.log("DRA V2 frontend refresh vs admin confirmed restart lifecycle PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});

(async () => {
  // Git ref lookup, diagnostic messages and re-renders must NEVER expand the
  // advanced source chooser. Only the user's own disclosure toggle may do so.
  const p = new Panel();
  const repository = "TheDaimos/gewitterradar";
  p._view = "main";
  p._serverVersion = "0.1.112";
  p._projects = [{repository, project_id:"gewitterradar", name:"Gewitterradar", active:true}];
  p._selectedMainRepo = repository;
  p._sourceChoices = {repository, choices:[], recommended:null};
  p._sourceChoicesMessage = "Git-Zweige und Tags geladen.";
  p._sourceChoicesBusy = true;
  p._render();
  assert.match(p.shadowRoot.innerHTML,/id="dra-source-advanced" >/);
  assert.doesNotMatch(p.shadowRoot.innerHTML,/id="dra-source-advanced" open>/);
  p._sourceChoicesBusy = false;
  p._render();
  assert.doesNotMatch(p.shadowRoot.innerHTML,/id="dra-source-advanced" open>/);
  p._sourceAdvancedOpen = true;
  p._render();
  assert.match(p.shadowRoot.innerHTML,/id="dra-source-advanced" open>/);
  p._sourceChoicesMessage = "Prüfung abgeschlossen.";
  p._render();
  assert.match(p.shadowRoot.innerHTML,/id="dra-source-advanced" open>/);
  p._sourceAdvancedOpen = false;
  p._render();
  assert.doesNotMatch(p.shadowRoot.innerHTML,/id="dra-source-advanced" open>/);
  console.log("DRA V2 advanced source chooser respects explicit user disclosure across refreshes PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});

(async () => {
  // Device B starts with no browser-held source report but a server-restored
  // V1 plan. This must show stage 2 and permit explicit, HA-authorized control.
  const p=new Panel();
  const repository="TheDaimos/example";
  p._serverVersion="0.1.112";
  p._selectedMainRepo=repository;
  p._projects=[{repository,project_id:"example",name:"Example",active:true}];
  p._sourceRepository=repository;
  p._mainSourceRef="deploy/dev";
  p._installPreparation={
    schema:"dra-v2-install-preparation.v1",repository,
    source_ref:"deploy/dev",source_commit:"a".repeat(40),
    challenge:"b".repeat(32),confirmation_required:true,
    add:1,change:0,remove:0,
  };
  p._controllerStatus={schema:"dra-v2-controller.v1",controller:true,occupied:false};
  // Android may hold a stale independent read-only preview, which must not
  // eclipse a valid HA-owned exact-commit installation plan.
  p._sourcePreview={repository,source_ref:"deploy/dev",
    source_commit:"d".repeat(40),sources_verified:true,
    installation_enabled:false,add:[],change:[],remove:[],
    unchanged_count:7};
  const calls=[];
  p._hass={async callWS(req) {
    calls.push(req.type);
    if(req.type==="deploy_relay_v2_dev/deployment/control") return {
      schema:"dra-v2-controller.v1",controller:true,occupied:false,
    };
    if(req.type==="deploy_relay_v2_dev/deployment/start") {
      assert.equal(req.challenge,"b".repeat(32));
      assert.equal(req.commit,"a".repeat(40));
      assert.equal(req.confirm,true);
      return {schema:"dra-v2-install-start.v1",job:{
        operation_id:"c".repeat(32),project_key:"example",status:"running",
      }};
    }
    if(req.type==="deploy_relay_v2_dev/deployment/status") return {
      schema:"dra-v2-install-status.v1",jobs:[],job:null,
    };
    throw Error("unexpected route "+req.type);
  }};
  p._render();
  assert.match(p.shadowRoot.innerHTML,/id="dra-install-confirm"/);
  assert.match(p.shadowRoot.innerHTML,/data-stage="2"/);
  await p._confirmInstallation();
  assert.deepEqual(calls,[
    "deploy_relay_v2_dev/deployment/control",
    "deploy_relay_v2_dev/deployment/start",
    "deploy_relay_v2_dev/deployment/status",
    "deploy_relay_v2_dev/batch/status",
  ]);
  console.log("DRA V2 second-device handoff resumes HA plan without local source preview PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});

(async () => {
  // An accepted HA transaction can lose its WebSocket receipt. Never blindly
  // resubmit the same installation: recover the newly admitted server job.
  const panel=new Panel();
  const repo="TheDaimos/example",commit="a".repeat(40),jobid="d".repeat(32);
  panel._serverVersion="0.1.112";
  panel._selectedMainRepo=repo;
  panel._projects=[{repository:repo,project_id:"example",active:true}];
  panel._sourceRepository=repo;
  panel._mainSourceRef="deploy/dev";
  panel._installPreparation={schema:"dra-v2-install-preparation.v1",
    repository:repo,source_ref:"deploy/dev",source_commit:commit,
    challenge:"b".repeat(32),confirmation_required:true,add:1,change:0,remove:0};
  const calls=[];
  panel._hass={async callWS(req) {
    calls.push(req.type);
    if(req.type==="deploy_relay_v2_dev/deployment/control")
      return {schema:"dra-v2-controller.v1",controller:true,occupied:false};
    if(req.type==="deploy_relay_v2_dev/deployment/start")
      throw Error("simulated lost reply after server acceptance");
    if(req.type==="deploy_relay_v2_dev/deployment/status")
      return {schema:"dra-v2-install-status.v1",jobs:[{
        operation_id:jobid,project_key:"example",source_commit:commit,
        status:"running",phase:"staging",
      }]};
    throw Error("unexpected request "+req.type);
  }};
  await panel._confirmInstallation();
  assert.deepEqual(calls,["deploy_relay_v2_dev/deployment/control",
    "deploy_relay_v2_dev/deployment/start",
    "deploy_relay_v2_dev/deployment/status"]);
  assert.equal(panel._installJobId,jobid);
  assert.equal(panel._installStartUncertain,null);
  assert.equal(panel._installPreparation,null);
  console.log("DRA V2 ambiguous receipt reconciles HA job without duplicate installation PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});

(async () => {
  // Without a verifiable server status, fail closed and block a second start.
  const panel=new Panel(),repo="TheDaimos/example",commit="a".repeat(40);
  panel._serverVersion="0.1.112";
  panel._selectedMainRepo=repo;
  panel._projects=[{repository:repo,project_id:"example",active:true}];
  panel._sourceRepository=repo;
  panel._mainSourceRef="deploy/dev";
  panel._installPreparation={schema:"dra-v2-install-preparation.v1",
    repository:repo,source_ref:"deploy/dev",source_commit:commit,
    challenge:"b".repeat(32),confirmation_required:true,add:1,change:0,remove:0};
  const calls=[];
  panel._hass={async callWS(req) {
    calls.push(req.type);
    if(req.type==="deploy_relay_v2_dev/deployment/control")
      return {schema:"dra-v2-controller.v1",controller:true,occupied:false};
    throw Error("simulated unavailable install receipt and job status");
  }};
  await panel._confirmInstallation();
  assert.equal(panel._installJob,null);
  assert.equal(panel._installPreparation.challenge,"b".repeat(32));
  assert.ok(panel._installStartUncertain);
  panel._render();
  assert.match(panel.shadowRoot.innerHTML,/id="dra-install-confirm"[^>]*disabled/);
  await panel._confirmInstallation();
  assert.deepEqual(calls,["deploy_relay_v2_dev/deployment/control",
    "deploy_relay_v2_dev/deployment/start",
    "deploy_relay_v2_dev/deployment/status"]);
  console.log("DRA V2 unconfirmed installation fails closed without second write PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});

(async () => {
  // An observer may inspect the exact server-held plan but cannot click
  // installation until explicit active-operator takeover succeeds.
  const panel=new Panel(),repo="TheDaimos/example";
  panel._serverVersion="0.1.112";
  panel._selectedMainRepo=repo;
  panel._projects=[{repository:repo,project_id:"example",active:true}];
  panel._sourceRepository=repo;
  panel._mainSourceRef="deploy/dev";
  panel._installPreparation={schema:"dra-v2-install-preparation.v1",
    repository:repo,source_ref:"deploy/dev",source_commit:"a".repeat(40),
    challenge:"b".repeat(32),confirmation_required:true,add:1,change:0,remove:0};
  panel._controllerStatus={schema:"dra-v2-controller.v1",controller:false,occupied:true};
  panel._render();
  assert.match(panel.shadowRoot.innerHTML,/id="dra-install-confirm"[^>]*disabled/);
  panel._controllerStatus={schema:"dra-v2-controller.v1",controller:true,occupied:false};
  panel._render();
  assert.match(panel.shadowRoot.innerHTML,/id="dra-install-confirm"/);
  assert.doesNotMatch(panel.shadowRoot.innerHTML,/id="dra-install-confirm"[^>]*disabled/);
  console.log("DRA V2 observer sees plan but cannot approve before session takeover PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});

(async () => {
  // iPad joins with no selected project and no /test/state result while
  // HA is already running a write job started from Android.
  const panel=new Panel();
  const active={
    operation_id:"d".repeat(32),project_key:"gewitterradar",
    status:"running",phase:"backup",progress_exact:true,progress_percent:35,
  };
  let available=true, job=active, calls=[];
  panel._hass={async callWS(request) {
    calls.push(request.type);
    assert.equal(request.type,"deploy_relay_v2_dev/deployment/status");
    if (!available) throw Error("simulated websocket dropout");
    return {schema:"dra-v2-install-status.v1",jobs:[job],job,
      project_names:{gewitterradar:"Gewitterradar"}};
  }};
  assert.equal(panel._serverVersion,null);
  assert.equal(panel._selectedMainRepo,null);
  await panel._pollInstallation();
  panel._render();
  assert.match(panel.shadowRoot.innerHTML,/Installation auf Home Assistant läuft/);
  assert.match(panel.shadowRoot.innerHTML,/Gewitterradar/);
  assert.match(panel.shadowRoot.innerHTML,/Sicherung · 35 %/);
  assert.match(panel.shadowRoot.innerHTML,/Auftrag d{12}/);
  assert.equal(panel._selectedMainRepo,null);
  available=false;
  await panel._pollInstallation();
  panel._render();
  assert.match(panel.shadowRoot.innerHTML,/Verbindung unterbrochen/);
  assert.match(panel.shadowRoot.innerHTML,/Letzter bekannter Stand · nicht aktuell/);
  available=true;
  job={...active,status:"success",phase:"complete",
    progress_percent:100,progress_exact:true};
  await panel._pollInstallation();
  panel._render();
  assert.match(panel.shadowRoot.innerHTML,/Installationsauftrag abgeschlossen/);
  assert.match(panel.shadowRoot.innerHTML,/Erfolgreich abgeschlossen · 100 %/);
  assert.deepEqual(calls,[
    "deploy_relay_v2_dev/deployment/status","deploy_relay_v2_dev/batch/status",
    "deploy_relay_v2_dev/deployment/status",
    "deploy_relay_v2_dev/deployment/status","deploy_relay_v2_dev/batch/status",
  ]);
  console.log("DRA V2 project-free iPad observer, staleness, and confirmed completion PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});

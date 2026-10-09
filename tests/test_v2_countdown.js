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
  return {
    remaining,
    innerHTML: "",
    querySelector(selector) {
      return selector === "#remaining" ? remaining : null;
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
const ctx = {
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
assert(panel.shadowRoot.innerHTML.includes("JSON-Datei herunterladen"));
assert(panel.shadowRoot.innerHTML.includes("Es gibt ausdrücklich kein vorbelegtes Repository."));
panel._downloadJSON().then(() => {
  assert.equal(downloads.length, 1);
  assert.equal(downloads[0].filename, filename);
  assert.equal(downloads[0].url, "blob:local-dra-v2");
  assert.equal(urls.length, 1);
  assert.equal(panel._downloadStatus, "JSON-Download gestartet: " + filename);
  assert.equal(panel._centralExport.repository, null);
  console.log("DRA V2 JSON download without GitHub PASS");
}).catch(error => {
  console.error(error);
  process.exitCode = 1;
});


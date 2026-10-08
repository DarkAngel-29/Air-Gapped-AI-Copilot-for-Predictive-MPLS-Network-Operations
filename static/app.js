/**
 * MPLS Network Simulator - Client Controller & Real-Time Telemetry Pipeline
 */

// Application State
const state = {
  isRunning: true,
  speed: 1.0,
  routers: [],
  activeFaults: {},
  elapsedTicks: 0,
  totalRecordsWritten: 0,
  logPath: 'logs/telemetry.jsonl',
  isLogPaused: false,
  isBackendConnected: false,
  pollIntervalMs: 1000
};

// Color palettes for router cards
const CARD_PALETTES = [
  { class: 'clay-card-lavender', accent: '#6d28d9', iconBg: '#cbbeff', iconColor: '#271c48' },
  { class: 'clay-card-mint', accent: '#047857', iconBg: '#a7f3d0', iconColor: '#065f46' },
  { class: 'clay-card-peach', accent: '#c2410c', iconBg: '#fed7aa', iconColor: '#9a3412' },
  { class: 'clay-card', accent: '#4f46e5', iconBg: '#e0e7ff', iconColor: '#3730a3' }
];

// Fallback embedded simulation if running without server
class LocalFallbackEngine {
  constructor() {
    this.routers = [
      { id: 'R1', name: 'Ingress Router 1', status: 'ACTIVE', baseLatency: 12.0, baseLoss: 0.1, baseJitter: 1.8, baseBw: 42, baseCpu: 31, baseMem: 38 },
      { id: 'R2', name: 'Core Router 2', status: 'ACTIVE', baseLatency: 14.5, baseLoss: 0.1, baseJitter: 2.2, baseBw: 48, baseCpu: 35, baseMem: 42 },
      { id: 'R3', name: 'Core Router 3', status: 'ACTIVE', baseLatency: 15.0, baseLoss: 0.1, baseJitter: 2.0, baseBw: 45, baseCpu: 33, baseMem: 40 },
      { id: 'R4', name: 'Egress Router 4', status: 'ACTIVE', baseLatency: 13.2, baseLoss: 0.05, baseJitter: 1.9, baseBw: 39, baseCpu: 28, baseMem: 36 }
    ];
    this.activeFaults = {};
    this.telemetryRecords = [];
    this.totalRecords = 0;
  }

  addRouter(id, name) {
    const rId = id.toUpperCase();
    if (!this.routers.find(r => r.id === rId)) {
      this.routers.push({
        id: rId,
        name: name || `Router ${rId}`,
        status: 'ACTIVE',
        baseLatency: 12 + Math.random() * 5,
        baseLoss: 0.1,
        baseJitter: 2.0,
        baseBw: 35 + Math.random() * 20,
        baseCpu: 25 + Math.random() * 15,
        baseMem: 35 + Math.random() * 15
      });
    }
  }

  removeRouter(id) {
    this.routers = this.routers.filter(r => r.id !== id);
    delete this.activeFaults[id];
  }

  injectFault(routerId, faultType, duration, intensity) {
    const fault = {
      target_router_id: routerId,
      fault_type: faultType,
      duration_seconds: duration,
      remaining_seconds: duration,
      intensity: intensity
    };
    this.activeFaults[routerId] = fault;
    const r = this.routers.find(x => x.id === routerId);
    if (r) r.status = 'FAULTED';
    return fault;
  }

  clearFaults(routerId) {
    if (routerId) {
      delete this.activeFaults[routerId];
      const r = this.routers.find(x => x.id === routerId);
      if (r) r.status = 'ACTIVE';
    } else {
      this.activeFaults = {};
      this.routers.forEach(r => r.status = 'ACTIVE');
    }
  }

  tick(dt) {
    // Decrement faults
    for (const [rId, fault] of Object.entries(this.activeFaults)) {
      fault.remaining_seconds -= dt;
      if (fault.remaining_seconds <= 0) {
        delete this.activeFaults[rId];
        const r = this.routers.find(x => x.id === rId);
        if (r) r.status = 'ACTIVE';
      }
    }

    const records = [];
    const timestamp = new Date().toISOString();

    for (const r of this.routers) {
      const fault = this.activeFaults[r.id];
      let lat = r.baseLatency + (Math.random() * 2 - 1);
      let loss = r.baseLoss + Math.random() * 0.05;
      let jit = r.baseJitter + (Math.random() * 0.4 - 0.2);
      let bw = Math.min(85, Math.max(15, r.baseBw + (Math.random() * 6 - 3)));
      let cpu = Math.min(80, Math.max(15, r.baseCpu + (Math.random() * 5 - 2.5)));
      let mem = Math.min(75, Math.max(20, r.baseMem + (Math.random() * 2 - 1)));
      let status = 'ACTIVE';
      let faultName = null;

      if (fault) {
        status = 'FAULTED';
        faultName = fault.fault_type;
        const factor = fault.intensity === 'Low' ? 0.4 : (fault.intensity === 'Medium' ? 0.7 : 1.0);

        if (fault.fault_type === 'CPU Overload') {
          cpu = Math.min(99.4, 91.0 + Math.random() * 8 * factor);
          lat += 70 * factor;
          jit += 15 * factor;
          loss += 1.8 * factor;
        } else if (fault.fault_type === 'Latency Spike') {
          lat += 180 * factor;
          jit += 25 * factor;
        } else if (fault.fault_type === 'Packet Loss Spike') {
          loss += 12 * factor;
          lat += 25 * factor;
        } else if (fault.fault_type === 'Bandwidth Congestion') {
          bw = Math.min(98.5, 88 + Math.random() * 10 * factor);
          lat += 90 * factor;
          jit += 20 * factor;
          loss += 2.5 * factor;
        } else if (fault.fault_type === 'High Jitter') {
          jit += 40 * factor;
          lat += 40 * factor;
        } else if (fault.fault_type === 'Memory Overload') {
          mem = Math.min(98.5, 90 + Math.random() * 8 * factor);
          cpu += 20 * factor;
        } else if (fault.fault_type === 'Link Failure') {
          loss = 100.0;
          lat = 999.0;
          bw = 0.0;
          jit = 0.0;
        }
      }

      const rec = {
        timestamp,
        router_id: r.id,
        latency: Math.round(lat * 100) / 100,
        packet_loss: Math.round(loss * 100) / 100,
        jitter: Math.round(jit * 100) / 100,
        bandwidth_usage: Math.round(bw * 10) / 10,
        cpu_usage: Math.round(cpu * 10) / 10,
        memory_usage: Math.round(mem * 10) / 10,
        status,
        active_fault: faultName
      };
      r.last_telemetry = rec;
      records.push(rec);
      this.totalRecords++;
    }
    return records;
  }
}

const fallbackEngine = new LocalFallbackEngine();

// DOM Elements
const routerCardsGrid = document.getElementById('routerCardsGrid');
const faultTargetSelect = document.getElementById('faultTargetSelect');
const faultTypeSelect = document.getElementById('faultTypeSelect');
const faultDurationSelect = document.getElementById('faultDurationSelect');
const faultIntensitySelect = document.getElementById('faultIntensitySelect');
const injectFaultBtn = document.getElementById('injectFaultBtn');
const clearFaultsBtn = document.getElementById('clearFaultsBtn');
const activeFaultBannerContainer = document.getElementById('activeFaultBannerContainer');
const faultBannerTitle = document.getElementById('faultBannerTitle');
const faultBannerSubtitle = document.getElementById('faultBannerSubtitle');
const faultCountdown = document.getElementById('faultCountdown');
const dismissFaultBannerBtn = document.getElementById('dismissFaultBannerBtn');

const simStatusPill = document.getElementById('simStatusPill');
const simStatusPing = document.getElementById('simStatusPing');
const simStatusDot = document.getElementById('simStatusDot');
const simStatusText = document.getElementById('simStatusText');
const activeNodesBadge = document.getElementById('activeNodesBadge');
const activeFaultsBadge = document.getElementById('activeFaultsBadge');
const logPathBadge = document.getElementById('logPathBadge');
const recordCountBadge = document.getElementById('recordCountBadge');
const elapsedTicksEl = document.getElementById('elapsedTicksEl');
const totalRecordsEl = document.getElementById('totalRecordsEl');

const btnSimStart = document.getElementById('btnSimStart');
const btnSimPause = document.getElementById('btnSimPause');
const btnSimReset = document.getElementById('btnSimReset');
const speedButtons = document.querySelectorAll('.speed-toggle');

const telemetryTerminal = document.getElementById('telemetryTerminal');
const btnPauseLogs = document.getElementById('btnPauseLogs');
const btnCopyLogs = document.getElementById('btnCopyLogs');
const btnClearLogs = document.getElementById('btnClearLogs');

const addRouterModal = document.getElementById('addRouterModal');
const openAddRouterBtn = document.getElementById('openAddRouterBtn');
const headerAddRouterBtn = document.getElementById('headerAddRouterBtn');
const closeModalBtn = document.getElementById('closeModalBtn');
const cancelAddRouterBtn = document.getElementById('cancelAddRouterBtn');
const addRouterForm = document.getElementById('addRouterForm');
const newRouterId = document.getElementById('newRouterId');
const newRouterName = document.getElementById('newRouterName');

// ---------------- Backend Sync & Polling ----------------
async function checkBackend() {
  try {
    const res = await fetch('/api/status', { method: 'GET' });
    if (res.ok) {
      state.isBackendConnected = true;
      return true;
    }
  } catch (err) {
    state.isBackendConnected = false;
  }
  return false;
}

async function fetchLiveTelemetry() {
  if (state.isBackendConnected) {
    try {
      const res = await fetch('/api/telemetry/live');
      if (res.ok) {
        const data = await res.json();
        state.isRunning = data.is_running;
        state.speed = data.speed;
        state.routers = data.routers || [];
        state.totalRecordsWritten = data.storage?.total_records || 0;
        state.logPath = data.storage?.log_path ? 'logs/telemetry.jsonl' : state.logPath;

        // Render logs from server
        if (!state.isLogPaused && data.recent_logs && data.recent_logs.length > 0) {
          appendTelemetryLogs(data.recent_logs.slice(-data.routers.length));
        }

        renderUI();
        return;
      }
    } catch (err) {
      state.isBackendConnected = false;
    }
  }

  // Fallback engine if backend is not responding
  if (state.isRunning) {
    state.elapsedTicks++;
    const records = fallbackEngine.tick(1.0 * state.speed);
    state.routers = fallbackEngine.routers.map(r => ({
      id: r.id,
      name: r.name,
      status: r.status,
      has_fault: !!fallbackEngine.activeFaults[r.id],
      active_fault: fallbackEngine.activeFaults[r.id] || null,
      telemetry: r.last_telemetry || null
    }));
    state.totalRecordsWritten = fallbackEngine.totalRecords;
    if (!state.isLogPaused) {
      appendTelemetryLogs(records);
    }
  }
  renderUI();
}

// ---------------- UI Rendering ----------------
function renderUI() {
  // 1. Status Pill
  if (state.isRunning) {
    simStatusPill.className = "clay-pill-btn bg-[#d8f8e8] px-3.5 py-1 flex items-center gap-2 text-[#0f5b3a] font-bold text-xs uppercase tracking-wider";
    simStatusPing.className = "animate-ping absolute inline-flex h-full w-full rounded-full bg-[#10b981] opacity-75";
    simStatusDot.className = "relative inline-flex rounded-full h-2.5 w-2.5 bg-[#059669]";
    simStatusText.textContent = "SIMULATING";
  } else {
    simStatusPill.className = "clay-pill-btn bg-[#fef3c7] px-3.5 py-1 flex items-center gap-2 text-[#92400e] font-bold text-xs uppercase tracking-wider";
    simStatusPing.className = "hidden";
    simStatusDot.className = "relative inline-flex rounded-full h-2.5 w-2.5 bg-[#d97706]";
    simStatusText.textContent = "PAUSED";
  }

  // 2. Counts & badges
  const faultedRouters = state.routers.filter(r => r.status === 'FAULTED');
  activeNodesBadge.textContent = `${state.routers.length} Nodes Active`;
  activeFaultsBadge.textContent = `${faultedRouters.length} Fault${faultedRouters.length === 1 ? '' : 's'}`;
  activeFaultsBadge.className = faultedRouters.length > 0 ? "text-red-700 font-bold" : "text-[#059669] font-bold";

  recordCountBadge.textContent = `${state.totalRecordsWritten.toLocaleString()} records`;
  totalRecordsEl.textContent = state.totalRecordsWritten.toLocaleString();
  elapsedTicksEl.textContent = state.elapsedTicks.toLocaleString();

  // 3. Active Fault Banner
  if (faultedRouters.length > 0) {
    const fNode = faultedRouters[0];
    const fInfo = fNode.active_fault;
    const remaining = fInfo ? Math.max(0, Math.ceil(fInfo.remaining_seconds)) : 0;
    const faultTypeName = fInfo ? fInfo.fault_type : 'Disturbance';
    const intensity = fInfo ? fInfo.intensity : 'High';

    activeFaultBannerContainer.classList.remove('hidden');
    faultBannerTitle.textContent = `FAULT ACTIVE: ${fNode.id} experiencing ${faultTypeName} (${intensity})`;
    faultBannerSubtitle.innerHTML = `Telemetry perturbed realistically. Returning toward baseline in: <span id="faultCountdown" class="font-extrabold text-red-950">${remaining}s</span>`;
  } else {
    activeFaultBannerContainer.classList.add('hidden');
  }

  // 4. Update Target Router Dropdown
  const prevSelected = faultTargetSelect.value;
  faultTargetSelect.innerHTML = '';
  state.routers.forEach(r => {
    const opt = document.createElement('option');
    opt.value = r.id;
    opt.textContent = `${r.id} - ${r.name}${r.status === 'FAULTED' ? ' [FAULTED]' : ''}`;
    faultTargetSelect.appendChild(opt);
  });
  if (prevSelected && state.routers.find(r => r.id === prevSelected)) {
    faultTargetSelect.value = prevSelected;
  }

  // 5. Render Router Cards
  renderRouterCards();
}

function renderRouterCards() {
  routerCardsGrid.innerHTML = '';

  state.routers.forEach((router, index) => {
    const isFaulted = router.status === 'FAULTED';
    const palette = isFaulted 
      ? { class: 'clay-card-alert', accent: '#b91c1c', iconBg: '#fecaca', iconColor: '#991b1b' }
      : CARD_PALETTES[index % CARD_PALETTES.length];

    const telem = router.telemetry || {
      latency: 14.0,
      packet_loss: 0.1,
      jitter: 2.0,
      bandwidth_usage: 40.0,
      cpu_usage: 30.0,
      memory_usage: 38.0
    };

    const card = document.createElement('div');
    card.className = "relative group";
    card.dataset.nodeId = router.id;

    card.innerHTML = `
      <div class="${palette.class} p-5 transition-transform duration-200 cursor-pointer hover:-translate-y-1.5 relative">
        <!-- Card Header: ID and Status Pill -->
        <div class="flex items-center justify-between pb-2 mb-3 border-b ${isFaulted ? 'border-red-300' : 'border-purple-200/60'}">
          <span class="font-mono text-xs font-extrabold uppercase" style="color: ${palette.accent}">
            NODE ${router.id}
          </span>
          <span class="clay-pill-btn ${isFaulted ? 'bg-[#fee2e2] text-[#991b1b]' : 'bg-[#def7ec] text-[#03543f]'} text-[10px] font-extrabold px-2.5 py-0.5 flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full ${isFaulted ? 'bg-red-600 animate-ping' : 'bg-[#10b981]'}"></span>
            ${router.status}
          </span>
        </div>

        <!-- Center: Router Icon and Name -->
        <div class="flex items-center gap-3.5 my-2">
          <div class="w-12 h-12 rounded-2xl flex items-center justify-center shadow-md shrink-0" style="background-color: ${palette.iconBg}; color: ${palette.iconColor}">
            <span class="material-symbols-outlined text-[26px]">router</span>
          </div>
          <div class="min-w-0 flex-1">
            <h3 class="text-sm sm:text-base font-extrabold text-clay-text truncate" title="${router.name}">
              ${router.name}
            </h3>
            <div class="text-xs font-mono font-bold text-clay-muted flex items-center gap-1">
              <span style="color: ${palette.accent}">${router.id}</span>
              <span>•</span>
              <span class="text-[11px]">${isFaulted ? 'Under Perturbation' : 'Nominal Core'}</span>
            </div>
          </div>
        </div>

        <!-- Mini Status Row -->
        <div class="clay-inset bg-white/70 px-3 py-2 mt-4 flex justify-between items-center text-[11px] font-mono font-bold text-clay-muted">
          <span>Latency: <strong class="${isFaulted ? 'text-red-700' : 'text-clay-text'}">${telem.latency}ms</strong></span>
          <span class="${isFaulted ? 'text-red-700 font-extrabold' : 'text-[#059669]'}">${telem.packet_loss}% loss</span>
        </div>
      </div>

      <!-- Telemetry Hover Popover Probe -->
      <div class="absolute left-0 top-full mt-2 z-40 w-72 p-4 clay-card bg-white/95 backdrop-blur-md opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto transition-all duration-200 shadow-2xl ${isFaulted ? 'border-2 border-red-300' : ''}">
        <div class="flex items-center justify-between pb-2 mb-2 border-b ${isFaulted ? 'border-red-200' : 'border-purple-200'}">
          <span class="font-mono text-xs font-extrabold" style="color: ${palette.accent}">
            TELEMETRY: ${router.id}
          </span>
          <span class="text-[10px] font-bold ${isFaulted ? 'text-red-700 bg-red-100' : 'text-emerald-700 bg-emerald-100'} px-2 py-0.5 rounded-full">
            ${isFaulted ? 'FAULT PERTURBATION' : 'NOMINAL BASELINE'}
          </span>
        </div>

        <div class="space-y-1.5 font-mono text-xs text-clay-muted">
          <div class="flex justify-between">
            <span>Latency:</span>
            <span class="font-bold ${isFaulted && telem.latency > 50 ? 'text-red-600' : 'text-clay-text'}">${telem.latency} ms</span>
          </div>

          <div class="flex justify-between">
            <span>Packet Loss:</span>
            <span class="font-bold ${isFaulted && telem.packet_loss > 1 ? 'text-red-600' : 'text-emerald-700'}">${telem.packet_loss} %</span>
          </div>

          <div class="flex justify-between">
            <span>Jitter:</span>
            <span class="font-bold ${isFaulted && telem.jitter > 10 ? 'text-red-600' : 'text-clay-text'}">${telem.jitter} ms</span>
          </div>

          <div class="flex justify-between items-center">
            <span>Bandwidth:</span>
            <div class="flex items-center gap-1.5">
              <span class="font-bold ${telem.bandwidth_usage > 80 ? 'text-amber-600' : 'text-clay-text'}">${telem.bandwidth_usage}%</span>
              <div class="w-14 h-2 rounded-full bg-purple-100 overflow-hidden">
                <div class="h-full ${telem.bandwidth_usage > 80 ? 'bg-amber-500' : 'bg-purple-500'} rounded-full transition-all duration-300" style="width: ${Math.min(100, telem.bandwidth_usage)}%;"></div>
              </div>
            </div>
          </div>

          <div class="flex justify-between items-center">
            <span>CPU Usage:</span>
            <div class="flex items-center gap-1.5">
              <span class="font-bold ${telem.cpu_usage > 85 ? 'text-red-600' : 'text-clay-text'}">${telem.cpu_usage}%</span>
              <div class="w-14 h-2 rounded-full bg-emerald-100 overflow-hidden">
                <div class="h-full ${telem.cpu_usage > 85 ? 'bg-red-500' : 'bg-emerald-500'} rounded-full transition-all duration-300" style="width: ${Math.min(100, telem.cpu_usage)}%;"></div>
              </div>
            </div>
          </div>

          <div class="flex justify-between items-center">
            <span>Memory:</span>
            <div class="flex items-center gap-1.5">
              <span class="font-bold ${telem.memory_usage > 85 ? 'text-red-600' : 'text-clay-text'}">${telem.memory_usage}%</span>
              <div class="w-14 h-2 rounded-full bg-blue-100 overflow-hidden">
                <div class="h-full ${telem.memory_usage > 85 ? 'bg-red-500' : 'bg-blue-500'} rounded-full transition-all duration-300" style="width: ${Math.min(100, telem.memory_usage)}%;"></div>
              </div>
            </div>
          </div>

          <div class="pt-1.5 border-t border-purple-100 flex justify-between text-[10px] text-clay-muted/80">
            <span>Generated Live</span>
            <span>Machine Persisted</span>
          </div>
        </div>
      </div>
    `;

    routerCardsGrid.appendChild(card);
  });

  // Append "+ Add Router" tactile action card at end of grid
  const addCard = document.createElement('button');
  addCard.className = "clay-card flex flex-col items-center justify-center min-h-[175px] p-5 text-clay-muted hover:text-clay-text hover:-translate-y-1.5 transition-all duration-200 w-full group";
  addCard.type = "button";
  addCard.innerHTML = `
    <div class="w-12 h-12 rounded-2xl bg-white flex items-center justify-center text-clay-text group-hover:bg-[#cbbeff] shadow-md mb-2.5 transition-all">
      <span class="material-symbols-outlined text-[26px]">add</span>
    </div>
    <span class="text-sm font-extrabold text-clay-text">Add Router</span>
    <span class="text-[11px] font-mono font-medium text-clay-muted/80 text-center mt-0.5">Provision node into mesh</span>
  `;
  addCard.addEventListener('click', openModal);
  routerCardsGrid.appendChild(addCard);
}

// ---------------- Terminal Log Display ----------------
function appendTelemetryLogs(records) {
  if (!telemetryTerminal || !records || records.length === 0) return;

  // Clear placeholder on first real records
  if (telemetryTerminal.querySelector('.italic')) {
    telemetryTerminal.innerHTML = '';
  }

  records.forEach(rec => {
    const isFault = rec.status === 'FAULTED' || rec.active_fault;
    const timeStr = rec.timestamp ? rec.timestamp.substring(11, 23) : new Date().toISOString().substring(11, 23);

    const row = document.createElement('div');
    if (isFault) {
      row.className = "flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-red-100/80 border border-red-200 text-red-900";
      row.innerHTML = `
        <span class="text-red-700/70 font-mono text-[11px]">[${timeStr}]</span>
        <span class="text-red-800 font-extrabold font-mono">${rec.router_id}</span>
        <span class="opacity-40">➔</span>
        <span class="font-mono font-bold">${rec.latency}ms | ${rec.packet_loss}% | ${rec.jitter}ms | BW:${rec.bandwidth_usage}% | CPU:${rec.cpu_usage}% | MEM:${rec.memory_usage}%</span>
        <span class="ml-auto text-red-900 font-extrabold text-[10px] px-2 py-0.5 rounded-full bg-red-200 uppercase">[FAULT: ${rec.active_fault || 'PERTURB'}]</span>
      `;
    } else {
      row.className = "flex items-center gap-2 px-2.5 py-1.5 rounded-xl hover:bg-white/50 text-clay-text transition-colors";
      row.innerHTML = `
        <span class="text-clay-muted/70 font-mono text-[11px]">[${timeStr}]</span>
        <span class="text-[#7c3aed] font-bold font-mono">${rec.router_id}</span>
        <span class="opacity-40">➔</span>
        <span class="font-mono">${rec.latency}ms | ${rec.packet_loss}% | ${rec.jitter}ms | BW:${rec.bandwidth_usage}% | CPU:${rec.cpu_usage}% | MEM:${rec.memory_usage}%</span>
        <span class="ml-auto text-emerald-800 font-bold text-[10px] px-2 py-0.5 rounded-full bg-emerald-100">[NOMINAL]</span>
      `;
    }
    telemetryTerminal.appendChild(row);
  });

  // Limit terminal lines to 35 for browser performance
  while (telemetryTerminal.children.length > 35) {
    telemetryTerminal.removeChild(telemetryTerminal.firstChild);
  }
  telemetryTerminal.scrollTop = telemetryTerminal.scrollHeight;
}

// ---------------- Modal Controls ----------------
function openModal() {
  // Suggest next router ID (e.g. R5, R6...)
  const count = state.routers.length + 1;
  let nextId = `R${count}`;
  while (state.routers.find(r => r.id === nextId)) {
    nextId = `R${parseInt(nextId.substring(1)) + 1}`;
  }
  newRouterId.value = nextId;
  newRouterName.value = `Core Router ${nextId.substring(1)}`;
  addRouterModal.classList.remove('hidden');
}

function closeModal() {
  addRouterModal.classList.add('hidden');
}

openAddRouterBtn.addEventListener('click', openModal);
headerAddRouterBtn.addEventListener('click', openModal);
closeModalBtn.addEventListener('click', closeModal);
cancelAddRouterBtn.addEventListener('click', closeModal);

addRouterForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const id = newRouterId.value.trim().toUpperCase();
  const name = newRouterName.value.trim() || `Router ${id}`;

  if (!id) return;

  if (state.isBackendConnected) {
    try {
      await fetch('/api/routers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, name })
      });
    } catch (err) {
      console.error('Failed to add router to server:', err);
    }
  } else {
    fallbackEngine.addRouter(id, name);
  }

  closeModal();
  fetchLiveTelemetry();
});

// ---------------- Simulation Actions ----------------
btnSimStart.addEventListener('click', async () => {
  state.isRunning = true;
  if (state.isBackendConnected) {
    await fetch('/api/simulation/start', { method: 'POST' });
  }
  renderUI();
});

btnSimPause.addEventListener('click', async () => {
  state.isRunning = false;
  if (state.isBackendConnected) {
    await fetch('/api/simulation/pause', { method: 'POST' });
  }
  renderUI();
});

btnSimReset.addEventListener('click', async () => {
  state.elapsedTicks = 0;
  if (state.isBackendConnected) {
    await fetch('/api/simulation/reset', { method: 'POST' });
  } else {
    fallbackEngine.activeFaults = {};
    fallbackEngine.totalRecords = 0;
  }
  telemetryTerminal.innerHTML = '<div class="text-clay-muted text-[11px] italic">Simulation reset. Stream initialized...</div>';
  fetchLiveTelemetry();
});

// Speed Toggle Handler
speedButtons.forEach(btn => {
  btn.addEventListener('click', async () => {
    const spd = parseFloat(btn.dataset.speed);
    state.speed = spd;

    speedButtons.forEach(b => {
      b.classList.remove('bg-[#cbb8ff]', 'text-clay-text', 'font-extrabold', 'shadow-sm');
      b.classList.add('text-clay-muted', 'font-bold');
    });
    btn.classList.add('bg-[#cbb8ff]', 'text-clay-text', 'font-extrabold', 'shadow-sm');
    btn.classList.remove('text-clay-muted');

    if (state.isBackendConnected) {
      await fetch('/api/simulation/speed', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ speed: spd })
      });
    }
    restartPollingInterval();
  });
});

// ---------------- Fault Injection Handlers ----------------
injectFaultBtn.addEventListener('click', async () => {
  const routerId = faultTargetSelect.value;
  const faultType = faultTypeSelect.value;
  const duration = parseFloat(faultDurationSelect.value);
  const intensity = faultIntensitySelect.value;

  if (!routerId) return;

  if (state.isBackendConnected) {
    try {
      await fetch('/api/faults/inject', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          router_id: routerId,
          fault_type: faultType,
          duration: duration,
          intensity: intensity
        })
      });
    } catch (err) {
      console.error('Failed to inject fault via server:', err);
    }
  } else {
    fallbackEngine.injectFault(routerId, faultType, duration, intensity);
  }

  fetchLiveTelemetry();
});

async function clearAllFaults() {
  if (state.isBackendConnected) {
    await fetch('/api/faults/clear', { method: 'POST' });
  } else {
    fallbackEngine.clearFaults();
  }
  fetchLiveTelemetry();
}

clearFaultsBtn.addEventListener('click', clearAllFaults);
dismissFaultBannerBtn.addEventListener('click', clearAllFaults);

// ---------------- Terminal Log Controls ----------------
btnPauseLogs.addEventListener('click', () => {
  state.isLogPaused = !state.isLogPaused;
  btnPauseLogs.textContent = state.isLogPaused ? 'Resume View' : 'Pause View';
});

btnClearLogs.addEventListener('click', () => {
  telemetryTerminal.innerHTML = '<div class="text-clay-muted text-[11px] italic">Terminal cleared. Telemetry persists to disk...</div>';
});

btnCopyLogs.addEventListener('click', () => {
  if (telemetryTerminal) {
    navigator.clipboard.writeText(telemetryTerminal.innerText).then(() => {
      const orig = btnCopyLogs.textContent;
      btnCopyLogs.textContent = 'Copied!';
      setTimeout(() => { btnCopyLogs.textContent = orig; }, 1500);
    });
  }
});

// ---------------- Polling Loop ----------------
let pollingTimer = null;

function restartPollingInterval() {
  if (pollingTimer) clearInterval(pollingTimer);
  const interval = Math.max(200, Math.floor(1000 / state.speed));
  pollingTimer = setInterval(fetchLiveTelemetry, interval);
}

// Initialize on Load
window.addEventListener('DOMContentLoaded', async () => {
  await checkBackend();
  await fetchLiveTelemetry();
  restartPollingInterval();
});

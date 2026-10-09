document.addEventListener("DOMContentLoaded", () => {
  initRouters();
  initAnomalies();
  initRisks();
  initTerminal();
  initChart();
  initTopology();
});

const routers = [
  { id: 'R1', role: 'CORE', status: 'HEALTHY', cpu: 32, mem: 45, lat: 14, drop: 0.1 },
  { id: 'R2', role: 'EDGE', status: 'HEALTHY', cpu: 28, mem: 36, lat: 15, drop: 0.0 },
  { id: 'R3', role: 'CORE', status: 'WARNING', cpu: 74, mem: 62, lat: 45, drop: 1.2 },
  { id: 'R4', role: 'EDGE', status: 'HEALTHY', cpu: 41, mem: 39, lat: 12, drop: 0.1 },
  { id: 'R5', role: 'CORE', status: 'CRITICAL', cpu: 92, mem: 88, lat: 120, drop: 8.4 },
  { id: 'R6', role: 'EDGE', status: 'HEALTHY', cpu: 22, mem: 31, lat: 11, drop: 0.0 },
  { id: 'R7', role: 'CORE', status: 'HEALTHY', cpu: 35, mem: 40, lat: 16, drop: 0.1 },
  { id: 'R8', role: 'EDGE', status: 'WARNING', cpu: 87, mem: 45, lat: 22, drop: 0.3 },
];

function getStatusClass(status) {
  if (status === 'HEALTHY') return 'led-green';
  if (status === 'WARNING') return 'led-amber pulse';
  return 'led-red';
}

function initRouters() {
  const container = document.getElementById('router-list');
  let html = '';
  routers.forEach(r => {
    html += `
      <div class="router-row">
        <div class="r-id">${r.id}</div>
        <div class="r-role">${r.role}</div>
        <div class="led ${getStatusClass(r.status)}"></div>
        <div class="r-metrics">
          <span title="CPU">C:${r.cpu}%</span>
          <span title="Memory">M:${r.mem}%</span>
          <span title="Latency">${r.lat}ms</span>
        </div>
      </div>
    `;
  });
  container.innerHTML = html;
}

function initAnomalies() {
  const container = document.getElementById('anomalies-list');
  const anomalies = [
    { sev: 'CRITICAL', node: 'R5', type: 'Packet Loss Spike', val: '8.4%', time: '2 min ago', cls: 'text-red' },
    { sev: 'WARNING', node: 'R3', type: 'Latency Spike', val: '74 ms', time: '6 min ago', cls: 'text-amber' },
    { sev: 'WARNING', node: 'R8', type: 'CPU Overload', val: '87%', time: '11 min ago', cls: 'text-amber' }
  ];
  let html = '';
  anomalies.forEach(a => {
    html += `
      <div class="anomaly-item">
        <div class="anomaly-header">
          <span class="anomaly-title ${a.cls}">${a.sev}</span>
          <span class="anomaly-time">${a.time}</span>
        </div>
        <div class="anomaly-desc">
          ${a.node} - ${a.type} <span class="anomaly-val">${a.val}</span>
        </div>
      </div>
    `;
  });
  container.innerHTML = html;
}

function initRisks() {
  const container = document.getElementById('risk-list');
  const risks = [
    { id: 'R5', val: '82%', lvl: 'HIGH RISK', cls: 'text-red', issues: 'CPU Saturation, Packet Loss' },
    { id: 'R3', val: '61%', lvl: 'MEDIUM RISK', cls: 'text-amber', issues: 'Latency Trend' }
  ];
  let html = '';
  risks.forEach(r => {
    html += `
      <div class="risk-item">
        <div class="risk-left">
          <div class="risk-id">${r.id}</div>
          <div>
            <div class="${r.cls} risk-val">${r.lvl} (${r.val})</div>
            <span class="risk-sub">${r.issues}</span>
          </div>
        </div>
        <div class="led ${r.cls === 'text-red' ? 'led-red' : 'led-amber'}"></div>
      </div>
    `;
  });
  container.innerHTML = html;
}

function initTerminal() {
  const container = document.getElementById('event-stream');
  const events = [
    { time: '20:41:02', node: 'R3', type: 'LATENCY_SPIKE', val: '74ms', cls: 'warning' },
    { time: '20:40:58', node: 'R5', type: 'PACKET_LOSS', val: '8.4%', cls: 'critical' },
    { time: '20:40:41', node: 'R2', type: 'TELEMETRY_UPDATE', val: '', cls: '' },
    { time: '20:40:37', node: 'R8', type: 'CPU_WARNING', val: '87%', cls: 'warning' },
    { time: '20:40:21', node: 'R1', type: 'TELEMETRY_UPDATE', val: '', cls: '' },
    { time: '20:40:15', node: 'SYS', type: 'AI_COPILOT_INFERENCE', val: 'COMPLETE', cls: 'violet' }
  ];
  
  let html = '';
  events.forEach(e => {
    let evtCls = e.cls === 'violet' ? 'violet-text' : '';
    html += `
      <div class="term-line ${e.cls}">
        <span class="time">${e.time}</span>
        <span class="node">${e.node}</span>
        <span class="event ${evtCls}">${e.type}</span>
        <span class="val">${e.val}</span>
      </div>
    `;
  });
  container.innerHTML = html;
}

function initChart() {
  const ctx = document.getElementById('liveChart').getContext('2d');
  
  // Mock data with an anomaly around index 15
  const labels = Array.from({length: 30}, (_, i) => `-${30-i}m`);
  const dataCore = Array.from({length: 30}, () => 12 + Math.random() * 5);
  const dataEdge = Array.from({length: 30}, () => 15 + Math.random() * 6);
  
  // Introduce anomaly
  dataCore[15] = 45; dataCore[16] = 60; dataCore[17] = 74; dataCore[18] = 50; dataCore[19] = 20;

  Chart.defaults.color = '#64748b';
  Chart.defaults.font.family = "'JetBrains Mono', monospace";
  Chart.defaults.font.size = 10;

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Core Avg (ms)',
          data: dataCore,
          borderColor: '#00e5ff',
          backgroundColor: 'rgba(0, 229, 255, 0.1)',
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 4,
          tension: 0.4,
          fill: true
        },
        {
          label: 'Edge Avg (ms)',
          data: dataEdge,
          borderColor: '#a855f7',
          backgroundColor: 'rgba(168, 85, 247, 0.05)',
          borderWidth: 2,
          borderDash: [4, 4],
          pointRadius: 0,
          pointHoverRadius: 4,
          tension: 0.4,
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          align: 'end',
          labels: { boxWidth: 12, usePointStyle: true }
        },
        tooltip: {
          backgroundColor: '#181d27',
          titleColor: '#e2e8f0',
          bodyColor: '#00e5ff',
          borderColor: '#3c4453',
          borderWidth: 1,
          padding: 10
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(100, 116, 139, 0.1)', drawBorder: false },
          ticks: { maxTicksLimit: 8 }
        },
        y: {
          grid: { color: 'rgba(100, 116, 139, 0.1)', drawBorder: false },
          beginAtZero: true
        }
      }
    }
  });
}

function initTopology() {
  const canvas = document.getElementById('topologyCanvas');
  const ctx = canvas.getContext('2d');
  
  // Resize for sharp rendering
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width;
  canvas.height = rect.height;

  const nodes = [
    { id: 'R1', x: 0.2, y: 0.3, status: 'HEALTHY' },
    { id: 'R2', x: 0.5, y: 0.3, status: 'HEALTHY' },
    { id: 'R3', x: 0.8, y: 0.3, status: 'WARNING' },
    { id: 'R4', x: 0.35, y: 0.7, status: 'HEALTHY' },
    { id: 'R5', x: 0.65, y: 0.7, status: 'CRITICAL' },
  ];

  const links = [
    { source: 0, target: 1 },
    { source: 1, target: 2 },
    { source: 0, target: 3 },
    { source: 1, target: 4 },
    { source: 3, target: 4 },
    { source: 2, target: 4 }
  ];

  const w = canvas.width;
  const h = canvas.height;

  function getColor(status) {
    if (status === 'HEALTHY') return '#10b981';
    if (status === 'WARNING') return '#f59e0b';
    if (status === 'CRITICAL') return '#ef4444';
    return '#00e5ff';
  }

  // Draw links
  ctx.lineWidth = 2;
  links.forEach(l => {
    const s = nodes[l.source];
    const t = nodes[l.target];
    
    // Check if link goes to a critical node
    let strokeStyle = '#2a313d';
    if (s.status === 'CRITICAL' || t.status === 'CRITICAL') {
      strokeStyle = 'rgba(239, 68, 68, 0.5)';
    } else if (s.status === 'WARNING' || t.status === 'WARNING') {
      strokeStyle = 'rgba(245, 158, 11, 0.5)';
    } else {
      strokeStyle = 'rgba(16, 185, 129, 0.3)';
    }
    
    ctx.beginPath();
    ctx.strokeStyle = strokeStyle;
    ctx.moveTo(s.x * w, s.y * h);
    ctx.lineTo(t.x * w, t.y * h);
    ctx.stroke();
  });

  // Draw nodes
  nodes.forEach(n => {
    const nx = n.x * w;
    const ny = n.y * h;
    const color = getColor(n.status);
    
    // Node body
    ctx.beginPath();
    ctx.fillStyle = '#181d27';
    ctx.arc(nx, ny, 16, 0, Math.PI * 2);
    ctx.fill();
    
    // Inner ring
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.arc(nx, ny, 12, 0, Math.PI * 2);
    ctx.stroke();
    
    // Glowing dot
    ctx.beginPath();
    ctx.fillStyle = color;
    ctx.arc(nx, ny, 3, 0, Math.PI * 2);
    ctx.fill();

    // Text
    ctx.fillStyle = '#e2e8f0';
    ctx.font = "11px 'JetBrains Mono'";
    ctx.textAlign = 'center';
    ctx.fillText(n.id, nx, ny + 32);
  });
}

// Ensure resize is handled
window.addEventListener('resize', () => {
  initTopology();
});

const UI_CONFIG = {
    colors: {
        cyan: '#66FCF1', blue: '#45A29E',
        amber: '#F7B733', crimson: '#FC4445', grid: '#45A29E22'
    }
};

// -- API Fetch with Mock Fallback --
async function fetchRadarData(days = 30, projectId = null) {
    try {
        const params = new URLSearchParams({ days });
        if (projectId) params.append('project_id', projectId);
        const res = await fetch(`/traceability/radar?${params}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } catch (e) {
        console.warn('[Radar] API unavailable, using mock data:', e.message);
        return null; // triggers mock fallback
    }
}

// Mock fallback data
const MOCK_API_DATA = {
    meta: { total_merged_mrs: 42, days: 30 },
    vsm: { avg_wait_minutes: 52.4, avg_draft_minutes: 300, flow_efficiency: 0.65 },
    collaboration: { rubber_stamp_rate: 0.185, effective_review_rate: 0.742, avg_effective_comments: 2.3 },
    security: { critical: 2, high: 5, medium: 8, low: 12, total_active: 27 },
    eloc: {
        labels: ['张伟', '李娜', '王芳', '刘洋', '陈磊', '周静'],
        values: [4820, 3940, 3120, 2680, 2100, 1450],
    },
    vsm_timeline: [
        { id: '!101', title: 'feat: add cost tracking',       draft_minutes: 120, wait_minutes: 45,  review_minutes: 180 },
        { id: '!102', title: 'fix: security vuln in api',     draft_minutes: 20,  wait_minutes: 10,  review_minutes: 50  },
        { id: '!103', title: 'refactor: mixin structure',     draft_minutes: 300, wait_minutes: 120, review_minutes: 240 },
        { id: '!104', title: 'docs: update data dictionary',  draft_minutes: 40,  wait_minutes: 5,   review_minutes: 15  },
    ]
};


// Static radar axes config (labels + default normalized scores)
const RADAR_AXES = [
    { label: 'Velocity',      key: 'flow_efficiency',      fallback: 0.8 },
    { label: 'Review Depth',  key: 'effective_review_rate', fallback: 0.9 },
    { label: 'No Rubber Stamp', key: '_no_rubber_stamp',   fallback: 0.8 },
    { label: 'SLA Success',   key: null,                   fallback: 0.7 },
    { label: 'Doc Quality',   key: null,                   fallback: 0.5 },
];

function buildRadarData(apiData) {
    const vsm = apiData?.vsm || {};
    const c = apiData?.collaboration || {};
    return RADAR_AXES.map(ax => {
        let val = ax.fallback;
        if (ax.key === '_no_rubber_stamp') {
            val = 1 - (c.rubber_stamp_rate ?? 0.2);
        } else if (ax.key === 'flow_efficiency') {
            val = vsm.flow_efficiency ?? ax.fallback;
        } else if (ax.key && c[ax.key] != null) {
            val = c[ax.key];
        }
        return { label: ax.label, value: val };
    });
}

function buildVSMData(apiData) {
    return (apiData?.vsm_timeline || []).map(m => ({
        id: m.id, title: m.title,
        draft: m.draft_minutes || 0,
        wait:  m.wait_minutes  || 0,
        review:m.review_minutes|| 0,
        total: (m.draft_minutes || 0) + (m.wait_minutes || 0) + (m.review_minutes || 0) || 1,
    }));
}

function updateMetricCards(apiData) {
    const vsm = apiData?.vsm || {};
    const col = apiData?.collaboration || {};
    const sec = apiData?.security || {};
    const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    set('card-wait-time',  vsm.avg_wait_minutes != null ? vsm.avg_wait_minutes + 'm' : '--');
    set('card-rubber-stamp', col.rubber_stamp_rate != null ? (col.rubber_stamp_rate * 100).toFixed(1) + '%' : '--');
    set('card-eff-review',   col.effective_review_rate != null ? (col.effective_review_rate * 100).toFixed(1) + '%' : '--');
    set('card-vuln-count', sec.total_active != null ? String(sec.total_active).padStart(2, '0') : '--');
    set('card-vuln-detail', `${sec.critical ?? 0} CRITICAL / ${sec.high ?? 0} HIGH`);
}

// -- Main Init --
window.addEventListener('DOMContentLoaded', async () => {
    const apiData = await fetchRadarData() || MOCK_API_DATA;

    // Update metric cards with live data
    updateMetricCards(apiData);

    // Draw visualizations
    drawRadar('radar-chart', buildRadarData(apiData));
    renderVSM('vsm-container', buildVSMData(apiData));
    drawELOC('eloc-chart', apiData.eloc || MOCK_API_DATA.eloc);
});


/**
 * Draws a Radar chart using SVG.
 */
function drawRadar(svgId, data) {
    const svg = document.getElementById(svgId);
    if (!svg) return;
    svg.innerHTML = ''; // Clear

    const centerX = 200;
    const centerY = 200;
    const radius = 150;
    const levels = 5;
    const angleStep = (Math.PI * 2) / data.length;

    // Draw concentric circles
    for (let i = 1; i <= levels; i++) {
        const r = (radius / levels) * i;
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", centerX);
        circle.setAttribute("cy", centerY);
        circle.setAttribute("r", r);
        circle.setAttribute("fill", "none");
        circle.setAttribute("stroke", UI_CONFIG.colors.grid);
        svg.appendChild(circle);
    }

    // Draw axis lines and labels
    data.forEach((item, i) => {
        const angle = i * angleStep - Math.PI / 2;
        const x = centerX + radius * Math.cos(angle);
        const y = centerY + radius * Math.sin(angle);

        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", centerX);
        line.setAttribute("y1", centerY);
        line.setAttribute("x2", x);
        line.setAttribute("y2", y);
        line.setAttribute("stroke", UI_CONFIG.colors.grid);
        svg.appendChild(line);

        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", centerX + (radius + 25) * Math.cos(angle));
        text.setAttribute("y", centerY + (radius + 25) * Math.sin(angle));
        text.setAttribute("fill", UI_CONFIG.colors.blue);
        text.setAttribute("font-family", "JetBrains Mono");
        text.setAttribute("font-size", "10");
        text.setAttribute("text-anchor", "middle");
        text.textContent = item.label;
        svg.appendChild(text);
    });

    // Draw data polygon
    const points = data.map((item, i) => {
        const angle = i * angleStep - Math.PI / 2;
        const r = radius * item.value;
        return `${centerX + r * Math.cos(angle)},${centerY + r * Math.sin(angle)}`;
    }).join(" ");

    const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
    polygon.setAttribute("points", points);
    polygon.setAttribute("fill", "rgba(102, 252, 241, 0.3)");
    polygon.setAttribute("stroke", UI_CONFIG.colors.cyan);
    polygon.setAttribute("stroke-width", "2");
    svg.appendChild(polygon);
}

/**
 * Draws the VSM Timeline.
 */
function renderVSM(containerId, data) {
    const container = document.getElementById(containerId);
    if (!container) return;

    let html = `
        <table style="width: 100%; border-collapse: collapse; font-family: var(--font-mono); font-size: 0.75rem;">
            <thead>
                <tr style="text-align: left; color: var(--accent-blue); border-bottom: 1px solid var(--border-color);">
                    <th style="padding: 10px;">ID</th>
                    <th style="padding: 10px;">TITLE</th>
                    <th style="padding: 10px;">LIFECYCLE VISUALIZATION (DRAFT / WAIT / REVIEW)</th>
                </tr>
            </thead>
            <tbody>
    `;

    data.forEach(item => {
        const total = item.total;
        const draftW = (item.draft / total) * 100;
        const waitW = (item.wait / total) * 100;
        const reviewW = (item.review / total) * 100;

        html += `
            <tr style="border-bottom: 1px solid var(--border-color); transition: background 0.2s;" onmouseover="this.style.background='rgba(69,162,158,0.1)'" onmouseout="this.style.background='transparent'">
                <td style="padding: 10px; color: var(--accent-cyan);">${item.id}</td>
                <td style="padding: 10px;">${item.title}</td>
                <td style="padding: 10px;">
                    <div style="display: flex; height: 12px; background: #000; border-radius: 2px; overflow: hidden;">
                        <div style="width: ${draftW}%; background: var(--accent-blue);" title="Draft: ${item.draft}m"></div>
                        <div style="width: ${waitW}%; background: var(--accent-amber);" title="Wait: ${item.wait}m"></div>
                        <div style="width: ${reviewW}%; background: var(--accent-cyan);" title="Review: ${item.review}m"></div>
                    </div>
                </td>
            </tr>
        `;
    });

    html += `</tbody></table>`;
    container.innerHTML = html;
}

/**
 * Draws ELOC bar chart using Chart.js.
 */
function drawELOC(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !window.Chart) return;
    
    // Clear existing chart instance if any
    if (window._elocChart) window._elocChart.destroy();

    window._elocChart = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Effective Lines of Code',
                data: data.values,
                backgroundColor: 'rgba(102, 252, 241, 0.25)',
                borderColor: '#66FCF1',
                borderWidth: 1,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#45A29E', font: { family: 'JetBrains Mono', size: 11 } }, grid: { color: '#45A29E22' } },
                y: { ticks: { color: '#45A29E', font: { family: 'JetBrains Mono', size: 11 } }, grid: { color: '#45A29E22' } }
            }
        }
    });
}

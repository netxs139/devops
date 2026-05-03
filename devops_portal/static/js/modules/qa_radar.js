import { Api, UI } from './sys_core.js';
import '../components/qa_radar_drawer.component.js';

/**
 * Traceability Radar Handler
 * 负责渲染研发效能雷达看板（Flow Efficiency, Collaboration, Security）
 */
const QaRadarHandler = {
    state: {
        days: 30,
        projectId: null,
        data: null,
        charts: {
            eloc: null
        }
    },

    init() {
        console.log("Traceability Radar Dashboard Initialized");
        
        // 绑定刷新按钮
        document.querySelector('.js-btn-radar-refresh')?.addEventListener('click', () => this.loadData());
        
        // 绑定天数切换
        document.getElementById('radar-filter-days')?.addEventListener('change', (e) => {
            this.state.days = parseInt(e.target.value);
            this.loadData();
        });

        // 监听产品/项目切换
        const selector = document.getElementById('radar-project-selector');
        if (selector) {
            selector.addEventListener('change', (e) => {
                this.state.projectId = e.detail.id;
                console.log('[Radar] Scope changed:', e.detail.type, e.detail.id);
                this.loadData();
            });
        }

        // 初次加载
        this.loadData();
    },

    /**
     * 从后端 API 加载数据
     */
    async loadData() {
        const container = document.getElementById('vsm-container');
        if (container) container.innerHTML = '<div class="u-text-center u-p-40 u-text-dim">Loading Radar data...</div>';

        try {
            const params = { days: this.state.days };
            if (this.state.projectId) params.project_id = this.state.projectId;

            const data = await Api.get('/traceability/radar', params);
            this.state.data = data;
            
            this.render(data);
            UI.showToast("Radar data synchronized", "success");
        } catch (e) {
            console.error('[Radar] Load failed:', e);
            UI.showToast("Failed to load radar data", "error");
        }
    },

    /**
     * 渲染所有组件
     */
    render(data) {
        this.updateMetricCards(data);
        this.drawRadarChart('radar-chart', this.buildRadarAxes(data));
        this.drawELOCChart('eloc-chart', data.eloc);
        this.renderVSM('vsm-container', this.buildVSMTimeline(data));
    },

    updateMetricCards(data) {
        const vsm = data.vsm || {};
        const col = data.collaboration || {};
        const sec = data.security || {};
        
        const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        set('card-wait-time',  vsm.avg_wait_minutes != null ? Math.round(vsm.avg_wait_minutes) + 'm' : '--');
        set('card-rubber-stamp', col.rubber_stamp_rate != null ? (col.rubber_stamp_rate * 100).toFixed(1) + '%' : '--');
        set('card-eff-review',   col.effective_review_rate != null ? (col.effective_review_rate * 100).toFixed(1) + '%' : '--');
        set('card-vuln-count', sec.total_active != null ? String(sec.total_active).padStart(2, '0') : '--');
        set('card-vuln-detail', `${sec.critical ?? 0} CRIT / ${sec.high ?? 0} HIGH`);

        // 绑定下钻事件
        this.bindDrilldown('card-wait-time', 'VSM_WAITING', '长等待 MR 详情');
        this.bindDrilldown('card-rubber-stamp', 'RUBBER_STAMP', '秒批 MR 详情');
        this.bindDrilldown('card-vuln-count', 'VULNERABILITY', '活跃漏洞详情');
    },

    bindDrilldown(elementId, type, title) {
        const el = document.getElementById(elementId);
        if (!el) return;
        el.style.cursor = 'pointer';
        el.title = '点击查看详情';
        el.onclick = () => this.showDetail(type, title);
    },

    async showDetail(type, title) {
        const drawer = document.getElementById('radar-detail-drawer');
        if (!drawer) return;

        try {
            UI.showToast("Fetching details...", "info");
            const params = { metric_type: type, days: this.state.days };
            if (this.state.projectId) params.project_id = this.state.projectId;

            const data = await Api.get('/traceability/detail', params);
            
            drawer.setAttribute('title', title);
            drawer.data = data.items;
            drawer.setAttribute('opened', 'true');
        } catch (e) {
            console.error('[Radar] Detail load failed:', e);
            UI.showToast("Failed to load details", "error");
        }
    },

    buildRadarAxes(data) {
        const vsm = data.vsm || {};
        const col = data.collaboration || {};
        
        // 定义 5 个维度的归一化得分 (0-1)
        return [
            { label: 'Flow Efficiency', value: vsm.flow_efficiency || 0.5 },
            { label: 'Review Depth',  value: col.effective_review_rate || 0.5 },
            { label: 'No Rubber Stamp', value: 1 - (col.rubber_stamp_rate || 0) },
            { label: 'Wait Time SLA', value: Math.max(0, 1 - (vsm.avg_wait_minutes || 0) / 480) }, // 假设 8h 为阈值
            { label: 'Commits Quality', value: 0.7 } // Placeholder for future metric
        ];
    },

    buildVSMTimeline(data) {
        return (data.vsm_timeline || []).map(m => ({
            id: m.id, title: m.title,
            draft: m.draft_minutes || 0,
            wait:  m.wait_minutes  || 0,
            review:m.review_minutes|| 0,
            total: m.total_minutes || 1
        }));
    },

    drawRadarChart(svgId, axes) {
        const svg = document.getElementById(svgId);
        if (!svg) return;
        svg.innerHTML = ''; 

        const centerX = 200, centerY = 200, radius = 150, levels = 5;
        const angleStep = (Math.PI * 2) / axes.length;
        const gridColor = 'rgba(69, 162, 158, 0.15)';
        const accentColor = '#66FCF1';

        // 网格背景
        for (let i = 1; i <= levels; i++) {
            const r = (radius / levels) * i;
            const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            circle.setAttribute("cx", centerX); circle.setAttribute("cy", centerY); circle.setAttribute("r", r);
            circle.setAttribute("fill", "none"); circle.setAttribute("stroke", gridColor);
            svg.appendChild(circle);
        }

        // 轴线与文字
        axes.forEach((ax, i) => {
            const angle = i * angleStep - Math.PI / 2;
            const x = centerX + radius * Math.cos(angle);
            const y = centerY + radius * Math.sin(angle);

            const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
            line.setAttribute("x1", centerX); line.setAttribute("y1", centerY);
            line.setAttribute("x2", x); line.setAttribute("y2", y);
            line.setAttribute("stroke", gridColor);
            svg.appendChild(line);

            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.setAttribute("x", centerX + (radius + 25) * Math.cos(angle));
            text.setAttribute("y", centerY + (radius + 25) * Math.sin(angle));
            text.setAttribute("fill", "#45A29E");
            text.setAttribute("font-family", "Outfit");
            text.setAttribute("font-size", "10");
            text.setAttribute("text-anchor", "middle");
            text.textContent = ax.label;
            svg.appendChild(text);
        });

        // 数据多边形
        const points = axes.map((ax, i) => {
            const angle = i * angleStep - Math.PI / 2;
            const r = radius * Math.min(1, ax.value);
            return `${centerX + r * Math.cos(angle)},${centerY + r * Math.sin(angle)}`;
        }).join(" ");

        const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
        polygon.setAttribute("points", points);
        polygon.setAttribute("fill", "rgba(102, 252, 241, 0.2)");
        polygon.setAttribute("stroke", accentColor);
        polygon.setAttribute("stroke-width", "2");
        svg.appendChild(polygon);
    },

    drawELOCChart(canvasId, elocData) {
        const canvas = document.getElementById(canvasId);
        if (!canvas || !window.Chart) return;

        if (this.state.charts.eloc) this.state.charts.eloc.destroy();

        this.state.charts.eloc = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: elocData.labels,
                datasets: [{
                    label: 'Effective Lines of Code',
                    data: elocData.values,
                    backgroundColor: 'rgba(102, 252, 241, 0.2)',
                    borderColor: '#66FCF1',
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: '#45A29E', font: { size: 10 } }, grid: { color: 'rgba(69, 162, 158, 0.1)' } },
                    y: { ticks: { color: '#45A29E', font: { size: 10 } }, grid: { display: false } }
                }
            }
        });
    },

    renderVSM(containerId, data) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (data.length === 0) {
            container.innerHTML = '<div class="u-text-center u-p-40 u-text-dim">No MR data found for selected period.</div>';
            return;
        }

        let html = `
            <table class="adm-data-table" style="font-size: 0.75rem;">
                <thead>
                    <tr>
                        <th style="width: 80px;">MR ID</th>
                        <th>TITLE</th>
                        <th>LIFECYCLE (DRAFT / WAIT / REVIEW)</th>
                    </tr>
                </thead>
                <tbody>
        `;

        data.forEach(item => {
            const total = item.total || 1;
            const draftW = (item.draft / total) * 100;
            const waitW = (item.wait / total) * 100;
            const reviewW = (item.review / total) * 100;

            html += `
                <tr>
                    <td class="u-weight-600 u-text-primary">${item.id}</td>
                    <td class="u-truncate" style="max-width: 300px;">${item.title}</td>
                    <td>
                        <div class="u-flex u-h-12 u-w-full u-radius-sm u-overflow-hidden" style="background: rgba(255,255,255,0.05);">
                            <div style="width: ${draftW}%; background: #45A29E;" title="Draft: ${Math.round(item.draft)}m"></div>
                            <div style="width: ${waitW}%; background: #F7B733;" title="Wait: ${Math.round(item.wait)}m"></div>
                            <div style="width: ${reviewW}%; background: #66FCF1;" title="Review: ${Math.round(item.review)}m"></div>
                        </div>
                    </td>
                </tr>
            `;
        });

        html += `</tbody></table>`;
        container.innerHTML = html;
    }
};

export default QaRadarHandler;

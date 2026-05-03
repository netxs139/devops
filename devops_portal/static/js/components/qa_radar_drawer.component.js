/**
 * @file qa_radar_drawer.component.js
 * @description 效能雷达下钻详情侧边抽屉组件
 */

class QaRadarDrawer extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this._data = [];
        this._title = "详情";
        this._opened = false;
    }

    set data(val) {
        this._data = val;
        this.render();
    }

    static get observedAttributes() {
        return ['title', 'opened'];
    }

    attributeChangedCallback(name, oldVal, newVal) {
        if (name === 'title') this._title = newVal;
        if (name === 'opened') this._opened = newVal !== null && newVal !== 'false';
        this.render();
    }

    render() {
        const isOpen = this._opened;
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    position: fixed;
                    top: 0;
                    right: 0;
                    bottom: 0;
                    left: 0;
                    z-index: 1000;
                    visibility: ${isOpen ? 'visible' : 'hidden'};
                    transition: visibility 0.3s;
                }
                .overlay {
                    position: absolute;
                    top: 0;
                    right: 0;
                    bottom: 0;
                    left: 0;
                    background: rgba(0,0,0,0.5);
                    opacity: ${isOpen ? 1 : 0};
                    transition: opacity 0.3s;
                }
                .drawer {
                    position: absolute;
                    top: 0;
                    right: 0;
                    bottom: 0;
                    width: 500px;
                    background: #1a1a1a;
                    color: #eee;
                    box-shadow: -5px 0 15px rgba(0,0,0,0.5);
                    transform: translateX(${isOpen ? '0' : '100%'});
                    transition: transform 0.3s ease-in-out;
                    display: flex;
                    flex-direction: column;
                }
                .header {
                    padding: 20px;
                    border-bottom: 1px solid #333;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .title { font-size: 1.2rem; font-weight: 600; color: #66FCF1; }
                .close-btn { cursor: pointer; font-size: 1.5rem; color: #888; }
                .content {
                    flex: 1;
                    overflow-y: auto;
                    padding: 20px;
                }
                .item-card {
                    background: #2a2a2a;
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 12px;
                    border-left: 4px solid #66FCF1;
                }
                .item-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
                .item-id { color: #888; font-size: 0.85rem; font-family: monospace; }
                .item-title { font-weight: 500; font-size: 1rem; color: #fff; margin-bottom: 10px; }
                .item-meta { display: flex; justify-content: space-between; align-items: center; font-size: 0.9rem; }
                .item-value { color: #66FCF1; font-weight: bold; }
                .item-link { color: #0071e3; text-decoration: none; font-size: 0.85rem; }
                .item-link:hover { text-decoration: underline; }
            </style>
            <div class="overlay js-close"></div>
            <div class="drawer">
                <div class="header">
                    <div class="title">${this._title}</div>
                    <div class="close-btn js-close">&times;</div>
                </div>
                <div class="content">
                    ${this._data.map(item => `
                        <div class="item-card">
                            <div class="item-header">
                                <span class="item-id">${item.id}</span>
                                <span class="item-id">${item.timestamp ? item.timestamp.split('T')[0] : ''}</span>
                            </div>
                            <div class="item-title">${item.title}</div>
                            <div class="item-meta">
                                <span>${item.author || ''}</span>
                                <span class="item-value">${item.value || ''}</span>
                            </div>
                            <div style="margin-top:10px; text-align:right;">
                                <a href="${item.url}" target="_blank" class="item-link">在 GitLab 中查看 ↗</a>
                            </div>
                        </div>
                    `).join('')}
                    ${this._data.length === 0 ? '<div style="text-align:center; padding-top:50px; color:#666;">暂无相关记录</div>' : ''}
                </div>
            </div>
        `;

        this.shadowRoot.querySelectorAll('.js-close').forEach(el => {
            el.onclick = () => {
                this.dispatchEvent(new CustomEvent('close', { bubbles: true, composed: true }));
                this.removeAttribute('opened');
            };
        });
    }
}

customElements.define('qa-radar-drawer', QaRadarDrawer);

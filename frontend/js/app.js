/**
 * SPACE WEATHER AI DASHBOARD
 */

// --- Space Background System ---
class Starfield {
    constructor() {
        this.canvas = document.getElementById('starfield');
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        this.stars = [];
        this.resize();
        this.initStars(200);
        window.addEventListener('resize', () => this.resize());
        this.animate();
    }
    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }
    initStars(count) {
        this.stars = [];
        for (let i = 0; i < count; i++) {
            this.stars.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                size: Math.random() * 2,
                speed: Math.random() * 0.5 + 0.1
            });
        }
    }
    animate() {
        this.ctx.fillStyle = '#050b14';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.fillStyle = '#ffffff';
        this.stars.forEach(star => {
            star.y += star.speed;
            if (star.y > this.canvas.height) {
                star.y = 0;
                star.x = Math.random() * this.canvas.width;
            }
            this.ctx.globalAlpha = Math.random() * 0.5 + 0.3;
            this.ctx.beginPath();
            this.ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2);
            this.ctx.fill();
        });
        requestAnimationFrame(() => this.animate());
    }
}

// --- 3D Globe with Satellites (Interactive) ---
class EarthViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        // Scene Setup
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(45, this.container.clientWidth / this.container.clientHeight, 0.1, 1000);
        this.camera.position.z = 15;

        this.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.container.appendChild(this.renderer.domElement);

        // Group to hold Earth and Satellites
        this.earthGroup = new THREE.Group();
        this.scene.add(this.earthGroup);

        // Interaction Setup (Raycaster)
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        this.selectedSat = null;

        // Tooltip Element
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'glass-panel'; // Re-use existing glass style
        Object.assign(this.tooltip.style, {
            position: 'absolute',
            display: 'none',
            padding: '10px',
            pointerEvents: 'none',
            zIndex: '100',
            border: '1px solid var(--primary)',
            borderRadius: '4px',
            backgroundColor: 'rgba(5, 11, 20, 0.9)',
            minWidth: '150px'
        });
        this.container.appendChild(this.tooltip);

        // Bind Click Event
        this.renderer.domElement.addEventListener('click', (e) => this.onMouseClick(e));

        this.initEarth();
        this.satellites = [];
        this.loadSatellites();
        this.animate();

        window.addEventListener('resize', () => {
            if (this.container) {
                this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
                this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
                this.camera.updateProjectionMatrix();
            }
        });
    }

    initEarth() {
        const geometry = new THREE.IcosahedronGeometry(5, 2);
        const material = new THREE.MeshBasicMaterial({
            color: 0x00f2ff,
            wireframe: true,
            transparent: true,
            opacity: 0.3
        });
        this.earthMesh = new THREE.Mesh(geometry, material);
        this.earthGroup.add(this.earthMesh);

        // Core
        const coreGeo = new THREE.IcosahedronGeometry(4.9, 2);
        const coreMat = new THREE.MeshBasicMaterial({ color: 0x000000 });
        this.earthGroup.add(new THREE.Mesh(coreGeo, coreMat));
    }

    async loadSatellites() {
        try {
            const res = await fetch('/api/satellites');
            const data = await res.json();
            if (data.success) {
                data.data.forEach(sat => this.addSatellite(sat));
            }
        } catch (e) { console.error("Satellites error", e); }
    }

    addSatellite(satData) {
        const satrec = satellite.twoline2satrec(satData.line1, satData.line2);
        const geometry = new THREE.SphereGeometry(0.15, 8, 8); // Radius 0.15
        const material = new THREE.MeshBasicMaterial({ color: 0xff0055 }); // Red dot
        const mesh = new THREE.Mesh(geometry, material);

        // Add User Data for easy access
        mesh.userData = { isSatellite: true, name: satData.name };

        this.earthGroup.add(mesh);

        // Store full object for calculations
        this.satellites.push({
            mesh: mesh,
            satrec: satrec,
            name: satData.name
        });
    }

    onMouseClick(event) {
        // Calculate mouse position in normalized device coordinates (-1 to +1)
        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        // Raycast
        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(this.earthGroup.children);

        // Check if we hit a satellite
        const hit = intersects.find(obj => obj.object.userData.isSatellite);

        if (hit) {
            const satObj = this.satellites.find(s => s.mesh === hit.object);
            if (satObj) {
                this.selectSatellite(satObj, event.clientX, event.clientY, rect);
            }
        } else {
            this.hideTooltip();
        }
    }

    selectSatellite(sat, clientX, clientY, rect) {
        // 1. Highlight Effect
        if (this.selectedSat) this.selectedSat.mesh.material.color.setHex(0xff0055); // Reset old
        this.selectedSat = sat;
        sat.mesh.material.color.setHex(0x00ff00); // Green highlight

        // 2. Calculate Real-Time Position
        const now = new Date();
        const posVel = satellite.propagate(sat.satrec, now);
        const gmst = satellite.gstime(now);
        const posGd = satellite.eciToGeodetic(posVel.position, gmst);

        const lat = satellite.degreesLat(posGd.latitude).toFixed(2);
        const lon = satellite.degreesLong(posGd.longitude).toFixed(2);
        const alt = posGd.height.toFixed(1);

        // 3. Show Tooltip
        this.tooltip.innerHTML = `
            <div style="color:var(--primary); font-weight:bold; border-bottom:1px solid #333; margin-bottom:5px; padding-bottom:5px;">
                <i class="fas fa-satellite"></i> ${sat.name}
            </div>
            <div style="font-size:0.85rem; color:#ccc; line-height: 1.4;">
                <div style="display:flex; justify-content:space-between;"><span>LAT:</span> <span style="color:#fff">${lat}°</span></div>
                <div style="display:flex; justify-content:space-between;"><span>LON:</span> <span style="color:#fff">${lon}°</span></div>
                <div style="display:flex; justify-content:space-between;"><span>ALT:</span> <span style="color:#fff">${alt} km</span></div>
            </div>
        `;

        // Position tooltip near mouse relative to container
        const x = clientX - rect.left + 15;
        const y = clientY - rect.top + 15;
        this.tooltip.style.left = `${x}px`;
        this.tooltip.style.top = `${y}px`;
        this.tooltip.style.display = 'block';
    }

    hideTooltip() {
        this.tooltip.style.display = 'none';
        if (this.selectedSat) {
            this.selectedSat.mesh.material.color.setHex(0xff0055); // Reset color
            this.selectedSat = null;
        }
    }

    updateSatellitePositions() {
        const now = new Date();
        const gmst = satellite.gstime(now);

        this.satellites.forEach(sat => {
            const posVel = satellite.propagate(sat.satrec, now);
            if (posVel.position) {
                const posGd = satellite.eciToGeodetic(posVel.position, gmst);

                // Map to sphere radius 5
                const R = 5;
                const scale = R / 6371; // Earth radius ~6371km
                const r = R + (posGd.height * scale);

                const lat = posGd.latitude;
                const lon = posGd.longitude;

                const x = r * Math.cos(lat) * Math.cos(lon);
                const y = r * Math.sin(lat);
                const z = -r * Math.cos(lat) * Math.sin(lon);

                sat.mesh.position.set(x, y, z);
            }
        });
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        this.earthGroup.rotation.y += 0.002; // Rotate Earth
        this.updateSatellitePositions();
        this.renderer.render(this.scene, this.camera);
    }
}

// --- Main Dashboard Logic ---
// --- Main Dashboard Logic ---
class Dashboard {
    constructor() {
        this.apiBase = window.location.hostname === 'localhost' ? 'http://localhost:8000/api' : '/api';
        this.token = localStorage.getItem('token');
        if (!this.token) {
            window.location.href = 'login.html';
        }
        this.charts = {};
        this.init();
    }

    getHeaders() {
        return {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
        };
    }

    init() {
        new Starfield();
        new EarthViewer('globe-container');
        this.initCharts();
        this.updateClock();

        this.fetchData();
        this.fetchHistory();
        this.fetchForecast();
        this.fetchAlerts();

        setInterval(() => this.updateClock(), 1000);
        setInterval(() => this.fetchData(), 60000);
        setInterval(() => this.fetchHistory(), 300000);

        // Logout handler
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) logoutBtn.addEventListener('click', () => this.logout());
    }

    logout() {
        localStorage.removeItem('token');
        window.location.href = 'login.html';
    }

    updateClock() {
        const now = new Date();
        const timeEl = document.getElementById('system-clock');
        if (timeEl) timeEl.innerHTML = now.toISOString().split('T')[1].split('.')[0] + ' UTC';
    }
    initCharts() {
        if (typeof Chart === 'undefined') return;
        Chart.defaults.color = '#8ba4b6';
        Chart.defaults.font.family = "'Rajdhani', sans-serif";
        const opts = {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { maxTicksLimit: 6 } },
                y: { grid: { color: 'rgba(255,255,255,0.05)' } }
            },
            elements: { point: { radius: 0, hitRadius: 10 }, line: { tension: 0.4 } }
        };
        const windEl = document.getElementById('chart-wind');
        if (windEl) {
            const windCtx = windEl.getContext('2d');
            const windGradient = windCtx.createLinearGradient(0, 0, 0, 300);
            windGradient.addColorStop(0, 'rgba(0, 242, 255, 0.2)');
            windGradient.addColorStop(1, 'rgba(0, 242, 255, 0)');
            this.charts.wind = new Chart(windCtx, {
                type: 'line',
                data: { labels: [], datasets: [{ label: 'Speed', data: [], borderColor: '#00f2ff', backgroundColor: windGradient, fill: true }] },
                options: opts
            });
        }
        const magEl = document.getElementById('chart-mag');
        if (magEl) {
            this.charts.mag = new Chart(magEl, {
                type: 'line',
                data: { labels: [], datasets: [{ label: 'Bz', data: [], borderColor: '#ff0055', borderWidth: 2 }] },
                options: opts
            });
        }
    }

    async checkAuth(res) {
        if (res.status === 401) {
            this.logout();
            throw new Error("Unauthorized");
        }
        return res;
    }

    async fetchData() {
        try {
            const res = await fetch(`${this.apiBase}/prediction`, { headers: this.getHeaders() });
            await this.checkAuth(res);
            const data = await res.json();
            if (data.success) this.updateUI(data);
        } catch (e) { console.error("Data fetch error", e); this.addLog("Satellite feed interruption.", "warning"); }
    }
    async fetchHistory() {
        try {
            const res = await fetch(`${this.apiBase}/historical?hours=24`, { headers: this.getHeaders() });
            await this.checkAuth(res);
            const data = await res.json();
            if (data.success) this.updateCharts(data.data);
        } catch (e) { console.error("History fetch error", e); }
    }

    async fetchForecast() {
        try {
            const res = await fetch(`${this.apiBase}/forecast`, { headers: this.getHeaders() });
            await this.checkAuth(res);
            const data = await res.json();
            if (data.success) {
                this.updateForecastUI(data.data);
            }
        } catch (e) { console.error("Forecast fetch error", e); }
    }

    updateForecastUI(forecasts) {
        if (!forecasts || forecasts.length === 0) return;
        forecasts.forEach(f => {
            const elId = `forecast-${f.hour}h`;
            const row = document.getElementById(elId);
            if (row) {
                const valSpan = row.querySelector('.f-val');
                if (valSpan) {
                    valSpan.textContent = `Kp ${f.kp.toFixed(1)}`;
                    // Simple color coding
                    if (f.kp > 6) valSpan.style.color = 'var(--danger)';
                    else if (f.kp > 4) valSpan.style.color = 'var(--warning)';
                    else valSpan.style.color = 'var(--success)';
                }
            }
        });
    }

    async fetchAlerts() {
        try {
            const res = await fetch(`${this.apiBase}/alerts`, { headers: this.getHeaders() });
            await this.checkAuth(res);
            const data = await res.json();
            if (data.success) {
                this.renderAlerts(data.data);
            }
        } catch (e) { console.error("Alerts fetch error", e); }
    }

    renderAlerts(alerts) {
        const container = document.getElementById('alerts-container');
        if (!container) return;

        if (!alerts || alerts.length === 0) {
            container.innerHTML = '<div class="no-alerts">SYSTEM NOMINAL</div>';
            return;
        }

        container.innerHTML = '';
        alerts.forEach(alert => {
            const el = document.createElement('div');
            el.className = `alert-item ${alert.level.toLowerCase()}`;
            el.innerHTML = `
                <div class="alert-icon"><i class="fas fa-exclamation-circle"></i></div>
                <div class="alert-content">
                    <div class="alert-title">${alert.level} - ${alert.type}</div>
                    <div class="alert-msg">${alert.message}</div>
                    <div class="alert-time">${new Date(alert.time).toLocaleTimeString()}</div>
                </div>
            `;
            container.appendChild(el);
        });

        // Also update log if new alerts found
        alerts.forEach(alert => {
            // Check if already logged to avoid spam (simple check)
            // this.addLog(`ALERT: ${alert.message}`, "error"); 
        });
    }

    updateUI(data) {
        const p = data.space_weather.prediction;
        const r = data.space_weather.raw_features;
        const isi = data.infrastructure_risk.infrastructure_stress_index;
        const risks = data.infrastructure_risk;

        const ring = document.getElementById('severity-ring-progress');
        const levelText = document.getElementById('severity-level');
        if (ring && levelText) {
            const color = this.getColor(p.severity);
            let pct = 0.3;
            if (p.severity.toLowerCase() === 'moderate') pct = 0.6;
            if (p.severity.toLowerCase() === 'severe') pct = 0.95;
            ring.style.strokeDashoffset = 283 - (283 * pct);
            ring.style.stroke = color;
            levelText.textContent = p.severity.toUpperCase();
            levelText.style.color = color;
        }
        document.getElementById('confidence-value').textContent = (p.confidence * 100).toFixed(0) + '%';
        document.getElementById('prediction-explanation').textContent = data.space_weather.explanation.reasoning || "Nominal operation.";
        this.updateParam('wind-speed', 'bar-speed', r.wind_speed, 800);
        this.updateParam('bz-value', 'bar-bz', r.bz, 25, true);
        this.updateParam('kp-value', 'bar-kp', r.kp_index, 9);
        this.updateParam('density-value', 'bar-density', r.density, 50);
        document.getElementById('isi-value').textContent = isi.value.toFixed(0);
        this.updateRiskRow('sat', risks.satellite_risk);
        this.updateRiskRow('grid', risks.power_system_risk);
        this.addLog(`Telemetry update: ${p.severity}`);
    }
    updateParam(textId, barId, value, max, isSigned = false) {
        if (value === undefined || value === null) return;
        document.getElementById(textId).textContent = value.toFixed(1);
        let pct = (Math.abs(value) / max) * 100;
        document.getElementById(barId).style.width = Math.min(pct, 100) + '%';
    }
    updateRiskRow(idPrefix, riskData) {
        const el = document.getElementById(`${idPrefix}-risk-level`);
        const light = document.getElementById(`${idPrefix}-light`);
        if (el && light) {
            el.textContent = riskData.level.toUpperCase();
            const color = this.getColor(riskData.level);
            el.style.color = color;
            light.style.backgroundColor = color;
            light.style.boxShadow = `0 0 10px ${color}`;
        }
    }
    getColor(level) {
        const l = level.toLowerCase();
        return (l === 'normal' || l === 'low') ? 'var(--success)' : (l === 'moderate' || l === 'medium' ? 'var(--warning)' : 'var(--danger)');
    }
    updateCharts(history) {
        if (!history || !this.charts.wind) return;
        const labels = history.map(d => new Date(d.timestamp).getUTCHours() + ':00');
        this.charts.wind.data.labels = labels;
        this.charts.wind.data.datasets[0].data = history.map(d => d.wind_speed);
        this.charts.wind.update();
        this.charts.mag.data.labels = labels;
        this.charts.mag.data.datasets[0].data = history.map(d => d.bz);
        this.charts.mag.update();
    }
    addLog(msg, type = "info") {
        const log = document.getElementById('action-log');
        if (!log) return;
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        const color = type === 'error' ? 'var(--danger)' : (type === 'warning' ? 'var(--warning)' : 'var(--success)');
        entry.innerHTML = `<span class="time" style="color:${color}">[${new Date().toLocaleTimeString()}]</span> ${msg}`;
        log.prepend(entry);
    }
}
document.addEventListener('DOMContentLoaded', () => { window.app = new Dashboard(); });
/**
 * Institutional Commodity Intelligence Terminal & 20-Year Seasonality Controller
 */

// Global Dashboard State
let currentCommodityCode = "CL";
let dashboardData = {};

document.addEventListener("DOMContentLoaded", () => {
    // Hydrate initial data from server JSON script tag
    const dataEl = document.getElementById("initial-dashboard-data");
    if (dataEl) {
        try {
            dashboardData = JSON.parse(dataEl.textContent);
            currentCommodityCode = dashboardData.code || "CL";
        } catch (e) {
            console.error("Failed to parse initial dashboard data:", e);
        }
    }

    // Initialize sub-tabs
    initSubTabs();

    // Initialize sector filter
    initSectorFilter();

    // Render Seasonality DOY Chart
    if (dashboardData.doy_points && dashboardData.doy_points.length > 0) {
        renderSeasonalitySvgChart(dashboardData.doy_points);
    }

    // Render Forward Curve M1-M24 Chart
    if (dashboardData.contracts && dashboardData.contracts.length > 0) {
        renderForwardCurveSvgChart(dashboardData.contracts);
    }
});

/**
 * Tab Navigation Controller
 */
function initSubTabs() {
    const tabButtons = document.querySelectorAll(".terminal-nav-tab");
    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetId = btn.getAttribute("data-tab");
            
            tabButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            document.querySelectorAll(".terminal-tab-panel").forEach(panel => {
                panel.style.display = "none";
            });

            const activePanel = document.getElementById(targetId);
            if (activePanel) {
                activePanel.style.display = "block";
            }
        });
    });
}

/**
 * Sector Filter Controller
 */
function initSectorFilter() {
    const sectorBtns = document.querySelectorAll(".sector-tab-btn");
    const commPills = document.querySelectorAll(".comm-pill-btn");

    sectorBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const sector = btn.getAttribute("data-sector");
            sectorBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            commPills.forEach(pill => {
                const pillSector = pill.getAttribute("data-sector");
                if (sector === "ALL" || pillSector === sector) {
                    pill.style.display = "inline-flex";
                } else {
                    pill.style.display = "none";
                }
            });
        });
    });
}

/**
 * Switch Commodity Dynamically
 */
function selectCommodity(code) {
    if (code === currentCommodityCode) return;
    
    // Smooth URL update
    const url = new URL(window.location);
    url.searchParams.set("commodity", code);
    window.location.href = url.toString();
}

/**
 * Render Vectorized Day-of-Year Seasonality SVG Chart
 */
function renderSeasonalitySvgChart(points) {
    const svg = document.getElementById("seasonalitySvgChart");
    if (!svg || !points || points.length === 0) return;

    const width = 960;
    const height = 360;
    const padding = { top: 30, right: 40, bottom: 45, left: 65 };

    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    // Find min and max normalized values
    let allVals = [];
    points.forEach(p => {
        if (p.p10 !== null) allVals.push(p.p10);
        if (p.p90 !== null) allVals.push(p.p90);
        if (p.med20 !== null) allVals.push(p.med20);
        if (p.med10 !== null) allVals.push(p.med10);
        if (p.med5 !== null) allVals.push(p.med5);
        if (p.curr !== null) allVals.push(p.curr);
    });

    const minVal = Math.min(...allVals, 90);
    const maxVal = Math.max(...allVals, 115);
    const valRange = maxVal - minVal || 1;

    const scaleX = (doy) => padding.left + ((doy - 1) / 364) * chartW;
    const scaleY = (val) => padding.top + chartH - ((val - minVal) / valRange) * chartH;

    let svgHtml = `
        <defs>
            <linearGradient id="envelopeGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#8b5cf6" stop-opacity="0.25"/>
                <stop offset="100%" stop-color="#00f2fe" stop-opacity="0.05"/>
            </linearGradient>
            <linearGradient id="currentYearGlow" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#00f2fe"/>
                <stop offset="100%" stop-color="#10b981"/>
            </linearGradient>
            <filter id="neonGlow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
        </defs>
    `;

    // Horizontal Grid Lines & Y-Axis Labels
    const numYGrid = 6;
    for (let i = 0; i <= numYGrid; i++) {
        const val = minVal + (valRange * (i / numYGrid));
        const y = scaleY(val);
        svgHtml += `
            <line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="rgba(255, 255, 255, 0.06)" stroke-dasharray="4 4" />
            <text x="${padding.left - 10}" y="${y + 4}" fill="#64748b" font-family="'JetBrains Mono', monospace" font-size="10" text-anchor="end">${val.toFixed(1)}</text>
        `;
    }

    // Base 100 Reference Line
    if (minVal <= 100 && maxVal >= 100) {
        const y100 = scaleY(100);
        svgHtml += `
            <line x1="${padding.left}" y1="${y100}" x2="${width - padding.right}" y2="${y100}" stroke="rgba(255, 255, 255, 0.22)" stroke-width="1.5" />
            <text x="${width - padding.right + 8}" y="${y100 + 3}" fill="#94a3b8" font-family="'JetBrains Mono', monospace" font-size="10">BASE 100</text>
        `;
    }

    // Month X-Axis Boundaries & Labels
    const months = [
        { name: "Jan", doy: 1 }, { name: "Feb", doy: 32 }, { name: "Mar", doy: 60 },
        { name: "Apr", doy: 91 }, { name: "May", doy: 121 }, { name: "Jun", doy: 152 },
        { name: "Jul", doy: 182 }, { name: "Aug", doy: 213 }, { name: "Sep", doy: 244 },
        { name: "Oct", doy: 274 }, { name: "Nov", doy: 305 }, { name: "Dec", doy: 335 },
    ];

    months.forEach((m) => {
        const x = scaleX(m.doy);
        svgHtml += `
            <line x1="${x}" y1="${padding.top}" x2="${x}" y2="${padding.top + chartH}" stroke="rgba(255, 255, 255, 0.05)" stroke-width="1" />
            <text x="${x + (chartW / 24)}" y="${height - 15}" fill="#94a3b8" font-family="'JetBrains Mono', monospace" font-size="10" text-anchor="middle">${m.name}</text>
        `;
    });

    // 1. Shaded 25th - 75th Percentile Envelope
    let envTop = [];
    let envBottom = [];
    points.forEach(p => {
        envTop.push(`${scaleX(p.doy)},${scaleY(p.p75)}`);
        envBottom.unshift(`${scaleX(p.doy)},${scaleY(p.p25)}`);
    });
    const envPoints = envTop.concat(envBottom).join(" ");
    svgHtml += `<polygon points="${envPoints}" fill="url(#envelopeGrad)" />`;

    // 2. 5-Year Median Path (Cyan line)
    const pts5 = points.map(p => `${scaleX(p.doy)},${scaleY(p.med5)}`).join(" ");
    svgHtml += `<polyline points="${pts5}" fill="none" stroke="#00f2fe" stroke-width="1.5" stroke-dasharray="3 3" opacity="0.65" />`;

    // 3. 10-Year Median Path (Purple dash line)
    const pts10 = points.map(p => `${scaleX(p.doy)},${scaleY(p.med10)}`).join(" ");
    svgHtml += `<polyline points="${pts10}" fill="none" stroke="#a855f7" stroke-width="1.8" stroke-dasharray="6 4" opacity="0.8" />`;

    // 4. 20-Year Median Path (Gold/Amber Master Benchmark)
    const pts20 = points.map(p => `${scaleX(p.doy)},${scaleY(p.med20)}`).join(" ");
    svgHtml += `<polyline points="${pts20}" fill="none" stroke="#f59e0b" stroke-width="2.5" />`;

    // 5. Current Year Realized Path (Glowing Neon Gradient)
    const currentPts = points.filter(p => p.curr !== null).map(p => `${scaleX(p.doy)},${scaleY(p.curr)}`).join(" ");
    if (currentPts) {
        svgHtml += `<polyline points="${currentPts}" fill="none" stroke="url(#currentYearGlow)" stroke-width="3.2" filter="url(#neonGlow)" />`;
        
        // Latest point pulsing marker
        const lastCurr = points.filter(p => p.curr !== null).pop();
        if (lastCurr) {
            const lx = scaleX(lastCurr.doy);
            const ly = scaleY(lastCurr.curr);
            svgHtml += `
                <circle cx="${lx}" cy="${ly}" r="6" fill="#00f2fe" opacity="0.4">
                    <animate attributeName="r" values="5;9;5" dur="2s" repeatCount="indefinite" />
                    <animate attributeName="opacity" values="0.6;0.1;0.6" dur="2s" repeatCount="indefinite" />
                </circle>
                <circle cx="${lx}" cy="${ly}" r="4" fill="#ffffff" stroke="#00f2fe" stroke-width="2" />
            `;
        }
    }

    svg.innerHTML = svgHtml;
}

/**
 * Render Forward Curve Strip M1-M24 SVG Chart
 */
function renderForwardCurveSvgChart(contracts) {
    const svg = document.getElementById("forwardCurveSvgChart");
    if (!svg || !contracts || contracts.length === 0) return;

    const width = 960;
    const height = 300;
    const padding = { top: 25, right: 55, bottom: 40, left: 65 };

    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    const prices = contracts.map(c => c.settlement_price);
    const minP = Math.min(...prices) * 0.98;
    const maxP = Math.max(...prices) * 1.02;
    const pRange = maxP - minP || 1;

    const scaleX = (idx) => padding.left + (idx / (contracts.length - 1 || 1)) * chartW;
    const scaleY = (p) => padding.top + chartH - ((p - minP) / pRange) * chartH;

    let svgHtml = `
        <defs>
            <linearGradient id="curveGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#00f2fe" stop-opacity="0.3"/>
                <stop offset="100%" stop-color="#3b82f6" stop-opacity="0.0"/>
            </linearGradient>
        </defs>
    `;

    // Horizontal Price Lines
    for (let i = 0; i <= 4; i++) {
        const val = minP + (pRange * (i / 4));
        const y = scaleY(val);
        svgHtml += `
            <line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="rgba(255, 255, 255, 0.06)" stroke-dasharray="4 4" />
            <text x="${padding.left - 10}" y="${y + 4}" fill="#64748b" font-family="'JetBrains Mono', monospace" font-size="10" text-anchor="end">${val.toFixed(2)}</text>
        `;
    }

    // Points & Polygon Area
    const curvePoints = contracts.map((c, i) => `${scaleX(i)},${scaleY(c.settlement_price)}`);
    const areaPoints = `${scaleX(0)},${padding.top + chartH} ` + curvePoints.join(" ") + ` ${scaleX(contracts.length - 1)},${padding.top + chartH}`;

    svgHtml += `<polygon points="${areaPoints}" fill="url(#curveGrad)" />`;
    svgHtml += `<polyline points="${curvePoints.join(' ')}" fill="none" stroke="#00f2fe" stroke-width="2.5" />`;

    // Contract nodes and Tenor X Labels
    contracts.forEach((c, i) => {
        const x = scaleX(i);
        const y = scaleY(c.settlement_price);

        svgHtml += `
            <circle cx="${x}" cy="${y}" r="4" fill="#0c1022" stroke="#00f2fe" stroke-width="2" />
            <text x="${x}" y="${height - 12}" fill="#94a3b8" font-family="'JetBrains Mono', monospace" font-size="9" text-anchor="middle">${c.tenor}</text>
        `;
    });

    svg.innerHTML = svgHtml;
}

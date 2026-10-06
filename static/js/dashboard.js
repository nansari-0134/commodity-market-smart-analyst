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

    // Initialize 40-Method Institutional Seasonality Matrix & Visual Workbench
    initSeasonality40Matrix();
    initSeasonalityWorkbench();

    // Initialize Interactive TradingView Lightweight Charts Stage
    initLightweightChart();

    // Initialize Real-Time Live Quote Telemetry & Auto-Polling
    initLiveQuoteTelemetry();
});


/**
 * Terminal Command Deck & View Mode Controller
 */
let terminalDeckMode = localStorage.getItem("terminalDeckMode") || "deck";

function setTerminalDeckMode(mode) {
    terminalDeckMode = mode;
    localStorage.setItem("terminalDeckMode", mode);

    const btnDeck = document.getElementById("btnModeDeck");
    const btnTabs = document.getElementById("btnModeTabs");
    if (btnDeck) btnDeck.classList.toggle("active", mode === "deck");
    if (btnTabs) btnTabs.classList.toggle("active", mode === "tabs");

    const panels = document.querySelectorAll(".terminal-tab-panel");

    if (mode === "deck") {
        panels.forEach(panel => {
            panel.style.display = "block";
        });
        if (typeof renderForwardCurveSvgChart === "function" && dashboardData && dashboardData.contracts) {
            renderForwardCurveSvgChart(dashboardData.contracts);
        }
    } else {
        const activeTab = document.querySelector(".terminal-nav-tab.active");
        const activeId = activeTab ? activeTab.getAttribute("data-tab") : "tab-seasonality";
        panels.forEach(panel => {
            panel.style.display = (panel.id === activeId) ? "block" : "none";
        });
        if (activeId === "tab-forward-curve" && typeof renderForwardCurveSvgChart === "function" && dashboardData && dashboardData.contracts) {
            renderForwardCurveSvgChart(dashboardData.contracts);
        }
    }
}

function handleNavTabClick(targetId) {
    const tabButtons = document.querySelectorAll(".terminal-nav-tab");
    tabButtons.forEach(b => {
        b.classList.toggle("active", b.getAttribute("data-tab") === targetId);
    });

    if (terminalDeckMode === "deck") {
        const activePanel = document.getElementById(targetId);
        if (activePanel) {
            activePanel.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    } else {
        document.querySelectorAll(".terminal-tab-panel").forEach(panel => {
            panel.style.display = (panel.id === targetId) ? "block" : "none";
        });
        if (targetId === "tab-forward-curve" && typeof renderForwardCurveSvgChart === "function" && dashboardData && dashboardData.contracts) {
            renderForwardCurveSvgChart(dashboardData.contracts);
        }
    }
}

function initSubTabs() {
    window.setTerminalDeckMode = setTerminalDeckMode;
    window.handleNavTabClick = handleNavTabClick;

    const tabButtons = document.querySelectorAll(".terminal-nav-tab");
    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetId = btn.getAttribute("data-tab");
            handleNavTabClick(targetId);
        });
    });

    // Apply saved or default deck mode on load
    setTerminalDeckMode(terminalDeckMode);
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

/**
 * Switch Sub-View inside Quantitative Seasonality Engine & Empirical Matrix
 * ('view-workbench', 'view-heatmap', 'view-both')
 */
function switchS40View(viewId) {
    const tabs = document.querySelectorAll("#s40ViewTabs .s40-view-tab");
    tabs.forEach(t => t.classList.toggle("active", t.getAttribute("data-view") === viewId));

    const wbPane = document.getElementById("view-workbench");
    const heatPane = document.getElementById("view-heatmap");

    if (viewId === "view-workbench") {
        if (wbPane) wbPane.style.display = "block";
        if (heatPane) heatPane.style.display = "none";
    } else if (viewId === "view-heatmap") {
        if (wbPane) wbPane.style.display = "none";
        if (heatPane) heatPane.style.display = "block";
    } else if (viewId === "view-both") {
        if (wbPane) wbPane.style.display = "block";
        if (heatPane) heatPane.style.display = "block";
    }
}
window.switchS40View = switchS40View;

/**
 * Quantitative Seasonality Engine & Empirical Matrix Controller
 */
function initSeasonality40Matrix() {
    const filterPills = document.querySelectorAll("#s40SectionFilters .s40-pill");
    const searchInput = document.getElementById("s40SearchInput");
    const select = document.getElementById("wbMethodSelect");

    let currentSection = "ALL";
    let searchQuery = "";

    function filterMethods() {
        const query = searchQuery.trim().toLowerCase();
        const methods = (dashboardData.seasonality_40 && dashboardData.seasonality_40.methods) || [];
        let firstMatch = null;

        if (select) {
            const optgroups = select.querySelectorAll("optgroup");
            optgroups.forEach(group => {
                let groupHasVisibleOption = false;
                const options = group.querySelectorAll("option");
                options.forEach(opt => {
                    const num = parseInt(opt.value, 10);
                    const m = methods.find(item => item.number === num);
                    if (!m) return;

                    const matchesSection = (currentSection === "ALL" || m.section === currentSection);
                    const textToSearch = `${m.name} ${m.why_it_matters} ${m.status} ${m.formula_summary} ${m.section} #${m.number}`.toLowerCase();
                    const matchesQuery = !query || textToSearch.includes(query);

                    if (matchesSection && matchesQuery) {
                        opt.hidden = false;
                        opt.disabled = false;
                        opt.style.display = "";
                        groupHasVisibleOption = true;
                        if (!firstMatch) {
                            firstMatch = num;
                        }
                    } else {
                        opt.hidden = true;
                        opt.disabled = true;
                        opt.style.display = "none";
                    }
                });

                group.style.display = groupHasVisibleOption ? "" : "none";
            });

            // If the currently active method is hidden, switch to the first matching method
            const currentSelectedOpt = select.querySelector(`option[value="${activeWorkbenchMethodNumber}"]`);
            if (currentSelectedOpt && (currentSelectedOpt.hidden || currentSelectedOpt.disabled)) {
                if (firstMatch) {
                    selectWorkbenchMethod(firstMatch, false);
                }
            }
        }

        const counterEl = document.getElementById("wbMethodCounter");
        if (counterEl) {
            let matchCount = 0;
            methods.forEach(m => {
                const matchesSection = (currentSection === "ALL" || m.section === currentSection);
                const textToSearch = `${m.name} ${m.why_it_matters} ${m.status} ${m.formula_summary} ${m.section} #${m.number}`.toLowerCase();
                const matchesQuery = !query || textToSearch.includes(query);
                if (matchesSection && matchesQuery) matchCount++;
            });
            counterEl.textContent = `Showing ${matchCount} of ${methods.length} Methods`;
        }
    }

    filterPills.forEach(pill => {
        pill.addEventListener("click", () => {
            filterPills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            currentSection = pill.getAttribute("data-section") || "ALL";
            filterMethods();
        });
    });

    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            searchQuery = e.target.value;
            filterMethods();
        });
    }

    // Escape key closes modal
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            closeSeasonalityInspector();
        }
    });
}

function openSeasonalityInspector(methodNumber) {
    const modal = document.getElementById("s40ModalBackdrop");
    if (!modal) return;

    const methods = (dashboardData.seasonality_40 && dashboardData.seasonality_40.methods) || [];
    const method = methods.find(m => m.number === methodNumber);
    if (!method) return;

    document.getElementById("s40ModalNum").textContent = `#${method.number}`;
    document.getElementById("s40ModalSection").textContent = method.section;
    document.getElementById("s40ModalSection").className = `s40-section-tag s40-badge-${method.section.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
    document.getElementById("s40ModalTitle").textContent = `${method.icon} ${method.name}`;
    
    const statusEl = document.getElementById("s40ModalStatus");
    statusEl.textContent = method.status;
    const isBull = /high|bullish|validated|expanded|persistent/i.test(method.status);
    const isBear = /bearish|contango|overbought|decay/i.test(method.status);
    statusEl.className = `s40-status-pill ${isBull ? "tag-exchange" : isBear ? "tag-pra" : "tag-internal"}`;

    document.getElementById("s40ModalWhy").textContent = method.why_it_matters;
    document.getElementById("s40ModalMetricLbl").textContent = method.headline_label;
    document.getElementById("s40ModalMetricVal").textContent = method.headline_metric;
    document.getElementById("s40ModalMetricType").textContent = `Metric Type: ${method.metric_type}`;
    document.getElementById("s40ModalFormula").textContent = method.formula_summary;

    const paramsPre = document.getElementById("s40ModalParams");
    const paramCount = Object.keys(method.parameters || {}).length;
    document.getElementById("s40ModalParamCount").textContent = `${paramCount} parameters`;
    paramsPre.textContent = JSON.stringify(method.parameters || {}, null, 2);

    modal.style.display = "flex";
    document.body.style.overflow = "hidden";
}

function closeSeasonalityInspector(event) {
    const modal = document.getElementById("s40ModalBackdrop");
    if (modal) {
        modal.style.display = "none";
        document.body.style.overflow = "";
    }
}

function openCurrentMethodInspector() {
    openSeasonalityInspector(activeWorkbenchMethodNumber);
}
window.openCurrentMethodInspector = openCurrentMethodInspector;

function stepWorkbenchMethod(delta) {
    let nextNum = activeWorkbenchMethodNumber + delta;
    if (nextNum < 1) nextNum = 40;
    if (nextNum > 40) nextNum = 1;
    selectWorkbenchMethod(nextNum, false);
}
window.stepWorkbenchMethod = stepWorkbenchMethod;

/* ==============================================================================
   ACTUAL IMPLEMENTATION: 40-Method Interactive Seasonality Workbench
   ============================================================================== */

let activeWorkbenchMethodNumber = 1;

/**
 * Initialize the Seasonality Method Workbench
 */
function initSeasonalityWorkbench() {
    const select = document.getElementById("wbMethodSelect");
    const prevBtn = document.getElementById("wbPrevBtn");
    const nextBtn = document.getElementById("wbNextBtn");

    if (select) {
        select.addEventListener("change", (e) => {
            const num = parseInt(e.target.value, 10);
            selectWorkbenchMethod(num, false);
        });
    }

    if (prevBtn) {
        prevBtn.addEventListener("click", () => {
            let nextNum = activeWorkbenchMethodNumber - 1;
            if (nextNum < 1) nextNum = 40;
            selectWorkbenchMethod(nextNum, true);
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener("click", () => {
            let nextNum = activeWorkbenchMethodNumber + 1;
            if (nextNum > 40) nextNum = 1;
            selectWorkbenchMethod(nextNum, true);
        });
    }

    // Keyboard navigation (ArrowLeft / ArrowRight) when in Seasonality Tab
    document.addEventListener("keydown", (e) => {
        const modal = document.getElementById("s40ModalBackdrop");
        if (modal && modal.style.display === "flex") return;

        const activeTab = document.querySelector(".terminal-nav-tab.active");
        if (!activeTab || activeTab.getAttribute("data-tab") !== "tab-seasonality") return;

        if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "SELECT" || e.target.tagName === "TEXTAREA")) return;

        if (e.key === "ArrowLeft") {
            let nextNum = activeWorkbenchMethodNumber - 1;
            if (nextNum < 1) nextNum = 40;
            selectWorkbenchMethod(nextNum, false);
        } else if (e.key === "ArrowRight") {
            let nextNum = activeWorkbenchMethodNumber + 1;
            if (nextNum > 40) nextNum = 1;
            selectWorkbenchMethod(nextNum, false);
        }
    });

    // Render initial Method #1 on load
    renderSeasonalityWorkbench(1);
}

/**
 * Select and activate a method in the workbench and highlight its card in the 40-grid
 */
function selectWorkbenchMethod(methodNumber, shouldScroll = true) {
    activeWorkbenchMethodNumber = methodNumber;

    const select = document.getElementById("wbMethodSelect");
    if (select && parseInt(select.value, 10) !== methodNumber) {
        select.value = methodNumber;
    }

    // Highlight card in 40-grid if present
    const cards = document.querySelectorAll("#s40CardsGrid .s40-card");
    if (cards.length > 0) {
        cards.forEach(c => {
            const cNum = parseInt(c.getAttribute("data-num"), 10);
            if (cNum === methodNumber) {
                c.classList.add("workbench-active");
            } else {
                c.classList.remove("workbench-active");
            }
        });
    }

    renderSeasonalityWorkbench(methodNumber);

    if (shouldScroll) {
        const wb = document.getElementById("seasonalityWorkbench");
        if (wb) {
            wb.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    }
}

/**
 * Deep parameter inspector for the currently selected workbench method
 */
function openCurrentMethodInspector() {
    openSeasonalityInspector(activeWorkbenchMethodNumber);
}

/**
 * Render the complete visual analytics workbench for a given seasonality method
 */
function renderSeasonalityWorkbench(methodNumber) {
    const methods = (dashboardData.seasonality_40 && dashboardData.seasonality_40.methods) || [];
    const method = methods.find(m => m.number === methodNumber);
    if (!method) return;

    activeWorkbenchMethodNumber = method.number;
    const viz = method.visualization || {};

    // 1. Header & Breadcrumbs
    const numEl = document.getElementById("wbMethodNum");
    if (numEl) numEl.textContent = `#${method.number}`;

    const badgeEl = document.getElementById("wbSectionBadge");
    if (badgeEl) {
        badgeEl.textContent = method.section;
        badgeEl.className = `s40-section-tag s40-badge-${method.section.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
    }

    const statusEl = document.getElementById("wbStatusPill");
    if (statusEl) {
        statusEl.textContent = method.status;
        const isBull = /high|bullish|validated|expanded|persistent/i.test(method.status);
        const isBear = /bearish|contango|overbought|decay/i.test(method.status);
        statusEl.className = `s40-status-pill ${isBull ? "tag-exchange" : isBear ? "tag-pra" : "tag-internal"}`;
    }

    const titleEl = document.getElementById("wbMethodTitle");
    if (titleEl) titleEl.innerHTML = `<span>${method.icon}</span> ${method.name}`;

    // 2. Narrative & Formula
    const whyEl = document.getElementById("wbWhyText");
    if (whyEl) whyEl.textContent = method.why_it_matters;

    const formEl = document.getElementById("wbFormulaText");
    if (formEl) formEl.textContent = method.formula_summary;

    // 3. Chart Header & Legend
    const chartTitleEl = document.getElementById("wbChartTitle");
    if (chartTitleEl) {
        chartTitleEl.innerHTML = `<span>📊</span> ${viz.chart_title || method.name}`;
    }

    const chartSubEl = document.getElementById("wbChartSubtitle");
    if (chartSubEl) {
        chartSubEl.textContent = `${method.section} Lens • Point-in-Time Quantitative Visualization • Y-Axis: ${viz.y_axis_label || 'Value'}`;
    }

    const legendEl = document.getElementById("wbChartLegend");
    if (legendEl) {
        const seriesList = viz.series || [];
        legendEl.innerHTML = seriesList.map(s => `
            <span class="wb-legend-item">
                <span class="wb-legend-dot" style="background:${s.color || '#00f2fe'};"></span>
                <span>${s.name}</span>
            </span>
        `).join("");
    }

    // 4. Render SVG Chart
    const svg = document.getElementById("workbenchSvgChart");
    if (svg) {
        drawWorkbenchChart(svg, viz);
    }

    // 5. KPIs Grid
    const kpiGrid = document.getElementById("wbKpisGrid");
    if (kpiGrid) {
        const kpis = viz.kpis || [
            { label: method.headline_label, val: method.headline_metric, badge: "tag-exchange" }
        ];
        kpiGrid.innerHTML = kpis.map(k => `
            <div class="wb-kpi-tile">
                <div class="wb-kpi-lbl">${k.label}</div>
                <div class="wb-kpi-val" style="color: ${k.color || '#ffffff'};">${k.val}</div>
                ${k.badge ? `<span class="badge-tag ${k.badge}" style="font-size:0.62rem; align-self:flex-start; margin-top:0.3rem;">VERIFIED</span>` : ''}
            </div>
        `).join("");
    }

    // 6. Institutional Takeaway
    const takeEl = document.getElementById("wbTakeawayText");
    if (takeEl) {
        takeEl.textContent = viz.institutional_takeaway || method.subtext || method.why_it_matters;
    }

    // 7. Empirical Data Table
    const tableHead = document.getElementById("wbTableHead");
    const tableBody = document.getElementById("wbTableBody");
    const rowCountEl = document.getElementById("wbTableRowCount");

    if (tableHead && tableBody) {
        const headers = viz.table_headers || ["Metric", "Value"];
        const rows = viz.table_rows || [];

        tableHead.innerHTML = `<tr>${headers.map(h => `<th>${h}</th>`).join("")}</tr>`;
        tableBody.innerHTML = rows.map(r => `
            <tr>
                ${r.map((cell, idx) => {
                    const isFirst = idx === 0;
                    const cellStr = String(cell);
                    let colorStyle = "";
                    if (cellStr.startsWith("+")) colorStyle = "color: var(--accent-emerald); font-weight: 600;";
                    else if (cellStr.startsWith("-") && !cellStr.startsWith("--")) colorStyle = "color: var(--accent-rose); font-weight: 600;";
                    else if (isFirst) colorStyle = "color: var(--accent-cyan); font-weight: 700;";
                    return `<td style="font-family: var(--font-mono); ${colorStyle}">${cell}</td>`;
                }).join("")}
            </tr>
        `).join("");

        if (rowCountEl) {
            rowCountEl.textContent = `${rows.length} OBSERVATIONS`;
        }
    }
}

/**
 * Universal SVG Chart Renderer for all 40 Seasonality Methods
 */
function drawWorkbenchChart(svg, viz) {
    if (!svg || !viz) return;

    const width = 960;
    const height = 320;
    const padding = { top: 30, right: 45, bottom: 45, left: 65 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    const chartType = viz.chart_type || "bar";
    const xLabels = viz.x_labels || [];
    const series = viz.series || [];
    const n = Math.max(1, xLabels.length);

    // Collect all numerical data points to compute min and max
    let allValues = [];
    series.forEach(s => {
        if (Array.isArray(s.data)) {
            s.data.forEach(v => {
                if (typeof v === "number" && !isNaN(v)) allValues.push(v);
            });
        }
    });

    if (allValues.length === 0) allValues = [0, 100];

    let minV = Math.min(...allValues);
    let maxV = Math.max(...allValues);

    // If zero is near or data is centered around zero, anchor scale to include 0
    if (chartType === "bar" || chartType === "grouped_bar" || chartType === "correlogram" || chartType === "underwater_curve") {
        if (minV > 0) minV = 0;
        if (maxV < 0) maxV = 0;
    }

    if (minV === maxV) {
        minV -= 1;
        maxV += 1;
    }

    // Add 8% vertical headroom
    const vRange = maxV - minV;
    minV -= vRange * 0.08;
    maxV += vRange * 0.08;
    const totalRange = maxV - minV || 1;

    // Coordinate scalers
    const scaleX = (idx) => padding.left + (idx / Math.max(1, n - 1)) * chartW;
    const slotW = chartW / n;
    const slotCenter = (idx) => padding.left + idx * slotW + slotW / 2;
    const scaleY = (v) => padding.top + chartH - ((v - minV) / totalRange) * chartH;
    const zeroY = Math.max(padding.top, Math.min(padding.top + chartH, scaleY(0)));

    let svgHtml = `
        <defs>
            <linearGradient id="wbGradArea" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#00f2fe" stop-opacity="0.3"/>
                <stop offset="100%" stop-color="#00f2fe" stop-opacity="0.0"/>
            </linearGradient>
            <linearGradient id="wbGradRose" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#f43f5e" stop-opacity="0.0"/>
                <stop offset="100%" stop-color="#f43f5e" stop-opacity="0.35"/>
            </linearGradient>
            <linearGradient id="wbGradEmerald" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#10b981" stop-opacity="0.35"/>
                <stop offset="100%" stop-color="#10b981" stop-opacity="0.0"/>
            </linearGradient>
            <filter id="wbNeon" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
        </defs>
    `;

    // 1. Horizontal Grid Lines & Y-Axis Labels
    const numGridLines = 5;
    for (let i = 0; i <= numGridLines; i++) {
        const val = minV + (totalRange * (i / numGridLines));
        const y = scaleY(val);

        let formattedVal = val.toFixed(1);
        if (Math.abs(val) >= 1000) formattedVal = (val / 1000).toFixed(1) + "k";
        else if (Math.abs(val) < 1 && val !== 0) formattedVal = val.toFixed(2);

        svgHtml += `
            <line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="rgba(255, 255, 255, 0.06)" stroke-dasharray="4 4" />
            <text x="${padding.left - 10}" y="${y + 3.5}" fill="#64748b" font-family="'JetBrains Mono', monospace" font-size="10" text-anchor="end">${formattedVal}</text>
        `;
    }

    // 2. Zero Axis Reference Line (if 0 is within range)
    if (minV < 0 && maxV > 0) {
        svgHtml += `
            <line x1="${padding.left}" y1="${zeroY}" x2="${width - padding.right}" y2="${zeroY}" stroke="rgba(255, 255, 255, 0.28)" stroke-width="1.2" />
        `;
    }

    // 3. X-Axis Labels (adaptive step so labels don't collide)
    const labelStep = n > 24 ? Math.ceil(n / 12) : (n > 15 ? 2 : 1);
    for (let i = 0; i < n; i += labelStep) {
        const xPos = (chartType === "bar" || chartType === "grouped_bar" || chartType === "correlogram") ? slotCenter(i) : scaleX(i);
        const lbl = xLabels[i] || "";
        svgHtml += `
            <line x1="${xPos}" y1="${padding.top + chartH}" x2="${xPos}" y2="${padding.top + chartH + 5}" stroke="rgba(255, 255, 255, 0.15)" />
            <text x="${xPos}" y="${height - 12}" fill="#94a3b8" font-family="'JetBrains Mono', monospace" font-size="9" text-anchor="middle">${lbl}</text>
        `;
    }

    // 4. Render Specialized Chart Geometries
    if (chartType === "bar" || chartType === "correlogram") {
        const s0 = series[0] || { data: [], color: "#00f2fe" };
        const dataArr = s0.data || [];
        const bw = Math.min(48, Math.max(12, slotW * 0.65));

        dataArr.forEach((val, i) => {
            const cx = slotCenter(i);
            const bx = cx - bw / 2;
            const y = scaleY(val);
            const by = Math.min(zeroY, y);
            const bh = Math.max(3, Math.abs(zeroY - y));

            let barColor = s0.color || "#00f2fe";
            if (val > 0) barColor = "#10b981";
            else if (val < 0) barColor = "#f43f5e";

            svgHtml += `
                <rect x="${bx}" y="${by}" width="${bw}" height="${bh}" rx="3" fill="${barColor}" opacity="0.88">
                    <title>${xLabels[i] || ''}: ${val > 0 ? '+' : ''}${val.toFixed(2)}</title>
                </rect>
            `;

            // Small value callout if bars aren't too crowded
            if (n <= 16) {
                const textY = val >= 0 ? by - 5 : by + bh + 12;
                svgHtml += `
                    <text x="${cx}" y="${textY}" fill="#e2e8f0" font-family="'JetBrains Mono', monospace" font-size="8.5" text-anchor="middle">
                        ${val > 0 ? '+' : ''}${val.toFixed(1)}
                    </text>
                `;
            }
        });

        // Correlogram 95% Confidence threshold dashed lines
        if (chartType === "correlogram") {
            const confVal = 1.96 / Math.sqrt(20 * 12); // ~0.126
            const yPosConf = scaleY(confVal);
            const yNegConf = scaleY(-confVal);
            svgHtml += `
                <line x1="${padding.left}" y1="${yPosConf}" x2="${width - padding.right}" y2="${yPosConf}" stroke="#f59e0b" stroke-dasharray="5 3" stroke-width="1.5" opacity="0.9" />
                <line x1="${padding.left}" y1="${yNegConf}" x2="${width - padding.right}" y2="${yNegConf}" stroke="#f59e0b" stroke-dasharray="5 3" stroke-width="1.5" opacity="0.9" />
                <text x="${width - padding.right}" y="${yPosConf - 4}" fill="#f59e0b" font-family="'JetBrains Mono', monospace" font-size="8" text-anchor="end">+95% CONFIDENCE (p < 0.05)</text>
                <text x="${width - padding.right}" y="${yNegConf + 11}" fill="#f59e0b" font-family="'JetBrains Mono', monospace" font-size="8" text-anchor="end">-95% CONFIDENCE (p < 0.05)</text>
            `;
        }

    } else if (chartType === "grouped_bar") {
        const numSeries = series.length;
        const bw = Math.min(26, Math.max(8, (slotW * 0.72) / numSeries));
        const groupW = numSeries * bw + (numSeries - 1) * 2;

        for (let i = 0; i < n; i++) {
            const startX = slotCenter(i) - groupW / 2;

            series.forEach((s, sIdx) => {
                const val = (s.data && s.data[i] !== undefined) ? s.data[i] : 0;
                const bx = startX + sIdx * (bw + 2);
                const y = scaleY(val);
                const by = Math.min(zeroY, y);
                const bh = Math.max(2, Math.abs(zeroY - y));

                svgHtml += `
                    <rect x="${bx}" y="${by}" width="${bw}" height="${bh}" rx="2" fill="${s.color || '#00f2fe'}" opacity="0.9">
                        <title>${s.name} (${xLabels[i]}): ${val.toFixed(2)}</title>
                    </rect>
                `;
            });
        }

    } else if (chartType === "range_area") {
        // Upper band, Lower band, and median/realized series
        if (series.length >= 2) {
            const sUpper = series[0];
            const sLower = series[1];
            const upPts = (sUpper.data || []).map((v, i) => `${scaleX(i)},${scaleY(v)}`);
            const lowPts = (sLower.data || []).map((v, i) => `${scaleX(i)},${scaleY(v)}`).reverse();
            const polyPoints = upPts.join(" ") + " " + lowPts.join(" ");

            svgHtml += `
                <polygon points="${polyPoints}" fill="${sUpper.color || '#00f2fe'}" opacity="0.16" />
                <polyline points="${upPts.join(' ')}" fill="none" stroke="${sUpper.color || '#00f2fe'}" stroke-width="1.2" stroke-dasharray="4 3" opacity="0.6" />
                <polyline points="${(sLower.data || []).map((v, i) => `${scaleX(i)},${scaleY(v)}`).join(' ')}" fill="none" stroke="${sLower.color || '#00f2fe'}" stroke-width="1.2" stroke-dasharray="4 3" opacity="0.6" />
            `;
        }

        // Render remaining series (e.g. median and current realized path)
        series.slice(2).forEach(s => {
            const pts = (s.data || []).map((v, i) => `${scaleX(i)},${scaleY(v)}`).join(" ");
            const isNeon = s.name.toLowerCase().includes("current") || s.name.toLowerCase().includes("realized");
            svgHtml += `
                <polyline points="${pts}" fill="none" stroke="${s.color || '#ffffff'}" stroke-width="${isNeon ? 3.2 : 2.2}" ${isNeon ? 'filter="url(#wbNeon)"' : ''} />
            `;
        });

    } else if (chartType === "equity_curve" || chartType === "underwater_curve") {
        const s0 = series[0] || { data: [], color: "#10b981" };
        const dataArr = s0.data || [];
        const pts = dataArr.map((v, i) => `${scaleX(i)},${scaleY(v)}`).join(" ");
        const gradId = chartType === "underwater_curve" ? "wbGradRose" : "wbGradEmerald";
        const areaPts = `${scaleX(0)},${zeroY} ` + pts + ` ${scaleX(dataArr.length - 1)},${zeroY}`;

        svgHtml += `
            <polygon points="${areaPts}" fill="url(#${gradId})" />
            <polyline points="${pts}" fill="none" stroke="${s0.color || (chartType === 'underwater_curve' ? '#f43f5e' : '#10b981')}" stroke-width="2.6" />
        `;

        // Render high-watermark or benchmark if present
        if (series.length > 1) {
            const sBench = series[1];
            const benchPts = (sBench.data || []).map((v, i) => `${scaleX(i)},${scaleY(v)}`).join(" ");
            svgHtml += `
                <polyline points="${benchPts}" fill="none" stroke="${sBench.color || '#94a3b8'}" stroke-width="1.5" stroke-dasharray="5 4" opacity="0.75" />
            `;
        }

    } else {
        // "line", "multi_line", "area_line"
        series.forEach((s, sIdx) => {
            const dataArr = s.data || [];
            const pts = dataArr.map((v, i) => `${scaleX(i)},${scaleY(v)}`).join(" ");

            if (chartType === "area_line" || s.fill) {
                const areaPts = `${scaleX(0)},${zeroY} ` + pts + ` ${scaleX(dataArr.length - 1)},${zeroY}`;
                svgHtml += `<polygon points="${areaPts}" fill="url(#wbGradArea)" />`;
            }

            const isCurrent = s.name.toLowerCase().includes("current") || s.name.toLowerCase().includes("2026");
            svgHtml += `
                <polyline points="${pts}" fill="none" stroke="${s.color || '#00f2fe'}" stroke-width="${isCurrent ? 3.0 : (s.width || 2.2)}" ${isCurrent ? 'filter="url(#wbNeon)"' : ''} ${s.dashed ? 'stroke-dasharray="6 4"' : ''} />
            `;

            // Draw nodes if points are manageable
            if (dataArr.length <= 25) {
                dataArr.forEach((v, i) => {
                    svgHtml += `
                        <circle cx="${scaleX(i)}" cy="${scaleY(v)}" r="3.5" fill="#0c1022" stroke="${s.color || '#00f2fe'}" stroke-width="2">
                            <title>${s.name} (${xLabels[i]}): ${v}</title>
                        </circle>
                    `;
                });
            }
        });
    }

    svg.innerHTML = svgHtml;
}


/* =========================================================================
   PART 2: INTERACTIVE TRADINGVIEW LIGHTWEIGHT CHARTS & TELEMETRY ENGINE
   ========================================================================= */

// Global Chart References
let tvChart = null;
let tvCandleSeries = null;
let tvAreaSeries = null;
let tvLineSeries = null;
let tvVolumeSeries = null;
let tvOiSeries = null;
let tvActiveTimeframe = "1Y";
let tvActiveChartType = "candles";
let tvCandleData = [];
let isVolumeVisible = true;
let isOiVisible = true;
let livePollInterval = null;

/**
 * Deduplicate, clean, and chronologically sort historical candles
 */
function prepareCandleData(rawCandles) {
    if (!rawCandles || !Array.isArray(rawCandles)) return [];

    const candleMap = new Map();
    rawCandles.forEach(c => {
        if (!c || !c.time) return;
        const t = typeof c.time === "string" ? c.time.split("T")[0] : c.time;
        candleMap.set(t, {
            time: t,
            open: Number(c.open),
            high: Number(c.high),
            low: Number(c.low),
            close: Number(c.close),
            volume: Number(c.volume || 0),
            open_interest: Number(c.open_interest || 0)
        });
    });

    const sorted = Array.from(candleMap.values()).sort((a, b) => (a.time > b.time ? 1 : -1));
    return sorted;
}

/**
 * Update the 60fps Interactive Crosshair Telemetry HUD
 */
function updateCrosshairHud(candle) {
    if (!candle) return;
    const hudDate = document.getElementById("hudDate");
    const hudOpen = document.getElementById("hudOpen");
    const hudHigh = document.getElementById("hudHigh");
    const hudLow = document.getElementById("hudLow");
    const hudClose = document.getElementById("hudClose");
    const hudChg = document.getElementById("hudChg");
    const hudVol = document.getElementById("hudVol");
    const hudOi = document.getElementById("hudOi");

    if (hudDate) hudDate.textContent = candle.time || "--";
    if (hudOpen) hudOpen.textContent = candle.open !== undefined ? Number(candle.open).toFixed(2) : "--";
    if (hudHigh) hudHigh.textContent = candle.high !== undefined ? Number(candle.high).toFixed(2) : "--";
    if (hudLow) hudLow.textContent = candle.low !== undefined ? Number(candle.low).toFixed(2) : "--";
    if (hudClose) hudClose.textContent = candle.close !== undefined ? Number(candle.close).toFixed(2) : "--";

    if (hudChg && candle.open && candle.close) {
        const diff = candle.close - candle.open;
        const pct = (diff / candle.open) * 100;
        hudChg.textContent = `${diff >= 0 ? '+' : ''}${diff.toFixed(2)} (${diff >= 0 ? '+' : ''}${pct.toFixed(2)}%)`;
        hudChg.className = `hud-val ${diff >= 0 ? 'pos' : 'neg'}`;
    }

    if (hudVol) {
        const vol = candle.volume || 0;
        hudVol.textContent = vol.toLocaleString();
    }
    if (hudOi) {
        const oi = candle.open_interest || 0;
        hudOi.textContent = oi.toLocaleString();
    }
}

/**
 * Apply Timeframe Zoom Window
 */
function applyTimeframe(tf) {
    if (!tvChart || tvCandleData.length === 0) return;
    tvActiveTimeframe = tf;

    const tfButtons = document.querySelectorAll("#tvTimeframeGroup .chart-tool-btn");
    tfButtons.forEach(b => b.classList.toggle("active", b.getAttribute("data-tf") === tf));

    if (tf === "ALL") {
        tvChart.timeScale().fitContent();
        return;
    }

    const lastCandle = tvCandleData[tvCandleData.length - 1];
    const lastDate = new Date(lastCandle.time);
    const fromDate = new Date(lastDate);

    if (tf === "1M") fromDate.setMonth(fromDate.getMonth() - 1);
    else if (tf === "3M") fromDate.setMonth(fromDate.getMonth() - 3);
    else if (tf === "6M") fromDate.setMonth(fromDate.getMonth() - 6);
    else if (tf === "1Y") fromDate.setFullYear(fromDate.getFullYear() - 1);
    else if (tf === "5Y") fromDate.setFullYear(fromDate.getFullYear() - 5);

    const fromStr = fromDate.toISOString().split("T")[0];
    const toStr = lastCandle.time;

    tvChart.timeScale().setVisibleRange({
        from: fromStr,
        to: toStr
    });
}

/**
 * Switch Chart Style (Candles, Area, Line)
 */
function switchChartType(type) {
    tvActiveChartType = type;
    const typeButtons = document.querySelectorAll("#tvChartTypeGroup .chart-tool-btn");
    typeButtons.forEach(b => b.classList.toggle("active", b.getAttribute("data-type") === type));

    if (tvCandleSeries) tvCandleSeries.applyOptions({ visible: type === "candles" });
    if (tvAreaSeries) tvAreaSeries.applyOptions({ visible: type === "area" });
    if (tvLineSeries) tvLineSeries.applyOptions({ visible: type === "line" });
}

/**
 * Toggle Volume Histogram Overlay
 */
function toggleVolumeOverlay() {
    isVolumeVisible = !isVolumeVisible;
    if (tvVolumeSeries) tvVolumeSeries.applyOptions({ visible: isVolumeVisible });
    const btn = document.getElementById("btnToggleVolume");
    if (btn) {
        btn.classList.toggle("active", isVolumeVisible);
        btn.classList.toggle("active-green", isVolumeVisible);
    }
}

/**
 * Toggle Open Interest (OI) Overlay Line
 */
function toggleOiOverlay() {
    isOiVisible = !isOiVisible;
    if (tvOiSeries) tvOiSeries.applyOptions({ visible: isOiVisible });
    const btn = document.getElementById("btnToggleOi");
    if (btn) {
        btn.classList.toggle("active", isOiVisible);
    }
}

/**
 * Mount and render TradingView Lightweight Charts
 */
function initLightweightChart() {
    const container = document.getElementById("tvChartContainer");
    if (!container) return;
    if (typeof LightweightCharts === "undefined") {
        console.warn("TradingView LightweightCharts library not found in window context.");
        return;
    }

    container.innerHTML = "";
    tvCandleData = prepareCandleData(dashboardData.candles || []);

    if (tvCandleData.length === 0) {
        container.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; height: 100%; color: var(--text-muted); font-family: var(--font-mono); font-size: 0.85rem;">
                No historical daily price observations found for ${currentCommodityCode}.
            </div>
        `;
        return;
    }

    // Create TradingView Chart Instance
    tvChart = LightweightCharts.createChart(container, {
        width: container.clientWidth || 800,
        height: 420,
        layout: {
            background: { type: 'solid', color: 'transparent' },
            textColor: '#94a3b8',
            fontFamily: "'JetBrains Mono', 'Roboto Mono', 'SF Pro Text', -apple-system, monospace",
            fontSize: 11,
        },
        grid: {
            vertLines: { color: 'rgba(255, 255, 255, 0.04)' },
            horzLines: { color: 'rgba(255, 255, 255, 0.04)' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
            vertLine: {
                color: 'rgba(0, 242, 254, 0.55)',
                width: 1,
                style: LightweightCharts.LineStyle.Dashed,
                labelBackgroundColor: '#00f2fe',
            },
            horzLine: {
                color: 'rgba(0, 242, 254, 0.55)',
                width: 1,
                style: LightweightCharts.LineStyle.Dashed,
                labelBackgroundColor: '#0f172a',
            },
        },
        rightPriceScale: {
            borderColor: 'rgba(255, 255, 255, 0.08)',
            scaleMargins: { top: 0.08, bottom: 0.28 },
        },
        timeScale: {
            borderColor: 'rgba(255, 255, 255, 0.08)',
            timeVisible: true,
            secondsVisible: false,
        },
    });

    // 1. Candlestick Series (Primary)
    tvCandleSeries = tvChart.addCandlestickSeries({
        upColor: '#10b981',
        downColor: '#f43f5e',
        borderVisible: false,
        wickUpColor: '#10b981',
        wickDownColor: '#f43f5e',
    });
    tvCandleSeries.setData(tvCandleData.map(c => ({
        time: c.time,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close
    })));

    // 2. Area Series (Alternate)
    tvAreaSeries = tvChart.addAreaSeries({
        topColor: 'rgba(0, 242, 254, 0.35)',
        bottomColor: 'rgba(0, 242, 254, 0.0)',
        lineColor: '#00f2fe',
        lineWidth: 2,
        visible: false,
    });
    tvAreaSeries.setData(tvCandleData.map(c => ({ time: c.time, value: c.close })));

    // 3. Line Series (Alternate)
    tvLineSeries = tvChart.addLineSeries({
        color: '#38bdf8',
        lineWidth: 2,
        visible: false,
    });
    tvLineSeries.setData(tvCandleData.map(c => ({ time: c.time, value: c.close })));

    // 4. Volume Histogram (Anchored to lower 22% of chart)
    tvVolumeSeries = tvChart.addHistogramSeries({
        priceFormat: { type: 'volume' },
        priceScaleId: 'volume_scale',
        visible: true,
    });
    tvChart.priceScale('volume_scale').applyOptions({
        scaleMargins: { top: 0.78, bottom: 0 },
    });
    tvVolumeSeries.setData(tvCandleData.map(c => ({
        time: c.time,
        value: c.volume,
        color: c.close >= c.open ? 'rgba(16, 185, 129, 0.45)' : 'rgba(244, 63, 94, 0.45)',
    })));

    // 5. Open Interest (OI) Overlay Line (Scaled between 62% and 80%)
    tvOiSeries = tvChart.addLineSeries({
        color: '#f59e0b',
        lineWidth: 1.8,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        priceScaleId: 'oi_scale',
        visible: true,
        title: 'OI',
    });
    tvChart.priceScale('oi_scale').applyOptions({
        scaleMargins: { top: 0.62, bottom: 0.20 },
    });
    tvOiSeries.setData(tvCandleData.map(c => ({
        time: c.time,
        value: c.open_interest,
    })));

    // Initial HUD State set to latest candle
    const lastCandle = tvCandleData[tvCandleData.length - 1];
    updateCrosshairHud(lastCandle);

    // Crosshair Hover Subscription (60fps dynamic HUD telemetry)
    tvChart.subscribeCrosshairMove((param) => {
        if (!param.time || !param.seriesData) {
            updateCrosshairHud(lastCandle);
            return;
        }
        const candle = param.seriesData.get(tvCandleSeries) || 
                       param.seriesData.get(tvAreaSeries) || 
                       param.seriesData.get(tvLineSeries);
        const vol = param.seriesData.get(tvVolumeSeries);
        const oi = param.seriesData.get(tvOiSeries);

        if (candle) {
            const timeStr = typeof param.time === 'string' 
                ? param.time 
                : `${param.time.year}-${String(param.time.month).padStart(2,'0')}-${String(param.time.day).padStart(2,'0')}`;
            updateCrosshairHud({
                time: timeStr,
                open: candle.open !== undefined ? candle.open : candle.value,
                high: candle.high !== undefined ? candle.high : candle.value,
                low: candle.low !== undefined ? candle.low : candle.value,
                close: candle.close !== undefined ? candle.close : candle.value,
                volume: vol ? vol.value : 0,
                open_interest: oi ? oi.value : 0,
            });
        }
    });

    // Wire Timeframe Selectors
    const tfButtons = document.querySelectorAll("#tvTimeframeGroup .chart-tool-btn");
    tfButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const tf = btn.getAttribute("data-tf");
            applyTimeframe(tf);
        });
    });

    // Wire Chart Type Toggles
    const typeButtons = document.querySelectorAll("#tvChartTypeGroup .chart-tool-btn");
    typeButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const type = btn.getAttribute("data-type");
            switchChartType(type);
        });
    });

    // Wire Overlay Buttons
    const btnVol = document.getElementById("btnToggleVolume");
    if (btnVol) btnVol.addEventListener("click", toggleVolumeOverlay);

    const btnOi = document.getElementById("btnToggleOi");
    if (btnOi) btnOi.addEventListener("click", toggleOiOverlay);

    const btnFit = document.getElementById("btnResetScale");
    if (btnFit) btnFit.addEventListener("click", () => tvChart.timeScale().fitContent());

    // Set Default Timeframe (1Y)
    applyTimeframe("1Y");

    // Responsive Canvas Resize Observer
    const resizeObserver = new ResizeObserver(entries => {
        if (entries.length > 0 && tvChart) {
            const { width } = entries[0].contentRect;
            if (width > 0) tvChart.applyOptions({ width });
        }
    });
    resizeObserver.observe(container);
}

/**
 * Update UI Telemetry with Live Price Quote Data
 */
function updateLiveTelemetryUI(data) {
    if (!data || data.status !== "ok") return;

    // 1. Live Hero Price with Neon Tick Flash
    const heroPriceEl = document.getElementById("liveHeroPrice");
    if (heroPriceEl && data.spot_price !== undefined) {
        const curPrice = parseFloat(heroPriceEl.textContent) || data.spot_price;
        const newPrice = Number(data.spot_price);
        heroPriceEl.textContent = newPrice.toFixed(2);

        if (newPrice > curPrice + 0.001) {
            heroPriceEl.classList.remove("flash-up", "flash-down");
            void heroPriceEl.offsetWidth; // Trigger reflow for animation restart
            heroPriceEl.classList.add("flash-up");
            setTimeout(() => heroPriceEl.classList.remove("flash-up"), 1200);
        } else if (newPrice < curPrice - 0.001) {
            heroPriceEl.classList.remove("flash-up", "flash-down");
            void heroPriceEl.offsetWidth; // Trigger reflow
            heroPriceEl.classList.add("flash-down");
            setTimeout(() => heroPriceEl.classList.remove("flash-down"), 1200);
        }
    }

    // 2. Returns and Point Change
    const heroChangeEl = document.getElementById("liveHeroChange");
    if (heroChangeEl && data.returns_1d !== undefined) {
        const ret1d = Number(data.returns_1d);
        const ptChg = Number(data.point_change || 0);
        heroChangeEl.className = `ticker-change ${ret1d >= 0 ? 'pos' : 'neg'}`;
        heroChangeEl.innerHTML = `
            ${ret1d >= 0 ? '+' : ''}${ret1d.toFixed(2)}%
            <span id="liveHeroPointChg" style="font-weight: 500; opacity: 0.9;">(${ptChg >= 0 ? '+' : ''}${ptChg.toFixed(2)})</span>
        `;
    }

    // 3. Day Range and 52W Range Pin Positions
    const spot = Number(data.spot_price);
    const dayL = Number(data.day_low);
    const dayH = Number(data.day_high);
    const low52 = Number(data.low_52w);
    const high52 = Number(data.high_52w);

    const valDayLow = document.getElementById("valDayLow");
    const valDayHigh = document.getElementById("valDayHigh");
    const val52wLow = document.getElementById("val52wLow");
    const val52wHigh = document.getElementById("val52wHigh");

    if (valDayLow && !isNaN(dayL)) valDayLow.textContent = `$${dayL.toFixed(2)}`;
    if (valDayHigh && !isNaN(dayH)) valDayHigh.textContent = `$${dayH.toFixed(2)}`;
    if (val52wLow && !isNaN(low52)) val52wLow.textContent = `$${low52.toFixed(2)}`;
    if (val52wHigh && !isNaN(high52)) val52wHigh.textContent = `$${high52.toFixed(2)}`;

    const dayPin = document.getElementById("dayRangePin");
    if (dayPin && dayH > dayL) {
        let pct = ((spot - dayL) / (dayH - dayL)) * 100;
        pct = Math.max(3, Math.min(97, pct));
        dayPin.style.left = `${pct.toFixed(1)}%`;
    }

    const pin52 = document.getElementById("pin52w");
    if (pin52 && high52 > low52) {
        let pct = ((spot - low52) / (high52 - low52)) * 100;
        pct = Math.max(3, Math.min(97, pct));
        pin52.style.left = `${pct.toFixed(1)}%`;
    }

    // 4. Session Telemetry Numbers
    const telVol = document.getElementById("telemetryVolume");
    if (telVol && data.day_volume !== undefined) telVol.textContent = Number(data.day_volume).toLocaleString();

    const telOi = document.getElementById("telemetryOi");
    if (telOi && data.day_oi !== undefined) telOi.textContent = Number(data.day_oi).toLocaleString();

    const telOpen = document.getElementById("telemetryOpen");
    if (telOpen && data.day_open !== undefined) telOpen.textContent = `$${Number(data.day_open).toFixed(2)}`;

    // 5. Timestamp
    const tsEl = document.getElementById("liveHeroTimestamp");
    if (tsEl) {
        const now = new Date();
        tsEl.textContent = `Live: ${now.toLocaleTimeString()}`;
    }

    // 6. Real-time Candle Propagation into TradingView Chart
    if (tvChart && data.candle && tvCandleSeries) {
        const c = data.candle;
        tvCandleSeries.update({
            time: c.time,
            open: Number(c.open),
            high: Number(c.high),
            low: Number(c.low),
            close: Number(c.close),
        });
        if (tvAreaSeries) tvAreaSeries.update({ time: c.time, value: Number(c.close) });
        if (tvLineSeries) tvLineSeries.update({ time: c.time, value: Number(c.close) });
        if (tvVolumeSeries && c.volume !== undefined) {
            tvVolumeSeries.update({
                time: c.time,
                value: Number(c.volume),
                color: Number(c.close) >= Number(c.open) ? 'rgba(16, 185, 129, 0.45)' : 'rgba(244, 63, 94, 0.45)',
            });
        }
        if (tvOiSeries && c.open_interest !== undefined) {
            tvOiSeries.update({
                time: c.time,
                value: Number(c.open_interest),
            });
        }
    }
}

/**
 * Fetch and refresh live quote from REST API
 */
async function refreshLiveQuote(isManual = false) {
    const refreshBtns = [
        document.getElementById("btnLiveRefresh"), 
        document.getElementById("btnLiveSyncAll")
    ];
    refreshBtns.forEach(btn => { if (btn) btn.classList.add("syncing"); });

    try {
        const url = `/api/market-data/live-quote/?commodity=${encodeURIComponent(currentCommodityCode)}&refresh=${isManual ? 1 : 0}`;
        const resp = await fetch(url);
        if (!resp.ok) throw new Error(`HTTP error ${resp.status}`);
        const data = await resp.json();

        if (data.status === "ok") {
            updateLiveTelemetryUI(data);
        }
    } catch (err) {
        console.warn("Live quote synchronization notice:", err);
    } finally {
        setTimeout(() => {
            refreshBtns.forEach(btn => { if (btn) btn.classList.remove("syncing"); });
        }, 600);
    }
}

/**
 * Initialize Live Quote Telemetry & Background Polling
 */
function initLiveQuoteTelemetry() {
    window.refreshLiveQuote = refreshLiveQuote;

    // Trigger initial background sync
    setTimeout(() => {
        refreshLiveQuote(false);
    }, 1200);

    // Auto poll live quote every 20 seconds while tab is focused
    if (livePollInterval) clearInterval(livePollInterval);
    livePollInterval = setInterval(() => {
        if (!document.hidden) {
            refreshLiveQuote(false);
        }
    }, 20000);
}



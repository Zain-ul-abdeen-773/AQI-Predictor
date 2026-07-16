/**
 * Pearls AQI - Advanced Minimalist Logic
 */
const API_URL = window.location.origin;

const COLORS = {
    good: "#34d399",
    mod: "#fbbf24",
    usg: "#fb923c",
    unh: "#ef4444",
    v_unh: "#a855f7",
    haz: "#991b1b"
};

function getAqiColor(val) {
    if (val <= 50) return COLORS.good;
    if (val <= 100) return COLORS.mod;
    if (val <= 150) return COLORS.usg;
    if (val <= 200) return COLORS.unh;
    if (val <= 300) return COLORS.v_unh;
    return COLORS.haz;
}

async function fetchAPI(endpoint, method = 'GET') {
    try {
        const res = await fetch(`${API_URL}${endpoint}`, { method, headers: { 'Content-Type': 'application/json' }});
        if (!res.ok) {
            console.warn(`API non-200 status on ${endpoint}:`, res.status);
            return null;
        }
        return await res.json();
    } catch (e) {
        console.error("API Error:", e);
        return null;
    }
}

function updateHeroAndTelemetry(data) {
    if (!data || !data.hourly_predictions) return;
    const aqi = Math.round(data.current_aqi);
    const color = getAqiColor(aqi);
    
    const aqiEl = document.getElementById('currentAqi');
    if (aqiEl) {
        aqiEl.innerText = aqi;
        aqiEl.style.color = color;
    }
    
    const indicator = document.getElementById('aqiIndicator');
    if (indicator) {
        indicator.style.backgroundColor = color;
        indicator.style.boxShadow = `0 0 20px ${color}`;
    }
    
    const levelEl = document.getElementById('aqiLevel');
    if (levelEl) {
        levelEl.innerText = data.current_level;
        levelEl.style.color = color;
    }
    
    const advisory = document.getElementById('advisoryText');
    if (advisory) advisory.innerText = `Health Advisory: ${data.current_level}. Take appropriate precautions based on your sensitivity.`;
    
    const summary = document.getElementById('summaryText');
    if (summary) summary.innerText = data.summary || "The neural network has processed atmospheric telemetry and forecast stable conditions.";
    
    const predictions = data.hourly_predictions.map(p => p.aqi_predicted);
    const peakEl = document.getElementById('peakAqi');
    if (peakEl) peakEl.innerText = Math.round(Math.max(...predictions));
    
    const lowEl = document.getElementById('lowAqi');
    if (lowEl) lowEl.innerText = Math.round(Math.min(...predictions));
    
    const sum = predictions.reduce((a, b) => a + b, 0);
    const avgEl = document.getElementById('avgAqi');
    if (avgEl) avgEl.innerText = Math.round(sum / predictions.length);
    
    const modelEl = document.getElementById('modelType');
    if (modelEl) modelEl.innerText = (data.model_type || "BI-LSTM").toUpperCase();
    
    const d = new Date();
    const syncEl = document.getElementById('lastUpdated');
    if (syncEl) syncEl.innerText = `Last sync: ${d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
}

function renderForecastChart(predictions) {
    if (!predictions || !predictions.length) return;
    const times = predictions.map(p => new Date(p.timestamp));
    const vals = predictions.map(p => p.aqi_predicted);
    const upper95 = predictions.map(p => p.aqi_upper_95 || p.aqi_predicted + 15);
    const lower95 = predictions.map(p => p.aqi_lower_95 || Math.max(0, p.aqi_predicted - 15));
    
    const traceUpper = { x: times, y: upper95, type: 'scatter', mode: 'lines', line: {width: 0}, hoverinfo: 'skip' };
    const traceLower = { x: times, y: lower95, type: 'scatter', mode: 'lines', line: {width: 0}, fill: 'tonexty', fillcolor: 'rgba(255,255,255,0.05)', hoverinfo: 'skip' };
    
    const traceMain = {
        x: times, y: vals, type: 'scatter', mode: 'lines',
        line: { color: '#ffffff', width: 2, shape: 'spline', smoothing: 1.2 },
        hovertemplate: '%{x|%b %d, %H:%M}<br><b>AQI: %{y:.0f}</b><extra></extra>'
    };

    const layout = {
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        margin: { l: 40, r: 20, t: 10, b: 30 },
        xaxis: { showgrid: false, zeroline: false, tickfont: { color: '#888' }, gridcolor: '#222' },
        yaxis: { showgrid: true, gridcolor: '#222', zeroline: false, tickfont: { color: '#888' } },
        hovermode: 'x unified', showlegend: false,
        hoverlabel: { bgcolor: '#111', font: {color: '#fff'}, bordercolor: '#333' }
    };

    Plotly.newPlot('forecastChart', [traceUpper, traceLower, traceMain], layout, { displayModeBar: false, responsive: true });
}

function renderHistoricalChart(data) {
    if(!data || !data.data) return;
    const times = data.data.map(d => new Date(d.timestamp));
    const aqi = data.data.map(d => d.aqi);
    
    const trace = {
        x: times, y: aqi, type: 'scatter', mode: 'lines',
        fill: 'tozeroy', fillcolor: 'rgba(255,255,255,0.05)',
        line: { color: '#888', width: 1.5, shape: 'spline' },
        hovertemplate: '%{x|%H:%M}<br><b>Observed: %{y:.0f}</b><extra></extra>'
    };
    
    const layout = {
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        margin: { l: 40, r: 20, t: 10, b: 30 },
        xaxis: { showgrid: false, tickfont: { color: '#888' } },
        yaxis: { showgrid: true, gridcolor: '#222', tickfont: { color: '#888' } },
        hovermode: 'x unified', showlegend: false
    };
    Plotly.newPlot('historicalChart', [trace], layout, { displayModeBar: false, responsive: true });
}

function renderShapChart(explainData) {
    if (!explainData || !explainData.contributions) return;
    
    let contribs = explainData.contributions.sort((a, b) => Math.abs(a.shap_value) - Math.abs(b.shap_value)).slice(-8);
    const names = contribs.map(c => c.feature_name.replace(/_/g, ' ').toUpperCase());
    const vals = contribs.map(c => c.shap_value);
    
    const trace = {
        type: 'bar', y: names, x: vals, orientation: 'h',
        marker: { color: vals.map(v => v > 0 ? '#fff' : '#444') },
        hovertemplate: '<b>%{y}</b>: %{x:+.2f} Impact<extra></extra>'
    };
    
    const layout = {
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        margin: { l: 120, r: 20, t: 10, b: 30 },
        xaxis: { showgrid: true, gridcolor: '#222', zeroline: true, zerolinecolor: '#444', tickfont: {color: '#888'} },
        yaxis: { showgrid: false, tickfont: {color: '#fff', size: 11, family: 'Outfit'} }
    };
    Plotly.newPlot('shapChart', [trace], layout, { displayModeBar: false, responsive: true });
}

async function initializeDashboard() {
    try {
        const [predict, explain, historical] = await Promise.all([
            fetchAPI('/predict', 'POST'),
            fetchAPI('/explain', 'POST'),
            fetchAPI('/historical?hours=72', 'GET')
        ]);
        
        if (predict && predict.hourly_predictions) {
            updateHeroAndTelemetry(predict);
            renderForecastChart(predict.hourly_predictions);
        } else if (historical && historical.data && historical.data.length > 0) {
            // Fallback UI display from historical data if predict is momentarily initializing
            const latest = historical.data[historical.data.length - 1];
            updateHeroAndTelemetry({
                current_aqi: latest.aqi,
                current_level: "Moderate",
                summary: "Displaying observed telemetry while forecast engine synchronizes.",
                hourly_predictions: historical.data.map(d => ({ timestamp: d.timestamp, aqi_predicted: d.aqi })),
                model_type: "TELEMETRY-SYNC"
            });
            renderForecastChart(historical.data.map(d => ({ timestamp: d.timestamp, aqi_predicted: d.aqi })));
        }
        
        if (explain) renderShapChart(explain);
        if (historical) renderHistoricalChart(historical);
    } catch (e) {
        console.error(e);
        const summary = document.getElementById('summaryText');
        if (summary) summary.innerText = "System currently offline or unreachable.";
    } finally {
        // Always hide loader reliably
        const loader = document.getElementById('loadingOverlay');
        if (loader) {
            loader.style.opacity = '0';
            setTimeout(() => loader.style.display = 'none', 500);
        }
    }
}

document.getElementById('refreshBtn').addEventListener('click', () => {
    document.getElementById('loadingOverlay').style.display = 'flex';
    setTimeout(() => document.getElementById('loadingOverlay').style.opacity = '1', 10);
    initializeDashboard();
});

document.addEventListener('DOMContentLoaded', initializeDashboard);

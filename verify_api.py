// --- Core Front-End Logic for AquaGuard ---

document.addEventListener('DOMContentLoaded', () => {
    // 1. Common Elements
    const rainInputs = document.querySelectorAll('.rain-input');
    const annualInput = document.getElementById('ANNUAL');
    const avgJuneInput = document.getElementById('avgjune');
    const syncJuneBtn = document.getElementById('btn-sync-june');
    const predictionForm = document.getElementById('prediction-form');

    // 2. Real-time Rain Calculations
    if (rainInputs.length > 0 && annualInput) {
        const calculateAnnualRain = () => {
            let total = 0;
            rainInputs.forEach(input => {
                total += parseFloat(input.value) || 0;
            });
            annualInput.value = total.toFixed(1);
        };

        // Add input listeners
        rainInputs.forEach(input => {
            input.addEventListener('input', calculateAnnualRain);
        });

        // Sync June Rainfall Helper (Monsoon Jun-Sep is typically index 2)
        if (syncJuneBtn && avgJuneInput) {
            syncJuneBtn.addEventListener('click', () => {
                const monsoonVal = parseFloat(document.getElementById('Jun_Sep').value) || 0;
                // June average is roughly 25% of the total monsoon rainfall
                const calculatedJune = monsoonVal * 0.25;
                avgJuneInput.value = calculatedJune.toFixed(1);
                
                // Add minor flash effect to show updated
                avgJuneInput.style.borderColor = '#00f2fe';
                setTimeout(() => {
                    avgJuneInput.style.borderColor = '';
                }, 800);
            });
        }
    }

    // 3. Scenario 1: Early Warning Form Submit
    if (predictionForm) {
        predictionForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const btnPredict = document.getElementById('btn-predict');
            btnPredict.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Running Analysis...';
            btnPredict.disabled = true;

            // Prepare JSON payload
            const formData = new FormData(predictionForm);
            const payload = {};
            formData.forEach((value, key) => {
                payload[key] = isNaN(value) ? value : parseFloat(value);
            });

            try {
                const response = await fetch('/api/predict', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();
                
                if (data.status === 'success') {
                    displaySinglePrediction(data);
                } else {
                    alert('Prediction error: ' + (data.error || 'Unknown error'));
                }
            } catch (err) {
                console.error(err);
                alert('Connection to prediction server failed.');
            } finally {
                btnPredict.innerHTML = '<i class="fa-solid fa-brain"></i> Run Risk Prediction';
                btnPredict.disabled = false;
            }
        });
    }

    // 4. Modal Triggers for Scenario 2 Dashboard
    const modalTrigger = document.getElementById('btn-add-region-trigger');
    const modalBackdrop = document.getElementById('region-modal');
    const modalCloseBtn = document.getElementById('btn-close-modal');
    const addRegionForm = document.getElementById('add-region-form');

    if (modalTrigger && modalBackdrop && modalCloseBtn) {
        modalTrigger.addEventListener('click', () => {
            modalBackdrop.classList.remove('hidden');
        });

        modalCloseBtn.addEventListener('click', () => {
            modalBackdrop.classList.add('hidden');
        });

        modalBackdrop.addEventListener('click', (e) => {
            if (e.target === modalBackdrop) {
                modalBackdrop.classList.add('hidden');
            }
        });
    }

    if (addRegionForm) {
        addRegionForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(addRegionForm);
            const payload = {};
            formData.forEach((value, key) => {
                payload[key] = isNaN(value) ? value : parseFloat(value);
            });

            const regionName = document.getElementById('region_name').value;

            try {
                const response = await fetch('/api/predict', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (data.status === 'success') {
                    // Add region card with returned predictions
                    addRegionToDashboard(regionName, payload, data.predictions.xgboost);
                    addRegionForm.reset();
                    modalBackdrop.classList.add('hidden');
                    updateDashboardStats();
                } else {
                    alert('Error evaluating region: ' + (data.error || 'Unknown error'));
                }
            } catch (err) {
                console.error(err);
                alert('Prediction service is offline.');
            }
        });
    }
});

// --- UI Rendering Functions ---

// 1. Display Scenario 1 Prediction Output
function displaySinglePrediction(data) {
    const resultsInitial = document.querySelector('.initial-results-state');
    const resultsDisplay = document.querySelector('.results-display');
    
    // Hide initial state, show results panel
    if (resultsInitial) resultsInitial.classList.add('hidden');
    if (resultsDisplay) resultsDisplay.classList.remove('hidden');

    const predictions = data.predictions;
    const xgb = predictions.xgboost;

    // A. Update Gauge
    const gaugeFill = document.getElementById('gauge-fill');
    const gaugeCover = document.getElementById('gauge-cover');
    const gaugeWrapper = document.querySelector('.gauge-wrapper');
    
    const prob = xgb.probability;
    // Rotation mapping: 0% is 0.25turn (90deg), 100% is 0.75turn (270deg)
    const turnVal = 0.25 + (prob * 0.5);
    gaugeFill.style.transform = `rotate(${turnVal}turn)`;
    gaugeCover.textContent = Math.round(prob * 100) + '%';

    // Reset gauge colors
    gaugeWrapper.classList.remove('gauge-green', 'gauge-orange', 'gauge-red');
    if (xgb.risk_level === 'Low') {
        gaugeWrapper.classList.add('gauge-green');
    } else if (xgb.risk_level === 'Medium') {
        gaugeWrapper.classList.add('gauge-orange');
    } else {
        gaugeWrapper.classList.add('gauge-red');
    }

    // B. Update Risk Info
    const riskBadge = document.getElementById('risk-badge');
    const riskDesc = document.getElementById('risk-description');
    
    riskBadge.textContent = xgb.risk_level + ' RISK';
    riskBadge.className = 'risk-badge'; // reset
    
    if (xgb.risk_level === 'Low') {
        riskBadge.classList.add('safe-badge');
        riskDesc.textContent = `All atmospheric indices suggest optimal stability. Calculated flood likelihood is very minimal (${Math.round(prob*100)}%). Local monitoring is sufficient.`;
    } else if (xgb.risk_level === 'Medium') {
        riskBadge.classList.add('warning-badge');
        riskDesc.textContent = `Caution: Elevated seasonal rainfall triggers warnings in low-lying sectors. Calculated flood probability is ${Math.round(prob*100)}%. Ready civil sandbags.`;
    } else {
        riskBadge.classList.add('danger-badge');
        riskDesc.textContent = `Critical: Extreme monsoon rainfall and heavy cloud cover detected. Calculated flood probability is ${Math.round(prob*100)}%. Evacuation directives are highly advised.`;
    }

    // C. Update Model Comparison Grid
    const updateModelCard = (id, result) => {
        const card = document.getElementById(id);
        const textVal = card;
        
        textVal.textContent = result.risk_level;
        textVal.className = 'model-pred-val'; // reset
        
        if (result.risk_level === 'Low') {
            textVal.classList.add('pred-safe');
        } else if (result.risk_level === 'Medium') {
            textVal.classList.add('pred-warning');
        } else {
            textVal.classList.add('pred-danger');
        }
    };

    updateModelCard('val-xgb', predictions.xgboost);
    updateModelCard('val-rf', predictions.random_forest);
    updateModelCard('val-dt', predictions.decision_tree);
    updateModelCard('val-knn', predictions.knn);

    // D. Emergency Checklist
    const evacBox = document.getElementById('evacuation-box');
    const subBasinNum = document.getElementById('sub-basin-num');
    
    if (xgb.prediction === 1) {
        evacBox.classList.remove('hidden');
        if (subBasinNum) subBasinNum.textContent = data.inputs.sub || '3';
    } else {
        evacBox.classList.add('hidden');
    }
}

// 2. Scenario 2: Dashboard Functions
let dashboardRegions = [];

function initDashboard() {
    // Populate with 3 initial demo regions matching monsoon scenarios
    const demoRegions = [
        {
            name: "West Basin Delta (Lowlands)",
            inputs: { Temp: 27.5, Humidity: 86.0, Cloud_Visibility: 3.1, Jun_Sep: 2600.0, ANNUAL: 3200.0, sub: 1 },
            pred: { prediction: 1, probability: 0.94, risk_level: "High" }
        },
        {
            name: "Central Valley Pass",
            inputs: { Temp: 29.2, Humidity: 74.0, Cloud_Visibility: 6.8, Jun_Sep: 1450.0, ANNUAL: 1900.0, sub: 3 },
            pred: { prediction: 0, probability: 0.28, risk_level: "Low" }
        },
        {
            name: "East Slope Catchment",
            inputs: { Temp: 25.8, Humidity: 81.2, Cloud_Visibility: 4.8, Jun_Sep: 1950.0, ANNUAL: 2350.0, sub: 4 },
            pred: { prediction: 0, probability: 0.58, risk_level: "Medium" }
        }
    ];

    demoRegions.forEach(r => {
        addRegionToDashboard(r.name, r.inputs, r.pred);
    });

    updateDashboardStats();
}

function addRegionToDashboard(name, inputs, pred) {
    const container = document.getElementById('regions-container');
    if (!container) return;

    const regionId = 'region_' + Date.now();
    
    // Create card element
    const card = document.createElement('div');
    card.className = 'card glass-card region-card';
    card.id = regionId;

    // Define priority actions based on risk
    let priorityClass = 'priority-low';
    let priorityText = 'Monitor Status';
    let pBarFillColor = '#10b981';

    if (pred.risk_level === 'Medium') {
        priorityClass = 'priority-medium';
        priorityText = 'Standby / Deploy Sandbags';
        pBarFillColor = '#f59e0b';
    } else if (pred.risk_level === 'High') {
        priorityClass = 'priority-high';
        priorityText = 'Deploy Boats & Evacuate';
        pBarFillColor = '#ef4444';
    }

    card.innerHTML = `
        <div class="region-header">
            <span class="region-title">${name}</span>
            <button class="region-delete-btn" onclick="removeRegion('${regionId}')" title="Stop monitoring">
                <i class="fa-solid fa-trash-can"></i>
            </button>
        </div>
        
        <div class="region-stats">
            <div class="region-metric">
                <span class="metric-label">Monsoon Rain</span>
                <span class="metric-value">${inputs.Jun_Sep} mm</span>
            </div>
            <div class="region-metric">
                <span class="metric-label">Visibility / Humid</span>
                <span class="metric-value">${inputs.Cloud_Visibility} km / ${inputs.Humidity}%</span>
            </div>
        </div>

        <div class="region-risk-bar">
            <div class="risk-bar-label">
                <span>Flood Probability</span>
                <span style="color: ${pBarFillColor}; font-weight: 700;">${Math.round(pred.probability * 100)}%</span>
            </div>
            <div class="risk-bar-bg">
                <div class="risk-bar-fill" style="width: ${Math.round(pred.probability * 100)}%; background-color: ${pBarFillColor}"></div>
            </div>
        </div>

        <div class="priority-box ${priorityClass}">
            <span>Priority: ${pred.risk_level}</span>
            <span><i class="fa-solid fa-truck-fast"></i> ${priorityText}</span>
        </div>
    `;

    container.appendChild(card);

    // Save in memory
    dashboardRegions.push({
        id: regionId,
        name: name,
        risk_level: pred.risk_level
    });
}

function removeRegion(id) {
    const card = document.getElementById(id);
    if (card) {
        card.remove();
        dashboardRegions = dashboardRegions.filter(r => r.id !== id);
        updateDashboardStats();
    }
}

function updateDashboardStats() {
    const totalEl = document.getElementById('stat-total-regions');
    const threatsEl = document.getElementById('stat-active-threats');
    
    if (totalEl) totalEl.textContent = dashboardRegions.length;
    
    if (threatsEl) {
        const highRiskCount = dashboardRegions.filter(r => r.risk_level === 'High').length;
        threatsEl.textContent = highRiskCount;
        
        // Add alert pulse class to threat count card icon if count > 0
        const dangerCardIcon = document.querySelector('.danger-icon');
        if (dangerCardIcon) {
            if (highRiskCount > 0) {
                dangerCardIcon.style.animation = 'pulse-alert 1.5s infinite';
            } else {
                dangerCardIcon.style.animation = 'none';
            }
        }
    }
}

// Add global styles for alerts dynamically if not present
if (!document.getElementById('dash-animation-style')) {
    const styleSheet = document.createElement("style");
    styleSheet.id = 'dash-animation-style';
    styleSheet.innerText = `
        @keyframes pulse-alert {
            0%, 100% { transform: scale(1); box-shadow: 0 0 0 rgba(239, 68, 68, 0); }
            50% { transform: scale(1.05); box-shadow: 0 0 15px rgba(239, 68, 68, 0.4); }
        }
    `;
    document.head.appendChild(styleSheet);
}

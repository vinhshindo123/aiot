const API_BASE_URL = 'http://localhost:8000';

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    loadMetrics();
    loadDataAnalysis();
    setupSliders();
    setupFormSubmit();
});

// Setup slider displays
function setupSliders() {
    const sliders = document.querySelectorAll('input[type="range"]');
    sliders.forEach(slider => {
        slider.addEventListener('input', (e) => {
            const valueSpan = document.getElementById(e.target.id + '_value');
            if (valueSpan) {
                valueSpan.textContent = e.target.value;
            }
        });
    });
}

// Load metrics data
async function loadMetrics() {
    try {
        // Gọi /model-info thay vì /metrics-data
        const response = await fetch(`${API_BASE_URL}/model-info`);
        const data = await response.json();

        if (data.metrics) {
            document.getElementById('r2Score').textContent = data.metrics.r2?.toFixed(4) || '0.0000';
            document.getElementById('rmseValue').textContent = data.metrics.rmse?.toFixed(4) || '0.0000';
            document.getElementById('maeValue').textContent = data.metrics.mae?.toFixed(4) || '0.0000';
            document.getElementById('totalSamples').textContent = data.total_samples || 0;

            // Tạo metrics bar chart
            createMetricsBarChart(data.metrics);
        }
    } catch (error) {
        console.error('Error loading metrics:', error);
        // Hiển thị dữ liệu mẫu nếu không có API
        showSampleData();
    }
}

function generateSampleData() {
    // Tạo dữ liệu phân phối CO mẫu (phân phối chuẩn)
    const sampleCO = [];
    for (let i = 0; i < 1000; i++) {
        let co = Math.random() * 8 + 0.5; // 0.5 to 8.5 mg/m³
        sampleCO.push(co);
    }

    // Tạo dữ liệu nhiệt độ mẫu
    const sampleTemp = [];
    for (let i = 0; i < 1000; i++) {
        let temp = Math.random() * 30 + 5; // 5°C to 35°C
        sampleTemp.push(temp);
    }

    // Dữ liệu decision mẫu
    const sampleDecisions = {
        'AIR_QUALITY_GOOD': 450,
        'AIR_QUALITY_MODERATE': 300,
        'AIR_QUALITY_POOR': 150,
        'AIR_QUALITY_HAZARDOUS': 50,
        'CHECK_SENSOR_CALIBRATION': 50
    };

    // Dữ liệu predictions mẫu
    const samplePredActual = {
        actual: [],
        predicted: []
    };
    for (let i = 0; i < 100; i++) {
        let actual = Math.random() * 8 + 0.5;
        let predicted = actual + (Math.random() - 0.5) * 1.5;
        samplePredActual.actual.push(actual);
        samplePredActual.predicted.push(predicted);
    }

    createCOHistogram(sampleCO);
    createTempHistogram(sampleTemp);
    createDecisionPieChart(sampleDecisions);
    createPredVsActualChart(samplePredActual);
}

// Thêm hàm showSampleData
function showSampleData() {
    const sampleMetrics = {
        r2: 0.8523,
        rmse: 0.8765,
        mae: 0.6543,
        mse: 0.7684
    };

    document.getElementById('r2Score').textContent = sampleMetrics.r2.toFixed(4);
    document.getElementById('rmseValue').textContent = sampleMetrics.rmse.toFixed(4);
    document.getElementById('maeValue').textContent = sampleMetrics.mae.toFixed(4);
    document.getElementById('totalSamples').textContent = '1,234';

    createMetricsBarChart(sampleMetrics);
}

// Load data analysis
async function loadDataAnalysis() {
    try {
        // Thử gọi API, nếu fail thì dùng dữ liệu mẫu
        const response = await fetch(`${API_BASE_URL}/data-analysis`);

        if (response && response.ok) {
            const data = await response.json();
            if (!data.error) {
                createCOHistogram(data.co_distribution);
                createTempHistogram(data.temperature_distribution);
                createDecisionPieChart(data.decision_distribution);

                if (data.pred_actual) {
                    createPredVsActualChart(data.pred_actual);
                }
                return;
            }
        }

        // Fallback: Tạo dữ liệu mẫu để hiển thị
        generateSampleData();

    } catch (error) {
        console.error('Error loading data analysis:', error);
        generateSampleData();
    }
}

// Create CO histogram
function createCOHistogram(data) {
    const trace = {
        x: data,
        type: 'histogram',
        marker: {
            color: '#667eea',
            line: {
                color: 'white',
                width: 1
            }
        },
        opacity: 0.8,
        nbinsx: 50
    };

    const layout = {
        title: {
            text: 'CO Concentration Distribution',
            font: { size: 14, color: '#666' }
        },
        xaxis: {
            title: 'CO (mg/m³)',
            showgrid: true,
            gridcolor: '#f0f0f0'
        },
        yaxis: {
            title: 'Frequency',
            showgrid: true,
            gridcolor: '#f0f0f0'
        },
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        height: 280,
        margin: { t: 40, l: 50, r: 20, b: 40 }
    };

    Plotly.newPlot('coHistogram', [trace], layout, { responsive: true });
}

// Create temperature histogram
function createTempHistogram(data) {
    const trace = {
        x: data,
        type: 'histogram',
        marker: {
            color: '#f59e0b',
            line: {
                color: 'white',
                width: 1
            }
        },
        opacity: 0.8,
        nbinsx: 50
    };

    const layout = {
        title: {
            text: 'Temperature Distribution',
            font: { size: 14, color: '#666' }
        },
        xaxis: {
            title: 'Temperature (°C)',
            showgrid: true,
            gridcolor: '#f0f0f0'
        },
        yaxis: {
            title: 'Frequency',
            showgrid: true,
            gridcolor: '#f0f0f0'
        },
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        height: 280,
        margin: { t: 40, l: 50, r: 20, b: 40 }
    };

    Plotly.newPlot('tempHistogram', [trace], layout, { responsive: true });
}

// Create metrics bar chart
function createMetricsBarChart(metrics) {
    const metricsData = {
        x: ['MSE', 'RMSE', 'MAE', 'R²'],
        y: [metrics.mse || 0, metrics.rmse || 0, metrics.mae || 0, metrics.r2 || 0],
        type: 'bar',
        marker: {
            color: ['#667eea', '#667eea', '#667eea', '#10b981'],
            line: {
                color: 'white',
                width: 2
            }
        },
        text: [metrics.mse?.toFixed(4), metrics.rmse?.toFixed(4), metrics.mae?.toFixed(4), metrics.r2?.toFixed(4)],
        textposition: 'auto',
        textfont: {
            size: 12,
            color: '#333'
        }
    };

    const layout = {
        title: {
            text: 'Model Evaluation Metrics',
            font: { size: 14, color: '#666' }
        },
        xaxis: {
            title: 'Metrics',
            showgrid: false
        },
        yaxis: {
            title: 'Score',
            showgrid: true,
            gridcolor: '#f0f0f0'
        },
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        height: 280,
        margin: { t: 40, l: 50, r: 20, b: 40 }
    };

    Plotly.newPlot('metricsBar', [metricsData], layout, { responsive: true });
}

// Create predictions vs actual chart
function createPredVsActualChart(data) {
    const trace1 = {
        y: data.actual,
        type: 'scatter',
        mode: 'lines',
        name: 'Actual CO',
        line: {
            color: '#f59e0b',
            width: 2
        },
        fill: 'tozeroy',
        fillcolor: 'rgba(245, 158, 11, 0.1)'
    };

    const trace2 = {
        y: data.predicted,
        type: 'scatter',
        mode: 'lines',
        name: 'Predicted CO',
        line: {
            color: '#667eea',
            width: 2,
            dash: 'dot'
        }
    };

    const layout = {
        title: {
            text: 'Predictions vs Actual (Last 100)',
            font: { size: 14, color: '#666' }
        },
        xaxis: {
            title: 'Sample Number',
            showgrid: true,
            gridcolor: '#f0f0f0'
        },
        yaxis: {
            title: 'CO (mg/m³)',
            showgrid: true,
            gridcolor: '#f0f0f0'
        },
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        height: 280,
        margin: { t: 40, l: 50, r: 20, b: 40 },
        legend: {
            x: 0.02,
            y: 0.98,
            bgcolor: 'rgba(255,255,255,0.8)'
        }
    };

    Plotly.newPlot('predVsActual', [trace1, trace2], layout, { responsive: true });
}

// Create decision pie chart
function createDecisionPieChart(data) {
    const labels = Object.keys(data);
    const values = Object.values(data);

    // Map decision types to colors
    const colorMap = {
        'AIR_QUALITY_GOOD': '#10b981',
        'AIR_QUALITY_MODERATE': '#f59e0b',
        'AIR_QUALITY_POOR': '#ef4444',
        'AIR_QUALITY_HAZARDOUS': '#7f1d1d',
        'CHECK_SENSOR_CALIBRATION': '#8b5cf6'
    };

    const colors = labels.map(label => colorMap[label] || '#999');

    const trace = {
        labels: labels,
        values: values,
        type: 'pie',
        marker: {
            colors: colors,
            line: {
                color: 'white',
                width: 2
            }
        },
        textinfo: 'label+percent',
        textfont: {
            size: 12
        },
        hoverinfo: 'label+value+percent',
        hole: 0.4
    };

    const layout = {
        title: {
            text: 'Air Quality Decision Distribution',
            font: { size: 14, color: '#666' }
        },
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        height: 280,
        margin: { t: 40, l: 20, r: 20, b: 20 },
        showlegend: true,
        legend: {
            orientation: 'v',
            x: 1.02,
            y: 0.5,
            bgcolor: 'rgba(255,255,255,0.8)'
        }
    };

    Plotly.newPlot('decisionPie', [trace], layout, { responsive: true });
}

// Setup form submission
function setupFormSubmit() {
    const form = document.getElementById('predictForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Show loading state
        const predictBtn = document.querySelector('.predict-btn');
        const originalText = predictBtn.innerHTML;
        predictBtn.innerHTML = '<div class="loading"></div> Predicting...';
        predictBtn.disabled = true;

        const payload = {
            location: "station_center",  // THÊM DÒNG NÀY
            timestamp: new Date().toISOString(),  // THÊM DÒNG NÀY
            PT08_S1_CO: parseFloat(document.getElementById('co_sensor').value),
            PT08_S2_NMHC: parseFloat(document.getElementById('nmhc_sensor').value),
            PT08_S3_NOx: parseFloat(document.getElementById('nox_sensor').value),
            PT08_S4_NO2: parseFloat(document.getElementById('no2_sensor').value),
            PT08_S5_O3: parseFloat(document.getElementById('o3_sensor').value),
            Temperature: parseFloat(document.getElementById('temp').value),
            Relative_Humidity: parseFloat(document.getElementById('humidity').value),
            Absolute_Humidity: parseFloat(document.getElementById('abs_humidity').value)
            // KHÔNG cần gửi hour và dayofweek vì backend tự tính từ timestamp
        };

        console.log('Sending payload:', payload); // Debug log

        try {
            const response = await fetch(`${API_BASE_URL}/predict`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            // Kiểm tra response status
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            const data = await response.json();
            console.log('Response:', data); // Debug log

            displayPrediction(data);
        } catch (error) {
            console.error('Prediction error:', error);
            showError(`Failed to get prediction: ${error.message}`);
        } finally {
            // Restore button
            predictBtn.innerHTML = originalText;
            predictBtn.disabled = false;
        }
    });
}

// Display prediction result
function displayPrediction(data) {
    const resultDiv = document.getElementById('result');
    const predictionDisplay = document.getElementById('predictionDisplay');
    const decisionBox = document.getElementById('decisionBox');

    const co = data.predicted_co_concentration_mg_per_m3;
    const level = data.air_quality_level;

    // Display prediction
    predictionDisplay.innerHTML = `
        <div style="text-align: center;">
            <div style="font-size: 14px; color: #666; margin-bottom: 10px;">Predicted CO Concentration</div>
            <div class="prediction-value">${co.toFixed(3)} <span style="font-size: 24px;">mg/m³</span></div>
            <div style="margin-top: 10px; font-size: 16px;">
                Air Quality Level: <strong style="color: #667eea;">${level}</strong>
            </div>
        </div>
    `;

    // Create gauge chart
    const gaugeValue = Math.min(co, 12);
    const gaugeColor = co <= 2 ? '#10b981' : (co <= 4 ? '#f59e0b' : (co <= 10 ? '#ef4444' : '#7f1d1d'));

    const gaugeData = [{
        type: 'indicator',
        mode: 'gauge+number',
        value: gaugeValue,
        domain: { x: [0, 1], y: [0, 1] },
        title: { text: 'CO Concentration (mg/m³)' },
        number: {
            font: { size: 24, color: gaugeColor },
            suffix: ' mg/m³'
        },
        gauge: {
            axis: {
                range: [0, 12],
                tickwidth: 1,
                tickcolor: '#ddd'
            },
            bar: { color: gaugeColor },
            bgcolor: 'white',
            borderwidth: 0,
            bordercolor: '#ccc',
            steps: [
                { range: [0, 2], color: 'rgba(16, 185, 129, 0.2)' },
                { range: [2, 4], color: 'rgba(245, 158, 11, 0.2)' },
                { range: [4, 10], color: 'rgba(239, 68, 68, 0.2)' },
                { range: [10, 12], color: 'rgba(127, 29, 29, 0.2)' }
            ],
            threshold: {
                line: { color: 'red', width: 4 },
                thickness: 0.75,
                value: co
            }
        }
    }];

    const gaugeLayout = {
        height: 300,
        margin: { t: 25, r: 25, l: 25, b: 25 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#666' }
    };

    Plotly.newPlot('gaugeChart', gaugeData, gaugeLayout, { responsive: true });

    // Decision message
    let decisionColor, decisionMsg, recommendation;
    if (co <= 2) {
        decisionColor = 'good';
        decisionMsg = '✅ Excellent Air Quality';
        recommendation = 'Normal operations - Air quality is safe';
    } else if (co <= 4) {
        decisionColor = 'moderate';
        decisionMsg = '⚠️ Moderate Air Quality';
        recommendation = 'Monitor closely - Consider ventilation';
    } else if (co <= 10) {
        decisionColor = 'poor';
        decisionMsg = '🚨 Poor Air Quality';
        recommendation = 'Immediate action required - Increase ventilation';
    } else {
        decisionColor = 'hazard';
        decisionMsg = '💀 Hazardous Air Quality';
        recommendation = 'CRITICAL - Evacuate area immediately!';
    }

    decisionBox.innerHTML = `
        <div class="decision-box ${decisionColor}">
            <h3 style="margin-bottom: 10px;">${decisionMsg}</h3>
            <p style="margin: 0; opacity: 0.9;">${recommendation}</p>
        </div>
    `;

    // Show result
    resultDiv.style.display = 'block';

    // Scroll to result
    resultDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Show error message
function showError(message) {
    const resultDiv = document.getElementById('result');
    const predictionDisplay = document.getElementById('predictionDisplay');

    predictionDisplay.innerHTML = `
        <div style="text-align: center; color: #ef4444; padding: 20px;">
            <div style="font-size: 48px; margin-bottom: 10px;">❌</div>
            <div>${message}</div>
        </div>
    `;

    resultDiv.style.display = 'block';
}

// Auto-refresh metrics every 30 seconds
setInterval(() => {
    loadMetrics();
}, 30000);
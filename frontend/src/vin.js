const API_URL = 'http://localhost:3000';

const vinInput = document.getElementById('vinInput');
const btnAnalyze = document.getElementById('btnAnalyze');
const btnClear = document.getElementById('btnClear');
const vinResults = document.getElementById('vinResults');
const vinResultContent = document.getElementById('vinResultContent');

btnAnalyze.addEventListener('click', async () => {
    const vin = vinInput.value.trim();
    if (!vin) return alert('Please enter a VIN');

    btnAnalyze.disabled = true;
    btnAnalyze.textContent = 'Analyzing...';

    try {
        const res = await fetch(`${API_URL}/analyze-vin`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ vin })
        });
        const data = await res.json();
        if (!data.success) {
            vinResultContent.innerText = JSON.stringify(data, null, 2);
            vinResults.style.display = 'block';
            return;
        }

        const analysis = data.analysis;
        if (analysis.error) {
            vinResultContent.innerText = 'Error: ' + (analysis.error || JSON.stringify(analysis));
            vinResults.style.display = 'block';
            return;
        }

        // Pretty render
        let html = '';
        if (analysis.decoded) {
            html += '<div class="result-item"><span class="result-label">Decoded Fields</span><div class="result-value">';
            for (const [k,v] of Object.entries(analysis.decoded)) {
                html += `<strong>${k}:</strong> ${String(v)}<br>`;
            }
            html += '</div></div>';
        }

        if (analysis.exceptions) {
            html += '<div class="result-item"><span class="result-label">Exceptions</span><div class="result-value">';
            html += analysis.exceptions.join('\n');
            html += '</div></div>';
        }

        if (analysis.confidence !== undefined) {
            html += `<div class="result-item"><span class="result-label">Confidence</span><div class="result-value">${analysis.confidence}</div></div>`;
        }

        if (analysis.explanation) {
            html += `<div class="result-item"><span class="result-label">Explanation</span><div class="result-value">${analysis.explanation}</div></div>`;
        }

        vinResultContent.innerHTML = html;
        vinResults.style.display = 'block';

    } catch (err) {
        vinResultContent.innerText = 'Request failed: ' + err;
        vinResults.style.display = 'block';
    } finally {
        btnAnalyze.disabled = false;
        btnAnalyze.textContent = 'Analyze';
    }
});

btnClear.addEventListener('click', () => {
    vinInput.value = '';
    vinResultContent.innerText = '';
    vinResults.style.display = 'none';
});

const API_URL = 'http://localhost:5000';

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const uploadProgress = document.getElementById('uploadProgress');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const resultsSection = document.getElementById('resultsSection');
const resultContent = document.getElementById('resultContent');
const filesList = document.getElementById('filesList');
const btnRefresh = document.getElementById('btnRefresh');
const statusIndicator = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');
const fileModal = document.getElementById('fileModal');
const modalTitle = document.getElementById('modalTitle');
const modalBody = document.getElementById('modalBody');
const btnCloseModal = document.getElementById('btnCloseModal');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    loadFiles();
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    // Upload area click
    uploadArea.addEventListener('click', () => fileInput.click());
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });
    
    // Refresh button
    btnRefresh.addEventListener('click', loadFiles);
    
    // Close modal
    btnCloseModal.addEventListener('click', () => {
        fileModal.style.display = 'none';
    });
    
    fileModal.addEventListener('click', (e) => {
        if (e.target === fileModal) {
            fileModal.style.display = 'none';
        }
    });
}

// Check API health and Ollama status
async function checkHealth() {
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();
        
        const statusDot = statusIndicator.querySelector('.status-dot');
        
        if (data.status === 'healthy') {
            statusDot.classList.add('connected');
            statusDot.classList.remove('disconnected');
            statusText.textContent = 'Connected to Ollama';
        } else {
            statusDot.classList.add('disconnected');
            statusDot.classList.remove('connected');
            statusText.textContent = 'Ollama disconnected';
        }
    } catch (error) {
        const statusDot = statusIndicator.querySelector('.status-dot');
        statusDot.classList.add('disconnected');
        statusDot.classList.remove('connected');
        statusText.textContent = 'API unavailable';
        console.error('Health check failed:', error);
    }
}

// Handle file upload
async function handleFileUpload(file) {
    // Show progress
    uploadProgress.style.display = 'block';
    progressFill.style.width = '0%';
    progressText.textContent = 'Uploading...';
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        // Simulate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 10;
            if (progress <= 90) {
                progressFill.style.width = `${progress}%`;
            }
        }, 100);
        
        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        
        clearInterval(progressInterval);
        progressFill.style.width = '100%';
        
        const data = await response.json();
        
        if (data.success) {
            progressText.textContent = 'Processing complete!';
            displayResults(data.data);
            loadFiles();
            
            // Reset after delay
            setTimeout(() => {
                uploadProgress.style.display = 'none';
                fileInput.value = '';
            }, 2000);
        } else {
            progressText.textContent = `Error: ${data.error}`;
            progressFill.style.backgroundColor = 'var(--error-color)';
        }
    } catch (error) {
        console.error('Upload failed:', error);
        progressText.textContent = 'Upload failed!';
        progressFill.style.backgroundColor = 'var(--error-color)';
    }
}

// Display upload results
function displayResults(data) {
    resultsSection.style.display = 'block';
    
    // Try to parse Ollama JSON output
    let analysisHtml = '';
    try {
        const analysis = JSON.parse(data.ollama_analysis);
        // store raw for negotiation assistant
        window._lastOllamaAnalysisRaw = data.ollama_analysis;
        // SLA parameters
        if (analysis.sla_parameters) {
            analysisHtml += `<div class="result-item"><span class="result-label">SLA Parameters:</span><div class="result-value">`;
            for (const [k, v] of Object.entries(analysis.sla_parameters)) {
                analysisHtml += `<strong>${escapeHtml(k)}:</strong> ${escapeHtml(String(v))}<br>`;
            }
            analysisHtml += `</div></div>`;
        }

        // Red flags
        if (analysis.red_flags && Array.isArray(analysis.red_flags)) {
            analysisHtml += `<div class="result-item"><span class="result-label">Red Flags:</span><div class="result-value">`;
            analysisHtml += analysis.red_flags.map(r => `- ${escapeHtml(r)}`).join('\n');
            analysisHtml += `</div></div>`;
        }

        // Fairness score
        if (analysis.contract_fairness_score !== undefined) {
            analysisHtml += `<div class="result-item"><span class="result-label">Contract Fairness Score:</span><div class="result-value">${escapeHtml(String(analysis.contract_fairness_score))}`;
            if (analysis.score_explanation) {
                analysisHtml += `\n\n${escapeHtml(analysis.score_explanation)}`;
            }
            analysisHtml += `</div></div>`;
        }

        // Summary
        if (analysis.summary) {
            analysisHtml += `<div class="result-item"><span class="result-label">Summary:</span><div class="result-value">${escapeHtml(analysis.summary)}</div></div>`;
        }
    } catch (e) {
        analysisHtml = `<div class="result-item"><span class="result-label">AI Analysis (raw):</span><div class="result-value">${escapeHtml(data.ollama_analysis)}</div></div>`;
    }

    resultContent.innerHTML = `
        <div class="result-item">
            <span class="result-label">Filename:</span>
            <div class="result-value">${data.original_filename}</div>
        </div>
        <div class="result-item">
            <span class="result-label">Upload Time:</span>
            <div class="result-value">${new Date(data.upload_time).toLocaleString()}</div>
        </div>
        <div class="result-item">
            <span class="result-label">File Size:</span>
            <div class="result-value">${formatFileSize(data.file_size)}</div>
        </div>
        <div class="result-item">
            <span class="result-label">Extracted Text Preview:</span>
            <div class="result-value">${escapeHtml(data.extracted_text)}</div>
        </div>
        ${analysisHtml}
    `;
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Load files list
async function loadFiles() {
    try {
        const response = await fetch(`${API_URL}/files`);
        const data = await response.json();
        
        if (data.success && data.files.length > 0) {
            filesList.innerHTML = data.files.map(file => `
                <div class="file-item" data-id="${file.id}">
                    <div class="file-info">
                        <div class="file-name">${escapeHtml(file.filename)}</div>
                        <div class="file-meta">
                            ${new Date(file.upload_time).toLocaleString()} • 
                            ${formatFileSize(file.file_size)}
                        </div>
                    </div>
                    <div class="file-actions">
                        <button class="btn-view" onclick="viewFile('${file.id}')">View Details</button>
                    </div>
                </div>
            `).join('');
        } else {
            filesList.innerHTML = `
                <div class="empty-state">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
                        <polyline points="13 2 13 9 20 9"></polyline>
                    </svg>
                    <p>No files uploaded yet</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Failed to load files:', error);
        filesList.innerHTML = `
            <div class="empty-state">
                <p>Failed to load files</p>
            </div>
        `;
    }
}

// View file details
async function viewFile(fileId) {
    try {
        const response = await fetch(`${API_URL}/files/${fileId}`);
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            modalTitle.textContent = data.original_filename;
            let bodyHtml = `
                <div class="detail-section">
                    <span class="detail-label">File Information</span>
                    <div class="detail-value">
Filename: ${escapeHtml(data.original_filename)}
Upload Time: ${new Date(data.upload_time).toLocaleString()}
File Size: ${formatFileSize(data.file_size)}
                    </div>
                </div>
                <div class="detail-section">
                    <span class="detail-label">Extracted Text</span>
                    <div class="detail-value">${escapeHtml(data.extracted_text)}</div>
                </div>
            `;

            try {
                const analysis = JSON.parse(data.ollama_analysis);
                // make raw available for negotiation assistant
                window._lastOllamaAnalysisRaw = data.ollama_analysis;
                // SLA parameters
                if (analysis.sla_parameters) {
                    bodyHtml += `<div class="detail-section"><span class="detail-label">SLA Parameters</span><div class="detail-value">`;
                    for (const [k, v] of Object.entries(analysis.sla_parameters)) {
                        bodyHtml += `<strong>${escapeHtml(k)}:</strong> ${escapeHtml(String(v))}<br>`;
                    }
                    bodyHtml += `</div></div>`;
                }

                if (analysis.red_flags && Array.isArray(analysis.red_flags)) {
                    bodyHtml += `<div class="detail-section"><span class="detail-label">Red Flags</span><div class="detail-value">` + analysis.red_flags.map(r => `- ${escapeHtml(r)}`).join('\n') + `</div></div>`;
                }

                if (analysis.contract_fairness_score !== undefined) {
                    bodyHtml += `<div class="detail-section"><span class="detail-label">Contract Fairness Score</span><div class="detail-value">${escapeHtml(String(analysis.contract_fairness_score))}`;
                    if (analysis.score_explanation) bodyHtml += `\n\n${escapeHtml(analysis.score_explanation)}`;
                    bodyHtml += `</div></div>`;
                }

                if (analysis.summary) {
                    bodyHtml += `<div class="detail-section"><span class="detail-label">Summary</span><div class="detail-value">${escapeHtml(analysis.summary)}</div></div>`;
                }
            } catch (e) {
                bodyHtml += `<div class="detail-section"><span class="detail-label">AI Analysis (raw)</span><div class="detail-value">${escapeHtml(data.ollama_analysis)}</div></div>`;
            }

            modalBody.innerHTML = bodyHtml;
            fileModal.style.display = 'flex';
        }
    } catch (error) {
        console.error('Failed to load file details:', error);
        alert('Failed to load file details');
    }
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

console.log('[home-script] ════════ home-script.js loading ════════');
const API_URL = 'http://localhost:3000';

// DOM Elements
const statusIndicator = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');
const chatBubbleBtn = document.getElementById('chatBubbleBtn');
const chatModal = document.getElementById('chatModal');
const chatCloseBtn = document.getElementById('chatCloseBtn');
const chatWindow = document.getElementById('chatWindow');
const chatInput = document.getElementById('chatInput');
const btnSend = document.getElementById('btnSend');
const btnClearChat = document.getElementById('btnClearChat');

// Initialize once
if (!window._homeChatInit) {
    window._homeChatInit = true;
    console.log('[home-script] ✓ Initializing home-script.js for first time');
    document.addEventListener('DOMContentLoaded', () => {
        console.log('[home-script] DOMContentLoaded fired');
        checkHealth();
        setupEventListeners();
    });
} else {
    console.log('[home-script] ⚠️ BLOCKED: already initialized, skipping');
}

// Event Listeners
function setupEventListeners() {
    // If required elements are missing, skip attaching listeners
    if (!chatBubbleBtn) {
        console.log('[home-script] chat UI elements not present, skipping listeners');
        return;
    }

    // Chatbot toggle
    if (!chatBubbleBtn._listenersAttached) {
        chatBubbleBtn._listenersAttached = true;
        chatBubbleBtn.addEventListener('click', () => {
            chatModal.classList.add('active');
            // Auto-start negotiation conversation
            if (!window._negotiationAutoStarted) {
                window._negotiationAutoStarted = true;
                startNegotiationChat();
            }
            // Check fine-tuning status when modal opens
            checkFineTuningStatus();
        });
    }

    if (chatCloseBtn && !chatCloseBtn._listenersAttached) {
        chatCloseBtn._listenersAttached = true;
        chatCloseBtn.addEventListener('click', () => {
            chatModal.classList.remove('active');
        });
    }

    // Send message
    if (btnSend && !btnSend._listenersAttached) {
        btnSend._listenersAttached = true;
        btnSend.addEventListener('click', sendChatMessage);
    }

    // Enter key to send
    if (chatInput && !chatInput._listenersAttached) {
        chatInput._listenersAttached = true;
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }

    // Clear chat
    if (btnClearChat && !btnClearChat._listenersAttached) {
        btnClearChat._listenersAttached = true;
        btnClearChat.addEventListener('click', clearChat);
    }
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
        
        // Also check fine-tuning status
        checkFineTuningStatus();
    } catch (error) {
        const statusDot = statusIndicator.querySelector('.status-dot');
        statusDot.classList.add('disconnected');
        statusDot.classList.remove('connected');
        statusText.textContent = 'API unavailable';
        console.error('Health check failed:', error);
    }
}

// Check fine-tuning status and update UI
async function checkFineTuningStatus() {
    try {
        const response = await fetch(`${API_URL}/fine-tune-status`);
        const data = await response.json();
        
        if (data.success && data.fine_tuning) {
            const status = data.fine_tuning;
            updateFineTuningUI(status);
            
            // If fine-tuning is running, check again in 5 seconds
            if (status.is_running) {
                setTimeout(checkFineTuningStatus, 3000);
            }
        }
    } catch (error) {
        console.error('Fine-tuning status check failed:', error);
    }
}

// Update fine-tuning UI indicator
function updateFineTuningUI(status) {
    let fineTuneIndicator = document.getElementById('fineTuneIndicator');
    
    // Create indicator if it doesn't exist
    if (!fineTuneIndicator && chatModal) {
        fineTuneIndicator = document.createElement('div');
        fineTuneIndicator.id = 'fineTuneIndicator';
        fineTuneIndicator.className = 'fine-tune-indicator';
        fineTuneIndicator.style.cssText = `
            position: absolute;
            bottom: 10px;
            left: 10px;
            right: 10px;
            padding: 8px 12px;
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 6px;
            font-size: 12px;
            color: #3b82f6;
            display: none;
            align-items: center;
            gap: 8px;
        `;
        
        const chatContainer = chatModal.querySelector('.chat-container');
        if (chatContainer) {
            chatContainer.style.position = 'relative';
            chatContainer.appendChild(fineTuneIndicator);
        }
    }
    
    if (!fineTuneIndicator) return;
    
    if (status.is_running) {
        const statusText = status.status === 'analyzing' ? 
            `Analyzing conversations... ${status.progress}%` :
            status.status === 'training' ?
            `Training model... ${status.progress}%` :
            `Processing... ${status.progress}%`;
        
        fineTuneIndicator.innerHTML = `
            <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; 
                         background: #3b82f6; animation: pulse 2s ease-in-out infinite;"></span>
            <span>${statusText}</span>
        `;
        fineTuneIndicator.style.display = 'flex';
    } else if (status.status === 'completed' && status.last_run) {
        const lastRun = new Date(status.last_run);
        const timeAgo = getTimeAgo(lastRun);
        fineTuneIndicator.innerHTML = `
            <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #10b981;"></span>
            <span>Model optimized ${timeAgo} (${status.conversations_processed} conversations analyzed)</span>
        `;
        fineTuneIndicator.style.display = 'flex';
        fineTuneIndicator.style.background = 'rgba(16, 185, 129, 0.1)';
        fineTuneIndicator.style.borderColor = 'rgba(16, 185, 129, 0.3)';
        fineTuneIndicator.style.color = '#10b981';
        
        // Hide after 10 seconds
        setTimeout(() => {
            fineTuneIndicator.style.display = 'none';
        }, 10000);
    } else {
        fineTuneIndicator.style.display = 'none';
    }
}

// Helper function to get time ago text
function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
    return `${Math.floor(seconds / 86400)} days ago`;
}

// Add CSS animation for pulse effect
if (!document.getElementById('fine-tune-animation-styles')) {
    const style = document.createElement('style');
    style.id = 'fine-tune-animation-styles';
    style.textContent = `
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
    `;
    document.head.appendChild(style);
}

// Chat functionality
window._chatHistory = window._chatHistory || [];

function renderChat() {
    if (!chatWindow) return;
    chatWindow.innerHTML = '';
    if (window._chatHistory.length === 0) {
        const el = document.createElement('div');
        el.className = 'chat-empty';
        el.textContent = 'Start a conversation with the assistant';
        chatWindow.appendChild(el);
        return;
    }

    for (const msg of window._chatHistory) {
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble ' + (msg.role === 'user' ? 'user' : 'assistant');
        if (msg.role === 'assistant' && msg.content && msg.content.trim() !== '...') {
            bubble.innerHTML = formatAssistantContent(msg.content);
        } else {
            bubble.textContent = msg.content;
        }
        chatWindow.appendChild(bubble);
    }
    
    // Scroll to bottom
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function formatAssistantContent(content) {
    // Try to parse JSON
    let parsed = null;
    try {
        parsed = JSON.parse(content);
    } catch (e) {
        // Sometimes models return JSON embedded in text
        const jsonMatch = content.match(/\{[\s\S]*\}|\[[\s\S]*\]/);
        if (jsonMatch) {
            try { 
                parsed = JSON.parse(jsonMatch[0]); 
            } catch (e) { 
                parsed = null; 
            }
        }
    }

    if (!parsed) {
        // Not JSON — return as plain text with simple newlines
        return escapeHtml(content).replace(/\n/g, '<br>');
    }

    // If parsed is an array
    if (Array.isArray(parsed)) {
        const items = parsed.map(i => `<li>${escapeHtml(String(i))}</li>`).join('');
        return `<ul>${items}</ul>`;
    }

    // Object: handle specific keys
    let html = '';

    if (parsed.questions && Array.isArray(parsed.questions)) {
        html += `<div class="assistant-section"><strong>Suggested Questions:</strong><ul>`;
        for (const q of parsed.questions) html += `<li>${escapeHtml(q)}</li>`;
        html += `</ul>`;
        if (parsed.explanation) html += `<div class="assistant-note">${escapeHtml(parsed.explanation)}</div>`;
        html += `</div>`;
    }

    if (parsed.negotiation_points && Array.isArray(parsed.negotiation_points)) {
        html += `<div class="assistant-section"><strong>Negotiation Points:</strong><ol>`;
        for (const p of parsed.negotiation_points) {
            html += `<li><strong>${escapeHtml(p.point || '')}</strong><div class="assistant-sub">${escapeHtml(p.rationale || '')}</div>`;
            if (p.suggested_text) html += `<pre class="assistant-suggest">${escapeHtml(p.suggested_text)}</pre>`;
            html += `</li>`;
        }
        html += `</ol>`;
        if (parsed.summary) html += `<div class="assistant-note">${escapeHtml(parsed.summary)}</div>`;
        html += `</div>`;
    }

    if (parsed.subject || parsed.body) {
        html += `<div class="assistant-section"><strong>Generated Email:</strong>`;
        if (parsed.subject) html += `<div class="assistant-sub"><strong>Subject:</strong> ${escapeHtml(parsed.subject)}</div>`;
        if (parsed.body) html += `<pre class="assistant-suggest">${escapeHtml(parsed.body)}</pre>`;
        if (parsed.notes) html += `<div class="assistant-note">${escapeHtml(parsed.notes)}</div>`;
        html += `</div>`;
    }

    // Fallback: render remaining keys as JSON
    const knownKeys = new Set(['questions','explanation','negotiation_points','summary','subject','body','notes']);
    const remaining = {};
    for (const k of Object.keys(parsed)) {
        if (!knownKeys.has(k)) remaining[k] = parsed[k];
    }
    if (Object.keys(remaining).length > 0) {
        html += `<div class="assistant-section"><strong>Details:</strong><pre class="assistant-suggest">${escapeHtml(JSON.stringify(remaining, null, 2))}</pre></div>`;
    }

    return html || escapeHtml(JSON.stringify(parsed, null, 2));
}

async function sendChatMessage() {
    const text = (chatInput.value || '').trim();
    if (!text) return;

    // Add user message
    window._chatHistory.push({ role: 'user', content: text });
    renderChat();
    chatInput.value = '';

    // Show typing indicator
    window._chatHistory.push({ role: 'assistant', content: '...' });
    renderChat();

    try {
        const payload = { 
            preset: 'car_negotiation',
            messages: window._chatHistory.map(m => ({ role: m.role, content: m.content }))
        };
        
        const resp = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await resp.json();
        
        // Remove typing placeholder
        if (window._chatHistory.length && window._chatHistory[window._chatHistory.length - 1].content === '...') {
            window._chatHistory.pop();
        }

        if (data.success && data.reply) {
            window._chatHistory.push({ role: 'assistant', content: data.reply });
        } else if (data.reply) {
            window._chatHistory.push({ role: 'assistant', content: JSON.stringify(data) });
        } else if (data.error) {
            window._chatHistory.push({ role: 'assistant', content: 'Error: ' + data.error });
        } else {
            window._chatHistory.push({ role: 'assistant', content: 'No response from server' });
        }
        renderChat();
    } catch (err) {
        // Remove typing placeholder
        if (window._chatHistory.length && window._chatHistory[window._chatHistory.length - 1].content === '...') {
            window._chatHistory.pop();
        }
        window._chatHistory.push({ role: 'assistant', content: 'Failed to send message: ' + (err.message || err) });
        renderChat();
    }
}

function clearChat() {
    window._chatHistory = [];
    window._negotiationAutoStarted = false;
    renderChat();
}

if (!window.startNegotiationChat) {
    window.startNegotiationChat = async function() {
        console.log('[home-script] Starting negotiation chat...');
        
        // Clear chat history and start fresh
        window._chatHistory = [];
        renderChat();
        
        // Show loading indicator
        window._chatHistory.push({ role: 'assistant', content: '...' });
        renderChat();

        try {
            const resp = await fetch(`${API_URL}/negotiation-start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });

            const data = await resp.json();
            
            // Remove loading indicator
            if (window._chatHistory.length && window._chatHistory[window._chatHistory.length - 1].content === '...') {
                window._chatHistory.pop();
            }
            
            if (data.success && data.greeting) {
                window._chatHistory.push({ role: 'assistant', content: data.greeting });
                window._currentSessionId = data.session_id;
                renderChat();
                console.log('[home-script] Negotiation chat started successfully');
            } else if (data.error) {
                window._chatHistory.push({ role: 'assistant', content: 'Error starting negotiation: ' + data.error });
                renderChat();
            } else {
                window._chatHistory.push({ role: 'assistant', content: 'Failed to start negotiation chat' });
                renderChat();
            }
        } catch (err) {
            // Remove loading indicator
            if (window._chatHistory.length && window._chatHistory[window._chatHistory.length - 1].content === '...') {
                window._chatHistory.pop();
            }
            window._chatHistory.push({ role: 'assistant', content: 'Failed to connect to server: ' + (err.message || err) });
            renderChat();
        }
    };
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

// Initial render
renderChat();

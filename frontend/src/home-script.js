const API_URL = 'http://localhost:5000';

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

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    // Chatbot toggle
    chatBubbleBtn.addEventListener('click', () => {
        chatModal.classList.add('active');
        // Auto-start negotiation chat if first time opening
        if (!window._negotiationAutoStarted) {
            window._negotiationAutoStarted = true;
            startNegotiationChat();
        }
    });

    chatCloseBtn.addEventListener('click', () => {
        chatModal.classList.remove('active');
    });

    // Send message
    btnSend.addEventListener('click', sendChatMessage);
    
    // Enter key to send
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });

    // Clear chat
    btnClearChat.addEventListener('click', clearChat);
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

async function startNegotiationChat() {
    const initial = "Hello — I'm ready to help you review and negotiate a car lease or loan contract. Please upload the contract or paste key terms, and tell me your negotiation goals (price reduction, mileage, early termination, etc.).";
    
    window._chatHistory = [];
    renderChat();

    try {
        const payload = { 
            preset: 'car_negotiation', 
            messages: [{ role: 'user', content: initial }] 
        };
        
        const resp = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await resp.json();
        
        if (data.success && data.reply) {
            window._chatHistory.push({ role: 'assistant', content: data.reply });
            renderChat();
        } else if (data.error) {
            window._chatHistory.push({ role: 'assistant', content: 'Error: ' + data.error });
            renderChat();
        } else {
            window._chatHistory.push({ role: 'assistant', content: 'No response from server' });
            renderChat();
        }
    } catch (err) {
        window._chatHistory.push({ role: 'assistant', content: 'Failed to start negotiation chat: ' + (err.message || err) });
        renderChat();
    }
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

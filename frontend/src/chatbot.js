// Shared Chatbot functionality
const API_URL = 'http://localhost:5000';

// Initialize chatbot
function initializeChatbot() {
    const chatBubbleBtn = document.getElementById('chatBubbleBtn');
    const chatModalFloating = document.getElementById('chatModalFloating');
    const chatCloseBtn = document.getElementById('chatCloseBtn');
    const chatWindow = document.getElementById('chatWindow');
    const chatInput = document.getElementById('chatInput');
    const btnSend = document.getElementById('btnSend');
    const btnClearChat = document.getElementById('btnClearChat');

    if (!chatBubbleBtn || !chatModalFloating) return;

    // Floating Chatbot toggle
    chatBubbleBtn.addEventListener('click', () => {
        chatModalFloating.classList.add('active');
        // Auto-start negotiation chat if first time opening
        if (!window._negotiationAutoStarted) {
            window._negotiationAutoStarted = true;
            startNegotiationChat();
        }
    });

    chatCloseBtn.addEventListener('click', () => {
        chatModalFloating.classList.remove('active');
    });

    // Send message
    if (btnSend) btnSend.addEventListener('click', sendChatMessage);
    if (btnClearChat) btnClearChat.addEventListener('click', clearChat);
    
    // Enter key to send
    if (chatInput) {
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }

    // Initial render
    renderChat();
}

// Chat functionality
window._chatHistory = window._chatHistory || [];

function renderChat() {
    const chatWindow = document.getElementById('chatWindow');
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
        return escapeHtml(content).replace(/\n/g, '<br>');
    }

    if (Array.isArray(parsed)) {
        const items = parsed.map(i => `<li>${escapeHtml(String(i))}</li>`).join('');
        return `<ul>${items}</ul>`;
    }

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
    const chatInput = document.getElementById('chatInput');
    const text = (chatInput.value || '').trim();
    if (!text) return;

    window._chatHistory.push({ role: 'user', content: text });
    renderChat();
    chatInput.value = '';

    window._chatHistory.push({ role: 'assistant', content: '...' });
    renderChat();

    try {
        // Filter out typing indicator from messages sent to backend
        const messagesToSend = window._chatHistory
            .filter(m => m.content !== '...')
            .map(m => ({ role: m.role, content: m.content }));
        
        const payload = { 
            preset: 'car_negotiation',
            messages: messagesToSend
        };
        
        const resp = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await resp.json();
        
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

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeChatbot);
} else {
    initializeChatbot();
}

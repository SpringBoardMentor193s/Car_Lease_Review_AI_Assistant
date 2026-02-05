const API_URL = 'http://localhost:5000';

// DOM Elements
const statusIndicator = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const btnSend = document.getElementById('btnSend');
const btnClear = document.getElementById('btnClear');

// Chat history
let chatHistory = [];
let isWaiting = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    setupEventListeners();
    startConversation();
});

// Event Listeners
function setupEventListeners() {
    btnSend.addEventListener('click', sendMessage);
    btnClear.addEventListener('click', clearChat);
    
    // Enter to send, Shift+Enter for new line
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize textarea
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 150) + 'px';
    });
}

// Check API health
async function checkHealth() {
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();
        
        const statusDot = statusIndicator.querySelector('.status-dot');
        
        if (data.status === 'healthy') {
            statusDot.classList.add('connected');
            statusDot.classList.remove('disconnected');
            statusText.textContent = 'Connected to AI';
        } else {
            statusDot.classList.add('disconnected');
            statusDot.classList.remove('connected');
            statusText.textContent = 'AI disconnected';
        }
    } catch (error) {
        const statusDot = statusIndicator.querySelector('.status-dot');
        statusDot.classList.add('disconnected');
        statusDot.classList.remove('connected');
        statusText.textContent = 'Connection failed';
        console.error('Health check failed:', error);
    }
}

// Start conversation with greeting
async function startConversation() {
    const initial = "Hello — I'm ready to help you review and negotiate a car lease or loan contract. Please upload the contract or paste key terms, and tell me your negotiation goals (price reduction, mileage, early termination, etc.).";
    
    showTyping();

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                preset: 'car_negotiation',
                messages: [{ role: 'user', content: initial }]
            })
        });

        const data = await response.json();
        removeTyping();

        if (data.success && data.reply) {
            addMessage('assistant', data.reply);
        } else {
            addMessage('assistant', 'Hello! How can I help you with your car lease negotiation today?');
        }
    } catch (error) {
        console.error('Failed to start conversation:', error);
        removeTyping();
        addMessage('assistant', 'Hello! How can I help you with your car lease negotiation today?');
    }
}

// Send message
async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text || isWaiting) return;

    // Add user message
    addMessage('user', text);
    chatInput.value = '';
    chatInput.style.height = 'auto';

    // Disable input while waiting
    isWaiting = true;
    btnSend.disabled = true;
    chatInput.disabled = true;

    // Show typing indicator
    showTyping();

    try {
        // Build message history for API (exclude typing indicators)
        const messages = chatHistory.map(msg => ({
            role: msg.role,
            content: msg.content
        }));

        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                preset: 'car_negotiation',
                messages: messages
            })
        });

        const data = await response.json();
        removeTyping();

        if (data.success && data.reply) {
            addMessage('assistant', data.reply);
        } else if (data.error) {
            addMessage('assistant', `Error: ${data.error}`);
        } else {
            addMessage('assistant', 'Sorry, I didn\'t receive a proper response. Please try again.');
        }
    } catch (error) {
        console.error('Failed to send message:', error);
        removeTyping();
        addMessage('assistant', `Failed to send message: ${error.message}`);
    } finally {
        // Re-enable input
        isWaiting = false;
        btnSend.disabled = false;
        chatInput.disabled = false;
        chatInput.focus();
    }
}

// Add message to chat
function addMessage(role, content) {
    // Add to history
    chatHistory.push({ role, content });

    // Remove empty state if present
    const emptyState = chatMessages.querySelector('.message-empty');
    if (emptyState) {
        emptyState.remove();
    }

    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    if (role === 'assistant') {
        messageDiv.innerHTML = formatAssistantContent(content);
    } else {
        messageDiv.textContent = content;
    }

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// Show typing indicator
function showTyping() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message typing';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = `
        <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    chatMessages.appendChild(typingDiv);
    scrollToBottom();
}

// Remove typing indicator
function removeTyping() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Format assistant content (handle JSON responses)
function formatAssistantContent(content) {
    let parsed = null;
    
    try {
        parsed = JSON.parse(content);
    } catch (e) {
        // Try to extract JSON from text
        const jsonMatch = content.match(/\{[\s\S]*\}|\[[\s\S]*\]/);
        if (jsonMatch) {
            try {
                parsed = JSON.parse(jsonMatch[0]);
            } catch (e2) {
                // Not JSON, return as plain text
                return escapeHtml(content).replace(/\n/g, '<br>');
            }
        } else {
            // Not JSON, return as plain text
            return escapeHtml(content).replace(/\n/g, '<br>');
        }
    }

    if (!parsed) {
        return escapeHtml(content).replace(/\n/g, '<br>');
    }

    // Handle array
    if (Array.isArray(parsed)) {
        const items = parsed.map(i => `<li>${escapeHtml(String(i))}</li>`).join('');
        return `<ul style="margin: 0.5rem 0 0 1.25rem;">${items}</ul>`;
    }

    // Handle object with specific structures
    let html = '';

    // Questions
    if (parsed.questions && Array.isArray(parsed.questions)) {
        html += `<div style="margin-bottom: 1rem;"><strong style="display: block; margin-bottom: 0.5rem;">Suggested Questions:</strong><ul style="margin-left: 1.25rem;">`;
        for (const q of parsed.questions) {
            html += `<li style="margin-bottom: 0.25rem;">${escapeHtml(q)}</li>`;
        }
        html += `</ul>`;
        if (parsed.explanation) {
            html += `<div style="background: var(--bg-secondary); padding: 0.5rem 0.75rem; border-radius: 0.5rem; margin-top: 0.5rem; font-size: 0.9rem; border-left: 3px solid var(--primary-color);">${escapeHtml(parsed.explanation)}</div>`;
        }
        html += `</div>`;
    }

    // Negotiation points
    if (parsed.negotiation_points && Array.isArray(parsed.negotiation_points)) {
        html += `<div style="margin-bottom: 1rem;"><strong style="display: block; margin-bottom: 0.5rem;">Negotiation Points:</strong><ol style="margin-left: 1.5rem;">`;
        for (const p of parsed.negotiation_points) {
            html += `<li style="margin-bottom: 0.75rem;"><strong>${escapeHtml(p.point || '')}</strong>`;
            if (p.rationale) {
                html += `<div style="color: var(--text-muted); font-size: 0.9rem; margin-top: 0.25rem;">${escapeHtml(p.rationale)}</div>`;
            }
            if (p.suggested_text) {
                html += `<pre style="background: var(--bg-color); padding: 0.75rem; border-radius: 0.5rem; margin-top: 0.5rem; font-family: 'Courier New', monospace; font-size: 0.85rem; overflow-x: auto; border: 1px solid var(--border-color);">${escapeHtml(p.suggested_text)}</pre>`;
            }
            html += `</li>`;
        }
        html += `</ol>`;
        if (parsed.summary) {
            html += `<div style="background: var(--bg-secondary); padding: 0.5rem 0.75rem; border-radius: 0.5rem; margin-top: 0.5rem; font-size: 0.9rem; border-left: 3px solid var(--primary-color);">${escapeHtml(parsed.summary)}</div>`;
        }
        html += `</div>`;
    }

    // Email
    if (parsed.subject || parsed.body) {
        html += `<div style="margin-bottom: 1rem;"><strong style="display: block; margin-bottom: 0.5rem;">Generated Email:</strong>`;
        if (parsed.subject) {
            html += `<div style="margin-bottom: 0.5rem;"><strong>Subject:</strong> ${escapeHtml(parsed.subject)}</div>`;
        }
        if (parsed.body) {
            html += `<pre style="background: var(--bg-color); padding: 0.75rem; border-radius: 0.5rem; font-family: 'Courier New', monospace; font-size: 0.85rem; overflow-x: auto; border: 1px solid var(--border-color); white-space: pre-wrap;">${escapeHtml(parsed.body)}</pre>`;
        }
        if (parsed.notes) {
            html += `<div style="background: var(--bg-secondary); padding: 0.5rem 0.75rem; border-radius: 0.5rem; margin-top: 0.5rem; font-size: 0.9rem; border-left: 3px solid var(--primary-color);">${escapeHtml(parsed.notes)}</div>`;
        }
        html += `</div>`;
    }

    // Fallback - show any remaining keys
    const knownKeys = new Set(['questions', 'explanation', 'negotiation_points', 'summary', 'subject', 'body', 'notes']);
    const remaining = {};
    for (const k of Object.keys(parsed)) {
        if (!knownKeys.has(k)) {
            remaining[k] = parsed[k];
        }
    }
    if (Object.keys(remaining).length > 0) {
        html += `<pre style="background: var(--bg-color); padding: 0.75rem; border-radius: 0.5rem; font-family: 'Courier New', monospace; font-size: 0.85rem; overflow-x: auto; border: 1px solid var(--border-color);">${escapeHtml(JSON.stringify(remaining, null, 2))}</pre>`;
    }

    return html || escapeHtml(JSON.stringify(parsed, null, 2));
}

// Clear chat
function clearChat() {
    if (confirm('Are you sure you want to clear the chat history?')) {
        chatHistory = [];
        chatMessages.innerHTML = `
            <div class="message-empty">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="opacity: 0.3; margin: 0 auto 1rem;">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
                <p>Start a conversation with the negotiation assistant</p>
            </div>
        `;
        startConversation();
    }
}

// Scroll to bottom
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Escape HTML
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

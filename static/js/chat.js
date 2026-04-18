document.addEventListener('DOMContentLoaded', () => {
    const chatArea = document.querySelector('.chat-area');
    if (!chatArea) return;

    const convId = chatArea.dataset.convId;
    const csrf = chatArea.dataset.csrf;
    const container = document.getElementById('messagesContainer');
    const form = document.getElementById('messageForm');
    const input = document.getElementById('messageInput');

    let lastMessageId = 0;

    // Scroll to bottom
    function scrollToBottom() {
        container.scrollTop = container.scrollHeight;
    }
    scrollToBottom();

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatTime(iso) {
        if (!iso) return '';
        const d = new Date(iso);
        return d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
    }

    // Create message element
    function createMessageEl(msg, isOwn) {
        const div = document.createElement('div');
        div.className = `message ${isOwn ? 'message-own' : ''}`;
        div.innerHTML = `
            <div class="message-avatar">
                <div class="avatar avatar-sm" style="background:${msg.color}">${escapeHtml(msg.initials)}</div>
            </div>
            <div class="message-bubble">
                <div class="message-content">${escapeHtml(msg.content)}</div>
                <div class="message-time">${formatTime(msg.created_at)}</div>
            </div>
        `;
        return div;
    }

    // Send message
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const content = input.value.trim();
        if (!content) return;
        input.value = '';

        try {
            const res = await fetch(`/api/conversation/${convId}/send/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf,
                },
                body: JSON.stringify({ content }),
            });
            const msg = await res.json();
            if (msg.id) {
                lastMessageId = Math.max(lastMessageId, msg.id);
                container.appendChild(createMessageEl(msg, true));
                scrollToBottom();
            }
        } catch (err) {
            console.error('Send failed:', err);
        }
    });

    // Poll for new messages (real-time feel)
    setInterval(async () => {
        try {
            const res = await fetch(`/api/conversation/${convId}/messages/?after=${lastMessageId}`);
            const data = await res.json();
            for (const msg of data.messages) {
                if (msg.id > lastMessageId) {
                    lastMessageId = msg.id;
                    const currentUser = document.querySelector('.user-info span')?.textContent?.trim();
                    const isOwn = msg.sender === currentUser;
                    container.appendChild(createMessageEl(msg, isOwn));
                    scrollToBottom();
                }
            }
        } catch {}
    }, 2000);

    // ── AI Assist Panel ──
    const aiPanel = document.getElementById('aiPanel');
    const toggleBtn = document.getElementById('toggleAIPanel');
    const closeBtn = document.getElementById('closeAIPanel');
    const assistBtn = document.getElementById('aiAssistBtn');
    const modelSelect = document.getElementById('aiModelSelect');
    const aiResult = document.getElementById('aiResult');

    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            aiPanel.classList.toggle('open');
        });
    }
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            aiPanel.classList.remove('open');
        });
    }

    if (assistBtn) {
        assistBtn.addEventListener('click', async () => {
            const model = modelSelect.value;
            assistBtn.disabled = true;
            assistBtn.textContent = 'Analyzing...';

            aiResult.innerHTML = `
                <div class="ai-streaming">
                    <div class="ai-section">
                        <div class="typing-indicator"><span></span><span></span><span></span></div>
                    </div>
                </div>
            `;

            try {
                const res = await fetch(`/api/conversation/${convId}/ai-assist/?model=${encodeURIComponent(model)}`);

                if (!res.ok) {
                    const err = await res.json();
                    aiResult.innerHTML = `<div class="ai-error">${escapeHtml(err.error || 'Something went wrong')}</div>`;
                    assistBtn.disabled = false;
                    assistBtn.textContent = 'Analyze & Suggest';
                    return;
                }

                const reader = res.body.getReader();
                const decoder = new TextDecoder();
                let fullText = '';
                let streamEl = null;

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value, { stream: true });
                    const lines = chunk.split('\n');

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = line.slice(6).trim();
                            if (data === '[DONE]') {
                                renderFinalResult(fullText);
                                continue;
                            }
                            try {
                                const parsed = JSON.parse(data);
                                if (parsed.token) {
                                    fullText += parsed.token;
                                    if (!streamEl) {
                                        aiResult.innerHTML = '<div class="ai-streaming"><pre class="ai-stream-text"></pre></div>';
                                        streamEl = aiResult.querySelector('.ai-stream-text');
                                    }
                                    streamEl.textContent = fullText;
                                }
                                if (parsed.error) {
                                    aiResult.innerHTML = `<div class="ai-error">${escapeHtml(parsed.error)}</div>`;
                                }
                            } catch {}
                        }
                    }
                }
            } catch (err) {
                aiResult.innerHTML = `<div class="ai-error">Connection error. Please try again.</div>`;
            }

            assistBtn.disabled = false;
            assistBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M8 1v14M1 8h14"/></svg>
                Analyze &amp; Suggest
            `;
        });
    }

    function renderFinalResult(fullText) {
        let sentiment = '';
        let context = '';
        let suggestion = fullText;

        if (fullText.includes('SENTIMENT:') && fullText.includes('---')) {
            const [header, ...rest] = fullText.split('---');
            suggestion = rest.join('---').trim();
            for (const line of header.split('\n')) {
                const trimmed = line.trim();
                if (trimmed.startsWith('SENTIMENT:')) {
                    sentiment = trimmed.replace('SENTIMENT:', '').trim();
                } else if (trimmed.startsWith('CONTEXT:')) {
                    context = trimmed.replace('CONTEXT:', '').trim();
                }
            }
        }

        let html = '';
        if (sentiment) {
            html += `<div class="ai-sentiment">
                <span class="ai-label">Sentiment</span>
                <span class="ai-sentiment-badge">${escapeHtml(sentiment)}</span>
            </div>`;
        }
        if (context) {
            html += `<div class="ai-context">
                <span class="ai-label">Mood</span>
                <p>${escapeHtml(context)}</p>
            </div>`;
        }
        html += `<div class="ai-suggestion">
            <span class="ai-label">Suggested Reply</span>
            <div class="ai-suggestion-text">${escapeHtml(suggestion)}</div>
            <button class="btn btn-sm btn-use-suggestion" onclick="useSuggestion(this)">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 7h7M7 3l4 4-4 4"/></svg>
                Use this reply
            </button>
        </div>`;

        aiResult.innerHTML = html;
    }

    // Global function so onclick works
    window.useSuggestion = function(btn) {
        const text = btn.parentElement.querySelector('.ai-suggestion-text').textContent;
        input.value = text;
        input.focus();
    };
});

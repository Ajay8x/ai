/**
 * AJAX AI - Shared Mini-Chat Widget
 * Available on every page. Connects to /api/chat/stream using active conversation session.
 */
(function() {
    let miniChatDrawer = null;
    let miniChatBody = null;
    let miniChatInput = null;
    let isStreaming = false;

    function ensureMiniChatDom() {
        if (miniChatDrawer) return;

        // Don't show floating mini-chat on any chat page or on mobile devices (< 768px)
        const path = window.location.pathname.toLowerCase();
        const isChatPage = path.includes('chat') || document.querySelector('.chat-message') !== null;
        const isMobile = window.innerWidth <= 768;
        if (isChatPage || isMobile) {
            const existing = document.getElementById('miniChatTrigger');
            if (existing) existing.remove();
            return;
        }

        // Create Trigger Button (compact 38px icon-only)
        const triggerBtn = document.createElement('button');
        triggerBtn.id = 'miniChatTrigger';
        triggerBtn.className = 'minichat-floating-trigger';
        triggerBtn.title = 'Open AJAX AI Assistant';
        triggerBtn.innerHTML = `<span class="trigger-icon">⚡</span>`;
        document.body.appendChild(triggerBtn);

        // Create Drawer
        miniChatDrawer = document.createElement('div');
        miniChatDrawer.id = 'miniChatDrawer';
        miniChatDrawer.className = 'minichat-drawer';
        miniChatDrawer.innerHTML = `
            <div class="minichat-header">
                <div class="minichat-brand">
                    <span>⚡</span>
                    <span>AJAX AI Assistant</span>
                </div>
                <div class="minichat-actions">
                    <button class="minichat-btn-icon" id="miniChatExpandBtn" title="Full Chat Screen">↗</button>
                    <button class="minichat-btn-icon" id="miniChatCloseBtn" title="Minimize">✕</button>
                </div>
            </div>
            <div class="minichat-body" id="miniChatBody">
                <div class="minichat-msg ai">
                    Hello Ajay! I am AJAX AI. You can ask me anything, or run tools and APIs from this page and send me the results to analyze.
                </div>
            </div>
            <div class="minichat-footer">
                <input type="text" class="minichat-input" id="miniChatInput" placeholder="Ask AJAX AI..." autocomplete="off">
                <button class="minichat-send-btn" id="miniChatSendBtn">Send</button>
            </div>
        `;
        document.body.appendChild(miniChatDrawer);

        miniChatBody = document.getElementById('miniChatBody');
        miniChatInput = document.getElementById('miniChatInput');

        // Event listeners
        triggerBtn.addEventListener('click', toggleMiniChat);
        document.getElementById('miniChatCloseBtn').addEventListener('click', () => toggleMiniChat(false));
        document.getElementById('miniChatExpandBtn').addEventListener('click', () => {
            window.location.href = '/AJAX/chat';
        });

        document.getElementById('miniChatSendBtn').addEventListener('click', sendMiniChatMessage);
        miniChatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendMiniChatMessage();
            }
        });
    }

    function toggleMiniChat(forceState) {
        ensureMiniChatDom();
        const isOpen = miniChatDrawer.classList.contains('open');
        const shouldOpen = forceState !== undefined ? forceState : !isOpen;
        if (shouldOpen) {
            miniChatDrawer.classList.add('open');
            setTimeout(() => miniChatInput.focus(), 150);
        } else {
            miniChatDrawer.classList.remove('open');
        }
    }

    async function sendMiniChatMessage() {
        const text = miniChatInput.value.trim();
        if (!text || isStreaming) return;

        appendMessage('user', text);
        miniChatInput.value = '';

        await executeAiStream(text);
    }

    function appendMessage(role, content) {
        ensureMiniChatDom();
        const msgDiv = document.createElement('div');
        msgDiv.className = `minichat-msg ${role}`;
        msgDiv.textContent = content;
        miniChatBody.appendChild(msgDiv);
        miniChatBody.scrollTop = miniChatBody.scrollHeight;
        return msgDiv;
    }

    async function executeAiStream(queryText) {
        isStreaming = true;
        const convId = window.ajaxState.getConversationId();
        const lang = window.ajaxState.getLanguage();
        const webSearch = window.ajaxState.isWebSearchEnabled();

        const aiMsgDiv = appendMessage('ai', '⚡ Thinking...');

        try {
            const response = await fetch('/api/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: queryText,
                    conversation_id: convId,
                    language: lang,
                    web_search: webSearch,
                    modality: 'web_minichat'
                })
            });

            if (!response.ok) {
                aiMsgDiv.textContent = `Error: Server returned HTTP ${response.status}`;
                return;
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let fullText = '';
            aiMsgDiv.textContent = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.replace('data: ', '').trim();
                        if (dataStr === '[DONE]') break;
                        try {
                            const parsed = JSON.parse(dataStr);
                            if (parsed.token) {
                                fullText += parsed.token;
                                aiMsgDiv.textContent = fullText;
                                miniChatBody.scrollTop = miniChatBody.scrollHeight;
                            }
                        } catch (_) {}
                    }
                }
            }

            if (!fullText) {
                aiMsgDiv.textContent = 'Received response from AJAX AI.';
            }
        } catch (err) {
            aiMsgDiv.textContent = `Connection error: ${err.message}`;
        } finally {
            isStreaming = false;
        }
    }

    /**
     * Expose global helper to ask AI about specific data
     */
    window.askAjaxAbout = function(contextTitle, dataPayload) {
        ensureMiniChatDom();
        toggleMiniChat(true);

        const dataStr = typeof dataPayload === 'string' ? dataPayload : JSON.stringify(dataPayload, null, 2);
        const prompt = `Please review and summarize this live result from "${contextTitle}":\n\n${dataStr.substring(0, 2000)}`;

        appendMessage('user', `Analyze result from: ${contextTitle}`);
        executeAiStream(prompt);
    };

    document.addEventListener('DOMContentLoaded', () => {
        ensureMiniChatDom();
    });
})();

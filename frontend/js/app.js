// AJAX AI - Frontend Master Application Logic
// Optimized for Mobile Touch & Desktop Responsive Experience

const API_BASE = window.location.origin.startsWith('http') && !window.location.origin.includes(':3000') && !window.location.origin.includes(':5173')
    ? '' 
    : 'http://127.0.0.1:8000';

let convId = "web_session_" + Date.now();
let voiceReplyEnabled = false;
let isRecording = false;
let recognition = null;
let attachedDocs = [];
let webSearchEnabled = false;

/* ==============================================================================
   RESPONSIVE DRAWER & SIDEBAR TOGGLE (Mobile & PC)
   ============================================================================== */

function toggleSidebar(forceState) {
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('sidebarBackdrop');
    if (!sidebar) return;

    const isOpen = sidebar.classList.contains('open');
    const shouldOpen = forceState !== undefined ? forceState : !isOpen;

    if (shouldOpen) {
        sidebar.classList.add('open');
        if (backdrop) backdrop.classList.add('active');
    } else {
        sidebar.classList.remove('open');
        if (backdrop) backdrop.classList.remove('active');
    }
}

function autoCloseSidebarOnMobile() {
    if (window.innerWidth <= 768) {
        toggleSidebar(false);
    }
}

/* ==============================================================================
   CHAT SESSION MANAGEMENT
   ============================================================================== */

function startNewChat() {
    convId = "web_session_" + Date.now();
    attachedDocs = [];
    renderAttachedDocs();
    
    const sessionDisplay = document.getElementById('sessionDisplay');
    if (sessionDisplay) sessionDisplay.innerText = "Interactive Web Workspace";

    const chat = document.getElementById('chatContainer');
    if (chat) {
        chat.innerHTML = `
            <div class="welcome-card" id="welcomeCard">
                <div class="welcome-icon">⚡</div>
                <h2 class="welcome-title">Welcome to AJAX AI</h2>
                <p class="welcome-subtitle">
                    Cloud-native AI Assistant powered by <strong>MongoDB Atlas</strong>, DuckDuckGo Live Search & RAG Document Intelligence.
                </p>
                <div class="quick-prompts-grid">
                    <button class="prompt-chip" onclick="sendQuickPrompt('What are the latest AI developments today?')">
                        <span class="chip-icon">🌐</span>
                        <span class="chip-text">Latest AI developments</span>
                    </button>
                    <button class="prompt-chip" onclick="sendQuickPrompt('Explain quantum computing in simple terms')">
                        <span class="chip-icon">💡</span>
                        <span class="chip-text">Explain quantum computing</span>
                    </button>
                    <button class="prompt-chip" onclick="sendQuickPrompt('Write a clean Python script for FastAPI REST endpoint')">
                        <span class="chip-icon">💻</span>
                        <span class="chip-text">Write a Python FastAPI code</span>
                    </button>
                    <button class="prompt-chip" onclick="sendQuickPrompt('What do you remember about my profile and preferences?')">
                        <span class="chip-icon">🧠</span>
                        <span class="chip-text">Check persistent memories</span>
                    </button>
                </div>
            </div>
        `;
    }
    loadConversationsList();
    autoCloseSidebarOnMobile();
}

function sendQuickPrompt(promptText) {
    const input = document.getElementById('userInput');
    if (input) {
        input.value = promptText;
        sendMessage();
    }
}

/* ==============================================================================
   CONVERSATION HISTORY LOADER & SELECTION (MongoDB Atlas)
   ============================================================================== */

async function loadConversationsList() {
    const listEl = document.getElementById('conversationsList');
    if (!listEl) return;

    try {
        const res = await fetch(`${API_BASE}/api/conversations`);
        const data = await res.json();
        if (data.conversations && data.conversations.length > 0) {
            listEl.innerHTML = data.conversations.map(c => `
                <div class="chat-history-item ${c.id === convId ? 'active' : ''}" onclick="selectConversation('${c.id}')">
                    <div class="chat-history-title" title="${c.title || 'Chat Session'}">💬 ${c.title || 'Chat Session'}</div>
                    <button class="chat-del-btn" onclick="deleteConversation('${c.id}', event)" title="Delete Conversation">✕</button>
                </div>
            `).join('');
        } else {
            listEl.innerHTML = '<div class="history-loading">No past conversations.</div>';
        }
    } catch (e) {
        listEl.innerHTML = '<div class="history-loading">Failed to load history.</div>';
    }
}

async function selectConversation(selectedId) {
    convId = selectedId;
    loadConversationsList();
    autoCloseSidebarOnMobile();

    const chat = document.getElementById('chatContainer');
    if (!chat) return;
    chat.innerHTML = '<div class="message ai-msg"><div class="loading-phase-container"><div class="loading-spinner"></div><span>Loading messages from MongoDB Atlas...</span></div></div>';

    try {
        const res = await fetch(`${API_BASE}/api/conversations/${selectedId}`);
        const data = await res.json();
        chat.innerHTML = '';
        if (data.messages && data.messages.length > 0) {
            data.messages.forEach(msg => {
                const isUser = msg.role === 'user';
                const div = document.createElement('div');
                div.className = `message ${isUser ? 'user-msg' : 'ai-msg'}`;
                if (isUser) {
                    div.innerText = msg.content;
                } else {
                    div.innerHTML = renderMarkdown(msg.content);
                    applyCodeCopyButtons(div);
                }
                chat.appendChild(div);
            });
        } else {
            chat.innerHTML = '<div class="message ai-msg">👋 No messages in this session yet.</div>';
        }
        chat.scrollTop = chat.scrollHeight;

        const sessionDisplay = document.getElementById('sessionDisplay');
        if (sessionDisplay && data.conversation && data.conversation.title) {
            sessionDisplay.innerText = data.conversation.title;
        }
    } catch (e) {
        chat.innerHTML = '<div class="message ai-msg">Failed to load conversation history.</div>';
    }
}

async function deleteConversation(targetId, event) {
    if (event) event.stopPropagation();
    try {
        await fetch(`${API_BASE}/api/conversations/${targetId}`, { method: 'DELETE' });
        if (convId === targetId) {
            startNewChat();
        } else {
            loadConversationsList();
        }
    } catch (e) {}
}

/* ==============================================================================
   LIVE WEB SEARCH TOGGLE
   ============================================================================== */

function toggleWebSearch() {
    webSearchEnabled = !webSearchEnabled;
    const barBtn = document.getElementById('webSearchBtn');
    const headerBtn = document.getElementById('headerWebSearchBtn');
    const indicator = document.getElementById('webSearchIndicator');

    if (webSearchEnabled) {
        if (barBtn) barBtn.classList.add('active');
        if (headerBtn) headerBtn.classList.add('active');
        if (indicator) indicator.innerText = 'ON';
    } else {
        if (barBtn) barBtn.classList.remove('active');
        if (headerBtn) headerBtn.classList.remove('active');
        if (indicator) indicator.innerText = 'OFF';
    }
}

/* ==============================================================================
   VOICE ASSISTANT (TTS & STT)
   ============================================================================== */

function toggleVoiceSpeech() {
    voiceReplyEnabled = !voiceReplyEnabled;
    const btn = document.getElementById('ttsToggleBtn');
    const status = document.getElementById('ttsStatus');
    const icon = document.getElementById('ttsIcon');
    if (voiceReplyEnabled) {
        if (btn) btn.classList.add('active');
        if (status) status.innerText = 'ON';
        if (icon) icon.innerText = '🔊';
        speakText('Voice reply enabled.');
    } else {
        if (btn) btn.classList.remove('active');
        if (status) status.innerText = 'OFF';
        if (icon) icon.innerText = '🔈';
        if (window.speechSynthesis) window.speechSynthesis.cancel();
    }
}

function speakText(text) {
    if (!voiceReplyEnabled || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const cleanText = text.replace(/<[^>]*>?/gm, '').replace(/[*#`_]/g, '');
    const utterance = new SpeechSynthesisUtterance(cleanText.substring(0, 400));
    utterance.rate = 1.05;
    window.speechSynthesis.speak(utterance);
}

function toggleVoiceRecording() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
        alert('Speech Recognition is not supported in this browser. Please use Chrome, Edge, or Safari.');
        return;
    }

    const micBtn = document.getElementById('micBtn');
    const input = document.getElementById('userInput');

    if (isRecording) {
        if (recognition) recognition.stop();
        isRecording = false;
        if (micBtn) micBtn.classList.remove('active');
        return;
    }

    try {
        recognition = new SpeechRec();
        recognition.lang = 'en-US';
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = () => {
            isRecording = true;
            if (micBtn) micBtn.classList.add('active');
            if (input) input.placeholder = "Listening... Speak now...";
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            if (input) input.value = transcript;
        };

        recognition.onerror = () => {
            isRecording = false;
            if (micBtn) micBtn.classList.remove('active');
            if (input) input.placeholder = "Ask anything, talk via 🎙️, or upload 📎 PDF...";
        };

        recognition.onend = () => {
            isRecording = false;
            if (micBtn) micBtn.classList.remove('active');
            if (input) {
                input.placeholder = "Ask anything, talk via 🎙️, or upload 📎 PDF...";
                if (input.value.trim()) {
                    sendMessage();
                }
            }
        };

        recognition.start();
    } catch (e) {
        isRecording = false;
        if (micBtn) micBtn.classList.remove('active');
    }
}

/* ==============================================================================
   DOCUMENT UPLOAD HANDLING (RAG + Cloudinary with 15MB Limit)
   ============================================================================== */

async function handleFileSelected(input) {
    if (!input.files || !input.files[0]) return;
    const file = input.files[0];

    // Enforce 15 MB Upload Limit
    const MAX_UPLOAD_MB = 15;
    if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
        const actualMb = (file.size / (1024 * 1024)).toFixed(2);
        alert(`❌ File Too Large: Maximum allowed upload limit is ${MAX_UPLOAD_MB} MB.\nYour file '${file.name}' is ${actualMb} MB.`);
        input.value = '';
        return;
    }

    const reader = new FileReader();

    reader.onload = async (e) => {
        const base64Data = e.target.result.split(',')[1];
        try {
            const res = await fetch(`${API_BASE}/api/upload`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: file.name,
                    content_base64: base64Data
                })
            });
            const data = await res.json();
            if (data.success) {
                attachedDocs.push({ name: file.name, chunks: data.chunks });
                renderAttachedDocs();

                const chat = document.getElementById('chatContainer');
                if (chat) {
                    const welcome = document.getElementById('welcomeCard');
                    if (welcome) welcome.remove();

                    chat.innerHTML += `
                        <div class="message ai-msg">
                            📄 <strong>${file.name}</strong> uploaded and indexed successfully into RAG & Cloudinary (${data.chunks} text chunks ready). You can now ask questions about this document.
                        </div>
                    `;
                    chat.scrollTop = chat.scrollHeight;
                }
            } else {
                alert('Upload failed: ' + (data.detail || data.error || 'Unknown error'));
            }
        } catch (err) {
            alert('Error uploading file: ' + err);
        }
    };
    reader.readAsDataURL(file);
    input.value = '';
}

function renderAttachedDocs() {
    const bar = document.getElementById('attachmentBar');
    if (!bar) return;
    if (attachedDocs.length === 0) {
        bar.innerHTML = '';
        return;
    }
    bar.innerHTML = attachedDocs.map((doc, idx) => `
        <div class="attached-doc-chip">
            <span>📄 ${doc.name}</span>
            <button onclick="removeAttachedDoc(${idx})" title="Remove">✕</button>
        </div>
    `).join('');
}

function removeAttachedDoc(idx) {
    attachedDocs.splice(idx, 1);
    renderAttachedDocs();
}

/* ==============================================================================
   MESSAGING & REAL-TIME STREAMING
   ============================================================================== */

async function sendMessage() {
    const input = document.getElementById('userInput');
    if (!input) return;
    const text = input.value.trim();
    if (!text) return;

    const chat = document.getElementById('chatContainer');
    if (chat) {
        const welcome = document.getElementById('welcomeCard');
        if (welcome) welcome.remove();

        chat.innerHTML += `<div class="message user-msg">${escapeHtml(text)}</div>`;
        chat.scrollTop = chat.scrollHeight;
    }
    input.value = '';

    const aiPlaceholder = document.createElement('div');
    aiPlaceholder.className = 'message ai-msg';
    aiPlaceholder.innerHTML = `
        <div class="loading-phase-container">
            <div class="loading-spinner"></div>
            <span>${webSearchEnabled ? '🌐 Searching live web & synthesizing sources...' : '⚡ AJAX is thinking...'}</span>
        </div>
    `;
    if (chat) {
        chat.appendChild(aiPlaceholder);
        chat.scrollTop = chat.scrollHeight;
    }

    const startTime = performance.now();
    let accumulatedText = "";
    let detectedTool = null;
    let detectedIntent = null;

    try {
        const response = await fetch(`${API_BASE}/api/chat/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: text,
                conversation_id: convId,
                web_search: webSearchEnabled
            })
        });

        if (!response.body) {
            throw new Error("Streaming not supported or failed");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n\n");
            buffer = lines.pop();

            for (const line of lines) {
                const trimmed = line.trim();
                if (trimmed.startsWith("data: ")) {
                    try {
                        const eventData = JSON.parse(trimmed.slice(6));
                        if (eventData.type === 'meta') {
                            detectedIntent = eventData.intent;
                            detectedTool = eventData.tool;
                        } else if (eventData.type === 'token') {
                            accumulatedText += eventData.token;
                            aiPlaceholder.innerHTML = renderMarkdown(accumulatedText);
                            if (chat) chat.scrollTop = chat.scrollHeight;
                        } else if (eventData.type === 'done') {
                            if (eventData.response && !accumulatedText) {
                                accumulatedText = eventData.response;
                            }
                            if (eventData.tool) detectedTool = eventData.tool;
                            if (eventData.intent) detectedIntent = eventData.intent;
                        }
                    } catch (err) {}
                }
            }
        }

        const latency = Math.round(performance.now() - startTime);
        let toolHtml = detectedTool ? `<span class="tool-badge">⚡ ${detectedTool}</span>` : '';
        let speedHtml = `<span class="speed-badge">${latency}ms</span>`;
        let badgesHtml = `<div class="meta-badges">${toolHtml} ${speedHtml}</div>`;

        aiPlaceholder.innerHTML = renderMarkdown(accumulatedText || "Action completed.") + badgesHtml;
        applyCodeCopyButtons(aiPlaceholder);
        if (chat) chat.scrollTop = chat.scrollHeight;

        loadConversationsList();
        speakText(accumulatedText);
    } catch (err) {
        aiPlaceholder.innerText = "Error processing request: " + err;
    }
}

/* ==============================================================================
   MARKDOWN RENDERING & CODE COPY
   ============================================================================== */

function renderMarkdown(raw) {
    if (window.marked) {
        try {
            marked.setOptions({
                highlight: (code, lang) => {
                    if (window.hljs && hljs.getLanguage(lang)) {
                        return hljs.highlight(code, { language: lang }).value;
                    }
                    return code;
                },
                breaks: true,
                gfm: true
            });
            return marked.parse(raw);
        } catch (e) {
            return raw;
        }
    }
    return raw;
}

function applyCodeCopyButtons(container) {
    container.querySelectorAll('pre').forEach(pre => {
        if (!pre.querySelector('.copy-code-btn')) {
            const btn = document.createElement('button');
            btn.className = 'copy-code-btn';
            btn.innerText = 'Copy';
            btn.onclick = () => {
                const codeText = pre.querySelector('code')?.innerText || pre.innerText;
                navigator.clipboard.writeText(codeText);
                btn.innerText = 'Copied!';
                setTimeout(() => btn.innerText = 'Copy', 2000);
            };
            pre.appendChild(btn);
        }
    });
}

function escapeHtml(string) {
    const entityMap = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    };
    return String(string).replace(/[&<>"']/g, s => entityMap[s]);
}

// Attach global action helpers
window.toggleSidebar = toggleSidebar;
window.autoCloseSidebarOnMobile = autoCloseSidebarOnMobile;
window.startNewChat = startNewChat;
window.sendQuickPrompt = sendQuickPrompt;
window.loadConversationsList = loadConversationsList;
window.sendMessage = sendMessage;
window.toggleWebSearch = toggleWebSearch;
window.toggleVoiceSpeech = toggleVoiceSpeech;
window.toggleVoiceRecording = toggleVoiceRecording;
window.handleFileSelected = handleFileSelected;

// Initial setup and click listeners
window.addEventListener('DOMContentLoaded', () => {
    loadConversationsList();

    const hamburger = document.querySelector('.hamburger-btn');
    if (hamburger) {
        hamburger.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleSidebar(true);
        });
    }

    const closeBtn = document.querySelector('.mobile-close-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleSidebar(false);
        });
    }

    const backdrop = document.getElementById('sidebarBackdrop');
    if (backdrop) {
        backdrop.addEventListener('click', () => {
            toggleSidebar(false);
        });
    }
});

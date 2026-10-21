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
let currentLanguage = 'en'; // Default is English

/* ==============================================================================
   LANGUAGE TOGGLE (English Default & Hindi Mode)
   ============================================================================== */

function setLanguage(lang) {
    currentLanguage = (lang === 'hi') ? 'hi' : 'en';

    const btnEn = document.getElementById('langBtnEn');
    const btnHi = document.getElementById('langBtnHi');
    if (btnEn) btnEn.classList.toggle('active', currentLanguage === 'en');
    if (btnHi) btnHi.classList.toggle('active', currentLanguage === 'hi');

    // Update speech recognition language if initialized
    if (recognition) {
        recognition.lang = currentLanguage === 'hi' ? 'hi-IN' : 'en-US';
    }

    // Dynamic input placeholder
    const input = document.getElementById('userInput');
    if (input && !isRecording) {
        if (currentLanguage === 'hi') {
            input.placeholder = "कुछ भी पूछें, बोलें 🎙️ या फाइल अपलोड करें 📎...";
        } else {
            input.placeholder = "Ask anything, talk via 🎙️, or upload 📎 PDF...";
        }
    }

    try {
        localStorage.setItem('ajax_lang', currentLanguage);
    } catch (e) {}
}

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
    utterance.lang = currentLanguage === 'hi' ? 'hi-IN' : 'en-US';
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
        recognition.lang = currentLanguage === 'hi' ? 'hi-IN' : 'en-US';
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = () => {
            isRecording = true;
            if (micBtn) micBtn.classList.add('active');
            if (input) input.placeholder = currentLanguage === 'hi' ? "सुन रहा हूँ... बोलिए..." : "Listening... Speak now...";
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            if (input) input.value = transcript;
        };

        recognition.onerror = () => {
            isRecording = false;
            if (micBtn) micBtn.classList.remove('active');
            if (input) input.placeholder = currentLanguage === 'hi' ? "कुछ भी पूछें, बोलें 🎙️ या फाइल अपलोड करें 📎..." : "Ask anything, talk via 🎙️, or upload 📎 PDF...";
        };

        recognition.onend = () => {
            isRecording = false;
            if (micBtn) micBtn.classList.remove('active');
            if (input) {
                input.placeholder = currentLanguage === 'hi' ? "कुछ भी पूछें, बोलें 🎙️ या फाइल अपलोड करें 📎..." : "Ask anything, talk via 🎙️, or upload 📎 PDF...";
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
            <span>${webSearchEnabled ? (currentLanguage === 'hi' ? '🌐 लाइव वेब सर्च और जानकारी जुटाई जा रही है...' : '🌐 Searching live web & synthesizing sources...') : (currentLanguage === 'hi' ? '⚡ AJAX सोच रहा है...' : '⚡ AJAX is thinking...')}</span>
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
                web_search: webSearchEnabled,
                language: currentLanguage
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
window.setLanguage = setLanguage;

/* ==============================================================================
   PUBLIC API HUB, SCHEMA STUDIO & LOOP DETECTION MONITOR
   ============================================================================== */

let allApiProviders = [];

function openApiHubModal() {
    const modal = document.getElementById('apiHubModal');
    if (modal) {
        modal.classList.add('open');
        if (!allApiProviders || allApiProviders.length === 0) {
            loadProvidersCatalog();
        }
    }
}

function closeApiHubModal() {
    const modal = document.getElementById('apiHubModal');
    if (modal) modal.classList.remove('open');
}

function switchApiTab(tabKey) {
    const tabMap = {
        catalog: { btn: 'tabBtnCatalog', pane: 'paneCatalog' },
        schema: { btn: 'tabBtnSchema', pane: 'paneSchema' },
        loops: { btn: 'tabBtnLoops', pane: 'paneLoops' },
        health: { btn: 'tabBtnHealth', pane: 'paneHealth' }
    };

    Object.keys(tabMap).forEach(key => {
        const item = tabMap[key];
        const btn = document.getElementById(item.btn);
        const pane = document.getElementById(item.pane);
        if (btn) btn.classList.toggle('active', key === tabKey);
        if (pane) pane.classList.toggle('active', key === tabKey);
    });

    if (tabKey === 'health') {
        const grid = document.getElementById('healthGrid');
        if (grid && grid.querySelector('.api-loading')) {
            loadHealthChecksUI();
        }
    }
}

async function loadProvidersCatalog() {
    const grid = document.getElementById('providersGrid');
    const select = document.getElementById('categoryFilterSelect');
    if (!grid) return;

    grid.innerHTML = '<div class="api-loading">Fetching verified provider registry...</div>';

    try {
        const res = await fetch(`${API_BASE}/api/connectors/providers`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        allApiProviders = data.providers || [];

        // Populate Category Filter dropdown
        if (select) {
            const categories = Array.from(new Set(allApiProviders.map(p => p.category))).sort();
            select.innerHTML = '<option value="">All 11 Categories</option>' + 
                categories.map(c => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join('');
        }

        renderProvidersUI(allApiProviders);
    } catch (err) {
        grid.innerHTML = `<div class="api-loading" style="color:#f87171;">Failed to load catalog: ${escapeHtml(err.message)}</div>`;
    }
}

function renderProvidersUI(providers) {
    const grid = document.getElementById('providersGrid');
    if (!grid) return;

    if (!providers || providers.length === 0) {
        grid.innerHTML = '<div class="api-loading">No providers matching query.</div>';
        return;
    }

    grid.innerHTML = providers.map(p => {
        let badgeClass = 'badge-live';
        if (p.data_classification === 'calculated') badgeClass = 'badge-calc';
        else if (p.data_classification === 'static_reference') badgeClass = 'badge-static';
        else if (p.data_classification === 'sample') badgeClass = 'badge-sample';

        const rateLimitText = p.rate_limit_per_minute 
            ? `${p.rate_limit_per_minute} req/min` 
            : (p.quota_period || 'Verified safe');

        return `
            <div class="provider-card">
                <div class="provider-card-header">
                    <h4>${escapeHtml(p.provider_name)}</h4>
                    <span class="badge-tag ${badgeClass}">${escapeHtml(p.data_classification || 'LIVE')}</span>
                </div>
                <p class="provider-desc">${escapeHtml(p.description || '')}</p>
                <div class="provider-meta-row">
                    <span><strong>Category:</strong> ${escapeHtml(p.category)}</span>
                    <span><strong>Auth:</strong> ${escapeHtml(p.auth_type)}</span>
                    <span><strong>Limits:</strong> ${escapeHtml(rateLimitText)}</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
                    <button class="test-live-btn" onclick="testProviderLive('${escapeHtml(p.provider_id)}')">⚡ Test Live Data</button>
                    ${p.documentation_url ? `<a href="${escapeHtml(p.documentation_url)}" target="_blank" rel="noopener" style="font-size:11.5px; color:var(--accent-cyan); text-decoration:none;">Docs ↗</a>` : ''}
                </div>
                <div id="liveResult_${escapeHtml(p.provider_id)}" class="live-result-drawer" style="display:none; margin-top:8px;"></div>
            </div>
        `;
    }).join('');
}

async function testProviderLive(providerId) {
    const box = document.getElementById(`liveResult_${providerId}`);
    if (!box) return;

    box.style.display = 'block';
    box.innerHTML = '<div class="api-loading">Executing live request through SSRF proxy...</div>';

    try {
        const res = await fetch(`${API_BASE}/api/connectors/health/check/${encodeURIComponent(providerId)}`, {
            method: 'POST'
        });
        const data = await res.json();
        const isHealthy = data.is_healthy;
        const latency = data.latency_ms !== null ? `${data.latency_ms.toFixed(1)} ms` : 'N/A';
        const sample = data.sample_data || { status: data.http_status, message: "Response received" };

        const sampleJsonString = JSON.stringify(sample);

        box.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <span style="font-size:11px; font-weight:600; color:${isHealthy ? '#22c55e' : '#ef4444'};">
                    ${isHealthy ? '✓ LIVE 200 OK' : '⚠ NOTICE'} (${latency})
                </span>
                <button class="schema-primary-btn" style="padding:2px 8px; font-size:10.5px;" onclick='sendLiveToSchema(${escapeHtml(JSON.stringify(sampleJsonString))})'>
                    📋 Map to Schema
                </button>
            </div>
            <pre style="margin:0; max-height:120px; overflow-y:auto; font-size:10.5px; background:rgba(0,0,0,0.4); padding:6px; border-radius:4px; color:#cbd5e1; font-family:'JetBrains Mono',monospace;">${escapeHtml(JSON.stringify(sample, null, 2))}</pre>
        `;
    } catch (err) {
        box.innerHTML = `<div style="font-size:11px; color:#ef4444;">Live query failed: ${escapeHtml(err.message)}</div>`;
    }
}

function sendLiveToSchema(jsonString) {
    switchApiTab('schema');
    const input = document.getElementById('schemaJsonInput');
    const pathInput = document.getElementById('schemaDataPathInput');
    if (input) {
        try {
            input.value = JSON.stringify(JSON.parse(jsonString), null, 2);
        } catch (e) {
            input.value = jsonString;
        }
    }
    if (pathInput) pathInput.value = "";
    inferSchemaFromUI();
}

function filterProvidersUI() {
    const search = (document.getElementById('providerSearchInput')?.value || '').toLowerCase().trim();
    const category = document.getElementById('categoryFilterSelect')?.value || '';

    const filtered = allApiProviders.filter(p => {
        const matchesCategory = !category || p.category === category;
        const name = (p.provider_name || p.name || '').toLowerCase();
        const id = (p.provider_id || p.id || '').toLowerCase();
        const desc = (p.description || p.attribution || '').toLowerCase();
        const matchesSearch = !search || 
            name.includes(search) || 
            id.includes(search) || 
            desc.includes(search);
        return matchesCategory && matchesSearch;
    });

    renderProvidersUI(filtered);
}

function loadPresetApiSample(presetKey) {
    const samples = {
        weather: {
            path: "current_weather",
            data: {
                latitude: 28.61,
                longitude: 77.20,
                elevation: 216.0,
                timezone: "GMT",
                current_weather: {
                    temperature: 29.4,
                    windspeed: 12.2,
                    winddirection: 195,
                    weathercode: 1,
                    is_day: 1,
                    time: "2026-10-21T04:00"
                }
            }
        },
        iss: {
            path: "",
            data: {
                name: "iss",
                id: 25544,
                latitude: -14.28,
                longitude: -12.44,
                altitude: 418.52,
                velocity: 27612.4,
                visibility: "daylight",
                footprint: 4501.2,
                timestamp: 1761021400
            }
        },
        earthquake: {
            path: "features[0].properties",
            data: {
                type: "FeatureCollection",
                metadata: { status: 200, count: 1, title: "USGS Earthquakes" },
                features: [{
                    type: "Feature",
                    properties: {
                        mag: 4.8,
                        place: "92 km NE of Tokyo, Japan",
                        time: 1761021200000,
                        url: "https://earthquake.usgs.gov/earthquakes/event/us7000test",
                        tsunami: 0,
                        alert: "green"
                    }
                }]
            }
        },
        fx: {
            path: "rates",
            data: {
                amount: 1.0,
                base: "USD",
                date: "2026-10-21",
                rates: { EUR: 0.92, INR: 84.15, GBP: 0.77, JPY: 152.4 }
            }
        },
        holidays: {
            path: "[0]",
            data: [{
                date: "2026-11-08",
                localName: "Diwali",
                name: "Deepavali",
                countryCode: "IN",
                fixed: false,
                global: true
            }]
        },
        countries: {
            path: "[0]",
            data: [{
                name: { common: "India", official: "Republic of India" },
                capital: ["New Delhi"],
                region: "Asia",
                population: 1428627663,
                currencies: { INR: { name: "Indian Rupee", symbol: "₹" } }
            }]
        },
        demo: {
            path: "",
            data: {
                userId: 1,
                id: 1,
                title: "Public API Integration Standard",
                body: "Verified automated schema parsing with loop detection and rate limiting."
            }
        }
    };

    if (!presetKey || !samples[presetKey]) return;

    const item = samples[presetKey];
    const input = document.getElementById('schemaJsonInput');
    const pathInput = document.getElementById('schemaDataPathInput');
    if (input) input.value = JSON.stringify(item.data, null, 2);
    if (pathInput) pathInput.value = item.path;
    inferSchemaFromUI();
}

function loadSampleWeatherJson() {
    loadPresetApiSample("weather");
}

async function inferSchemaFromUI() {
    const input = document.getElementById('schemaJsonInput');
    const pathInput = document.getElementById('schemaDataPathInput');
    const preview = document.getElementById('schemaPreviewBox');
    if (!preview) return;

    const rawText = (input?.value || '').trim();
    if (!rawText) {
        alert("Please enter a sample JSON payload first or click 'Load Sample Weather'");
        return;
    }

    let parsed;
    try {
        parsed = JSON.parse(rawText);
    } catch (e) {
        alert("Invalid JSON format: " + e.message);
        return;
    }

    preview.innerHTML = '<div class="api-loading">Analyzing payload & inferring 14 types...</div>';

    try {
        const res = await fetch(`${API_BASE}/api/connectors/schema/infer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sample_json: parsed,
                data_path: (pathInput?.value || '').trim() || null
            })
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const fields = data.fields || [];

        if (fields.length === 0) {
            preview.innerHTML = '<div class="schema-placeholder-text">No fields could be extracted at this path.</div>';
            return;
        }

        preview.innerHTML = `
            <div style="font-size:11.5px; color:#22c55e; margin-bottom:10px; font-weight:600;">
                ✓ Successfully inferred ${fields.length} schema fields (Version: ${escapeHtml(data.schema_version)})
            </div>
            ${fields.map(f => `
                <div class="schema-field-card">
                    <div>
                        <div class="field-info-title">${escapeHtml(f.label)}</div>
                        <div class="field-info-meta">key: <strong>${escapeHtml(f.field_key)}</strong> | path: <code>${escapeHtml(f.json_path)}</code></div>
                    </div>
                    <span class="field-type-pill">${escapeHtml(f.field_type)}</span>
                </div>
            `).join('')}
        `;
    } catch (err) {
        preview.innerHTML = `<div class="api-loading" style="color:#f87171;">Inference failed: ${escapeHtml(err.message)}</div>`;
    }
}

async function testWorkflowCycleDetection(simulateCycle) {
    const box = document.getElementById('cycleResultBox');
    if (!box) return;

    box.innerText = "Analyzing directed graph with Tarjan's DFS algorithm...";

    const edges = simulateCycle ? [
        { from_step: "Weather_Fetch", to_step: "Schema_Generator" },
        { from_step: "Schema_Generator", to_step: "Refresh_Workflow" },
        { from_step: "Refresh_Workflow", to_step: "Weather_Fetch" }
    ] : [
        { from_step: "Weather_Fetch", to_step: "Schema_Generator" },
        { from_step: "Schema_Generator", to_step: "Form_Renderer" }
    ];

    try {
        const res = await fetch(`${API_BASE}/api/connectors/loop/validate-workflow`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ workflow_id: "test_pipeline", edges: edges })
        });

        const data = await res.json();
        if (data.is_valid_dag) {
            box.innerText = `✅ VALID DIRECTED ACYCLIC GRAPH (DAG)\nNo cycles found. Workflow execution is safe to schedule.`;
            box.style.borderColor = 'rgba(34, 197, 94, 0.4)';
        } else {
            const cycles = (data.detected_cycles || []).map(c => c.join(' ➔ ')).join('\n');
            box.innerText = `🚨 CYCLE REJECTED BY LOOP GUARD:\n${cycles}\nError: ${data.error_message}`;
            box.style.borderColor = 'rgba(239, 68, 68, 0.5)';
        }
    } catch (err) {
        box.innerText = `Error running cycle check: ${err.message}`;
    }
}

async function loadHealthChecksUI() {
    const grid = document.getElementById('healthGrid');
    if (!grid) return;

    grid.innerHTML = '<div class="api-loading">Dispatching lightweight canary probes...</div>';

    try {
        const res = await fetch(`${API_BASE}/api/connectors/health`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const checks = data.health_checks || [];

        if (checks.length === 0) {
            grid.innerHTML = '<div class="api-loading">No health reports available.</div>';
            return;
        }

        grid.innerHTML = checks.map(c => {
            const isUp = c.is_healthy;
            const latency = c.latency_ms !== null ? `${c.latency_ms.toFixed(1)} ms` : 'N/A';
            const breakerState = c.circuit_breaker_state || 'CLOSED';

            return `
                <div class="health-card">
                    <div class="health-card-top">
                        <span class="health-provider-name">${escapeHtml(c.provider_id)}</span>
                        <span class="health-pill ${isUp ? 'up' : 'down'}">${isUp ? 'UP (200)' : 'DOWN'}</span>
                    </div>
                    <div class="health-meta">
                        Latency: <strong>${latency}</strong> | Breaker: <strong>${escapeHtml(breakerState)}</strong>
                    </div>
                    ${c.last_error ? `<div style="font-size:10.5px; color:#f87171; overflow:hidden; text-overflow:ellipsis;">${escapeHtml(c.last_error)}</div>` : ''}
                </div>
            `;
        }).join('');
    } catch (err) {
        grid.innerHTML = `<div class="api-loading" style="color:#f87171;">Telemetry failed: ${escapeHtml(err.message)}</div>`;
    }
}

let healthPollInterval = null;

function toggleHealthAutoPoll() {
    const btn = document.getElementById('healthPollToggleBtn');
    const badge = document.getElementById('healthPollBadge');
    if (healthPollInterval) {
        clearInterval(healthPollInterval);
        healthPollInterval = null;
        if (btn) {
            btn.innerText = '⚡ Auto-Poll: OFF';
            btn.classList.remove('active');
        }
        if (badge) {
            badge.innerText = 'IDLE';
            badge.classList.remove('active');
        }
    } else {
        loadHealthChecksUI();
        healthPollInterval = setInterval(loadHealthChecksUI, 20000); // Poll every 20 seconds
        if (btn) {
            btn.innerText = '● Auto-Poll: ON (20s)';
            btn.classList.add('active');
        }
        if (badge) {
            badge.innerText = 'POLLING';
            badge.classList.add('active');
        }
    }
}

// Attach public API studio actions to window
window.openApiHubModal = openApiHubModal;
window.closeApiHubModal = closeApiHubModal;
window.switchApiTab = switchApiTab;
window.loadProvidersCatalog = loadProvidersCatalog;
window.filterProvidersUI = filterProvidersUI;
window.inferSchemaFromUI = inferSchemaFromUI;
window.loadSampleWeatherJson = loadSampleWeatherJson;
window.loadPresetApiSample = loadPresetApiSample;
window.testProviderLive = testProviderLive;
window.sendLiveToSchema = sendLiveToSchema;
window.testWorkflowCycleDetection = testWorkflowCycleDetection;
window.loadHealthChecksUI = loadHealthChecksUI;
window.toggleHealthAutoPoll = toggleHealthAutoPoll;

// Initial setup and click listeners
window.addEventListener('DOMContentLoaded', () => {
    // English is the default language
    try {
        const savedLang = localStorage.getItem('ajax_lang');
        setLanguage(savedLang === 'hi' ? 'hi' : 'en');
    } catch (e) {
        setLanguage('en');
    }

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


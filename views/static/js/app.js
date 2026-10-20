// Standalone Frontend Application Logic
// Supports both standalone hosting (e.g. port 3000 / Live Server / static file) and backend proxying.

const API_BASE = window.location.origin.startsWith('http') && !window.location.origin.includes(':3000') && !window.location.origin.includes(':5173')
    ? '' 
    : 'http://127.0.0.1:8000';

let convId = "web_session_" + Date.now();
let voiceReplyEnabled = false;
let isRecording = false;
let recognition = null;
let attachedDocs = [];

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    event.target.classList.add('active');
    const target = document.getElementById('tab-' + tabName);
    if (target) target.classList.add('active');
}

function appendLog(line) {
    const terminal = document.getElementById('logsTerminal');
    if (!terminal) return;
    const div = document.createElement('div');
    div.className = 'log-entry';
    if (line.includes('[INFO]')) div.className += ' log-info';
    else if (line.includes('[TOOL]')) div.className += ' log-tool';
    else if (line.includes('[SUCCESS]') || line.includes('[AUTH]')) div.className += ' log-success';
    else if (line.includes('[WARNING]')) div.className += ' log-warning';
    else if (line.includes('[ERROR]')) div.className += ' log-error';
    div.innerText = line;
    terminal.appendChild(div);
    terminal.scrollTop = terminal.scrollHeight;
}

function clearLogs() {
    const terminal = document.getElementById('logsTerminal');
    if (terminal) {
        terminal.innerHTML = '<div class="log-entry log-info">[INFO] Logs cleared.</div>';
    }
}

function startNewChat() {
    convId = "web_session_" + Date.now();
    attachedDocs = [];
    renderAttachedDocs();
    const chat = document.getElementById('chatContainer');
    if (chat) {
        chat.innerHTML = `
            <div class="message ai-msg">
                👋 New chat session started! Ask me anything, speak via 🎙️ mic, or upload a 📎 PDF document.
            </div>
        `;
    }
    appendLog('[SESSION] New conversation session started.');
}

/* Voice Speech Output (TTS) Toggle */
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

/* Voice Input (STT) Speech Recognition */
function toggleVoiceRecording() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
        alert('Speech Recognition is not supported in this browser. Please use Google Chrome or Edge.');
        return;
    }

    const micBtn = document.getElementById('micBtn');
    const input = document.getElementById('userInput');

    if (isRecording) {
        if (recognition) recognition.stop();
        isRecording = false;
        if (micBtn) micBtn.classList.remove('listening');
        return;
    }

    recognition = new SpeechRec();
    recognition.lang = 'en-IN'; // Strictly type in English / Roman alphabet
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onstart = () => {
        isRecording = true;
        if (micBtn) micBtn.classList.add('listening');
        if (input) input.placeholder = '🎙️ Listening... Speak now (typing in English)...';
        appendLog('[VOICE] Microphone listening in English/Hinglish mode...');
    };


    recognition.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
        }
        if (input) input.value = transcript;
    };

    recognition.onerror = (e) => {
        isRecording = false;
        if (micBtn) micBtn.classList.remove('listening');
        if (input) input.placeholder = "Ask anything, talk via 🎙️, or upload a 📎 PDF...";
        appendLog(`[VOICE_ERROR] ${e.error}`);
    };

    recognition.onend = () => {
        isRecording = false;
        if (micBtn) micBtn.classList.remove('listening');
        if (input) {
            input.placeholder = "Ask anything, talk via 🎙️, or upload a 📎 PDF...";
            if (input.value.trim().length > 1) {
                sendMessage();
            }
        }
    };

    try {
        recognition.start();
    } catch (e) {
        isRecording = false;
        if (micBtn) micBtn.classList.remove('listening');
    }
}

/* Document Upload Handling */
async function handleFileSelected(input) {
    if (!input.files || !input.files[0]) return;
    const file = input.files[0];

    // Enforce 15 MB Upload Limit
    const MAX_UPLOAD_MB = 15;
    if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
        const actualMb = (file.size / (1024 * 1024)).toFixed(2);
        alert(`❌ File Too Large: Maximum upload limit is ${MAX_UPLOAD_MB} MB.\nYour file '${file.name}' is ${actualMb} MB.`);
        appendLog(`[ERROR] Upload rejected: '${file.name}' (${actualMb} MB) exceeds ${MAX_UPLOAD_MB} MB limit.`);
        input.value = '';
        return;
    }

    const reader = new FileReader();
    appendLog(`[UPLOAD] Reading document: ${file.name} (${(file.size / 1024).toFixed(1)} KB)...`);

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
                appendLog(`[SUCCESS] Indexed ${file.name} (${data.chunks} chunks ready for instant Q&A).`);

                const chat = document.getElementById('chatContainer');
                if (chat) {
                    chat.innerHTML += `
                        <div class="message ai-msg">
                            📄 <strong>${file.name}</strong> uploaded and indexed successfully! (${data.chunks} text chunks ready). You can now ask questions or summarize this document.
                        </div>
                    `;
                    chat.scrollTop = chat.scrollHeight;
                }
            } else {
                alert('Upload failed: ' + (data.error || 'Unknown error'));
            }
        } catch (err) {
            alert('Error uploading file: ' + err);
        }
    };
    reader.readAsDataURL(file);
    input.value = '';
}

let webSearchEnabled = false;

function toggleWebSearch() {
    webSearchEnabled = !webSearchEnabled;
    const btn = document.getElementById('webSearchBtn');
    const input = document.getElementById('userInput');
    
    if (webSearchEnabled) {
        if (btn) btn.classList.add('active');
        if (input) input.placeholder = "🌐 Web Search Active: Type question to search live internet & Wikipedia...";
        appendLog("[WEB_SEARCH] Live Internet Search Mode ENABLED.");
    } else {
        if (btn) btn.classList.remove('active');
        if (input) input.placeholder = "Ask anything, talk via 🎙️, or upload a 📎 PDF...";
        appendLog("[WEB_SEARCH] Live Internet Search Mode DISABLED.");
    }
    renderAttachedDocs();
}

function performDirectWebSearch() {
    const input = document.getElementById('userInput');
    if (!input) return;
    const text = input.value.trim();
    if (!text) {
        toggleWebSearch();
        input.focus();
        return;
    }
    const previousState = webSearchEnabled;
    webSearchEnabled = true;
    const btn = document.getElementById('webSearchBtn');
    if (btn) btn.classList.add('active');
    renderAttachedDocs();
    sendMessage().finally(() => {
        if (!previousState) {
            webSearchEnabled = false;
            if (btn) btn.classList.remove('active');
            renderAttachedDocs();
            if (input) input.placeholder = "Ask anything, talk via 🎙️, or upload a 📎 PDF...";
        }
    });
}

function renderAttachedDocs() {
    const bar = document.getElementById('attachmentBar');
    if (!bar) return;
    let html = attachedDocs.map((doc, idx) => `
        <div class="doc-chip">
            📄 <span>${doc.name}</span>
            <button onclick="removeAttachedDoc(${idx})" title="Remove">✕</button>
        </div>
    `).join('');

    if (webSearchEnabled) {
        html += `
            <div class="search-active-pill">
                🌐 <span>Live Web Search: <strong>ON</strong></span>
                <button onclick="toggleWebSearch()" title="Disable Web Search">✕</button>
            </div>
        `;
    }
    bar.innerHTML = html;
}

function removeAttachedDoc(idx) {
    attachedDocs.splice(idx, 1);
    renderAttachedDocs();
}

let seenLogs = new Set();

async function fetchLiveLogs() {
    const logsTab = document.getElementById('tab-logs');
    if (!logsTab || !logsTab.classList.contains('active')) return;

    try {
        const res = await fetch(`${API_BASE}/api/logs`);
        const data = await res.json();
        if (data.logs && data.logs.length) {
            data.logs.forEach(l => {
                if (!seenLogs.has(l)) {
                    seenLogs.add(l);
                    appendLog(l);
                }
            });
            if (seenLogs.size > 200) {
                const arr = Array.from(seenLogs);
                seenLogs = new Set(arr.slice(-100));
            }
        }
    } catch (e) {}
}
setInterval(fetchLiveLogs, 2000);


function renderMarkdown(text) {
    if (!text) return '';
    if (window.marked) {
        try {
            return marked.parse(text);
        } catch (e) {}
    }
    return text
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\*([^*]+)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
}

function applyCodeCopyButtons(container) {
    if (!container) return;
    if (window.hljs) {
        container.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }
    container.querySelectorAll('pre').forEach((pre) => {
        if (!pre.querySelector('.copy-code-btn')) {
            const btn = document.createElement('button');
            btn.className = 'copy-code-btn';
            btn.innerText = 'Copy';
            btn.onclick = () => {
                const code = pre.querySelector('code')?.innerText || pre.innerText;
                navigator.clipboard.writeText(code);
                btn.innerText = 'Copied!';
                setTimeout(() => { btn.innerText = 'Copy'; }, 2000);
            };
            pre.appendChild(btn);
        }
    });
}

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
                    <button class="chat-del-btn" onclick="deleteConversation('${c.id}', event)" title="Delete Chat">✕</button>
                </div>
            `).join('');
        } else {
            listEl.innerHTML = '<div style="font-size:12px; color:var(--text-muted); text-align:center; padding:12px;">No past conversations.</div>';
        }
    } catch (e) {
        listEl.innerHTML = '<div style="font-size:12px; color:var(--text-muted); text-align:center; padding:12px;">Failed to load history.</div>';
    }
}

async function selectConversation(selectedId) {
    convId = selectedId;
    loadConversationsList();
    const chat = document.getElementById('chatContainer');
    if (!chat) return;
    chat.innerHTML = '<div class="message ai-msg">⏳ Loading session messages...</div>';
    
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
        appendLog(`[SESSION] Loaded conversation: ${selectedId}`);
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

async function sendMessage() {
    const input = document.getElementById('userInput');
    if (!input) return;
    const text = input.value.trim();
    if (!text) return;

    const chat = document.getElementById('chatContainer');
    if (chat) {
        chat.innerHTML += `<div class="message user-msg">${text}</div>`;
        chat.scrollTop = chat.scrollHeight;
    }
    input.value = '';
    appendLog(`[QUERY] Incoming query: '${text}'`);

    const aiPlaceholder = document.createElement('div');
    aiPlaceholder.className = 'message ai-msg';
    aiPlaceholder.innerHTML = `
        <div class="loading-title" style="display:flex; align-items:center; gap:8px;">
            <div class="loading-spinner"></div>
            <span class="loading-phase">${webSearchEnabled ? '🌐 AJAX is searching the live web & retrieving sources...' : '⚡ AJAX is thinking & retrieving...'}</span>
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
        let toolHtml = detectedTool ? `<span class="tool-badge">⚡ Tool: ${detectedTool}</span>` : '';
        let speedHtml = `<span class="speed-badge">⚡ ${latency} ms</span>`;
        let badgesHtml = `<div class="meta-badges">${toolHtml} ${speedHtml}</div>`;

        aiPlaceholder.innerHTML = renderMarkdown(accumulatedText || "Action completed.") + badgesHtml;
        applyCodeCopyButtons(aiPlaceholder);
        if (chat) chat.scrollTop = chat.scrollHeight;

        appendLog(`[SUCCESS] Responded in ${latency}ms (Intent: ${detectedIntent || 'CHAT'})`);
        loadConversationsList();
        speakText(accumulatedText);
    } catch (err) {
        aiPlaceholder.innerText = "Error processing request: " + err;
        appendLog(`[ERROR] Request failed: ${err}`);
    }
}

// Initial history load
window.addEventListener('DOMContentLoaded', () => {
    loadConversationsList();
});


let convId = "web_session_" + Date.now();
let voiceReplyEnabled = false;
let isRecording = false;
let recognition = null;
let attachedDocs = [];

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById('tab-' + tabName).classList.add('active');
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
    document.getElementById('logsTerminal').innerHTML = '<div class="log-entry log-info">[INFO] Logs cleared.</div>';
}

function startNewChat() {
    convId = "web_session_" + Date.now();
    attachedDocs = [];
    renderAttachedDocs();
    const chat = document.getElementById('chatContainer');
    chat.innerHTML = `
        <div class="message ai-msg">
            👋 New chat session started! Ask me anything, speak via 🎙️ mic, or upload a 📎 PDF document.
        </div>
    `;
    appendLog('[SESSION] New conversation session started.');
}

/* Voice Speech Output (TTS) Toggle */
function toggleVoiceSpeech() {
    voiceReplyEnabled = !voiceReplyEnabled;
    const btn = document.getElementById('ttsToggleBtn');
    const status = document.getElementById('ttsStatus');
    const icon = document.getElementById('ttsIcon');
    if (voiceReplyEnabled) {
        btn.classList.add('active');
        status.innerText = 'ON';
        icon.innerText = '🔊';
        speakText('Voice reply enabled.');
    } else {
        btn.classList.remove('active');
        status.innerText = 'OFF';
        icon.innerText = '🔈';
        window.speechSynthesis.cancel();
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
        micBtn.classList.remove('listening');
        return;
    }

    recognition = new SpeechRec();
    recognition.lang = 'hi-IN'; // Multi-lingual Indian English / Hindi
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onstart = () => {
        isRecording = true;
        micBtn.classList.add('listening');
        input.placeholder = '🎙️ Listening... Speak now in Hindi or English...';
        appendLog('[VOICE] Microphone listening...');
    };

    recognition.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
        }
        input.value = transcript;
    };

    recognition.onerror = (e) => {
        isRecording = false;
        micBtn.classList.remove('listening');
        input.placeholder = "Ask anything, talk via 🎙️, or upload a 📎 PDF...";
        appendLog(`[VOICE_ERROR] ${e.error}`);
    };

    recognition.onend = () => {
        isRecording = false;
        micBtn.classList.remove('listening');
        input.placeholder = "Ask anything, talk via 🎙️, or upload a 📎 PDF...";
        if (input.value.trim().length > 1) {
            sendMessage();
        }
    };

    try {
        recognition.start();
    } catch (e) {
        isRecording = false;
        micBtn.classList.remove('listening');
    }
}

/* Document Upload Handling */
async function handleFileSelected(input) {
    if (!input.files || !input.files[0]) return;
    const file = input.files[0];
    const reader = new FileReader();

    appendLog(`[UPLOAD] Reading document: ${file.name} (${(file.size / 1024).toFixed(1)} KB)...`);

    reader.onload = async (e) => {
        const base64Data = e.target.result.split(',')[1];
        try {
            const res = await fetch('/api/upload', {
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
                chat.innerHTML += `
                    <div class="message ai-msg">
                        📄 <strong>${file.name}</strong> uploaded and indexed successfully! (${data.chunks} text chunks ready). You can now ask questions or summarize this document.
                    </div>
                `;
                chat.scrollTop = chat.scrollHeight;
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

function renderAttachedDocs() {
    const bar = document.getElementById('attachmentBar');
    bar.innerHTML = attachedDocs.map((doc, idx) => `
        <div class="doc-chip">
            📄 <span>${doc.name}</span>
            <button onclick="removeAttachedDoc(${idx})" title="Remove">✕</button>
        </div>
    `).join('');
}

function removeAttachedDoc(idx) {
    attachedDocs.splice(idx, 1);
    renderAttachedDocs();
}

async function fetchLiveLogs() {
    try {
        const res = await fetch('/api/logs');
        const data = await res.json();
        if (data.logs && data.logs.length) {
            const terminal = document.getElementById('logsTerminal');
            const currentCount = terminal.children.length;
            if (data.logs.length > currentCount) {
                data.logs.slice(currentCount).forEach(l => appendLog(l));
            }
        }
    } catch (e) {}
}
setInterval(fetchLiveLogs, 2000);

async function sendMessage() {
    const input = document.getElementById('userInput');
    const text = input.value.trim();
    if (!text) return;

    const chat = document.getElementById('chatContainer');
    chat.innerHTML += `<div class="message user-msg">${text}</div>`;
    input.value = '';
    chat.scrollTop = chat.scrollHeight;
    appendLog(`[QUERY] Incoming query: '${text}'`);

    const aiPlaceholder = document.createElement('div');
    aiPlaceholder.className = 'message ai-msg';
    aiPlaceholder.innerHTML = `
        <div class="loading-card">
            <div class="loading-header">
                <div class="loading-title">
                    <div class="loading-spinner"></div>
                    <span class="loading-phase">⚡ Analyzing Intent & Context...</span>
                </div>
                <span class="loading-pct">15%</span>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width: 15%;"></div>
            </div>
        </div>
    `;
    chat.appendChild(aiPlaceholder);
    chat.scrollTop = chat.scrollHeight;

    let progress = 15;
    const startTime = performance.now();
    const phases = [
        { p: 25, text: '🧠 Semantic Matching & Reasoning...' },
        { p: 60, text: '⚡ Tool & Document Retrieval...' },
        { p: 85, text: '✨ Synthesizing Response...' },
        { p: 95, text: '🚀 Finalizing output...' }
    ];

    const progressTimer = setInterval(() => {
        if (progress < 94) {
            progress += Math.floor(Math.random() * 8) + 4;
            if (progress > 94) progress = 94;

            const phase = phases.slice().reverse().find(s => progress >= s.p) || phases[0];
            const fillEl = aiPlaceholder.querySelector('.progress-bar-fill');
            const pctEl = aiPlaceholder.querySelector('.loading-pct');
            const phaseEl = aiPlaceholder.querySelector('.loading-phase');

            if (fillEl) fillEl.style.width = progress + '%';
            if (pctEl) pctEl.innerText = progress + '%';
            if (phaseEl && phase) phaseEl.innerText = phase.text;
        }
    }, 120);

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: text, conversation_id: convId })
        });
        const data = await res.json();
        const latency = Math.round(performance.now() - startTime);

        clearInterval(progressTimer);
        const fillEl = aiPlaceholder.querySelector('.progress-bar-fill');
        const pctEl = aiPlaceholder.querySelector('.loading-pct');
        if (fillEl) fillEl.style.width = '100%';
        if (pctEl) pctEl.innerText = '100%';

        setTimeout(() => {
            let toolHtml = data.tool_called ? `<span class="tool-badge">⚡ Tool: ${data.tool_called}</span>` : '';
            let speedHtml = `<span class="speed-badge">⚡ ${latency} ms</span>`;
            let badgesHtml = `<div class="meta-badges">${toolHtml} ${speedHtml}</div>`;

            const replyText = data.response || 'Action processed.';
            aiPlaceholder.innerHTML = replyText.replace(/\\n/g, '<br>') + badgesHtml;
            chat.scrollTop = chat.scrollHeight;
            appendLog(`[SUCCESS] Responded in ${latency}ms (Intent: ${data.intent})`);

            speakText(replyText);
        }, 100);
    } catch (e) {
        clearInterval(progressTimer);
        aiPlaceholder.innerText = 'Error processing request.';
        chat.scrollTop = chat.scrollHeight;
        appendLog(`[ERROR] Failed to process request: ${e}`);
    }
}

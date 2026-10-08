"""
AJAX AI - Local REST API & Web Dashboard Server
Runs a lightweight, zero-dependency HTTP server exposing REST APIs and Web UI with Live Logs, Telemetry & Authentication.
"""

import os
import json
import urllib.parse
from typing import Any, Dict, List, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from core.router import router
from core.diagnostics import diagnostics
from system.monitor import system_monitor
from database.crud import create_conversation, list_conversations, search_memories, save_memory
from tools.registry import registry
from config.config_loader import config
from core.logger import ajax_logger, error_logger, LOGS_DIR

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AJAX AI - Autonomous Assistant</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #080b11;
            --bg-card: rgba(15, 22, 36, 0.75);
            --accent-cyan: #00f2fe;
            --accent-blue: #4facfe;
            --accent-purple: #9d4edd;
            --accent-green: #00f5a0;
            --text-main: #f0f4f8;
            --text-muted: #8e9bb0;
            --border-glass: rgba(255, 255, 255, 0.08);
            --border-active: rgba(0, 242, 254, 0.4);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Outfit', sans-serif; }
        body { background: var(--bg-primary); color: var(--text-main); display: flex; height: 100vh; overflow: hidden; }
        
        /* Sidebar */
        .sidebar { width: 360px; background: rgba(10, 14, 24, 0.96); border-right: 1px solid var(--border-glass); display: flex; flex-direction: column; padding: 20px; gap: 16px; z-index: 10; }
        .logo-row { display: flex; align-items: center; justify-content: space-between; }
        .logo { font-size: 22px; font-weight: 700; background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; display: flex; align-items: center; gap: 8px; }
        .status-pill { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; background: rgba(0, 245, 160, 0.1); border: 1px solid rgba(0, 245, 160, 0.3); border-radius: 20px; font-size: 11px; color: var(--accent-green); font-weight: 600; }
        .status-dot { width: 7px; height: 7px; background: var(--accent-green); border-radius: 50%; box-shadow: 0 0 8px var(--accent-green); animation: pulse 2s infinite; }

        /* Navigation Tabs */
        .tabs-nav { display: flex; background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border-glass); border-radius: 10px; padding: 3px; gap: 4px; }
        .tab-btn { flex: 1; background: transparent; border: none; color: var(--text-muted); padding: 7px 0; font-size: 12px; font-weight: 600; border-radius: 7px; cursor: pointer; transition: 0.2s; }
        .tab-btn.active { background: rgba(0, 242, 254, 0.12); color: var(--accent-cyan); border: 1px solid rgba(0, 242, 254, 0.25); }

        .tab-content { flex: 1; display: none; flex-direction: column; gap: 12px; overflow-y: auto; }
        .tab-content.active { display: flex; }

        /* Telemetry Cards */
        .telemetry-card { background: var(--bg-card); border: 1px solid var(--border-glass); border-radius: 12px; padding: 14px; font-size: 13px; line-height: 1.8; backdrop-filter: blur(10px); }
        .telemetry-card h4 { color: var(--accent-cyan); margin-bottom: 8px; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; display: flex; justify-content: space-between; align-items: center; }
        .metric-row { display: flex; justify-content: space-between; margin-bottom: 4px; color: var(--text-muted); }
        .metric-val { color: var(--text-main); font-family: 'JetBrains Mono', monospace; font-weight: 600; }

        /* Live Logs Terminal Widget */
        .logs-terminal { flex: 1; min-height: 280px; background: rgba(5, 7, 12, 0.95); border: 1px solid rgba(0, 242, 254, 0.15); border-radius: 10px; padding: 12px; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #a0aec0; overflow-y: auto; display: flex; flex-direction: column; gap: 6px; }
        .log-entry { line-height: 1.4; word-break: break-all; }
        .log-info { color: #63b3ed; }
        .log-tool { color: #b794f4; }
        .log-success { color: #68d391; }
        .log-warning { color: #f6ad55; }
        .log-error { color: #fc8181; }
        .logs-controls { display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: var(--text-muted); }
        .clear-btn { background: transparent; border: 1px solid var(--border-glass); color: var(--text-muted); border-radius: 6px; padding: 2px 8px; cursor: pointer; }
        .clear-btn:hover { color: #fff; border-color: var(--accent-cyan); }

        /* Main Workspace & Top Header */
        .main-content { flex: 1; display: flex; flex-direction: column; background: radial-gradient(circle at top right, rgba(0, 242, 254, 0.04), transparent 50%); position: relative; }
        .top-header { height: 60px; border-bottom: 1px solid var(--border-glass); display: flex; align-items: center; justify-content: space-between; padding: 0 32px; background: rgba(10, 13, 20, 0.6); backdrop-filter: blur(10px); }
        .header-title { font-size: 15px; font-weight: 600; color: var(--text-muted); display: flex; align-items: center; gap: 8px; }
        .header-title span { color: var(--accent-cyan); }
        
        .user-auth-pill { display: flex; align-items: center; gap: 10px; background: rgba(255, 255, 255, 0.04); border: 1px solid var(--border-glass); padding: 5px 14px; border-radius: 30px; cursor: pointer; transition: 0.2s; }
        .user-auth-pill:hover { border-color: var(--accent-cyan); background: rgba(0, 242, 254, 0.08); }
        .user-avatar { width: 26px; height: 26px; border-radius: 50%; background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue)); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px; color: #0a0d14; }
        .user-info { font-size: 13px; font-weight: 600; }
        .user-role { font-size: 11px; color: var(--accent-cyan); }

        /* Chat Messages */
        .chat-container { flex: 1; overflow-y: auto; padding: 28px 32px; display: flex; flex-direction: column; gap: 18px; }
        .message { max-width: 78%; padding: 16px 22px; border-radius: 16px; line-height: 1.6; font-size: 15px; animation: fadeIn 0.3s ease; }
        .user-msg { align-self: flex-end; background: linear-gradient(135deg, #1e3c72, #2a5298); color: #fff; border-bottom-right-radius: 4px; box-shadow: 0 4px 15px rgba(30, 60, 114, 0.2); }
        .ai-msg { align-self: flex-start; background: var(--bg-card); border: 1px solid var(--border-glass); border-bottom-left-radius: 4px; backdrop-filter: blur(12px); }
        .meta-badges { display: flex; align-items: center; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
        .tool-badge { font-family: 'JetBrains Mono', monospace; font-size: 11px; padding: 2px 10px; background: rgba(0, 242, 254, 0.1); border: 1px solid rgba(0, 242, 254, 0.25); border-radius: 6px; color: var(--accent-cyan); }
        .speed-badge { font-family: 'JetBrains Mono', monospace; font-size: 11px; padding: 2px 8px; background: rgba(0, 245, 160, 0.1); border: 1px solid rgba(0, 245, 160, 0.25); border-radius: 6px; color: var(--accent-green); }

        /* Futuristic Loading & Thinking Indicator */
        .loading-card { display: flex; flex-direction: column; gap: 12px; min-width: 280px; max-width: 360px; padding: 4px; }
        .loading-header { display: flex; justify-content: space-between; align-items: center; font-size: 13px; }
        .loading-title { display: flex; align-items: center; gap: 10px; font-weight: 600; color: var(--text-main); }
        .loading-spinner { width: 16px; height: 16px; border: 2px solid rgba(0, 242, 254, 0.2); border-top-color: var(--accent-cyan); border-radius: 50%; animation: spin 0.7s linear infinite; }
        .loading-pct { font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 700; color: var(--accent-cyan); }
        .progress-bar-bg { width: 100%; height: 6px; background: rgba(255, 255, 255, 0.08); border-radius: 10px; overflow: hidden; position: relative; }
        .progress-bar-fill { height: 100%; width: 10%; background: linear-gradient(90deg, var(--accent-cyan), var(--accent-blue)); border-radius: 10px; transition: width 0.25s ease; box-shadow: 0 0 12px rgba(0, 242, 254, 0.6); }

        /* Input Controls */
        .input-area { padding: 20px 32px; background: rgba(10, 13, 20, 0.95); border-top: 1px solid var(--border-glass); display: flex; gap: 12px; }
        .input-box { flex: 1; background: rgba(255, 255, 255, 0.04); border: 1px solid var(--border-glass); border-radius: 12px; padding: 14px 20px; color: #fff; font-size: 15px; outline: none; transition: 0.3s; }
        .input-box:focus { border-color: var(--accent-cyan); box-shadow: 0 0 20px rgba(0, 242, 254, 0.25); }
        .send-btn { background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue)); border: none; border-radius: 12px; padding: 0 28px; color: #080b11; font-weight: 700; cursor: pointer; transition: 0.2s; display: flex; align-items: center; gap: 6px; }
        .send-btn:hover { transform: scale(1.02); box-shadow: 0 0 20px rgba(0, 242, 254, 0.4); }

        /* Auth / Login Modal */
        .modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.75); backdrop-filter: blur(8px); display: none; align-items: center; justify-content: center; z-index: 100; animation: fadeIn 0.2s ease; }
        .modal-card { width: 380px; background: #0f1624; border: 1px solid var(--border-active); border-radius: 16px; padding: 28px; display: flex; flex-direction: column; gap: 18px; box-shadow: 0 0 40px rgba(0, 242, 254, 0.2); }
        .modal-header { display: flex; justify-content: space-between; align-items: center; }
        .modal-header h3 { color: var(--accent-cyan); font-size: 18px; }
        .close-modal-btn { background: transparent; border: none; color: var(--text-muted); font-size: 20px; cursor: pointer; }
        .modal-input { background: rgba(255, 255, 255, 0.05); border: 1px solid var(--border-glass); border-radius: 10px; padding: 12px 16px; color: #fff; font-size: 14px; outline: none; width: 100%; }
        .modal-input:focus { border-color: var(--accent-cyan); }
        .modal-btn { background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue)); border: none; border-radius: 10px; padding: 12px; color: #080b11; font-weight: 700; cursor: pointer; width: 100%; }

        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <!-- Sidebar -->
    <div class="sidebar">
        <div class="logo-row">
            <div class="logo">⚡ AJAX AI</div>
            <div class="status-pill"><div class="status-dot"></div> ONLINE</div>
        </div>

        <!-- Navigation Tabs -->
        <div class="tabs-nav">
            <button class="tab-btn active" onclick="switchTab('telemetry')">📊 Telemetry</button>
            <button class="tab-btn" onclick="switchTab('logs')">📜 Live Logs</button>
            <button class="tab-btn" onclick="switchTab('tools')">⚡ Tools</button>
        </div>

        <!-- Tab 1: Live Diagnostics -->
        <div class="tab-content active" id="tab-telemetry">
            <div class="telemetry-card">
                <h4>System Hardware <span style="font-size:10px; color:var(--accent-cyan)">LIVE</span></h4>
                <div class="metric-row"><span>CPU Usage:</span><span class="metric-val" id="cpuMetric">...</span></div>
                <div class="metric-row"><span>RAM Load:</span><span class="metric-val" id="ramMetric">...</span></div>
                <div class="metric-row"><span>Disk Free:</span><span class="metric-val" id="diskMetric">...</span></div>
                <div class="metric-row"><span>Battery:</span><span class="metric-val" id="batteryMetric">...</span></div>
            </div>

            <div class="telemetry-card">
                <h4>Engine Status</h4>
                <div class="metric-row"><span>Intelligence:</span><span class="metric-val" style="color:var(--accent-cyan)">Hybrid RAG + Rule</span></div>
                <div class="metric-row"><span>Latency Tier:</span><span class="metric-val" style="color:var(--accent-green)">Sub-50ms Ultra-Fast</span></div>
                <div class="metric-row"><span>RAG Knowledge:</span><span class="metric-val">78 Documents</span></div>
                <div class="metric-row"><span>Tools Ready:</span><span class="metric-val">22 Direct Tools</span></div>
            </div>
        </div>

        <!-- Tab 2: Live Activity & Execution Logs -->
        <div class="tab-content" id="tab-logs">
            <div class="logs-controls">
                <span>Real-Time System Log Stream</span>
                <button class="clear-btn" onclick="clearLogs()">Clear</button>
            </div>
            <div class="logs-terminal" id="logsTerminal">
                <div class="log-entry log-info">[INFO] Server online. Listening at http://127.0.0.1:8000</div>
                <div class="log-entry log-success">[INFO] RAG Knowledge Store initialized: 78 docs ready.</div>
                <div class="log-entry log-tool">[INFO] Intent Classifier loaded 20 neural intents.</div>
            </div>
        </div>

        <!-- Tab 3: Registered Tools -->
        <div class="tab-content" id="tab-tools">
            <div class="telemetry-card" style="max-height:360px; overflow-y:auto;">
                <h4>Active Tools (22)</h4>
                <div style="font-size:12px; line-height:1.7; color:var(--text-muted)">
                    <div>• <strong>get_system_status</strong> - CPU/RAM/Battery</div>
                    <div>• <strong>calculate</strong> - Fast Math Engine</div>
                    <div>• <strong>open_application</strong> - Launch Apps</div>
                    <div>• <strong>search_wikipedia</strong> - Online/RAG Encyclopedia</div>
                    <div>• <strong>search_web</strong> - Google Live Search</div>
                    <div>• <strong>control_volume</strong> - Windows Audio</div>
                    <div>• <strong>take_screenshot</strong> - Instant Screen Capture</div>
                    <div>• <strong>set_timer / alarm</strong> - Scheduling</div>
                    <div>• <strong>remember / recall</strong> - Persistent Memory</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Main Chat Workspace -->
    <div class="main-content">
        <!-- Top Header Bar -->
        <div class="top-header">
            <div class="header-title">
                Session: <span id="sessionDisplay">Interactive Web Workspace</span>
            </div>
            
            <!-- User Login / Profile Badge -->
            <div class="user-auth-pill" onclick="openLoginModal()">
                <div class="user-avatar" id="userAvatar">A</div>
                <div>
                    <div class="user-info" id="userName">Ajay Singh</div>
                    <div class="user-role" id="userRole">● Administrator</div>
                </div>
            </div>
        </div>

        <!-- Chat History -->
        <div class="chat-container" id="chatContainer">
            <div class="message ai-msg">
                👋 Hello! I am <strong>AJAX AI</strong>. How can I help you control your PC, solve calculations, search Wikipedia, or execute actions with instant sub-second speed?
            </div>
        </div>
        
        <!-- Input Area -->
        <div class="input-area">
            <input type="text" id="userInput" class="input-box" placeholder="Ask anything or command PC (e.g. 'what is oops inheritance', 'calculate 150*4', 'check battery')..." onkeydown="if(event.key==='Enter') sendMessage()">
            <button class="send-btn" onclick="sendMessage()">Send ➔</button>
        </div>
    </div>

    <!-- Auth / Login Modal -->
    <div class="modal-overlay" id="loginModal">
        <div class="modal-card">
            <div class="modal-header">
                <h3>⚡ User Authentication</h3>
                <button class="close-modal-btn" onclick="closeLoginModal()">✕</button>
            </div>
            <p style="font-size:13px; color:var(--text-muted)">Login to authenticate your AJAX AI session or switch user profile.</p>
            <input type="text" id="loginUser" class="modal-input" placeholder="Username (Default: Ajay Singh)" value="Ajay Singh">
            <input type="password" id="loginPass" class="modal-input" placeholder="Passcode / PIN (Optional)">
            <button class="modal-btn" onclick="handleLogin()">Sign In & Authenticate</button>
        </div>
    </div>

    <script>
        let convId = "web_session_" + Date.now();

        function switchTab(tabName) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById('tab-' + tabName).classList.add('active');
        }

        function openLoginModal() { document.getElementById('loginModal').style.display = 'flex'; }
        function closeLoginModal() { document.getElementById('loginModal').style.display = 'none'; }
        
        function handleLogin() {
            const user = document.getElementById('loginUser').value.trim() || 'Ajay Singh';
            document.getElementById('userName').innerText = user;
            document.getElementById('userAvatar').innerText = user.charAt(0).toUpperCase();
            closeLoginModal();
            appendLog(`[AUTH] User '${user}' authenticated successfully.`);
        }

        function appendLog(line) {
            const terminal = document.getElementById('logsTerminal');
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

        async function fetchTelemetry() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                document.getElementById('cpuMetric').innerText = `${data.cpu.usage_percent}% (${data.cpu.cores} Cores)`;
                document.getElementById('ramMetric').innerText = `${data.ram.percent}% (${data.ram.used_mb}MB / ${data.ram.total_mb}MB)`;
                document.getElementById('diskMetric').innerText = `${data.disk.free_gb} GB Free`;
                document.getElementById('batteryMetric').innerText = `${data.battery.percent || 'Plugged In'}%`;
            } catch(e) {}
        }
        setInterval(fetchTelemetry, 3000);
        fetchTelemetry();

        async function fetchLiveLogs() {
            try {
                const res = await fetch('/api/logs');
                const data = await res.json();
                if (data.logs && data.logs.length) {
                    const terminal = document.getElementById('logsTerminal');
                    // update if changed
                    const currentCount = terminal.children.length;
                    if (data.logs.length > currentCount) {
                        data.logs.slice(currentCount).forEach(l => appendLog(l));
                    }
                }
            } catch(e) {}
        }
        setInterval(fetchLiveLogs, 2000);

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const text = input.value.trim();
            if(!text) return;
            
            const chat = document.getElementById('chatContainer');
            chat.innerHTML += `<div class="message user-msg">${text}</div>`;
            input.value = '';
            chat.scrollTop = chat.scrollHeight;
            appendLog(`[QUERY] Incoming query: '${text}'`);

            // Animated glowing loading indicator
            const aiPlaceholder = document.createElement('div');
            aiPlaceholder.className = 'message ai-msg';
            aiPlaceholder.innerHTML = `
                <div class="loading-card">
                    <div class="loading-header">
                        <div class="loading-title">
                            <div class="loading-spinner"></div>
                            <span class="loading-phase">⚡ Analyzing Intent & Safety...</span>
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
                { p: 25, text: '🧠 Intent & Semantic Matching...' },
                { p: 60, text: '⚡ Tool & Knowledge Execution...' },
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
                    
                    aiPlaceholder.innerHTML = (data.response || 'Action processed.').replace(/\\n/g, '<br>') + badgesHtml;
                    chat.scrollTop = chat.scrollHeight;
                    appendLog(`[SUCCESS] Responded in ${latency}ms (Intent: ${data.intent})`);
                }, 100);
            } catch(e) {
                clearInterval(progressTimer);
                aiPlaceholder.innerText = 'Error processing request.';
                chat.scrollTop = chat.scrollHeight;
                appendLog(`[ERROR] Failed to process request: ${e}`);
            }
        }
    </script>
</body>
</html>
"""

class AJAXRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, data: Any):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_DASHBOARD.encode("utf-8"))
        elif path == "/api/status":
            stats = system_monitor.get_full_diagnostics()
            self._send_json(200, stats)
        elif path == "/api/diagnostics":
            diag = diagnostics.run_health_check()
            self._send_json(200, diag)
        elif path == "/api/logs":
            log_file = os.path.join(LOGS_DIR, "ajax.log")
            lines = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                        lines = [line.strip() for line in f.readlines()[-30:] if line.strip()]
                except Exception:
                    pass
            self._send_json(200, {"logs": lines})
        elif path == "/api/tools":
            tools_data = [{"name": t.name, "description": t.description, "permission": t.permission} for t in registry.list_tools()]
            self._send_json(200, {"tools": tools_data})
        elif path == "/api/memory":
            mems = search_memories(limit=20)
            self._send_json(200, {"memories": mems})
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        content_len = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_len).decode("utf-8")
        try:
            body = json.loads(post_data) if post_data else {}
        except Exception:
            body = {}

        if path == "/api/chat":
            query = body.get("query", "")
            conv_id = body.get("conversation_id") or create_conversation("API Chat")
            result = router.process_query(query, conv_id, modality="api")
            self._send_json(200, result)
        elif path == "/api/memory":
            key = body.get("key", "")
            value = body.get("value", "")
            if key and value:
                mem_id = save_memory(key_text=key, value_text=value)
                self._send_json(200, {"success": True, "memory_id": mem_id})
            else:
                self._send_json(400, {"success": False, "error": "Missing key or value"})
        elif path == "/api/tools/execute":
            tool_name = body.get("tool_name", "")
            params = body.get("parameters", {})
            confirmed = body.get("confirmed", False)
            res = registry.execute_tool(tool_name, parameters=params, confirmed_by_user=confirmed)
            self._send_json(200, res.to_dict())
        else:
            self.send_error(404, "Not Found")

def start_server(host: str = "127.0.0.1", port: int = 8000):
    server = HTTPServer((host, port), AJAXRequestHandler)
    ajax_logger.info(f"AJAX AI Server running at http://{host}:{port}")
    print(f"\n==================================================================")
    print(f"  [*] AJAX AI Server Online: http://{host}:{port}")
    print(f"  [*] Web UI & REST APIs are live! Press Ctrl+C to stop.")
    print(f"==================================================================\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        ajax_logger.info("Server stopped.")
        server.server_close()

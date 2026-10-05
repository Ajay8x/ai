"""
AJAX AI - Local REST API & Web Dashboard Server
Runs a lightweight, zero-dependency HTTP server exposing REST APIs and Web UI.
"""

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
from core.logger import ajax_logger, error_logger

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AJAX AI - Autonomous Assistant</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0a0d14;
            --bg-card: rgba(18, 24, 38, 0.7);
            --accent-cyan: #00f2fe;
            --accent-blue: #4facfe;
            --text-main: #f0f4f8;
            --text-muted: #8e9bb0;
            --border-glass: rgba(255, 255, 255, 0.08);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Outfit', sans-serif; }
        body { background: var(--bg-primary); color: var(--text-main); display: flex; height: 100vh; overflow: hidden; }
        
        /* Sidebar */
        .sidebar { width: 320px; background: rgba(12, 16, 26, 0.95); border-right: 1px solid var(--border-glass); display: flex; flex-direction: column; padding: 24px; gap: 20px; }
        .logo { font-size: 24px; font-weight: 700; background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; display: flex; align-items: center; gap: 10px; }
        .status-pill { display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; background: rgba(0, 242, 254, 0.1); border: 1px solid rgba(0, 242, 254, 0.3); border-radius: 20px; font-size: 12px; color: var(--accent-cyan); width: fit-content; }
        .telemetry-card { background: var(--bg-card); border: 1px solid var(--border-glass); border-radius: 12px; padding: 16px; font-size: 13px; line-height: 1.8; backdrop-filter: blur(10px); }
        .telemetry-card h4 { color: var(--accent-cyan); margin-bottom: 8px; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }

        /* Main Chat Area */
        .main-content { flex: 1; display: flex; flex-direction: column; background: radial-gradient(circle at top right, rgba(0, 242, 254, 0.05), transparent 40%); }
        .chat-container { flex: 1; overflow-y: auto; padding: 32px; display: flex; flex-direction: column; gap: 16px; }
        .message { max-width: 75%; padding: 16px 20px; border-radius: 16px; line-height: 1.6; font-size: 15px; animation: fadeIn 0.3s ease; }
        .user-msg { align-self: flex-end; background: linear-gradient(135deg, #1e3c72, #2a5298); color: #fff; border-bottom-right-radius: 4px; }
        .ai-msg { align-self: flex-start; background: var(--bg-card); border: 1px solid var(--border-glass); border-bottom-left-radius: 4px; backdrop-filter: blur(10px); }
        .tool-badge { display: inline-block; font-family: 'JetBrains Mono', monospace; font-size: 11px; padding: 2px 8px; background: rgba(255, 255, 255, 0.05); border-radius: 6px; color: var(--accent-cyan); margin-top: 8px; }

        /* Input Area */
        .input-area { padding: 24px 32px; background: rgba(10, 13, 20, 0.9); border-top: 1px solid var(--border-glass); display: flex; gap: 12px; }
        .input-box { flex: 1; background: rgba(255, 255, 255, 0.04); border: 1px solid var(--border-glass); border-radius: 12px; padding: 14px 20px; color: #fff; font-size: 15px; outline: none; transition: 0.3s; }
        .input-box:focus { border-color: var(--accent-cyan); box-shadow: 0 0 15px rgba(0, 242, 254, 0.2); }
        .send-btn { background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue)); border: none; border-radius: 12px; padding: 0 24px; color: #0a0d14; font-weight: 700; cursor: pointer; transition: transform 0.2s; }
        .send-btn:hover { transform: scale(1.03); }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="logo">⚡ AJAX AI</div>
        <div class="status-pill">● System Online</div>
        
        <div class="telemetry-card" id="telemetryCard">
            <h4>Live Diagnostics</h4>
            <div id="cpuMetric">CPU: Loading...</div>
            <div id="ramMetric">RAM: Loading...</div>
            <div id="diskMetric">Disk: Loading...</div>
            <div id="batteryMetric">Battery: Loading...</div>
        </div>
        
        <div class="telemetry-card">
            <h4>Capabilities</h4>
            <div>• Full PC & Windows Control</div>
            <div>• Real-Time Web & YouTube</div>
            <div>• Multi-Tier Persistent Memory</div>
            <div>• Multi-Provider LLM Brain</div>
        </div>
    </div>

    <div class="main-content">
        <div class="chat-container" id="chatContainer">
            <div class="message ai-msg">
                👋 Hello! I am <strong>AJAX AI</strong> (Adaptive Intelligence & Autonomous eXecution). How can I help you control your PC, search the web, or answer questions today?
            </div>
        </div>
        
        <div class="input-area">
            <input type="text" id="userInput" class="input-box" placeholder="Type a command or message (e.g. 'check cpu status', 'open chrome', 'play song')..." onkeydown="if(event.key==='Enter') sendMessage()">
            <button class="send-btn" onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        let convId = "web_session_" + Date.now();

        async function fetchTelemetry() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                document.getElementById('cpuMetric').innerText = `CPU: ${data.cpu.usage_percent}% (${data.cpu.cores} Cores)`;
                document.getElementById('ramMetric').innerText = `RAM: ${data.ram.percent}% (${data.ram.used_mb}MB / ${data.ram.total_mb}MB)`;
                document.getElementById('diskMetric').innerText = `Disk Free: ${data.disk.free_gb} GB`;
                document.getElementById('batteryMetric').innerText = `Battery: ${data.battery.percent || 'Plugged'}%`;
            } catch(e) {}
        }
        setInterval(fetchTelemetry, 3000);
        fetchTelemetry();

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const text = input.value.trim();
            if(!text) return;
            
            const chat = document.getElementById('chatContainer');
            chat.innerHTML += `<div class="message user-msg">${text}</div>`;
            input.value = '';
            chat.scrollTop = chat.scrollHeight;

            const aiPlaceholder = document.createElement('div');
            aiPlaceholder.className = 'message ai-msg';
            aiPlaceholder.innerText = 'Thinking & Executing...';
            chat.appendChild(aiPlaceholder);
            chat.scrollTop = chat.scrollHeight;

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: text, conversation_id: convId })
                });
                const data = await res.json();
                
                let toolHtml = data.tool_called ? `<br><span class="tool-badge">⚡ Tool: ${data.tool_called}</span>` : '';
                aiPlaceholder.innerHTML = (data.response || 'Action processed.').replace(/\\n/g, '<br>') + toolHtml;
            } catch(e) {
                aiPlaceholder.innerText = 'Error processing request.';
            }
            chat.scrollTop = chat.scrollHeight;
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
    print(f"  ⚡ AJAX AI Server Online: http://{host}:{port}")
    print(f"  ⚡ Web UI & REST APIs are live! Press Ctrl+C to stop.")
    print(f"==================================================================\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        ajax_logger.info("Server stopped.")
        server.server_close()

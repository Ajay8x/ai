"""
AJAX AI - Interactive Command Line Interface (CLI)
Supports full chat, voice trigger, slash commands, diagnostics, and settings management.
"""

import sys
import json
from core.router import router
from database.crud import create_conversation, list_conversations, search_memories, delete_memory
from tools.registry import registry
from core.diagnostics import diagnostics
from system.monitor import system_monitor
from config.config_loader import config
from voice.manager import voice_manager
from voice.tts import tts_engine

BANNER = r"""
================================================================================
     _     _   _  __  __     _    ___ 
    / \   | | / \ \ \/ /    / \  |_ _|
   / _ \  | |/ _ \ \  /    / _ \  | | 
  / ___ \ |_/ ___ \/  \   / ___ \ | | 
 /_/   \_\_/_/   \/_/\_\ /_/   \_|___|
 Adaptive Intelligence & Autonomous eXecution
================================================================================
 Type your query or use slash commands (e.g. /help, /status, /tools, /voice, /exit)
"""

class AJAXCLI:
    def __init__(self):
        self.conversation_id = create_conversation("CLI Session")

    def print_help(self):
        print("\n--- AVAILABLE COMMANDS ---")
        print("  /chat <msg>      : Send a chat query")
        print("  /voice           : Start voice assistant mode")
        print("  /tools           : List all registered tools")
        print("  /status          : Show live CPU, RAM, Disk, and Battery diagnostics")
        print("  /diagnostics     : Run system & subsystem health checks")
        print("  /memory          : List saved long-term memories")
        print("  /settings        : Display current configuration")
        print("  /clear           : Start a new conversation context")
        print("  /help            : Show this help menu")
        print("  /exit            : Quit AJAX AI\n")

    def run(self):
        print(BANNER)
        
        while True:
            try:
                user_input = input("\nAJAX >> ").strip()
                if not user_input:
                    continue

                if user_input.startswith("/"):
                    parts = user_input.split(" ", 1)
                    cmd = parts[0].lower()
                    arg = parts[1].strip() if len(parts) > 1 else ""

                    if cmd in ("/exit", "/quit", "/q"):
                        print("Goodbye! Exiting AJAX AI.")
                        break
                    elif cmd == "/help":
                        self.print_help()
                    elif cmd == "/status":
                        stats = system_monitor.get_full_diagnostics()
                        print("\n[SYSTEM TELEMETRY]")
                        print(f" CPU Usage: {stats['cpu']['usage_percent']}% ({stats['cpu']['cores']} Cores)")
                        print(f" RAM: {stats['ram']['used_mb']}MB / {stats['ram']['total_mb']}MB ({stats['ram']['percent']}%)")
                        print(f" Disk Free: {stats['disk']['free_gb']}GB ({stats['disk']['percent']}% used)")
                        print(f" Battery: {stats['battery']['percent']}%")
                    elif cmd == "/diagnostics":
                        diag = diagnostics.run_health_check()
                        print("\n[HEALTH DIAGNOSTICS]")
                        print(f" Overall Status: {diag['overall_status']}")
                        for k, v in diag["subsystems"].items():
                            print(f"  - {k.upper()}: {v}")
                    elif cmd == "/tools":
                        tools_list = registry.list_tools()
                        print(f"\n[REGISTERED TOOLS ({len(tools_list)})]")
                        for t in tools_list:
                            print(f"  • {t.name:<20} [{t.permission:<16}] : {t.description}")
                    elif cmd == "/memory":
                        mems = search_memories(limit=15)
                        print(f"\n[SAVED MEMORIES ({len(mems)})]")
                        for m in mems:
                            print(f"  • [{m['category']}] {m['key_text']} = {m['value_text']} (ID: {m['id']})")
                    elif cmd == "/settings":
                        print("\n[CURRENT CONFIGURATION]")
                        print(f"  LLM Provider : {config.llm.provider}")
                        print(f"  LLM Model    : {config.llm.model}")
                        print(f"  Voice Rate   : {config.voice.rate}")
                        print(f"  Safety Level : {config.safety.level}")
                    elif cmd == "/clear":
                        self.conversation_id = create_conversation("CLI Session")
                        print("Conversation context cleared. Started fresh session.")
                    elif cmd == "/voice":
                        print("Starting voice mode... Press Ctrl+C to return to CLI.")
                        try:
                            voice_manager.run_loop()
                        except KeyboardInterrupt:
                            print("\nVoice mode stopped.")
                    elif cmd == "/chat":
                        if arg:
                            self.handle_query(arg)
                        else:
                            print("Please provide a query (e.g. /chat What is python?)")
                    else:
                        print(f"Unknown command '{cmd}'. Type /help for available options.")
                else:
                    self.handle_query(user_input)

            except KeyboardInterrupt:
                print("\nSession interrupted. Exiting.")
                break
            except Exception as e:
                print(f"Error: {e}")

    def handle_query(self, query: str):
        res = router.process_query(query, self.conversation_id, modality="cli")
        print(f"\nAJAX: {res['response']}")
        if res.get("tool_called"):
            print(f" [Tools Used: {res['tool_called']}]")

cli = AJAXCLI()

"""
AJAX AI - Interactive Command Line Interface (CLI)
Provides rich interactive terminal sessions with slash commands and full conversational agent.
"""

import sys
import os
import readline if sys.platform != "win32" else None
from core.router import router
from database.crud import create_conversation, list_conversations, get_conversation_messages, save_memory, search_memories
from core.diagnostics import diagnostics
from system.monitor import system_monitor
from tools.registry import registry
from plugins.manager import plugin_manager
from config.config_loader import config
from voice.manager import voice_manager

BANNER = r"""
    ___       __ ___   _  __     ___    ____
   /   |     / //   | | |/ /    /   |  /  _/
  / /| |__  / // /| | |   /    / /| |  / /  
 / ___ / /_/ // ___ |/   |    / ___ |_/ /   
/_/  |_\____//_/  |_/_/|_|   /_/  |_/___/   
  Autonomous Assistant & Cognitive Engine
"""

HELP_TEXT = """
Available Commands:
  /chat <message>   - Send a query directly to AJAX AI (or just type directly)
  /voice            - Launch hands-free continuous voice session
  /model [name]     - View or switch active LLM provider (ollama, openai, groq)
  /train            - Run neural intent training on candidate examples
  /evaluate         - Run model validation and accuracy evaluation
  /memory [search]  - Inspect or search stored long-term memories
  /tools            - List all registered system automation tools
  /plugins          - List discovered plugins and their status
  /status           - Display real-time CPU, RAM, Disk, and Battery telemetry
  /diagnostics      - Run comprehensive system health check
  /settings         - View active configuration parameters
  /clear            - Clear terminal screen
  /help             - Show this help menu
  /exit or /quit    - Exit the CLI session
"""

def print_colored(text: str, color_code: str = "36"):
    print(f"\033[{color_code}m{text}\033[0m")

class AJAXCli:
    def __init__(self):
        self.conv_id = create_conversation("CLI Session")

    def run(self):
        print("\033[36m" + BANNER + "\033[0m")
        print("Type \033[33m/help\033[0m for available commands, or just type your query directly.")
        print(f"Active Session ID: \033[32m{self.conv_id}\033[0m\n")

        while True:
            try:
                user_input = input("\033[1;36mAJAX ❯ \033[0m").strip()
                if not user_input:
                    continue

                if user_input in ["/exit", "/quit", "exit", "quit"]:
                    print("\033[33mShutting down AJAX CLI. Goodbye!\033[0m")
                    break

                if user_input.startswith("/"):
                    self.handle_command(user_input)
                else:
                    self.handle_chat(user_input)

            except (KeyboardInterrupt, EOFError):
                print("\n\033[33mSession interrupted. Exiting...\033[0m")
                break
            except Exception as e:
                print(f"\033[31m[ERROR] {e}\033[0m")

    def handle_chat(self, query: str):
        print("\033[90mThinking...\033[0m", end="\r", flush=True)
        res = router.process_query(query, conversation_id=self.conv_id, modality="cli")
        intent = res.get("intent", "GENERAL_CHAT")
        conf = res.get("confidence", 0.0)
        tool = res.get("tool_called")
        resp_text = res.get("response", "")

        meta_info = f"[{intent} | {conf:.2f}]"
        if tool:
            meta_info += f" [Tool: {tool}]"

        print(f"\033[32mAJAX \033[90m{meta_info}\033[0m:\n{resp_text}\n")

    def handle_command(self, cmd_line: str):
        parts = cmd_line.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd == "/help":
            print(HELP_TEXT)

        elif cmd == "/clear":
            os.system("cls" if os.name == "nt" else "clear")

        elif cmd == "/chat":
            if not arg:
                print("\033[33mUsage: /chat <your message>\033[0m")
            else:
                self.handle_chat(arg)

        elif cmd == "/voice":
            print("\033[32m[VOICE] Starting voice assistant loop... Say 'exit' or 'stop' to return to CLI.\033[0m")
            try:
                voice_manager.run_loop()
            except Exception as e:
                print(f"\033[31m[VOICE ERROR] {e}\033[0m")

        elif cmd == "/status":
            metrics = system_monitor.get_all_metrics()
            print("\n\033[1;36m=== REAL-TIME SYSTEM TELEMETRY ===\033[0m")
            print(f" • CPU:     {metrics['cpu']['usage_percent']}% ({metrics['cpu']['cores']} cores)")
            print(f" • RAM:     {metrics['ram']['used_mb']}MB / {metrics['ram']['total_mb']}MB ({metrics['ram']['percent']}%)")
            print(f" • DISK:    {metrics['disk']['free_gb']}GB free / {metrics['disk']['total_gb']}GB total ({metrics['disk']['percent']}%)")
            print(f" • BATTERY: {metrics['battery']['percent']}% (Plugged: {metrics['battery']['plugged']})\n")

        elif cmd == "/diagnostics":
            report = diagnostics.run_health_check()
            print("\n\033[1;36m=== SYSTEM HEALTH & DIAGNOSTICS ===\033[0m")
            print(f"Overall Status: \033[32m{report['overall_status']}\033[0m")
            for sub, details in report['subsystems'].items():
                print(f" • {sub.upper()}: {details}")
            print()

        elif cmd == "/tools":
            tools = registry.list_tools()
            print(f"\n\033[1;36m=== REGISTERED AUTOMATION TOOLS ({len(tools)}) ===\033[0m")
            for t in tools:
                print(f" • \033[33m{t.name:<24}\033[0m [{t.permission}] - {t.description}")
            print()

        elif cmd == "/plugins":
            plugins = plugin_manager.list_plugins()
            print(f"\n\033[1;36m=== DISCOVERED PLUGINS ({len(plugins)}) ===\033[0m")
            for p in plugins:
                status = "\033[32mACTIVE\033[0m" if p["is_active"] else "\033[31mINACTIVE\033[0m"
                print(f" • \033[33m{p['name']} v{p['version']}\033[0m [{status}]: {p['description']}")
            print()

        elif cmd == "/memory":
            if arg:
                mems = search_memories(arg)
                print(f"\n\033[1;36m=== MEMORY SEARCH RESULTS FOR '{arg}' ({len(mems)}) ===\033[0m")
                for m in mems:
                    print(f" • [{m['category']}] {m['key_text']} = {m['value_text']}")
            else:
                mems = search_memories("")
                print(f"\n\033[1;36m=== STORED MEMORIES ({len(mems)}) ===\033[0m")
                for m in mems[:20]:
                    print(f" • [{m['category']}] {m['key_text']} = {m['value_text']}")
            print()

        elif cmd == "/model":
            if arg:
                config.llm.provider = arg
                print(f"\033[32mActive LLM provider set to: {arg}\033[0m")
            else:
                print(f"\033[36mCurrent LLM Provider: {config.llm.provider} (Model: {config.llm.model})\033[0m")

        elif cmd == "/train":
            print("\033[36mRunning intent training on collected candidate examples...\033[0m")
            try:
                from training.train import train_intent_model
                train_intent_model()
                print("\033[32mTraining complete! Model updated.\033[0m")
            except Exception as e:
                print(f"\033[31mTraining note: {e}\033[0m")

        elif cmd == "/evaluate":
            print("\033[36mEvaluating neural intent classifier...\033[0m")
            try:
                from training.evaluate import evaluate_intent_model
                evaluate_intent_model()
            except Exception as e:
                print(f"\033[31mEvaluation note: {e}\033[0m")

        elif cmd == "/settings":
            print("\n\033[1;36m=== ACTIVE SYSTEM CONFIGURATION ===\033[0m")
            print(f" • LLM Provider:   {config.llm.provider} (Model: {config.llm.model})")
            print(f" • Fallback Mode:  Active Local Rule & Neural Engine")
            print(f" • Database:       {config.database.type} ({config.database_path})")
            print(f" • Voice Enabled:  {config.voice.enabled} (TTS: {config.voice.tts_engine}, STT: {config.voice.stt_engine})")
            print(f" • Security:       Strict Path & Shell Command Whitelist")
            print()

        else:
            print(f"\033[31mUnknown command '{cmd}'. Type /help for available commands.\033[0m")

def start_cli():
    cli = AJAXCli()
    cli.run()

if __name__ == "__main__":
    start_cli()

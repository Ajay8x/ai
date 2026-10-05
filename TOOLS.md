# AJAX AI - Tools Catalog & Reference

All system tools are registered inside the centralized `ToolRegistry` and strictly checked against the `SafetyEngine`.

| Tool Name | Category | Permission Level | Description |
| :--- | :--- | :--- | :--- |
| `get_system_time` | `SYSTEM` | `SAFE` | Fetches current formatted time and date. |
| `get_system_status` | `SYSTEM` | `SAFE` | Live CPU, RAM, Disk, and Battery diagnostics. |
| `control_volume` | `SYSTEM` | `SAFE` | Turn system volume up/down, mute or unmute. |
| `take_screenshot` | `SYSTEM` | `SAFE` | Captures and saves desktop screenshots to `data/screenshots/`. |
| `system_power` | `SYSTEM` | `CONFIRM_REQUIRED` | Locks, sleeps, restarts, or shuts down the PC. |
| `open_application` | `APPLICATION` | `SAFE` | Launches installed Windows applications (Chrome, Notepad, VS Code, Calc, etc.). |
| `close_application` | `APPLICATION` | `SAFE` | Terminates running processes safely. |
| `search_web` | `WEB` | `SAFE` | Searches DuckDuckGo / Google for live information. |
| `search_wikipedia` | `WEB` | `SAFE` | Fetches factual summaries from Wikipedia. |
| `play_youtube` | `WEB` | `SAFE` | Plays requested music or videos on YouTube. |
| `open_website` | `WEB` | `SAFE` | Opens 100+ recognized websites or direct URLs. |
| `search_files` | `FILESYSTEM` | `SAFE` | Searches for files by pattern or name across allowed directories. |
| `read_file` | `FILESYSTEM` | `SAFE` | Reads text, code, or markdown files safely. |
| `delete_file` | `FILESYSTEM` | `CONFIRM_REQUIRED` | Safely removes files outside protected system paths. |
| `get_weather` | `WEB` | `SAFE` | Retrieves live meteorological data for any city. |
| `set_timer` | `SCHEDULER` | `SAFE` | Non-blocking countdown timer with audio alert. |
| `set_alarm` | `SCHEDULER` | `SAFE` | Schedules alarms for specific times. |
| `remember_fact` | `MEMORY` | `SAFE` | Stores long-term user preferences or notes with privacy checking. |
| `recall_memory` | `MEMORY` | `SAFE` | Searches stored memories. |
| `query_documents` | `FILESYSTEM` | `SAFE` | RAG query across indexed local documents and notes. |
| `analyze_screen` | `SYSTEM` | `SAFE` | Captures and analyzes active screen elements. |

"""
AJAX AI - Web and Browser Tools
Integrates Google Search, Wikipedia knowledge, YouTube playback, News, and Quick Site Launching.
"""

import webbrowser
import urllib.parse
from typing import Dict, Any, Optional
from tools.base import BaseTool, ToolResult
from core.permissions import PermissionLevel, ToolCategory

try:
    from config.sites import sites as raw_sites
    if isinstance(raw_sites, list):
        SITES_MAP = {item[0].lower(): item[1] for item in raw_sites if isinstance(item, (list, tuple)) and len(item) >= 2}
    elif isinstance(raw_sites, dict):
        SITES_MAP = {k.lower(): v for k, v in raw_sites.items()}
    else:
        SITES_MAP = {}
except Exception:
    SITES_MAP = {}

class WebSearchTool(BaseTool):
    name = "search_web"
    description = "Search the internet using DuckDuckGo and return text summaries for questions. Do NOT open browser."
    category = ToolCategory.WEB
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"}
        },
        "required": ["query"]
    }

    def execute(self, query: str, **kwargs) -> ToolResult:
        query_clean = query.strip()
        results_text = ""
        
        # Try DuckDuckGo first
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query_clean, max_results=3))
                if results:
                    snippets = [f"• {r.get('title')}: {r.get('body')}" for r in results if r.get('body')]
                    results_text = "\n".join(snippets)
        except Exception:
            pass

        if not results_text:
            return ToolResult(success=False, output=None, error="No search snippets found.")

        return ToolResult(success=True, output=results_text)

class WikipediaTool(BaseTool):
    name = "search_wikipedia"
    description = "Search Wikipedia for factual encyclopedic summaries."
    category = ToolCategory.WEB
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Topic or query to search"}
        },
        "required": ["query"]
    }

    def execute(self, query: str, sentences: int = 3, **kwargs) -> ToolResult:
        try:
            import wikipedia
            wikipedia.set_user_agent("AjaxAI/3.0 (https://github.com/Ajay8x/ai; contact@ajax.local)")
            try:
                summary = wikipedia.summary(query, sentences=sentences, auto_suggest=False)
                return ToolResult(success=True, output=summary)
            except (wikipedia.DisambiguationError, wikipedia.PageError):
                # Try search results
                search_results = wikipedia.search(query, results=3)
                if search_results:
                    for title in search_results:
                        try:
                            summary = wikipedia.summary(title, sentences=sentences, auto_suggest=False)
                            return ToolResult(success=True, output=summary)
                        except Exception:
                            continue
                return ToolResult(success=False, output=None, error="No direct Wikipedia article found.")
        except Exception as e:
            return ToolResult(success=False, output=None, error=f"Wikipedia search error: {str(e)}")

class YouTubePlayTool(BaseTool):
    name = "play_youtube"
    description = "Play a video or song directly on YouTube."
    category = ToolCategory.WEB
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Song, video, or topic to play"}
        },
        "required": ["query"]
    }

    def execute(self, query: str, **kwargs) -> ToolResult:
        try:
            import pywhatkit
            pywhatkit.playonyt(query)
            return ToolResult(success=True, output=f"Playing '{query}' on YouTube.")
        except Exception as e:
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            webbrowser.open(url)
            return ToolResult(success=True, output=f"Opened YouTube search for '{query}'.")

class OpenWebsiteTool(BaseTool):
    name = "open_website"
    description = "Launch an external website in the browser ONLY when the user explicitly commands to open a site (e.g. 'open youtube', 'open github'). NEVER use this for 'what is' or factual questions."
    category = ToolCategory.WEB
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "site_name_or_url": {"type": "string", "description": "Name or URL of the website to open"}
        },
        "required": ["site_name_or_url"]
    }

    def execute(self, site_name_or_url: str = "", **kwargs) -> ToolResult:
        if not site_name_or_url and kwargs:
            site_name_or_url = str(kwargs.get("url") or kwargs.get("site") or kwargs.get("query") or list(kwargs.values())[0] if kwargs else "")
            
        key = str(site_name_or_url).lower().strip()
        if not key:
            return ToolResult(success=False, output=None, error="No website or URL specified.")

        url = SITES_MAP.get(key)
        
        if not url:
            if key.startswith("http://") or key.startswith("https://"):
                url = key
            elif "." in key:
                url = "https://" + key
            else:
                url = f"https://www.google.com/search?q={urllib.parse.quote(key)}"
                
        webbrowser.open(url)
        return ToolResult(success=True, output=f"Opened {url} in browser.")

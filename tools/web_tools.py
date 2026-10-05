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
    from config.sites import sites as SITES_MAP
except ImportError:
    SITES_MAP = {}

class WebSearchTool(BaseTool):
    name = "search_web"
    description = "Search the internet using DuckDuckGo or Google and return summaries."
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
                results = list(ddgs.text(query_clean, max_results=4))
                if results:
                    snippets = [f"- {r.get('title')}: {r.get('body')} ({r.get('href')})" for r in results]
                    results_text = "\n".join(snippets)
        except Exception:
            pass

        # If no direct text, fallback to opening browser search
        if not results_text:
            url = f"https://www.google.com/search?q={urllib.parse.quote(query_clean)}"
            webbrowser.open(url)
            results_text = f"Opened web search in browser for: {query_clean}"

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
            summary = wikipedia.summary(query, sentences=sentences)
            return ToolResult(success=True, output=summary)
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
    description = "Open any URL or recognized website by name (e.g. youtube, github, chatgpt, instagram)."
    category = ToolCategory.WEB
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "site_name_or_url": {"type": "string", "description": "Name or URL of the website to open"}
        },
        "required": ["site_name_or_url"]
    }

    def execute(self, site_name_or_url: str, **kwargs) -> ToolResult:
        key = site_name_or_url.lower().strip()
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

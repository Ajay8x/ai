"""
AJAX AI - Tools Package
Initializes and registers all built-in tools with ToolRegistry.
"""

from tools.registry import registry
from tools.system_tools import GetSystemTimeTool, GetSystemStatusTool
from tools.web_tools import WebSearchTool, WikipediaTool, YouTubePlayTool, OpenWebsiteTool
from tools.file_tools import SearchFilesTool, ReadFileTool, DeleteFileTool
from tools.weather_tool import WeatherTool
from tools.scheduler_tools import SetTimerTool, SetAlarmTool
from tools.memory_tools import RememberTool, RecallMemoryTool
from tools.rag_tools import QueryDocumentsTool
from tools.calculator_tool import CalculatorTool
from tools.public_api_tools import (
    ISSTrackerTool,
    EarthquakeTrackerTool,
    CurrencyExchangeTool,
    GeocodeTool,
    PublicHolidayTool
)

def register_all_tools():
    """Register all default tools with the singleton registry (PC automation excluded)."""
    tools = [
        GetSystemTimeTool(),
        GetSystemStatusTool(),
        WebSearchTool(),
        WikipediaTool(),
        YouTubePlayTool(),
        OpenWebsiteTool(),
        SearchFilesTool(),
        ReadFileTool(),
        DeleteFileTool(),
        WeatherTool(),
        SetTimerTool(),
        SetAlarmTool(),
        RememberTool(),
        RecallMemoryTool(),
        QueryDocumentsTool(),
        CalculatorTool(),
        ISSTrackerTool(),
        EarthquakeTrackerTool(),
        CurrencyExchangeTool(),
        GeocodeTool(),
        PublicHolidayTool()
    ]
    for t in tools:
        registry.register(t)

# Run registration on module load
register_all_tools()

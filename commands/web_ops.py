import wikipedia
import pywhatkit
import re
import requests
import xml.etree.ElementTree as ET

def search_web(query, speak_func):
    """
    User ki query ko Wikipedia aur Google par search karta hai.
    """
    speak_func(f"Searching for {query}...")
    try:
        clean_query = re.sub(
            r'^(what is a|what is|who is|who was|where is|tell me about|define)\s+',
            '',
            query,
            flags=re.IGNORECASE
        ).strip()

        search_results = wikipedia.search(clean_query)
        if search_results:
            summary = wikipedia.summary(search_results[0], sentences=2, auto_suggest=False)
            speak_func("According to Wikipedia")
            speak_func(summary)
        else:
            speak_func("I couldn't find a direct answer.")
    except Exception:
        speak_func("Sorry, I couldn't fetch the spoken answer.")

    pywhatkit.search(query)

def play_youtube(query, speak_func):
    song = query.replace('play', '').strip()
    speak_func(f"Playing {song}")
    pywhatkit.playonyt(song)

def get_news(speak_func):
    speak_func("Fetching the top news headlines.")
    try:
        url = "https://news.google.com/rss"
        resp = requests.get(url)
        root = ET.fromstring(resp.content)
        for item in root.findall('.//item')[:3]:
            speak_func(item.find('title').text)
    except Exception:
        speak_func("Sorry, I couldn't fetch the news.")

from tts import speak, wish_user
from stt import take_command
from web_ops import search_web, play_youtube, get_news
from system_ops import get_time, get_date, system_power, volume_control, take_screenshot, open_app, close_app, check_battery, check_cpu
from memory_ops import remember_data, fetch_memory
from timer_ops import set_timer, set_alarm
from weather import get_weather

def run_jarvis():
    """
    Ye JARVIS ka minimal main function hai.
    """
    wish_user()

    while True:
        query = take_command()

        if query == "none":
            continue
        
        # Web Searches
        elif 'search' in query or 'google' in query or 'wikipedia' in query:
            search_web(query, speak)
        
        # YouTube
        elif 'play' in query:
            play_youtube(query, speak)
        
        # Time & Date
        elif 'time' in query:
            get_time(speak)
            
        elif 'date' in query:
            get_date(speak)
            
        # Weather & News
        elif 'weather' in query:
            speak("Fetching the latest weather.")
            weather_info = get_weather(query)
            speak(weather_info)
            
        elif 'news' in query:
            get_news(speak)
            
        # App Controls
        elif query.startswith('open '):
            open_app(query, speak)
            
        elif query.startswith('close '):
            close_app(query, speak)
            
        # System Power
        elif 'shutdown' in query or 'restart' in query or 'sleep' in query:
            system_power(query, speak)
            break
            
        # Volume & Media Control
        elif 'volume' in query or 'mute' in query or 'pause' in query or 'resume' in query:
            volume_control(query, speak)
            
        # Screenshots
        elif 'screenshot' in query:
            take_screenshot(speak)
            
        # Battery & CPU
        elif 'battery' in query:
            check_battery(speak)
            
        elif 'cpu' in query:
            check_cpu(speak)
            
        # Timers & Alarms
        elif 'timer' in query:
            set_timer(query, speak)
            
        elif 'alarm' in query:
            set_alarm(query, speak)
            
        # Memory
        elif 'remember that' in query:
            remember_data(query, speak)
            
        elif 'what do you remember' in query:
            fetch_memory(speak)
            
        # Exit
        elif 'exit' in query or 'stop' in query:
            speak("Goodbye! Have a great day.")
            break
            
        # Unrecognized Commands
        else:
            speak("Sorry, I didn't understand that command. Please say 'search' if you want me to search the web.")

if __name__ == "__main__":
    run_jarvis()
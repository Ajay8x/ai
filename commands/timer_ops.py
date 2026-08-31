import threading
import time
import datetime
import re
import winsound

def set_timer(query, speak_func):
    # Extract number of minutes from query
    match = re.search(r'(\d+)\s*minute', query, re.IGNORECASE)
    if not match:
        speak_func("Please specify the number of minutes for the timer.")
        return

    minutes = int(match.group(1))
    speak_func(f"Timer set for {minutes} minutes.")

    def timer_task():
        time.sleep(minutes * 60)
        speak_func("Sir, your timer is up!")
        winsound.Beep(1000, 2000) # Frequency 1000Hz, Duration 2000ms (2 seconds)

    # Start the timer in a background thread so Jarvis can still listen
    threading.Thread(target=timer_task, daemon=True).start()

def set_alarm(query, speak_func):
    # Extract time from query like "7 am" or "7:30 pm"
    match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', query, re.IGNORECASE)
    if not match:
        speak_func("Please specify a valid time for the alarm, like 7 AM.")
        return
        
    hour = int(match.group(1))
    minute = int(match.group(2)) if match.group(2) else 0
    meridiem = match.group(3).lower() if match.group(3) else None
    
    if meridiem == 'pm' and hour != 12:
        hour += 12
    elif meridiem == 'am' and hour == 12:
        hour = 0
        
    now = datetime.datetime.now()
    alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # If the time has already passed today, set it for tomorrow
    if alarm_time < now:
        alarm_time += datetime.timedelta(days=1)
        
    delta_seconds = (alarm_time - now).total_seconds()
    
    speak_func(f"Alarm set for {alarm_time.strftime('%I:%M %p')}.")
    
    def alarm_task():
        time.sleep(delta_seconds)
        speak_func("Sir, it is time for your alarm!")
        winsound.Beep(1000, 3000) # Beep for 3 seconds
        
    # Start the alarm in a background thread
    threading.Thread(target=alarm_task, daemon=True).start()

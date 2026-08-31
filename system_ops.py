import os
import datetime
import pyautogui
import webbrowser
import psutil
from sites import sites
from app_cmd import app_commands
from close_cmd import close_commands

def check_battery(speak_func):
    battery = psutil.sensors_battery()
    if battery:
        percent = battery.percent
        plugged = "and plugged in" if battery.power_plugged else "and not plugged in"
        speak_func(f"Sir, your battery is at {percent} percent {plugged}.")
    else:
        speak_func("I cannot detect a battery on this system.")

def check_cpu(speak_func):
    usage = psutil.cpu_percent(interval=1)
    speak_func(f"The CPU usage is at {usage} percent.")

def get_time(speak_func):
    current_time = datetime.datetime.now().strftime('%I:%M %p')
    speak_func(f"Current time is {current_time}")

def get_date(speak_func):
    current_date = datetime.datetime.now().strftime('%d-%m-%Y')
    speak_func(f"Today's date is {current_date}")

def system_power(command, speak_func):
    if 'shutdown' in command:
        speak_func("Shutting down the computer.")
        os.system("shutdown /s /t 5")
    elif 'restart' in command:
        speak_func("Restarting the computer.")
        os.system("shutdown /r /t 5")
    elif 'sleep' in command:
        speak_func("Going to sleep mode.")
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

def volume_control(command, speak_func):
    if 'volume up' in command:
        speak_func("Increasing volume.")
        pyautogui.press("volumeup", presses=5)
    elif 'volume down' in command:
        speak_func("Decreasing volume.")
        pyautogui.press("volumedown", presses=5)
    elif 'mute' in command:
        speak_func("Muting volume.")
        pyautogui.press("volumemute")
    elif 'pause' in command or 'resume' in command:
        speak_func("Toggling media.")
        pyautogui.press("playpause")

def take_screenshot(speak_func):
    speak_func("Taking a screenshot.")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    pyautogui.screenshot(filename)
    speak_func(f"Screenshot saved as {filename}")

def open_app(query, speak_func):
    app_name = query.replace('open ', '').strip()
    
    # Chrome special case
    if app_name == 'chrome':
        speak_func("Opening Google Chrome.")
        try:
            os.startfile(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        except Exception:
            speak_func("Chrome not found at the specified path.")
        return True

    # Try sites.py
    for site in sites:
        if app_name == site[0]:
            speak_func(f"Opening {site[0]}...")
            webbrowser.open(site[1])
            return True

    # Try app_cmd.py
    command_to_run = app_commands.get(app_name, app_name)
    speak_func(f"Opening {app_name}")
    os.system(f"start {command_to_run}")
    return True

def close_app(query, speak_func):
    app_name = query.replace('close ', '').strip()
    process_name = close_commands.get(app_name)
    
    if process_name:
        speak_func(f"Closing {app_name}")
        os.system(f"taskkill /f /im {process_name}")
        return True

    # Check in sites.py
    is_site = False
    for site in sites:
        if app_name == site[0]:
            is_site = True
            break
    
    if is_site or app_name in ['tab', 'browser', 'window']:
        speak_func(f"Closing {app_name}.")
        pyautogui.hotkey('ctrl', 'w')
        return True
    
    speak_func(f"Sorry, I don't know how to close {app_name}.")
    return False

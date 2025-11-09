import time
import winreg
import pygetwindow as gw
import pyautogui
import pyperclip
import subprocess
import win32gui
import win32con


common_apps = {
    "notepad": "notepad",
    "wordpad": "wordpad",
    "microsoft word": "word",
    "ms word": "word",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "paint": "mspaint",
    "calculator": "calc",
    "vlc": "vlc",
    "vs code": "code",
    "visual studio code": "code",
    "chrome": "chrome",
    "firefox": "firefox",
    "edge": "msedge",
    "cmd": "cmd",
    "command prompt": "cmd",
    "terminal": "wt",
    "camera": "microsoft.windows.camera:",
    "settings": "ms-settings:",
    "snipping tool": "snippingtool"
}

installed_apps = []


def get_installed_apps():
    apps = []
    reg_paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    ]
    for path in reg_paths:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    subkey = winreg.OpenKey(key, winreg.EnumKey(key, i))
                    app_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                    apps.append(app_name.lower())
                except:
                    continue
            winreg.CloseKey(key)
        except Exception:
            pass
    return apps

def load_installed_apps():
    global installed_apps
    installed_apps = get_installed_apps() + list(common_apps.keys())


def is_known_app(app_name: str) -> bool:
    app_name = app_name.lower().strip()
    return app_name in installed_apps or app_name in common_apps


def open_application(app_name: str) -> bool:
    app_name = app_name.lower().strip()
    command = common_apps.get(app_name, app_name)

    try:
        
        if command.endswith(":"):
            subprocess.Popen(["start", command], shell=True)
        else:
            pyautogui.press('win')
            time.sleep(1)
            pyautogui.write(command)
            time.sleep(1)
            pyautogui.press('enter')
            time.sleep(5)
            if "word" in command:  
                pyautogui.press('enter')  
            elif "excel" in command:  
                pyautogui.press('enter')  
            elif "powerpnt" in command: 
                pyautogui.press('enter')
            elif "notepad" in command:  
                pyautogui.hotkey('ctrl','n')
        return True
    except Exception as e:
        print(f"Error opening application: {e}")
        return False

def open_website_search(query):
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    profile_path = r"--profile-directory=Default"

    subprocess.Popen([chrome_path, profile_path, "https://www.google.com"])
    time.sleep(5)

    pyperclip.copy(query)
    pyautogui.hotkey("ctrl", "l")
    time.sleep(0.5)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.5)
    pyautogui.press("enter")
    time.sleep(4)
    pyautogui.click(337, 346)  
    print("Opened web search for:", query)


def close_application(app_name: str) -> bool:
    app_name = app_name.lower().strip()
    for title in gw.getAllTitles():
        if app_name in title.lower():
            gw.getWindowsWithTitle(title)[0].close()
            return True
    return False


def type_into_application(app_name: str, text_to_type: str) -> bool:
    app_name = app_name.lower().strip()
    target_hwnd = None

    
    def find_window_callback(hwnd, extra):
        title = win32gui.GetWindowText(hwnd)
       
        if app_name in title.lower() and win32gui.IsWindowVisible(hwnd):
            extra.append(hwnd)
        return True

    hwnds = []
    win32gui.EnumWindows(find_window_callback, hwnds)

    
    if not hwnds:
        print(f"No open window found for {app_name}. Attempting to open it...")
        if not is_known_app(app_name):
            print(f"Application {app_name} is not known or installed.")
            return False
        
        if not open_application(app_name):
            print(f"Failed to open application {app_name}.")
            return False
        
        
        time.sleep(3)
        hwnds = []
        win32gui.EnumWindows(find_window_callback, hwnds)
        
        if not hwnds:
            print(f"Still could not find window for {app_name} after opening.")
            return False

    if hwnds:
        target_hwnd = hwnds[0]  

    if target_hwnd:
        try:
           
            win32gui.ShowWindow(target_hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(target_hwnd)
            time.sleep(1)  

            pyautogui.write(text_to_type)
            return True
        except Exception as e:
            print(f"Error typing into application {app_name}: {e}")
            return False
    else:
        print(f"Could not find an open window for {app_name}.")
        return False

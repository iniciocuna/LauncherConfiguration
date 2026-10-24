import json
import os
import sys
import threading
import urllib.request
import webbrowser
import customtkinter as ctk
import re

base = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))

bundle = getattr(sys, "_MEIPASS", base)
cache = os.path.join(os.environ.get("APPDATA", base), "APTPLauncher")
os.makedirs(cache, exist_ok=True)

RAW = "https://raw.githubusercontent.com/iniciocuna/LauncherConfiguration/main/"

def load_json(name):
    # Order: next to the .exe (testing) -> downloaded cache -> bundled inside the .exe
    for folder in (base, cache, bundle):
        try:
            with open(os.path.join(folder, name), encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            continue
    return {}

def sync_assets(names):
    for name in names:
        # Only accept names like lan.en-us.json, never paths, in case the repo is ever tampered with
        if not re.fullmatch(r"lan\.[a-z]{2}-[a-z]{2}\.json", name):
            continue
        try:
            with urllib.request.urlopen(RAW + name, timeout=5) as r:
                data = r.read()
            json.loads(data)   # make sure it's valid JSON before saving
            tmp = os.path.join(cache, name + ".tmp")
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, os.path.join(cache, name))
        except Exception:
            pass

config = load_json("config.json")


DEFAULT_TEXT = {
    "Launcher.Title": "Game Launcher",
    "Launcher.LaunchButtonText": "Play",
    "Launcher.LaunchButtonWaitingText": "Launching...",
    "Launcher.LaunchButtonErrorText": "Error, Try Again",
    "Launcher.UpdateAvailableText": "Update available: {0}",
    "Launcher.UpdateAvailableButtonText": "Download launcher update",
    "Launcher.VersionText": "Version {0}",
    "Launcher.UpToDateText": "Version {0} (up to date)",
}
text = {**DEFAULT_TEXT, **load_json(f"lan.{config.get('language', 'en-us')}.json")}

def t(key, *args):
    return text[key].format(*args)

def parse(v):
    return tuple(int(p) for p in v.strip().split("."))

remote = {}

app = ctk.CTk()
app.title(t("Launcher.Title"))
app.geometry("320x200")

status = ctk.CTkLabel(app, text=t("Launcher.VersionText", config.get("version", "?")))
status.pack(pady=(20, 5))

def reset_button():
    play_btn.configure(text=t("Launcher.LaunchButtonText"), state="normal")

def play():
    play_btn.configure(text=t("Launcher.LaunchButtonWaitingText"), state="disabled")
    try:
        os.startfile(f"roblox://experiences/start?placeId={int(config['placeId'])}")
    except Exception:
        play_btn.configure(text=t("Launcher.LaunchButtonErrorText"), state="normal")
        return
    if remote.get("closeafterlaunch", config.get("closeafterlaunch", False)):
        app.after(300, app.destroy)
    else:
        app.after(4000, reset_button)

play_btn = ctk.CTkButton(app, text=t("Launcher.LaunchButtonText"), command=play)
play_btn.pack(pady=5)

update_btn = ctk.CTkButton(app, text=t("Launcher.UpdateAvailableButtonText"))

def check_update():
    try:
        with urllib.request.urlopen(config["versionUrl"], timeout=5) as r:
            data = json.load(r)
        remote.update(data)
        if parse(data["version"]) > parse(config["version"]):
            def show():
                status.configure(text=t("Launcher.UpdateAvailableText", data["version"]))
                update_btn.configure(command=lambda: webbrowser.open(data["download"]))
                update_btn.pack(pady=5)
            app.after(0, show)
        else:
            app.after(0, lambda: status.configure(text=t("Launcher.UpToDateText", config["version"])))
    except Exception:
        pass

threading.Thread(target=check_update, daemon=True).start()
app.mainloop()
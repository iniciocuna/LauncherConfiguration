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
    for folder in (base, cache, bundle):
        try:
            with open(os.path.join(folder, name), encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            continue
    return {}

def sync_assets(names):
    for name in names:
        if not re.fullmatch(r"lan\.[a-z]{2}-[a-z]{2}\.json", name):
            continue
        try:
            with urllib.request.urlopen(RAW + name, timeout=5) as r:
                data = r.read()
            json.loads(data)
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

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title(t("Launcher.Title"))
app.geometry("360x260")
app.resizable(False, False)

ctk.CTkLabel(app, text=t("Launcher.Title"),
             font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(30, 2))

status = ctk.CTkLabel(app, text=t("Launcher.VersionText", config.get("version", "?")),
                      font=ctk.CTkFont(size=12), text_color="gray60")
status.pack(pady=(0, 20))

play_btn = ctk.CTkButton(app, text=t("Launcher.LaunchButtonText"), command=play,
                         width=220, height=48, corner_radius=12,
                         font=ctk.CTkFont(size=16, weight="bold"))
play_btn.pack(pady=5)

update_btn = ctk.CTkButton(app, text=t("Launcher.UpdateAvailableButtonText"),
                           width=220, height=34, corner_radius=12,
                           fg_color="transparent", border_width=1)

update_btn = ctk.CTkButton(app, text=t("Launcher.UpdateAvailableButtonText"))

def check_update():
    try:
        with urllib.request.urlopen(config["versionUrl"], timeout=5) as r:
            data = json.load(r)
        remote.update(data)
        sync_assets(data.get("assets", []))
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

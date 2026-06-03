import os
import json

# ── Default Settings (Fallback) ───────────────────────────────────────────────
TIMEZONE = "Asia/Ho_Chi_Minh"
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5-coder:latest"
POLL_INTERVAL_SECONDS = 1.5
DEBOUNCE_CACHE_SECONDS = 10

import sys

# Get target directory correctly whether running as normal script or compiled PyInstaller .exe
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

# ── Fixed Configs ─────────────────────────────────────────────────────────────
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
CLIENT_SECRET_FILE = os.path.join(base_dir, "credentials.json")
TOKEN_FILE = os.path.join(base_dir, "token.json")
LOG_FILE_PATH = os.path.join(base_dir, "coordinator.log")

# ── Auto-generate / Load settings.json ────────────────────────────────────────
settings_file = os.path.join(base_dir, "settings.json")

if not os.path.exists(settings_file):
    # Auto-generate a settings.json template file with default configurations
    default_settings = {
        "OLLAMA_API_URL": OLLAMA_API_URL,
        "MODEL_NAME": MODEL_NAME,
        "TIMEZONE": TIMEZONE,
        "POLL_INTERVAL_SECONDS": POLL_INTERVAL_SECONDS,
        "DEBOUNCE_CACHE_SECONDS": DEBOUNCE_CACHE_SECONDS
    }
    try:
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(default_settings, f, indent=4)
    except Exception as e:
        pass
else:
    # Load settings from file and override defaults
    try:
        with open(settings_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        if "TIMEZONE" in data:
            TIMEZONE = str(data["TIMEZONE"])
        if "OLLAMA_API_URL" in data:
            OLLAMA_API_URL = str(data["OLLAMA_API_URL"])
        if "MODEL_NAME" in data:
            MODEL_NAME = str(data["MODEL_NAME"])
        if "POLL_INTERVAL_SECONDS" in data:
            POLL_INTERVAL_SECONDS = float(data["POLL_INTERVAL_SECONDS"])
        if "DEBOUNCE_CACHE_SECONDS" in data:
            DEBOUNCE_CACHE_SECONDS = int(data["DEBOUNCE_CACHE_SECONDS"])
    except Exception as e:
        pass

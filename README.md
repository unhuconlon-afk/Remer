# 📅 Standalone Calendar Assistant Application

A premium standalone Windows desktop application (`CalendarAssistant.exe`) that runs a background listener for Windows Action Center notifications (e.g. from Chrome, Zalo Web, Telegram, Slack, or any web messaging app), semantically parses schedule intents using a local Ollama LLM, and automatically logs events to Google Calendar. It includes a sleek, always-on-top checklist dashboard with an integrated collapsible logs drawer.

---

## ✨ Features
1. **Zero Console Clutter:** Runs as a native Windows executable (`CalendarAssistant.exe`) with a hidden console window.
2. **Integrated GUI Logs:** Built-in collapsible scrollable log drawer ("Logs ▲/▼") to trace background operations, API calls, and Ollama semantic analysis.
3. **Windows Notification Hooking:** Uses native WinRT bindings (`winsdk`) to capture desktop notification text in real-time.
4. **Local AI Schedule Parsing:** Sends notification context to your local Ollama LLM (`qwen2.5-coder:latest`) to extract intents, summaries, and relative datetimes (e.g., "Mai 10h", "hôm nay", "mốt").
5. **Google Calendar API Sync:** Automatically inserts events to your Google Calendar.
6. **Desktop Checklist Widget:** Sleek, dark-themed, always-on-top checklist. Checking a task prompts you twice to confirm before deleting the event from Google Calendar.
7. **Debounce / Anti-Spam:** Employs an MD5 message-hash cache filter to prevent duplicate calendar triggers from double notifications.
8. **No-Code Configuration (`settings.json`):** Overrides default settings easily via `settings.json` (auto-generated in the same folder as the `.exe` on first run).

---

## 🏛️ Codebase Structure

| Filename | Purpose |
| :--- | :--- |
| **`CalendarAssistant.exe`** | **The main application executable.** Double-click to run the widget and background notification listener. |
| **`sticky_notes.py`** | Main entry-point script defining the Tkinter interface, threads, and Windows listener. |
| **`config.py`** | Configures paths dynamically relative to `sys.executable` (for compiled mode) or `__file__` (for dev script mode). |
| **`settings.json`** | Configuration overrides for local AI domain URLs, models, and timezone preferences. |
| **`calendar_syncer.py`** | Google Calendar integration handler (OAuth, Event Insert/Delete). |
| **`ollama_analyzer.py`** | Semantic text analyzer that calls the local Ollama endpoint. |
| **`build_exe.bat`** | Compilation script that installs PyInstaller and packages `sticky_notes.py` into the standalone binary. |
| **`google_setup.md`** | Setup instructions for Google Calendar API OAuth client descriptors. |

---

## 🛠️ Setup & Running

### 1. Prerequisites (Ollama & Google OAuth)
1. **Ollama Setup:**
   * Download and install [Ollama](https://ollama.com/).
   * Run in terminal: `ollama pull qwen2.5-coder:latest` (or your preferred model).
2. **Google OAuth setup:**
   * Follow the **[Google Setup Guide](google_setup.md)** to obtain your `credentials.json` client secret descriptor.
   * Save the downloaded file as **`credentials.json`** inside the folder containing `CalendarAssistant.exe`.
   * Double-click `CalendarAssistant.exe` to run it. It will open your web browser once for Google OAuth login approval, then save your login credentials locally into `token.json` for all future runs.

### 2. Customizing Local AI domain & Settings
On the first run, the app auto-generates a **`settings.json`** file in the same directory. You can edit this file to configure:
* `"OLLAMA_API_URL"`: The URL endpoint for your local or remote Ollama service (e.g. `http://localhost:11434/api/generate`).
* `"MODEL_NAME"`: The local AI model name (e.g., `qwen2.5-coder:latest`).
* `"TIMEZONE"`: Your local timezone (e.g. `Asia/Ho_Chi_Minh`).

### 3. Usage
* **Double-click `CalendarAssistant.exe`** to start. The application opens as a sticky checklist widget.
* Click **`Logs ▼`** in the header to expand the scrollable log drawer and view real-time analysis traces.
* Click **`Assistant: ON`** to toggle the background listener. When ON, it listens for incoming Windows toast notifications. When OFF, notification capturing is paused.
* To close the application, simply click the standard window close button `[X]`. No more background batch scripts are required!

---

## 🛠️ Rebuilding / Modifying the Application
If you make changes to the Python code and want to compile a new `.exe`, run:
```powershell
.\build_exe.bat
```
This script will install PyInstaller and generate a new `CalendarAssistant.exe` in the root folder.

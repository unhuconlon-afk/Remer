import sys
import os
import time
import queue
import hashlib
import asyncio
import threading
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta

# Append project directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config
from calendar_syncer import get_calendar_service, insert_event_to_google
from ollama_analyzer import analyze_text_with_ollama

# Global queue to transfer background print/log statements to the GUI log terminal
GLOBAL_LOG_QUEUE = queue.Queue()

class Tee:
    def __init__(self, file, original):
        self.file = file
        self.original = original
    def write(self, data):
        try:
            self.file.write(data)
        except Exception:
            pass
        if self.original:
            try:
                self.original.write(data)
            except Exception:
                pass
        GLOBAL_LOG_QUEUE.put(data)
    def flush(self):
        try:
            self.file.flush()
        except Exception:
            pass
        if self.original:
            try:
                self.original.flush()
            except Exception:
                pass

try:
    log_file_path = config.LOG_FILE_PATH
    log_file = open(log_file_path, "a", encoding="utf-8", buffering=1)
    
    if sys.stdout and getattr(sys.stdout, 'encoding', None) != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    if sys.stderr and getattr(sys.stderr, 'encoding', None) != 'utf-8':
        try:
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass
        
    sys.stdout = Tee(log_file, sys.stdout)
    sys.stderr = Tee(log_file, sys.stderr)
except Exception:
    pass

class PremiumStickyNotesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Calendar Assistant")
        
        # Dimensions: 360 wide, starts at 520 high (collapsible logs drawer)
        self.normal_geometry = "360x520"
        self.expanded_geometry = "360x740"
        
        self.root.geometry(self.normal_geometry)
        self.root.configure(bg="#121212")  # Dark theme background
        
        # Keep window always-on-top (Sticky Note behavior)
        self.root.attributes("-topmost", True)
        
        # Premium styling color tokens
        self.colors = {
            "bg": "#121212",
            "card_bg": "#1e1e1e",
            "accent": "#1a73e8",
            "text": "#e3e3e3",
            "text_muted": "#888888",
            "border": "#2d2d2d",
            "success": "#0f9d58",
            "danger": "#d93025"
        }
        
        # Dashboard parameters
        self.listener_active = True
        self.logs_visible = False
        self.processed_messages_cache = {}
        
        # Main Layout Header
        self.header_frame = tk.Frame(self.root, bg=self.colors["bg"], pady=12, padx=16)
        self.header_frame.pack(fill=tk.X)
        
        self.title_label = tk.Label(
            self.header_frame, 
            text="📅 Tasks & Logs", 
            font=("Segoe UI", 13, "bold"), 
            fg=self.colors["text"], 
            bg=self.colors["bg"]
        )
        self.title_label.pack(side=tk.LEFT)
        
        # Refresh Checklist Button
        self.refresh_btn = tk.Button(
            self.header_frame,
            text="🔄",
            font=("Segoe UI", 11),
            fg=self.colors["text"],
            bg=self.colors["border"],
            activebackground=self.colors["accent"],
            activeforeground=self.colors["text"],
            bd=0,
            padx=8,
            pady=2,
            cursor="hand2",
            command=self.refresh_events
        )
        self.refresh_btn.pack(side=tk.RIGHT)
        
        # View Logs Toggle Button
        self.logs_btn = tk.Button(
            self.header_frame,
            text="Logs ▼",
            font=("Segoe UI", 9),
            fg=self.colors["text"],
            bg=self.colors["border"],
            activebackground=self.colors["accent"],
            activeforeground=self.colors["text"],
            bd=0,
            padx=10,
            pady=2,
            cursor="hand2",
            command=self.toggle_logs_drawer
        )
        self.logs_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Assistant ON/OFF Switch
        self.toggle_btn = tk.Button(
            self.header_frame,
            text="Assistant: ON",
            font=("Segoe UI", 9, "bold"),
            fg=self.colors["text"],
            bg=self.colors["success"],
            activebackground=self.colors["accent"],
            activeforeground=self.colors["text"],
            bd=0,
            padx=10,
            pady=2,
            cursor="hand2",
            command=self.toggle_listener
        )
        self.toggle_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Scrollable Frame for Events (Checklist panel)
        self.container = tk.Frame(self.root, bg=self.colors["bg"])
        self.container.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 6))
        
        self.canvas = tk.Canvas(self.container, bg=self.colors["bg"], bd=0, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.colors["bg"])
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.boundingbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Allow mousewheel scrolling
        self.canvas.bind_all("<MouseWheel>", lambda event: self.canvas.yview_scroll(int(-1*(event.delta/120)), "units"))
        
        # Collapsible Logs Drawer Frame at the bottom
        self.logs_drawer = tk.Frame(
            self.root, 
            bg=self.colors["card_bg"], 
            height=200, 
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        # Scrollable Text Widget for Logs
        self.logs_text = tk.Text(
            self.logs_drawer, 
            bg="#080808", 
            fg="#00ff00",  # Classic terminal green text
            font=("Consolas", 9),
            bd=0, 
            highlightthickness=0,
            padx=6,
            pady=6
        )
        self.logs_scrollbar = tk.Scrollbar(self.logs_drawer, command=self.logs_text.yview)
        self.logs_text.configure(yscrollcommand=self.logs_scrollbar.set)
        
        self.logs_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.logs_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Initialize Google Calendar service
        self.service = None
        try:
            self.service = get_calendar_service()
        except Exception as e:
            messagebox.showerror("Auth Error", f"Failed to authenticate with Google Calendar:\n{e}")
            
        # Initial fetch
        self.refresh_events()
        
        # Start background polling thread for Windows Action Center notifications
        self.listener_thread = threading.Thread(target=self.run_listener, daemon=True)
        self.listener_thread.start()
        
        # Begin queue polling to pull console print statements into the Logs text box
        self.poll_log_queue()

    def toggle_logs_drawer(self):
        """Expands/collapses the logs terminal view at the bottom of the widget."""
        self.logs_visible = not self.logs_visible
        if self.logs_visible:
            self.logs_btn.configure(text="Logs ▲")
            self.logs_drawer.pack(fill=tk.BOTH, side=tk.BOTTOM, padx=12, pady=(0, 12))
            self.root.geometry(self.expanded_geometry)
            self.logs_text.see(tk.END)
        else:
            self.logs_btn.configure(text="Logs ▼")
            self.logs_drawer.pack_forget()
            self.root.geometry(self.normal_geometry)

    def poll_log_queue(self):
        """Fetches pending console print strings from the global queue and appends them to the Text widget."""
        while not GLOBAL_LOG_QUEUE.empty():
            try:
                data = GLOBAL_LOG_QUEUE.get_nowait()
                self.logs_text.insert(tk.END, data)
                self.logs_text.see(tk.END)
            except queue.Empty:
                break
        self.root.after(100, self.poll_log_queue)

    def toggle_listener(self):
        """Flips the state of the background notification listener."""
        self.listener_active = not self.listener_active
        if self.listener_active:
            self.toggle_btn.configure(text="Assistant: ON", bg=self.colors["success"])
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🟢 Assistant Listener turned ON.")
        else:
            self.toggle_btn.configure(text="Assistant: OFF", bg="#444444")
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔴 Assistant Listener turned OFF.")

    def refresh_events(self):
        """Fetches upcoming events and redraws the UI list."""
        if not self.service:
            try:
                self.service = get_calendar_service()
            except Exception:
                self.show_error_message("No Calendar connection.")
                return

        # Clear existing event cards
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        try:
            now_iso = datetime.utcnow().isoformat() + 'Z'
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now_iso,
                maxResults=15,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            
            if not events:
                self.show_empty_message()
                return

            for event in events:
                self.create_event_card(event)

        except Exception as err:
            self.show_error_message(f"Fetch Error: {err}")

    def show_empty_message(self):
        empty_label = tk.Label(
            self.scrollable_frame,
            text="No upcoming tasks or events!",
            font=("Segoe UI", 11, "italic"),
            fg=self.colors["text_muted"],
            bg=self.colors["bg"],
            pady=40
        )
        empty_label.pack(fill=tk.X, expand=True)

    def show_error_message(self, msg):
        err_label = tk.Label(
            self.scrollable_frame,
            text=msg,
            font=("Segoe UI", 10),
            fg="#d93025",
            bg=self.colors["bg"],
            pady=20
        )
        err_label.pack(fill=tk.X)

    def format_event_time(self, event):
        start = event.get('start', {})
        date_str = start.get('dateTime') or start.get('date')
        if not date_str:
            return "All Day"
            
        try:
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                today = datetime.now().date()
                if dt.date() == today:
                    return f"Today, {dt.strftime('%H:%M')}"
                elif dt.date() == today + timedelta(days=1):
                    return f"Tomorrow, {dt.strftime('%H:%M')}"
                else:
                    return dt.strftime('%d/%m, %H:%M')
            else:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                today = datetime.now().date()
                if dt.date() == today:
                    return "Today (All Day)"
                elif dt.date() == today + timedelta(days=1):
                    return "Tomorrow (All Day)"
                else:
                    return dt.strftime('%d/%m (All Day)')
        except Exception:
            return date_str

    def create_event_card(self, event):
        event_id = event.get('id')
        summary = event.get('summary', 'No Title')
        time_formatted = self.format_event_time(event)
        
        card = tk.Frame(
            self.scrollable_frame, 
            bg=self.colors["card_bg"], 
            pady=8, 
            padx=10,
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            bd=0
        )
        card.pack(fill=tk.X, pady=4, padx=2)
        
        cb_canvas = tk.Canvas(
            card, 
            width=18, 
            height=18, 
            bg=self.colors["card_bg"], 
            bd=0, 
            highlightthickness=0,
            cursor="hand2"
        )
        cb_canvas.pack(side=tk.LEFT, padx=(0, 8))
        cb_canvas.create_rectangle(2, 2, 16, 16, outline=self.colors["text_muted"], width=2, tags="box")
        
        info_frame = tk.Frame(card, bg=self.colors["card_bg"])
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        lbl_summary = tk.Label(
            info_frame, 
            text=summary, 
            font=("Segoe UI", 11, "bold"), 
            fg=self.colors["text"], 
            bg=self.colors["card_bg"],
            anchor="w",
            justify=tk.LEFT
        )
        lbl_summary.pack(fill=tk.X)
        
        lbl_time = tk.Label(
            info_frame, 
            text=time_formatted, 
            font=("Segoe UI", 9), 
            fg=self.colors["text_muted"], 
            bg=self.colors["card_bg"],
            anchor="w"
        )
        lbl_time.pack(fill=tk.X)
        
        cb_canvas.bind("<Enter>", lambda e: cb_canvas.itemconfig("box", outline=self.colors["accent"]))
        cb_canvas.bind("<Leave>", lambda e: cb_canvas.itemconfig("box", outline=self.colors["text_muted"]))
        cb_canvas.bind("<Button-1>", lambda e: self.complete_task(event_id, summary, cb_canvas))

    def complete_task(self, event_id, summary, canvas):
        canvas.delete("all")
        canvas.create_rectangle(2, 2, 16, 16, fill=self.colors["accent"], outline=self.colors["accent"], tags="box")
        canvas.create_line(5, 9, 8, 12, fill="white", width=2)
        canvas.create_line(8, 12, 13, 5, fill="white", width=2)
        self.root.update()
        
        ans1 = messagebox.askyesno(
            "Confirm Event Completion",
            f"Have you completed the event '{summary}'?\nThis will remove it from Google Calendar."
        )
        
        if ans1:
            ans2 = messagebox.askyesno(
                "Permanent Deletion",
                f"Double Check:\nAre you absolutely sure you want to delete '{summary}' permanently?"
            )
            if ans2:
                try:
                    self.service.events().delete(calendarId='primary', eventId=event_id).execute()
                    self.refresh_events()
                    return
                except Exception as err:
                    messagebox.showerror("Error", f"Failed to delete event:\n{err}")
        
        canvas.delete("all")
        canvas.create_rectangle(2, 2, 16, 16, outline=self.colors["text_muted"], width=2, tags="box")

    # ── Notification Listener Background Loop ──────────────────────────────────
    def run_listener(self):
        """Standard Thread entry point to boot an asyncio polling loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.poll_notifications())

    async def poll_notifications(self):
        """Notification polling loop querying the Windows UserNotificationListener."""
        try:
            from winsdk.windows.ui.notifications.management import (
                UserNotificationListener,
                UserNotificationListenerAccessStatus,
            )
            from winsdk.windows.ui.notifications import NotificationKinds
        except ImportError as exc:
            print(f"[Import Error] winsdk fails: {exc}")
            return

        listener = UserNotificationListener.current
        access_status = await listener.request_access_async()

        if access_status != UserNotificationListenerAccessStatus.ALLOWED:
            print("[Access Denied] Access to Windows Action Center is denied.")
            return

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ Background listener loop initialized.")
        
        # Fetch current notification IDs to prevent historical loading
        try:
            initial_notifs = await listener.get_notifications_async(NotificationKinds.TOAST)
            processed_ids = {n.id for n in initial_notifs}
        except Exception as e:
            print(f"Error initializing notification IDs: {e}")
            processed_ids = set()

        while True:
            await asyncio.sleep(config.POLL_INTERVAL_SECONDS)
            if not self.listener_active:
                continue

            try:
                active_notifs = await listener.get_notifications_async(NotificationKinds.TOAST)
                active_ids = set()
                for n in active_notifs:
                    active_ids.add(n.id)
                    if n.id not in processed_ids:
                        processed_ids.add(n.id)
                        
                        # Process this newly received notification
                        self.process_notification(n)
                # Keep processed cache aligned with currently active events
                processed_ids = processed_ids.intersection(active_ids)
            except Exception as e:
                print(f"[Listener Thread Loop Error] {e}")

    def get_message_hash(self, text):
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def is_duplicate(self, text):
        msg_hash = self.get_message_hash(text)
        current_time = time.time()
        
        # Clear old cache values
        keys_to_delete = [k for k, v in self.processed_messages_cache.items() if current_time - v > config.DEBOUNCE_CACHE_SECONDS]
        for k in keys_to_delete:
            del self.processed_messages_cache[k]
            
        if msg_hash in self.processed_messages_cache:
            return True
            
        self.processed_messages_cache[msg_hash] = current_time
        return False

    def process_notification(self, n):
        """Processes the UserNotification object by parsing contents via Ollama and saving to Calendar."""
        try:
            app_name = "Unknown App"
            if n.app_info and n.app_info.display_info:
                app_name = n.app_info.display_info.display_name

            toast_texts = []
            if n.notification and n.notification.visual:
                for binding in n.notification.visual.bindings:
                    for text_el in binding.get_text_elements():
                        clean_text = text_el.text.strip()
                        if clean_text:
                            toast_texts.append(clean_text)

            if not toast_texts:
                return

            # Clean and format combined texts
            clean_texts = [t.strip() for t in toast_texts if t.strip()]
            if not clean_texts:
                return

            if len(clean_texts) >= 2:
                title = clean_texts[0]
                body = " ".join(clean_texts[1:])
                joined_text = f"From: {title}\nMessage: {body}"
            else:
                joined_text = clean_texts[0]

            if self.is_duplicate(joined_text):
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⏳ Ignored duplicate notification from {app_name}")
                return

            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔔 Toast received from: {app_name}")
            print(f"   Payload:\n{joined_text}")

            # Step 1: Analyze text using Ollama
            print("   🧠 Analyzing with local Ollama service...")
            parsed_json = analyze_text_with_ollama(joined_text)

            if "error" in parsed_json:
                print(f"   ❌ Ollama analysis failed: {parsed_json['error']}")
                return

            print("   Standardized JSON parsed:")
            import json
            print(json.dumps(parsed_json, indent=4, ensure_ascii=False))

            # Step 2: Handle branching logic
            co_lich_hen = parsed_json.get("co_lich_hen", False)
            loai_thong_bao = parsed_json.get("loai_thong_bao", "")

            if co_lich_hen:
                print("   📅 Syncing event to Google Calendar API...")
                sync_result = insert_event_to_google(parsed_json)
                
                if "error" in sync_result:
                    print(f"   ❌ Sync failed: {sync_result['error']}")
                else:
                    print("   🎉 Sync complete! Google Calendar updated successfully.")
                    # Safe UI list refresh on the main thread
                    self.root.after(0, self.refresh_events)
            elif loai_thong_bao == "nhac_nho_chung":
                warning_msg = f"There's a deadline reminder message from {app_name}, but the time is unclear!"
                print(f"   ⚠️ Received a general deadline message, please check the original message!")
                self.show_local_toast("Deadline reminder", warning_msg)
            else:
                print("   ⚠️ Notification text does not contain a clear schedule event or timing. Skipping calendar sync.")

        except Exception as exc:
            print(f"[Listener Process Error] {exc}")

    def show_local_toast(self, title: str, message: str):
        """Sends a native Windows Toast notification using winsdk."""
        try:
            import winsdk.windows.ui.notifications as notifications
            xml_template = notifications.ToastNotificationManager.get_template_content(notifications.ToastTemplateType.TOAST_TEXT02)
            text_nodes = xml_template.get_elements_by_tag_name("text")
            text_nodes.item(0).append_child(xml_template.create_text_node(title))
            text_nodes.item(1).append_child(xml_template.create_text_node(message))
            
            notifier = notifications.ToastNotificationManager.create_toast_notifier("Microsoft.Windows.Explorer")
            toast = notifications.ToastNotification(xml_template)
            notifier.show(toast)
        except BaseException as e:
            print(f"   ❌ Failed to send toast notification (Safe Fallback): {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PremiumStickyNotesApp(root)
    root.mainloop()

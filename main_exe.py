import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import requests
from datetime import datetime
import queue

class DuckDNSUpdater:
    def __init__(self, master):
        self.master = master
        self.master.title("DuckDNS Updater")

        # Create input fields and labels
        tk.Label(master, text="DuckDNS Subdomain:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.subdomain_entry = tk.Entry(master, width=30)
        self.subdomain_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(master, text="DuckDNS Token:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.token_entry = tk.Entry(master, width=30, show="*")
        self.token_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(master, text="Update Interval (minutes):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.interval_entry = tk.Entry(master, width=30)
        self.interval_entry.grid(row=2, column=1, padx=5, pady=5)

        # Create Start and Stop buttons
        self.start_button = tk.Button(master, text="Start", command=self.start_updater)
        self.start_button.grid(row=3, column=0, padx=5, pady=5)

        self.stop_button = tk.Button(master, text="Stop", command=self.stop_updater, state=tk.DISABLED)
        self.stop_button.grid(row=3, column=1, padx=5, pady=5)

        # Create a scrolled text widget for logs
        self.log_text = scrolledtext.ScrolledText(master, width=50, height=10, state='disabled')
        self.log_text.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

        # For managing the background updater thread
        self.updater_thread = None
        self.stop_event = threading.Event()

        # Use a thread-safe queue for logging from background threads
        self.log_queue = queue.Queue()
        self.master.after(100, self.process_log_queue)

    def log(self, message):
        """Add a timestamped message to the log queue."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {message}\n")

    def process_log_queue(self):
        """Periodically update the log widget with messages from the queue."""
        try:
            while True:
                line = self.log_queue.get_nowait()
                self.log_text.configure(state='normal')
                self.log_text.insert(tk.END, line)
                self.log_text.configure(state='disabled')
                self.log_text.yview(tk.END)
        except queue.Empty:
            pass
        self.master.after(100, self.process_log_queue)

    def start_updater(self):
        """Start the updater thread after validating input."""
        subdomain = self.subdomain_entry.get().strip()
        token = self.token_entry.get().strip()
        try:
            interval_minutes = float(self.interval_entry.get().strip())
        except ValueError:
            self.log("Invalid interval. Please enter a numeric value.")
            return

        if not subdomain or not token:
            self.log("Both subdomain and token are required!")
            return

        self.stop_event.clear()
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.updater_thread = threading.Thread(
            target=self.run_updater,
            args=(subdomain, token, interval_minutes),
            daemon=True
        )
        self.updater_thread.start()
        self.log("Updater started.")

    def stop_updater(self):
        """Signal the updater thread to stop."""
        self.stop_event.set()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log("Updater stopped.")

    def run_updater(self, subdomain, token, interval_minutes):
        """Background thread: periodically sends the update request."""
        while not self.stop_event.is_set():
            try:
                # Construct the DuckDNS update URL
                url = f"https://www.duckdns.org/update?domains={subdomain}&token={token}&ip="
                response = requests.get(url)
                self.log(f"Update sent. Response: {response.text}")
            except Exception as e:
                self.log(f"Error during update: {str(e)}")
            # Wait for the specified interval; check for stop signal every second
            total_seconds = interval_minutes * 60
            for _ in range(int(total_seconds)):
                if self.stop_event.is_set():
                    break
                time.sleep(1)
        self.log("Updater thread exiting.")

def main():
    root = tk.Tk()
    app = DuckDNSUpdater(root)
    root.mainloop()

if __name__ == '__main__':
    main()

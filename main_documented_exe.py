# Import the tkinter module for creating graphical user interfaces (GUIs)
# We alias it as "tk" to simplify subsequent references to its classes and methods.
import tkinter as tk

# Import the scrolledtext widget from tkinter. This widget is a text area with a built-in scrollbar,
# which is useful for displaying long logs or messages that might exceed the visible area.
from tkinter import scrolledtext

# Import the threading module to enable concurrent execution of code.
# This allows us to run the updater in the background without freezing the GUI.
import threading

# Import the time module to access time-related functions like sleep.
# We use this to pause the thread for a specified amount of time (i.e., update interval).
import time

# Import the requests library which provides a simple API for making HTTP requests.
# This is used to send the update requests to DuckDNS.
import requests

# Import the datetime class from the datetime module to work with dates and times.
# We use it to timestamp log messages so we know when each action occurred.
from datetime import datetime

# Import the queue module which provides a thread-safe queue.
# This is useful for passing log messages from the background thread to the main GUI thread.
import queue


# Define a class called DuckDNSUpdater which encapsulates all functionality of our updater application.
class DuckDNSUpdater:
    # The __init__ method initializes the instance and sets up the GUI elements.
    def __init__(self, master):
        # Save the root Tkinter window (master) so we can add widgets and control the window.
        self.master = master
        # Set the title of the window to "DuckDNS Updater" to inform the user of the application’s purpose.
        self.master.title("DuckDNS Updater")

        # ---------------------------
        # Create GUI components below
        # ---------------------------

        # Create and place a Label widget that prompts the user for the DuckDNS subdomain.
        # The grid() method is used to position the widget in the window layout.
        tk.Label(master, text="DuckDNS Subdomain:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

        # Create an Entry widget for the user to input the DuckDNS subdomain.
        # 'width=30' specifies the number of characters the entry box can display.
        self.subdomain_entry = tk.Entry(master, width=30)
        # Place the entry widget next to the label using grid() layout.
        self.subdomain_entry.grid(row=0, column=1, padx=5, pady=5)

        # Create and place a Label widget prompting the user for the DuckDNS token.
        tk.Label(master, text="DuckDNS Token:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)

        # Create an Entry widget for the token, with the 'show' parameter set to "*" to mask the token input.
        self.token_entry = tk.Entry(master, width=30, show="*")
        # Place the token entry widget in the grid layout.
        self.token_entry.grid(row=1, column=1, padx=5, pady=5)

        # Create and place a Label widget asking for the update interval in minutes.
        tk.Label(master, text="Update Interval (minutes):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)

        # Create an Entry widget for the update interval.
        self.interval_entry = tk.Entry(master, width=30)
        # Place the update interval entry widget in the grid layout.
        self.interval_entry.grid(row=2, column=1, padx=5, pady=5)

        # ---------------------------
        # Create control buttons below
        # ---------------------------

        # Create a Start button that, when clicked, triggers the start_updater method.
        self.start_button = tk.Button(master, text="Start", command=self.start_updater)
        # Place the Start button on the grid.
        self.start_button.grid(row=3, column=0, padx=5, pady=5)

        # Create a Stop button that triggers the stop_updater method.
        # Initially, the Stop button is disabled (state=tk.DISABLED) because the updater is not running.
        self.stop_button = tk.Button(master, text="Stop", command=self.stop_updater, state=tk.DISABLED)
        # Place the Stop button on the grid.
        self.stop_button.grid(row=3, column=1, padx=5, pady=5)

        # ---------------------------
        # Create log display area below
        # ---------------------------

        # Create a scrolled text widget to display log messages.
        # 'width=50' and 'height=10' set the dimensions, and 'state=disabled' prevents user edits.
        self.log_text = scrolledtext.ScrolledText(master, width=50, height=10, state='disabled')
        # Place the log widget so that it spans two columns (covering both the labels and entries).
        self.log_text.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

        # ---------------------------
        # Initialize threading components
        # ---------------------------

        # This variable will hold our updater thread once it is created.
        self.updater_thread = None

        # Create a threading.Event object which acts as a flag for stopping the background updater thread.
        self.stop_event = threading.Event()

        # Create a thread-safe queue for log messages. This allows the background thread to safely send
        # log messages to the main thread where they are displayed.
        self.log_queue = queue.Queue()

        # Schedule the process_log_queue method to run after 100 milliseconds.
        # This creates a periodic check to update the log display with new messages from the queue.
        self.master.after(100, self.process_log_queue)

    # ---------------------------
    # Logging methods
    # ---------------------------
    def log(self, message):
        """
        Adds a message to the log queue with a current timestamp.
        This ensures that log messages show the time they occurred.
        """
        # Format the current time as a human-readable string.
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Put the timestamped message into the thread-safe log queue.
        self.log_queue.put(f"[{timestamp}] {message}\n")

    def process_log_queue(self):
        """
        Periodically checks the log queue for new messages and updates the log widget.
        This method is scheduled to run repeatedly using the Tkinter 'after' method.
        """
        try:
            # Process all messages currently in the queue.
            while True:
                # Attempt to retrieve a message without blocking.
                line = self.log_queue.get_nowait()
                # Enable the log widget to allow text insertion.
                self.log_text.configure(state='normal')
                # Insert the log message at the end of the text widget.
                self.log_text.insert(tk.END, line)
                # Disable the widget again to prevent user edits.
                self.log_text.configure(state='disabled')
                # Automatically scroll to the bottom so the latest log is visible.
                self.log_text.yview(tk.END)
        except queue.Empty:
            # If the queue is empty, a queue.Empty exception is raised; simply pass and continue.
            pass
        # Reschedule this method to run again after 100 milliseconds.
        self.master.after(100, self.process_log_queue)

    # ---------------------------
    # Control methods to start and stop the updater
    # ---------------------------
    def start_updater(self):
        """
        Validates user input and starts the updater thread.
        The updater thread will run in the background and send periodic update requests.
        """
        # Retrieve and strip any extra whitespace from the subdomain and token input fields.
        subdomain = self.subdomain_entry.get().strip()
        token = self.token_entry.get().strip()

        # Try to retrieve and convert the update interval to a float (representing minutes).
        try:
            interval_minutes = float(self.interval_entry.get().strip())
        except ValueError:
            # If conversion fails, log an error message and exit the method.
            self.log("Invalid interval. Please enter a numeric value.")
            return

        # Check if the subdomain or token fields are empty.
        if not subdomain or not token:
            # Log an error message if either field is missing.
            self.log("Both subdomain and token are required!")
            return

        # Clear the stop event flag in case it was set previously (i.e., if restarting).
        self.stop_event.clear()

        # Disable the Start button to prevent starting multiple threads,
        # and enable the Stop button so the user can stop the updater if needed.
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        # Create a new thread to run the updater functionality.
        # The thread is marked as daemon so it will exit when the main program exits.
        self.updater_thread = threading.Thread(
            target=self.run_updater,                     # The function to run in the background.
            args=(subdomain, token, interval_minutes),   # Arguments to pass to the function.
            daemon=True                                  # Daemon thread: stops automatically on exit.
        )
        # Start the background updater thread.
        self.updater_thread.start()

        # Log that the updater has started.
        self.log("Updater started.")

    def stop_updater(self):
        """
        Signals the background updater thread to stop and updates the GUI buttons accordingly.
        """
        # Set the stop event flag which signals the thread to stop execution.
        self.stop_event.set()

        # Re-enable the Start button to allow restarting the updater,
        # and disable the Stop button because the updater is no longer running.
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

        # Log that the updater has been stopped.
        self.log("Updater stopped.")

    def run_updater(self, subdomain, token, interval_minutes):
        """
        The function executed by the background thread. It continuously sends update requests
        to the DuckDNS service at the specified interval until signaled to stop.
        """
        # Continue running until the stop event flag is set.
        while not self.stop_event.is_set():
            try:
                # Build the update URL for DuckDNS using the provided subdomain and token.
                # The URL format follows the DuckDNS API specifications.
                url = f"https://www.duckdns.org/update?domains={subdomain}&token={token}&ip="
                
                # Send a GET request to the constructed URL using the requests library.
                response = requests.get(url)
                
                # Log the response text returned by DuckDNS (which may indicate success or failure).
                self.log(f"Update sent. Response: {response.text}")
            except Exception as e:
                # If any exception occurs during the HTTP request, log the error message.
                self.log(f"Error during update: {str(e)}")
            
            # Calculate the total waiting time in seconds based on the interval in minutes.
            total_seconds = interval_minutes * 60
            
            # Instead of sleeping for the entire interval in one go, check the stop event every second.
            # This loop ensures that we can exit promptly if the user decides to stop the updater.
            for _ in range(int(total_seconds)):
                if self.stop_event.is_set():
                    # If a stop has been signaled, break out of the waiting loop immediately.
                    break
                # Sleep for one second before checking the stop flag again.
                time.sleep(1)
        
        # When the while loop exits (i.e., when stop_event is set), log that the updater thread is exiting.
        self.log("Updater thread exiting.")


# Define the main function which sets up and runs the Tkinter GUI application.
def main():
    # Create the main Tkinter window.
    root = tk.Tk()
    
    # Instantiate the DuckDNSUpdater class with the main window as the master.
    app = DuckDNSUpdater(root)
    
    # Start the Tkinter event loop. This loop listens for events such as button clicks,
    # updates the GUI, and ensures that the application remains responsive.
    root.mainloop()


# The standard Python idiom to ensure that main() is only executed when this script is run directly,
# and not when it is imported as a module in another script.
if __name__ == '__main__':
    main()

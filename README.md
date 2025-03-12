# DuckDNS Updater for Windows (Static IP)

## Overview
DuckDNS Updater for Windows is a Python-based GUI application that automatically updates your DuckDNS dynamic DNS record. It periodically sends update requests to DuckDNS, ensuring your subdomain always points to your current IP address. The main script is **`main_exe.py`**.

## Features
- Simple GUI built with Tkinter
- Configurable update interval (in minutes)
- Masked token input for added security
- Real-time, timestamped logging
- Background threading to keep the interface responsive

## Prerequisites
- **Windows OS**
- **Python 3.x** (only if running from source)
- **requests** library (only if running from source)

### Building from Source

1. **Clone** the repository:
  
   ```bash "git clone https://github.com/akaash-r/duck_dns_windows.exe.git"```
   ```cd "duck_dns_windows.exe"```

### Install dependencies:

```python "pip install requests"```

### Run the application:

```python "python main_exe.py"```

## Usage

- Launch the application (via the .exe or main_exe.py).
- Enter your DuckDNS subdomain and token.
- Specify an update interval (in minutes).
- Click Start to begin sending updates, or Stop to halt them.
- Monitor the real-time log messages in the scrollable text area.

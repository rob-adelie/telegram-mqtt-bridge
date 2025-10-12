# JS8Call Telegram Bridge

## Project Overview

This project is a Python-based application that acts as a bridge between a **Telegram bot** and an **MQTT broker**. Its primary purpose is to allow a user to interact with the JS8Call amateur radio application remotely via Telegram commands.

The application works by:

* Subscribing to MQTT topics to receive messages from JS8Call and forward them to Telegram.

* Publishing commands received from Telegram to the MQTT broker, which are then picked up by the JS8Call to MQTT bridge.

This setup provides a convenient way to monitor and control your amateur radio station from anywhere you have access to Telegram.

## Features

* **Bidirectional Communication:** Seamlessly sends messages from Telegram to JS8Call and from JS8Call to Telegram.

* **Thread-Safe Design:** Uses `threading` and `queue` to handle concurrent operations, ensuring stable communication between the Telegram bot and the MQTT client.

* **Custom Telegram Commands:** Provides specific commands for common JS8Call functions like sending heartbeats (`/hb`), getting station information (`/info`), requesting SNR (`/snr`), and sending messages (`/send`, `/mail`).

* **Robust Parsing:** Includes a helper function to correctly parse callsigns and group identifiers from Telegram commands.

## Prerequisites

To run this application, you need the following:

* **Python 3.8+**

* A running **MQTT Broker** (e.g., Mosquitto).

* The **JS8Call MQTT Bridge** middleware running and connected to both JS8Call and your MQTT broker.

* A **Telegram Bot Token** and your personal **Telegram Chat ID**.

## Installation & Setup

### Linux/macOS Installation

1. **Clone the Repository:**
```bash
git clone https://github.com/rob-adelie/telegram-mqtt-bridge.git
cd telegram-mqtt-bridge
```

2. **Configure the Application:**
Edit `telegram-mqtt-bridge.cfg` with your system settings:
- Telegram Bot Token
- Chat ID
- MQTT Broker details
- Your callsign and grid

3. **Run Installation Script:**
```bash
./install.sh
```

### Windows Installation

1. **Clone the Repository:**
```bash
git clone https://github.com/rob-adelie/telegram-mqtt-bridge.git
cd telegram-mqtt-bridge
```

2. **Configure the Application:**
Edit `telegram-mqtt-bridge.cfg` with your system settings:
- Telegram Bot Token
- Chat ID  
- MQTT Broker details
- Your callsign and grid

3. **Run Installation Script:**
Double-click `install.bat` or run from command prompt:
```cmd
install.bat
```

The Windows installer will:
- Create a Python virtual environment
- Install required dependencies
- Create a startup shortcut for automatic launch
- Set up logging directory

4. **Manual Testing:**
To test the installation, run:
```cmd
run.bat
```

5. **Uninstallation:**
To remove the installation, run:
```cmd
uninstall.bat
```


## Usage

Once the application is running, you can interact with it via Telegram using the following commands:

* `/start`: A welcome message.

* `/help`: Displays a list of available commands.

* `/hb`: Sends a heartbeat message (`@HB`) to JS8Call.

* `/info <@callsign>`: Sends a request for information from a specific callsign (e.g., `/info @ZS6RSJ`).

* `/snr <@callsign>`: Sends a request for the SNR from a specific callsign (e.g., `/snr @ZS6RSJ`).

* `/send <@callsign> <message>`: Sends a direct message to a callsign (e.g., `/send @ZS6RSJ Hello there`).

* `/mail <@callsign> <message>`: Sends a message to a callsign's mailbox (e.g., `/mail @ZS6RSJ Hi, this is a test`).

All JS8Call messages received via MQTT on the configured topic will be automatically forwarded to your Telegram chat.

## Contributing & License

This project is licensed under the GPLv3 License. Contributions are welcome! Feel free to open issues or submit pull requests











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

1. **Clone the Repository:**

git clone https://www.google.com/search?q=https://github.com/your-username/js8-telegram-bridge.git
cd js8-telegram-bridge

Enter your system settings in the .cfg file

Run install.sh


4. **Configure the Application:**


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











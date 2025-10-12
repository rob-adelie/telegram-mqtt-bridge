###############################################################################
# telegram-mqtt-bridge
# 
# This project is a Python-based application that acts as a bridge between a 
# Telegram bot and an MQTT broker. Its primary purpose is to allow a user to 
# interact with the JS8Call amateur radio application remotely via Telegram 
# commands.
#
# Copyright (C) 2025  RSJ Cole
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
###############################################################################

import asyncio
import threading
import queue
import json
import paho.mqtt.client as mqtt
import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import re
import time
import logging
import sys

####### Setup Logging ######
# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a file handler for logging to a file
file_handler = logging.FileHandler('logs/telegram-mqtt-bridge.log')
file_handler.setLevel(logging.DEBUG)

# Create a stream handler for logging to the console
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.DEBUG)

# Create a formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.info("Starting Logging...")


######## Get all parameters from the config file ###########
conf = {}
with open('telegram-mqtt-bridge.cfg', 'r') as file:
    # Iterate over each line
    for line in file:
        line = line.strip()
        if line and not line.startswith('#'):  # Ignore blank lines and comments
            key, value = line.split('=', 1)  # Split by the first '=' encountered
            conf[key.strip()] = value.strip()

TELEGRAM_BOT_TOKEN = conf["TELEGRAM_BOT_TOKEN"].strip()
CHAT_ID = conf["CHAT_ID"].strip()
MQTT_BROKER = conf["MQTT_BROKER"].strip()
MQTT_PORT = conf["MQTT_PORT"].strip()
#MQTT_TOPIC = conf["MQTT_TOPIC"].strip()
MQTT_USERNAME = conf["MQTT_USERNAME"].strip()
MQTT_PASSWORD = conf["MQTT_PASSWORD"].strip()
MY_CALLSIGN = conf["MY_CALLSIGN"].strip()
MY_GRID = conf["MY_GRID"].strip()

MQTT_TOPIC = "js8/rx/complete"  

def parse_identifier(identifier: str) -> str:
    """
    Parses a string to determine if it's a callsign or a group identifier.

    - A callsign is a string prepended with '@' and contains numbers.
      The '@' is removed if it's a valid callsign.
    - A group identifier is a string prepended with '@' but contains no numbers.
      The '@' is kept for group identifiers.
    - Any other format is considered an error.

    Args:
        identifier: The input string to parse (e.g., "@k4nkk", "@groupname", "invalid").

    Returns:
        The validated and formatted string, or an error message.
    """
    # Rule 1: Check if the identifier starts with '@'.
    if not identifier.startswith('@'):
        return "Error: Callsign must start with @"

    # Remove the '@' to test the rest of the string.
    body = identifier[1:]

    # Rule 2: Check for the presence of numbers.
    # We use a regular expression to search for any digit (0-9).
    has_numbers = bool(re.search(r'\d', body))

    # Rule 3: Decide based on the presence of numbers.
    if has_numbers:
        # It's a callsign. Call signs must have parameters (numbers).
        # We should remove the '@' for this case.
        # Example: "@k4nkk" -> "k4nkk"
        return body
    else:
        # It's a group. Groups have '@' but no numbers.
        # We must leave the '@'.
        # Example: "@groupname" -> "@groupname"
        return identifier



# Create thread-safe queues to pass messages between MQTT and Telegram
# inbound_queue is for messages received from MQTT -> Telegram
inbound_queue = queue.Queue()
# outbound_queue is for messages to be sent from Telegram -> MQTT
outbound_queue = queue.Queue()

# Email sequence number counter (1-10, cycles back to 1)
email_sequence = 1

# --- MQTT Functions ---
def on_connect(client, userdata, flags, rc, properties):
    """Callback function for when the MQTT client connects."""
    if rc == 0:
        logger.info("*** Connected to MQTT Broker!")
        # Subscribe to the topic once connected
        client.subscribe(MQTT_TOPIC)
        logger.info(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        logger.erro(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    """Callback function for when an MQTT message is received."""
    payload_decoded = msg.payload.decode('utf-8')
    logger.info(f"Received MQTT message: {payload_decoded} on topic: {msg.topic}")
    
    # Put the received message into the inbound queue
    inbound_queue.put((msg.topic, payload_decoded))

def run_mqtt_client():
    """Starts the MQTT client in a separate thread and manages a message publishing loop."""
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="telegram_mqtt_bot")
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    mqtt_client.username_pw_set(username=MQTT_USERNAME, password=MQTT_PASSWORD)

    try:
        mqtt_client.connect(MQTT_BROKER,int(MQTT_PORT), 60)
        mqtt_client.loop_start()  # Start the background loop for incoming messages
        
        while True:
            try:
                # Check the outbound queue for messages to publish without blocking
                topic, payload = outbound_queue.get_nowait()
                mqtt_client.publish(topic, payload)
                logger.info(f"Published MQTT message: {payload} on topic: {topic}")
                outbound_queue.task_done()
            except queue.Empty:
                # No messages to publish, so continue the loop
                pass
            
            time.sleep(0.1) # Small delay to prevent a busy loop
            
    except Exception as e:
        logger.error(f"Could not connect to MQTT broker: {e}")
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()



help_info = "/hb                             Send Heartbeat\
           \n/info <@callsign>   Get INFO\
           \n/snr <@callsign>     Get SNR\
           \n/send <@callsign>  Msg to\
           \n/hearing <@callsign>  Hearing\
           \n/mail <@callsign>   Msg to mailbox\
           \n/email <email> <message>  Send email via JS8Call"
            

# --- Telegram Bot Functions ---
async def start(update, context):
    """Command handler for the /start command."""
    await update.message.reply_text("Telegram to JS8 Bot, type /help for HELP")

async def doHelp(update, context):
    """Command handler for the /help command."""
    global help_info
    await update.message.reply_text(f"{help_info}")

async def echo(update, context):
    """Command handler to echo a message back."""
    await update.message.reply_text(update.message.text)


async def check_for_mqtt_messages(context):
    """Periodically checks the inbound queue for new messages and sends them to Telegram."""
    try:
        # Get a message from the queue without blocking
        topic, payload = inbound_queue.get_nowait()
        
        message_to_send = ""
        snr = "N/A" # Default value for SNR
        
        try:
            # Try to parse the payload as JSON
            data = json.loads(payload)
            # Use .get() to safely retrieve the 'text' field, with the raw payload as a fallback
            message_to_send = data.get('text', payload)
            snr = data.get('snr', 'N/A')
        except json.JSONDecodeError:
            # If it's not valid JSON, just use the raw payload
            logger.warn("Error decoding JSON payload. Sending raw message.")
            message_to_send = payload
        
        # Remove the heart symbol from the message, which is used as an end-of-text marker
        message_to_send = message_to_send.replace('♥', '').replace('\u00e2\u0099', '')
        
        # Remove the whitespace after the first colon using a positive lookbehind
        message_to_send = re.sub(r'(?<=:)\s+', '', message_to_send, 1)

        # Replace any sequence of whitespace with a single space, then strip leading/trailing spaces
        message_to_send = re.sub(r'\s+', ' ', message_to_send).strip()
        
        logger.debug (message_to_send)
        
        # Send the message to the configured chat ID
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=f"`{message_to_send}` (snr `{snr}`)",
            parse_mode='Markdown'
        )
        # Mark the task as done
        inbound_queue.task_done()
    except queue.Empty:
        # If the queue is empty, do nothing
        pass
    except Exception as e:
        logger.error(f"Error sending message to Telegram: {e}")


async def heartbeat(update, context):
    """Sends a @HB message."""
    global MY_GRID
    # Just ignoring any extra params
    json_payload = {
        "message": f"@HB HEARTBEAT {MY_GRID}"
    }
    # Convert the Python dictionary to a JSON string
    message_to_send = json.dumps(json_payload)
    # Place the message and topic in the outbound queue for the MQTT thread to publish
    outbound_queue.put(('js8/tx/command', message_to_send))
    await update.message.reply_text(f"Sending @HB")


async def info(update, context):
    """Sends a 'info?' request message to a destination callsign."""
    args = context.args
    if not args:
        await update.message.reply_text("Please provide callsign.\ne.g. /info @ZS6XYZ")
        return
    dest_callsign = parse_identifier(args[0].upper())
    if "Error:" in dest_callsign:
        await update.message.reply_text(f"{dest_callsign}")
        return
    # Create the JSON payload with the correct 'message' key
    json_payload = {
        "message": f"{dest_callsign} info?"
    }
    # Convert the Python dictionary to a JSON string
    message_to_send = json.dumps(json_payload)
    # Place the message and topic in the outbound queue for the MQTT thread to publish
    outbound_queue.put(('js8/tx/command', message_to_send))
    await update.message.reply_text(f"Sending INFO? to {dest_callsign}...")


async def get_snr(update, context):
    """Sends a 'snr?' request message to a destination callsign."""
    args = context.args
    if not args:
        await update.message.reply_text("Please provide callsign. \ne.g. /snr @ZS6XYZ")
        return
    dest_callsign = parse_identifier(args[0].upper())
    if "Error:" in dest_callsign:
        await update.message.reply_text(f"{dest_callsign}")
        return
    # Create the JSON payload with the correct 'message' key
    json_payload = {
        "message": f"{dest_callsign} snr?"
    }
    # Convert the Python dictionary to a JSON string
    message_to_send = json.dumps(json_payload)
    # Place the message and topic in the outbound queue for the MQTT thread to publish
    outbound_queue.put(('js8/tx/command', message_to_send))
    await update.message.reply_text(f"Sending SNR? to {dest_callsign}...")

async def hearing(update, context):
    """Sends a 'hearing?' request message to a destination callsign."""
    args = context.args
    if not args:
        await update.message.reply_text("Please provide callsign. \ne.g. /snr @ZS6XYZ")
        return
    dest_callsign = parse_identifier(args[0].upper())
    if "Error:" in dest_callsign:
        await update.message.reply_text(f"{dest_callsign}")
        return
    # Create the JSON payload with the correct 'message' key
    json_payload = {
        "message": f"{dest_callsign} hearing?"
    }
    # Convert the Python dictionary to a JSON string
    message_to_send = json.dumps(json_payload)
    # Place the message and topic in the outbound queue for the MQTT thread to publish
    outbound_queue.put(('js8/tx/command', message_to_send))
    await update.message.reply_text(f"Sending HEARING? to {dest_callsign}...")

async def send_mail_message(update, context):
    """
    Sends a message to a destination callsign's mailbox.
    The message will be formatted as "CALLSIGN MSG MESSAGE_TEXT".
    
    Example usage in Telegram: /sendmail ZS6XXX hello there 
    """
    args = context.args
    # Check for the correct number of arguments (callsign + at least one word for the message)
    if len(args) < 2:
        await update.message.reply_text("Please provide callsign and message. \ne.g. /mail @ZS6XYZ Hello from Telegram!")
        return
    dest_callsign = parse_identifier(args[0].upper())
    if "Error:" in dest_callsign:
        await update.message.reply_text(f"{dest_callsign}")
        return
    # The rest of the arguments are the message text. We join them with spaces.
    message_text = " ".join(args[1:])
    # Create the JSON payload with the correct 'message' key
    json_payload = {
        "message": f"{dest_callsign} MSG {message_text}"
    }
    # Convert the Python dictionary to a JSON string
    message_to_send = json.dumps(json_payload)
    # Place the message and topic in the outbound queue for the MQTT thread to publish
    outbound_queue.put(('js8/tx/command', message_to_send))
    await update.message.reply_text(f"Sending message to mailbox of {dest_callsign}...")

async def send_message(update, context):
    """
    Sends a message to a destination callsign
    
    Example usage in Telegram: /msg ZS6XXX hello there 
    """
    args = context.args
    # Check for the correct number of arguments (callsign + at least one word for the message)
    if len(args) < 2:
        await update.message.reply_text("Please provide callsign and message. \ne.g. /send ZS6XYZ Hello from Telegram!")
        return
    dest_callsign = parse_identifier(args[0].upper())
    if "Error:" in dest_callsign:
        await update.message.reply_text(f"{dest_callsign}")
        return
    # The rest of the arguments are the message text. We join them with spaces.
    message_text = " ".join(args[1:])
    # Create the JSON payload with the correct 'message' key
    json_payload = {
        "message": f"{dest_callsign} {message_text}"
    }
    # Convert the Python dictionary to a JSON string
    message_to_send = json.dumps(json_payload)
    # Place the message and topic in the outbound queue for the MQTT thread to publish
    outbound_queue.put(('js8/tx/command', message_to_send))
    await update.message.reply_text(f"Sending message to {dest_callsign}...")

async def send_email(update, context):
    """
    Sends an email via JS8Call's APRSIS CMD capability.
    
    Example usage in Telegram: /email user@example.com "Test Subject" "Hello from JS8Call!"
    """
    global email_sequence
    
    args = context.args
    # Check for the correct number of arguments (email + subject + at least one word for the message)
    if len(args) < 3:
        await update.message.reply_text("Please provide email, subject, and message. \ne.g. /email user@example.com \"Test Subject\" \"Hello from JS8Call!\"")
        return
    
    email_address = args[0]
    subject = args[1]
    # The rest of the arguments are the message text. We join them with spaces.
    message_text = " ".join(args[2:])
    
    # Validate email format (basic validation)
    if "@" not in email_address or "." not in email_address.split("@")[1]:
        await update.message.reply_text("Please provide a valid email address.")
        return
    
    # Format the email message for JS8Call APRSIS CMD
    # JS8Call uses @APRSIS CMD :EMAIL-2  :recipient message{sequence_number} format
    # We generate the sequence number (1-10, cycles back to 1)
    email_command = f"@APRSIS CMD :EMAIL-2  :{email_address} {subject} {message_text}{{{email_sequence:02d}}}"
    
    # Increment sequence number (1-10, then back to 1)
    email_sequence = (email_sequence % 10) + 1
    
    # Create the JSON payload with the correct 'message' key
    json_payload = {
        "message": email_command
    }
    # Convert the Python dictionary to a JSON string
    message_to_send = json.dumps(json_payload)
    # Place the message and topic in the outbound queue for the MQTT thread to publish
    outbound_queue.put(('js8/tx/command', message_to_send))
    await update.message.reply_text(f"Sending email to {email_address} with subject '{subject}'...")


# --- Main Functions ---
def run_telegram_bot():
    """Starts the Telegram bot using polling."""
    try:

        #application = Application.builder().token(telegramconf["TELEGRAM_BOT_TOKEN"].strip()).build()
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Add a command handler for /start
        application.add_handler(CommandHandler("start", start))
        
        # Add a command handler for /help
        application.add_handler(CommandHandler("help", doHelp))
        
        # Add a command handler for /snr
        application.add_handler(CommandHandler("snr", get_snr))
        
        # Add a command handler for /hearing
        application.add_handler(CommandHandler("hearing", hearing))
        
        # Add a command handler for /msg
        application.add_handler(CommandHandler("send", send_message))
        
        # Add a command handler for /mail
        application.add_handler(CommandHandler("mail", send_mail_message))

        # Add a command handler for /email
        application.add_handler(CommandHandler("email", send_email))

        # Add a command handler for /hb
        application.add_handler(CommandHandler("hb", heartbeat))
        
        # Add a command handler for /info
        application.add_handler(CommandHandler("info", info))

        # Add a message handler for all text messages (filters.TEXT)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

        # Start a recurring job to check the MQTT inbound message queue every second
        application.job_queue.run_repeating(check_for_mqtt_messages, interval=1)

        # Run the bot until the user presses Ctrl-C
        application.run_polling(poll_interval=1, timeout=30)
    except Exception as e:
        logger.error(f"Error starting Telegram bot: {e}")

if __name__ == "__main__":
    
    # Run the MQTT client in its own thread
    mqtt_thread = threading.Thread(target=run_mqtt_client, daemon=True)
    mqtt_thread.start()

    # Run the Telegram bot in the main thread
    run_telegram_bot()


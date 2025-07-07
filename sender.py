import os
import sys
import time
import math
import json
import logging
import zlib, base64
from meshtastic.serial_interface import SerialInterface
from pubsub import pub

CONFIG_FILE = "meshtastic_config.json"
LOG_FILE = "sender.log"
CHUNK_SIZE = 160  # Max length of each chunk
CONFIRMATION_TIMEOUT = 15  # Time in seconds to wait for confirmation messages

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="w"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Store confirmation state
confirmation_state = {}

def save_device_path(dev_path):
    """Save the detected device path to a configuration file."""
    with open(CONFIG_FILE, "w") as config_file:
        json.dump({"device_path": dev_path}, config_file)
    logger.info(f"Device path saved to config: {dev_path}")

def load_device_path():
    """Load the saved device path from the configuration file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as config_file:
            config = json.load(config_file)
            return config.get("device_path")
    return None

def connect_to_device():
    """Connect to the Meshtastic device using the saved config or by scanning."""
    saved_path = load_device_path()
    if saved_path:
        logger.info(f"Trying saved device path: {saved_path}")
        try:
            interface = SerialInterface(devPath=saved_path)
            logger.info(f"Connected to Meshtastic device on {saved_path}")
            return interface
        except Exception as e:
            logger.warning(f"Failed to connect to saved device path: {e}")

    # If no saved path or failed connection, scan for devices
    logger.info("Searching for Meshtastic devices...")
    try:
        interface = SerialInterface()
        save_device_path(interface.devPath)
        logger.info(f"Connected to Meshtastic device on {interface.devPath}")
        return interface
    except Exception as e:
        logger.error(f"Unable to connect to any Meshtastic device: {e}")
        return None

def on_receive(packet, interface):
    """Process all incoming messages."""
    try:
        decoded = packet.get("decoded", {})
        text = decoded.get("text", None)
        sender = packet.get("fromId", "Unknown Sender")

        logger.info(f"Message received from {sender}: {text}")

        # Check if the message is a confirmation
        if text and "confirmed" in text:
            parts = text.split(":")
            if len(parts) == 2:
                filename_chunk, confirmation = parts
                filename, chunk_info = filename_chunk.strip(), confirmation.strip()

                if filename not in confirmation_state:
                    confirmation_state[filename] = set()

                confirmation_state[filename].add(chunk_info)
                logger.info(f"Confirmation received: {filename} {chunk_info}")
    except Exception as e:
        logger.error(f"Error processing incoming message: {e}")

def send_text_via_meshtastic(message, dest, interface):
    """Send a text message via the Meshtastic command-line interface."""
    try:
        interface.sendText(message, destinationId=dest)
        logger.info(f"Sent: {message} to {dest}")
    except Exception as e:
        logger.error(f"Error sending message: {e}")

def send_file(file_path, dest, interface):
    """Send a file over Meshtastic in chunks."""
    if not os.path.exists(file_path):
        logger.error("File not found.")
        return

    try:
        with open(file_path, "rb") as file:
            content1 = file.read()
            content =  base64.b64encode(zlib.compress(content1,9))
            content = content.decode('utf-8')
        total_length = len(content)
        total_chunks = math.ceil(total_length / CHUNK_SIZE)
        file_name = os.path.basename(file_path)

        logger.info(f"Sending file: {file_path} ({total_chunks} chunks)")

        # Step 1: Announce the file name
        start_message = f"[START] {file_name}"
        send_text_via_meshtastic(start_message, dest, interface)
        time.sleep(3)

        # Step 2: Send chunks
        for i in range(total_chunks):
            chunk_number = i + 1
            chunk = content[i * CHUNK_SIZE: (i + 1) * CHUNK_SIZE]
            message = f"[CHUNK] {chunk_number}/{total_chunks} {file_name} {chunk}"
            send_text_via_meshtastic(message, dest, interface)
            time.sleep(2)  # Prevent flooding

            # Wait for confirmation
            retries = 0
            while retries < 5:
                if f"{chunk_number}/{total_chunks} confirmed" in confirmation_state.get(file_name, set()):
                    logger.info(f"Chunk {chunk_number}/{total_chunks} confirmed.")
                    break
                else:
                    retries += 1
                    send_text_via_meshtastic(message, dest, interface)
                    logger.info(f"Waiting for confirmation of chunk {chunk_number}/{total_chunks} (Retry {retries})...")
                    time.sleep(CONFIRMATION_TIMEOUT)

            if retries >= 5:
                logger.error(f"Failed to confirm chunk {chunk_number}/{total_chunks}. Aborting.")
                return

        # Step 3: End message
        end_message = f"[END] {file_name}"
        send_text_via_meshtastic(end_message, dest, interface)
        logger.info("File transmission complete.")
    except Exception as e:
        logger.error(f"Error reading or sending the file: {e}")

def main():
    """Main function to send a file with confirmation."""
    if len(sys.argv) < 3:
        print("Usage: python3 sender_confirmation.py <file.txt> <destination>")
        return

    file_path = sys.argv[1]
    dest = sys.argv[2]

    interface = connect_to_device()
    if not interface:
        logger.error("Failed to connect to any Meshtastic device.")
        return

    # Subscribe to receive all incoming messages
    pub.subscribe(on_receive, "meshtastic.receive.text")

    send_file(file_path, dest, interface)

if __name__ == "__main__":
    main()



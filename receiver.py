import json
import os
import logging
import meshtastic
from meshtastic.serial_interface import SerialInterface
from pubsub import pub

CONFIG_FILE = "meshtastic_config.json"
LOG_FILE = "listener.log"

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

# Dictionary to store collected chunks
chunk_storage = {}

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
    """Callback function to process incoming packets."""
    try:
        decoded = packet.get("decoded", {})
        portnum = decoded.get("portnum", None)
        text = decoded.get("text", None)
        sender = packet.get("fromId", "Unknown Sender")

        if portnum == "TEXT_MESSAGE_APP" and text:
            logger.info(f"Text message received from {sender}: {text}")

            # Process [CHUNK] messages
            if text.startswith("[CHUNK]"):
                process_chunk_message(text, sender, interface)

    except Exception as e:
        logger.error(f"Error processing packet: {e}")

def process_chunk_message(text, sender, interface):
    """Process and collect [CHUNK] messages."""
    try:
        # Extract chunk info
        if not text.startswith("[CHUNK]"):
            logger.warning(f"Malformed [CHUNK] message: {text}")
            return

        # Remove [CHUNK] prefix and split remaining text
        chunk_info, filename, chunk_data = text[len("[CHUNK] "):].split(" ", 2)
        chunk_index, total_chunks = map(int, chunk_info.split("/"))

        # Initialize storage for this file if not already present
        if filename not in chunk_storage:
            chunk_storage[filename] = {
                "total_chunks": total_chunks,
                "received_chunks": {},
            }

        # Store the chunk
        chunk_storage[filename]["received_chunks"][chunk_index] = chunk_data
        logger.info(f"Received chunk {chunk_index}/{total_chunks} for file: {filename}")

        # Check progress
        received_count = len(chunk_storage[filename]["received_chunks"])
        progress_message = f"{filename}: {received_count}/{total_chunks} confirmed"
        logger.info(progress_message)

        # Send progress confirmation back to the sender
        interface.sendText(progress_message, destinationId=sender)

    except Exception as e:
        logger.error(f"Error processing chunk message: {e}")

def on_connection(interface, topic=pub.AUTO_TOPIC):
    """Callback for connection establishment."""
    logger.info("Connection established.")
    interface.sendText("Hello, mesh!")

def main():
    """Main function to initialize the interface and listen for messages."""
    interface = connect_to_device()
    if not interface:
        logger.error("Failed to connect to any Meshtastic device.")
        return

    # Subscribe to relevant Meshtastic events
    pub.subscribe(on_receive, "meshtastic.receive")
    pub.subscribe(on_connection, "meshtastic.connection.established")

    logger.info("Listening for messages... Press Ctrl+C to exit.")

    try:
        # Keep the script running to listen for incoming packets
        while True:
            pass
    except KeyboardInterrupt:
        logger.info("Exiting...")
    finally:
        interface.close()

if __name__ == "__main__":
    main()



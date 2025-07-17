import os
import sys
import time
import math
import json
import logging
import zlib, base64
import argparse, hashlib
from meshtastic.serial_interface import SerialInterface
from pubsub import pub

CONFIG_FILE = "meshtastic_config.json"
LOG_FILE = "sender.log"
CHUNK_SIZE = 180  # Max length of each chunk
CONFIRMATION_TIMEOUT = 3  # Time in seconds to wait for confirmation messages
START_TIME = time.localtime()
START_TIME = time.strftime("%H:%M:%S", START_TIME)
print(START_TIME)
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

# Define a function to calculate the SHA-256 hash of a file.
def calculate_hash(file_path):
   # Create a SHA-256 hash object.
   sha256_hash = hashlib.sha256()
   # Open the file in binary mode for reading (rb).
   with open(file_path, "rb") as file:
       # Read the file in 64KB chunks to efficiently handle large files.
       while True:
           data = file.read(65536)  # Read the file in 64KB chunks.
           if not data:
               break
           # Update the hash object with the data read from the file.
           sha256_hash.update(data)
   # Return the hexadecimal representation of the calculated hash.
   return sha256_hash.hexdigest()

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

def send_file(file_path, dest, interface, chunkstart):
    """Send a file over Meshtastic in chunks."""
    if not os.path.exists(file_path):
        logger.error("File not found.")
        return

    try:
        with open(file_path, "rb") as file:
            content1 = file.read()
            logger.info(f"Uncompressed Size: {len(content1)} bytes")
            content =  base64.b64encode(zlib.compress(content1,9))
            content = content.decode('utf-8')
            logger.info(f"Compressed Size: {len(content)} bytes")
            if len(content1) < len(content) :
                logger.info(f"Sending UnCompressed version")
                content=base64.b64encode(content1)
                content = content.decode('utf-8')
        total_length = len(content)
        total_chunks = math.ceil(total_length / CHUNK_SIZE)
        file_name = os.path.basename(file_path)
        #logger.info(content)
        hashid=calculate_hash(file_path)
        logger.info(f"Sending file: {file_path} ({total_chunks} chunks of {CHUNK_SIZE} bytes) : HASH: {hashid}")


        # Step 1: Announce the file name
        start_message = f"[START] {file_name}"
        send_text_via_meshtastic(start_message, dest, interface)
        time.sleep(3)


        # Step 2: Send chunks
        for i in range(chunkstart,total_chunks):
            
            chunk_number = i + 1
            chunk = content[i * CHUNK_SIZE: (i + 1) * CHUNK_SIZE]
            message = f"[CHUNK] {chunk_number}/{total_chunks} {file_name} {chunk}"
            send_text_via_meshtastic(message, dest, interface)
            
            time.sleep(CONFIRMATION_TIMEOUT)
            #time.sleep(5)  # Prevent flooding

            # Wait for confirmation
            retries = 0
            while retries < 30:
                if f"{chunk_number}/{total_chunks} confirmed" in confirmation_state.get(file_name, set()):
                    logger.info(f"Chunk {chunk_number}/{total_chunks} confirmed.")
                    retries = 0
                    break
                else:
                    retries += 1
                    if retries == 9 or retries==18 :
                        send_text_via_meshtastic(message, dest, interface)
                        logger.info(f"Resend chunk {chunk_number}/{total_chunks})...")
                    logger.info(f"Waiting for confirmation of chunk {chunk_number}/{total_chunks} (Retry {retries})...")
                    time.sleep(CONFIRMATION_TIMEOUT)

            if retries >= 5:
                logger.error(f"Failed to confirm chunk {chunk_number}/{total_chunks}. Aborting.")
                return

        # Step 3: End message
        end_message = f"[END] {file_name} HASH: {hashid}"
        send_text_via_meshtastic(end_message, dest, interface)
        logger.info("File transmission complete.")
        NOW_TIME = time.localtime()
        current_time = time.strftime("%H:%M:%S", NOW_TIME)
        logger.info(f"Start time {START_TIME}")
        logger.info(f"End time {current_time}")

    except Exception as e:
        logger.error(f"Error reading or sending the file: {e}")

def main():
    """Main function to send a file with confirmation."""
    if len(sys.argv) < 3:
        print("Usage: python3 sender_confirmation.py <file.txt> <destination>")
        return

    file_path = sys.argv[1]
    dest = sys.argv[2]
    
    
    if len(sys.argv) > 3 :
        chunkstart = int(sys.argv[3])-1
        
    else : 
        chunkstart = 0
    print(chunkstart)

    interface = connect_to_device()
    if not interface:
        logger.error("Failed to connect to any Meshtastic device.")
        return

    # Subscribe to receive all incoming messages
    pub.subscribe(on_receive, "meshtastic.receive.text")

    send_file(file_path, dest, interface, chunkstart)

if __name__ == "__main__":
    main()



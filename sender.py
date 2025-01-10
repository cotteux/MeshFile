import os
import sys
import time
import math
import subprocess

CHUNK_SIZE = 180  # Max length of each chunk

def send_text_via_meshtastic(message, dest=None):
    """Send a text message via the Meshtastic command-line interface."""
    try:
        if dest:
            cmd = ["meshtastic", "--sendtext", message, "--dest", dest]
        else:
            cmd = ["meshtastic", "--sendtext", message]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Sent: {message}")
        else:
            print(f"Failed to send message: {result.stderr}")
    except Exception as e:
        print(f"Error sending message: {e}")

def send_file(file_path, dest=None):
    """Send a file over Meshtastic in chunks."""
    if not os.path.exists(file_path):
        print("File not found.")
        return

    try:
        with open(file_path, "r") as file:
            content = file.read()

        total_length = len(content)
        total_chunks = math.ceil(total_length / CHUNK_SIZE)

        print(f"Sending file: {file_path} ({total_chunks} chunks)")

        # Step 1: Announce the file name
        file_name = os.path.basename(file_path)
        start_message = f"[START] {file_name}"
        send_text_via_meshtastic(start_message, dest)
        time.sleep(1)

        # Step 2: Send chunks
        for i in range(total_chunks):
            chunk = content[i * CHUNK_SIZE: (i + 1) * CHUNK_SIZE]
            # Encapsulate chunk in delimiters
            message = f"[CHUNK] {i + 1}/{total_chunks} <<{chunk}>>"
            send_text_via_meshtastic(message, dest)
            time.sleep(1)  # Prevent flooding

        # Step 3: End message
        end_message = "[END] Transfer complete."
        send_text_via_meshtastic(end_message, dest)
        print("File transmission complete.")
    except Exception as e:
        print(f"Error reading or sending the file: {e}")

if __name__ == "__main__":
    # Parse command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python3 sender.py <file.txt> [--dest <destination>]")
    else:
        file_path = sys.argv[1]
        dest = None

        # Check for destination flag
        if len(sys.argv) > 2 and sys.argv[2] == "--dest" and len(sys.argv) > 3:
            dest = sys.argv[3]

        send_file(file_path, dest)


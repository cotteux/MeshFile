import meshtastic
import time
import sys
import math
import os
import zlib
import hashlib

interface = meshtastic.serial_interface.SerialInterface()

def calculate_hash(data):
    return hashlib.sha256(data).hexdigest()

def send_file(file_path):
    if not os.path.exists(file_path):
        print("File not found.")
        return

    # Read file in binary mode and compress
    with open(file_path, "rb") as f:
        file_content = f.read()

    compressed_content = zlib.compress(file_content)
    file_hash = calculate_hash(file_content)  # Calculate hash of the original file

    chunk_size = 200
    total_length = len(compressed_content)
    total_chunks = math.ceil(total_length / chunk_size)

    # Send the START packet with total chunk count and hash
    interface.sendText(f"[START]{total_chunks:02d}#{file_hash}")
    print(f"Sent: [START]{total_chunks:02d}#{file_hash}")
    time.sleep(1)

    # Send the file in chunks
    for i in range(total_chunks):
        chunk = compressed_content[i * chunk_size: (i + 1) * chunk_size]
        chunk_number = f"{i + 1:02d}"
        full_message = f"[CONT]{chunk_number}".encode() + chunk
        interface.sendData(full_message)
        print(f"Sent: [CONT]{chunk_number} ({len(chunk)} bytes)")
        time.sleep(2)  # Prevent flooding

    # Send the END packet
    interface.sendText(f"[END]{total_chunks:02d}")
    print(f"Sent: [END]{total_chunks:02d}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 send.py <file.bmp>")
    else:
        send_file(sys.argv[1])

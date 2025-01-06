import meshtastic
import time
import zlib
import hashlib

interface = meshtastic.serial_interface.SerialInterface()
received_chunks = {}
retry_counts = {}
total_chunks = 0
file_hash = ""
retry_limit = 5  # Maximum number of retry attempts per chunk
message_complete = False

def calculate_hash(data):
    return hashlib.sha256(data).hexdigest()

def on_receive(packet, interface):
    global total_chunks, file_hash, message_complete
    payload = packet['payload'].get('data', b'')
    text = packet['payload'].get('text', '')

    if text.startswith("[START]"):
        parts = text.replace("[START]", "").split("#")
        total_chunks = int(parts[0])
        file_hash = parts[1]
        received_chunks.clear()
        retry_counts.clear()
        print(f"Receiving {total_chunks} chunks... Expected Hash: {file_hash}")
        message_complete = False

    elif payload.startswith(b"[CONT]"):
        chunk_number = int(payload[6:8])
        chunk_content = payload[8:]
        received_chunks[chunk_number] = chunk_content
        retry_counts.pop(chunk_number, None)  # Clear retry count for received chunk
        print(f"Received chunk {chunk_number}")

    elif text.startswith("[END]"):
        expected_chunks = int(text.replace("[END]", ""))
        if len(received_chunks) == expected_chunks:
            reconstruct_file()
        else:
            print("Chunks missing! Requesting retransmission...")
            request_missing_chunks(expected_chunks)

def request_missing_chunks(expected_chunks):
    missing = [i for i in range(1, expected_chunks + 1) if i not in received_chunks]
    
    for chunk in missing:
        if retry_counts.get(chunk, 0) < retry_limit:
            interface.sendText(f"[REQ]{chunk:02d}")
            retry_counts[chunk] = retry_counts.get(chunk, 0) + 1
            print(f"Requested chunk {chunk:02d} (Attempt {retry_counts[chunk]}/{retry_limit})")
        else:
            print(f"Chunk {chunk:02d} failed to arrive after {retry_limit} attempts.")

    if all(retry_counts.get(chunk, 0) >= retry_limit for chunk in missing):
        print("File transmission failed. Not all chunks received.")

def reconstruct_file():
    global received_chunks, message_complete
    if message_complete:
        return

    reconstructed = b"".join([received_chunks[i] for i in sorted(received_chunks)])
    
    try:
        file_data = zlib.decompress(reconstructed)
        received_hash = calculate_hash(file_data)

        # Hash verification
        if received_hash == file_hash:
            with open("received_output.bmp", "wb") as f:
                f.write(file_data)
            print("File successfully reconstructed as 'received_output.bmp'")
            print(f"Hash Match: {received_hash}")
        else:
            print("Hash Mismatch! File may be corrupted.")
            print(f"Expected: {file_hash}")
            print(f"Received: {received_hash}")
        
        message_complete = True
    except zlib.error as e:
        print(f"Decompression failed: {e}")

interface.onReceive = on_receive

while True:
    time.sleep(1)

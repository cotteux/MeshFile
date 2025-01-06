# MeshFile - Reliable File Transfer Over Meshtastic Networks

## MeshFile is a lightweight tool for transmitting files over long-range, low-power LoRa networks using Meshtastic devices. It compresses files, splits them into chunks, and ensures integrity with SHA-256 hash verification. Missing chunks are automatically requested, making the system resilient to packet loss.

### Features

* Reliable File Transfer – Ensures complete and accurate file delivery.

* Compression – Reduces file size before transmission.

* Chunked Transmission – Splits files into 200-byte packets.

* Hash Verification – SHA-256 hash checks ensure file integrity.

* Retransmission – Automatically requests missing chunks.

### Hardware Requirements

* 2 x Raspberry Pi (3B/4 or Zero 2 W) – One for sending, one for receiving.

* 2 x Meshtastic LoRa Devices (e.g., T-Beam, Heltec LoRa 32)

* Antennas – Properly tuned to the frequency of your region (433 MHz, 868 MHz, or 915 MHz).

* USB Cable – To connect the LoRa devices to the Raspberry Pi.

### Software Requirements

* Raspberry Pi OS (Lite or Desktop)

* Python 3

* Meshtastic Python Library

* zlib – For compression.

* hashlib – For SHA-256 hashing.

### Setup

#### 1. Install Raspberry Pi OS

* Download and flash Raspberry Pi OS (Lite or Desktop) using the Raspberry Pi Imager.

* Enable SSH (optional) by adding an empty ssh file in the /boot directory.

* Configure Wi-Fi (optional) by adding a wpa_supplicant.conf file in /boot.

#### 2. Install Required Packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-serial git
pip3 install meshtastic
```

#### 3. Connect Meshtastic Devices

1 Connect the LoRa device to each Raspberry Pi via USB.

2 Verify device detection:
```bash
ls /dev/ttyUSB*
```
3 Confirm connection:
```bash
meshtastic --info
```
#### 4. Clone MeshFile
```bash
git clone https://github.com/VeggieVampire/MeshFile
cd meshfile
```
## Sending a File
```bash
python3 send.py file.bmp
```
* Compresses and sends the file in chunks.

* Hash is transmitted for verification.

Receiving a File (Continuous Listening)
```bash
nohup python3 receive.py &
```
* Continuously listens for incoming files and reconstructs the file from received chunks.

* Verifies hash to ensure integrity.

## Example Setup

Sender (Pi 1):
```bash
python3 send.py example.bmp
```
Receiver (Pi 2):
```bash
nohup python3 receive.py &
```
License

Creative Commons Attribution-NonCommercial 4.0 International
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](http://creativecommons.org/licenses/by-nc/4.0/)

MeshFile - Reliable File Transfer Over Meshtastic Networks
Copyright (C)

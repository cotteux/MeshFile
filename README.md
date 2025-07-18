# MeshFile - Reliable File Transfer Over Meshtastic Networks

## MeshFile is a lightweight tool for transmitting files over long-range, low-power LoRa networks using Meshtastic devices. It compresses files, splits them into chunks. Missing chunks are automatically requested, making the system resilient to packet loss.

### Features

* Reliable File Transfer – Ensures complete and accurate file delivery.

* Compression – Reduces file size before transmission with Zlib.

* Retransmission – Automatically requests missing chunks.
  
* Manual retransmission - Resend a part of the file to complete it

### Hardware Requirements

* 2 x computers – One for sending, one for receiving.

* 2 x Meshtastic LoRa Devices (e.g., T-Beam, Heltec LoRa 32)

* Antennas – Properly tuned to the frequency of your region (433 MHz, 868 MHz, or 915 MHz).

* USB Cable – To connect the LoRa devices to the computer.

### Software Requirements

* Linux

* Python 3

* Meshtastic Python Library

* zlib – For compression.

* HashLib
### Setup


#### 1. Install Required Packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-serial git
pip3 install meshtastic
pip3 install zlib
pip3 install hashlib
```

#### 2. Connect Meshtastic Devices

1 Connect the LoRa device to each Raspberry Pi via USB.

2 Verify device detection:
```bash
ls /dev/ttyUSB*
```
3 Confirm connection:
```bash
python3 -m meshtastic --info
```
#### 3. Clone MeshFile
```bash
git clone https://github.com/cotteux/MeshFile.git
cd meshfile
```
## Sending a File
```bash
python3 sender.py <file.txt> '<destination>' <chunk to start(optionnal)>```
Like This for simply send:
```bash
python3 sender.py bob.jpg '!75ce81b8'
```
or like This to resume with chunk 3 and after: 
```bash
python3 sender.py bob.jpg '!75ce81b8' 3
```
* Compresses and sends the file in chunks.

* Hash is transmitted for verification at the end.

Receiving a File (Continuous Listening)
```bash
nohup python3 receiver.py &
```
* Continuously listens for incoming files and reconstructs the file from received chunks.

* Verifies hash to ensure integrity.(TODO)

## Example Setup

Sender (PC 1):
```bash
python3 sender.py <file.txt> '<destination>'
```
Receiver (PC 2):
```bash
nohup python3 receiver.py &
```
License

Creative Commons Attribution-NonCommercial 4.0 International
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](http://creativecommons.org/licenses/by-nc/4.0/)

MeshFile - Reliable File Transfer Over Meshtastic Networks
Copyright (C)

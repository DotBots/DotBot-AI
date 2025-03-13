# DotBot-AI: Object Tracking Firmware for DotBot  

This repository contains the **SEGGER Embedded Studio project** for controlling DotBot using **object tracking with Nicla Vision**.  
The Nicla Vision detects objects and sends their **Y-coordinate** via UART. The DotBot firmware, written in **C**, processes this data to control the motors accordingly.

## Project Structure
- `Nicla_Vision/main.py`: MicroPython code for Nicla Vision.
- "Nicla_Vision/trained_stitch.tflite": Trained AI model for detection.
- "Nicla_Vision/labels_stitch.txt": Model labels.
- "DotBot_firmware_AI/DotBot_control_motors_AI.c": C code for receiving data and controlling the motors.

## Functionality  
### **Nicla Vision (MicroPython)**
- Captures images and detects objects using **TinyML** ("trained_stitch.tflite").  
- Sends **Y-coordinate** via **UART** ("bytearray" format).  
- "center_y" is used instead of "center_x" because the camera is rotated 90°.

### **DotBot Firmware (C)**
- Listens to UART data from Nicla Vision.  
- Determines whether the object is **above, below, or centered**.  
- Adjusts **motor speed and direction** accordingly. 

## Installation & Setup

### 1.- Connect the Arduino Nicla Vision to the computer via USB and upload the files main.py, labels_stitch.txt, and trained_stitch.tflite
  
### 2.- Clone the Required Repositories
- Since this project depends on the **DotBot Firmware**, you need to clone it inside the same parent directory as this repository: 

```bash
git clone https://github.com/DotBots/DotBot-firmware
```

- Make sure DotBot-AI and DotBot-Firmware are in the same directory.

### 3.- Install **SEGGER Embedded Studio** (if not already installed).

### 4.- Upload the firmware to the DotBot.

- 1.- Open **SEGGER Embedded Studio**
- 2.- Connect the **nRF5340-DK** to the computer and then to the **DotBot**.
- 3.- Power on the **nRF5340-DK** and the **DotBot**.
- 4.- Go to Target -> Connect J-Link.
- 5.- To upload the firmware, double-click the **DotBot_firmware_AI** project (it should now appear in bold) and press Ctrl+t followed by l (lowercase L).

## Run the system

### 1.- Connect the Nicla Vision arduino to the battery, this will turn it on automatically. 
### 2.- Turn the Dotbot switch to “ON”. DotBot will automatically begin detecting and tracking the object.

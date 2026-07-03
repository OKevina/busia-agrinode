# busia-agrinode

An ESP32 (MicroPython, no display) soil-moisture and microclimate node that
gives per-crop irrigation advice. The node reads temperature, humidity and soil
moisture, encrypts each reading, and publishes it over MQTT (TLS) to a HiveMQ
Cloud broker. A Python Flask backend subscribes, verifies and decrypts the
readings, stores them in SQLite, and serves a web dashboard with live values,
historical charts and CSV export.

The node's only local feedback is the on-board LED (on when its configured crop
needs water) and serial-console prints in Thonny. The web dashboard is the main
readout.

## How it works

- The node measures soil moisture and compares it to a per-crop threshold
  (maize 45 percent, beans 40 percent, sweet potato 30 percent). It advises
  watering when soil is below the threshold. It does not operate a pump.
- Temperature and humidity adjust the threshold: hot or dry air raises it so
  watering is advised sooner.
- Each reading is encrypted and signed on the node (AES-128-CBC with an
  HMAC-SHA256 tag) before it is sent, so the payload is ciphertext in transit
  and at rest. Only the server holds the key and can decrypt.

## Data flow

ESP32 node, then MQTT over TLS (port 8883), then HiveMQ Cloud, then the Flask
server (which decrypts and stores ciphertext in SQLite), then the web dashboard
(which fetches decrypted JSON from the server over HTTP).

## Layout

    firmware/    boot.py, config.py, main.py, secure.py   (runs on the ESP32)
    server/      app.py, secure.py, requirements.txt,
                 credentials_example.py                    (runs on the laptop)
    dashboard/   index.html                                (served by app.py)

## Reading fields

Each reading is a JSON object with these fields: node, crop, temp, humidity,
soil, threshold, irrigate.

## Requirements

- Python 3.
- Thonny, used to flash MicroPython and edit the board.
- A USB-serial driver for the ESP32 (usually CP210x or CH340).
- MicroPython firmware (a .bin file) for the ESP32.
- A HiveMQ Cloud cluster (free tier) with a username and password.
- A 2.4 GHz Wi-Fi network with internet access.

## Setup

1. Install the Python dependencies (Flask, paho-mqtt, cryptography):

       pip install -r server/requirements.txt

2. Create the server credentials file. Copy the example, then edit it:

       copy server\credentials_example.py server\credentials.py

   Open server/credentials.py and set MQTT_BROKER, MQTT_USER and MQTT_PASS from
   your HiveMQ Cloud cluster, and set SECRET_PASSPHRASE to any shared secret.
   This file is git-ignored and must not be committed.

3. Edit firmware/config.py and fill in the placeholder values: WIFI_SSID,
   WIFI_PASS, MQTT_BROKER, MQTT_USER, MQTT_PASS and SECRET_PASSPHRASE.
   SECRET_PASSPHRASE must be identical to the one in server/credentials.py, or
   the server will reject the node's messages.

4. Flash MicroPython onto the ESP32 with Thonny, then upload the firmware files
   to the board: boot.py, config.py, main.py and secure.py.

5. Wire the sensors (power both sensors from 3.3 V):

   - DHT22 data pin to GPIO4
   - Soil sensor analog output to GPIO33
   - LED, through a resistor, to GPIO32

6. Calibrate the soil sensor. Read the raw ADC value in dry soil and in wet
   soil, then set SOIL_DRY and SOIL_WET in firmware/config.py.

## Running

1. Start the server:

       python server/app.py

2. Open the dashboard at http://localhost:8000. To view it from a phone on the
   same network, use http://<laptop-ip>:8000.

The server connects to HiveMQ, subscribes to the telemetry topic, and stores
each reading. The dashboard shows the per-crop advisory, the current sensor
values and historical charts, and provides a CSV download.

## Development and testing mode

Setting `SIMULATE = True` in `firmware/config.py` makes the node publish generated sensor values (tagged `[SIM]` in the serial log). This is for developing and testing the full node-to-dashboard pipeline offline — before the sensors are wired, or when hardware is unavailable.

## Security notes

Real secrets live only in server/credentials.py (git-ignored) and in the values
you enter in firmware/config.py on the board. Do not commit them. The
pre-shared passphrase is a demonstration key; a production deployment would
provision a unique key to each device securely.

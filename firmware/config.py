# config.py — settings imported by boot.py, main.py and secure.py.
# Fill in the placeholder values before flashing this file to the board.

# Wi-Fi
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASS = "YOUR_WIFI_PASSWORD"

# HiveMQ Cloud (MQTT over TLS)
MQTT_BROKER = "YOUR_CLUSTER.s1.eu.hivemq.cloud"
MQTT_PORT   = 8883
MQTT_USER   = "YOUR_HIVEMQ_USERNAME"
MQTT_PASS   = "YOUR_HIVEMQ_PASSWORD"

# Shared secret for payload encryption — MUST match server/credentials.py
SECRET_PASSPHRASE = b"CHANGE_ME_shared_secret_passphrase"

# Node identity / topics
NODE_ID   = "4d"
TOPIC     = b"kevin/agrinode/4d/telemetry"
CMD_TOPIC = b"kevin/agrinode/4d/cmd"
PUB_EVERY_S = 5

# Soil-moisture calibration (raw 12-bit ADC values measured dry / wet)
SOIL_DRY = 3200
SOIL_WET = 1200

# Crops with their base "irrigate below" soil-moisture percentages
CROPS = {
    "maize":        45,
    "beans":        40,
    "sweet_potato": 30,
}
ACTIVE_CROP = "maize"

# Microclimate adjustment: hot and/or dry air raises the trigger point
ET_TEMP_HOT  = 30
ET_HUMID_DRY = 40
ET_ADJUST    = 5

# Publish generated values when the physical sensors are unavailable
SIMULATE = False

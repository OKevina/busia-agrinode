# credentials_example.py — copy to credentials.py and fill in your real values.
# credentials.py is gitignored, so secrets are never committed.

MQTT_BROKER = "YOUR_CLUSTER.s1.eu.hivemq.cloud"
MQTT_USER   = "YOUR_HIVEMQ_USERNAME"
MQTT_PASS   = "YOUR_HIVEMQ_PASSWORD"

# Must equal the firmware SECRET_PASSPHRASE (config.py on the board)
SECRET_PASSPHRASE = b"CHANGE_ME_shared_secret_passphrase"

import time
import json
import ssl
import random
import dht
from machine import Pin, ADC
from umqtt.simple import MQTTClient
import config
import secure

DHT_PIN  = 4
SOIL_PIN = 33
LED_PIN  = 32

dht_sensor = dht.DHT22(Pin(DHT_PIN))

soil_adc = ADC(Pin(SOIL_PIN))
soil_adc.atten(ADC.ATTN_11DB)
soil_adc.width(ADC.WIDTH_12BIT)

led = Pin(LED_PIN, Pin.OUT)
led.value(0)

state = {"crop": config.ACTIVE_CROP}

_sim = {"t": 25.0, "h": 60.0}
def sim_step():
    _sim["t"] = max(15.0, min(38.0, _sim["t"] + (random.random() - 0.5) * 1.2))
    _sim["h"] = max(20.0, min(95.0, _sim["h"] + (random.random() - 0.5) * 4.0))
    return round(_sim["t"], 1), int(_sim["h"]), 20 + int(random.random() * 70)


def soil_percent(raw):
    span = config.SOIL_DRY - config.SOIL_WET
    if span == 0:
        return 0
    pct = (config.SOIL_DRY - raw) * 100 // span
    if pct < 0:
        pct = 0
    elif pct > 100:
        pct = 100
    return pct


def effective_threshold(base, temp, humidity):
    adj = 0
    if temp is not None and temp > config.ET_TEMP_HOT:
        adj += config.ET_ADJUST
    if humidity is not None and humidity < config.ET_HUMID_DRY:
        adj += config.ET_ADJUST
    thr = base + adj
    if thr > 100:
        thr = 100
    return thr


def on_cmd(topic, msg):
    try:
        crop = json.loads(msg).get("crop")
    except Exception as e:
        print("CMD: ignoring bad message:", e)
        return
    if crop in config.CROPS:
        state["crop"] = crop
        print("CMD: crop changed to", crop)
    else:
        print("CMD: ignoring unknown crop:", crop)


def connect_mqtt():
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.verify_mode = ssl.CERT_NONE
    client = MQTTClient(b"kevin-agrinode-node-4d", config.MQTT_BROKER,
                        port=config.MQTT_PORT, user=config.MQTT_USER,
                        password=config.MQTT_PASS, ssl=ctx)
    client.set_callback(on_cmd)
    client.connect()
    client.subscribe(config.CMD_TOPIC)
    print("MQTT: connected to %s:%d (listening for crop cmds on %s)"
          % (config.MQTT_BROKER, config.MQTT_PORT, config.CMD_TOPIC))
    return client


def main():
    client = None

    while True:
        if client is not None:
            try:
                client.check_msg()
            except Exception as e:
                print("MQTT: check_msg failed, will reconnect:", e)
                client = None

        crop = state["crop"]
        base = config.CROPS.get(crop, 40)

        if config.SIMULATE:
            temp, humidity, soil = sim_step()
            raw = 0
            tag = "[SIM] "
        else:
            tag = ""
            temp = None
            humidity = None
            try:
                dht_sensor.measure()
                temp = dht_sensor.temperature()
                humidity = dht_sensor.humidity()
            except Exception as e:
                print("DHT: read failed:", e)
            raw = soil_adc.read()
            soil = soil_percent(raw)

        threshold = effective_threshold(base, temp, humidity)
        irrigate = soil < threshold
        led.value(1 if irrigate else 0)

        print("%scrop=%s temp=%s humidity=%s soil=%d%% (raw=%d) base=%d%% eff=%d%% -> %s"
              % (tag, crop,
                 "--" if temp is None else "%.1fC" % temp,
                 "--" if humidity is None else "%.0f%%" % humidity,
                 soil, raw, base, threshold,
                 "IRRIGATE" if irrigate else "soil OK"))

        reading = {
            "node":      config.NODE_ID,
            "crop":      crop,
            "temp":      temp,
            "humidity":  humidity,
            "soil":      soil,
            "threshold": threshold,
            "irrigate":  irrigate,
        }
        try:
            if client is None:
                client = connect_mqtt()
            client.publish(config.TOPIC, secure.encrypt_reading(reading))
        except Exception as e:
            print("MQTT: publish failed, will reconnect next cycle:", e)
            client = None

        time.sleep(config.PUB_EVERY_S)


main()

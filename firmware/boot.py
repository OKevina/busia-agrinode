# boot.py — runs on power-up before main.py: brings up Wi-Fi in station mode.

import network
import time
import config


def connect_wifi(timeout_s=10):
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if not sta.isconnected():
        print("WiFi: connecting to '%s' ..." % config.WIFI_SSID)
        sta.connect(config.WIFI_SSID, config.WIFI_PASS)
        deadline = time.ticks_add(time.ticks_ms(), timeout_s * 1000)
        while not sta.isconnected():
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                print("WiFi: FAILED to connect within %ds." % timeout_s)
                return None
            time.sleep_ms(200)
    ip = sta.ifconfig()[0]
    print("WiFi: connected. IP =", ip)
    return ip


connect_wifi()

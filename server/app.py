import os
import csv
import io
import json
import sqlite3
import threading
from datetime import datetime, timezone

from flask import Flask, jsonify, request, send_from_directory, Response
import paho.mqtt.client as mqtt

import secure
from credentials import MQTT_BROKER, MQTT_USER, MQTT_PASS

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "dashboard"))
DB_PATH       = os.path.join(BASE_DIR, "agrinode.db")

MQTT_PORT   = 8883
MQTT_TOPIC  = "kevin/agrinode/4d/telemetry"

app = Flask(__name__)


def db_connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = db_connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id  INTEGER PRIMARY KEY AUTOINCREMENT,
            ts  TEXT,
            enc TEXT
        )
    """)
    conn.commit()
    conn.close()


def store_token(token):
    conn = db_connect()
    conn.execute(
        "INSERT INTO readings (ts, enc) VALUES (?, ?)",
        (datetime.now(timezone.utc).isoformat(timespec="seconds"), token),
    )
    conn.commit()
    conn.close()


def on_connect(client, userdata, flags, rc, *args):
    print("MQTT: connected (rc=%s), subscribing to %s" % (rc, MQTT_TOPIC))
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    token = msg.payload.decode("utf-8", "replace")
    reading = secure.decrypt_reading(token)
    if reading is None:
        print("SECURITY: rejected tampered/unreadable message (%d bytes)"
              % len(msg.payload))
        return
    try:
        store_token(token)
    except Exception as e:
        print("DB: insert failed (%s)" % e)


def mqtt_thread():
    try:
        client = mqtt.Client(
            client_id="kevin-agrinode-server",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
    except (AttributeError, TypeError):
        client = mqtt.Client(client_id="kevin-agrinode-server")

    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set()
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_forever()


@app.route("/")
def index():
    return send_from_directory(DASHBOARD_DIR, "index.html")


@app.route("/history")
def history():
    limit = request.args.get("limit", default=200, type=int)
    conn = db_connect()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, ts, enc FROM readings ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    out = []
    for r in reversed(rows):
        d = secure.decrypt_reading(r["enc"])
        if d is None:
            continue
        d["id"] = r["id"]
        d["ts"] = r["ts"]
        out.append(d)
    return jsonify(out)


@app.route("/security/raw")
def security_raw():
    limit = request.args.get("limit", default=5, type=int)
    conn = db_connect()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, ts, enc FROM readings ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return jsonify([
        {"id": r["id"], "ts": r["ts"], "ciphertext": r["enc"]}
        for r in reversed(rows)
    ])


@app.route("/export.csv")
def export_csv():
    conn = db_connect()
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT id, ts, enc FROM readings ORDER BY id ASC").fetchall()
    conn.close()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "ts", "node", "crop", "temp", "humidity",
                     "soil", "threshold", "irrigate"])
    for r in rows:
        d = secure.decrypt_reading(r["enc"]) or {}
        writer.writerow([r["id"], r["ts"], d.get("node"), d.get("crop"),
                         d.get("temp"), d.get("humidity"), d.get("soil"),
                         d.get("threshold"), 1 if d.get("irrigate") else 0])

    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=agrinode.csv"},
    )


if __name__ == "__main__":
    init_db()
    threading.Thread(target=mqtt_thread, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
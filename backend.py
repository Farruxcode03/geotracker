
import os
from pathlib import Path
from threading import Lock

from flask import Flask, Response, jsonify, request
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from config import Config

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

socketio = SocketIO(
    app,
    async_mode="threading",
    cors_allowed_origins="*"
)

CORS(app, resources={
    r"/api/*": {
        "origins": app.config["CORS_ORIGINS"]
    }
})

# Umumiy foydalanuvchilar holati
online_users = set()
locations = {}

state_lock = Lock()


def get_locations():
    with state_lock:
        return list(locations.values())


def broadcast_online_count():
    with state_lock:
        count = len(online_users)

    socketio.emit("online_count", {
        "count": count
    })


def broadcast_locations():
    socketio.emit("locations_update", {
        "locations": get_locations()
    })


@socketio.on("connect")
def handle_connect(auth=None):
    with state_lock:
        online_users.add(request.sid)

    broadcast_online_count()

    emit("locations_update", {
        "locations": get_locations()
    })


@socketio.on("location_update")
def handle_location_update(data):
    if not isinstance(data, dict):
        return

    name = str(data.get("name", "")).strip()[:40]

    try:
        lat = float(data.get("lat"))
        lon = float(data.get("lon"))
    except (TypeError, ValueError):
        return

    if not name:
        return

    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return

    with state_lock:
        locations[request.sid] = {
            "id": request.sid,
            "name": name,
            "lat": lat,
            "lon": lon
        }

    broadcast_locations()


@socketio.on("location_stop")
def handle_location_stop():
    with state_lock:
        locations.pop(request.sid, None)

    broadcast_locations()


@socketio.on("disconnect")
def handle_disconnect(reason=None):
    with state_lock:
        online_users.discard(request.sid)
        locations.pop(request.sid, None)

    broadcast_online_count()
    broadcast_locations()


@app.route("/")
def home():
    html_path = BASE_DIR / "index.html"

    return Response(
        html_path.read_text(encoding="utf-8"),
        content_type="text/html; charset=utf-8"
    )


@app.route("/api/status")
def status():
    with state_lock:
        count = len(online_users)
        gps_count = len(locations)

    return jsonify({
        "status": "online",
        "online_users": count,
        "gps_users": gps_count
    })


if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )

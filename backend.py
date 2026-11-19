
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

# Online brauzer ulanishlari
online_users = set()
online_lock = Lock()


def broadcast_online_count():
    with online_lock:
        count = len(online_users)

    socketio.emit("online_count", {
        "count": count
    })


@socketio.on("connect")
def handle_connect(auth=None):
    with online_lock:
        online_users.add(request.sid)

    broadcast_online_count()


@socketio.on("disconnect")
def handle_disconnect(reason=None):
    with online_lock:
        online_users.discard(request.sid)

    broadcast_online_count()


@app.route("/")
def home():
    html_path = BASE_DIR / "index.html"

    return Response(
        html_path.read_text(encoding="utf-8"),
        content_type="text/html; charset=utf-8"
    )


@app.route("/api/status")
def status():
    return jsonify({
        "status": "online",
        "online_users": len(online_users)
    })


if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )


import os
from pathlib import Path

from flask import Flask, Response, jsonify
from flask_socketio import SocketIO
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


@app.route("/")
def home():
    html_path = BASE_DIR / "index.html"

    return Response(
        html_path.read_text(encoding="utf-8"),
        content_type="text/html; charset=utf-8"
    )


@app.route("/api/status")
def status():
    try:
        with db.engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")

        return jsonify({
            "status": "online",
            "database": "connected"
        })

    except Exception as error:
        app.logger.exception("Database connection error")

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )

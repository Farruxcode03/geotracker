
import os
from flask import Flask, Response, jsonify
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
socketio = SocketIO(app, async_mode="threading")
CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})


@app.route("/")
def home():
    return Response(
        open("index.html", encoding="utf-8").read(),
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
        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    print("GEOTRACKER PRO ISHGA TUSHDI")
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)

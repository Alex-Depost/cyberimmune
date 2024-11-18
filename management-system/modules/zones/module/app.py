from flask import Flask, jsonify
from config import Config

app = Flask(__name__)

@app.route("/allowed_zones", methods=["GET"])
def get_allowed_zones():
    """Возвращает список разрешённых зон."""
    return jsonify(Config.ZONES), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8003)

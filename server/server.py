from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import os

SERVER_ID = os.environ.get("SERVER_ID")

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)


@app.route('/home', methods=['GET'])
def home(): 
    return jsonify(message=f"Hello from Server: {SERVER_ID}", status="successful"), 200


@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    return "", 200

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)


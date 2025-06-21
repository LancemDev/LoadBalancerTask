from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import socket

app = Flask(__name__)
CORS(app)

# Get server ID from environment variable or use hostname as fallback
SERVER_ID = os.environ.get("SERVER_ID", socket.gethostname())

@app.route('/home', methods=['GET'])
def home():
    return jsonify({
        "message": f"Hello from Server: {SERVER_ID}",
        "status": "successful"
    }), 200

@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    # Return empty response with 200 status code
    return "", 200

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def handle_other_paths(path):
    # Return 404 for any other path
    return jsonify({
        "message": f"Endpoint /{path} not found on server {SERVER_ID}",
        "status": "failure"
    }), 404

if __name__ == '__main__':
    # Get port from environment variable or use default 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)


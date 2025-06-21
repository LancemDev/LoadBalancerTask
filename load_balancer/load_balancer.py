from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
# import os
import threading
import time
from .consistent_hash import ConsistentHash

class LoadBalancer:
    def __init__(self, num_servers=3, num_slots=512):
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Initialize consistent hash
        self.consistent_hash = ConsistentHash(
            num_servers=num_servers,
            num_slots=num_slots,
            num_virtual_servers=9  # log2(512) = 9
        )
        
        # Server configuration
        self.servers = {}
        self.server_port_start = 5001
        self.health_check_interval = 5  # seconds
        
        # Register routes
        self._register_routes()
        
        # Start health check thread
        self._start_health_check()
    
    def _register_routes(self):
        @self.app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
        def route_request(path):
            # Get request ID from header or generate one
            request_id = int(request.headers.get('X-Request-ID', hash(request.remote_addr + str(time.time()))))
            
            # Get server for this request
            server_id = self.consistent_hash.get_server(request_id)
            if server_id is None:
                return jsonify({"error": "No available servers"}), 503
            
            # Forward request to the appropriate server
            server_url = f"http://server{server_id}:{self.server_port_start + server_id - 1}"
            
            try:
                # Forward the request to the selected server
                response = requests.request(
                    method=request.method,
                    url=f"{server_url}/{path}",
                    headers=dict(request.headers),
                    data=request.get_data(),
                    cookies=request.cookies,
                    allow_redirects=False
                )
                
                return (response.content, response.status_code, dict(response.headers))
                
            except requests.exceptions.RequestException as e:
                return jsonify({"error": f"Failed to forward request: {str(e)}"}), 500
        
        @self.app.route('/add_server', methods=['POST'])
        def add_server():
            data = request.get_json()
            server_id = data.get('server_id')
            
            if server_id is None:
                return jsonify({"error": "server_id is required"}), 400
                
            self.consistent_hash.add_server(server_id)
            return jsonify({"message": f"Server {server_id} added"}), 200
        
        @self.app.route('/remove_server', methods=['POST'])
        def remove_server():
            data = request.get_json()
            server_id = data.get('server_id')
            
            if server_id is None:
                return jsonify({"error": "server_id is required"}), 400
                
            self.consistent_hash.remove_server(server_id)
            return jsonify({"message": f"Server {server_id} removed"}), 200
    
    def _health_check(self):
        while True:
            time.sleep(self.health_check_interval)
            
            for server_id in list(self.consistent_hash.servers):
                try:
                    response = requests.get(
                        f"http://server{server_id}:{self.server_port_start + server_id - 1}/heartbeat",
                        timeout=2
                    )
                    if response.status_code != 200:
                        self.consistent_hash.remove_server(server_id)
                        print(f"Server {server_id} failed health check, removed from pool")
                except:
                    self.consistent_hash.remove_server(server_id)
                    print(f"Server {server_id} failed health check, removed from pool")
    
    def _start_health_check(self):
        health_check_thread = threading.Thread(target=self._health_check, daemon=True)
        health_check_thread.start()
    
    def run(self, host='0.0.0.0', port=5000):
        # Add initial servers
        for i in range(1, 4):  # Add 3 servers by default
            self.consistent_hash.add_server(i)
        
        self.app.run(host=host, port=port, debug=True)

if __name__ == '__main__':
    lb = LoadBalancer()
    lb.run()

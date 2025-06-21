from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os
import threading
import time
import random
import string
import json
from .consistent_hash import ConsistentHash

class LoadBalancer:
    def __init__(self, num_servers=3, num_slots=512, num_virtual_servers=9):
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Initialize consistent hash
        self.consistent_hash = ConsistentHash(
            num_slots=num_slots,
            num_virtual_servers=num_virtual_servers
        )
        
        # Server configuration
        self.servers = {}
        self.server_port = 5000  # All servers run on port 5000 internally
        self.health_check_interval = 5  # seconds
        self.base_server_name = "Server"
        
        # Register routes
        self._register_routes()
        
        # Add initial servers
        self._add_initial_servers(num_servers)
        
        # Start health check thread
        self._start_health_check()
    
    def _add_initial_servers(self, count):
        for i in range(1, count + 1):
            server_name = f"{self.base_server_name}_{i}"
            hostname = f"server{i}"
            self.consistent_hash.add_server(server_name, hostname)
            self.servers[server_name] = {
                'hostname': hostname,
                'port': self.server_port,
                'status': 'healthy'
            }
            print(f"Added initial server: {server_name} ({hostname})")
    
    def _register_routes(self):
        @self.app.route('/rep', methods=['GET'])
        def get_replicas():
            servers = []
            for server_name in self.consistent_hash.get_servers():
                server_info = self.consistent_hash.get_server_info(server_name)
                servers.append({
                    'name': server_name,
                    'hostname': server_info['hostname']
                })
            
            return jsonify({
                'message': {
                    'N': len(servers),
                    'replicas': [s['name'] for s in servers]
                },
                'status': 'successful'
            }), 200
        
        @self.app.route('/add', methods=['POST'])
        def add_servers():
            data = request.get_json()
            if not data or 'n' not in data:
                return jsonify({
                    'message': 'Invalid request',
                    'status': 'failure'
                }), 400
            
            n = data['n']
            hostnames = data.get('hostnames', [])
            
            if len(hostnames) > n:
                return jsonify({
                    'message': 'Number of hostnames exceeds number of servers to add',
                    'status': 'failure'
                }), 400
            
            added_servers = []
            for i in range(n):
                server_name = hostnames[i] if i < len(hostnames) else f"{self.base_server_name}_{len(self.consistent_hash.get_servers()) + 1}"
                if self.consistent_hash.add_server(server_name):
                    added_servers.append(server_name)
            
            return jsonify({
                'message': {
                    'N': self.consistent_hash.get_server_count(),
                    'replicas': self.consistent_hash.get_servers()
                },
                'status': 'successful'
            }), 200
        
        @self.app.route('/rm', methods=['DELETE'])
        def remove_servers():
            data = request.get_json()
            if not data or 'n' not in data:
                return jsonify({
                    'message': 'Invalid request',
                    'status': 'failure'
                }), 400
            
            n = data['n']
            hostnames = data.get('hostnames', [])
            
            if n > self.consistent_hash.get_server_count():
                return jsonify({
                    'message': 'Cannot remove more servers than available',
                    'status': 'failure'
                }), 400
            
            if len(hostnames) > n:
                return jsonify({
                    'message': 'Number of hostnames exceeds number of servers to remove',
                    'status': 'failure'
                }), 400
            
            # Remove specified servers
            removed = 0
            for hostname in hostnames:
                if self.consistent_hash.remove_server(hostname):
                    removed += 1
            
            # If we still need to remove more servers, remove random ones
            remaining = n - removed
            servers = self.consistent_hash.get_servers()
            for _ in range(min(remaining, len(servers))):
                if servers:
                    self.consistent_hash.remove_server(servers[0])
            
            return jsonify({
                'message': {
                    'N': self.consistent_hash.get_server_count(),
                    'replicas': self.consistent_hash.get_servers()
                },
                'status': 'successful'
            }), 200
        
        @self.app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
        def route_request(path):
            # Get request ID from header or generate one
            request_id = int(request.headers.get('X-Request-ID', hash(request.remote_addr + str(time.time()))))
            
            # Get server for this request
            server_name = self.consistent_hash.get_server(request_id)
            if server_name is None:
                return jsonify({"message": "No available servers", "status": "failure"}), 503
            
            server_info = self.consistent_hash.get_server_info(server_name)
            if not server_info:
                return jsonify({"message": f"Server {server_name} not found", "status": "failure"}), 503
                
            server_hostname = server_info.get('hostname')
            server_url = f"http://{server_hostname}:{self.server_port}"
            print(f"Routing request to {server_url}/{path}")
            
            try:
                # Forward the request to the selected server
                response = requests.request(
                    method=request.method,
                    url=f"{server_url}/{path}",
                    headers={k: v for k, v in request.headers if k != 'Host'},
                    data=request.get_data(),
                    cookies=request.cookies,
                    allow_redirects=False,
                    timeout=5
                )
                
                # Return the response from the server
                return (
                    response.content,
                    response.status_code,
                    dict(response.headers)
                )
                
            except requests.exceptions.RequestException as e:
                # If request fails, remove the server and try again with a different one
                self.consistent_hash.remove_server(server_name)
                return self.route_request(path)
    
    def _health_check(self):
        while True:
            time.sleep(self.health_check_interval)
            
            for server_name in self.consistent_hash.get_servers()[:]:
                try:
                    server_info = self.consistent_hash.get_server_info(server_name)
                    if not server_info:
                        print(f"Server {server_name} not found in consistent hash")
                        continue
                        
                    server_hostname = server_info.get('hostname')
                    if not server_hostname:
                        print(f"No hostname for server {server_name}")
                        continue
                        
                    response = requests.get(
                        f"http://{server_hostname}:{self.server_port}/heartbeat",
                        timeout=2
                    )
                    if response.status_code != 200:
                        print(f"Server {server_name} failed health check with status {response.status_code}")
                        self.consistent_hash.remove_server(server_name)
                        if server_name in self.servers:
                            del self.servers[server_name]
                        print(f"Removed server {server_name} from pool")
                        
                except requests.exceptions.RequestException as e:
                    print(f"Health check failed for {server_name}: {str(e)}")
                    self.consistent_hash.remove_server(server_name)
                    if server_name in self.servers:
                        del self.servers[server_name]
                    print(f"Removed server {server_name} from pool due to error")
    
    def _start_health_check(self):
        health_check_thread = threading.Thread(target=self._health_check, daemon=True)
        health_check_thread.start()
    
    def run(self, host='0.0.0.0', port=5000):
        # Add initial servers
        for i in range(1, 4):
            self.consistent_hash.add_server(f"{self.base_server_name}_{i}", f"server{i}")
        
        self.app.run(host=host, port=port, debug=True, threaded=True)

def create_app():
    lb = LoadBalancer()
    return lb.app

if __name__ == '__main__':
    lb = LoadBalancer()
    lb.run()

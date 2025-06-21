class ConsistentHash:
    def __init__(self, num_servers=3, num_slots=512, num_virtual_servers=9):
        """
        Initialize the consistent hash map
        :param num_servers: Number of server containers (N)
        :param num_slots: Total number of slots in the hash map
        :param num_virtual_servers: Number of virtual servers per physical server (K)
        """
        self.num_slots = num_slots
        self.num_virtual_servers = num_virtual_servers
        self.hash_map = [None] * num_slots
        self.servers = {}  # server_id -> server_info
        self.server_counter = 0
    
    def hash_request(self, i):
        """Hash function for request mapping: H(i) = i² + 2i + 172"""
        return (i * i + 2 * i + 172) % self.num_slots
    
    def hash_virtual_server(self, i, j):
        """Hash function for virtual server mapping: Φ(i, j) = i + j + 2j + 25"""
        return (i + j + 2 * j + 25) % self.num_slots
    
    def add_server(self, server_name, hostname=None):
        """Add a server to the consistent hash map"""
        if server_name in self.servers:
            return False
            
        server_id = self.server_counter
        self.server_counter += 1
        
        self.servers[server_name] = {
            'id': server_id,
            'hostname': hostname or f'server{server_id}',
            'virtual_servers': []
        }
        
        # Add virtual servers
        for j in range(self.num_virtual_servers):
            slot = self.hash_virtual_server(server_id, j)
            
            # Linear probing in case of collision
            while self.hash_map[slot] is not None:
                slot = (slot + 1) % self.num_slots
                
            self.hash_map[slot] = server_name
            self.servers[server_name]['virtual_servers'].append(slot)
        
        return True
    
    def remove_server(self, server_name):
        """Remove a server and all its virtual servers from the hash map"""
        if server_name not in self.servers:
            return False
            
        # Remove all virtual servers for this server
        for slot in self.servers[server_name]['virtual_servers']:
            self.hash_map[slot] = None
            
        del self.servers[server_name]
        return True
    
    def get_server(self, request_id):
        """Get the server that should handle the given request"""
        if not self.servers:
            return None
            
        slot = self.hash_request(request_id)
        
        # Linear probing to find the next available server
        for i in range(self.num_slots):
            current_slot = (slot + i) % self.num_slots
            if self.hash_map[current_slot] is not None:
                return self.hash_map[current_slot]
                
        return None
    
    def get_servers(self):
        """Get list of all server names"""
        return list(self.servers.keys())
    
    def get_server_info(self, server_name):
        """Get information about a specific server"""
        return self.servers.get(server_name)
    
    def get_server_count(self):
        """Get the number of servers"""
        return len(self.servers)
    
    def get_distribution(self):
        """Get the distribution of virtual servers across physical servers"""
        return {name: len(info['virtual_servers']) for name, info in self.servers.items()}

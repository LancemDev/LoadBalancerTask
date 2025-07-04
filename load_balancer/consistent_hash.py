class ConsistentHash:
    def __init__(self, num_servers=3, num_slots=512, num_virtual_servers=100):
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
    
    def _fnv1a_hash(self, data):
        """FNV-1a hash function for better distribution"""
        if isinstance(data, int):
            data = str(data).encode('utf-8')
        elif isinstance(data, str):
            data = data.encode('utf-8')
        
        # 32-bit FNV-1a hash
        h = 0x811c9dc5  # FNV offset basis
        for byte in data:
            h ^= byte
            h = (h * 0x01000193) & 0xffffffff  # FNV prime for 32-bit
        return h
    
    def hash_request(self, i):
        """Improved hash function for request mapping using FNV-1a"""
        # Convert to string to handle both string and integer inputs
        hash_val = self._fnv1a_hash(str(i))
        return hash_val % self.num_slots
    
    def hash_virtual_server(self, i, j):
        """Improved hash function for virtual server mapping using FNV-1a"""
        # Create a unique string combining server_id and replica_id
        key = f"{i}:{j}"
        hash_val = self._fnv1a_hash(key)
        return hash_val % self.num_slots
    
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
        
        # Use binary search for better performance with many slots
        for i in range(self.num_slots):
            current_slot = (slot + i) % self.num_slots
            if self.hash_map[current_slot] is not None:
                return self.hash_map[current_slot]
        
        # Fallback: Find first available server (shouldn't happen in normal operation)
        for server_name in self.servers:
            if self.servers[server_name]['virtual_servers']:
                return server_name
                
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

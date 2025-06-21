class ConsistentHash:
    def __init__(self, num_servers=3, num_slots=512, num_virtual_servers=9):
        """
        Initialize the consistent hash map
        :param num_servers: Number of server containers (N)
        :param num_slots: Total number of slots in the hash map
        :param num_virtual_servers: Number of virtual servers per physical server (K)
        """
        self.num_servers = num_servers
        self.num_slots = num_slots
        self.num_virtual_servers = num_virtual_servers
        self.hash_map = [None] * num_slots
        self.servers = set()
        
    def hash_request(self, i):
        """Hash function for request mapping: H(i) = i² + 2i + 17"""
        return (i * i + 2 * i + 17) % self.num_slots
    
    def hash_virtual_server(self, server_id, j):
        """Hash function for virtual server mapping: Φ(i, j) = i + j + 2j + 25"""
        return (server_id + j + 2 * j + 25) % self.num_slots
    
    def add_server(self, server_id):
        """Add a server to the consistent hash map"""
        if server_id in self.servers:
            return
            
        self.servers.add(server_id)
        
        # Add virtual servers
        for j in range(self.num_virtual_servers):
            slot = self.hash_virtual_server(server_id, j)
            
            # Linear probing in case of collision
            while self.hash_map[slot] is not None:
                slot = (slot + 1) % self.num_slots
                
            self.hash_map[slot] = server_id
    
    def remove_server(self, server_id):
        """Remove a server and all its virtual servers from the hash map"""
        if server_id not in self.servers:
            return
            
        self.servers.remove(server_id)
        
        # Remove all virtual servers for this server
        for i in range(self.num_slots):
            if self.hash_map[i] == server_id:
                self.hash_map[i] = None
    
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
                
        return None  # Should never reach here if we have servers

    def get_server_distribution(self):
        """Get the distribution of requests across servers (for debugging)"""
        distribution = {server: 0 for server in self.servers}
        for slot in self.hash_map:
            if slot is not None:
                distribution[slot] += 1
        return distribution

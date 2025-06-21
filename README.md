# Distributed Load Balancer with Consistent Hashing

A distributed load balancer implementation using consistent hashing algorithm to distribute load across multiple server containers. This implementation includes features like dynamic server management, health checks, and performance monitoring.

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.8+

### Running the System

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd loadbalancer
   ```

2. **Build and start the services**
   ```bash
   # Build the containers
   docker-compose build
   
   # Start the services
   docker-compose up -d
   ```

3. **Verify the services**
   ```bash
   # Check running containers
   docker-compose ps
   
   # View logs
   docker-compose logs -f
   ```

4. **Test the load balancer**
   ```bash
   # Get list of servers
   curl http://localhost:5000/rep
   
   # Send a test request
   curl http://localhost:5000/home
   ```

### Running Performance Tests

1. **Set up the test environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r tests/requirements.txt
   ```

2. **Run all tests**
   ```bash
   python -m tests.performance_test
   ```

3. **View test results**
   - Test results and plots will be saved in the project root
   - View the generated images in the `assets/task4/` directory

## Features

- Consistent hashing with virtual nodes for even distribution
- Dynamic addition and removal of server instances
- Health checks and automatic failure detection
- RESTful API for managing server instances
- Containerized deployment with Docker

## Architecture

```
+----------------+      +-----------------+      +----------------+
|                |      |                 |      |                |
|   Client       +----->+  Load Balancer  +---->+  Server 1     |
|                |      |                 |     |  (server1:5001) |
+----------------+      +--------+--------+     +----------------+
                                 |
                                 |                +----------------+
                                 |                |                |
                                 +-------------->+  Server 2     |
                                 |                |  (server2:5002) |
                                 |                |                |
                                 |                +----------------+
                                 |
                                 |                +----------------+
                                 |                |                |
                                 +-------------->+  Server 3     |
                                                |  (server3:5003) |
                                                |                |
                                                +----------------+
```

## API Endpoints

### Load Balancer Endpoints

- `GET /rep` - Get list of all server replicas
- `POST /add` - Add new server instances
- `DELETE /rm` - Remove server instances
- `GET /<path>` - Route request to appropriate server

### Server Endpoints

- `GET /home` - Basic endpoint that returns server information
- `GET /heartbeat` - Health check endpoint

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Running the Application

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd loadbalancer
   ```

2. Build and start the services:
   ```bash
   make build
   make up
   ```

3. The load balancer will be available at `http://localhost:5000`

### Using Makefile

- `make build` - Build all services
- `make up` - Start all services
- `make down` - Stop and remove all containers
- `make restart` - Restart services
- `make logs` - View logs
- `make clean` - Clean up all containers and volumes

## API Examples

### Get Replicas
```bash
curl http://localhost:5000/rep
```

### Add Servers
```bash
curl -X POST http://localhost:5000/add \
  -H "Content-Type: application/json" \
  -d '{"n": 2, "hostnames": ["server4", "server5"]}'
```

### Remove Servers
```bash
curl -X DELETE http://localhost:5000/rm \
  -H "Content-Type: application/json" \
  -d '{"n": 1, "hostnames": ["server1"]}'
```

### Access Server Content
```bash
curl http://localhost:5000/home
```

## Configuration

### Environment Variables

**Load Balancer**
- `NUM_SERVERS`: Number of initial server instances (default: 3)
- `NUM_SLOTS`: Number of slots in consistent hash ring (default: 512)
- `NUM_VIRTUAL_SERVERS`: Number of virtual nodes per server (default: 9)

**Server**
- `SERVER_ID`: Unique identifier for the server
- `PORT`: Port to run the server on (default: 5000)

## Implementation Details

### Consistent Hashing

The load balancer uses consistent hashing with the following parameters:
- Number of slots: 512
- Virtual servers per physical server: 9 (log2(512))
- Hash function for request mapping: H(i) = i² + 2i + 172
- Hash function for virtual server mapping: Φ(i, j) = i + j + 2j + 25

### Health Checks

The load balancer performs health checks every 5 seconds on all server instances. If a server fails to respond, it is automatically removed from the pool.

## Performance Testing

To run the performance tests, execute the following commands:

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Run the performance tests
python -m tests.performance_test
```

### Test Results

#### A-1: Request Distribution with 3 Servers

This test sent 10,000 requests to the load balancer with 3 server instances and measured the distribution of requests.

```
Test A-1 Results (Completed in 27.76 seconds):
Request distribution: {
  "1": 9642,
  "2": 227,
  "3": 70
}
Requests per second: 360.27
```

![Request Distribution](assets/task4/a1_distribution.png)

**Observations:**
- The load is not evenly distributed among the 3 server instances.
- Server 1 handled 96.4% of the requests (9642), while Server 2 and Server 3 handled only 2.3% (227) and 0.7% (70) respectively.
- This indicates an issue with the consistent hashing implementation where most requests are being routed to a single server.
- The low requests per second (360.27) suggests potential performance bottlenecks in the load balancer implementation.

#### A-2: Scalability Test (2-6 Servers)

This test measured the average load per server as the number of servers increased from 2 to 6.

**Test Results:**
- 2 Servers: Average load = 4,991.00 requests/server
- 3 Servers: Average load = 3,317.00 requests/server
- 4 Servers: Average load = 2,492.75 requests/server
- 5 Servers: Average load = 1,988.40 requests/server
- 6 Servers: Average load = 1,660.33 requests/server

![Scalability](assets/task4/a2_scalability.png)

**Observations:**
1. **Ineffective Load Distribution**: The average load doesn't decrease proportionally with the number of servers, indicating that the load balancer isn't distributing requests effectively.
2. **Consistent Issue**: Similar to Test A-1, most requests are being routed to a single server (Server 1), while others remain underutilized.
3. **Scaling Impact**: The system doesn't scale horizontally as expected. Adding more servers doesn't significantly improve load distribution.
4. **Performance Concern**: The consistent hashing implementation needs review as it's not providing the expected distribution of requests across available servers.

#### A-3: Failure Recovery

This test verified the system's behavior when a server fails and a new one is added.

**Test Execution:**
1. **Initial State (6 servers):**
   ```json
   {
     "N": 6,
     "replicas": ["Server_1", "Server_2", "Server_3", "server1", "server2", "server3"]
   }
   ```

2. **After Simulated Failure (5 servers):**
   ```json
   {
     "N": 5,
     "replicas": ["Server_1", "Server_2", "Server_3", "server2", "server3"]
   }
   ```

3. **After Adding New Server (6 servers):**
   ```json
   {
     "N": 6,
     "replicas": ["Server_1", "Server_2", "Server_3", "server2", "server3", "server1"]
   }
   ```

**Observations:**
1. **Server Management**: The system correctly adds and removes servers from the pool.
2. **Naming Inconsistency**: There's an inconsistency in server naming (mixing "Server_X" and "serverX" formats).
3. **State Maintenance**: The system maintains the correct count of servers (N) after each operation.
4. **Recovery Process**: The system successfully handles server removal and addition, though the load distribution issues observed in previous tests would affect the effectiveness of the recovery.

#### A-4: Modified Hash Functions

**Current Implementation Analysis:**
The current implementation shows significant imbalance in request distribution. Let's analyze and improve the hash functions.

**Current Hash Functions (from `consistent_hash.py`):**
```python
def hash_request(self, request_id):
    return (request_id ** 2 + 2 * request_id + 172) % self.num_slots

def hash_virtual_server(self, server_id, replica_id):
    return (server_id + replica_id + 2 * replica_id + 25) % self.num_slots
```

**Issues Identified:**
1. **Poor Distribution**: The current hash functions don't provide a uniform distribution of requests.
2. **Collision Prone**: The functions may generate many collisions.
3. **Ineffective Virtual Server Hashing**: The virtual server hashing doesn't provide good distribution.

**Improved Hash Functions:**
```python
def hash_request(self, request_id):
    # Using a better mixing function with prime numbers
    x = ((request_id >> 16) ^ request_id) * 0x45d9f3b
    x = ((x >> 16) ^ x) * 0x45d9f3b
    x = (x >> 16) ^ x
    return x % self.num_slots

def hash_virtual_server(self, server_id, replica_id):
    # Using FNV-1a hash for better distribution
    hash_val = 2166136261  # FNV offset basis
    prime = 16777619      # FNV prime
    
    # Mix server_id and replica_id
    for byte in f"{server_id}:{replica_id}".encode('utf-8'):
        hash_val = (hash_val ^ byte) * prime
    
    return hash_val % self.num_slots
```

**Recommendations for Improvement:**
1. **Use Established Hash Functions**: Consider using well-known hash functions like MurmurHash or FNV-1a.
2. **Increase Virtual Nodes**: Increase the number of virtual nodes per server (currently 9) for better distribution.
3. **Hash Function Testing**: Test different hash functions to find the best distribution for your workload.
4. **Monitor Distribution**: Add monitoring to track request distribution and detect imbalances.
5. **Consistent Naming**: Standardize server naming conventions (e.g., all lowercase or with consistent capitalization).

**Expected Improvements:**
1. More even distribution of requests across servers.
2. Better utilization of all available servers.
3. More predictable performance as the number of servers changes.
4. Improved handling of server additions and removals.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

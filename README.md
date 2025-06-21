# Distributed Load Balancer with Consistent Hashing

A distributed load balancer implementation using consistent hashing algorithm to distribute load across multiple server containers.

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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

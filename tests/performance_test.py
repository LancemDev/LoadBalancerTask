import asyncio
import aiohttp
import time
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import json

class LoadBalancerTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        if self.session:
            await self.session.close()
    
    async def send_requests(self, endpoint, num_requests):
        results = defaultdict(int)
        url = f"{self.base_url}{endpoint}"
        
        async def make_request():
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'message' in data and 'Server:' in data['message']:
                            server_id = data['message'].split('Server:')[-1].strip()
                            return server_id
            except Exception as e:
                print(f"Request failed: {e}")
            return None
        
        tasks = [make_request() for _ in range(num_requests)]
        server_ids = await asyncio.gather(*tasks)
        
        for server_id in server_ids:
            if server_id:
                results[server_id] += 1
        
        return dict(results)
    
    async def add_servers(self, count):
        url = f"{self.base_url}/add"
        data = {"n": count, "hostnames": [f"server{i}" for i in range(1, count + 1)]}
        async with self.session.post(url, json=data) as response:
            return await response.json()
    
    async def remove_servers(self, count):
        url = f"{self.base_url}/rm"
        data = {"n": count, "hostnames": [f"server{i}" for i in range(1, count + 1)]}
        async with self.session.delete(url, json=data) as response:
            return await response.json()
    
    async def get_replicas(self):
        url = f"{self.base_url}/rep"
        async with self.session.get(url) as response:
            return await response.json()

async def plot_request_distribution(results, title, filename):
    if not results:
        print("No results to plot")
        return
        
    servers = list(results.keys())
    counts = list(results.values())
    
    plt.figure(figsize=(10, 6))
    plt.bar(servers, counts)
    plt.title(title)
    plt.xlabel('Server ID')
    plt.ylabel('Number of Requests')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    print(f"Saved plot to {filename}")

async def test_a1():
    """Test A-1: Launch 10000 requests on 3 servers"""
    async with LoadBalancerTester() as tester:
        # Ensure we have exactly 3 servers
        await tester.remove_servers(10)  # Remove all servers first
        await tester.add_servers(3)
        
        # Send requests
        print("Sending 10000 requests...")
        start_time = time.time()
        results = await tester.send_requests("/home", 10000)
        duration = time.time() - start_time
        
        print(f"\nTest A-1 Results (Completed in {duration:.2f} seconds):")
        print("Request distribution:", json.dumps(results, indent=2))
        print(f"Requests per second: {10000/duration:.2f}")
        
        await plot_request_distribution(
            results, 
            "Request Distribution with 3 Servers (10000 requests)",
            "a1_distribution.png"
        )
        return results

async def test_a2():
    """Test A-2: Test scalability from 2 to 6 servers"""
    results = {}
    
    async with LoadBalancerTester() as tester:
        for n in range(2, 7):  # Test with 2 to 6 servers
            # Reset to N servers
            await tester.remove_servers(10)  # Remove all servers first
            await tester.add_servers(n)
            
            # Wait for servers to be ready
            await asyncio.sleep(2)
            
            # Send requests
            print(f"\nTesting with {n} servers...")
            distribution = await tester.send_requests("/home", 10000)
            
            # Calculate metrics
            total_requests = sum(distribution.values())
            avg_load = total_requests / n
            results[n] = avg_load
            
            print(f"N={n}, Average load: {avg_load:.2f}")
            print("Distribution:", json.dumps(distribution, indent=2))
    
    # Plot scalability results
    if results:
        plt.figure(figsize=(10, 6))
        plt.plot(list(results.keys()), list(results.values()), marker='o')
        plt.title('Average Load vs Number of Servers')
        plt.xlabel('Number of Servers (N)')
        plt.ylabel('Average Requests per Server (10000 total requests)')
        plt.grid(True)
        plt.xticks(range(2, 7))
        plt.tight_layout()
        plt.savefig('a2_scalability.png')
        plt.close()
        print("\nSaved scalability plot to a2_scalability.png")
    
    return results

async def test_a3():
    """Test A-3: Failure recovery"""
    print("\nTest A-3: Failure Recovery")
    async with LoadBalancerTester() as tester:
        # Start with 3 servers
        await tester.remove_servers(10)
        await tester.add_servers(3)
        
        # Get initial state
        initial = await tester.get_replicas()
        print("Initial servers:", json.dumps(initial, indent=2))
        
        # Simulate server failure (remove one server)
        print("\nSimulating server failure...")
        await tester.remove_servers(1)
        
        # Check if load balancer detects the failure
        after_failure = await tester.get_replicas()
        print("After failure:", json.dumps(after_failure, indent=2))
        
        # Add a new server
        print("\nAdding new server...")
        await tester.add_servers(1)
        
        # Check final state
        final = await tester.get_replicas()
        print("Final servers:", json.dumps(final, indent=2))
        
        return {"initial": initial, "after_failure": after_failure, "final": final}

async def main():
    print("Starting Load Balancer Performance Tests")
    print("=" * 50)
    
    # Install required packages if not already installed
    try:
        import aiohttp
        import matplotlib
    except ImportError:
        print("Installing required packages...")
        import sys
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp", "matplotlib"])
    
    # Run tests
    print("\n" + "="*50)
    print("TEST A-1: Request Distribution with 3 Servers")
    print("="*50)
    await test_a1()
    
    print("\n" + "="*50)
    print("TEST A-2: Scalability Test (2-6 Servers)")
    print("="*50)
    await test_a2()
    
    print("\n" + "="*50)
    print("TEST A-3: Failure Recovery")
    print("="*50)
    await test_a3()
    
    print("\nTests completed. Check the generated plots for results.")

if __name__ == "__main__":
    asyncio.run(main())

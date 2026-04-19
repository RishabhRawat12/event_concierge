import asyncio
import time
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Benchmark")

async def benchmark_endpoint(url: str, payload: dict, concurrent_requests: int = 10):
    """Measures latency and throughput for a specific endpoint."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        start_time = time.perf_counter()
        
        tasks = []
        for _ in range(concurrent_requests):
            tasks.append(client.post(url, json=payload))
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.perf_counter()
        
        latencies = []
        success_count = 0
        for resp in responses:
            if isinstance(resp, httpx.Response) and resp.status_code == 200:
                success_count += 1
                latencies.append(resp.elapsed.total_seconds())
        
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        total_duration = end_time - start_time
        req_per_sec = concurrent_requests / total_duration
        
        print(f"\n--- Benchmark Results for {url.split('/')[-1]} ---")
        print(f"Concurrent Requests: {concurrent_requests}")
        print(f"Success Rate: {(success_count/concurrent_requests)*100:.1f}%")
        print(f"Average Latency: {avg_latency*1000:.2f}ms")
        print(f"Throughput: {req_per_sec:.2f} req/sec")
        print(f"Total Duration: {total_duration:.2f}s")

async def main():
    base_url = "http://localhost:8000"
    itinerary_payload = {
        "user_location": {"latitude": 37.7, "longitude": -122.4},
        "start_time": "10:00 AM",
        "end_time": "11:00 AM",
        "preferred_topics": ["AI"]
    }
    
    print("Starting performance benchmarks...")
    # Benchmarking the itinerary synthesis (hits AI or cache)
    await benchmark_endpoint(f"{base_url}/api/itinerary", itinerary_payload, 5)
    
    # Benchmarking a lighter endpoint if exists, but we focus on the core logic
    print("\nBenchmark complete.")

if __name__ == "__main__":
    asyncio.run(main())

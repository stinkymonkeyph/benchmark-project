import asyncio
import aiohttp
import time
import statistics
import json
from typing import List
import argparse
from dataclasses import dataclass


@dataclass
class BenchmarkResult:
    endpoint: str
    method: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    median_response_time: float
    p95_response_time: float
    requests_per_second: float
    total_time: float


class FastAPIBenchmark:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[BenchmarkResult] = []

    async def make_request(
        self, session: aiohttp.ClientSession, method: str, url: str, data: dict = None
    ) -> tuple:
        """Make a single HTTP request and return response time and status"""
        start_time = time.time()
        try:
            if method.upper() == "GET":
                async with session.get(url) as response:
                    await response.text()
                    return time.time() - start_time, response.status
            elif method.upper() == "POST":
                async with session.post(url, json=data) as response:
                    await response.text()
                    return time.time() - start_time, response.status
            elif method.upper() == "PUT":
                async with session.put(url, json=data) as response:
                    await response.text()
                    return time.time() - start_time, response.status
            elif method.upper() == "DELETE":
                async with session.delete(url) as response:
                    await response.text()
                    return time.time() - start_time, response.status
        except Exception as e:
            return time.time() - start_time, 0

    async def benchmark_endpoint(
        self,
        endpoint: str,
        method: str,
        num_requests: int,
        concurrent_requests: int = 10,
        data: dict = None,
    ) -> BenchmarkResult:
        """Benchmark a single endpoint"""
        print(
            f"Benchmarking {method} {endpoint} with {num_requests} requests ({concurrent_requests} concurrent)"
        )

        url = f"{self.base_url}{endpoint}"
        response_times = []
        status_codes = []

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(concurrent_requests)

        async def limited_request(session):
            async with semaphore:
                return await self.make_request(session, method, url, data)

        start_time = time.time()

        # Create session and make requests
        async with aiohttp.ClientSession() as session:
            tasks = [limited_request(session) for _ in range(num_requests)]
            results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        # Process results
        for response_time, status_code in results:
            response_times.append(response_time)
            status_codes.append(status_code)

        successful_requests = len([s for s in status_codes if 200 <= s < 300])
        failed_requests = num_requests - successful_requests

        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        median_response_time = statistics.median(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[
            18
        ]  # 95th percentile
        requests_per_second = num_requests / total_time

        result = BenchmarkResult(
            endpoint=endpoint,
            method=method,
            total_requests=num_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time * 1000,  # Convert to ms
            min_response_time=min_response_time * 1000,
            max_response_time=max_response_time * 1000,
            median_response_time=median_response_time * 1000,
            p95_response_time=p95_response_time * 1000,
            requests_per_second=requests_per_second,
            total_time=total_time,
        )

        self.results.append(result)
        return result

    async def run_comprehensive_benchmark(
        self, num_requests: int = 1000, concurrent_requests: int = 50
    ):
        """Run comprehensive benchmark on all endpoints"""
        print("=== FastAPI Comprehensive Benchmark ===\n")

        # Test basic endpoints
        await self.benchmark_endpoint("/", "GET", num_requests, concurrent_requests)
        await self.benchmark_endpoint(
            "/health", "GET", num_requests, concurrent_requests
        )

        # Test echo endpoints
        echo_data = {
            "message": "Hello benchmark",
            "data": {"test": "data", "number": 42},
        }
        await self.benchmark_endpoint(
            "/echo", "POST", num_requests, concurrent_requests, echo_data
        )
        await self.benchmark_endpoint(
            "/echo/benchmark-test", "GET", num_requests, concurrent_requests
        )

        # Test database operations
        await self.benchmark_endpoint(
            "/db/items", "GET", num_requests, concurrent_requests
        )
        await self.benchmark_endpoint(
            "/db/items/1", "GET", num_requests, concurrent_requests
        )

        # Test database writes (fewer requests to avoid database bloat)
        write_requests = min(num_requests // 10, 100)
        item_data = {
            "name": "Benchmark Item",
            "description": "Item created during benchmarking",
            "price": 99.99,
        }
        await self.benchmark_endpoint(
            "/db/items", "POST", write_requests, min(concurrent_requests, 10), item_data
        )

        # Test CPU stress endpoint
        await self.benchmark_endpoint(
            "/stress/cpu/1000", "GET", num_requests // 5, concurrent_requests // 2
        )

        # Test memory stress endpoint
        await self.benchmark_endpoint(
            "/stress/memory/1", "GET", num_requests // 10, concurrent_requests // 5
        )

    def print_results(self):
        """Print benchmark results in a formatted table"""
        print("\n=== BENCHMARK RESULTS ===\n")

        # Header
        header = f"{'Endpoint':<30} {'Method':<8} {'Req/s':<10} {'Avg(ms)':<10} {'Min(ms)':<10} {'Max(ms)':<10} {'P95(ms)':<10} {'Success':<10}"
        print(header)
        print("=" * len(header))

        # Results
        for result in self.results:
            row = f"{result.endpoint:<30} {result.method:<8} {result.requests_per_second:<10.1f} {result.avg_response_time:<10.2f} {result.min_response_time:<10.2f} {result.max_response_time:<10.2f} {result.p95_response_time:<10.2f} {result.successful_requests}/{result.total_requests:<10}"
            print(row)

        print("\n=== SUMMARY ===")
        total_requests = sum(r.total_requests for r in self.results)
        total_successful = sum(r.successful_requests for r in self.results)
        avg_rps = statistics.mean([r.requests_per_second for r in self.results])
        avg_response_time = statistics.mean([r.avg_response_time for r in self.results])

        print(f"Total Requests: {total_requests}")
        print(f"Successful Requests: {total_successful}")
        print(f"Success Rate: {(total_successful / total_requests) * 100:.2f}%")
        print(f"Average RPS: {avg_rps:.1f}")
        print(f"Average Response Time: {avg_response_time:.2f}ms")

    def save_results_json(self, filename: str = "benchmark_results.json"):
        """Save results to JSON file"""
        results_dict = []
        for result in self.results:
            results_dict.append(
                {
                    "endpoint": result.endpoint,
                    "method": result.method,
                    "total_requests": result.total_requests,
                    "successful_requests": result.successful_requests,
                    "failed_requests": result.failed_requests,
                    "avg_response_time_ms": result.avg_response_time,
                    "min_response_time_ms": result.min_response_time,
                    "max_response_time_ms": result.max_response_time,
                    "median_response_time_ms": result.median_response_time,
                    "p95_response_time_ms": result.p95_response_time,
                    "requests_per_second": result.requests_per_second,
                    "total_time_seconds": result.total_time,
                }
            )

        with open(filename, "w") as f:
            json.dump(results_dict, f, indent=2)
        print(f"\nResults saved to {filename}")


async def main():
    parser = argparse.ArgumentParser(description="FastAPI Benchmark Tool")
    parser.add_argument(
        "--url", default="http://localhost:8000", help="Base URL of FastAPI server"
    )
    parser.add_argument(
        "--requests", type=int, default=1000, help="Number of requests per endpoint"
    )
    parser.add_argument(
        "--concurrent", type=int, default=50, help="Number of concurrent requests"
    )
    parser.add_argument(
        "--output", default="benchmark_results.json", help="Output JSON file"
    )

    args = parser.parse_args()

    benchmark = FastAPIBenchmark(args.url)

    try:
        await benchmark.run_comprehensive_benchmark(args.requests, args.concurrent)
        benchmark.print_results()
        benchmark.save_results_json(args.output)
    except Exception as e:
        print(f"Benchmark failed: {e}")
        print("Make sure your FastAPI server is running!")


if __name__ == "__main__":
    asyncio.run(main())

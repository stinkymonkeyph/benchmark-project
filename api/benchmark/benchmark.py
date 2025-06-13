import asyncio
import aiohttp
import time
import statistics
import json
from typing import List
import argparse
from dataclasses import dataclass
from datetime import datetime


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


@dataclass
class ComparisonResult:
    endpoint: str
    method: str
    fastapi_rps: float
    rust_rps: float
    fastapi_avg_ms: float
    rust_avg_ms: float
    performance_ratio: float
    latency_ratio: float


class ComparativeBenchmark:
    def __init__(
        self,
        fastapi_url: str = "http://localhost:8000",
        rust_url: str = "http://localhost:3000",
    ):
        self.fastapi_url = fastapi_url
        self.rust_url = rust_url
        self.fastapi_results: List[BenchmarkResult] = []
        self.rust_results: List[BenchmarkResult] = []
        self.comparison_results: List[ComparisonResult] = []

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
        base_url: str,
        endpoint: str,
        method: str,
        num_requests: int,
        concurrent_requests: int = 10,
        data: dict = None,
    ) -> BenchmarkResult:
        """Benchmark a single endpoint"""
        print(
            f"Benchmarking {base_url}{endpoint} ({method}) - {num_requests} requests, {concurrent_requests} concurrent"
        )

        url = f"{base_url}{endpoint}"
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

        if not response_times:
            return BenchmarkResult(
                endpoint,
                method,
                num_requests,
                0,
                num_requests,
                0,
                0,
                0,
                0,
                0,
                0,
                total_time,
            )

        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        median_response_time = statistics.median(response_times)

        # Handle edge case for p95 calculation
        if len(response_times) > 1:
            p95_response_time = statistics.quantiles(response_times, n=20)[
                18
            ]  # 95th percentile
        else:
            p95_response_time = response_times[0]

        requests_per_second = num_requests / total_time if total_time > 0 else 0

        return BenchmarkResult(
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

    async def run_server_health_check(self, base_url: str, server_name: str) -> bool:
        """Check if server is running"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{base_url}/health", timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        print(f"✅ {server_name} server is running at {base_url}")
                        return True
        except:
            pass

        print(f"❌ {server_name} server is not responding at {base_url}")
        return False

    async def run_comparative_benchmark(
        self, num_requests: int = 1000, concurrent_requests: int = 50
    ):
        """Run comparative benchmark between FastAPI and Rust Axum"""
        print("🚀 Starting Comparative Benchmark: FastAPI vs Rust Axum\n")
        print("=" * 60)

        # Health checks
        fastapi_healthy = await self.run_server_health_check(
            self.fastapi_url, "FastAPI"
        )
        rust_healthy = await self.run_server_health_check(self.rust_url, "Rust Axum")

        if not fastapi_healthy or not rust_healthy:
            print(
                "\n❌ One or more servers are not running. Please start both servers and try again."
            )
            return

        print("\n🔥 Both servers are ready! Starting benchmark...\n")

        # Define test endpoints for comparison
        test_endpoints = [
            ("/", "GET", None, "Root endpoint"),
            ("/health", "GET", None, "Health check"),
            (
                "/echo",
                "POST",
                {"message": "benchmark test", "data": {"number": 42}},
                "Echo POST",
            ),
            ("/echo/test", "GET", None, "Echo GET"),
            ("/db/items", "GET", None, "Database read"),
            ("/stress/cpu/1000", "GET", None, "CPU stress test"),
        ]

        for endpoint, method, data, description in test_endpoints:
            print(f"\n📊 Testing: {description}")
            print("-" * 40)

            # Test FastAPI
            fastapi_result = await self.benchmark_endpoint(
                self.fastapi_url,
                endpoint,
                method,
                num_requests,
                concurrent_requests,
                data,
            )
            self.fastapi_results.append(fastapi_result)

            # Test Rust Axum
            rust_result = await self.benchmark_endpoint(
                self.rust_url, endpoint, method, num_requests, concurrent_requests, data
            )
            self.rust_results.append(rust_result)

            # Calculate comparison metrics
            if (
                fastapi_result.requests_per_second > 0
                and rust_result.requests_per_second > 0
            ):
                performance_ratio = (
                    rust_result.requests_per_second / fastapi_result.requests_per_second
                )
                latency_ratio = (
                    fastapi_result.avg_response_time / rust_result.avg_response_time
                    if rust_result.avg_response_time > 0
                    else 0
                )

                comparison = ComparisonResult(
                    endpoint=endpoint,
                    method=method,
                    fastapi_rps=fastapi_result.requests_per_second,
                    rust_rps=rust_result.requests_per_second,
                    fastapi_avg_ms=fastapi_result.avg_response_time,
                    rust_avg_ms=rust_result.avg_response_time,
                    performance_ratio=performance_ratio,
                    latency_ratio=latency_ratio,
                )
                self.comparison_results.append(comparison)

    def print_detailed_results(self):
        """Print detailed results for both servers"""
        print("\n" + "=" * 80)
        print("📈 DETAILED BENCHMARK RESULTS")
        print("=" * 80)

        # FastAPI Results
        print("\n🐍 FASTAPI RESULTS")
        print("-" * 50)
        self._print_server_results(self.fastapi_results)

        # Rust Results
        print("\n🦀 RUST AXUM RESULTS")
        print("-" * 50)
        self._print_server_results(self.rust_results)

    def _print_server_results(self, results: List[BenchmarkResult]):
        """Print results for a single server"""
        header = f"{'Endpoint':<20} {'Method':<8} {'RPS':<10} {'Avg(ms)':<10} {'P95(ms)':<10} {'Success':<10}"
        print(header)
        print("-" * len(header))

        for result in results:
            success_rate = f"{result.successful_requests}/{result.total_requests}"
            print(
                f"{result.endpoint:<20} {result.method:<8} {result.requests_per_second:<10.1f} "
                f"{result.avg_response_time:<10.2f} {result.p95_response_time:<10.2f} {success_rate:<10}"
            )

    def print_comparison_summary(self):
        """Print a clear comparison summary"""
        print("\n" + "=" * 80)
        print("🏆 PERFORMANCE COMPARISON SUMMARY")
        print("=" * 80)

        if not self.comparison_results:
            print("No comparison data available.")
            return

        # Comparison table
        print(
            f"\n{'Endpoint':<20} {'FastAPI RPS':<12} {'Rust RPS':<12} {'Rust Advantage':<15} {'Latency Advantage':<18}"
        )
        print("-" * 85)

        total_fastapi_rps = 0
        total_rust_rps = 0
        rust_wins = 0

        for comp in self.comparison_results:
            total_fastapi_rps += comp.fastapi_rps
            total_rust_rps += comp.rust_rps

            if comp.performance_ratio > 1:
                rust_wins += 1
                perf_indicator = f"{comp.performance_ratio:.1f}x faster"
            else:
                perf_indicator = f"{1 / comp.performance_ratio:.1f}x slower"

            if comp.latency_ratio > 1:
                latency_indicator = f"{comp.latency_ratio:.1f}x lower latency"
            else:
                latency_indicator = f"{1 / comp.latency_ratio:.1f}x higher latency"

            print(
                f"{comp.endpoint:<20} {comp.fastapi_rps:<12.1f} {comp.rust_rps:<12.1f} "
                f"{perf_indicator:<15} {latency_indicator:<18}"
            )

        # Overall summary
        print("\n" + "=" * 80)
        print("📊 OVERALL PERFORMANCE SUMMARY")
        print("=" * 80)

        avg_fastapi_rps = total_fastapi_rps / len(self.comparison_results)
        avg_rust_rps = total_rust_rps / len(self.comparison_results)
        overall_advantage = avg_rust_rps / avg_fastapi_rps

        fastapi_avg_latency = statistics.mean(
            [c.fastapi_avg_ms for c in self.comparison_results]
        )
        rust_avg_latency = statistics.mean(
            [c.rust_avg_ms for c in self.comparison_results]
        )
        latency_advantage = fastapi_avg_latency / rust_avg_latency

        print(f"🐍 FastAPI Average RPS: {avg_fastapi_rps:.1f}")
        print(f"🦀 Rust Axum Average RPS: {avg_rust_rps:.1f}")
        print(f"🚀 Rust Performance Advantage: {overall_advantage:.1f}x faster")
        print(f"⚡ Rust Latency Advantage: {latency_advantage:.1f}x lower latency")
        print(f"🏁 Rust wins in {rust_wins}/{len(self.comparison_results)} endpoints")

        # Performance categories
        print(f"\n📈 PERFORMANCE BREAKDOWN:")
        if overall_advantage > 2:
            print("🔥 Rust shows SIGNIFICANT performance advantage")
        elif overall_advantage > 1.5:
            print("✨ Rust shows NOTABLE performance advantage")
        elif overall_advantage > 1.1:
            print("📈 Rust shows MODERATE performance advantage")
        else:
            print("🤝 Performance is COMPARABLE between both frameworks")

        print(f"\n⏱️  LATENCY BREAKDOWN:")
        if latency_advantage > 2:
            print("🚄 Rust has SIGNIFICANTLY lower latency")
        elif latency_advantage > 1.5:
            print("⚡ Rust has NOTABLY lower latency")
        elif latency_advantage > 1.1:
            print("📉 Rust has MODERATELY lower latency")
        else:
            print("⚖️  Latency is COMPARABLE between both frameworks")

    def save_comparison_results(self, filename: str = "comparison_results.json"):
        """Save comparison results to JSON"""
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "fastapi_results": [
                {
                    "endpoint": r.endpoint,
                    "method": r.method,
                    "requests_per_second": r.requests_per_second,
                    "avg_response_time_ms": r.avg_response_time,
                    "p95_response_time_ms": r.p95_response_time,
                    "success_rate": r.successful_requests / r.total_requests
                    if r.total_requests > 0
                    else 0,
                }
                for r in self.fastapi_results
            ],
            "rust_results": [
                {
                    "endpoint": r.endpoint,
                    "method": r.method,
                    "requests_per_second": r.requests_per_second,
                    "avg_response_time_ms": r.avg_response_time,
                    "p95_response_time_ms": r.p95_response_time,
                    "success_rate": r.successful_requests / r.total_requests
                    if r.total_requests > 0
                    else 0,
                }
                for r in self.rust_results
            ],
            "comparisons": [
                {
                    "endpoint": c.endpoint,
                    "method": c.method,
                    "fastapi_rps": c.fastapi_rps,
                    "rust_rps": c.rust_rps,
                    "performance_ratio": c.performance_ratio,
                    "latency_ratio": c.latency_ratio,
                }
                for c in self.comparison_results
            ],
        }

        with open(filename, "w") as f:
            json.dump(results_data, f, indent=2)
        print(f"\n💾 Comparison results saved to {filename}")

    def create_performance_chart(self, filename: str = "performance_comparison.png"):
        """Create a visual comparison chart"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np

            if not self.comparison_results:
                print("No data available for chart generation.")
                return

            endpoints = [c.endpoint for c in self.comparison_results]
            fastapi_rps = [c.fastapi_rps for c in self.comparison_results]
            rust_rps = [c.rust_rps for c in self.comparison_results]

            x = np.arange(len(endpoints))
            width = 0.35

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

            # RPS Comparison
            ax1.bar(
                x - width / 2,
                fastapi_rps,
                width,
                label="FastAPI",
                color="#3776ab",
                alpha=0.8,
            )
            ax1.bar(
                x + width / 2,
                rust_rps,
                width,
                label="Rust Axum",
                color="#dea584",
                alpha=0.8,
            )
            ax1.set_xlabel("Endpoints")
            ax1.set_ylabel("Requests per Second")
            ax1.set_title("Performance Comparison: Requests per Second")
            ax1.set_xticks(x)
            ax1.set_xticklabels(endpoints, rotation=45, ha="right")
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # Latency Comparison
            fastapi_latency = [c.fastapi_avg_ms for c in self.comparison_results]
            rust_latency = [c.rust_avg_ms for c in self.comparison_results]

            ax2.bar(
                x - width / 2,
                fastapi_latency,
                width,
                label="FastAPI",
                color="#3776ab",
                alpha=0.8,
            )
            ax2.bar(
                x + width / 2,
                rust_latency,
                width,
                label="Rust Axum",
                color="#dea584",
                alpha=0.8,
            )
            ax2.set_xlabel("Endpoints")
            ax2.set_ylabel("Average Response Time (ms)")
            ax2.set_title("Latency Comparison: Average Response Time")
            ax2.set_xticks(x)
            ax2.set_xticklabels(endpoints, rotation=45, ha="right")
            ax2.legend()
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.savefig(filename, dpi=300, bbox_inches="tight")
            print(f"📊 Performance chart saved to {filename}")

        except ImportError:
            print(
                "📊 Matplotlib not available. Install it with: pip install matplotlib"
            )
        except Exception as e:
            print(f"Error creating chart: {e}")


async def main():
    parser = argparse.ArgumentParser(
        description="FastAPI vs Rust Axum Comparative Benchmark"
    )
    parser.add_argument(
        "--fastapi-url",
        default="http://localhost:8000",
        help="FastAPI server URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--rust-url",
        default="http://localhost:3000",
        help="Rust Axum server URL (default: http://localhost:3000)",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=1000,
        help="Number of requests per endpoint (default: 1000)",
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=50,
        help="Number of concurrent requests (default: 50)",
    )
    parser.add_argument(
        "--output",
        default="comparison_results.json",
        help="Output JSON file (default: comparison_results.json)",
    )
    parser.add_argument(
        "--chart",
        default="performance_comparison.png",
        help="Output chart file (default: performance_comparison.png)",
    )

    args = parser.parse_args()

    benchmark = ComparativeBenchmark(args.fastapi_url, args.rust_url)

    try:
        await benchmark.run_comparative_benchmark(args.requests, args.concurrent)
        benchmark.print_detailed_results()
        benchmark.print_comparison_summary()
        benchmark.save_comparison_results(args.output)
        benchmark.create_performance_chart(args.chart)

        print("\n🎉 Benchmark completed successfully!")
        print(f"📄 Detailed results: {args.output}")
        print(f"📊 Performance chart: {args.chart}")

    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure both FastAPI and Rust servers are running")
        print("2. Check that the URLs are correct")
        print("3. Ensure both servers have the required endpoints")


if __name__ == "__main__":
    asyncio.run(main())


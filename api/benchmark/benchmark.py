import asyncio
import aiohttp
import time
import statistics
import json
from typing import List, Dict
import argparse
from dataclasses import dataclass
from datetime import datetime
import random


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
    nodejs_rps: float
    fastapi_avg_ms: float
    rust_avg_ms: float
    nodejs_avg_ms: float


class CRUDBenchmark:
    def __init__(
        self,
        fastapi_url: str = "http://localhost:8000",
        rust_url: str = "http://localhost:3000",
        nodejs_url: str = "http://localhost:4000",
    ):
        self.fastapi_url = fastapi_url
        self.rust_url = rust_url
        self.nodejs_url = nodejs_url
        self.fastapi_results: List[BenchmarkResult] = []
        self.rust_results: List[BenchmarkResult] = []
        self.nodejs_results: List[BenchmarkResult] = []
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

    async def cleanup_databases(self, fastapi_healthy, rust_healthy, nodejs_healthy):
        """Clean up databases after benchmark to ensure consistent state"""
        print("\n🧹 CLEANUP: Resetting databases to initial state...")
        print("=" * 60)

        cleanup_tasks = []

        # Clean FastAPI database
        if fastapi_healthy:
            cleanup_tasks.append(
                self._cleanup_server_database(self.fastapi_url, "FastAPI")
            )

        # Clean Rust database
        if rust_healthy:
            cleanup_tasks.append(self._cleanup_server_database(self.rust_url, "Rust"))

        # Clean Node.js database
        if nodejs_healthy:
            cleanup_tasks.append(
                self._cleanup_server_database(self.nodejs_url, "Node.js")
            )

        # Run cleanup in parallel
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            print("✅ Database cleanup completed")
        else:
            print("⚠️ No databases to clean")

    async def _cleanup_server_database(self, base_url: str, server_name: str):
        """Clean up database for a specific server"""
        try:
            async with aiohttp.ClientSession() as session:
                # Delete all items except the original sample data (IDs 1, 2, 3)
                # First, get all items to see what we have
                async with session.get(f"{base_url}/db/items") as response:
                    if response.status == 200:
                        items = await response.json()
                        items_to_delete = [
                            item["id"] for item in items if item["id"] > 3
                        ]

                        print(
                            f"🗑️ {server_name}: Deleting {len(items_to_delete)} benchmark items..."
                        )

                        # Delete items in batches to avoid overwhelming the server
                        for item_id in items_to_delete[
                            :50
                        ]:  # Limit to avoid too many requests
                            try:
                                async with session.delete(
                                    f"{base_url}/db/items/{item_id}"
                                ) as del_response:
                                    pass  # Don't need to process response
                            except:
                                pass  # Continue even if some deletions fail

                        print(f"✅ {server_name}: Database cleanup completed")
                    else:
                        print(f"⚠️ {server_name}: Could not access database for cleanup")
        except Exception as e:
            print(f"❌ {server_name}: Cleanup failed - {e}")

    async def run_crud_benchmark(
        self, num_requests: int = 1000, concurrent_requests: int = 50
    ):
        """Run comprehensive CRUD benchmark with cleanup"""
        print(
            "🚀 Starting Comprehensive CRUD Benchmark: FastAPI vs Rust Axum vs Node.js TypeScript\n"
        )
        print("=" * 90)

        # Health checks
        fastapi_healthy = await self.run_server_health_check(
            self.fastapi_url, "FastAPI"
        )
        rust_healthy = await self.run_server_health_check(self.rust_url, "Rust Axum")
        nodejs_healthy = await self.run_server_health_check(
            self.nodejs_url, "Node.js TypeScript"
        )

        running_servers = sum([fastapi_healthy, rust_healthy, nodejs_healthy])
        if running_servers == 0:
            print(
                "\n❌ No servers are running. Please start at least one server and try again."
            )
            return
        elif running_servers < 3:
            print(
                f"\n⚠️ Only {running_servers}/3 servers are running. Continuing with available servers..."
            )

        print("\n🔥 Starting comprehensive CRUD benchmark...\n")

        try:
            # Phase 1: Basic endpoints
            basic_endpoints = [
                ("/", "GET", None, "Root endpoint"),
                ("/health", "GET", None, "Health check"),
                (
                    "/echo",
                    "POST",
                    {"message": "benchmark test", "data": {"number": 42}},
                    "Echo POST",
                ),
                ("/echo/test", "GET", None, "Echo GET"),
            ]

            print("📋 PHASE 1: Basic Endpoints")
            print("=" * 50)
            await self._run_endpoint_tests(
                basic_endpoints,
                num_requests,
                concurrent_requests,
                fastapi_healthy,
                rust_healthy,
                nodejs_healthy,
            )

            # Phase 2: Database READ operations
            read_endpoints = [
                ("/db/items", "GET", None, "Database READ all (SELECT *)"),
                ("/db/items/1", "GET", None, "Database READ single (SELECT WHERE)"),
            ]

            print("\n📖 PHASE 2: Database READ Operations")
            print("=" * 50)
            await self._run_endpoint_tests(
                read_endpoints,
                num_requests,
                concurrent_requests,
                fastapi_healthy,
                rust_healthy,
                nodejs_healthy,
            )

            # Phase 3: Database CREATE operations
            create_requests = min(num_requests // 2, 500)  # Moderate number of creates
            create_endpoints = [
                (
                    "/db/items",
                    "POST",
                    {
                        "name": "Benchmark Item",
                        "description": "Created during benchmark",
                        "price": 99.99,
                    },
                    "Database CREATE (INSERT)",
                ),
            ]

            print(
                f"\n📝 PHASE 3: Database CREATE Operations ({create_requests} requests)"
            )
            print("=" * 50)
            await self._run_endpoint_tests(
                create_endpoints,
                create_requests,
                min(concurrent_requests, 25),
                fastapi_healthy,
                rust_healthy,
                nodejs_healthy,
            )

            # Phase 4: Database UPDATE operations
            update_requests = min(num_requests // 4, 250)  # Fewer updates
            print(
                f"\n✏️ PHASE 4: Database UPDATE Operations ({update_requests} requests)"
            )
            print("=" * 50)

            update_data = {
                "name": "Updated Item",
                "description": "Updated during benchmark",
                "price": 149.99,
            }

            # Test UPDATE on item ID 1 (should exist from sample data)
            await self._test_crud_operation(
                "UPDATE",
                "/db/items/1",
                "PUT",
                update_data,
                update_requests,
                min(concurrent_requests, 20),
                fastapi_healthy,
                rust_healthy,
                nodejs_healthy,
            )

            # Phase 5: Database DELETE operations
            delete_requests = min(num_requests // 10, 100)  # Very few deletes
            print(
                f"\n🗑️ PHASE 5: Database DELETE Operations ({delete_requests} requests)"
            )
            print("=" * 50)

            # Test DELETE on items that likely exist (sample data items)
            await self._test_crud_operation(
                "DELETE",
                "/db/items/2",
                "DELETE",
                None,
                delete_requests,
                min(concurrent_requests, 10),
                fastapi_healthy,
                rust_healthy,
                nodejs_healthy,
            )

            # Phase 6: Stress tests
            stress_endpoints = [
                ("/stress/cpu/1000", "GET", None, "CPU stress test"),
                ("/stress/memory/1", "GET", None, "Memory stress test"),
            ]

            print(f"\n💪 PHASE 6: Stress Tests")
            print("=" * 50)
            await self._run_endpoint_tests(
                stress_endpoints,
                num_requests // 2,
                concurrent_requests // 2,
                fastapi_healthy,
                rust_healthy,
                nodejs_healthy,
            )

        finally:
            # Always clean up databases, even if benchmark fails
            await self.cleanup_databases(fastapi_healthy, rust_healthy, nodejs_healthy)

    async def _run_endpoint_tests(
        self,
        endpoints,
        num_requests,
        concurrent_requests,
        fastapi_healthy,
        rust_healthy,
        nodejs_healthy,
    ):
        """Helper method to run tests on a list of endpoints"""
        for endpoint, method, data, description in endpoints:
            print(f"\n📊 Testing: {description}")
            print("-" * 60)

            results = {}

            # Test all available servers
            if fastapi_healthy:
                result = await self.benchmark_endpoint(
                    self.fastapi_url,
                    endpoint,
                    method,
                    num_requests,
                    concurrent_requests,
                    data,
                )
                self.fastapi_results.append(result)
                results["fastapi"] = result

            if rust_healthy:
                result = await self.benchmark_endpoint(
                    self.rust_url,
                    endpoint,
                    method,
                    num_requests,
                    concurrent_requests,
                    data,
                )
                self.rust_results.append(result)
                results["rust"] = result

            if nodejs_healthy:
                result = await self.benchmark_endpoint(
                    self.nodejs_url,
                    endpoint,
                    method,
                    num_requests,
                    concurrent_requests,
                    data,
                )
                self.nodejs_results.append(result)
                results["nodejs"] = result

            # Create comparison
            if len(results) >= 2:
                self._add_comparison(endpoint, method, results)

    async def _test_crud_operation(
        self,
        operation_name,
        endpoint,
        method,
        data,
        num_requests,
        concurrent_requests,
        fastapi_healthy,
        rust_healthy,
        nodejs_healthy,
    ):
        """Helper method to test CRUD operations"""
        print(f"\n📊 Testing: Database {operation_name}")
        print("-" * 60)

        results = {}

        if fastapi_healthy:
            result = await self.benchmark_endpoint(
                self.fastapi_url,
                endpoint,
                method,
                num_requests,
                concurrent_requests,
                data,
            )
            self.fastapi_results.append(result)
            results["fastapi"] = result

        if rust_healthy:
            result = await self.benchmark_endpoint(
                self.rust_url, endpoint, method, num_requests, concurrent_requests, data
            )
            self.rust_results.append(result)
            results["rust"] = result

        if nodejs_healthy:
            result = await self.benchmark_endpoint(
                self.nodejs_url,
                endpoint,
                method,
                num_requests,
                concurrent_requests,
                data,
            )
            self.nodejs_results.append(result)
            results["nodejs"] = result

        # Create comparison
        if len(results) >= 2:
            self._add_comparison(endpoint, method, results)

    def _add_comparison(self, endpoint, method, results):
        """Helper method to add comparison results"""
        comparison = ComparisonResult(
            endpoint=endpoint,
            method=method,
            fastapi_rps=results.get(
                "fastapi", BenchmarkResult("", "", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            ).requests_per_second,
            rust_rps=results.get(
                "rust", BenchmarkResult("", "", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            ).requests_per_second,
            nodejs_rps=results.get(
                "nodejs", BenchmarkResult("", "", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            ).requests_per_second,
            fastapi_avg_ms=results.get(
                "fastapi", BenchmarkResult("", "", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            ).avg_response_time,
            rust_avg_ms=results.get(
                "rust", BenchmarkResult("", "", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            ).avg_response_time,
            nodejs_avg_ms=results.get(
                "nodejs", BenchmarkResult("", "", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            ).avg_response_time,
        )
        self.comparison_results.append(comparison)

    def print_detailed_results(self):
        """Print detailed results for all servers"""
        print("\n" + "=" * 100)
        print("📈 COMPREHENSIVE CRUD BENCHMARK RESULTS")
        print("=" * 100)

        if self.fastapi_results:
            print("\n🐍 FASTAPI RESULTS")
            print("-" * 70)
            self._print_server_results(self.fastapi_results)

        if self.rust_results:
            print("\n🦀 RUST AXUM RESULTS")
            print("-" * 70)
            self._print_server_results(self.rust_results)

        if self.nodejs_results:
            print("\n🟢 NODE.JS TYPESCRIPT RESULTS")
            print("-" * 70)
            self._print_server_results(self.nodejs_results)

    def _print_server_results(self, results: List[BenchmarkResult]):
        """Print results for a single server"""
        header = f"{'Endpoint':<25} {'Method':<8} {'RPS':<10} {'Avg(ms)':<10} {'P95(ms)':<10} {'Success':<10}"
        print(header)
        print("-" * len(header))

        for result in results:
            success_rate = f"{result.successful_requests}/{result.total_requests}"
            print(
                f"{result.endpoint:<25} {result.method:<8} {result.requests_per_second:<10.1f} "
                f"{result.avg_response_time:<10.2f} {result.p95_response_time:<10.2f} {success_rate:<10}"
            )

    def print_comparison_summary(self):
        """Print a clear comparison summary with CRUD breakdown"""
        print("\n" + "=" * 100)
        print("🏆 COMPREHENSIVE CRUD PERFORMANCE COMPARISON")
        print("=" * 100)

        if not self.comparison_results:
            print("No comparison data available.")
            return

        # Group results by operation type
        basic_ops = []
        read_ops = []
        write_ops = []
        stress_ops = []

        for comp in self.comparison_results:
            if comp.endpoint in ["/", "/health", "/echo"]:
                basic_ops.append(comp)
            elif comp.method == "GET" and "/db/" in comp.endpoint:
                read_ops.append(comp)
            elif comp.method in ["POST", "PUT", "DELETE"] and "/db/" in comp.endpoint:
                write_ops.append(comp)
            elif "/stress/" in comp.endpoint:
                stress_ops.append(comp)

        # Print comparison by operation type
        self._print_operation_comparison("🔧 Basic Operations", basic_ops)
        self._print_operation_comparison("📖 Database READ Operations", read_ops)
        self._print_operation_comparison("✏️ Database WRITE Operations", write_ops)
        self._print_operation_comparison("💪 Stress Test Operations", stress_ops)

        # Overall summary
        print("\n" + "=" * 100)
        print("📊 OVERALL CRUD PERFORMANCE SUMMARY")
        print("=" * 100)

        # Calculate category winners
        categories = {
            "Basic Operations": basic_ops,
            "Database READ": read_ops,
            "Database WRITE": write_ops,
            "Stress Tests": stress_ops,
        }

        category_winners = {}
        overall_scores = {"FastAPI": 0, "Rust": 0, "Node.js": 0}

        for category_name, ops in categories.items():
            if ops:
                category_winner = self._get_category_winner(ops)
                category_winners[category_name] = category_winner
                overall_scores[category_winner] += 1

        # Print category winners
        print("🏅 Category Winners:")
        for category, winner in category_winners.items():
            print(f"   {category}: {winner}")

        # Determine overall winner
        overall_winner = max(overall_scores, key=overall_scores.get)
        print(f"\n🏆 Overall CRUD Champion: {overall_winner}")
        print(f"   (Won {overall_scores[overall_winner]}/{len(categories)} categories)")

        # Performance insights
        print(f"\n💡 Performance Insights:")

        if overall_winner == "Rust":
            print("🦀 Rust Axum dominates with:")
            print("   • Superior memory management and zero-cost abstractions")
            print("   • Excellent async performance with Tokio runtime")
            print("   • Efficient database operations with SQLx")
            print("   • Minimal overhead for high-throughput scenarios")

        elif overall_winner == "Node.js":
            print("🟢 Node.js TypeScript excels with:")
            print("   • V8 engine optimization for JavaScript execution")
            print("   • Efficient event loop for I/O operations")
            print("   • Good JSON processing performance")
            print("   • Mature ecosystem and async/await patterns")

        elif overall_winner == "FastAPI":
            print("🐍 FastAPI leads with:")
            print("   • Excellent async Python performance")
            print("   • Uvicorn's efficient ASGI implementation")
            print("   • Good balance of performance and developer productivity")
            print("   • Strong ecosystem integration")

        # CRUD-specific analysis
        if write_ops:
            write_winner = self._get_category_winner(write_ops)
            print(f"\n📝 CRUD Write Performance Leader: {write_winner}")
            print(
                "   Write operations (CREATE, UPDATE, DELETE) are often bottlenecked by:"
            )
            print("   • Database transaction overhead")
            print("   • Connection pool management")
            print("   • Data validation and serialization")

        if read_ops:
            read_winner = self._get_category_winner(read_ops)
            print(f"\n📖 CRUD Read Performance Leader: {read_winner}")
            print("   Read operations benefit from:")
            print("   • Efficient query execution")
            print("   • JSON serialization speed")
            print("   • Connection pooling strategies")

    def _print_operation_comparison(self, title, operations):
        """Print comparison for a specific operation type"""
        if not operations:
            return

        print(f"\n{title}")
        print("-" * 80)
        print(
            f"{'Endpoint':<20} {'Method':<8} {'FastAPI':<12} {'Rust':<12} {'Node.js':<12} {'Winner':<12}"
        )
        print("-" * 80)

        for comp in operations:
            # Determine winner for this endpoint
            rps_values = [
                ("FastAPI", comp.fastapi_rps),
                ("Rust", comp.rust_rps),
                ("Node.js", comp.nodejs_rps),
            ]
            rps_values = [(name, rps) for name, rps in rps_values if rps > 0]

            if rps_values:
                winner = max(rps_values, key=lambda x: x[1])
                winner_name = winner[0]
            else:
                winner_name = "N/A"

            print(
                f"{comp.endpoint:<20} {comp.method:<8} "
                f"{comp.fastapi_rps:<12.1f} {comp.rust_rps:<12.1f} "
                f"{comp.nodejs_rps:<12.1f} {winner_name:<12}"
            )

    def _get_category_winner(self, operations):
        """Determine the winner for a category of operations"""
        if not operations:
            return "N/A"

        total_scores = {"FastAPI": 0, "Rust": 0, "Node.js": 0}

        for comp in operations:
            rps_values = [
                ("FastAPI", comp.fastapi_rps),
                ("Rust", comp.rust_rps),
                ("Node.js", comp.nodejs_rps),
            ]
            rps_values = [(name, rps) for name, rps in rps_values if rps > 0]

            if rps_values:
                winner = max(rps_values, key=lambda x: x[1])
                total_scores[winner[0]] += 1

        return max(total_scores, key=total_scores.get)

    def save_comparison_results(
        self, filename: str = "comprehensive_crud_results.json"
    ):
        """Save comprehensive CRUD results to JSON"""
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "benchmark_type": "Comprehensive CRUD Benchmark",
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
            "nodejs_results": [
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
                for r in self.nodejs_results
            ],
            "comparisons": [
                {
                    "endpoint": c.endpoint,
                    "method": c.method,
                    "fastapi_rps": c.fastapi_rps,
                    "rust_rps": c.rust_rps,
                    "nodejs_rps": c.nodejs_rps,
                    "fastapi_avg_ms": c.fastapi_avg_ms,
                    "rust_avg_ms": c.rust_avg_ms,
                    "nodejs_avg_ms": c.nodejs_avg_ms,
                }
                for c in self.comparison_results
            ],
        }

        with open(filename, "w") as f:
            json.dump(results_data, f, indent=2)
        print(f"\n💾 Comprehensive CRUD results saved to {filename}")

    def create_performance_chart(
        self, filename: str = "crud_performance_comparison.png"
    ):
        """Create a visual comparison chart for CRUD operations"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np

            if not self.comparison_results:
                print("No data available for chart generation.")
                return

            # Group results by operation type for cleaner visualization
            basic_ops = [
                c
                for c in self.comparison_results
                if c.endpoint in ["/", "/health", "/echo"]
            ]
            read_ops = [
                c
                for c in self.comparison_results
                if c.method == "GET" and "/db/" in c.endpoint
            ]
            write_ops = [
                c
                for c in self.comparison_results
                if c.method in ["POST", "PUT", "DELETE"] and "/db/" in c.endpoint
            ]

            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 12))

            # Basic Operations RPS
            if basic_ops:
                self._plot_operation_comparison(
                    ax1, basic_ops, "Basic Operations - RPS", "rps"
                )

            # Database Read Operations RPS
            if read_ops:
                self._plot_operation_comparison(
                    ax2, read_ops, "Database READ Operations - RPS", "rps"
                )

            # Database Write Operations RPS
            if write_ops:
                self._plot_operation_comparison(
                    ax3, write_ops, "Database WRITE Operations - RPS", "rps"
                )

            # Combined Latency Comparison
            if self.comparison_results:
                self._plot_operation_comparison(
                    ax4,
                    self.comparison_results[:6],
                    "Response Time Comparison",
                    "latency",
                )

            plt.tight_layout()
            plt.savefig(filename, dpi=300, bbox_inches="tight")
            print(f"📊 Comprehensive CRUD chart saved to {filename}")

        except ImportError as e:
            missing_package = (
                "matplotlib"
                if "matplotlib" in str(e)
                else "numpy"
                if "numpy" in str(e)
                else "unknown package"
            )
            print(
                f"📊 {missing_package} not available. Install it with: pipenv install matplotlib numpy"
            )
        except Exception as e:
            print(f"Error creating chart: {e}")

    def _plot_operation_comparison(self, ax, operations, title, metric_type):
        """Helper method to plot operation comparisons"""
        if not operations:
            return

        endpoints = [f"{op.endpoint}\n({op.method})" for op in operations]

        if metric_type == "rps":
            fastapi_values = [op.fastapi_rps for op in operations]
            rust_values = [op.rust_rps for op in operations]
            nodejs_values = [op.nodejs_rps for op in operations]
            ylabel = "Requests per Second"
        else:  # latency
            fastapi_values = [op.fastapi_avg_ms for op in operations]
            rust_values = [op.rust_avg_ms for op in operations]
            nodejs_values = [op.nodejs_avg_ms for op in operations]
            ylabel = "Average Response Time (ms)"

        # Use range instead of numpy.arange to avoid numpy dependency issues
        x = list(range(len(endpoints)))
        width = 0.25

        # Calculate bar positions manually
        fastapi_positions = [i - width for i in x]
        rust_positions = x
        nodejs_positions = [i + width for i in x]

        ax.bar(
            fastapi_positions,
            fastapi_values,
            width,
            label="FastAPI",
            color="#3776ab",
            alpha=0.8,
        )
        ax.bar(
            rust_positions,
            rust_values,
            width,
            label="Rust Axum",
            color="#dea584",
            alpha=0.8,
        )
        ax.bar(
            nodejs_positions,
            nodejs_values,
            width,
            label="Node.js TypeScript",
            color="#339933",
            alpha=0.8,
        )

        ax.set_xlabel("Endpoints")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(endpoints, rotation=45, ha="right", fontsize=8)
        ax.legend()
        ax.grid(True, alpha=0.3)


async def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive CRUD Benchmark: FastAPI vs Rust Axum vs Node.js TypeScript"
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
        "--nodejs-url",
        default="http://localhost:4000",
        help="Node.js TypeScript server URL (default: http://localhost:4000)",
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
        default="comprehensive_crud_results.json",
        help="Output JSON file (default: comprehensive_crud_results.json)",
    )
    parser.add_argument(
        "--chart",
        default="crud_performance_comparison.png",
        help="Output chart file (default: crud_performance_comparison.png)",
    )

    args = parser.parse_args()

    benchmark = CRUDBenchmark(args.fastapi_url, args.rust_url, args.nodejs_url)

    try:
        await benchmark.run_crud_benchmark(args.requests, args.concurrent)
        benchmark.print_detailed_results()
        benchmark.print_comparison_summary()
        benchmark.save_comparison_results(args.output)
        benchmark.create_performance_chart(args.chart)

        print("\n🎉 Comprehensive CRUD benchmark completed successfully!")
        print(f"📄 Detailed results: {args.output}")
        print(f"📊 Performance chart: {args.chart}")
        print("\n📋 Summary:")
        print("   ✅ Basic endpoints (root, health, echo)")
        print("   ✅ Database READ operations (SELECT)")
        print("   ✅ Database WRITE operations (INSERT, UPDATE, DELETE)")
        print("   ✅ Stress tests (CPU, memory)")
        print("   ✅ Performance comparison across all CRUD operations")

    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure all servers are running:")
        print("   - FastAPI: cd api/python && pipenv shell && fastapi dev server.py")
        print("   - Rust: cd api/rust && cargo run")
        print("   - Node.js: cd api/typescript-node && npm run dev")
        print("2. Check that the URLs are correct")
        print("3. Ensure all servers have the required CRUD endpoints")


if __name__ == "__main__":
    asyncio.run(main())

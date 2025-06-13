# 🚀 FastAPI vs Rust Axum Performance Benchmark

A comprehensive performance comparison between FastAPI (Python) and Axum (Rust) web frameworks. This project provides identical APIs in both frameworks and benchmarks them across various endpoints to measure throughput, latency, and resource efficiency.

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running the Benchmark](#running-the-benchmark)
- [Understanding Results](#understanding-results)
- [Benchmark Metrics Explained](#benchmark-metrics-explained)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

This benchmark project compares two popular web frameworks:

- **FastAPI** (Python) - Modern, fast web framework with automatic API documentation
- **Axum** (Rust) - Ergonomic and modular web framework built on Tokio

Both implementations provide identical functionality:
- ✅ JSON REST APIs
- ✅ Database operations (SQLite)
- ✅ Echo endpoints for latency testing
- ✅ CPU and memory stress tests
- ✅ Health checks

## ⚡ Quick Start

```bash
# 1. Setup Python API (using pipenv)
cd api/python
pipenv shell
pipenv install
fastapi dev server.py            # Port 8000

# 2. Setup Rust API (new terminal)
cd api/rust  
cargo build
cargo run                        # Port 3000

# 3. Run comparison benchmark (new terminal)
cd api/benchmark
pipenv shell
pipenv install
python benchmark.py
```

## 📁 Project Structure

```
benchmark-project/
├── api/
│   ├── benchmark/               # Benchmark tools
│   │   ├── Pipfile             # Python dependencies for benchmarking
│   │   ├── Pipfile.lock
│   │   ├── benchmark.py        # Individual server benchmark
│   │   ├── comparison_results.json
│   │   ├── performance_comparison.png
│   │   └── models.py
│   ├── python/                 # FastAPI implementation
│   │   ├── Pipfile            # Python dependencies
│   │   ├── Pipfile.lock
│   │   ├── benchmark.db       # SQLite database
│   │   └── server.py          # FastAPI server
│   └── rust/                  # Rust Axum implementation
│       ├── src/
│       │   └── main.rs        # Rust Axum server
│       ├── Cargo.toml         # Rust dependencies
│       ├── Cargo.lock
│       └── benchmark.db       # SQLite database
└── README.md
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+ with pipenv
- Rust 1.70+ with Cargo

### FastAPI Setup (Python)

```bash
cd api/python

# Activate virtual environment
pipenv shell

# Install dependencies using pipenv
pipenv install

# If Pipfile doesn't exist, create dependencies:
# pipenv install fastapi uvicorn sqlalchemy aiofiles pydantic
```

**Create Pipfile in `api/python/`:**
```toml
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
fastapi = "==0.104.1"
uvicorn = {extras = ["standard"], version = "==0.24.0"}
pydantic = "==2.5.0"
sqlalchemy = "==2.0.23"
aiofiles = "==23.2.1"

[dev-packages]

[requires]
python_version = "3.8"
```

### Rust Axum Setup

```bash
cd api/rust

# Build dependencies
cargo build

# For production-like performance testing, use:
# cargo build --release
```

### Benchmark Tools Setup

```bash
cd api/benchmark

# Activate virtual environment
pipenv shell

# Install benchmark dependencies
pipenv install

# If Pipfile doesn't exist, create dependencies:
# pipenv install aiohttp matplotlib numpy
```

**Create Pipfile in `api/benchmark/`:**
```toml
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
aiohttp = "==3.9.1"
matplotlib = "==3.8.0"
numpy = "==1.24.3"

[dev-packages]

[requires]
python_version = "3.8"
```

## 🚀 Running the Benchmark

### Step 1: Start FastAPI Server

```bash
cd api/python
pipenv shell           # Activate virtual environment
pipenv install         # Install dependencies
fastapi dev server.py  # Start development server
```

You should see:
```
🚀 Server running on http://0.0.0.0:8000
```

### Step 2: Start Rust Axum Server (New Terminal)

```bash
cd api/rust
cargo build            # Build dependencies
cargo run              # Start server
```

For maximum performance testing, use:
```bash
cargo build --release
cargo run --release
```

You should see:
```
🚀 Server running on http://0.0.0.0:3000
```

### Step 3: Run Individual Benchmarks (Optional, New Terminal)

Test each server individually:

```bash
cd api/benchmark
pipenv shell          # Activate virtual environment
pipenv install        # Install dependencies

# Test FastAPI only
python benchmark.py --url http://localhost:8000 --requests 1000

# Test Rust only  
python benchmark.py --url http://localhost:3000 --requests 1000
```

### Step 4: Run Comparative Benchmark

```bash
cd api/benchmark
pipenv shell          # If not already in pipenv shell
python benchmark.py --fastapi-url http://localhost:8000 --rust-url http://localhost:3000
```

**Available options:**
```bash
# Custom request count and concurrency
python benchmark.py --requests 2000 --concurrent 100

# Save results to custom file
python benchmark.py --output my_results.json --chart my_chart.png

# Test different ports
python benchmark.py --fastapi-url http://localhost:8001 --rust-url http://localhost:3001
```

## 📊 Understanding Results

### Benchmark Metrics Explained

Each endpoint is tested with detailed performance metrics. Here's what each metric means and how it's calculated:

#### 🔢 **Core Metrics**

| Metric | Formula | What It Measures | Why It Matters |
|--------|---------|------------------|----------------|
| **RPS** | `Total Requests ÷ Total Time` | Throughput/Performance | How many requests the server can handle per second |
| **Avg(ms)** | `Sum of all response times ÷ Request count` | Mean Latency | Average time to process a request |
| **Min(ms)** | `Fastest response time` | Best Case Performance | Optimal server response under ideal conditions |
| **Max(ms)** | `Slowest response time` | Worst Case Performance | How bad it gets under stress |
| **P95(ms)** | `95th percentile of response times` | Tail Latency | 95% of requests are faster than this |
| **Success Rate** | `(Successful Requests ÷ Total Requests) × 100` | Reliability | Percentage of requests that didn't fail |

#### 📈 **Comparison Metrics**

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **Performance Ratio** | `Rust RPS ÷ FastAPI RPS` | > 1.0 = Rust is faster<br>< 1.0 = FastAPI is faster |
| **Latency Ratio** | `FastAPI Avg(ms) ÷ Rust Avg(ms)` | > 1.0 = Rust has lower latency<br>< 1.0 = FastAPI has lower latency |

#### 🎯 **What These Numbers Mean in Practice**

**RPS (Requests Per Second):**
- `< 1,000 RPS` = Low performance, suitable for internal tools
- `1,000 - 5,000 RPS` = Good performance, suitable for most web apps
- `5,000 - 10,000 RPS` = High performance, suitable for busy services
- `> 10,000 RPS` = Excellent performance, suitable for high-traffic APIs

**Response Time (Latency):**
- `< 10ms` = Excellent (sub-frame response)
- `10-50ms` = Very Good (imperceptible to users)
- `50-100ms` = Good (barely noticeable)
- `100-300ms` = Acceptable (noticeable but tolerable)
- `> 300ms` = Poor (users will notice delays)

**P95 Latency:**
- This is crucial for user experience
- If P95 = 100ms, then 95% of users experience < 100ms response
- Only 5% of users experience slower responses
- Much more important than average for real-world performance

#### 🧮 **How Benchmarks Are Calculated**

**1. Request Generation:**
```python
# Pseudo-code for benchmark process
concurrent_requests = 50
total_requests = 1000
semaphore = Semaphore(concurrent_requests)

start_time = time.now()
for i in range(total_requests):
    async with semaphore:  # Limit concurrency
        request_start = time.now()
        response = await make_request()
        request_time = time.now() - request_start
        record_metrics(request_time, response.status)
total_time = time.now() - start_time
```

**2. Statistical Calculations:**
```python
# Response time statistics
response_times = [0.012, 0.015, 0.018, ...]  # in seconds
avg_response_time = sum(response_times) / len(response_times)
min_response_time = min(response_times)
max_response_time = max(response_times)

# Sort for percentile calculations
sorted_times = sorted(response_times)
p95_index = int(len(sorted_times) * 0.95)
p95_response_time = sorted_times[p95_index]

# Throughput calculation
rps = total_requests / total_time_seconds
```

#### 🎭 **Load Testing Patterns**

**Concurrency Model:**
- **50 concurrent requests** = 50 virtual users hitting the server simultaneously
- **1000 total requests** = Each virtual user makes ~20 requests
- **Semaphore limiting** = Prevents overwhelming the server unfairly

**Request Distribution:**
```
Time →  [====|====|====|====|====]
User 1: [Req1|Req2|Req3|Req4|Req5]
User 2: [Req1|Req2|Req3|Req4|Req5]
...
User50: [Req1|Req2|Req3|Req4|Req5]
```

### Endpoints Tested

| Endpoint | Type | Purpose | What It Stresses |
|----------|------|---------|------------------|
| `GET /` | Basic | Simple JSON response | Basic HTTP handling, JSON serialization |
| `GET /health` | Basic | Health check with DB status | Database connectivity, status queries |
| `POST /echo` | Latency | Echo JSON data with timing | JSON parsing, request/response cycle |
| `GET /echo/test` | Latency | Simple GET echo | Minimal processing overhead |
| `GET /db/items` | I/O | Database read operations | Database queries, connection pooling |
| `POST /db/items` | I/O | Database write operations | Insert operations, transaction handling |
| `GET /stress/cpu/1000` | CPU | CPU-intensive calculations | Pure computational performance |
| `GET /stress/memory/1` | Memory | Memory allocation test | Memory management, garbage collection |

### Sample Output Explained

```
🚀 Starting Comparative Benchmark: FastAPI vs Rust Axum

✅ FastAPI server is running at http://localhost:8000
✅ Rust Axum server is running at http://localhost:3000

🏆 PERFORMANCE COMPARISON SUMMARY
================================================================
Endpoint             FastAPI RPS  Rust RPS     Rust Advantage  Latency Advantage
-------------------------------------------------------------------------------------
/                    2,847.3      8,924.1      3.1x faster     2.8x lower latency
/health              2,156.8      7,832.4      3.6x faster     3.2x lower latency
/echo                1,923.7      6,547.9      3.4x faster     3.1x lower latency
/db/items            1,234.5      3,891.2      3.2x faster     2.9x lower latency

📊 OVERALL PERFORMANCE SUMMARY
================================================================
🐍 FastAPI Average RPS: 2,040.6
🦀 Rust Axum Average RPS: 6,798.9  
🚀 Rust Performance Advantage: 3.3x faster
⚡ Rust Latency Advantage: 3.0x lower latency
🏁 Rust wins in 6/6 endpoints

🔥 Rust shows SIGNIFICANT performance advantage
🚄 Rust has SIGNIFICANTLY lower latency
```

#### 🔍 **Breaking Down This Example:**

**Root Endpoint (`/`):**
- **FastAPI**: 2,847 requests/second, ~0.35ms average response
- **Rust**: 8,924 requests/second, ~0.11ms average response
- **Analysis**: Rust processes 3.1x more requests and responds 2.8x faster

**Database Endpoint (`/db/items`):**
- **FastAPI**: 1,234 requests/second (lower due to I/O)
- **Rust**: 3,891 requests/second (still maintains high performance)
- **Analysis**: Database operations are bottlenecks, but Rust handles them more efficiently

**Overall Performance:**
- **3.3x faster** = If FastAPI handles 100 users, Rust handles 330 users
- **3.0x lower latency** = If FastAPI takes 30ms, Rust takes 10ms

### Performance Categories

| Ratio | Category | Description | Real-World Impact |
|-------|----------|-------------|-------------------|
| `> 2.0x` | 🔥 **SIGNIFICANT** | Major performance difference | Can handle 2x+ more users with same hardware |
| `1.5-2.0x` | ✨ **NOTABLE** | Clear performance advantage | Noticeable improvement in response times |
| `1.1-1.5x` | 📈 **MODERATE** | Noticeable improvement | Marginal but measurable benefits |
| `< 1.1x` | 🤝 **COMPARABLE** | Similar performance | Negligible difference for most use cases |

#### 🎮 **Interactive Interpretation Guide**

**If you see RPS of 5,000+:**
- ✅ Excellent for high-traffic APIs
- ✅ Can handle viral content or traffic spikes
- ✅ Suitable for microservices architecture

**If you see RPS of 1,000-5,000:**
- ✅ Good for most web applications
- ✅ Suitable for business applications
- ⚠️ May need scaling for high-traffic scenarios

**If you see RPS < 1,000:**
- ⚠️ Acceptable for internal tools
- ⚠️ May need optimization for public APIs
- 🔴 Not suitable for high-traffic applications

**If you see latency > 100ms:**
- 🔴 Users will notice delays
- 🔴 Mobile users will be especially affected
- 🔴 Consider caching or optimization

**If you see P95 > 2x average:**
- ⚠️ Inconsistent performance
- ⚠️ Some users experience much slower responses
- ⚠️ May indicate resource contention or GC issues

## 🎛️ Customization

### Testing Different Workloads

```bash
# Make sure you're in pipenv shell first
cd api/benchmark
pipenv shell

# Light load testing
python benchmark.py --requests 500 --concurrent 25

# Heavy load testing
python benchmark.py --requests 5000 --concurrent 200

# Sustained load testing  
python benchmark.py --requests 10000 --concurrent 100
```

### Adding Custom Endpoints

Edit the `test_endpoints` list in `benchmark.py`:

```python
test_endpoints = [
    ("/", "GET", None, "Root endpoint"),
    ("/custom", "POST", {"data": "test"}, "Custom endpoint"),
    # Add your endpoints here
]
```

### Database Configuration

Both servers use SQLite by default. To test with PostgreSQL:

1. **Update connection strings** in both `server.py` and `main.rs`
2. **Install database drivers**: `asyncpg` for Python, `sqlx` with PostgreSQL features for Rust
3. **Run migrations** to create tables

### Production-Like Testing

For more realistic results:

```bash
# Use release builds for maximum performance
cd api/rust
cargo build --release
cargo run --release

# Disable debug logging
export RUST_LOG=warn

# Test on production-like hardware
# Use external database (PostgreSQL/MySQL)
# Include network latency in testing
```

## 🔧 Troubleshooting

### Common Issues

**1. "Server not responding"**
```bash
# Check if servers are running
curl http://localhost:8000/health  # FastAPI
curl http://localhost:3000/health  # Rust

# Check processes
ps aux | grep python
ps aux | grep target
```

**2. Port conflicts**
```bash
# Kill processes on ports
kill $(lsof -t -i:8000)  # FastAPI
kill $(lsof -t -i:3000)  # Rust

# Or use different ports
python benchmark.py --fastapi-url http://localhost:8001
```

**3. Pipenv issues**
```bash
# Reset pipenv environment
pipenv --rm
pipenv shell
pipenv install

# If pipenv shell doesn't work, use:
pipenv run python benchmark.py

# Use system Python if needed
python -m pip install fastapi uvicorn aiohttp matplotlib
```

**4. Database errors**
```bash
# Reset databases
rm api/python/benchmark.db
rm api/rust/benchmark.db

# Check permissions
chmod 666 benchmark.db
```

**5. Rust compilation errors**
```bash
# Update Rust
rustup update

# Clean build
cargo clean
cargo build

# For production performance
cargo build --release
```

**6. Import/dependency errors**
```bash
# Install missing packages
cd api/benchmark
pipenv shell
pipenv install matplotlib numpy

cd api/python  
pipenv shell
pipenv install fastapi uvicorn
```

### Performance Debugging

**Low performance issues:**

1. **Check CPU usage**: `htop` or `top`
2. **Monitor memory**: `free -h`
3. **Check disk I/O**: `iotop`
4. **Network latency**: `ping localhost`
5. **Database locks**: Check SQLite journal files

**Inconsistent results:**

1. **Run multiple times** and average results
2. **Increase warmup requests**
3. **Close other applications**
4. **Use dedicated hardware**
5. **Disable CPU throttling**

### Getting Help

If you encounter issues:

1. **Check server logs** for error messages
2. **Verify endpoint availability** with curl
3. **Test with fewer concurrent requests**
4. **Check system resources** (CPU, memory, disk)
5. **Try different request patterns**

## 🎯 Expected Results

### Typical Performance Characteristics

**Rust Axum Advantages:**
- 🚀 **2-4x higher throughput** (RPS)
- ⚡ **2-5x lower latency** (response time)
- 📈 **Better CPU efficiency**
- 🔥 **Superior performance under high load**
- 💾 **Lower memory usage**

**FastAPI Advantages:**
- 🐍 **Faster development time**
- 📚 **Rich ecosystem** (more libraries)
- 🛠️ **Better debugging tools**
- 👥 **Larger community**
- 📖 **Automatic API documentation**

### When to Choose Each

**Choose Rust Axum when:**
- Performance is critical
- High concurrent load expected
- Long-running services
- Resource efficiency matters
- Type safety is important

**Choose FastAPI when:**
- Rapid prototyping needed
- Complex business logic
- Extensive Python ecosystem required
- Team expertise in Python
- Quick API documentation needed

## 📈 Output Files

The benchmark generates several files:

- **`comparison_results.json`** - Detailed JSON results for further analysis
- **`performance_comparison.png`** - Visual charts comparing both frameworks
- **Console output** - Real-time results and summary

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Axum Documentation](https://docs.rs/axum/)
- [SQLx Documentation](https://docs.rs/sqlx/)
- [Tokio Documentation](https://tokio.rs/)
- [Performance Testing Best Practices](https://docs.python.org/3/library/profile.html)

---

**Happy Benchmarking! 🎉**

For questions or issues, please check the troubleshooting section or create an issue in the repository.

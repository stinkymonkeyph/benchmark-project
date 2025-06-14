# 🚀 FastAPI vs Rust Axum vs Node.js TypeScript Performance Benchmark

A comprehensive performance comparison between three popular web frameworks: FastAPI (Python), Axum (Rust), and Express with TypeScript (Node.js). This project provides identical APIs across all three frameworks and benchmarks them with complete CRUD operations to measure throughput, latency, and resource efficiency.

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running the Benchmark](#running-the-benchmark)
- [Understanding Results](#understanding-results)
- [Benchmark Metrics Explained](#benchmark-metrics-explained)
- [CRUD Operations Testing](#crud-operations-testing)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

This benchmark project compares three modern web frameworks:

- **FastAPI** (Python) - Modern, fast web framework with automatic API documentation
- **Axum** (Rust) - Ergonomic and modular web framework built on Tokio
- **Express TypeScript** (Node.js) - Popular JavaScript framework with TypeScript support

All implementations provide identical functionality:
- ✅ JSON REST APIs with full CRUD operations
- ✅ Database operations (SQLite with CREATE, READ, UPDATE, DELETE)
- ✅ Echo endpoints for latency testing
- ✅ CPU and memory stress tests
- ✅ Health checks and monitoring
- ✅ Automatic database cleanup after testing

## ⚡ Quick Start

```bash
# 1. Setup Python FastAPI (using pipenv)
cd api/python
pipenv shell
pipenv install
uvicorn server:app --host 0.0.0.0 --port 8000  # Port 8000

# 2. Setup Rust Axum (new terminal)
cd api/rust  
cargo build --release
cargo run --release                              # Port 3000

# 3. Setup Node.js TypeScript (new terminal)
cd api/typescript-node
npm install
npm run dev                                      # Port 4000

# 4. Run comprehensive CRUD benchmark (new terminal)
cd api/benchmark
pipenv shell
pipenv install
python enhanced_crud_benchmark.py
```

## 📁 Project Structure

```
benchmark-project/
├── api/
│   ├── benchmark/               # Benchmark tools
│   │   ├── Pipfile             # Python dependencies for benchmarking
│   │   ├── Pipfile.lock
│   │   ├── benchmark.py        # Individual server benchmark
│   │   ├── enhanced_crud_benchmark.py  # Comprehensive CRUD benchmark
│   │   ├── comprehensive_crud_results.json
│   │   └── crud_performance_comparison.png
│   ├── python/                 # FastAPI implementation
│   │   ├── Pipfile            # Python dependencies
│   │   ├── Pipfile.lock
│   │   ├── benchmark.db       # SQLite database
│   │   └── server.py          # FastAPI server
│   ├── rust/                  # Rust Axum implementation
│   │   ├── src/
│   │   │   └── main.rs        # Rust Axum server
│   │   ├── Cargo.toml         # Rust dependencies
│   │   ├── Cargo.lock
│   │   └── benchmark.db       # SQLite database
│   └── typescript-node/       # Node.js TypeScript implementation
│       ├── src/
│       │   └── server.ts      # TypeScript server
│       ├── package.json       # Node.js dependencies
│       ├── tsconfig.json      # TypeScript configuration
│       ├── node_modules/      # Dependencies
│       ├── dist/             # Compiled JavaScript
│       └── benchmark.db       # SQLite database
├── .gitignore
└── README.md
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+ with pipenv
- Rust 1.70+ with Cargo
- Node.js 16+ with npm

### FastAPI Setup (Python)

```bash
cd api/python

# Activate virtual environment
pipenv shell

# Install dependencies using pipenv
pipenv install

# If Pipfile doesn't exist, create dependencies:
# pipenv install fastapi uvicorn[standard] sqlalchemy aiofiles pydantic
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
cargo build --release

# For maximum performance testing, always use release mode
```

### Node.js TypeScript Setup

```bash
cd api/typescript-node

# Install dependencies
npm install

# If package.json doesn't exist, initialize:
# npm init -y
# npm install express sqlite3 sqlite cors
# npm install -D @types/express @types/node @types/cors typescript ts-node
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

# Start server using uvicorn directly
uvicorn server:app --host 0.0.0.0 --port 8000

# For production-like performance, use:
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 1 --loop uvloop

# Alternative: if you have the optimized version with startup code
python server.py
```

You should see:
```
🚀 Server running on http://0.0.0.0:8000
```

### Step 2: Start Rust Axum Server (New Terminal)

```bash
cd api/rust

# For maximum performance testing, always use release mode
cargo build --release
cargo run --release
```

You should see:
```
🚀 Server running on http://0.0.0.0:3000
```

### Step 3: Start Node.js TypeScript Server (New Terminal)

```bash
cd api/typescript-node
npm install            # Install dependencies
npm run dev            # Start development server
```

You should see:
```
🚀 Node.js TypeScript server running on http://0.0.0.0:4000
```

### Step 4: Run Individual Benchmarks (Optional, New Terminal)

Test each server individually:

```bash
cd api/benchmark
pipenv shell          # Activate virtual environment
pipenv install        # Install dependencies

# Test FastAPI only
python benchmark.py --url http://localhost:8000 --requests 1000

# Test Rust only  
python benchmark.py --url http://localhost:3000 --requests 1000

# Test Node.js only
python benchmark.py --url http://localhost:4000 --requests 1000
```

### Step 5: Run Comprehensive CRUD Benchmark

```bash
cd api/benchmark
pipenv shell          # If not already in pipenv shell
python enhanced_crud_benchmark.py
```

**Available options:**
```bash
# Custom request count and concurrency
python enhanced_crud_benchmark.py --requests 2000 --concurrent 100

# Save results to custom file
python enhanced_crud_benchmark.py --output my_results.json --chart my_chart.png

# Test specific servers only
python enhanced_crud_benchmark.py --fastapi-url http://localhost:8000 --nodejs-url http://localhost:4000
```

## 📊 Understanding Results

### CRUD Operations Testing

The enhanced benchmark now tests **complete CRUD operations** across all frameworks:

#### 🔧 **Phase 1: Basic Endpoints**
- `GET /` - Root endpoint (JSON response)
- `GET /health` - Health check with database status
- `POST /echo` - Echo POST with JSON data and timing
- `GET /echo/test` - Simple GET echo endpoint

#### 📖 **Phase 2: Database READ Operations**
- `GET /db/items` - **SELECT all** items from database
- `GET /db/items/1` - **SELECT single** item with WHERE clause

#### 📝 **Phase 3: Database CREATE Operations**
- `POST /db/items` - **INSERT** new records (500 requests)
- Tests database write performance and connection handling

#### ✏️ **Phase 4: Database UPDATE Operations**
- `PUT /db/items/1` - **UPDATE** existing records (250 requests)
- Tests modification performance and transaction handling

#### 🗑️ **Phase 5: Database DELETE Operations**
- `DELETE /db/items/2` - **DELETE** records (100 requests)
- Tests removal performance and referential integrity

#### 💪 **Phase 6: Stress Tests**
- `GET /stress/cpu/1000` - CPU-intensive calculations
- `GET /stress/memory/1` - Memory allocation and cleanup

#### 🧹 **Phase 7: Automatic Cleanup**
- Removes all benchmark-created items (ID > 3)
- Preserves original sample data for consistency
- Ensures reproducible benchmark results

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
| **Performance Ratio** | `Winner RPS ÷ Other RPS` | > 1.0 = Performance advantage |
| **Category Winner** | `Highest RPS in operation type` | Framework that excels in specific operations |

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

### Sample Output Explained

```
🚀 Starting Comprehensive CRUD Benchmark: FastAPI vs Rust Axum vs Node.js TypeScript

✅ FastAPI server is running at http://localhost:8000
✅ Rust Axum server is running at http://localhost:3000
✅ Node.js TypeScript server is running at http://localhost:4000

🏅 Category Winners:
   Basic Operations: Rust
   Database READ: Rust  
   Database WRITE: Node.js
   Stress Tests: Rust

🏆 Overall CRUD Champion: Rust
   (Won 3/4 categories)

💡 Performance Insights:
🦀 Rust Axum dominates with:
   • Superior memory management and zero-cost abstractions
   • Excellent async performance with Tokio runtime
   • Efficient database operations with SQLx

🧹 CLEANUP: Resetting databases to initial state...
🗑️ FastAPI: Deleting 387 benchmark items...
🗑️ Rust: Deleting 402 benchmark items...
🗑️ Node.js: Deleting 395 benchmark items...
✅ Database cleanup completed
```

### Performance Categories

| Ratio | Category | Description | Real-World Impact |
|-------|----------|-------------|-------------------|
| `> 2.0x` | 🔥 **SIGNIFICANT** | Major performance difference | Can handle 2x+ more users with same hardware |
| `1.5-2.0x` | ✨ **NOTABLE** | Clear performance advantage | Noticeable improvement in response times |
| `1.1-1.5x` | 📈 **MODERATE** | Noticeable improvement | Marginal but measurable benefits |
| `< 1.1x` | 🤝 **COMPARABLE** | Similar performance | Negligible difference for most use cases |

### CRUD-Specific Performance Insights

**Database READ Operations:**
- **SELECT queries** are typically the fastest database operations
- **Connection pooling** efficiency becomes crucial under load
- **JSON serialization** speed affects overall response time

**Database WRITE Operations:**
- **INSERT/UPDATE/DELETE** are slower due to transaction overhead
- **Foreign key constraints** and **indexes** impact performance
- **Connection management** is critical for write-heavy workloads

**Framework Strengths by Operation:**

🦀 **Rust Axum typically excels at:**
- Basic HTTP handling (zero-cost abstractions)
- Memory-intensive operations
- CPU-bound computations
- High-concurrency scenarios

🐍 **FastAPI typically excels at:**
- Complex business logic (Python ecosystem)
- Rapid development and iteration
- Scientific computing integration
- Data processing pipelines

🟢 **Node.js TypeScript typically excels at:**
- I/O-heavy operations (event loop)
- JSON processing (V8 optimization)
- Real-time applications
- Microservices architecture

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

# Use optimized Python server
cd api/python
pipenv shell
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 1 --loop uvloop

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

**3. FastAPI startup issues**
```bash
# Check if server.py contains the app variable
python -c "from server import app; print('App found successfully')"

# If using different filename, adjust the uvicorn command:
uvicorn your_filename:app --host 0.0.0.0 --port 8000

# If app variable has different name:
uvicorn server:your_app_name --host 0.0.0.0 --port 8000

# Test without uvloop if it causes issues:
uvicorn server:app --host 0.0.0.0 --port 8000

# Alternative: run with Python directly if server.py has startup code
python server.py
```

**4. Pipenv issues**
```bash
# Reset pipenv environment
pipenv --rm
pipenv shell
pipenv install

# If pipenv shell doesn't work, use:
pipenv run uvicorn server:app --host 0.0.0.0 --port 8000
pipenv run python benchmark.py

# Use system Python if needed
python -m pip install fastapi uvicorn aiohttp matplotlib
```

**5. Database errors**
```bash
# Reset databases
rm api/python/benchmark.db
rm api/rust/benchmark.db

# Check permissions
chmod 666 benchmark.db
```

**6. Rust compilation errors**
```bash
# Update Rust
rustup update

# Clean build
cargo clean
cargo build --release

# For production performance, always use release mode
cargo run --release
```

**7. Import/dependency errors**
```bash
# Install missing packages
cd api/benchmark
pipenv shell
pipenv install matplotlib numpy aiohttp

cd api/python  
pipenv shell
pipenv install fastapi uvicorn[standard] pydantic
```

**8. uvloop installation issues**
```bash
# If uvloop fails to install or run
pip install uvloop

# Or run without uvloop
uvicorn server:app --host 0.0.0.0 --port 8000

# On Windows, uvloop might not be available
pip install uvicorn[standard]
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
- 📈 **Superior CPU efficiency**
- 🔥 **Excellent performance under high load**
- 💾 **Lowest memory usage**
- 🎯 **Consistent performance** (no garbage collection pauses)

**Node.js TypeScript Advantages:**
- 🟢 **Strong I/O performance** (event loop efficiency)
- ⚡ **Fast JSON processing** (V8 engine optimization)
- 📊 **Good async/await performance**
- 🚀 **Competitive throughput** (often 2nd place)
- 🔄 **Efficient connection handling**
- 💡 **Moderate memory usage**

**FastAPI Advantages:**
- 🐍 **Fastest development time**
- 📚 **Rich ecosystem** (more libraries)
- 🛠️ **Better debugging tools**
- 👥 **Largest community**
- 📖 **Automatic API documentation**
- 🧠 **Great for data science integration**

### When to Choose Each

**Choose Rust Axum when:**
- Performance is critical
- High concurrent load expected
- Long-running services
- Resource efficiency matters
- Type safety is paramount
- Microservices with tight SLAs

**Choose Node.js TypeScript when:**
- I/O-heavy applications
- Real-time features needed
- JavaScript ecosystem familiarity
- Rapid iteration required
- JSON-heavy APIs
- Microservices architecture
- Good balance of performance and productivity

**Choose FastAPI when:**
- Rapid prototyping needed
- Complex business logic
- Extensive Python ecosystem required
- Team expertise in Python
- Data science/ML integration
- Quick API documentation needed

## 📈 Output Files

The benchmark generates several files:

- **`comparison_results.json`** - Detailed JSON results for further analysis
- **`performance_comparison.png`** - Visual charts comparing all frameworks
- **Console output** - Real-time results and summary

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Uvicorn Documentation](https://www.uvicorn.org/)
- [Axum Documentation](https://docs.rs/axum/)
- [SQLx Documentation](https://docs.rs/sqlx/)
- [Tokio Documentation](https://tokio.rs/)
- [Performance Testing Best Practices](https://docs.python.org/3/library/profile.html)

---

**Happy Benchmarking! 🎉**

For questions or issues, please check the troubleshooting section or create an issue in the repository.

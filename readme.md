# 🚀 FastAPI vs Rust Axum Performance Benchmark

A comprehensive performance comparison between FastAPI (Python) and Axum (Rust) web frameworks. This project provides identical APIs in both frameworks and benchmarks them across various endpoints to measure throughput, latency, and resource efficiency.

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running the Benchmark](#running-the-benchmark)
- [Understanding Results](#understanding-results)
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

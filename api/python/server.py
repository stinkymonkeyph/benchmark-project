from typing import Union, List, Optional
from fastapi import FastAPI, HTTPException, Request
import time
import asyncio
from datetime import datetime
import sqlite3
import os
import contextlib
from functools import lru_cache

# Inline models since you might not have a separate models.py file
from pydantic import BaseModel, Field
from typing import Optional, Any


class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Item name")
    description: Optional[str] = Field(
        None, max_length=1000, description="Item description"
    )
    price: float = Field(..., ge=0, description="Item price (must be non-negative)")


class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    created_at: str


class EchoRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Message to echo")
    data: Optional[Any] = Field(None, description="Optional data payload")


class EchoResponse(BaseModel):
    message: str
    data: Optional[Any]
    timestamp: str
    processing_time_ms: float


app = FastAPI(title="FastAPI Benchmark API", version="1.0.0")

DATABASE_URL = "benchmark.db"

# Connection pool simulation using a simple connection context manager


@contextlib.contextmanager
def get_db_connection():
    """Context manager for database connections with optimizations"""
    conn = sqlite3.connect(DATABASE_URL, timeout=30.0)
    try:
        # Enable WAL mode and other optimizations
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = 64000")  # 64MB cache
        conn.execute("PRAGMA temp_store = memory")
        conn.execute("PRAGMA mmap_size = 268435456")  # 256MB memory map
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute("PRAGMA auto_vacuum = NONE")
        conn.execute("PRAGMA page_size = 4096")
        conn.row_factory = sqlite3.Row  # Enable row factory for better performance
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize database with performance optimizations"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Create table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for better query performance
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_items_created_at ON items(created_at)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_name ON items(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_price ON items(price)")

        # Optimize SQLite query planner
        cursor.execute("PRAGMA optimize")

        # Check if we need sample data
        cursor.execute("SELECT COUNT(*) FROM items")
        if cursor.fetchone()[0] == 0:
            sample_items = [
                ("Laptop", "High-performance laptop", 999.99),
                ("Mouse", "Wireless mouse", 29.99),
                ("Keyboard", "Mechanical keyboard", 79.99),
            ]
            cursor.executemany(
                "INSERT INTO items (name, description, price) VALUES (?, ?, ?)",
                sample_items,
            )

        conn.commit()


# Initialize database on startup
init_db()


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()  # More precise timing
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@lru_cache(maxsize=1)
def get_current_timestamp_cached():
    """Cache timestamp for very short periods to reduce datetime overhead"""
    return datetime.now().isoformat()


@app.get("/")
def read_root():
    return {"Hello": "World", "timestamp": datetime.now().isoformat()}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q, "timestamp": datetime.now().isoformat()}


@app.post("/echo", response_model=EchoResponse)
async def echo_post(request: EchoRequest):
    start_time = time.perf_counter()

    # Simulate some processing time
    await asyncio.sleep(0.001)  # 1ms delay

    processing_time = (time.perf_counter() - start_time) * 1000

    return EchoResponse(
        message=request.message,
        data=request.data,
        timestamp=datetime.now().isoformat(),
        processing_time_ms=processing_time,
    )


@app.get("/echo/{message}")
async def echo_get(message: str):
    """Simple GET echo endpoint"""
    start_time = time.perf_counter()
    await asyncio.sleep(0.001)
    processing_time = (time.perf_counter() - start_time) * 1000

    return {
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "processing_time_ms": processing_time,
    }


# Database CRUD endpoints for benchmarking - OPTIMIZED


@app.get("/db/items", response_model=List[ItemResponse])
def get_all_items():
    """Get all items from database - optimized query"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Optimized query with simpler ORDER BY for better performance
        cursor.execute(
            "SELECT id, name, description, price, created_at FROM items ORDER BY id"
        )
        rows = cursor.fetchall()

    return [
        ItemResponse(
            id=row[0], name=row[1], description=row[2], price=row[3], created_at=row[4]
        )
        for row in rows
    ]


@app.get("/db/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int):
    """Get single item by ID"""
    if item_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid item ID")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, description, price, created_at FROM items WHERE id = ?",
            (item_id,),
        )
        row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Item not found")

    return ItemResponse(
        id=row[0], name=row[1], description=row[2], price=row[3], created_at=row[4]
    )


@app.post("/db/items", response_model=ItemResponse)
def create_item(item: Item):
    """Create new item in database with validation"""
    # Input validation
    if not item.name or not item.name.strip():
        raise HTTPException(
            status_code=400, detail="Name is required and must be non-empty"
        )

    if item.price is None or item.price < 0:
        raise HTTPException(
            status_code=400, detail="Price must be a non-negative number"
        )

    with get_db_connection() as conn:
        cursor = conn.cursor()

        try:
            # Insert the item (SQLite handles this atomically)
            cursor.execute(
                "INSERT INTO items (name, description, price) VALUES (?, ?, ?)",
                (item.name.strip(), item.description, item.price),
            )
            item_id = cursor.lastrowid

            # Get the created item
            cursor.execute(
                "SELECT id, name, description, price, created_at FROM items WHERE id = ?",
                (item_id,),
            )
            row = cursor.fetchone()

            conn.commit()

        except Exception as e:
            print(f"Database error in create_item: {e}")
            raise HTTPException(status_code=500, detail="Database error")

    return ItemResponse(
        id=row[0], name=row[1], description=row[2], price=row[3], created_at=row[4]
    )


@app.put("/db/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item: Item):
    """Update existing item with validation"""
    if item_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid item ID")

    # Input validation
    if not item.name or not item.name.strip():
        raise HTTPException(
            status_code=400, detail="Name is required and must be non-empty"
        )

    if item.price is None or item.price < 0:
        raise HTTPException(
            status_code=400, detail="Price must be a non-negative number"
        )

    with get_db_connection() as conn:
        cursor = conn.cursor()

        try:
            # Check if item exists
            cursor.execute("SELECT id FROM items WHERE id = ?", (item_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Item not found")

            # Update the item (SQLite handles this atomically)
            cursor.execute(
                "UPDATE items SET name = ?, description = ?, price = ? WHERE id = ?",
                (item.name.strip(), item.description, item.price, item_id),
            )

            # Get the updated item
            cursor.execute(
                "SELECT id, name, description, price, created_at FROM items WHERE id = ?",
                (item_id,),
            )
            row = cursor.fetchone()

            conn.commit()

        except HTTPException:
            raise
        except Exception as e:
            print(f"Database error in update_item: {e}")
            raise HTTPException(status_code=500, detail="Database error")

    return ItemResponse(
        id=row[0], name=row[1], description=row[2], price=row[3], created_at=row[4]
    )


@app.delete("/db/items/{item_id}")
def delete_item(item_id: int):
    """Delete item by ID"""
    if item_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid item ID")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        try:
            # Check if item exists
            cursor.execute("SELECT id FROM items WHERE id = ?", (item_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Item not found")

            # Delete the item (SQLite handles this atomically)
            cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))

            conn.commit()

        except HTTPException:
            raise
        except Exception as e:
            print(f"Database error in delete_item: {e}")
            raise HTTPException(status_code=500, detail="Database error")

    return {"message": f"Item {item_id} deleted successfully"}


# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint for monitoring with actual DB test"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
    }


# Stress test endpoints
@app.get("/stress/cpu/{iterations}")
def cpu_stress(iterations: int):
    """CPU intensive endpoint for stress testing"""
    if iterations < 0:
        raise HTTPException(status_code=400, detail="Iterations must be non-negative")

    start_time = time.perf_counter()

    # Simple CPU intensive task
    result = 0
    for i in range(iterations):
        result += i * i  # More consistent with other implementations

    processing_time = (time.perf_counter() - start_time) * 1000

    return {
        "iterations": iterations,
        "result": result,
        "processing_time_ms": processing_time,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/stress/memory/{size_mb}")
def memory_stress(size_mb: int):
    """Memory allocation endpoint for stress testing"""
    if size_mb < 0:
        raise HTTPException(status_code=400, detail="Size must be non-negative")

    if size_mb > 100:  # Limit to prevent server issues
        raise HTTPException(status_code=400, detail="Size too large, max 100MB")

    start_time = time.perf_counter()

    # Allocate memory (be careful with large values)
    data = bytearray(size_mb * 1024 * 1024)  # Allocate MB of memory
    data_size = len(data)
    del data  # Explicit cleanup

    processing_time = (time.perf_counter() - start_time) * 1000

    return {
        "allocated_bytes": data_size,
        "allocated_mb": size_mb,
        "processing_time_ms": processing_time,
        "timestamp": datetime.now().isoformat(),
    }


# Database benchmark endpoint
@app.get("/db/benchmark/select/{count}")
def db_benchmark_select(count: int):
    """Database SELECT performance benchmark"""
    if count < 0:
        raise HTTPException(status_code=400, detail="Count must be non-negative")

    start_time = time.perf_counter()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, description, price FROM items LIMIT ?", (count,)
        )
        rows = cursor.fetchall()

    processing_time = (time.perf_counter() - start_time) * 1000

    return {
        "rows_fetched": len(rows),
        "processing_time_ms": processing_time,
        "timestamp": datetime.now().isoformat(),
    }


# Startup event to ensure optimal database configuration
@app.on_event("startup")
async def startup_event():
    """Run database optimizations on startup"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Run ANALYZE to update statistics for query planner
        cursor.execute("ANALYZE")
        cursor.execute("PRAGMA optimize")
        conn.commit()


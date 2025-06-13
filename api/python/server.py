from typing import Union, List
from fastapi import FastAPI, HTTPException, Request
import time
import asyncio
from datetime import datetime
import sqlite3
import os
from models import Item, EchoResponse, ItemResponse, EchoRequest

app = FastAPI(title="FastAPI Benchmark API", version="1.0.0")

DATABASE_URL = "benchmark.db"


def init_db():
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
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
    conn.close()


init_db()


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/")
def read_root():
    return {"Hello": "World", "timestamp": datetime.now().isoformat()}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q, "timestamp": datetime.now().isoformat()}


@app.post("/echo", response_model=EchoResponse)
async def echo_post(request: EchoRequest):
    start_time = time.time()

    # Simulate some processing time
    await asyncio.sleep(0.001)  # 1ms delay

    processing_time = (time.time() - start_time) * 1000

    return EchoResponse(
        message=request.message,
        data=request.data,
        timestamp=datetime.now().isoformat(),
        processing_time_ms=processing_time,
    )


@app.get("/echo/{message}")
async def echo_get(message: str):
    """Simple GET echo endpoint"""
    start_time = time.time()
    await asyncio.sleep(0.001)
    processing_time = (time.time() - start_time) * 1000

    return {
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "processing_time_ms": processing_time,
    }


# Database CRUD endpoints for benchmarking
@app.get("/db/items", response_model=List[ItemResponse])
def get_all_items():
    """Get all items from database"""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, price, created_at FROM items")
    rows = cursor.fetchall()
    conn.close()

    return [
        ItemResponse(
            id=row[0], name=row[1], description=row[2], price=row[3], created_at=row[4]
        )
        for row in rows
    ]


@app.get("/db/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int):
    """Get single item by ID"""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, description, price, created_at FROM items WHERE id = ?",
        (item_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Item not found")

    return ItemResponse(
        id=row[0], name=row[1], description=row[2], price=row[3], created_at=row[4]
    )


@app.post("/db/items", response_model=ItemResponse)
def create_item(item: Item):
    """Create new item in database"""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO items (name, description, price) VALUES (?, ?, ?)",
        (item.name, item.description, item.price),
    )
    item_id = cursor.lastrowid

    # Get the created item
    cursor.execute(
        "SELECT id, name, description, price, created_at FROM items WHERE id = ?",
        (item_id,),
    )
    row = cursor.fetchone()
    conn.commit()
    conn.close()

    return ItemResponse(
        id=row[0], name=row[1], description=row[2], price=row[3], created_at=row[4]
    )


@app.put("/db/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item: Item):
    """Update existing item"""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Check if item exists
    cursor.execute("SELECT id FROM items WHERE id = ?", (item_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")

    # Update the item
    cursor.execute(
        "UPDATE items SET name = ?, description = ?, price = ? WHERE id = ?",
        (item.name, item.description, item.price, item_id),
    )

    # Get the updated item
    cursor.execute(
        "SELECT id, name, description, price, created_at FROM items WHERE id = ?",
        (item_id,),
    )
    row = cursor.fetchone()
    conn.commit()
    conn.close()

    return ItemResponse(
        id=row[0], name=row[1], description=row[2], price=row[3], created_at=row[4]
    )


@app.delete("/db/items/{item_id}")
def delete_item(item_id: int):
    """Delete item by ID"""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Check if item exists
    cursor.execute("SELECT id FROM items WHERE id = ?", (item_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")

    # Delete the item
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

    return {"message": f"Item {item_id} deleted successfully"}


# Health check endpoint


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if os.path.exists(DATABASE_URL) else "disconnected",
    }


# Stress test endpoints


@app.get("/stress/cpu/{iterations}")
def cpu_stress(iterations: int):
    """CPU intensive endpoint for stress testing"""
    start_time = time.time()

    # Simple CPU intensive task
    result = 0
    for i in range(iterations):
        result += i**2

    processing_time = (time.time() - start_time) * 1000

    return {
        "iterations": iterations,
        "result": result,
        "processing_time_ms": processing_time,
    }


@app.get("/stress/memory/{size_mb}")
def memory_stress(size_mb: int):
    """Memory allocation endpoint for stress testing"""
    start_time = time.time()

    # Allocate memory (be careful with large values)
    if size_mb > 100:  # Limit to prevent server issues
        raise HTTPException(status_code=400, detail="Size too large, max 100MB")

    data = bytearray(size_mb * 1024 * 1024)  # Allocate MB of memory
    data_size = len(data)
    del data

    processing_time = (time.time() - start_time) * 1000

    return {
        "allocated_bytes": data_size,
        "allocated_mb": size_mb,
        "processing_time_ms": processing_time,
    }


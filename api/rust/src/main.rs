use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    middleware::{self, Next},
    response::{Json, Response},
    routing::{get, post, put, delete},
    Router,
};
use serde::{Deserialize, Serialize};
use sqlx::sqlite::SqlitePool;
use std::{
    collections::HashMap,
    time::{Duration, Instant},
};
use tokio::time::sleep;
use tower::ServiceBuilder;
use tower_http::cors::CorsLayer;

// Application state
#[derive(Clone)]
pub struct AppState {
    pub db: SqlitePool,
}

// Data models
#[derive(Debug, Serialize, Deserialize)]
pub struct Item {
    pub name: String,
    pub description: Option<String>,
    pub price: f64,
}

#[derive(Debug, Serialize, Deserialize, sqlx::FromRow)]
pub struct ItemResponse {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub price: f64,
    pub created_at: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct EchoRequest {
    pub message: String,
    pub data: Option<serde_json::Value>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct EchoResponse {
    pub message: String,
    pub data: Option<serde_json::Value>,
    pub timestamp: String,
    pub processing_time_ms: f64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HealthResponse {
    pub status: String,
    pub timestamp: String,
    pub database: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CpuStressResponse {
    pub iterations: u64,
    pub result: u64,
    pub processing_time_ms: f64,
    pub timestamp: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct MemoryStressResponse {
    pub allocated_bytes: usize,
    pub allocated_mb: u64,
    pub processing_time_ms: f64,
    pub timestamp: String,
}

// Database initialization with performance optimizations
pub async fn init_db() -> Result<SqlitePool, sqlx::Error> {
    let pool = SqlitePool::connect_with(
        sqlx::sqlite::SqliteConnectOptions::new()
            .filename("benchmark.db")
            .create_if_missing(true)
            .pragma("journal_mode", "WAL")
            .pragma("synchronous", "NORMAL")
            .pragma("cache_size", "64000")
            .pragma("temp_store", "memory")
            .pragma("mmap_size", "268435456")
            .pragma("foreign_keys", "off")
            .pragma("auto_vacuum", "none")
            .pragma("page_size", "4096")
    ).await?;

    // Create table
    sqlx::query(
        r#"
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        "#,
    )
    .execute(&pool)
    .await?;

    // Create indexes
    sqlx::query("CREATE INDEX IF NOT EXISTS idx_items_created_at ON items(created_at)")
        .execute(&pool).await?;
    sqlx::query("CREATE INDEX IF NOT EXISTS idx_items_name ON items(name)")
        .execute(&pool).await?;
    sqlx::query("CREATE INDEX IF NOT EXISTS idx_items_price ON items(price)")
        .execute(&pool).await?;

    sqlx::query("PRAGMA optimize").execute(&pool).await?;

    // Insert sample data if empty
    let count: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM items")
        .fetch_one(&pool).await?;

    if count == 0 {
        let sample_items = vec![
            ("Laptop", Some("High-performance laptop"), 999.99),
            ("Mouse", Some("Wireless mouse"), 29.99),
            ("Keyboard", Some("Mechanical keyboard"), 79.99),
        ];

        for (name, description, price) in sample_items {
            sqlx::query("INSERT INTO items (name, description, price) VALUES (?, ?, ?)")
                .bind(name)
                .bind(description)
                .bind(price)
                .execute(&pool)
                .await?;
        }
    }

    Ok(pool)
}

// Middleware
pub async fn add_process_time_header(
    request: axum::extract::Request,
    next: Next,
) -> Response {
    let start = Instant::now();
    let mut response = next.run(request).await;
    let elapsed = start.elapsed();
    
    response.headers_mut().insert(
        "x-process-time",
        elapsed.as_secs_f64().to_string().parse().unwrap(),
    );
    
    response
}

// Utility functions
fn current_iso_timestamp() -> String {
    chrono::Utc::now().to_rfc3339()
}

// Route handlers
pub async fn read_root() -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "Hello": "World",
        "timestamp": current_iso_timestamp()
    }))
}

pub async fn read_item(
    Path(item_id): Path<u32>,
    Query(params): Query<HashMap<String, String>>,
) -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "item_id": item_id,
        "q": params.get("q"),
        "timestamp": current_iso_timestamp()
    }))
}

pub async fn health_check(State(state): State<AppState>) -> Json<HealthResponse> {
    let db_status = match sqlx::query("SELECT 1").fetch_one(&state.db).await {
        Ok(_) => "connected",
        Err(_) => "disconnected",
    };

    Json(HealthResponse {
        status: "healthy".to_string(),
        timestamp: current_iso_timestamp(),
        database: db_status.to_string(),
    })
}

pub async fn echo_post(Json(payload): Json<EchoRequest>) -> Json<EchoResponse> {
    let start = Instant::now();
    sleep(Duration::from_millis(1)).await;
    let processing_time = start.elapsed().as_secs_f64() * 1000.0;
    
    Json(EchoResponse {
        message: payload.message,
        data: payload.data,
        timestamp: current_iso_timestamp(),
        processing_time_ms: processing_time,
    })
}

pub async fn echo_get(Path(message): Path<String>) -> Json<serde_json::Value> {
    let start = Instant::now();
    sleep(Duration::from_millis(1)).await;
    let processing_time = start.elapsed().as_secs_f64() * 1000.0;
    
    Json(serde_json::json!({
        "message": message,
        "timestamp": current_iso_timestamp(),
        "processing_time_ms": processing_time
    }))
}

// Database CRUD operations - NO COMPILE-TIME MACROS
pub async fn get_all_items(State(state): State<AppState>) -> Result<Json<Vec<ItemResponse>>, StatusCode> {
    let items: Vec<ItemResponse> = sqlx::query_as(
        "SELECT id, name, description, price, created_at FROM items ORDER BY id"
    )
    .fetch_all(&state.db)
    .await
    .map_err(|e| {
        eprintln!("Database error in get_all_items: {:?}", e);
        StatusCode::INTERNAL_SERVER_ERROR
    })?;

    Ok(Json(items))
}

pub async fn get_item(
    Path(item_id): Path<i64>,
    State(state): State<AppState>,
) -> Result<Json<ItemResponse>, StatusCode> {
    let item: ItemResponse = sqlx::query_as(
        "SELECT id, name, description, price, created_at FROM items WHERE id = ?"
    )
    .bind(item_id)
    .fetch_one(&state.db)
    .await
    .map_err(|_| StatusCode::NOT_FOUND)?;

    Ok(Json(item))
}

pub async fn create_item(
    State(state): State<AppState>,
    Json(payload): Json<Item>,
) -> Result<Json<ItemResponse>, StatusCode> {
    if payload.name.is_empty() || payload.price < 0.0 {
        return Err(StatusCode::BAD_REQUEST);
    }

    let result = sqlx::query("INSERT INTO items (name, description, price) VALUES (?, ?, ?)")
        .bind(&payload.name)
        .bind(&payload.description)
        .bind(payload.price)
        .execute(&state.db)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    let item_id = result.last_insert_rowid();

    let item: ItemResponse = sqlx::query_as(
        "SELECT id, name, description, price, created_at FROM items WHERE id = ?"
    )
    .bind(item_id)
    .fetch_one(&state.db)
    .await
    .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(item))
}

pub async fn update_item(
    Path(item_id): Path<i64>,
    State(state): State<AppState>,
    Json(payload): Json<Item>,
) -> Result<Json<ItemResponse>, StatusCode> {
    if payload.name.is_empty() || payload.price < 0.0 {
        return Err(StatusCode::BAD_REQUEST);
    }

    // Check if exists
    let existing = sqlx::query("SELECT id FROM items WHERE id = ?")
        .bind(item_id)
        .fetch_optional(&state.db)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    if existing.is_none() {
        return Err(StatusCode::NOT_FOUND);
    }

    // Update
    sqlx::query("UPDATE items SET name = ?, description = ?, price = ? WHERE id = ?")
        .bind(&payload.name)
        .bind(&payload.description)
        .bind(payload.price)
        .bind(item_id)
        .execute(&state.db)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    // Get updated item
    let item: ItemResponse = sqlx::query_as(
        "SELECT id, name, description, price, created_at FROM items WHERE id = ?"
    )
    .bind(item_id)
    .fetch_one(&state.db)
    .await
    .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(item))
}

pub async fn delete_item(
    Path(item_id): Path<i64>,
    State(state): State<AppState>,
) -> Result<Json<serde_json::Value>, StatusCode> {
    // Check if exists
    let existing = sqlx::query("SELECT id FROM items WHERE id = ?")
        .bind(item_id)
        .fetch_optional(&state.db)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    if existing.is_none() {
        return Err(StatusCode::NOT_FOUND);
    }

    // Delete
    sqlx::query("DELETE FROM items WHERE id = ?")
        .bind(item_id)
        .execute(&state.db)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(serde_json::json!({
        "message": format!("Item {} deleted successfully", item_id)
    })))
}

// Stress test endpoints
pub async fn cpu_stress(Path(iterations): Path<u64>) -> Json<CpuStressResponse> {
    let start = Instant::now();
    let mut result = 0u64;
    for i in 0..iterations {
        result = result.wrapping_add(i.wrapping_mul(i));
    }
    let processing_time = start.elapsed().as_secs_f64() * 1000.0;
    
    Json(CpuStressResponse {
        iterations,
        result,
        processing_time_ms: processing_time,
        timestamp: current_iso_timestamp(),
    })
}

pub async fn memory_stress(Path(size_mb): Path<u64>) -> Result<Json<MemoryStressResponse>, StatusCode> {
    if size_mb > 100 {
        return Err(StatusCode::BAD_REQUEST);
    }
    
    let start = Instant::now();
    let size_bytes = (size_mb * 1024 * 1024) as usize;
    let data = vec![0u8; size_bytes];
    let allocated_bytes = data.len();
    drop(data);
    let processing_time = start.elapsed().as_secs_f64() * 1000.0;
    
    Ok(Json(MemoryStressResponse {
        allocated_bytes,
        allocated_mb: size_mb,
        processing_time_ms: processing_time,
        timestamp: current_iso_timestamp(),
    }))
}

pub async fn db_benchmark_select(
    Path(count): Path<u32>,
    State(state): State<AppState>,
) -> Result<Json<serde_json::Value>, StatusCode> {
    let start = Instant::now();
    
    let rows = sqlx::query("SELECT id, name, description, price FROM items LIMIT ?")
        .bind(count)
        .fetch_all(&state.db)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    let processing_time = start.elapsed().as_secs_f64() * 1000.0;

    Ok(Json(serde_json::json!({
        "rows_fetched": rows.len(),
        "processing_time_ms": processing_time,
        "timestamp": current_iso_timestamp()
    })))
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt::init();

    let db = init_db().await?;
    let app_state = AppState { db };

    let app = Router::new()
        .route("/", get(read_root))
        .route("/items/:item_id", get(read_item))
        .route("/health", get(health_check))
        .route("/echo", post(echo_post))
        .route("/echo/:message", get(echo_get))
        .route("/db/items", get(get_all_items).post(create_item))
        .route("/db/items/:item_id", get(get_item).put(update_item).delete(delete_item))
        .route("/db/benchmark/select/:count", get(db_benchmark_select))
        .route("/stress/cpu/:iterations", get(cpu_stress))
        .route("/stress/memory/:size_mb", get(memory_stress))
        .with_state(app_state)
        .layer(
            ServiceBuilder::new()
                .layer(CorsLayer::permissive())
                .layer(middleware::from_fn(add_process_time_header))
        );

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await?;
    println!("🚀 Server running on http://0.0.0.0:3000");
    
    axum::serve(listener, app).await?;
    Ok(())
}

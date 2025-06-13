use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    middleware::{self, Next},
    response::{Json, Response},
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use sqlx::{sqlite::SqlitePool, Row};
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

#[derive(Debug, Serialize, Deserialize)]
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
pub struct StressResponse {
    pub processing_time_ms: f64,
    pub timestamp: String,
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

// Database initialization
pub async fn init_db() -> Result<SqlitePool, sqlx::Error> {
    let database_url = "sqlite:benchmark.db?mode=rwc";
    let pool = SqlitePool::connect(database_url).await?;

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

    // Insert sample data if table is empty
    let count: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM items")
        .fetch_one(&pool)
        .await?;

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

// Middleware for adding processing time
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

// Basic endpoints
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

// Health check
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

// Echo endpoints
pub async fn echo_post(Json(payload): Json<EchoRequest>) -> Json<EchoResponse> {
    let start = Instant::now();
    
    // Simulate some processing time
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

// Database CRUD operations
pub async fn get_all_items(State(state): State<AppState>) -> Result<Json<Vec<ItemResponse>>, StatusCode> {
    let rows = sqlx::query("SELECT id, name, description, price, created_at FROM items")
        .fetch_all(&state.db)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    let items: Vec<ItemResponse> = rows
        .iter()
        .map(|row| ItemResponse {
            id: row.get("id"),
            name: row.get("name"),
            description: row.get("description"),
            price: row.get("price"),
            created_at: row.get::<String, _>("created_at"),
        })
        .collect();

    Ok(Json(items))
}

pub async fn get_item(
    Path(item_id): Path<i64>,
    State(state): State<AppState>,
) -> Result<Json<ItemResponse>, StatusCode> {
    let row = sqlx::query("SELECT id, name, description, price, created_at FROM items WHERE id = ?")
        .bind(item_id)
        .fetch_one(&state.db)
        .await
        .map_err(|_| StatusCode::NOT_FOUND)?;

    let item = ItemResponse {
        id: row.get("id"),
        name: row.get("name"),
        description: row.get("description"),
        price: row.get("price"),
        created_at: row.get("created_at"),
    };

    Ok(Json(item))
}

pub async fn create_item(
    State(state): State<AppState>,
    Json(payload): Json<Item>,
) -> Result<Json<ItemResponse>, StatusCode> {
    let result = sqlx::query("INSERT INTO items (name, description, price) VALUES (?, ?, ?)")
        .bind(&payload.name)
        .bind(&payload.description)
        .bind(payload.price)
        .execute(&state.db)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    let item_id = result.last_insert_rowid();

    let row = sqlx::query("SELECT id, name, description, price, created_at FROM items WHERE id = ?")
        .bind(item_id)
        .fetch_one(&state.db)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    let item = ItemResponse {
        id: row.get("id"),
        name: row.get("name"),
        description: row.get("description"),
        price: row.get("price"),
        created_at: row.get("created_at"),
    };

    Ok(Json(item))
}

// Stress test endpoints
pub async fn cpu_stress(Path(iterations): Path<u64>) -> Json<CpuStressResponse> {
    let start = Instant::now();
    
    // CPU intensive task
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
    
    // Allocate memory
    let size_bytes = (size_mb * 1024 * 1024) as usize;
    let data = vec![0u8; size_bytes];
    let allocated_bytes = data.len();
    
    // Keep data in scope briefly then drop
    drop(data);
    
    let processing_time = start.elapsed().as_secs_f64() * 1000.0;
    
    Ok(Json(MemoryStressResponse {
        allocated_bytes,
        allocated_mb: size_mb,
        processing_time_ms: processing_time,
        timestamp: current_iso_timestamp(),
    }))
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize tracing
    tracing_subscriber::fmt::init();

    // Initialize database
    let db = init_db().await?;
    let app_state = AppState { db };

    // Build our application with routes
    let app = Router::new()
        // Basic routes
        .route("/", get(read_root))
        .route("/items/:item_id", get(read_item))
        .route("/health", get(health_check))
        
        // Echo routes
        .route("/echo", post(echo_post))
        .route("/echo/:message", get(echo_get))
        
        // Database CRUD routes
        .route("/db/items", get(get_all_items).post(create_item))
        .route("/db/items/:item_id", get(get_item))
        
        // Stress test routes
        .route("/stress/cpu/:iterations", get(cpu_stress))
        .route("/stress/memory/:size_mb", get(memory_stress))
        
        // Add state and middleware
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

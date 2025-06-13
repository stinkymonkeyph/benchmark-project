import express, { Request, Response, NextFunction } from 'express';
import sqlite3 from 'sqlite3';
import { open, Database } from 'sqlite';
import cors from 'cors';
import { promisify } from 'util';

// Types
interface Item {
  name: string;
  description?: string;
  price: number;
}

interface ItemResponse {
  id: number;
  name: string;
  description?: string;
  price: number;
  created_at: string;
}

interface EchoRequest {
  message: string;
  data?: any;
}

interface EchoResponse {
  message: string;
  data?: any;
  timestamp: string;
  processing_time_ms: number;
}

interface HealthResponse {
  status: string;
  timestamp: string;
  database: string;
}

interface CpuStressResponse {
  iterations: number;
  result: number;
  processing_time_ms: number;
  timestamp: string;
}

interface MemoryStressResponse {
  allocated_bytes: number;
  allocated_mb: number;
  processing_time_ms: number;
  timestamp: string;
}

// Database setup
let db: Database;

async function initDatabase(): Promise<void> {
  db = await open({
    filename: 'benchmark.db',
    driver: sqlite3.Database
  });

  // Create table
  await db.exec(`
    CREATE TABLE IF NOT EXISTS items (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      description TEXT,
      price REAL NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Insert sample data if table is empty
  const count = await db.get('SELECT COUNT(*) as count FROM items');
  if (count.count === 0) {
    const sampleItems = [
      ['Laptop', 'High-performance laptop', 999.99],
      ['Mouse', 'Wireless mouse', 29.99],
      ['Keyboard', 'Mechanical keyboard', 79.99]
    ];

    for (const [name, description, price] of sampleItems) {
      await db.run(
        'INSERT INTO items (name, description, price) VALUES (?, ?, ?)',
        [name, description, price]
      );
    }
  }
}

// Middleware to add processing time
const addProcessTimeHeader = (req: Request, res: Response, next: NextFunction) => {
  const startTime = process.hrtime.bigint();

  // Store the original json and send methods
  const originalJson = res.json;
  const originalSend = res.send;

  // Override json method
  res.json = function (body?: any) {
    const endTime = process.hrtime.bigint();
    const processingTime = Number(endTime - startTime) / 1000000;
    this.setHeader('X-Process-Time', processingTime.toString());
    return originalJson.call(this, body);
  };

  // Override send method
  res.send = function (body?: any) {
    const endTime = process.hrtime.bigint();
    const processingTime = Number(endTime - startTime) / 1000000;
    this.setHeader('X-Process-Time', processingTime.toString());
    return originalSend.call(this, body);
  };

  next();
};

// Utility functions
const getCurrentTimestamp = (): string => {
  return new Date().toISOString();
};

const sleep = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

// Express app setup
const app = express();
const PORT = process.env.PORT || 4000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(addProcessTimeHeader);

// Basic endpoints
app.get('/', (req: Request, res: Response) => {
  res.json({
    Hello: 'World',
    timestamp: getCurrentTimestamp()
  });
});

app.get('/items/:itemId', (req: Request, res: Response) => {
  const itemId = parseInt(req.params.itemId);
  const q = req.query.q as string;

  res.json({
    item_id: itemId,
    q: q || null,
    timestamp: getCurrentTimestamp()
  });
});

// Health check
app.get('/health', async (req: Request, res: Response) => {
  try {
    await db.get('SELECT 1');
    const response: HealthResponse = {
      status: 'healthy',
      timestamp: getCurrentTimestamp(),
      database: 'connected'
    };
    res.json(response);
  } catch (error) {
    const response: HealthResponse = {
      status: 'healthy',
      timestamp: getCurrentTimestamp(),
      database: 'disconnected'
    };
    res.json(response);
  }
});

// Echo endpoints
app.post('/echo', async (req: Request, res: Response) => {
  const startTime = process.hrtime.bigint();
  const echoRequest: EchoRequest = req.body;

  // Simulate some processing time
  await sleep(1);

  const endTime = process.hrtime.bigint();
  const processingTime = Number(endTime - startTime) / 1000000;

  const response: EchoResponse = {
    message: echoRequest.message,
    data: echoRequest.data,
    timestamp: getCurrentTimestamp(),
    processing_time_ms: processingTime
  };

  res.json(response);
});

app.get('/echo/:message', async (req: Request, res: Response) => {
  const startTime = process.hrtime.bigint();
  const message = req.params.message;

  await sleep(1);

  const endTime = process.hrtime.bigint();
  const processingTime = Number(endTime - startTime) / 1000000;

  res.json({
    message,
    timestamp: getCurrentTimestamp(),
    processing_time_ms: processingTime
  });
});

// Database CRUD operations
app.get('/db/items', async (req: Request, res: Response) => {
  try {
    const rows = await db.all(`
      SELECT id, name, description, price, created_at 
      FROM items
    `);

    const items: ItemResponse[] = rows.map(row => ({
      id: row.id,
      name: row.name,
      description: row.description,
      price: row.price,
      created_at: row.created_at
    }));

    res.json(items);
  } catch (error) {
    res.status(500).json({ error: 'Database error' });
  }
});

app.get('/db/items/:itemId', async (req: Request, res: Response): Promise<void> => {
  try {
    const itemId = parseInt(req.params.itemId);
    const row = await db.get(`
      SELECT id, name, description, price, created_at 
      FROM items WHERE id = ?
    `, [itemId]);

    if (!row) {
      res.status(404).json({ error: 'Item not found' });
      return;
    }

    const item: ItemResponse = {
      id: row.id,
      name: row.name,
      description: row.description,
      price: row.price,
      created_at: row.created_at
    };

    res.json(item);
  } catch (error) {
    res.status(500).json({ error: 'Database error' });
  }
});

app.post('/db/items', async (req: Request, res: Response) => {
  try {
    const item: Item = req.body;

    const result = await db.run(`
      INSERT INTO items (name, description, price) 
      VALUES (?, ?, ?)
    `, [item.name, item.description, item.price]);

    const newItem = await db.get(`
      SELECT id, name, description, price, created_at 
      FROM items WHERE id = ?
    `, [result.lastID]);

    const response: ItemResponse = {
      id: newItem.id,
      name: newItem.name,
      description: newItem.description,
      price: newItem.price,
      created_at: newItem.created_at
    };

    res.status(201).json(response);
  } catch (error) {
    res.status(500).json({ error: 'Database error' });
  }
});

app.put('/db/items/:itemId', async (req: Request, res: Response): Promise<void> => {
  try {
    const itemId = parseInt(req.params.itemId);
    const item: Item = req.body;

    // Check if item exists
    const existing = await db.get('SELECT id FROM items WHERE id = ?', [itemId]);
    if (!existing) {
      res.status(404).json({ error: 'Item not found' });
      return;
    }

    // Update the item
    await db.run(`
      UPDATE items 
      SET name = ?, description = ?, price = ? 
      WHERE id = ?
    `, [item.name, item.description, item.price, itemId]);

    // Get the updated item
    const updatedItem = await db.get(`
      SELECT id, name, description, price, created_at 
      FROM items WHERE id = ?
    `, [itemId]);

    const response: ItemResponse = {
      id: updatedItem.id,
      name: updatedItem.name,
      description: updatedItem.description,
      price: updatedItem.price,
      created_at: updatedItem.created_at
    };

    res.json(response);
  } catch (error) {
    res.status(500).json({ error: 'Database error' });
  }
});

app.delete('/db/items/:itemId', async (req: Request, res: Response): Promise<void> => {
  try {
    const itemId = parseInt(req.params.itemId);

    // Check if item exists
    const existing = await db.get('SELECT id FROM items WHERE id = ?', [itemId]);
    if (!existing) {
      res.status(404).json({ error: 'Item not found' });
      return;
    }

    // Delete the item
    await db.run('DELETE FROM items WHERE id = ?', [itemId]);

    res.json({
      message: `Item ${itemId} deleted successfully`
    });
  } catch (error) {
    res.status(500).json({ error: 'Database error' });
  }
});

// Stress test endpoints
app.get('/stress/cpu/:iterations', (req: Request, res: Response) => {
  const startTime = process.hrtime.bigint();
  const iterations = parseInt(req.params.iterations);

  // CPU intensive task
  let result = 0;
  for (let i = 0; i < iterations; i++) {
    result += i * i;
  }

  const endTime = process.hrtime.bigint();
  const processingTime = Number(endTime - startTime) / 1000000;

  const response: CpuStressResponse = {
    iterations,
    result,
    processing_time_ms: processingTime,
    timestamp: getCurrentTimestamp()
  };

  res.json(response);
});

app.get('/stress/memory/:sizeMb', (req: Request, res: Response): void => {
  const startTime = process.hrtime.bigint();
  const sizeMb = parseInt(req.params.sizeMb);

  if (sizeMb > 100) {
    res.status(400).json({ error: 'Size too large, max 100MB' });
    return;
  }

  // Allocate memory
  const sizeBytes = sizeMb * 1024 * 1024;
  const buffer = Buffer.alloc(sizeBytes);
  const allocatedBytes = buffer.length;

  // Clean up immediately
  buffer.fill(0);

  const endTime = process.hrtime.bigint();
  const processingTime = Number(endTime - startTime) / 1000000;

  const response: MemoryStressResponse = {
    allocated_bytes: allocatedBytes,
    allocated_mb: sizeMb,
    processing_time_ms: processingTime,
    timestamp: getCurrentTimestamp()
  };

  res.json(response);
});

// Error handling middleware
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

// 404 handler
app.use((req: Request, res: Response) => {
  res.status(404).json({ error: 'Not found' });
});

// Start server
async function startServer() {
  try {
    await initDatabase();
    console.log('Database initialized successfully');

    app.listen(PORT, () => {
      console.log(`🚀 Node.js TypeScript server running on http://0.0.0.0:${PORT}`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('\nShutting down gracefully...');
  if (db) {
    await db.close();
  }
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('\nShutting down gracefully...');
  if (db) {
    await db.close();
  }
  process.exit(0);
});

startServer();

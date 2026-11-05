import sqlite3
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse

def init_db():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            title TEXT,
            done INTEGER,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # Check for existing table schema and add timestamp columns if missing
    cursor.execute("PRAGMA table_info(tasks)")
    columns = [col[1] for col in cursor.fetchall()]
    if "created_at" not in columns:
        cursor.execute("ALTER TABLE tasks ADD COLUMN created_at TEXT")
    if "updated_at" not in columns:
        cursor.execute("ALTER TABLE tasks ADD COLUMN updated_at TEXT")
    
    now = datetime.utcnow().isoformat()
    cursor.execute("UPDATE tasks SET created_at = ? WHERE created_at IS NULL", (now,))
    cursor.execute("UPDATE tasks SET updated_at = ? WHERE updated_at IS NULL", (now,))

    cursor.execute("SELECT COUNT(*) FROM tasks")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done, created_at, updated_at) VALUES (?, ?, ?, ?)",
            [
                ("Buy a book", 0, now, now),
                ("Write Lab Assignment", 1, now, now),
                ("Walk the dog", 0, now, now),
            ]
        )
    conn.commit()
    conn.close()

init_db()

app = FastAPI()

# Root endpoint - returns basic API info
@app.get("/")
async def root():
    return JSONResponse(
        status_code=200,
        content={"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}
    )

# Get tasks from database with optional search and status filtering
@app.get("/tasks")
async def get_all_tasks(search: Optional[str] = None, done: Optional[bool] = None):
    query = "SELECT * FROM tasks"
    conditions = []
    params = []

    if search:
        conditions.append("title LIKE ?")
        params.append(f"%{search}%")

    if done is not None:
        conditions.append("done = ?")
        params.append(1 if done else 0)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "done": bool(row["done"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
        for row in rows
    ]

# Get a single task by ID
@app.get("/tasks/{id}")
async def get_task_by_id(id: int):
    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row["id"],
            "title": row["title"],
            "done": bool(row["done"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
    return JSONResponse(
        status_code=404,
        content={"error": "Task not found"}
    )

# Create a new task (stored in SQLite with timestamps)
@app.post("/tasks")
async def create_task(task: dict):
    title = task.get("title")
    if title is None or title.strip() == "":
        return JSONResponse(
            status_code=400,
            content={"error": "Task title is required"}
        )
    
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, done, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (title.strip(), 0, now, now)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    new_task = {
        "id": new_id,
        "title": title.strip(),
        "done": False,
        "created_at": now,
        "updated_at": now
    }
    
    return JSONResponse(
        status_code=201,
        content=new_task
    )

# Update task title and/or done status in database (refreshes updated_at)
@app.put("/tasks/{id}")
async def update_task(id: int, task: dict):
    if not task:
        return JSONResponse(
            status_code=400,
            content={"error": "Body required"}
        )
    
    title = task.get("title")
    done = task.get("done")
    if title is None and done is None:
        return JSONResponse(
            status_code=400,
            content={"error": "title or done is required"}
        )
    
    if title is not None and str(title).strip() == "":
        return JSONResponse(
            status_code=400,
            content={"error": "Task title cannot be empty"}
        )

    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"}
        )
    
    new_title = title.strip() if title is not None else row["title"]
    new_done = int(done) if done is not None else row["done"]
    now = datetime.utcnow().isoformat()

    cursor.execute(
        "UPDATE tasks SET title = ?, done = ?, updated_at = ? WHERE id = ?",
        (new_title, new_done, now, id)
    )
    conn.commit()
    conn.close()

    return {
        "id": id,
        "title": new_title,
        "done": bool(new_done),
        "created_at": row["created_at"],
        "updated_at": now
    }

# Delete a task by ID from database
@app.delete("/tasks/{id}")
async def delete_task(id: int):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"}
        )

    cursor.execute("DELETE FROM tasks WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return Response(status_code=204)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

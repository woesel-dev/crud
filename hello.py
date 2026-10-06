import sqlite3

def init_db():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            title TEXT,
            done INTEGER
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM tasks")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [
                ("Buy a book", 0),
                ("Write Lab Assignment", 1),
                ("Walk the dog", 0),
            ]
        )
    conn.commit()
    conn.close()

init_db()

tasks =[
    {"id": 1, "title":"Buy a book", "done": False},
    {"id": 2, "title":"Write Lab Assignment", "done": True},
    {"id": 3, "title":"Walk the dog", "done": False},
]

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
async def root():
    return JSONResponse(
        status_code = 200,
        content = {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"] }
    )

@app.get("/tasks")
async def get_all_tasks():
    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row["id"], "title": row["title"], "done": bool(row["done"])} for row in rows]

@app.get("/tasks/{id}")
async def get_task_by_id(id: int):
    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}
    return JSONResponse(
        status_code=404,
        content={"error": "Task not found"}
    )

@app.post("/tasks")
async def create_task(task: dict):
    title = task.get("title")
    if title is None or title.strip() == "":
        return JSONResponse(
            status_code=400,
            content={"error": "Task title is required"}
        )
    new_task = {
        "id": len(tasks) + 1,
        "title": title.strip(),
        "done": False
    }
    tasks.append(new_task)
    return JSONResponse(
        status_code=201,
        content= new_task
    )

@app.put("/tasks/{id}")
async def update_task(id: int, task: dict):
    if not task:
        return JSONResponse(
            status_code=400,
            content={"error":"Body required"}
        )
    for i in tasks:
        if i["id"] == id:
            title = task.get("title")
            done = task.get("done")
            if title is None and done is None:
                return JSONResponse(
                    status_code=400,
                    content={"error":"title or done is required"}
                )
            if title is not None:
                i["title"] = title
            if done is not None:
                i["done"] = done
            return i
    return JSONResponse(
        status_code=404,
        content={"error":"Task not found"}
    )

@app.delete("/tasks/{id}")
async def delete_task(id: int):
    for i in tasks:
        if i["id"] == id:
            tasks.remove(i)
            return JSONResponse(
                status_code=204,
                content={}
            )
    return JSONResponse(
        status_code=404,
        content={"error":"Task not found"}
    )

@app.get("/health")
async def health_check():
    return { "status": "ok"}

#Checked Swagger UI
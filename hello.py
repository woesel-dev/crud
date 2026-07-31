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
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"] }

@app.get("/tasks")
async def get_all_tasks():
    return tasks

@app.get("/task/{id}")
async def get_task_by_id(id:int):
    for task in tasks:
        if task["id"] == id:
            return task
    return JSONResponse(
        status_code=404,
        content={"error": f"Task {id} not found"}
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

@app.get("/health")
async def health_check():
    return { "status": "ok"}
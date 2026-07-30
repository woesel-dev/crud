tasks =[
    {"id": 1, "title":"Buy a book", "done": False},
    {"id": 2, "title":"Write Lab Assignment", "done": True},
    {"id": 3, "title":"Walk the dog", "done": False},
]

from fastapi import FastAPI

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

@app.get("/health")
async def health_check():
    return { "status": "ok"}
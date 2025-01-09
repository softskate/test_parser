import subprocess
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from itertools import cycle
from threading import Thread, Semaphore
import time
from contextlib import asynccontextmanager
from config import proxies


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Запускается при старте приложения, чтобы начать отсчёт времени.
    """
    global start_time
    start_time = time.time()

    # Запускаем парсер в отдельном потоке
    Thread(target=launch_parser, daemon=True).start()
    yield


app = FastAPI(lifespan=lifespan)

MAX_CONCURRENT_RUNS = 10
semaphore = Semaphore(MAX_CONCURRENT_RUNS)

proxies = cycle(proxies)

# Хранилище задач
tasks = []
completed_tasks = []
start_time = None
end_time = None

# Модель завершённой задачи
class CompletedTask(BaseModel):
    id: str
    title: str
    price: str
    success: bool


@app.get("/tasks", response_model=Optional[dict])
def get_task():
    """
    Отдаёт первую незавершённую задачу из списка.
    Ограничивает количество одновременно выдаваемых задач.
    """
    global tasks
    if not tasks:
        return None

    return tasks.pop(0)

@app.post("/tasks/complete")
def complete_task(task: CompletedTask, background_tasks: BackgroundTasks):
    """
    Принимает завершённую задачу с результатом.
    Освобождает место для запуска следующей задачи.
    """
    global completed_tasks, semaphore, end_time
    
    # Проверяем, была ли задача ранее выдана
    task_ids = [t["id"] for t in completed_tasks]
    if task.id in task_ids:
        raise HTTPException(status_code=400, detail="Task already completed")
    
    # Добавляем завершённую задачу
    completed_tasks.append(task.model_dump())
    
    # Освобождаем семафор
    semaphore.release()

    # Если задач больше нет, завершаем работу
    if not tasks and semaphore._value == MAX_CONCURRENT_RUNS:
        end_time = time.time()
        background_tasks.add_task(log_summary)

    return {"message": "Task completed successfully", "task": task}

def log_summary():
    """
    Логирует общую информацию о выполнении задач.
    """
    global start_time, end_time, completed_tasks
    total_time = end_time - start_time if end_time and start_time else 0
    successful_tasks = sum(1 for task in completed_tasks if task["success"])
    failed_tasks = len(completed_tasks) - successful_tasks

    print("\nSummary:")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Tasks completed successfully: {successful_tasks}")
    print(f"Tasks failed: {failed_tasks}")

@app.get("/summary")
def get_summary():
    """
    Возвращает сводную информацию о выполнении задач.
    """
    global start_time, end_time, completed_tasks
    if not end_time:
        raise HTTPException(status_code=400, detail="Tasks are still running.")
    
    total_time = end_time - start_time if end_time and start_time else 0
    successful_tasks = sum(1 for task in completed_tasks if task["success"])
    failed_tasks = len(completed_tasks) - successful_tasks
    
    return {
        "total_time": total_time,
        "successful_tasks": successful_tasks,
        "failed_tasks": failed_tasks
    }

def launch_parser():
    """
    Запускает парсер.
    """
    for task_num in range(10):
        semaphore.acquire()
        creds, host = next(proxies).split('@')
        login, password = creds.split(':')
        tasks.append({
            "id": str(uuid4()),
            "urls": ["https://www.feuvert.fr", "https://www.feuvert.fr/autoradio/pioneer-autoradio-video-mirroring-dmh-a240dab-pioneer/p612906.html"],
            'proxy': {
                'host': host,
                'login': login,
                'password': password
            }
        })
        print(f"Task {task_num} added")
        subprocess.Popen(["parser/RemoteExecuteScriptSilent.exe"])

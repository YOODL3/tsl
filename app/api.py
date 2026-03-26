import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.celery_app import celery_app
from celery.result import AsyncResult

router = APIRouter()

UPLOAD_DIR = "/app/data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    # 1. Save the file to the shared disk
    file_location = f"{UPLOAD_DIR}/{file.filename}"
    
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # 2. Tell Celery to start processing it in the background
    task = celery_app.send_task("app.worker.process_audio", args=[file_location])

    # 3. Return the ticket number immediately
    return {
        "message": "File uploaded and queued for transcription.",
        "filename": file.filename,
        "task_id": task.id
    }

@router.get("/status/{task_id}")
async def get_status(task_id: str):
    # Check Redis for the status of the job
    task_result = AsyncResult(task_id)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
    }
    
    if task_result.status == 'SUCCESS':
        response["result"] = task_result.result
    elif task_result.status == 'FAILURE':
        response["error"] = str(task_result.info)
        
    return response
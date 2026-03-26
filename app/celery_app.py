import os
from celery import Celery

# Pull the Redis URL from the environment (set in docker-compose)
# Fallback to localhost if running outside of Docker for testing
REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "transcription_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.worker"] # Tells Celery where to look for the tasks
)

# Optimize Celery for long-running audio tasks
celery_app.conf.update(
    task_track_started=True,
    task_serializer='json',
    worker_prefetch_multiplier=1 # Only grab one audio file at a time per GPU
)
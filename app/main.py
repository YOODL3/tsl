from fastapi import FastAPI
from app.api import router

app = FastAPI(
    title="Radio Station Transcription Speed Line",
    description="Internal tool for asynchronous WhisperX transcription",
    version="1.0.0"
)

# Bring in our upload and status endpoints
app.include_router(router)
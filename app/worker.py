import os
import json
import whisperx
from app.celery_app import celery_app

# 1. Load the models ONCE into GPU memory when the worker starts
device = "cuda" # Forces it to use the NVIDIA GPU
compute_type = "float16" # Optimizes VRAM usage
hf_token = os.getenv("HUGGINGFACE_TOKEN") # Required for speaker diarization

print("Loading WhisperX model into VRAM...")
model = whisperx.load_model("large-v3", device, compute_type=compute_type)

print("Loading Diarization model...")
diarize_model = whisperx.DiarizationPipeline(use_auth_token=hf_token, device=device)

TRANSCRIPT_DIR = "/app/data/transcripts"
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)


@celery_app.task(bind=True)
def process_audio(self, file_path: str):
    """The actual background job that chews through the audio."""
    try:
        # Step 1: Load audio
        self.update_state(state='PROGRESS', meta={'step': 'Loading audio'})
        audio = whisperx.load_audio(file_path)

        # Step 2: Transcribe (Fast)
        self.update_state(state='PROGRESS', meta={'step': 'Transcribing'})
        result = model.transcribe(audio, batch_size=16)

        # Step 3: Align timestamps
        self.update_state(state='PROGRESS', meta={'step': 'Aligning timestamps'})
        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
        result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)

        # Step 4: Diarize (Figure out who is speaking)
        self.update_state(state='PROGRESS', meta={'step': 'Diarizing speakers'})
        diarize_segments = diarize_model(audio)
        result = whisperx.assign_word_speakers(diarize_segments, result)

        # Step 5: Save the result
        base_name = os.path.basename(file_path).split('.')[0]
        output_file = f"{TRANSCRIPT_DIR}/{base_name}_transcript.json"
        
        with open(output_file, "w") as f:
            json.dump(result["segments"], f, indent=4)

        # Cleanup the raw audio file to save disk space if desired
        # os.remove(file_path)

        return {"message": "Success", "output_file": output_file}

    except Exception as e:
        # If it crashes, pass the error back to the API so the user knows
        raise Exception(f"Transcription failed: {str(e)}")
# 🎙️ Transcription Speed Line
An internal, high-throughput, asynchronous transcription tool built specifically for processing large volumes of radio audio.

It leverages WhisperX for highly accurate text transcription and forced alignment, alongside Pyannote for state-of-the-art speaker diarization (Speaker A / Speaker B). The system is built on an asynchronous task queue architecture to ensure the web server never hangs, even when processing hours of audio.

## 🚀 Features
100% Local / Open-Source: No expensive SaaS per-minute transcription fees.

Asynchronous Queue: FastAPI handles web traffic and file uploads instantly, while Celery and Redis manage the heavy GPU queue in the background.

Speaker Diarization: Accurately distinguishes between multiple hosts/guests.

Word-Level Timestamps: Maps every single word to exact millisecond timestamps.

Scalable: Need more speed? Just add another GPU worker container pointed at the same Redis queue.

## 🏗️ System Architecture
Frontend/API: A lightweight FastAPI container intercepts the .mp3/.wav upload, saves it to a shared disk, and hands the user a unique Job ID.

Message Broker: Redis acts as the "waiting room," keeping track of which files are next in line.

GPU Worker: A heavy PyTorch container running Celery watches the queue. When a GPU is free, it grabs the file, runs it through the WhisperX pipeline, and saves a JSON transcript.

## 🛠️ Prerequisites & Setup
### 1. Hardware & Docker Environment
To run this tool at "speed line" pace, you must have an NVIDIA GPU.

Install the latest NVIDIA Game Ready or Studio drivers on your Windows host.

Install Docker Desktop and ensure WSL 2 Integration is enabled in the settings.

Verify WSL2 can see your GPU by opening your terminal and running nvidia-smi.

### 2. Hugging Face Authentication (Crucial)
Pyannote's diarization models are "gated" by Hugging Face. You must authenticate to download them.

- Create a free account at Hugging Face.

- Generate a read-only Access Token at hf.co/settings/tokens.

- You MUST visit these three links while logged in, fill out the brief form, and click "Agree and access repository" on each: pyannote/speaker-diarization-3.1 pyannote/segmentation-3.0 pyannote/speaker-diarization-community-1

### 3. Environment Variables (Crucial)
For security reasons, the environment variables file is deliberately excluded from version control (`.gitignore`). **The pipeline will crash if you do not manually create this file.**

1. In the root folder of this project (next to `docker-compose.yml`), create a new text file and name it exactly `.env`
2. Open the file and add your Hugging Face token like this:
   ```env
   HUGGINGFACE_TOKEN=hf_your_long_token_string_here

## 💻 Installation & Running
Clone the repository:

Bash
git clone https://github.com/YOODL3/tsl
cd transcription-speed-line
Build and start the infrastructure:

Bash
docker-compose up --build
(Note: The very first time you run this, the worker will take a few minutes to download the 3GB AI models into VRAM. Wait until you see celery@transcription_worker ready in the terminal).

## 🎧 How to Use (API)
Once the containers are running, you can interact with the system via the auto-generated Swagger UI.

Open your browser and go to: http://localhost:8000/docs

To Transcribe: Expand the POST /upload endpoint. Upload an audio file and execute. It will return a unique task_id.

To Check Status: Expand the GET /status/{task_id} endpoint. Paste your ID to check if the job is PENDING, PROGRESS, or SUCCESS.

The Output: Once successful, the fully formatted transcript will be saved locally inside the data/transcripts/ directory.

## 📂 Project Structure

```text
transcription-speed-line/
├── app/
│   ├── __init__.py          # Marks folder as a module
│   ├── main.py              # FastAPI web server entry point
│   ├── api.py               # Upload and status routing logic
│   ├── celery_app.py        # Redis queue configuration
│   └── worker.py            # WhisperX / Pyannote GPU processing logic
├── data/
│   ├── uploads/             # Temporary holding zone for raw audio
│   └── transcripts/         # Final JSON/Text output zone
├── .env                     # Contains HUGGINGFACE_TOKEN (Ignored by Git)
├── requirements.txt         # Python dependencies
├── Dockerfile.api           # Builds the lightweight web server
├── Dockerfile.worker        # Builds the heavy PyTorch GPU worker
└── docker-compose.yml       # Orchestrates containers and GPU passthrough
```

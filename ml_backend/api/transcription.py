import sys
from multiprocessing import SimpleQueue, Process

from fastapi import FastAPI
from faster_whisper import WhisperModel

import os

from video_processing import run_command, delete, make_video_id, download_video

sys.setrecursionlimit(16385)

os.makedirs("./videos/", exist_ok=True)
os.makedirs("./audios/", exist_ok=True)


def extract_audio(video_url, audio_path):
    video_id = make_video_id(video_url)
    run_command([
        f'ffmpeg', '-y', '-i', f'./videos/{video_id}', '-vn',
        '-c:a', 'copy', audio_path
    ])


def transcribe(video_url: str, model: WhisperModel):
    video_id = make_video_id(video_url)
    download_video(video_url)
    audio_path = f"./audios/{video_id.replace('.mp4', '.m4a')}"
    extract_audio(video_url, audio_path)
    segments, info = model.transcribe(audio_path)
    delete(video_url)
    return " ".join(segment.text for segment in segments), info.all_language_probs[:2]


def load_model():
    return WhisperModel("small", cpu_threads=24)


def model_worker(queue: SimpleQueue):
    model = load_model()
    print("Whisper loaded")
    while url := queue.get():
        if url is None:
            print("Shutting down")
            break
        try:
            queue.put(transcribe(url, model))
        except:
            queue.put(f"Error while processing {url}")


transcription_queue = SimpleQueue()
app = FastAPI()


@app.post("/transcription")
def transcribe_url(video_url: str):
    transcription_queue.put(video_url)
    return transcription_queue.get()


ml_process: Process


@app.on_event("startup")
def startup():
    global ml_process
    ml_process = Process(target=model_worker, args=(transcription_queue,))
    ml_process.start()


@app.on_event("shutdown")
def shutdown_event():
    global ml_process
    transcription_queue.put(None)
    ml_process.terminate()

import sys
from multiprocessing import SimpleQueue, Process

from fastapi import FastAPI
from faster_whisper import WhisperModel
import logging
import os
from multiprocessing import Process, SimpleQueue
import sys

import scipy
from pydantic import BaseModel, Field
from fastapi import FastAPI

import tensorflow as tf
import tensorflow_hub as hub
import csv

from scipy.io import wavfile

import os

from video_processing import run_command, delete, make_video_id, download_video

sys.setrecursionlimit(16385)

os.makedirs("./videos/", exist_ok=True)
os.makedirs("./audios/", exist_ok=True)
os.makedirs("./audio_classification", exist_ok=True)

logger = logging.getLogger(__name__)


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
    return WhisperModel("small", cpu_threads=16)


def model_worker(queue: SimpleQueue):
    model = load_model()
    print("Whisper loaded")
    sys.stdout.flush()
    while url := queue.get():
        if url is None:
            print("Shutting down")
            break
        try:
            queue.put(transcribe(url, model))
        except Exception as e:
            print(e)
            sys.stdout.flush()
            queue.put(f"Error while processing {url}")


classification_queue = SimpleQueue()
transcription_queue = SimpleQueue()
app = FastAPI()


@app.post("/transcription")
def transcribe_url(video_url: str):
    classification_queue.put(video_url)

    classification_result = classification_queue.get()
    if classification_result.lower() not in ["speech", "Narration, monologue", 'children shouting', "conversation", ]:
        return classification_result

    transcription_queue.put(video_url)
    return transcription_queue.get()


ml_process: Process
audio_classification_process: Process


def ensure_sample_rate(original_sample_rate, waveform,
                       desired_sample_rate=16000):
    """Resample waveform if required."""
    if original_sample_rate != desired_sample_rate:
        desired_length = int(round(float(len(waveform)) /
                                   original_sample_rate * desired_sample_rate))
        waveform = scipy.signal.resample(waveform, desired_length)
    return desired_sample_rate, waveform


def get_audio_classification(url, model, class_names):
    video_id = make_video_id(url)
    audio_path = f'./audio_classification/{video_id.replace(".mp4", "")}.wav'
    run_command([
        f'ffmpeg', '-i', url,
        "-ac", "1",
        "-ar", "16000",
        "-y",
        audio_path
    ])
    if not os.path.exists(audio_path):
        logger.error(f"no audio for classification {url}")
        return "Error"
    sample_rate, wav_data = wavfile.read(audio_path, )
    sample_rate, wav_data = ensure_sample_rate(sample_rate, wav_data)
    waveform = wav_data / tf.int16.max
    scores, embeddings, spectrogram = model(waveform)
    scores_np = scores.numpy()
    return class_names[scores_np.mean(axis=0).argmax()]


def audio_worker(queue: SimpleQueue):
    model, class_names = load_audio_model()
    print("YAMNET loaded")
    sys.stdout.flush()
    while url := queue.get():
        try:
            queue.put(get_audio_classification(url, model, class_names))
        except Exception as e:
            logger.exception(e)
            queue.put("Error while processing text embedding")


app = FastAPI()


def load_audio_model():
    model = hub.load('https://tfhub.dev/google/yamnet/1')

    def class_names_from_csv(class_map_csv_text):
        """Returns list of class names corresponding to score vector."""
        class_names = []
        with tf.io.gfile.GFile(class_map_csv_text) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                class_names.append(row['display_name'])

        return class_names

    class_map_path = model.class_map_path().numpy()
    class_names = class_names_from_csv(class_map_path)
    return model, class_names


@app.on_event("startup")
def startup():
    global ml_process, audio_classification_process
    ml_process = Process(target=model_worker, args=(transcription_queue,))
    audio_classification_process = Process(target=audio_worker, args=(classification_queue,))
    audio_classification_process.start()
    ml_process.start()


@app.on_event("shutdown")
def shutdown_event():
    global ml_process, audio_classification_process
    transcription_queue.put(None)
    ml_process.terminate()
    classification_queue.put(None)
    audio_classification_process.terminate()

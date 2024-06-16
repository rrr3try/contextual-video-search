import logging
import os
from multiprocessing import Process, SimpleQueue
import sys

import scipy
from pydantic import BaseModel, Field
from fastapi import FastAPI

import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import csv

from scipy.io import wavfile

from video_processing import run_command, make_video_id

logger = logging.getLogger(__name__)
audio_classification_process: Process
os.makedirs("./audio_classification", exist_ok=True)


class AudioClassificationResponse(BaseModel):
    result: str = Field()
    is_success: bool


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


# def extract_audio():
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
    spectrogram_np = spectrogram.numpy()
    # infered_class =
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


#
#
#
app = FastAPI()
audio_queue = SimpleQueue()


#
#
@app.on_event("startup")
def startup():
    global audio_classification_process
    audio_classification_process = Process(target=audio_worker, args=(audio_queue,))
    audio_classification_process.start()


#
#
@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down process")
    audio_queue.put(None)
    audio_classification_process.terminate()


#
#
@app.post("/audio-classification")
def audio_classification(url: str) -> AudioClassificationResponse:
    audio_queue.put(url)
    result = audio_queue.get()
    if result != url:
        return AudioClassificationResponse(result=result, is_success=True)

# if __name__ == '__main__':
#     ...

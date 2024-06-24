import logging
from multiprocessing import Process, SimpleQueue, Queue
import sys
import torch
import transformers
from transformers import AutoModelForSeq2SeqLM, T5TokenizerFast
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from time import sleep
import re

logger = logging.getLogger(__name__)
text_embeddings_process: Process
video_embeddings_process: Process
device = "cuda" if torch.cuda.is_available() else "cpu"

class TextResponse(BaseModel):
    result: str
    is_success: bool

def load_text_correction_model():
    MODEL_NAME = 'UrukHan/t5-russian-spell'
    tokenizer = T5TokenizerFast.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    return model, tokenizer

def apply_text_correction(data, model, tokenizer):
    MAX_INPUT=256
    print("trying process", data)
    sys.stdout.flush()
    task_prefix = "Spell correct: "
    if type(data) != list: data = [data]
    encoded = tokenizer(
        [task_prefix + sequence for sequence in data],
        padding="longest",
        max_length=MAX_INPUT,
        truncation=True,
        return_tensors="pt",
    )
    predicts = model.generate(**encoded)
    result = tokenizer.batch_decode(predicts, skip_special_tokens=True)
    result = re.sub(r'[^a-zA-Z0-9a-яА-Я\s]', "", result[0])
    return result



def worker(input_queue: Queue, output_queue: Queue):
    model, tokenizer = load_text_correction_model()
    print("t5-russian-spell loaded")
    sys.stdout.flush()
    while text := input_queue.get():
        try:
            print("txt", text)
            sys.stdout.flush()
            output_queue.put(apply_text_correction(text, model, tokenizer), timeout=30)
        except Exception as e:
            print("txt", text)
            print("txt", type(text))
            print(e)
            logger.exception(e)
            sys.stdout.flush()
            # queue.put("Error while processing text embedding")

app = FastAPI()
text_queue = Queue()
text_queue_output = Queue()
video_queue = SimpleQueue()

@app.on_event("startup")
def startup():
    global text_correction_process
    text_correction_process = Process(target=worker, args=(text_queue, text_queue_output))
    text_correction_process.start()

@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down process")
    text_queue.put(None)
    text_correction_process.terminate()

@app.post("/text_correction")
def text_correction(text: str | None) -> TextResponse:
    if text is None or len(text) < 1:
        raise HTTPException(status_code=400)
    text_queue.put(text, block=False)
    sleep(0.1)
    result = text_queue_output.get(timeout=40)
    if result != text:
        return TextResponse(result=result, is_success=True)
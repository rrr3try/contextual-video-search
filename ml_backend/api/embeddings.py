import logging
import types
from multiprocessing import Process, SimpleQueue
import sys
import open_clip
import torch
import transformers
from PIL import Image
from multilingual_clip import pt_multilingual_clip
from pydantic import BaseModel, Field
from transformers.tokenization_utils_base import TruncationStrategy
from transformers.file_utils import PaddingStrategy
from fastapi import FastAPI

from video_processing import extract_images

logger = logging.getLogger(__name__)
audio_classification_process: Process
video_embeddings_process: Process
device = "cuda" if torch.cuda.is_available() else "cpu"


class EmbeddingResponse(BaseModel):
    result: list | None = Field(min_length=640, max_length=640)
    is_success: bool


def load_text_model():
    model_name = 'M-CLIP/XLM-Roberta-Large-Vit-B-16Plus'
    text_model = pt_multilingual_clip.MultilingualCLIP.from_pretrained(model_name, cache_dir="./mclip")
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_name, cache_dir="./mclip")

    tokenizer.set_truncation_and_padding(padding_strategy=PaddingStrategy("max_length"),
                                         truncation_strategy=TruncationStrategy("only_first"),
                                         max_length=512, stride=0,
                                         pad_to_multiple_of=None)

    # rewrite model.forward() method, to add truncation to the tokenizer
    def forward(self, txt, tokenizer_):
        txt_tok = tokenizer_(txt, padding=True, return_tensors='pt', truncation=True)
        embs = self.transformer(**txt_tok)[0]
        att = txt_tok['attention_mask']
        embs = (embs * att.unsqueeze(2)).sum(dim=1) / att.sum(dim=1)[:, None]
        return self.LinearTransformation(embs)

    text_model.forward = types.MethodType(forward, text_model)
    return text_model, tokenizer


def load_video_model():
    image_model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-16-plus-240', pretrained="laion400m_e32")
    image_model.to(device)
    return image_model, preprocess


def get_video_embeddings(url, image_model, preprocess):
    with torch.no_grad():
        for image_path in extract_images(url):
            image = Image.open(image_path)
            image = preprocess(image).unsqueeze(0).to(device)
            image_features = image_model.encode_image(image)
            print("Image features shape:", image_features.shape)
            return image_features[0].tolist()


def get_text_embeddings(data, text_model, tokenizer):
    return text_model.forward(data, tokenizer).detach().tolist()


# class Embeddings(BaseModel):
#     values: list = Field(min_length=)

def text_worker(queue: SimpleQueue):
    text_model, tokenizer = load_text_model()
    print("MClip text loaded")
    sys.stdout.flush()
    while text := queue.get():
        try:
            queue.put(get_text_embeddings(text, text_model, tokenizer)[0])
        except Exception as e:
            logger.exception(e)
            queue.put("Error while processing text embedding")


def video_worker(queue: SimpleQueue):
    image_model, preprocessing = load_video_model()
    print("MClip image loaded")
    sys.stdout.flush()
    while url := queue.get():
        try:
            queue.put(get_video_embeddings(url, image_model, preprocessing))
        except Exception as e:
            logger.exception(e)
            queue.put("Error while processing image(video) embedding")


app = FastAPI()
text_queue = SimpleQueue()
video_queue = SimpleQueue()


@app.on_event("startup")
def startup():
    global audio_classification_process, video_embeddings_process
    text_embeddings_process = Process(target=text_worker, args=(text_queue,))
    video_embeddings_process = Process(target=video_worker, args=(video_queue,))
    text_embeddings_process.start()
    video_embeddings_process.start()


@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down process")
    text_queue.put(None)
    video_queue.put(None)
    video_embeddings_process.terminate()
    audio_classification_process.terminate()


@app.post("/text_embeddings")
def text_embeddings(text: str) -> EmbeddingResponse:
    text_queue.put(text)
    result = text_queue.get()
    if result != text:
        return EmbeddingResponse(result=result, is_success=True)


@app.post("/video_embeddings")
def video_embeddings(url: str) -> EmbeddingResponse:
    video_queue.put(url)
    result = video_queue.get()
    if result != url:
        return EmbeddingResponse(result=result, is_success=True)

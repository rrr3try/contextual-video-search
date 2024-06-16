import logging
import os
import subprocess
from glob import glob

import requests
from pydantic import BaseModel


def run_command(command: list[str]):
    """ command example ["ffmpeg", "Hello, World!"] """

    process = subprocess.Popen(command,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode == 0:
        output = stdout.decode('utf-8').strip()
    else:
        output = stderr.decode()
        logging.error(output)

    return process.returncode, output


def delete(video_url):
    video_id = video_url.replace("https://cdn-st.rutubelist.ru/media/", "").replace("/", "-")
    os.remove(f"./videos/{video_id}")
    audio_id = video_id.replace(".mp4", ".m4a")
    os.remove(f"./audios/{audio_id}")


def make_video_id(video_url):
    return video_url.replace("https://cdn-st.rutubelist.ru/media/", "").replace("/", "-")


def download_video(video_url: str, save_path: str = None):
    if save_path is None:
        save_path = f"./videos/{make_video_id(video_url)}"
    with open(save_path, "wb") as fh:
        fh.write(requests.get(video_url).content)


def extract_images(video_url: str):
    video_id = make_video_id(video_url)
    run_command([
        f'ffmpeg', '-i', video_url,
        # '-vf', 'fps=1',
        '-vframes', '1',
        f'./thumbnails/{video_id.replace(".mp4", "")}%010d.jpg'
    ])
    # run_command([
    #     f'ffmpeg', '-i', video_path, '-vf',
    #     'thumbnail,select=gt(scene\,0.015)', '-vsync', 'vfr', '-r', '1',
    #     '-frame_pts', '1', '-frames:v', str(number_of_frames), f'./thumbnails/{video_id.replace(".mp4", "")}%010d.jpg'
    # ])
    return glob(f"./thumbnails/{video_id.replace('.mp4', '')}*.jpg")

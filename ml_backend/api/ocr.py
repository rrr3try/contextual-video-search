import logging
import os
from glob import glob
from multiprocessing import Process, SimpleQueue

from fastapi import FastAPI
from paddleocr import PaddleOCR
from pydantic import BaseModel
from video_processing import run_command, make_video_id, download_video

ocr_queue = SimpleQueue()
app = FastAPI()
ocr_process: Process
logger = logging.getLogger(__name__)


# ['https://cdn-st.rutubelist.ru/media/39/6c/b31bc6864bef9d8a96814f1822ca/fhd.mp4',
#  '🤫НЕ ВВОДИ ЭТУ КОМАНДУ В РОБЛОКС ! #shorts #roblox #роблокс']


class OCRResponse(BaseModel):
    result: str
    is_success: bool


@app.on_event("startup")
def startup():
    global ocr_process
    ocr_process = Process(target=ocr_worker, args=(ocr_queue,))
    ocr_process.start()


@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down OCR process")
    ocr_queue.put(None)
    ocr_process.terminate()


os.makedirs("./thumbnails/", exist_ok=True)
os.makedirs("./videos/", exist_ok=True)


@app.post("/ocr")
def ocr_video(video_url: str) -> OCRResponse:
    ocr_queue.put(video_url)
    result = ocr_queue.get()
    if result == video_url:
        return OCRResponse(result="Model not responding", is_success=False)
    return result


def extract_images(video_path: str):
    # number_of_frames = 10
    video_id = make_video_id(video_path)
    # print(" ".join([
    #     f'ffmpeg', '-i', video_path, '-vf',
    #     'fps=1',
    #     # "-vf", "crop=720:0:300:0",
    #     # 'vfr', '-r', '1',
    #     f'./thumbnails/{video_id.replace(".mp4", "")}%010d.jpg'
    # ]))
    run_command([
        f'ffmpeg', '-i', video_path, '-vf',
        'fps=1',
        # "-vf", "crop=720:0:300:0",
        # 'vfr', '-r', '1',
        f'./thumbnails/{video_id.replace(".mp4", "")}%010d.jpg'
    ])
    # run_command([
    #     f'ffmpeg', '-i', video_path, '-vf',
    #     'thumbnail,select=gt(scene\,0.015)', '-vsync', 'vfr', '-r', '1',
    #     '-frame_pts', '1', '-frames:v', str(number_of_frames), f'./thumbnails/{video_id.replace(".mp4", "")}%010d.jpg'
    # ])
    return glob(f"./thumbnails/{video_id.replace('.mp4', '')}*.jpg")


def ocr_worker(queue: SimpleQueue):
    ocr = PaddleOCR(use_angle_cls=True,
                    lang="ru",
                    rec_model_dir="./rec",
                    # ocr_version='PP-OCRv3',
                    # det_east_score_thresh=0.1,
                    # det_db_score_mode="slow",
                    # det_db_unclip_ratio=3,
                    # det_db_thresh=0.1,
                    # type='Truezz',
                    # table=False,
                    # binarize=True,
                    # drop_score=0.9,
                    # mode="rec",
                    # rec_algorithm="CRNN",
                    # rec_algorithm="SRN",
                    # rec_image_shape='3, 320, 48',
                    # image_orientation=True,
                    # e2e_algorithm="FFF"
                    # merge_no_span_structure=False,
                    )
    ("Namespace("

     "help='==SUPPRESS==', use_gpu=False, use_xpu=False, use_npu=False, ir_optim=True, use_tensorrt=False,"
     " min_subgraph_size=15, precision='fp32', gpu_mem=500, gpu_id=0, image_dir=None, page_num=0, det_algorithm='DB',"
     " det_model_dir='/root/.paddleocr/whl/det/ml/Multilingual_PP-OCRv3_det_infer', det_limit_side_len=960, "
     "det_limit_type='max', det_box_type='quad', det_db_thresh=0.3, det_db_box_thresh=0.6, det_db_unclip_ratio=1.5,"
     " max_batch_size=10, use_dilation=False, det_db_score_mode='fast', det_east_score_thresh=0.8,"
     " det_east_cover_thresh=0.1, det_east_nms_thresh=0.2, det_sast_score_thresh=0.5, det_sast_nms_thresh=0.2,"
     " det_pse_thresh=0, det_pse_box_thresh=0.85, det_pse_min_area=16, det_pse_scale=1, scales=[8, 16, 32], "
     "alpha=1.0, beta=1.0, fourier_degree=5, rec_algorithm='SVTR_LCNet', "
     "rec_model_dir='/root/.paddleocr/whl/rec/cyrillic/cyrillic_PP-OCRv3_rec_infer', rec_image_inverse=True, "
     "rec_image_shape='3, 48, 320', rec_batch_num=6, max_text_length=25,"
     " rec_char_dict_path='/usr/local/lib/python3.10/site-packages/paddleocr/ppocr/utils/dict/cyrillic_dict.txt',"
     " use_space_char=True, vis_font_path='./doc/fonts/simfang.ttf', drop_score=0.5, e2e_algorithm='PGNet', "
     "e2e_model_dir=None, e2e_limit_side_len=768, e2e_limit_type='max', e2e_pgnet_score_thresh=0.5, "
     "e2e_char_dict_path='./ru_dict.txt', e2e_pgnet_valid_set='totaltext', e2e_pgnet_mode='fast',"
     " use_angle_cls=True, cls_model_dir='/root/.paddleocr/whl/cls/ch_ppocr_mobile_v2.0_cls_infer', "
     "cls_image_shape='3, 48, 192', label_list=['0', '180'], cls_batch_num=6, cls_thresh=0.9, "
     "enable_mkldnn=False, cpu_threads=10, use_pdserving=False, warmup=False, sr_model_dir=None, "
     "sr_image_shape='3, 32, 128', sr_batch_num=1, draw_img_save_dir='./inference_results', "
     "save_crop_res=False, crop_res_save_dir='./output', use_mp=False, total_process_num=1, "
     "process_id=0, benchmark=False, save_log_path='./log_output/', show_log=True, use_onnx=False, "
     "output='./output', table_max_len=488, table_algorithm='TableAttn', table_model_dir=None, "
     "merge_no_span_structure=True, table_char_dict_path=None, layout_model_dir=None, layout_dict_path=None, "
     "layout_score_threshold=0.5, layout_nms_threshold=0.5, kie_algorithm='LayoutXLM', ser_model_dir=None,"
     " re_model_dir=None, use_visual_backbone=True, ser_dict_path='../train_data/XFUND/class_list_xfun.txt', "
     "ocr_order_method=None, mode='structure', image_orientation=False, layout=True, table=True, ocr=True, "
     "recovery=False, use_pdf2docx_api=False, invert=False, binarize=False, alphacolor=(255, 255, 255), lang='ru',"
     " det=True, rec=True, type='ocr', ocr_version='PP-OCRv4', structure_version='PP-StructureV2')")
    logger.info("PaddleOCR loaded", )
    while video_url := queue.get():
        try:
            # download_video(video_url)
            # extract_images(video_url)
            full_text = []
            for image_path in extract_images(video_url):
                results = ocr.ocr(image_path, cls=True)
                if results[0]:
                    for r in results[0]:
                        if r and r[1]:
                            text = r[1][0]
                            if text not in full_text:
                                full_text.append(text)
                    # full_text.extend(r[1][0] for r in results[0] if r and r[1])
            queue.put(OCRResponse(result=" ".join(full_text), is_success=True))
        except:
            logger.exception(video_url)
            queue.put(OCRResponse(result=f"Error while processing {video_url}", is_success=False))

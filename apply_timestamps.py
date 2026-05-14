import cv2
import os
import numpy as np
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "C:/Windows/Fonts/consola.ttf"
FONT_SIZE  = 48
OUTLINE    = 2   # 아웃라인 두께 (±px)
POS_X      = 10
POS_Y      = 25  # 기준 영상과 동일한 y 위치


def _get_font():
    try:
        return ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except OSError:
        return ImageFont.truetype("C:/Windows/Fonts/cour.ttf", FONT_SIZE)


def draw_timestamp(frame_bgr: np.ndarray, text: str, font) -> np.ndarray:
    """BGR numpy 프레임에 타임스탬프를 그리고 BGR로 반환."""
    # OpenCV BGR → PIL RGB
    pil = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil)

    # 8방향 검정 아웃라인
    for dx in range(-OUTLINE, OUTLINE + 1):
        for dy in range(-OUTLINE, OUTLINE + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((POS_X + dx, POS_Y + dy), text, font=font, fill=(0, 0, 0))

    # 흰 텍스트
    draw.text((POS_X, POS_Y), text, font=font, fill=(255, 255, 255))

    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)


def add_timestamp(video_path, target_date, target_time):
    print(f"Processing {video_path}...")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return

    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    output_path = video_path.replace(".mp4", "_temp.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out    = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    start_dt = datetime.strptime(f"{target_date} {target_time}", "%Y-%m-%d %H:%M:%S")
    font     = _get_font()

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 기존 타임스탬프 블러로 제거 (상단 y:0-90, x:0-800)
        frame[0:90, 0:800] = cv2.GaussianBlur(frame[0:90, 0:800], (31, 31), 0)

        current_time  = start_dt + timedelta(seconds=frame_count / fps)
        timestamp_str = current_time.strftime("%Y-%m-%d %H:%M:%S")

        frame = draw_timestamp(frame, timestamp_str, font)

        out.write(frame)
        frame_count += 1

        if frame_count % 100 == 0:
            print(f"  {frame_count}/{total} frames...")

    cap.release()
    out.release()

    if os.path.exists(output_path):
        os.remove(video_path)
        os.rename(output_path, video_path)
        print(f"  Done: {video_path}")
    else:
        print(f"  Error: output not created for {video_path}")


if __name__ == "__main__":
    base_dir = r"c:\The_searchlight\SearchLight\backend\static\mp4Data"

    tasks = [
        ("assault2.mp4", "2026-05-16", "14:15:30"),
        ("break1.mp4",   "2026-05-17", "15:30:45"),
        ("thief2.mp4",   "2026-05-18", "16:45:10"),
    ]

    for filename, date, time in tasks:
        path = os.path.join(base_dir, filename)
        if os.path.exists(path):
            add_timestamp(path, date, time)
        else:
            print(f"Warning: {path} not found.")

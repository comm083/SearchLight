import random
import numpy as np
from typing import Optional
import cv2

from .config import CFG


def sample_frames_uniform(video_path: str, num_frames: int) -> Optional[np.ndarray]:
    """영상에서 균일한 간격으로 num_frames개 프레임을 추출합니다."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames < 1:
        cap.release()
        return None

    if total_frames >= num_frames:
        indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
    else:
        indices = np.arange(total_frames)
        indices = np.pad(indices, (0, num_frames - total_frames), mode="wrap")
        indices = sorted(indices)

    frames = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ret, frame = cap.read()
        if not ret:
            if frames:
                frames.append(frames[-1].copy())
            else:
                frames.append(np.zeros((CFG.frame_size, CFG.frame_size, 3), dtype=np.uint8))
        else:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame)

    cap.release()
    return np.stack(frames)

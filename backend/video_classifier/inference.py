"""
단일 영상 추론 모듈.
makeJsonData.py에서 import하여 사용합니다.

사용 예:
    from video_classifier.inference import VideoClassifier
    classifier = VideoClassifier("video_classifier/checkpoints/best_model.pt")
    result = classifier.predict("clip.mp4")
    # {"label": "assault", "confidence": 0.91, "scores": {...}, "low_confidence": False}
"""

import torch
import torch.nn.functional as F
import numpy as np
from transformers import VideoMAEImageProcessor

from .config import CFG
from .dataset import sample_frames_uniform
from .model import load_checkpoint


class VideoClassifier:
    def __init__(self, checkpoint_path: str):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = VideoMAEImageProcessor.from_pretrained(CFG.model_name)
        self.model = load_checkpoint(checkpoint_path, self.device)
        self.model.eval()
        print(f"추론기 준비 완료 ({self.device})")

    @torch.no_grad()
    def predict(self, video_path: str) -> dict:
        """
        영상 1개를 분류합니다.

        Returns:
            {
                "label": str,
                "confidence": float,
                "scores": dict[str, float],
                "low_confidence": bool,
            }
        """
        frames = sample_frames_uniform(video_path, CFG.num_frames)
        if frames is None:
            return self._fallback(video_path)

        from PIL import Image
        pil_frames = [Image.fromarray(f) for f in frames]
        inputs = self.processor(pil_frames, return_tensors="pt")
        pixel_values = inputs["pixel_values"].to(self.device)

        from torch.cuda.amp import autocast
        with autocast(enabled=CFG.fp16):
            outputs = self.model(pixel_values=pixel_values)

        probs = F.softmax(outputs.logits, dim=-1).squeeze(0).cpu().float()
        confidence, pred_idx = probs.max(dim=0)
        confidence = confidence.item()
        label = CFG.id2label[pred_idx.item()]

        scores = {CFG.id2label[i]: round(probs[i].item(), 4) for i in range(CFG.num_classes)}

        return {
            "label": label,
            "confidence": round(confidence, 4),
            "scores": scores,
            "low_confidence": confidence < CFG.confidence_threshold,
        }

    def _fallback(self, video_path: str) -> dict:
        print(f"[경고] 영상 로드 실패: {video_path}")
        return {
            "label": "normal",
            "confidence": 0.0,
            "scores": {c: 0.0 for c in CFG.classes},
            "low_confidence": True,
        }


_classifier: VideoClassifier | None = None


def classify_video(video_path: str, checkpoint_path: str) -> dict:
    """
    전역 싱글턴 classifier를 사용해 영상을 분류합니다.
    첫 호출 시 모델을 로드하며 이후 호출은 재사용합니다.
    """
    global _classifier
    if _classifier is None:
        _classifier = VideoClassifier(checkpoint_path)
    return _classifier.predict(video_path)


if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from video_classifier.inference import classify_video as _classify

    if len(sys.argv) < 3:
        print("사용법: python -m video_classifier.inference <video_path> <checkpoint_path>")
        sys.exit(1)

    video = sys.argv[1]
    ckpt = sys.argv[2]
    result = _classify(video, ckpt)

    print(f"\n── 분류 결과 ──────────────────")
    print(f"  클래스    : {result['label']}")
    print(f"  신뢰도    : {result['confidence']:.4f}")
    print(f"  저신뢰도  : {result['low_confidence']}")
    print(f"  전체 점수 :")
    for cls, score in sorted(result["scores"].items(), key=lambda x: -x[1]):
        bar = "█" * int(score * 30)
        print(f"    {cls:<10} {score:.4f}  {bar}")

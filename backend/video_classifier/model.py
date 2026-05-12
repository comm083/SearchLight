import torch
import torch.nn as nn
from transformers import VideoMAEForVideoClassification

from .config import CFG


def build_model() -> VideoMAEForVideoClassification:
    model = VideoMAEForVideoClassification.from_pretrained(
        CFG.model_name,
        num_labels=CFG.num_classes,
        label2id=CFG.label2id,
        id2label=CFG.id2label,
        ignore_mismatched_sizes=True,
    )
    return model


def load_checkpoint(checkpoint_path: str, device: torch.device) -> VideoMAEForVideoClassification:
    model = build_model()
    state = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(state["model_state_dict"])
    model.to(device)
    model.eval()
    print(f"체크포인트 로드 완료: {checkpoint_path} (epoch {state.get('epoch', '?')}, val_acc {state.get('val_acc', '?'):.4f})")
    return model

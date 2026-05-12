from dataclasses import dataclass, field

@dataclass
class Config:
    # 데이터 경로
    data_dir: str = "data"
    except_dir: str = "except"
    max_per_class: int = 200
    output_dir: str = "outputs"
    checkpoint_dir: str = "checkpoints"

    # 클래스 정의
    classes: list = field(default_factory=lambda: [
        "falling", "break", "assault", "smoking",
        "disaster", "theft", "normal"
    ])

    # 영상 처리
    num_frames: int = 16
    frame_size: int = 224
    fps_sample: float = 1.0

    # 데이터 분할
    train_ratio: float = 0.8
    val_ratio: float = 0.1
    test_ratio: float = 0.1
    seed: int = 42

    # 학습
    model_name: str = "MCG-NJU/videomae-base"
    num_epochs: int = 30
    batch_size: int = 4
    learning_rate: float = 5e-5
    weight_decay: float = 1e-4
    warmup_ratio: float = 0.1
    fp16: bool = True
    grad_accumulation_steps: int = 4
    patience: int = 5

    # 추론
    confidence_threshold: float = 0.65

    @property
    def num_classes(self) -> int:
        return len(self.classes)

    @property
    def label2id(self) -> dict:
        return {c: i for i, c in enumerate(self.classes)}

    @property
    def id2label(self) -> dict:
        return {i: c for i, c in enumerate(self.classes)}


CFG = Config()

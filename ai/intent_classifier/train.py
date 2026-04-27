"""
KoELECTRA 의도 분류 모델 파인튜닝 학습 스크립트
실행 방법: python train.py (가상환경 활성화 후 실행)
"""
import os
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from dotenv import load_dotenv

load_dotenv()

# ────────────────────────────────────────────
# 1. 설정값
# ────────────────────────────────────────────
MODEL_NAME = "monologg/koelectra-base-v3-discriminator"
DATA_PATH = os.path.join(os.path.dirname(__file__), "intent_dataset.csv")
SAVE_DIR = os.path.join(os.path.dirname(__file__), "../../model/koelectra_finetuned")
NUM_LABELS = 5
EPOCHS = 5
BATCH_SIZE = 16
MAX_LEN = 64
LEARNING_RATE = 2e-5

LABEL_NAMES = {
    0: "조회 (SEARCH)",
    1: "위험 (EMERGENCY)",
    2: "장애 (ERROR)",
    3: "출입 (ACCESS)",
    4: "일상 (GENERAL)"
}

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[Train] 사용 디바이스: {device}")


# ────────────────────────────────────────────
# 2. 데이터셋 클래스
# ────────────────────────────────────────────
class IntentDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        encoding = self.tokenizer(
            self.texts[idx],
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels": torch.tensor(self.labels[idx], dtype=torch.long)
        }


# ────────────────────────────────────────────
# 3. 학습 함수
# ────────────────────────────────────────────
def train():
    # 학습 로그 저장을 위한 리스트
    history = []
    log_path = os.path.join(os.path.dirname(__file__), "training_log.csv")

    # 데이터 로드
    print(f"[Train] 데이터 로드 중: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    print(f"[Train] 총 {len(df)}건의 데이터 로드 완료")
    print(df["label"].value_counts().sort_index().to_string())

    texts = df["text"].tolist()
    labels = df["label"].tolist()

    # 학습/검증 분리 (80:20)
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    # 토크나이저 및 모델 로드
    print(f"\n[Train] 모델 로드 중: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=NUM_LABELS
    ).to(device)

    # DataLoader
    train_dataset = IntentDataset(train_texts, train_labels, tokenizer, MAX_LEN)
    val_dataset = IntentDataset(val_texts, val_labels, tokenizer, MAX_LEN)
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE)

    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)

    best_accuracy = 0.0

    # 학습 루프
    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0

        for batch in train_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            label_batch = batch["labels"].to(device)

            outputs = model(input_ids, attention_mask=attention_mask, labels=label_batch)
            loss = outputs.loss

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)

        # 검증
        model.eval()
        all_preds, all_labels = [], []
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                label_batch = batch["labels"].to(device)

                outputs = model(input_ids, attention_mask=attention_mask)
                preds = torch.argmax(outputs.logits, dim=1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(label_batch.cpu().numpy())

        accuracy = accuracy_score(all_labels, all_preds)
        print(f"[Epoch {epoch+1}/{EPOCHS}] Loss: {avg_loss:.4f} | Val Accuracy: {accuracy*100:.1f}%")

        # 최고 성능 모델 저장
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            os.makedirs(SAVE_DIR, exist_ok=True)
            model.save_pretrained(SAVE_DIR)
            tokenizer.save_pretrained(SAVE_DIR)
            print(f"  -> 모델 저장 완료! (현재 최고 정확도: {best_accuracy*100:.1f}%)")

        # 로그 기록 추가
        history.append({
            "epoch": epoch + 1,
            "loss": avg_loss,
            "accuracy": accuracy
        })

    # 학습 로그 CSV 저장
    df_log = pd.DataFrame(history)
    df_log.to_csv(log_path, index=False)
    print(f"\n[Train] 학습 로그가 저장되었습니다: {log_path}")


    # 최종 성능 리포트
    print("\n" + "="*50)
    print(f"학습 완료! 최종 최고 정확도: {best_accuracy*100:.1f}%")
    print("="*50)
    print("\n[분류 상세 리포트]")
    target_names = [LABEL_NAMES[i] for i in range(NUM_LABELS)]
    print(classification_report(all_labels, all_preds, target_names=target_names))
    print(f"\n학습된 모델 저장 위치: {os.path.abspath(SAVE_DIR)}")


if __name__ == "__main__":
    train()

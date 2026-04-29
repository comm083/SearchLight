import torch
import torch.nn.functional as F
from transformers import ElectraTokenizer, ElectraForSequenceClassification
from torch.utils.data import DataLoader, Dataset
from typing import Dict, List, Optional, Any

# 의도 분류 카테고리
INTENT_CLASSES = {
    0: "시간",      # 특정 시간/시간대 관련 질의
    1: "사람 수",   # 인원/건수 집계 질의
    2: "행동",      # 특정 행동/동작 관련 질의
    3: "정보 요약", # 데이터 요약/리포트 요청
    4: "오류 감지"  # 시스템/장비 이상 질의
}

class IntentDataset(Dataset):
    """의도 분류 학습을 위한 PyTorch Dataset"""
    def __init__(self, texts: List[str], labels: List[int], tokenizer: ElectraTokenizer, max_len: int = 128) -> None:
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, item):
        text = str(self.texts[item])
        label = self.labels[item]

        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt',
        )

        return {
            'text': text,
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

class IntentClassifier:
    """KoELECTRA 기반 의도 분류기"""
    def __init__(self, model_name: str = "monologg/koelectra-small-v3-discriminator", num_labels: int = 5) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = ElectraTokenizer.from_pretrained(model_name)
        self.model = ElectraForSequenceClassification.from_pretrained(model_name, num_labels=num_labels)
        self.model.to(self.device)
        self.num_labels = num_labels

    def train(self, train_texts: List[str], train_labels: List[int], epochs: int = 3, batch_size: int = 16, lr: float = 2e-5) -> None:
        """모델 학습 로직"""
        dataset = IntentDataset(train_texts, train_labels, self.tokenizer)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=lr)
        
        self.model.train()
        for epoch in range(epochs):
            total_loss = 0
            for batch in dataloader:
                optimizer.zero_grad()
                
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                outputs = self.model(input_ids, attention_mask=attention_mask, labels=labels)
                loss = outputs.loss
                
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            print(f"Epoch {epoch+1}/{epochs} - Loss: {total_loss/len(dataloader):.4f}")

    def predict(self, text: str) -> Dict[str, Any]:
        """질문 의도 확률값 반환 인퍼런스""""
        self.model.eval()
        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=128,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt',
        )
        
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        with torch.no_grad():
            outputs = self.model(input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            probs = F.softmax(logits, dim=1)
            
            confidence, predicted_class = torch.max(probs, dim=1)
            
        class_idx = predicted_class.item()
        
        return {
            "text": text,
            "intent_id": class_idx,
            "intent_label": INTENT_CLASSES[class_idx],
            "confidence": confidence.item(),
            "probabilities": {INTENT_CLASSES[i]: probs[0][i].item() for i in range(self.num_labels)}
        }
    
    def save_model(self, path: str) -> None:
        self.model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)
        
    def load_model(self, path: str) -> None:
        self.tokenizer = ElectraTokenizer.from_pretrained(path)
        self.model = ElectraForSequenceClassification.from_pretrained(path, num_labels=self.num_labels, use_safetensors=True)
        self.model.to(self.device)

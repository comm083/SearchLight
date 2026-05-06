import os
import torch
import torch.nn.functional as F
from transformers import ElectraTokenizer, ElectraForSequenceClassification
from torch.utils.data import DataLoader, Dataset
from ai.core.model_manager import model_manager

# 의도 분류 카테고리 (백엔드와 통일)
INTENT_CLASSES = {
    0: "COUNTING",      # 인원/건수 집계 질의
    1: "SUMMARIZATION", # 데이터 요약/리포트 요청
    2: "LOCALIZATION",  # 특정 위치/현재 상태 질의
    3: "BEHAVIORAL",    # 특정 행동/동작 관련 질의
    4: "CAUSAL"         # 사건 원인/인과 관계 질의
}

class IntentClassifier:
    """KoELECTRA 기반 의도 분류기"""
    def __init__(self, model_path="model/koelectra_finetuned", num_labels=5):
        self.device = model_manager.get_device()
        self.num_labels = num_labels
        self.model = None
        self.tokenizer = None
        
        # 모델 경로가 존재하면 자동 로드
        abs_path = model_manager.get_model_path(model_path)
        if os.path.exists(abs_path):
            self.load_model(abs_path)
        else:
            print(f"[IntentClassifier] 모델을 찾을 수 없어 기본 모드로 시작합니다: {abs_path}")

    def train(self, train_texts, train_labels, epochs=3, batch_size=16, lr=2e-5):
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

    def predict(self, text):
        """질문 의도 확률값 반환 인퍼런스"""
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
    
    def save_model(self, path):
        self.model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)
        
    def load_model(self, path):
        self.tokenizer = ElectraTokenizer.from_pretrained(path)
        self.model = ElectraForSequenceClassification.from_pretrained(path, num_labels=self.num_labels, use_safetensors=True)
        self.model.to(self.device)

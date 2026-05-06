import re
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from ai.core.model_manager import model_manager

# 모델과 토크나이저를 전역적으로 관리합니다.
_model = None
_tokenizer = None

def _get_model_and_tokenizer():
    """KoBART 교정 모델과 토크나이저를 지연 로딩합니다."""
    global _model, _tokenizer
    if _model is None or _tokenizer is None:
        try:
            # 더 정교한 한국어 문법 교정 모델 (theSOL1/kogrammar-distil) 사용
            model_id = "theSOL1/kogrammar-distil"
            _tokenizer = AutoTokenizer.from_pretrained(model_id)
            _model = AutoModelForSeq2SeqLM.from_pretrained(model_id)
            _model.to(model_manager.get_device())
        except Exception as e:
            print(f"Error loading KoBART model: {e}")
            return None, None
    return _model, _tokenizer

def correct_stt_text(stt_text: str) -> str:
    """
    STT로 인식된 텍스트의 오류를 교정하고 자연스러운 문장으로 완성합니다.
    향후 LLM (GPT, KoBART 등) API나 모델을 연동하여 고도화할 수 있습니다.
    
    Args:
        stt_text (str): STT에서 출력된 원본 불완전 텍스트
        
    Returns:
        str: 문법 및 문맥에 맞게 교정/완성된 텍스트
    """
    if not stt_text or not stt_text.strip():
        return ""
        
    corrected_text = stt_text.strip()
    
    # 1. 룰 기반 텍스트 교정 (사전 기반 예시)
    # CCTV 도메인에서 자주 오인식되는 단어 매핑
    correction_dict = {
        "씨씨티비": "CCTV",
        "빨간색 오슬": "빨간색 옷을",
        "노랑 오슬": "노란 옷을",
        "노란색 오슬": "노란색 옷을",
        "검은색 오슬": "검은색 옷을",
        "파란색 오슬": "파란색 옷을",
        "하얀색 오슬": "하얀색 옷을",
        "찍킨게": "찍힌 게",
        "찍킨": "찍힌",
        "도둑이 드렀어": "도둑이 들었어",
        "찾아조": "찾아줘",
        "보여조": "보여줘",
    }
    
    for wrong, right in correction_dict.items():
        corrected_text = corrected_text.replace(wrong, right)
        
    # 2. 간단한 문맥 교정 및 종결어미 처리
    # 예: "사람 찾아" -> "사람 찾아줘"
    if corrected_text.endswith("찾아"):
        corrected_text += "줘"
    elif corrected_text.endswith("보여"):
        corrected_text += "줘"
        
    # 특수문자나 불필요한 공백 제거
    corrected_text = re.sub(r'\s+', ' ', corrected_text)
    
    # 3. KoBART 모델을 이용한 고도화 교정
    model, tokenizer = _get_model_and_tokenizer()
    if model and tokenizer:
        try:
            # 모델 입력 준비
            input_ids = tokenizer.encode(corrected_text, return_tensors="pt").to(model_manager.get_device())
            
            # 문장 생성 (교정 수행)
            outputs = model.generate(
                input_ids, 
                max_length=64, 
                num_beams=5,
                repetition_penalty=1.2,
                no_repeat_ngram_size=3,
                early_stopping=True
            )
            
            # 결과 디코딩 및 정제
            # skip_special_tokens=False로 읽어서 특수 토큰 위치를 확인합니다.
            raw_text = tokenizer.decode(outputs[0], skip_special_tokens=False)
            
            # </s>, <s> 등 기본 토큰 제거 후 <pad>나 <unused> 토큰이 나오면 그 이전까지만 사용
            # (일부 모델은 교정 결과 뒤에 태그나 패딩을 붙이는 경우가 있음)
            corrected_text = raw_text.replace('</s>', '').replace('<s>', '')
            if '<pad>' in corrected_text:
                corrected_text = corrected_text.split('<pad>')[0]
            if '<unused' in corrected_text:
                corrected_text = corrected_text.split('<unused')[0]
                
            # 추가적인 노이즈 제거 (문장 끝 이후의 불필요한 문자들)
            corrected_text = corrected_text.strip()
            
            # 최종적으로 한글, 숫자, 일반 문장부호 이외의 이상한 기호가 섞여있다면 정제
            corrected_text = re.sub(r'[^가-힣0-9a-zA-Z\s\?\!\.\,\(\)\"\'\:\-]', '', corrected_text)
            corrected_text = corrected_text.strip()
        except Exception as e:
            print(f"Error during KoBART correction: {e}")
    
    return corrected_text

import re

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
    
    # 향후 NLP 고도화 부분:
    # --------------------------------------------------------
    # from transformers import pipeline
    # corrector = pipeline("text2text-generation", model="선택한_교정_모델")
    # corrected_text = corrector(corrected_text)[0]['generated_text']
    # --------------------------------------------------------
    
    return corrected_text

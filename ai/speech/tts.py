from gtts import gTTS
import os

def perform_tts(text: str, output_file_path: str, language: str = "ko") -> bool:
    """
    텍스트를 음성 파일로 변환합니다. (Text-to-Speech)
    
    Args:
        text (str): 변환할 텍스트
        output_file_path (str): 저장할 오디오 파일 경로 (예: output.mp3)
        language (str): 음성 언어 코드 (기본값: 한국어 'ko')
        
    Returns:
        bool: 변환 및 저장 성공 여부
    """
    try:
        if not text or not text.strip():
            print("TTS: 변환할 텍스트가 없습니다.")
            return False
            
        # gTTS 객체 생성 및 파일 저장
        tts = gTTS(text=text.strip(), lang=language, slow=False)
        tts.save(output_file_path)
        
        return os.path.exists(output_file_path)
        
    except Exception as e:
        print(f"TTS: 처리 중 오류 발생 - {e}")
        return False

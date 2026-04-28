import speech_recognition as sr

def perform_stt(audio_file_path: str, language: str = "ko-KR") -> str:
    """
    오디오 파일을 텍스트로 변환합니다. (Speech-to-Text)
    
    Args:
        audio_file_path (str): 오디오 파일의 경로 (예: .wav 파일)
        language (str): 인식할 언어 코드 (기본값: 한국어 'ko-KR')
        
    Returns:
        str: 인식된 텍스트. 실패 시 빈 문자열 반환.
    """
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file_path) as source:
            # 노이즈 조절 등 필요한 전처리 추가 가능
            recognizer.adjust_for_ambient_noise(source)
            audio_data = recognizer.record(source)
            
            # Google Web Speech API 사용 (기본 제공)
            # 향후 Whisper 등 다른 모델로 교체 가능
            text = recognizer.recognize_google(audio_data, language=language)
            return text
            
    except sr.UnknownValueError:
        print("STT: 음성을 명확히 인식할 수 없습니다.")
        return ""
    except sr.RequestError as e:
        print(f"STT: 서비스 요청 오류 - {e}")
        return ""
    except Exception as e:
        print(f"STT: 알 수 없는 오류 발생 - {e}")
        return ""

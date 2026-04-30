import { useState, useRef } from 'react';

export const useVoice = (onResult) => {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const startListening = async () => {
    if (isListening) {
      stopListening();
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await sendAudioToBackend(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsListening(true);
      window.speechSynthesis?.cancel();
      setIsSpeaking(false);
    } catch (err) {
      console.error("마이크 접근 실패:", err);
      alert("마이크 접근 권한이 필요합니다.");
    }
  };

  const stopListening = () => {
    if (mediaRecorderRef.current && isListening) {
      mediaRecorderRef.current.stop();
      setIsListening(false);
    }
  };

  const sendAudioToBackend = async (blob) => {
    const formData = new FormData();
    formData.append('file', blob, 'recording.wav');

    try {
      const response = await fetch('http://localhost:8000/api/stt', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (data.status === 'success' && data.text) {
        onResult(data.text);
      }
    } catch (error) {
      console.error("STT 요청 실패:", error);
    }
  };

  const speak = (text) => {
    if (!window.speechSynthesis || !text) return;
    window.speechSynthesis.cancel();
    const cleanText = text
      .replace(/\*\*?(.*?)\*\*?/g, '$1')                      // **bold** / *italic*
      .replace(/#{1,6}\s?/g, '')                               // ## 헤더
      .replace(/[_~`>|]/g, '')                                 // 나머지 마크다운 기호
      .replace(/[\u{1F000}-\u{1FFFF}]/gu, '')                  // 이모지 (보조 평면)
      .replace(/[\u{2600}-\u{27BF}]/gu, '')                    // 기호·돋보기·화살표 등
      .replace(/[\u{FE00}-\u{FEFF}]/gu, '')                    // variation selector
      .replace(/\n{2,}/g, '. ')                                // 빈 줄 → 문장 구분
      .replace(/\n/g, ' ')
      .trim();
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'ko-KR';
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    window.speechSynthesis.speak(utterance);
  };

  return { isListening, isSpeaking, startListening, stopListening, speak };
};

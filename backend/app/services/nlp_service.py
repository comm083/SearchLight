import os
import sys
from openai import OpenAI
from app.core.config import settings

# 프로젝트 루트를 경로에 추가 (ai 모듈 접근용)
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# AI 모듈 선택적 로드
try:
    from ai.nlp.sentence_correction import correct_stt_text as _correct_stt_text
    _HAS_KOBART = True
except Exception:
    _HAS_KOBART = False

try:
    from ai.intent_classifier.classifier import IntentClassifier as _IntentClassifier
    _HAS_KOELECTRA = True
except Exception:
    _HAS_KOELECTRA = False


class NLPService:
    def __init__(self):
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            print("[Warning] OPENAI_API_KEY가 설정되지 않았습니다. AI 보고서 기능이 비활성화됩니다.")
            self.client = None
            return
        self.client = OpenAI(api_key=api_key)

        # KoELECTRA 의도 분류기 초기화 (선택적)
        self._koelectra = None
        if _HAS_KOELECTRA:
            try:
                clf = _IntentClassifier()
                model_path = os.path.join(_project_root, "model", "koelectra_finetuned")
                if os.path.exists(model_path):
                    clf.load_model(model_path)
                    print(f"[NLP] KoELECTRA 학습 모델 로드 완료: {model_path}")
                else:
                    print("[NLP] KoELECTRA 기본(사전학습) 모델 사용 중.")
                self._koelectra = clf
            except Exception as e:
                print(f"[NLP] KoELECTRA 로드 실패 (규칙 기반으로 대체): {e}")

        # KoBART 모델 사전 로딩 (비동기 처리 중 데드락 방지)
        if _HAS_KOBART:
            try:
                from ai.nlp.sentence_correction import _get_model_and_tokenizer
                print("[NLP] KoBART 문법 교정 모델 사전 로딩 중 (최초 다운로드 시 시간이 걸릴 수 있습니다)...")
                _get_model_and_tokenizer()
                print("[NLP] KoBART 모델 로딩 완료!")
            except Exception as e:
                print(f"[NLP] KoBART 로딩 실패: {e}")

        print("[Service] OpenAI NLP 서비스 초기화 완료!")

    def generate_security_report(self, query: str, contexts: list, intent: str = "SUMMARIZATION", is_fallback: bool = False, requested_time: str = "알 수 없는 시간", mode: str = "summary", start_time: str = None, end_time: str = None, conversation_history: list = None):
        """검색된 장면들을 바탕으로 자연어 보안 보고서를 생성합니다."""
        if not self.client:
            return "AI 보고서 기능이 비활성화 상태입니다. (OpenAI API 키 필요)"

        if not contexts:
            return f"죄송합니다. 요청하신 {requested_time} 근처에는 기록된 보안 이벤트가 없습니다."

        context_text = self._build_context_text(contexts)
        fallback_notice = self._get_fallback_notice(is_fallback, requested_time)
        system_prompt = self._get_system_prompt(mode)
        specific_instruction = self._get_intent_instruction(intent)

        date_range = ""
        if start_time and end_time:
            date_range = f" (실제 조회 기간: {start_time[:10]} ~ {end_time[:10]})"
        elif start_time:
            date_range = f" (실제 조회 기간: {start_time[:10]} 이후)"

        user_prompt = f"""
{fallback_notice}
의도: {intent} ({specific_instruction})
사용자 질문: {query}
요청 시각: {requested_time}{date_range}
실제 데이터: {context_text}

[작성 지침]:
{self._get_writing_guidelines(mode)}
"""
        try:
            report = self._call_llm(system_prompt, user_prompt, history=conversation_history)
            is_valid, corrected_report = self._verify_report(report, requested_time, context_text)
            
            if not is_valid:
                print(f"[NLP Service] 사실 관계 모순 감지! 재교정 수행 중...")
                retry_prompt = f"{system_prompt}\n\n[🚨 재교정 요청] 방금 생성된 보고서에서 날짜나 사실 관계 오류가 발견되었습니다. 실제 데이터 시점과 요청 시점을 엄격히 구분하여 다시 작성해 주세요."
                report = self._call_llm(retry_prompt, user_prompt)
                _, final_report = self._verify_report(report, requested_time, context_text, force_warning=True)
                return final_report
                
            return corrected_report

        except Exception as e:
            print(f"[NLP Error] AI 보고서 생성 중 오류: {e}")
            return "보안 보고서를 생성하는 동안 기술적인 문제가 발생했습니다. 잠시 후 다시 시도해 주세요."

    def _build_context_text(self, contexts: list) -> str:
        from datetime import timezone as _tz
        import re
        items = []
        for c in contexts:
            desc = c.get('description', '설명 없음')
            ts_raw = c.get('timestamp') or c.get('event_date') or ''

            date_label = ''
            time_label = ''

            if ts_raw:
                try:
                    from datetime import datetime as _dt, timezone as _tz, timedelta as _td
                    dt = _dt.fromisoformat(str(ts_raw).replace('Z', '+00:00'))
                    kst = _tz(_td(hours=9))
                    dt_kst = dt.astimezone(kst)
                    date_label = f"[{dt_kst.strftime('%Y-%m-%d')}]"
                    h = dt_kst.hour
                    ampm = '오전' if h < 12 else '오후'
                    h12 = 12 if h == 0 else (h if h <= 12 else h - 12)
                    time_label = f"[{ampm} {h12}:{dt_kst.strftime('%M:%S')}]"
                except Exception:
                    ts_str = str(ts_raw)
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', ts_str)
                    if date_match:
                        date_label = f"[{date_match.group(1)}]"
                    time_match = re.search(r'(\d{1,2}):(\d{2}):(\d{2})', ts_str)
                    if time_match:
                        h, mi, s = int(time_match.group(1)), time_match.group(2), time_match.group(3)
                        ampm = '오전' if h < 12 else '오후'
                        h12 = 12 if h == 0 else (h if h <= 12 else h - 12)
                        time_label = f"[{ampm} {h12}:{mi}:{s}]"
            
            ts_display = f"{date_label} {time_label}".strip()
            dets = c.get('detections', [])
            det_text = ", ".join([f"[{d['time']}] {d['description']}" for d in dets]) if dets else "상세 정보 없음"
            
            if ts_display:
                items.append(f"시점: {ts_display} | 장면: {desc} | 상세: {det_text}")
            else:
                items.append(f"장면: {desc} | 상세: {det_text}")
        return "\n".join([f"- {item}" for item in items])

    def _get_fallback_notice(self, is_fallback: bool, requested_time: str) -> str:
        if not is_fallback: return ""
        return f"⚠️ [중요]: 요청하신 '{requested_time}'에 해당하는 데이터가 없어 가장 인접한 최신 데이터를 사용했습니다. 보고서 서두에 이 사실을 명시하세요.\n"

    def _get_system_prompt(self, mode: str) -> str:
        if mode == "flash":
            return "당신은 보안 분석관입니다. 특정 시점의 핵심 상황을 1~2문장으로 즉답하세요. 타임스탬프를 문장 끝에 포함하세요. (예: '...포착되었습니다. [13:05]') 제공된 데이터에 관련 정보가 없으면 '관련 기록이 없습니다.'라고만 답하세요."
        return "당신은 지능형 CCTV 보안 분석 AI '서치라이트'의 전문 분석관입니다. 제공된 실제 데이터를 기반으로 1~2문장 내외로 간결하게 보고하며, 관련 데이터가 없을 시 절대 상상해서 지어내지 않습니다."

    def _get_intent_instruction(self, intent: str) -> str:
        instructions = {
            "COUNTING": "발견된 인물, 차량 등의 수량을 정확히 파악하여 요약해 주세요.",
            "CAUSAL": "사건의 원인과 경위를 논리적으로 추론하여 상세히 기술해 주세요.",
            "BEHAVIORAL": "이상 행동의 위험 요소를 보안 관점에서 중점적으로 분석해 주세요.",
            "SUMMARIZATION": "전반적인 상황을 시간 순서대로 요약하는 데 집중해 주세요.",
            "LOCALIZATION": "현재 위치와 상태를 확인하는 데 집중해 주세요."
        }
        return instructions.get(intent, instructions["SUMMARIZATION"])

    def _get_writing_guidelines(self, mode: str) -> str:
        if mode == "flash": return "1. 핵심 상황 즉답. 2. 타임스탬프 포함. 3. 데이터가 없으면 '관련 정보가 없습니다.' 응답. 4. 상상/추측 금지. 5. 맺음말 생략."
        return """1. 📌 상황 요약, 🔍 핵심 분석, 🚨 위험 및 조치 섹션만 사용.
2. 📌 상황 요약 섹션은 반드시 각 이벤트를 별도 줄에 "[오전/오후 HH:MM:SS] 내용" 형식으로 나열할 것. (예: [오전 9:30:00] 손님이 음료 냉장고 앞에서 제품을 고르고 있습니다.) 절대 하나의 통합 문장으로 합치지 말 것.
3. 실제 데이터의 타임스탬프를 그대로 사용하며 절대 임의로 변경하지 말 것.
4. 🔍 핵심 분석, 🚨 위험 및 조치 섹션은 각각 최대 2문장.
5. [핵심] 제공된 [실제 데이터]에 질문에 대한 답변 정보가 전혀 없다면 절대 상상해서 지어내지 말고, '요청하신 정보와 관련된 기록이 없습니다'라고 명확히 답변할 것.
6. 맺음말 절대 금지."""

    def _call_llm(self, system_prompt: str, user_content: str, history: list = None) -> str:
        """LLM 호출 공통 로직 — history가 있으면 다중 턴 컨텍스트로 주입"""
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history[-6:])  # 최근 3턴만 포함 (토큰 절약)
        messages.append({"role": "user", "content": user_content})
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.2,
        )
        return response.choices[0].message.content

    def _verify_report(self, report: str, requested_time: str, context: str, force_warning: bool = False) -> tuple[bool, str]:
        """보고서의 사실 관계를 검증합니다."""
        import re
        actual_dates = set(re.findall(r"\d+월 \d+일", context))
        req_date_match = re.search(r"\d+월 \d+일", requested_time)
        req_date = req_date_match.group(0) if req_date_match else None
        
        is_valid = True
        if req_date and req_date not in actual_dates:
            suspicious_patterns = [
                f"{req_date}(에|은|는) .* (있었습니다|발생했습니다|포착되었습니다|기록되었습니다|확인되었습니다)"
            ]
            for pattern in suspicious_patterns:
                if re.search(pattern, report):
                    is_valid = False
                    break
        
        if not is_valid or force_warning:
            warning_msg = "\n\n> ⚠️ **검증 알림**: 본 보고서는 요청하신 시간대의 데이터가 존재하지 않아 시스템에서 검색된 가장 인접한 데이터 기반으로 작성되었습니다."
            if warning_msg not in report:
                report += warning_msg
                
        return is_valid, report

    def preprocess_query(self, query: str) -> dict:
        """
        쿼리 전처리: 문장 교정 후 FAISS 검색용 최적 쿼리 반환
        Returns: {"corrected": str, "best_query": str}
        """
        # KoBART 교정 시도
        corrected = query
        if _HAS_KOBART:
            try:
                corrected = _correct_stt_text(query) or query
            except Exception as e:
                print(f"[NLP] KoBART 교정 실패: {e}")

        return {
            "corrected": corrected,
            "best_query": corrected,
        }

    def transcribe_audio(self, file_path: str) -> str:
        """OpenAI Whisper를 사용한 음성 인식"""
        if not self.client:
            raise RuntimeError("OpenAI API 키가 설정되지 않았습니다.")
        with open(file_path, "rb") as f:
            result = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="ko"
            )
        return result.text

    def generate_ood_response(self, user_query: str):
        """
        보안과 관련 없는 질문(Out-of-Distribution)에 대해 친절하게 거절하며 가이드를 제공합니다.
        """
        if not self.client:
            return "안녕하세요, 저는 지능형 보안 분석관 SearchLight입니다.\n보안 및 관제 관련 질문이 있으시면 언제든지 말씀해 주세요.\n도움이 필요하신 부분에 대해 전문적으로 안내해 드리겠습니다."
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """너는 SearchLight라는 지능형 CCTV 보안 분석 AI야. 
사용자로부터 보안과 관련 없는 일상적인 질문을 받으면, 자신을 '지능형 보안 분석관 SearchLight'로 소개하며 보안 및 관제 관련 질문을 해달라고 전문적인 톤으로 요청해줘.
인삿말은 반드시 아래와 같이 한 문장씩 줄바꿈하여 포함해야 해:
"안녕하세요, 저는 지능형 보안 분석관 SearchLight입니다.
보안 및 관제 관련 질문이 있으시면 언제든지 말씀해 주세요.
도움이 필요하신 부분에 대해 전문적으로 안내해 드리겠습니다."

원활한 분석을 위해 사용자가 어떤 질문을 할 수 있는지 아래 가이드를 반드시 포함해줘:

💡 **질문 가이드:**
- **특정 인물/차량 검색** (예: '빨간색 옷을 입은 사람 찾아줘', '흰색 SUV 차량 포착됐어?')
- **보안 상황 요약** (예: '어제 밤 10시 이후 주차장 상황 요약해줘')
- **실시간 상태 확인** (예: '지금 정문에 특이사항 있어?')

답변은 간결하면서도 신뢰감 있는 전문적인 어조를 유지해줘."""},
                    {"role": "user", "content": f"사용자 질문: {user_query}"}
                ],
                max_tokens=350,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return (
                "안녕하세요, 저는 지능형 보안 분석관 SearchLight입니다.\n"
                "보안 및 관제 관련 질문이 있으시면 언제든지 말씀해 주세요.\n"
                "도움이 필요하신 부분에 대해 전문적으로 안내해 드리겠습니다.\n\n"
                "💡 **질문 가이드:**\n"
                "- **특정 인물/차량 검색** (예: '빨간색 옷을 입은 사람 찾아줘', '흰색 SUV 차량 포착됐어?')\n"
                "- **보안 상황 요약** (예: '어제 밤 10시 이후 주차장 상황 요약해줘')\n"
                "- **실시간 상태 확인** (예: '지금 정문에 특이사항 있어?')"
            )


# 싱글톤 인스턴스 생성
nlp_service = NLPService()

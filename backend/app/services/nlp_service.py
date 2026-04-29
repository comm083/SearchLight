import os
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

class NLPService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("[Warning] OPENAI_API_KEY가 설정되지 않았습니다. AI 보고서 기능이 비활성화됩니다.")
            self.client = None
            return
        self.client = OpenAI(api_key=api_key)
        print("[Service] OpenAI NLP 서비스 초기화 완료!")

    def generate_security_report(self, query: str, contexts: list, intent: str = "SUMMARIZATION", is_fallback: bool = False, requested_time: str = "알 수 없는 시간", mode: str = "summary"):
        """
        검색된 장면들(contexts)을 바탕으로 의도(intent)에 맞는 자연어 보안 보고서를 생성합니다.
        """
        if not self.client:
            return "AI 보고서 기능이 비활성화 상태입니다. (OpenAI API 키 필요)"
        
        if not contexts:
            return f"죄송합니다. 요청하신 {requested_time} 근처에는 기록된 보안 이벤트가 없습니다."

        # 검색된 장면들의 프레임별 상세 묘사를 컨텍스트로 사용
        context_items = []
        for c in contexts:
            desc = c.get('description', '설명 없음')
            dets = c.get('detections', [])
            det_text = ", ".join([f"[{d['time']}] {d['description']}" for d in dets]) if dets else "상세 정보 없음"
            context_items.append(f"장면 요약: {desc} | 상세 타임라인: {det_text}")
            
        context_text = "\n".join([f"- {item}" for item in context_items])
        
        fallback_notice = ""
        if is_fallback:
            fallback_notice = f"⚠️ [중요 안내]: 사용자가 요청한 '{requested_time}'에 해당하는 검색 결과가 전혀 없습니다. 따라서 시스템이 보유한 가장 유사하거나 최신의 데이터를 대신 가져왔습니다. 보고서 서두에 '요청하신 {requested_time}에는 기록이 없으나, 대신 가장 근접한 데이터를 기반으로 분석한 결과입니다'라는 내용을 반드시 포함하세요.\n"

        # 의도별 맞춤 지침
        intent_instructions = {
            "COUNTING": "사용자가 개체 수를 궁금해하므로, 검색된 장면들에서 발견된 인물, 차량 등의 수량을 정확히 파악하여 보고서 서두에 요약해 주세요. (예: '총 3명의 인물이 포착되었습니다.')",
            "CAUSAL": "사건의 원인과 경위를 분석하는 것이 목표입니다. 왜 이런 상황이 발생했는지, 이전 장면과 어떤 연관이 있는지 논리적으로 추론하여 '주요 분석' 섹션에 상세히 기술해 주세요.",
            "BEHAVIORAL": "이상 행동 탐지가 핵심입니다. 인물의 움직임이 왜 수상한지(예: 주변을 살핌, 담을 넘으려 함) 보안 관점에서 위험 요소를 중점적으로 분석해 주세요.",
            "SUMMARIZATION": "전반적인 상황을 시간 순서대로 요약하는 데 집중해 주세요.",
            "LOCALIZATION": "현재 위치와 상태를 확인하는 데 집중해 주세요."
        }
        
        specific_instruction = intent_instructions.get(intent, intent_instructions["SUMMARIZATION"])

        if mode == "flash":
            # ⚡ [신규] 특정 시점용 즉답 프롬프트
            system_prompt = f"""당신은 보안 분석관입니다. 사용자가 특정 시점을 콕 집어 물어봤으므로, 
            보고서 형식을 완전히 생략하고 1~2문장으로 해당 시점의 핵심 상황을 즉답하세요. 
            존댓말을 사용하며, 반드시 타임스탬프를 문장 끝에 포함하세요. 
            (예: "당시 13시 05분경 주차장에서 검정 옷 인물이 담을 넘는 것이 포착되었습니다. [13:05]")
            절대 "분석 완료"와 같은 맺음말을 쓰지 마세요."""
        else:
            # 📊 [기본] 요약 보고서용 프롬프트
            system_prompt = "당신은 지능형 CCTV 보안 분석 AI '서치라이트'의 전문 보안 분석관입니다. 가독성을 위해 불필요한 미사여구를 제거하고, 핵심 정보만 1~2문장 내외로 매우 간결하게 보고합니다."

        user_prompt = f"""
{fallback_notice}
의도: {intent} ({specific_instruction})
사용자 질문: {query}
요청 시각: {requested_time}
실제 데이터: {context_text}

[작성 지침 - 매우 중요]:
"""
        if mode != "flash":
            user_prompt += """
1. 반드시 아래의 3가지 섹션만 사용하여 **최대한 짧고 간결하게** 작성하세요.
   - 📌 **상황 요약**: 현재 상황을 1문장으로 요약
   - 🔍 **핵심 분석**: 포착된 주요 장면과 특징을 1~2문장으로 요약 (상세 타임라인 근거)
   - 🚨 **위험 및 조치**: 위험 수준(낮음~긴급)과 필요한 조치 제언. (단, 위험 수준이 **'낮음'**인 경우에는 "추가 감시 및 신고 필요"와 같은 경고성 문구는 제외하고 안심할 수 있는 표현을 사용하세요.)
2. [중요] 사용자가 요청한 날짜({requested_time})에 데이터가 없다면, 반드시 "요청하신 시간대의 기록은 없으나 대안으로 가장 가까운 기록을 보고합니다"라고 명확히 서두에 밝히세요. 
3. [중요] 절대 실제 데이터에 없는 날짜를 지어내거나, 다른 날짜의 데이터를 요청 날짜인 것처럼 속이지 마세요.
4. [중요] 모든 핵심 사실 뒤에는 근거가 되는 타임스탬프를 대괄호 안에 표기하세요. (예: "인물 포착 [10:05]")
5. 각 섹션은 **최대 2문장**을 넘지 마세요.
6. 마지막에 "분석 완료. 이상입니다."와 같은 형식적인 맺음말은 **절대 포함하지 마세요.**
"""
        
        try:
            # 1. 보고서 생성 시도
            report = self._call_llm(system_prompt, user_prompt)
            
            # 2. 고도화된 사실 관계 검증 (Anti-Hallucination Verification)
            is_valid, corrected_report = self._verify_report(report, requested_time, context_text)
            
            if not is_valid:
                print(f"[NLP Service] 사실 관계 모순 감지! 재교정 수행 중...")
                # 재교정 프롬프트와 함께 한 번 더 시도
                retry_prompt = f"{system_prompt}\n\n[🚨 재교정 요청] 방금 생성된 보고서에서 날짜나 사실 관계 오류가 발견되었습니다. 실제 데이터 시점과 요청 시점을 엄격히 구분하여 다시 작성해 주세요."
                report = self._call_llm(retry_prompt, user_prompt)
                # 최종 검증 (그래도 틀리면 경고 문구 강제 삽입)
                _, final_report = self._verify_report(report, requested_time, context_text, force_warning=True)
                return final_report
                
            return corrected_report

        except Exception as e:
            print(f"[NLP Error] AI 보고서 생성 중 오류: {e}")
            return "보안 보고서를 생성하는 동안 기술적인 문제가 발생했습니다. 잠시 후 다시 시도해 주세요."

    def _call_llm(self, system_prompt: str, user_content: str) -> str:
        """LLM 호출 공통 로직"""
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.2, # 낮은 온도로 일관성 유지
        )
        return response.choices[0].message.content

    def _verify_report(self, report: str, requested_time: str, context: str, force_warning: bool = False) -> tuple[bool, str]:
        """
        생성된 보고서의 사실 관계를 검증합니다.
        1. 요청 시간과 실제 데이터 시간이 혼용되었는지 체크
        2. 실제 데이터에 없는 날짜 정보가 포함되었는지 체크
        """
        import re
        
        # 실제 데이터에서 발견되는 모든 날짜 추출 (예: 4월 28일)
        actual_dates = set(re.findall(r"\d+월 \d+일", context))
        # 요청한 날짜 추출
        req_date_match = re.search(r"\d+월 \d+일", requested_time)
        req_date = req_date_match.group(0) if req_date_match else None
        
        # 만약 요청 날짜가 실제 데이터에 없는데, 보고서에서 요청 날짜가 '사실'인 것처럼 쓰였는지 체크
        is_valid = True
        if req_date and req_date not in actual_dates:
            # 보고서 내에서 요청 날짜를 언급하며 "포착되었습니다", "발생했습니다" 등의 긍정문을 사용하는지 검사
            suspicious_patterns = [
                f"{req_date}(에|은|는) .* (있었습니다|발생했습니다|포착되었습니다|기록되었습니다)"
            ]
            for pattern in suspicious_patterns:
                if re.search(pattern, report):
                    is_valid = False
                    break
        
        # 검증 실패 시 또는 강제 경고 필요 시 문구 보정
        if not is_valid or force_warning:
            warning_msg = "\n\n> ⚠️ **검증 알림**: 본 보고서는 요청하신 시간대의 데이터가 존재하지 않아 시스템에서 검색된 가장 인접한 시간대의 데이터를 기반으로 작성되었습니다."
            if warning_msg not in report:
                report += warning_msg
                
        return is_valid, report

    def generate_ood_response(self, user_query: str):
        """
        보안과 관련 없는 질문(Out-of-Distribution)에 대해 친절하게 거절하며 가이드를 제공합니다.
        """
        if not self.client:
            return "안녕하세요. 저는 지능형 보안 AI SearchLight입니다. 현재는 보안 및 CCTV 관제와 관련된 질문에 대해서만 도움을 드릴 수 있습니다. 궁금하신 보안 사항이 있다면 말씀해 주세요."
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """너는 SearchLight라는 지능형 CCTV 보안 분석 AI야. 
사용자로부터 보안과 관련 없는 일상적인 질문을 받으면, 자신을 '지능형 보안 분석관 SearchLight'로 소개하며 보안 및 관제 관련 질문을 해달라고 전문적인 톤으로 요청해줘.
원활한 분석을 위해 사용자가 어떤 질문을 할 수 있는지 아래 예시를 참고해서 마크다운 형식의 가이드를 포함해줘:

💡 **질문 가이드:**
- **특정 인물/차량 검색** (예: '빨간색 옷을 입은 사람 찾아줘', '흰색 SUV 차량 포착됐어?')
- **보안 상황 요약** (예: '어제 밤 10시 이후 주차장 상황 요약해줘')
- **실시간 상태 확인** (예: '지금 정문에 특이사항 있어?')

답변은 간결하면서도 신뢰감 있는 전문적인 어조를 유지해줘."""},
                    {"role": "user", "content": f"사용자 질문: {user_query}"}
                ],
                max_tokens=200,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return "반갑습니다. 지능형 보안 분석관 SearchLight입니다. 무엇을 도와드릴까요?\n\n저는 CCTV 영상 분석과 보안 관제에 최적화되어 있습니다. 원활한 분석을 위해 아래와 같이 보안/관제와 관련된 질문을 입력해 주시기 바랍니다.\n\n💡 **질문 예시:**\n- 인물 검색: '빨간색 옷을 입은 사람 찾아줘'\n- 상황 요약: '어제 오후 주차장 상황 요약해줘'\n- 실시간 확인: '지금 로비에 특이사항 있어?'"

# 싱글톤 인스턴스 생성
nlp_service = NLPService()

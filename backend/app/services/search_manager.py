import os
from app.services.vector_db_service import vector_db_service
from app.services.intent_classifier import intent_service
from app.services.database import db_service
from app.services.korean_time_parser import KoreanTimeParser
from app.services.nlp_service import nlp_service
from app.services.alert_service import alert_service

class SearchManager:
    def __init__(self):
        self.time_parser = KoreanTimeParser()
        self.session_memory = {}
        self.intent_messages = {
            "COUNTING":     "대상에 대한 수량 집계를 완료했습니다.",
            "SUMMARIZATION": "해당 시간대의 보안 상황을 요약하여 보고합니다.",
            "LOCALIZATION":  "현재 실시간 위치 및 상태를 확인합니다.",
            "BEHAVIORAL":    "이상 행동 분석 및 검색 결과를 보고합니다.",
            "CAUSAL":        "이벤트 발생 원인 및 인과 관계를 분석합니다.",
            "EMERGENCY":     "🚨 긴급 상황이 감지되었습니다. 즉시 관계자에게 연락하고 해당 구역을 확인해 주세요.",
            "ERROR":         "⚠️ 시스템 장애 관련 문의입니다. 카메라 연결 상태를 점검해 주세요.",
            "GENERAL":       "💬 일반 대화로 분류되었습니다. 보안 질문을 입력해 주세요.",
        }
        self.feature_keywords = ["빨간", "파란", "검은", "하얀", "초록", "노란", "정장", "청바지", "가방", "배낭", "차량", "자동차", "오토바이", "헬멧", "모자", "안경", "마스크", "후드"]

    def handle_query(self, query_text: str, session_id: str, top_k: int = 2, is_logged_in: bool = False, user_name: str = "guest"):
        # 1. 세션 메모리 및 지칭어 처리
        memory = self.session_memory.get(session_id, {})
        pronouns = ["그", "거기", "그때", "이전", "다시", "아까", "마지막", "방금", "방금 전"]
        has_pronoun = any(p in query_text for p in pronouns)

        # 2. 의도 분류
        intent_result = intent_service.classify(query_text)
        current_intent = intent_result.intent

        # 2-1. 일상 질의 예외 처리
        if current_intent == "CHITCHAT":
            return self._handle_chitchat(query_text, intent_result)

        # 의도 계승 로직
        context_used = False
        if has_pronoun and current_intent == "GENERAL" and "last_intent" in memory:
            current_intent = memory["last_intent"]
            intent_result.intent = current_intent
            context_used = True

        # 3. 시간 파싱 및 모드 결정
        parsed_time = self.time_parser.parse(query_text)
        response_mode = "summary"
        if parsed_time:
            duration = (parsed_time.end - parsed_time.start).total_seconds()
            if 0 < duration <= 3600:
                response_mode = "flash"

        if not parsed_time and has_pronoun and "last_time" in memory:
            time_info = memory["last_time"]
            context_used = True
        elif parsed_time:
            time_info = {
                "start_time": parsed_time.start.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": parsed_time.end.strftime("%Y-%m-%d %H:%M:%S"),
                "raw": parsed_time.raw_expression
            }
        else:
            time_info = {"start_time": None, "end_time": None, "raw": "전체"}

        # 4. 특징 추출 및 맥락 유지
        current_features = [kw for kw in self.feature_keywords if kw in query_text]
        stored_features = memory.get("features", [])
        if has_pronoun and stored_features:
            missing_features = [f for f in stored_features if f not in current_features]
            if missing_features:
                feature_context = " ".join(missing_features)
                query_text = f"{feature_context} {query_text}"
                context_used = True
        
        updated_features = list(set(stored_features + current_features))

        # 5. 결과 생성 데이터 구성
        response_data = {
            "status": "success",
            "message": self.intent_messages.get(current_intent, "요청을 처리했습니다."),
            "intent_info": {
                "intent": current_intent,
                "confidence": intent_result.confidence,
                "method": intent_result.method
            },
            "time_info": time_info,
            "context_used": context_used,
            "response_mode": response_mode,
            "results": [],
            "ai_report": None
        }

        # 6. 의도별 라우팅
        if current_intent == "LOCALIZATION":
            self._process_localization(query_text, response_data)
        elif current_intent in ("SUMMARIZATION", "BEHAVIORAL", "CAUSAL", "COUNTING"):
            self._process_search(query_text, top_k, time_info, response_data, response_mode)

        # 7. 메모리 및 DB 기록
        self.session_memory[session_id] = {
            "last_intent": current_intent,
            "last_time": time_info,
            "last_query": query_text,
            "features": updated_features
        }

        db_service.log_search(
            query=query_text, 
            intent=current_intent, 
            session_id=session_id,
            ai_report=response_data.get("ai_report") or response_data.get("answer")
        )

        return response_data

    def _handle_chitchat(self, query_text, intent_result):
        try:
            answer = nlp_service.generate_ood_response(query_text)
        except Exception as e:
            answer = "반갑습니다. 지능형 보안 분석관 SearchLight입니다. 무엇을 도와드릴까요?..."
        
        return {
            "status": "success",
            "message": "지능형 보안 AI 가이드",
            "intent_info": {
                "intent": "CHITCHAT",
                "confidence": getattr(intent_result, 'confidence', 0),
                "method": getattr(intent_result, 'method', 'direct')
            },
            "answer": answer,
            "results": [],
            "ai_report": None
        }

    def _process_localization(self, query_text, response_data):
        locations = ["정문", "로비", "주차장", "식당", "창고", "사무실", "하역장", "엘리베이터", "옥상"]
        target_loc = next((loc for loc in locations if loc in query_text), None)
        latest_status = db_service.get_latest_status(location=target_loc)
        
        if latest_status:
            response_data["results"] = [latest_status]
            response_data["ai_report"] = f"📌 **실시간 위치 확인 보고**\n\n확인된 위치: **{latest_status['location']}**\n..."
        else:
            response_data["ai_report"] = "⚠️ **위치 확인 불가**..."

    def _process_search(self, query_text, top_k, time_info, response_data, response_mode):
        # 요약(SUMMARIZATION) 의도일 경우 더 많은 맥락을 가져와서 풍부하게 요약하도록 top_k 상향
        current_intent = response_data["intent_info"]["intent"]
        effective_top_k = top_k
        if current_intent == "SUMMARIZATION":
            effective_top_k = max(top_k, 10)

        search_results = vector_db_service.search(
            query=query_text, 
            top_k=effective_top_k,
            start_time=time_info.get("start_time"),
            end_time=time_info.get("end_time")
        )
        
        is_fallback = False
        if not search_results and any(kw in query_text for kw in ["방금", "최근", "지금", "어떤일"]):
            search_results = vector_db_service.search(query=query_text, top_k=top_k)
            is_fallback = True
            response_data["context_used"] = True

        response_data["results"] = search_results
        
        if search_results:
            response_data["ai_report"] = nlp_service.generate_security_report(
                query=query_text, 
                contexts=search_results,
                intent=response_data["intent_info"]["intent"],
                is_fallback=is_fallback,
                requested_time=time_info.get("raw", "전체 시간"),
                mode=response_mode
            )
        else:
            response_data["ai_report"] = "현재 시스템에 기록된 보안 이벤트가 없습니다."

search_manager = SearchManager()

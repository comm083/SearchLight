from typing import Dict, Any, List, Optional
from app.services.nlp_service import nlp_service
from app.services.intent_classifier import intent_service
from app.services.vector_db_service import vector_db_service
from app.services.database import db_service
from app.services.korean_time_parser import KoreanTimeParser
from app.services.session_manager import session_manager

class SearchManager:
    def __init__(self):
        self.time_parser = KoreanTimeParser()
        self.pronouns = ["그", "거기", "그때", "이전", "다시", "아까", "마지막", "방금", "방금 전"]
        self.feature_keywords = ["빨간", "파란", "검은", "하얀", "초록", "노란", "정장", "청바지", "가방", "배낭", "차량", "자동차", "오토바이", "헬멧", "모자", "안경", "마스크", "후드"]
        self.intent_messages = {
            "GENERAL": "일반 검색 결과를 표시합니다.",
            "SUMMARIZATION": "요약 정보를 표시합니다.",
            "BEHAVIORAL": "행동/동선 검색 결과를 표시합니다.",
            "CAUSAL": "원인/상황 분석 결과를 표시합니다.",
            "COUNTING": "계측/카운팅 결과를 표시합니다.",
            "LOCALIZATION": "위치 추적 결과를 표시합니다.",
            "CHITCHAT": "대화 응답을 표시합니다."
        }

    async def process_query(self, query: str, session_id: str, top_k: int = 2) -> Dict[str, Any]:
        # 1. 대화 메모리 로드
        memory = session_manager.get_session(session_id)
        has_pronoun = any(p in query for p in self.pronouns)

        # 2. NLP 전처리
        preprocess = nlp_service.preprocess_query(query)
        corrected_query = preprocess["corrected"]

        # 3. 의도 분류
        intent_result = intent_service.classify(corrected_query)
        current_intent = intent_result.intent

        # 3-1. 일상 질의 처리
        if current_intent == "CHITCHAT":
            response_data = self._handle_chitchat(query, intent_result)
            self._finalize(session_id, current_intent, {"raw": "N/A"}, query, response_data)
            return response_data

        # 3-2. 지칭어 및 의도 보정
        context_used = False
        if has_pronoun and current_intent == "GENERAL" and memory.get("last_intent"):
            current_intent = memory["last_intent"]
            intent_result.intent = current_intent
            context_used = True

        # 4. 시간 표현 파싱
        time_info = self._parse_time(corrected_query, has_pronoun, memory)
        if has_pronoun and not self.time_parser.parse(corrected_query):
            context_used = True

        # 5. 특징 추출 및 맥락 유지
        query, context_used = self._apply_feature_context(query, has_pronoun, memory, context_used)

        # 6. 의도별 검색 및 보고서 생성
        response_data = self._init_response(current_intent, intent_result, time_info, context_used)

        # 시간 정보가 있으면 가장 가까운 이벤트 조회
        if time_info.get("start_time"):
            nearest = db_service.get_nearest_event(time_info["start_time"])
            response_data["nearest_event"] = nearest
        else:
            response_data["nearest_event"] = None

        if current_intent == "LOCALIZATION":
            response_data = self._handle_localization(query, response_data)
        elif current_intent in ("SUMMARIZATION", "BEHAVIORAL", "CAUSAL", "COUNTING"):
            response_data = self._handle_vector_search(query, top_k, time_info, current_intent, response_data)

        # 7. 세션 및 DB 업데이트
        self._finalize(session_id, current_intent, time_info, query, response_data)

        return response_data

    def _handle_chitchat(self, query: str, intent_result) -> Dict[str, Any]:
        try:
            answer = nlp_service.generate_ood_response(query)
        except Exception as e:
            print(f"[OOD Error] {e}")
            answer = (
                "안녕하세요, 저는 지능형 보안 분석관 SearchLight입니다.\n"
                "보안 및 관제 관련 질문이 있으시면 언제든지 말씀해 주세요.\n"
                "도움이 필요하신 부분에 대해 전문적으로 안내해 드리겠습니다.\n\n"
                "💡 **질문 가이드:**\n"
                "- **특정 인물/차량 검색** (예: '빨간색 옷을 입은 사람 찾아줘', '흰색 SUV 차량 포착됐어?')\n"
                "- **보안 상황 요약** (예: '어제 밤 10시 이후 주차장 상황 요약해줘')\n"
                "- **실시간 상태 확인** (예: '지금 정문에 특이사항 있어?')"
            )
            
        return {
            "status": "success",
            "message": "지능형 보안 AI 가이드",
            "intent_info": {
                "intent": "CHITCHAT",
                "confidence": getattr(intent_result, 'confidence', 0),
                "method": getattr(intent_result, 'method', 'direct')
            },
            "time_info": {"start_time": None, "end_time": None, "raw": "전체"},
            "context_used": False,
            "response_mode": "summary",
            "answer": answer,
            "results": [],
            "ai_report": None
        }

    def _parse_time(self, query: str, has_pronoun: bool, memory: Dict) -> Dict:
        parsed_time = self.time_parser.parse(query)
        if not parsed_time and has_pronoun and memory.get("last_time"):
            return memory["last_time"]
        elif parsed_time:
            return {
                "start_time": parsed_time.start.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": parsed_time.end.strftime("%Y-%m-%d %H:%M:%S"),
                "raw": parsed_time.raw_expression
            }
        return {"start_time": None, "end_time": None, "raw": "전체"}

    def _apply_feature_context(self, query: str, has_pronoun: bool, memory: Dict, context_used: bool) -> tuple:
        current_features = [kw for kw in self.feature_keywords if kw in query]
        stored_features = memory.get("features", [])
        
        if has_pronoun and stored_features:
            missing_features = [f for f in stored_features if f not in current_features]
            if missing_features:
                feature_context = " ".join(missing_features)
                query = f"{feature_context} {query}"
                context_used = True
        
        session_manager.add_features(memory.get("session_id", "default"), current_features)
        return query, context_used

    def _init_response(self, intent: str, intent_result, time_info: Dict, context_used: bool) -> Dict:
        return {
            "status": "success",
            "message": self.intent_messages.get(intent, "요청을 처리했습니다."),
            "intent_info": {
                "intent": intent,
                "confidence": intent_result.confidence,
                "method": intent_result.method
            },
            "time_info": time_info,
            "context_used": context_used,
            "response_mode": "summary",
            "results": [],
            "ai_report": None
        }

    def _handle_localization(self, query: str, response: Dict) -> Dict:
        locations = ["정문", "로비", "주차장", "식당", "창고", "사무실", "하역장", "엘리베이터", "옥상"]
        target_loc = next((loc for loc in locations if loc in query), None)
        
        # 임계값 필터링이 적용된 벡터 검색을 통해 대상이 실제로 존재하는지 확인
        search_results = vector_db_service.search(query=query, top_k=1)
        
        if search_results:
            latest_status = search_results[0]
            response["results"] = [latest_status]
            loc_str = latest_status.get('location', target_loc or '확인된 구역')
            time_str = latest_status.get('timestamp') or latest_status.get('event_date')
            desc_str = latest_status.get('description', '')
            
            response["ai_report"] = (
                f"📌 **실시간 위치 확인 보고**\n\n"
                f"확인된 위치: **{loc_str}**\n"
                f"최종 포착 시각: {time_str}\n"
                f"현재 상태: {desc_str}\n\n"
                f"💡 **분석**: 대상이 마지막으로 포착된 지점은 {loc_str} 구역이며, "
                f"'{desc_str}' 행동을 보인 후 현재 해당 구역 내에 머물고 있거나 인접 구역으로 이동 중인 것으로 판단됩니다."
            )
        else:
            response["ai_report"] = (
                f"⚠️ **위치 확인 불가**: " + 
                (f"'{target_loc}' 구역에서 " if target_loc else "전체 구역에서 ") +
                "요청하신 대상과 일치하는 유의미한 보안 이벤트(CCTV 기록)를 찾을 수 없습니다."
            )
        return response

    def _handle_vector_search(self, query: str, top_k: int, time_info: Dict, intent: str, response: Dict) -> Dict:
        search_results = vector_db_service.search(
            query=query, 
            top_k=top_k,
            start_time=time_info.get("start_time"),
            end_time=time_info.get("end_time")
        )
        
        is_fallback = False
        if not search_results and any(kw in query for kw in ["방금", "최근", "지금", "어떤일"]):
            search_results = vector_db_service.search(query=query, top_k=top_k)
            is_fallback = True
            response["context_used"] = True

        response["results"] = search_results
        if search_results:
            response["ai_report"] = nlp_service.generate_security_report(
                query=query, contexts=search_results, intent=intent,
                is_fallback=is_fallback, requested_time=time_info.get("raw", "전체 시간")
            )
        else:
            response["ai_report"] = "현재 시스템에 기록된 보안 이벤트가 없습니다. 카메라 연결 상태를 확인하거나 잠시 후 다시 시도해 주세요."
        return response

    def _finalize(self, session_id: str, intent: str, time_info: Dict, query: str, response: Dict):
        session_manager.update_session(
            session_id,
            last_intent=intent,
            last_time=time_info,
            last_query=query
        )
        db_service.log_search(
            query=query,
            intent=intent,
            session_id=session_id,
            ai_report=response.get("ai_report") or response.get("answer"),
            results=response.get("results") or []
        )

search_manager = SearchManager()

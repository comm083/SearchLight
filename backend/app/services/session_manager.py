from typing import Dict, Any, List

class SessionManager:
    def __init__(self):
        self._memory: Dict[str, Dict[str, Any]] = {}

    def get_session(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self._memory:
            self._memory[session_id] = {
                "last_intent": "GENERAL",
                "last_time": {"start_time": None, "end_time": None, "raw": "전체"},
                "last_query": "",
                "features": [],
                "last_results": [],
                "conversation_history": [],
            }
        return self._memory[session_id]

    def update_session(self, session_id: str, **kwargs):
        session = self.get_session(session_id)
        session.update(kwargs)

    def add_features(self, session_id: str, new_features: List[str]):
        session = self.get_session(session_id)
        current_features = set(session.get("features", []))
        current_features.update(new_features)
        session["features"] = list(current_features)

    def update_last_results(self, session_id: str, results: list):
        """마지막 검색 결과 핵심 정보 저장 (지칭어 처리용)"""
        session = self.get_session(session_id)
        summaries = []
        for r in results[:3]:
            desc = r.get("description") or r.get("short_summary") or ""
            if desc:
                summaries.append({
                    "description": desc,
                    "situation": r.get("situation") or r.get("tag") or "",
                    "timestamp": r.get("timestamp") or r.get("event_date") or "",
                })
        session["last_results"] = summaries

    def add_conversation_turn(self, session_id: str, user_query: str, assistant_report: str):
        """대화 히스토리에 한 턴 추가 (최근 6턴 유지)"""
        session = self.get_session(session_id)
        history = session.get("conversation_history", [])
        history.append({"role": "user", "content": user_query})
        history.append({"role": "assistant", "content": assistant_report[:800]})  # 길이 제한
        session["conversation_history"] = history[-12:]  # 최근 6턴(12개 메시지)

session_manager = SessionManager()

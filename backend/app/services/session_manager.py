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
                "features": []
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

session_manager = SessionManager()

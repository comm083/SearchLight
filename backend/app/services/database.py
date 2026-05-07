import os
from supabase import create_client, Client
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

from app.core.config import settings

class SupabaseService:
    def __init__(self):
        url = settings.SUPABASE_URL
        key = settings.SUPABASE_KEY
        if not url or not key:
            print("[Warning] Supabase 설정이 없습니다. 로그 저장 기능이 비활성화됩니다.")
            self.supabase = None
            return
        self.supabase: Client = create_client(url, key)
        print("[Service] Supabase 클라우드 DB 연동 완료!")

    def log_search(self, query: str, intent: str, session_id: str = "default", ai_report: str = None, results: list = None):
        if not self.supabase:
            print(f"[Mock DB] 로그 기록 (DB 연결 없음): {query} / {intent}")
            return
        import json
        try:
            # Supabase 'search_logs' 테이블에 데이터 전송
            data = {
                "query": query,
                "intent": intent,
                "session_id": session_id
            }
            if ai_report:
                data["ai_report"] = ai_report
            if results:
                data["results"] = json.dumps(results, ensure_ascii=False)
                
            response = self.supabase.table('search_logs').insert(data).execute()
        except Exception as e:
            # results 컬럼이 없는 경우 results 제외하고 재시도
            if results and 'results' in str(e):
                try:
                    data.pop("results", None)
                    self.supabase.table('search_logs').insert(data).execute()
                    print(f"[Supabase] results 컬럼 없음 - results 제외하고 저장 완료")
                except Exception as e2:
                    print(f"[Supabase Error] 로그 저장 실패: {e2}")
            else:
                print(f"[Supabase Error] 로그 저장 실패: {e}")

    def get_search_history(self, session_id: str = "default", limit: int = 20):
        """
        특정 세션의 과거 검색 기록을 가져옵니다.
        """
        try:
            # session_id가 포함된 것 가져오기 (기존 하위 호환 및 새로운 _timestamp 포맷 지원)
            response = self.supabase.table('search_logs') \
                .select("*") \
                .like("session_id", f"{session_id}%") \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            # 다른 사용자(예: admin vs admin2)가 섞이지 않도록 엄격히 필터링
            import json
            filtered_data = []
            for row in response.data:
                if row['session_id'] == session_id or row['session_id'].startswith(f"{session_id}_"):
                    # results 컬럼이 JSON 문자열이면 파싱
                    if row.get('results') and isinstance(row['results'], str):
                        try:
                            row['results'] = json.loads(row['results'])
                        except Exception:
                            row['results'] = []
                    elif not row.get('results'):
                        row['results'] = []
                    filtered_data.append(row)
            return filtered_data
        except Exception as e:
            print(f"[Supabase Error] 히스토리 조회 실패: {e}")
            return []

    def delete_search_history(self, history_id: str):
        """
        특정 ID의 검색 기록을 삭제합니다.
        """
        try:
            # ID가 숫자인 경우 숫자로 변환 (Supabase 타입 매칭을 위해)
            target_id = history_id
            try:
                if isinstance(history_id, str) and history_id.isdigit():
                    target_id = int(history_id)
            except:
                pass

            response = self.supabase.table('search_logs') \
                .delete() \
                .eq("id", target_id) \
                .execute()
            return True
        except Exception as e:
            print(f"[Supabase Error] 히스토리 삭제 실패: {e}")
            return False

    def save_alert(self, alert_data: dict):
        """
        실시간 감지된 이상 행동 알림을 Supabase 'alerts' 테이블에 저장합니다.
        """
        if not self.supabase:
            print(f"[Mock DB] 알림 기록 (DB 연결 없음): {alert_data.get('type')}")
            return
        try:
            response = self.supabase.table('alerts').insert(alert_data).execute()
            print(f"[Supabase] 실시간 알림 DB 저장 성공: {alert_data.get('type')}")
        except Exception as e:
            # 테이블이 없거나 권한 문제일 수 있으므로 에러 메시지 출력
            print(f"[Supabase Error] 알림 저장 실패: {e}")

    def get_latest_status(self, location: str = None):
        """
        특정 구역 또는 전체 구역의 가장 최신 보안 이벤트를 가져옵니다. (Localization 용)
        """
        try:
            query = self.supabase.table('cctv_vectors').select('content, metadata').order('metadata->timestamp', desc=True).limit(1)
            
            if location:
                # location 필터링 (metadata 내의 location 필드 기준)
                # Supabase에서는 json 필터링이 가능함
                query = query.filter('metadata->>location', 'eq', location)
            
            response = query.execute()
            if response.data:
                item = response.data[0]
                return {
                    "description": item['content'],
                    "timestamp": item['metadata'].get('timestamp'),
                    "location": item['metadata'].get('location'),
                    "image_path": item['metadata'].get('image_path')
                }
            return None
        except Exception as e:
            print(f"[Supabase Error] 최신 상태 조회 실패: {e}")
            return None

    def get_all_events(self, limit: int = 50):
        """
        영상 보관함(Event History)에 표시할 이벤트 데이터를 모두 가져옵니다.
        """
        try:
            query = self.supabase.table('cctv_vectors').select('id, content, metadata').order('metadata->timestamp', desc=True).limit(limit)
            response = query.execute()
            
            events = []
            if response.data:
                for item in response.data:
                    metadata = item.get('metadata', {})
                    # confidence 값 등 UI에 필요한 항목들 추출 (없을 경우 기본값)
                    events.append({
                        "id": item.get('id', str(len(events))),
                        "title": item.get('content', '보안 이벤트 기록'),
                        "location": metadata.get('location', '미상'),
                        "timestamp": metadata.get('timestamp', ''),
                        "image_path": metadata.get('image_path', ''),
                        "tag": metadata.get('person', '') if metadata.get('person') else 'Event',
                        "confidence": metadata.get('confidence', 90)
                    })
            return events
        except Exception as e:
            print(f"[Supabase Error] 이벤트 목록 조회 실패: {e}")
            return []

    def get_nearest_event(self, timestamp_str: str) -> dict | None:
        """
        주어진 시각과 가장 가까운 event 테이블 레코드를 반환합니다.
        event_intents도 함께 조회합니다.
        """
        if not self.supabase:
            return None
        try:
            response = self.supabase.table('event') \
                .select('*, event_intents(*)') \
                .order('timestamp') \
                .execute()
            if not response.data:
                return None

            from datetime import datetime
            target = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

            def diff(row):
                ts = row.get('timestamp')
                if not ts:
                    return float('inf')
                try:
                    t = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    return abs((t - target).total_seconds())
                except Exception:
                    return float('inf')

            nearest = min(response.data, key=diff)
            return nearest
        except Exception as e:
            print(f"[Supabase Error] nearest event 조회 실패: {e}")
            return None

    def log_feedback(self, history_id: int, feedback_type: str, comment: str = None):
        """
        검색 결과에 대한 사용자 피드백(예: wrong_result)을 기록합니다.
        """
        if not self.supabase:
            print(f"[Mock DB] 피드백 기록: ID={history_id}, 타입={feedback_type}")
            return False
            
        try:
            data = {"feedback": feedback_type}
            if comment:
                data["feedback_comment"] = comment
                
            response = self.supabase.table('search_logs') \
                .update(data) \
                .eq("id", history_id) \
                .execute()
            print(f"[Supabase] 피드백 기록 완료: {history_id}")
            return True
        except Exception as e:
            print(f"[Supabase Error] 피드백 저장 실패 (스키마 불일치일 수 있음): {e}")
            return False

# 싱글톤 패턴 (서버 내에서 한 번만 생성되도록)
db_service = SupabaseService()

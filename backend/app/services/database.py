import os
from supabase import create_client, Client
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

from app.core.config import settings

class SupabaseService:
    def __init__(self):
        url = settings.SUPABASE_URL
        key = settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_KEY
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

    def get_all_events(self, limit: int = 50):
        """
        영상 보관함(Event History)에 표시할 이벤트 데이터를 모두 가져옵니다.
        event_clips 테이블에서 클립 목록을 조인하며, 없으면 clip_url로 폴백합니다.
        """
        try:
            response = self.supabase.table('event') \
                .select('id, summary, short_summary, timestamp, video_filename, situation, clip_url, event_clips(id, clip_url, start_sec, end_sec, clip_index)') \
                .order('timestamp', desc=True) \
                .limit(limit) \
                .execute()

            events = []
            if response.data:
                for item in response.data:
                    raw_clips = item.get('event_clips') or []
                    raw_clips_sorted = sorted(raw_clips, key=lambda c: c.get('clip_index', 0))

                    if raw_clips_sorted:
                        clips = [
                            {
                                "clip_url":   c.get('clip_url'),
                                "start_sec":  c.get('start_sec'),
                                "end_sec":    c.get('end_sec'),
                                "clip_index": c.get('clip_index'),
                            }
                            for c in raw_clips_sorted
                        ]
                    elif item.get('clip_url'):
                        # 기존 데이터 호환: event.clip_url을 단일 클립으로 처리
                        clips = [{"clip_url": item['clip_url'], "start_sec": None, "end_sec": None, "clip_index": 1}]
                    else:
                        clips = []

                    first_clip_url = clips[0]['clip_url'] if clips else None

                    events.append({
                        "id": item.get('id'),
                        "title": item.get('summary', '보안 이벤트 기록'),
                        "short_summary": item.get('short_summary') or '',
                        "location": item.get('video_filename', '미상'),
                        "timestamp": item.get('timestamp', ''),
                        "clip_url": first_clip_url,
                        "clips": clips,
                        "tag": item.get('situation', 'normal'),
                        "image_path": None,
                        "confidence": None,
                    })
            return events
        except Exception as e:
            print(f"[Supabase Error] 이벤트 목록 조회 실패: {e}")
            return []

    def get_pending_events(self, limit: int = 100):
        """
        timestamp가 NULL인 이벤트(처리대기영상)를 반환합니다.
        """
        try:
            response = self.supabase.table('event') \
                .select('id, summary, timestamp, video_filename, situation, clip_url, event_clips(id, clip_url, start_sec, end_sec, clip_index)') \
                .is_('timestamp', 'null') \
                .order('id', desc=True) \
                .limit(limit) \
                .execute()

            events = []
            if response.data:
                for item in response.data:
                    raw_clips = item.get('event_clips') or []
                    raw_clips_sorted = sorted(raw_clips, key=lambda c: c.get('clip_index', 0))
                    if raw_clips_sorted:
                        clips = [{"clip_url": c.get('clip_url'), "start_sec": c.get('start_sec'), "end_sec": c.get('end_sec'), "clip_index": c.get('clip_index')} for c in raw_clips_sorted]
                    elif item.get('clip_url'):
                        clips = [{"clip_url": item['clip_url'], "start_sec": None, "end_sec": None, "clip_index": 1}]
                    else:
                        clips = []
                    events.append({
                        "id": item.get('id'),
                        "title": item.get('summary', '보안 이벤트 기록'),
                        "location": item.get('video_filename', '미상'),
                        "timestamp": None,
                        "clip_url": clips[0]['clip_url'] if clips else None,
                        "clips": clips,
                        "tag": item.get('situation', 'normal'),
                    })
            return events
        except Exception as e:
            print(f"[Supabase Error] 처리대기 이벤트 조회 실패: {e}")
            return []

    def update_event_timestamp(self, event_id: str, timestamp: str) -> bool:
        """
        특정 이벤트의 timestamp를 수동으로 업데이트합니다.
        """
        try:
            self.supabase.table('event') \
                .update({"timestamp": timestamp}) \
                .eq('id', event_id) \
                .execute()
            return True
        except Exception as e:
            print(f"[Supabase Error] timestamp 업데이트 실패: {e}")
            return False

    def fix_timestamps_kst(self) -> dict:
        """
        기존에 KST 시각을 timezone 없이 저장해 UTC로 오인된 타임스탬프를 -9시간 보정합니다.
        최초 1회만 실행해야 합니다.
        """
        try:
            self.supabase.rpc('fix_event_timestamps_kst', {}).execute()
            return {"status": "success", "message": "타임스탬프 KST 보정 완료"}
        except Exception:
            # RPC가 없으면 직접 Python으로 보정
            try:
                rows = self.supabase.table('event').select('id, timestamp').not_.is_('timestamp', 'null').execute()
                fixed = 0
                from datetime import datetime, timedelta, timezone
                for row in rows.data:
                    ts = row['timestamp']
                    try:
                        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                        dt_utc = dt.astimezone(timezone.utc)
                        corrected = dt_utc - timedelta(hours=9)
                        corrected_str = corrected.strftime("%Y-%m-%d %H:%M:%S+00:00")
                        self.supabase.table('event').update({"timestamp": corrected_str}).eq('id', row['id']).execute()
                        fixed += 1
                    except Exception:
                        pass
                return {"status": "success", "fixed": fixed, "message": f"{fixed}건 타임스탬프 보정 완료"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

    def delete_event(self, event_id: str) -> bool:
        try:
            self.supabase.table('event').delete().eq('id', event_id).execute()
            return True
        except Exception as e:
            print(f"[Supabase Error] 이벤트 삭제 실패: {e}")
            return False

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

            self.supabase.table('search_logs') \
                .update(data) \
                .eq("id", history_id) \
                .execute()
            print(f"[Supabase] 피드백 기록 완료: {history_id}")
            return True
        except Exception as e:
            print(f"[Supabase Error] 피드백 저장 실패: {e}")
            return False

    def get_feedbacks(self, status: str = 'pending') -> list:
        """관리자용 피드백 목록 조회"""
        try:
            q = self.supabase.table('search_logs').select('*')
            if status == 'pending':
                q = q.eq('feedback', 'wrong_result')
            elif status == 'resolved':
                q = q.eq('feedback', 'resolved')
            else:
                q = q.in_('feedback', ['wrong_result', 'resolved'])

            rows = q.order('created_at', desc=True).execute().data or []

            # correct_event_id가 있으면 event 정보 조인
            import json as _json
            for row in rows:
                row['parsed_comment'] = None
                row['correct_event'] = None
                try:
                    if row.get('feedback_comment'):
                        parsed = _json.loads(row['feedback_comment'])
                        row['parsed_comment'] = parsed
                        eid = parsed.get('correct_event_id')
                        if eid:
                            ev = self.supabase.table('event') \
                                .select('id, short_summary, timestamp, situation, video_filename') \
                                .eq('id', eid).limit(1).execute().data
                            row['correct_event'] = ev[0] if ev else None
                except Exception:
                    pass
            return rows
        except Exception as e:
            print(f"[Supabase Error] 피드백 목록 조회 실패: {e}")
            return []

    def resolve_feedback(self, feedback_id: int) -> bool:
        """피드백 처리 완료 마크"""
        try:
            self.supabase.table('search_logs') \
                .update({'feedback': 'resolved'}) \
                .eq('id', feedback_id).execute()
            return True
        except Exception as e:
            print(f"[Supabase Error] 피드백 처리 완료 실패: {e}")
            return False

    def boost_event_from_feedback(self, feedback_id: int) -> bool:
        """정답 이벤트의 event_intents.info_sent에 피드백 쿼리를 추가해 검색 가중치 향상"""
        import json as _json
        try:
            fb = self.supabase.table('search_logs') \
                .select('*').eq('id', feedback_id).limit(1).execute().data
            if not fb:
                return False
            fb = fb[0]

            parsed = _json.loads(fb.get('feedback_comment') or '{}')
            correct_event_id = parsed.get('correct_event_id')
            query_text = fb.get('query', '')

            if not correct_event_id:
                return False

            intents = self.supabase.table('event_intents') \
                .select('id, info_sent') \
                .eq('event_id', correct_event_id).limit(1).execute().data
            if not intents:
                return False

            intent = intents[0]
            updated = f"{intent.get('info_sent') or ''} | 검색어: {query_text}".strip(' |')
            self.supabase.table('event_intents') \
                .update({'info_sent': updated}) \
                .eq('id', intent['id']).execute()

            self.resolve_feedback(feedback_id)
            return True
        except Exception as e:
            print(f"[Supabase Error] 피드백 적용 실패: {e}")
            return False

# 싱글톤 패턴 (서버 내에서 한 번만 생성되도록)
db_service = SupabaseService()

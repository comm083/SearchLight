from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel
from typing import Optional
import os
import shutil

from app.services.vector_db_service import vector_db_service
from app.services.intent_classifier import intent_service
from app.services.database import db_service
from app.services.korean_time_parser import KoreanTimeParser
from app.services.nlp_service import nlp_service
from app.services.image_search_service import image_search_service

router = APIRouter()
time_parser = KoreanTimeParser()

# 전역 대화 메모리 (세션별 저장) - main.py에서 옮겨옴
SESSION_MEMORY = {}

class SearchRequest(BaseModel):
    query: str
    top_k: int = 2
    session_id: str = "default"
    start_time: Optional[str] = None
    end_time: Optional[str] = None

# 5가지 의도별 맞춤 응답 메시지
INTENT_MESSAGES = {
    "사람 수":     "대상에 대한 수량 집계를 완료했습니다.",
    "정보 요약":   "해당 시간대의 보안 상황을 요약하여 보고합니다.",
    "시간":        "현재 실시간 위치 및 상태를 확인합니다.",
    "행동":        "이상 행동 분석 및 검색 결과를 보고합니다.",
    "오류 감지":   "이벤트 발생 원인 및 인과 관계를 분석합니다.",
    "EMERGENCY":     "🚨 긴급 상황이 감지되었습니다. 즉시 관계자에게 연락하고 해당 구역을 확인해 주세요.",
    "ERROR":         "⚠️ 시스템 장애 관련 문의입니다. 카메라 연결 상태를 점검해 주세요.",
    "GENERAL":       "💬 일반 대화로 분류되었습니다. 보안 질문을 입력해 주세요.",
}

@router.post("")
async def process_user_query(request: SearchRequest):
    query_text = request.query
    session_id = request.session_id

    # 1. 대화 메모리 로드
    memory = SESSION_MEMORY.get(session_id, {})
    
    # 지칭어(그, 거기, 그때 등) 탐지
    pronouns = ["그", "거기", "그때", "이전", "다시", "아까", "마지막", "방금", "방금 전"]
    has_pronoun = any(p in query_text for p in pronouns)

    # 2. 의도 분류 (KoELECTRA - 5종)
    intent_result = intent_service.classify(query_text)
    current_intent = intent_result.intent

    # 2-1. 일상 질의(CHITCHAT) 예외 처리
    if current_intent == "CHITCHAT":
        try:
            answer = await nlp_service.generate_ood_response(query_text)
        except Exception as e:
            print(f"[OOD Error] {e}")
            answer = "반갑습니다. 지능형 보안 분석관 SearchLight입니다. 무엇을 도와드릴까요?\n\n저는 CCTV 영상 분석과 보안 관제에 최적화되어 있습니다. 원활한 분석을 위해 아래와 같이 보안/관제와 관련된 질문을 입력해 주시기 바랍니다.\n\n💡 **질문 예시:**\n- 인물 검색: '빨간색 옷을 입은 사람 찾아줘'\n- 상황 요약: '어제 오후 주차장 상황 요약해줘'\n- 실시간 확인: '지금 로비에 특이사항 있어?'"

            
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

    # 지칭어가 있는데 의도가 불분명한 경우 이전 의도 계승
    if has_pronoun and current_intent == "GENERAL" and "last_intent" in memory:
        current_intent = memory["last_intent"]
        intent_result.intent = current_intent
        context_used = True
    else:
        context_used = False

    # 3. 시간 표현 파싱 (새로운 파서 사용)
    parsed_time = time_parser.parse(query_text)
    
    # 응답 모드 결정 (시간 범위가 1시간 이내면 flash, 아니면 summary)
    response_mode = "summary"
    if parsed_time:
        duration = (parsed_time.end - parsed_time.start).total_seconds()
        if 0 < duration <= 3600: # 1시간 이내
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

    # [고도화] 특징(Feature) 추출 및 대화 맥락 유지 (Feature Persistence)
    feature_keywords = ["빨간", "파란", "검은", "하얀", "초록", "노란", "정장", "청바지", "가방", "배낭", "차량", "자동차", "오토바이", "헬멧", "모자", "안경", "마스크", "후드"]
    current_features = [kw for kw in feature_keywords if kw in query_text]
    
    # 지칭어("그", "거기", "그때" 등) 사용 시 이전 맥락의 특징을 자동으로 결합
    stored_features = memory.get("features", [])
    if has_pronoun and stored_features:
        # 현재 쿼리에 없는 이전 특징들만 골라서 결합
        missing_features = [f for f in stored_features if f not in current_features]
        if missing_features:
            feature_context = " ".join(missing_features)
            query_text = f"{feature_context} {query_text}"
            print(f"[Context Persistence] 지칭어 감지: 이전 특징 '{feature_context}'을(를) 반영합니다.")
            context_used = True
    
    # 새로운 특징 저장 (누적)
    updated_features = list(set(stored_features + current_features))

    # 5. 의도별 라우팅 및 검색
    response_data = {
        "status": "success",
        "message": INTENT_MESSAGES.get(current_intent, "요청을 처리했습니다."),
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

    # 🚨 [고도화] LOCALIZATION 전용 처리 (RAG를 거치지 않고 DB 최신 상태 직접 조회)
    if current_intent == "시간":
        # 특정 구역 언급 확인
        locations = ["정문", "로비", "주차장", "식당", "창고", "사무실", "하역장", "엘리베이터", "옥상"]
        target_loc = next((loc for loc in locations if loc in query_text), None)
        
        # 1. DB에서 가장 최신의 실제 로그/상태 조회
        latest_status = db_service.get_latest_status(location=target_loc)
        
        if latest_status:
            response_data["results"] = [latest_status]
            loc_str = latest_status['location']
            time_str = latest_status['timestamp']
            desc_str = latest_status['description']
            
            # 고증된 보고서 형식으로 출력
            response_data["ai_report"] = (
                f"📌 **실시간 위치 확인 보고**\n\n"
                f"확인된 위치: **{loc_str}**\n"
                f"최종 포착 시각: {time_str}\n"
                f"현재 상태: {desc_str}\n\n"
                f"💡 **분석**: 대상이 마지막으로 포착된 지점은 {loc_str} 구역이며, "
                f"'{desc_str}' 행동을 보인 후 현재 해당 구역 내에 머물고 있거나 인접 구역으로 이동 중인 것으로 판단됩니다."
            )
        else:
            response_data["ai_report"] = (
                f"⚠️ **위치 확인 불가**: " + 
                (f"'{target_loc}' 구역에서 " if target_loc else "전체 구역에서 ") +
                "최근 1시간 내에 포착된 유의미한 보안 이벤트가 없습니다. 실시간 스트리밍 확인을 권장합니다."
            )

    # 검색이 필요한 의도인 경우 (나머지 보안 질의)
    elif current_intent in ("정보 요약", "행동", "오류 감지", "사람 수"):
        # [Cloud Native] Supabase Vector DB에서 검색 수행 (시간 필터링 포함)
        search_results = vector_db_service.search(
            query=query_text, 
            top_k=request.top_k,
            start_time=time_info.get("start_time"),
            end_time=time_info.get("end_time")
        )
        
        # 🚨 [신규] "방금", "최근" 등의 질문인데 해당 시간대 결과가 없는 경우 전체 최신 데이터로 폴백
        is_fallback = False
        if not search_results and any(kw in query_text for kw in ["방금", "최근", "지금", "어떤일", "무슨일", "있었어"]):
            print(f"[Fallback] '{query_text}'에 대한 최근 데이터가 없어 전체 최신 데이터로 재검색합니다.")
            search_results = vector_db_service.search(
                query=query_text,
                top_k=request.top_k,
                start_time=None,
                end_time=None
            )
            is_fallback = True
            context_used = True # 폴백 데이터 사용됨을 표시

        response_data["results"] = search_results
        
        # [Advanced RAG] 검색 결과를 바탕으로 AI 보안 보고서 생성
        if search_results:
            # 최대 점수 계산 (환각 방지용)
            max_score = max([res.get('score', 0) for res in search_results]) if search_results else 0
            
            ai_report = await nlp_service.generate_security_report(
                query=query_text, 
                contexts=search_results,
                intent=current_intent,
                is_fallback=is_fallback,
                requested_time=time_info.get("raw", "전체 시간"),
                mode=response_data.get("response_mode", "summary"),
                max_score=max_score
            )
            response_data["ai_report"] = ai_report
        else:
            response_data["ai_report"] = "현재 시스템에 기록된 보안 이벤트가 없습니다. 카메라 연결 상태를 확인하거나 잠시 후 다시 시도해 주세요."

    # 세션 메모리 업데이트
    SESSION_MEMORY[session_id] = {
        "last_intent": current_intent,
        "last_time": time_info,
        "last_query": query_text,
        "features": updated_features
    }

    # 최종 로그 기록 (AI 보고서 포함)
    db_service.log_search(
        query=query_text, 
        intent=current_intent, 
        session_id=session_id,
        ai_report=response_data.get("ai_report") or response_data.get("answer")
    )

    return response_data

# 📸 [신규] 이미지 기반 유사 인물 검색 API
@router.post("/image")
async def search_by_image(file: UploadFile = File(...), top_k: int = 3):
    """
    사용자가 업로드한 이미지를 기반으로 유사한 CCTV 장면을 검색합니다.
    """
    # 임시 파일 저장 경로
    temp_dir = os.path.join(os.path.dirname(__file__), "..", "..", "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    temp_file_path = os.path.join(temp_dir, file.filename)
    
    try:
        # 파일 저장
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 이미지 검색 수행
        results = image_search_service.search(temp_file_path, top_k=top_k)
        
        return {
            "status": "success",
            "message": f"이미지 기반 유사도 검색 결과 {len(results)}건을 발견했습니다.",
            "results": results
        }
    except Exception as e:
        return {"status": "error", "message": f"이미지 검색 중 오류 발생: {str(e)}"}
    finally:
        # 임시 파일 삭제
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

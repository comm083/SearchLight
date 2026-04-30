import os
import shutil
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.schemas import SearchRequest, SearchResponse, HistoryResponse, AlertSimulationRequest
from app.services.search_manager import search_manager
from app.services.database import db_service
from app.services.nlp_service import nlp_service
from app.services.alert_service import alert_service
from app.services.image_search_service import image_search_service

app = FastAPI(title="SearchLight CCTV 통합 검색 API", version="3.0")

# 정적 파일 서빙
static_path = os.path.join(os.path.dirname(__file__), "..", "static")
if not os.path.exists(static_path):
    os.makedirs(static_path)
app.mount("/static", StaticFiles(directory=static_path), name="static")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/search", response_model=SearchResponse)
async def process_user_query(request: SearchRequest):
    query_text = request.query
    session_id = request.session_id

    # 1. 대화 메모리 로드
    memory = SESSION_MEMORY.get(session_id, {})
    
    # 지칭어(그, 거기, 그때 등) 탐지
    pronouns = ["그", "거기", "그때", "이전", "다시", "아까", "마지막", "방금", "방금 전"]
    has_pronoun = any(p in query_text for p in pronouns)

    # 2. NLP 전처리: 문장 교정 → 관점별 재작성 → 의도 분류 (KoELECTRA)
    preprocess = nlp_service.preprocess_query(query_text)
    corrected_query = preprocess["corrected"]
    search_query = preprocess["best_query"]   # FAISS 검색에 사용할 최적 쿼리

    # 2-1. 규칙 기반 의도 분류 (라우팅용)
    intent_result = intent_service.classify(corrected_query)
    current_intent = intent_result.intent

    # 2-1. 일상 질의(CHITCHAT) 예외 처리
    if current_intent == "CHITCHAT":
        try:
            answer = nlp_service.generate_ood_response(query_text)
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

    # 3. 시간 표현 파싱 (교정된 쿼리 기준)
    parsed_time = time_parser.parse(corrected_query)
    
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
        "results": [],
        "ai_report": None
    }

    # 🚨 [고도화] LOCALIZATION 전용 처리 (RAG를 거치지 않고 DB 최신 상태 직접 조회)
    if current_intent == "LOCALIZATION":
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
    elif current_intent in ("SUMMARIZATION", "BEHAVIORAL", "CAUSAL", "COUNTING"):
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
            ai_report = nlp_service.generate_security_report(
                query=query_text, 
                contexts=search_results,
                intent=current_intent,
                is_fallback=is_fallback,
                requested_time=time_info.get("raw", "전체 시간")
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

@app.get("/api/history/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str):
    """사용자의 이전 검색 기록 조회"""
    return {
        "status": "success",
        "history": db_service.get_search_history(session_id)
    }

@app.delete("/api/history/{history_id}")
async def delete_history(history_id: str):
    """특정 검색 기록 삭제"""
    success = db_service.delete_search_history(history_id)
    if success:
        return {"status": "success", "message": "기록이 삭제되었습니다."}
    return {"status": "error", "message": "삭제 실패"}

@app.post("/api/alerts/simulate")
async def simulate_realtime_event(request: AlertSimulationRequest):
    """이상 행동 시뮬레이션"""
    alert = alert_service.process_new_event(request.description, request.image_path)
    if alert:
        return {"status": "alert", "message": "[위험] 상황 감지!", "data": alert}
    return {"status": "normal", "message": "정상 상황"}

@app.get("/api/alerts/latest")
async def get_latest_alerts():
    """최신 알림 목록 조회"""
    return alert_service.get_latest_alerts()

@app.post("/api/stt")
async def speech_to_text(file: UploadFile = File(...)):
    """OpenAI Whisper를 사용한 음성 인식"""
    temp_dir = os.path.join(os.path.dirname(__file__), "..", "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    temp_file_path = os.path.join(temp_dir, f"stt_{file.filename}")
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        text = nlp_service.transcribe_audio(temp_file_path)
        return {"status": "success", "text": text}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/api/search/image")
async def search_by_image(file: UploadFile = File(...), top_k: int = 3):
    """이미지 기반 유사 장면 검색"""
    temp_dir = os.path.join(os.path.dirname(__file__), "..", "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    temp_file_path = os.path.join(temp_dir, file.filename)
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        results = image_search_service.search(temp_file_path, top_k=top_k)
        return {
            "status": "success",
            "message": f"검색 결과 {len(results)}건 발견",
            "results": results
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

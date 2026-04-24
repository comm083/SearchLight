# 🔦 SearchLight - CCTV 자연어 의미 검색 시스템

> **마지막 업데이트: 2026-04-24**

자연어로 CCTV 영상을 검색할 수 있는 AI 기반 통합 검색 시스템입니다.
사용자가 "빨간 옷 입은 사람 찾아줘"라고 입력하면, AI가 의도를 파악하고 관련 CCTV 장면을 의미 기반으로 검색하여 보여줍니다.

---

## 🎯 프로젝트 목표

**보안 특화 NLP 기술(의도 분류·시간 파싱)**을 결합하여, 방대한 CCTV 이벤트 데이터를 대화형으로 분석하고 상황별 맞춤 응답을 생성하는 **RAG 기반 지능형 보안 보조 시스템** 구축.

### 📌 해결하려는 문제

| 문제 | 설명 |
| :--- | :--- |
| **인간적 오류 (Human Error)** | CCTV 관제는 장시간 모니터링 과정에서 중요한 장면을 놓치거나 잘못 해석하는 오류가 발생할 수 있다. 이러한 인간적 오류는 사건 대응의 지연이나 부정확한 판단으로 이어져 보안 시스템의 신뢰성을 저하시킨다. |
| **장시간의 CCTV 기록** | 6~8시간 이상의 긴 영상 기록은 사건 발생 시점을 정확히 기억하거나 기록하지 않으면, 다시 확인하는 데 많은 시간이 소요된다. |
| **비직관적인 인터페이스** | 기존 CCTV 시스템은 전문가 중심으로 설계되어 있어 일반 사용자가 쉽게 사용하기 어렵다. 이로 인해 원하는 정보를 빠르게 찾기 힘들고, 상황 대응이 지연될 수 있다. |

### 🔧 핵심 기술 스택

| 기술 | 역할 |
| :--- | :--- |
| **KoELECTRA (의도 분류)** | 사용자 질의의 목적(조회/위험/장애/출입/일상)을 5종으로 분류 |
| **시간 파싱 (Time Parsing)** | "어제 오후 3시", "3일 전 오전 10시" 같은 자연어 시간 표현을 정확한 datetime으로 변환 |
| **FAISS (벡터 검색)** | 자연어 질의와 유사한 CCTV 장면 묘사 텍스트를 의미 기반으로 검색 |
| **RAG (검색 증강 생성)** | 검색된 CCTV 데이터를 컨텍스트로 활용하여 상황별 맞춤 자연어 응답 생성 |
| **Supabase (클라우드 DB)** | 검색 로그 및 이벤트 데이터 저장 |

---

## 🗂️ 프로젝트 구조

```
SearchLight/
├── ai/
│   ├── data/                   # 공유 데이터 (scene_descriptions.json 등)
│   ├── intent_classifier/      # C담당: KoELECTRA 의도 분류 모듈
│   └── vector_search/          # B담당: FAISS 벡터 검색 모듈
├── backend/                    # FastAPI 백엔드 서버
│   ├── app/
│   │   ├── main.py             # API 엔드포인트 (/api/search)
│   │   └── services/           # DB, 의도분류, 벡터검색 서비스 모듈
│   └── static/images/          # CCTV 예시 이미지 70장 보관
├── database/                   # A담당: SQLite 정형 데이터 관리
├── frontend/                   # React 프론트엔드 (Vite + Tailwind)
└── .env                        # API 키 등 환경변수 (GitHub 비공개)
```

---

## 📊 전체 프로젝트 진행 현황

> **범례**: ✅ 완료 | 🔄 진행중 | ⬜ 미착수

### 🔗 시스템 통합 (Integration)

| 항목 | 상태 | 비고 |
| :--- | :---: | :--- |
| FastAPI 백엔드 서버 구동 | ✅ | `/api/search` 엔드포인트 정상 작동 |
| FAISS 벡터 검색 → 백엔드 연동 | ✅ | 150건 장면 묘사 데이터 로드 및 검색 작동 |
| KoELECTRA 의도 분류 → 백엔드 연동 | ✅ | 임시 모델로 API 연동 완료 |
| Supabase 클라우드 DB 연동 | ✅ | 검색 로그 정상 저장 확인 |
| React 프론트엔드 UI 구현 | ✅ | 다크 테마, 애니메이션, 이미지 카드 UI 완성 |
| React 프론트엔드 ↔ 백엔드 연결 | ✅ | Vite 프록시 설정 완료, API 통신 정상 |
| 이미지 static 서빙 설정 | ✅ | `backend/static/images/` 경로로 70장 서빙 중 |
| 검색 결과에 이미지 경로 연동 | ✅ | `scene_descriptions.json`에 `image_path` 매핑 완료 |
| API 키 환경변수(.env) 보안 처리 | ✅ | .gitignore 등록 완료 |

---

### 👤 A. 정형 데이터 & 인프라 (`database/`)

| 항목 | 상태 | 비고 |
| :--- | :---: | :--- |
| `yolo_events` DB 스키마 설계 | ⬜ | SQLite 테이블 생성 필요 |
| 가상 이벤트 데이터 480건 삽입 | ⬜ | 시뮬레이션용 더미 데이터 |
| 시간 기반 정밀 필터링 쿼리 구현 | ⬜ | 분 단위 쿼리 로직 |
| 검색 API에서 시간 필터 파라미터 수용 | ⬜ | `/api/search`에 `start_time`, `end_time` 파라미터 추가 |

---

### 👤 B. 비정형 데이터 & 벡터 검색 (`ai/vector_search/`)

| 항목 | 상태 | 비고 |
| :--- | :---: | :--- |
| 장면 묘사 데이터셋 구축 | ✅ | 150건 (`scene_descriptions.json`) 완성 |
| Sentence-Transformers 임베딩 파이프라인 | ✅ | KR-SBERT 모델 활용 |
| FAISS 인덱스 생성 및 Top-K 검색 | ✅ | 백엔드 서비스로 통합 완료 |
| 예시 사진 70장 경로 DB 연동 | ✅ | `scene_descriptions.json`에 `image_path` 필드 추가 완료 |
| 검색 결과에서 이미지 URL 반환 | ✅ | `vector_search.py` 수정 완료 |

---

### 👤 C. 의도 분류 & 데이터 증강 (`ai/intent_classifier/`)

| 항목 | 상태 | 비고 |
| :--- | :---: | :--- |
| 의도 분류 API 모듈 백엔드 연동 | ✅ | `intent_classifier.py` 서비스 연동 완료 |
| 현재 모델 성능 수치화 | ✅ | **정확도 20.0%** (파인튜닝 필요 확인) |
| 데이터 증강 스크립트 작성 | ✅ | `data_augmentation.py` (OpenAI gpt-4o-mini 사용) |
| 수동 학습 데이터 기초 구축 | ✅ | 카테고리별 20건씩 **총 100건** `intent_dataset.csv` 생성 |
| KoELECTRA 파인튜닝 학습 스크립트 | ✅ | `train.py` 작성 완료 |
| OpenAI API 결제 완료 | ✅ | `gpt-4o-mini` 사용 가능 (약 13~15원/500건) |
| **GPT 데이터 증강 실행 (300건 목표)** | 🔄 | **⭐ 지금 바로 실행 가능!** `python ai/intent_classifier/data_augmentation.py` |
| KoELECTRA 파인튜닝 실행 | ⬜ | 증강 완료 즉시 실행: `python ai/intent_classifier/train.py` |
| 파인튜닝 후 성능 재평가 | ⬜ | `evaluate_current_model.py` 재실행 → 90%+ 목표 |
| 학습된 모델로 백엔드 교체 | ⬜ | `intent_classifier.py`의 모델 경로를 `ai/model/koelectra_finetuned`로 변경 |
| 5가지 의도 카테고리 전체 지원 | ⬜ | `classify()` 함수가 현재 SEARCH/GENERAL 2종만 반환 → 5종으로 확장 |

---

## 🚨 지금 당장 실행할 순서 (결제 완료!)

```bash
# [1단계] 데이터 증강 실행 (약 2~3분, 비용 13원 내외)
python ai/intent_classifier/data_augmentation.py

# [2단계] 모델 학습 (약 5~10분)
python ai/intent_classifier/train.py

# [3단계] 성능 확인
python ai/intent_classifier/evaluate_current_model.py

# [4단계] 백엔드 재시작 (새 모델 반영)
# backend/app/services/intent_classifier.py 모델 경로 수정 후:
.\searchlight\Scripts\python.exe -m uvicorn --app-dir backend app.main:app --host 127.0.0.1 --port 8000
```

---

## 📋 발표 전 최종 체크리스트

| 항목 | 상태 |
| :--- | :---: |
| 파인튜닝 모델로 "주차장 화면 보여줘" 정상 검색되는지 확인 | ⬜ |
| 검색 결과에 이미지가 실제로 출력되는지 확인 | ⬜ |
| A 파트 SQLite DB 연동 및 시간 필터 작동 확인 | ⬜ |
| 발표용 Before/After 정확도 비교 화면 캡처 (20% → 90%+) | ⬜ |
| 팀원 전체 로컬 환경에서 서버 구동 테스트 | ⬜ |

## ⚡ 빠른 시작 (Quick Start)

```bash
# 가상환경 활성화
.\searchlight\Scripts\Activate.ps1

# 백엔드 서버 실행 (루트 폴더에서)
.\searchlight\Scripts\python.exe -m uvicorn --app-dir backend app.main:app --host 127.0.0.1 --port 8000

# 프론트엔드 서버 실행 (새 터미널)
cd frontend
npm run dev
# → http://localhost:3000 접속


# 학습 데이터 증강 (OpenAI 크레딧 필요)
python ai/intent_classifier/data_augmentation.py

# 모델 학습 (데이터 300건 확보 후)
python ai/intent_classifier/train.py
```

---

## 👥 팀 역할 분담

| 개발자 | 담당 역할 | 핵심 기술 스택 | 주요 결과물 |
| :--- | :--- | :--- | :--- |
| **A (Data 엔지니어)** | 정형 데이터 & 인프라 | SQLite, Pandas, FastAPI | `yolo_events` DB, 시간 기반 필터링 모듈 |
| **B (AI 엔지니어 - 검색)** | 비정형 데이터 & RAG | FAISS, Sentence-Transformers | `scene_descriptions` 벡터 인덱스, 검색 엔진 |
| **C (AI 엔지니어 - NLP)** | 의도 분류 & 데이터 증강 | KoELECTRA, PyTorch, GPT API | `Intent Dataset`, 질문 분류 모델(5종) |

# Intent Classifier

사용자 질의의 의도를 5가지 카테고리로 분류하는 KoELECTRA 모델 관련 코드와 학습셋이 저장되는 공간입니다. (개발자 C 관리)

## C. 세부 과제 체크리스트

> 마지막 업데이트: 2026-04-24

### ✅ 완료된 작업

- [x] **백엔드 의도 분류 모듈 연동**: `backend/app/services/intent_classifier.py` 구현 완료. FastAPI에서 KoELECTRA 호출 정상 작동 확인.
- [x] **Supabase 클라우드 DB 연동**: `database.py` 통해 검색 로그(query, intent) Supabase에 정상 저장 확인.
- [x] **FAISS 벡터 검색 연동**: `scene_descriptions.json` 150건 로드 및 의미 기반 검색 정상 작동 확인.
- [x] **현재 모델 성능 수치화**: `evaluate_current_model.py` 작성 및 실행. 현재 정확도 **20.0% (10개 중 2개 정답)** 측정 완료.
- [x] **데이터 증강 스크립트 준비**: `data_augmentation.py` OpenAI 최신 문법(v2.x)으로 수정 완료.

---

### 🔴 진행 중 / 해야 할 작업 (필수)

- [ ] **학습 데이터 확보** *(최우선)*: OpenAI API 크레딧 부족으로 자동 증강 실패. 아래 두 방법 중 하나 선택:
  - 옵션 A: OpenAI 계정에 크레딧 충전 후 `data_augmentation.py` 실행
  - 옵션 B: 수동 또는 다른 도구로 카테고리별 최소 50~60건씩, 총 300건 CSV 작성
- [ ] **KoELECTRA 파인튜닝 학습**: 확보된 데이터셋(`intent_dataset.csv`)으로 `train.py` 작성 후 모델 학습. (목표 정확도: 90% 이상)
- [ ] **학습된 모델로 백엔드 교체**: `intent_classifier.py`에서 현재 임시 NSMC 모델을 파인튜닝 모델로 교체.

---

### 💡 추가 권장 작업 (발표 퀄리티 향상)

- [ ] **발표용 성능 비교 그래프 생성**: 학습 전(20%) vs 학습 후(90%+) 정확도를 막대 그래프로 시각화 (matplotlib 활용)
- [ ] **예시 사진/영상 클립 DB 연동**: 검색 결과에 CCTV 예시 이미지 경로를 함께 반환하도록 `scene_descriptions.json` 및 API 수정
- [ ] **5가지 의도 카테고리 전체 지원**: 현재 모델은 SEARCH/GENERAL 2종만 반환. 학습 후 조회/위험/장애/출입/일상 5종 전부 지원하도록 `classify()` 함수 수정
- [ ] **API 키 환경변수 처리**: `data_augmentation.py`에 하드코딩된 API 키를 `.env` 파일로 분리 (보안)

---

## 역할 분담 및 담당 영역

| 개발자                     | 담당 역할                   | 핵심 기술 스택               | 주요 결과물                                 |
| :------------------------- | :-------------------------- | :--------------------------- | :------------------------------------------ |
| **A (Data 엔지니어)**      | **정형 데이터 & 인프라**    | SQLite, Pandas, FastAPI      | `yolo_events` DB, 시간 기반 필터링 모듈     |
| **B (AI 엔지니어 - 검색)** | **비정형 데이터 & RAG**     | FAISS, Sentence-Transformers | `scene_descriptions` 벡터 인덱스, 검색 엔진 |
| **C (AI 엔지니어 - NLP)**  | **의도 분류 & 데이터 증강** | KoELECTRA, PyTorch, GPT API  | `Intent Dataset`, 질문 분류(5종)       |

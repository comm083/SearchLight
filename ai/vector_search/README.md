# Vector Search (Semantic Search)

비정형 장면 묘사 데이터를 벡터화하고 FAISS 인덱스를 관리하는 모듈입니다. (개발자 B 관리)

## B. 세부 과제 체크리스트

- [ ] **장면 묘사 데이터셋**: 50건 이상 영상 상황 텍스트 준비.
- [ ] **임베딩 파이프라인**: Sentence-Transformers 기반 벡터 변환.
- [ ] **FAISS 벡터 스토어**: 인덱스 생성 및 Top-K 검색 로직 구현.

## 역할 분담 및 담당 영역

| 개발자                     | 담당 역할                   | 핵심 기술 스택               | 주요 결과물                                 |
| :------------------------- | :-------------------------- | :--------------------------- | :------------------------------------------ |
| **A (Data 엔지니어)**      | **정형 데이터 & 인프라**    | SQLite, Pandas, FastAPI      | `yolo_events` DB, 시간 기반 필터링 모듈     |
| **B (AI 엔지니어 - 검색)** | **비정형 데이터 & RAG**     | FAISS, Sentence-Transformers | `scene_descriptions` 벡터 인덱스, 검색 엔진 |
| **C (AI 엔지니어 - NLP)**  | **의도 분류 & 데이터 증강** | KoELECTRA, PyTorch, GPT API  | `Intent Dataset`, 질문 분류 모델(5종)       |

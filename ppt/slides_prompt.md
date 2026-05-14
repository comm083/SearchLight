# SearchLight PPT — Genspark 프롬프트

---

## Genspark 한 번에 생성용 프롬프트

아래 전체를 복사해서 Genspark에 붙여넣으세요.

---

```
Create a professional dark-themed presentation for an AI security surveillance system called "SearchLight".

Project overview:
SearchLight is a RAG-based intelligent CCTV security analysis system that combines computer vision (VLM) and natural language processing (NLP) to automatically detect security events from CCTV footage and answer natural language queries from security operators.

Team: 1팀 윤이버스 (TheSearchLight) — 김도윤, 이건영
Branding: Show "AI SECURITY / REPORT" on top-left and "YOON-E-VERSE" on top-right of every slide.
Design: Dark navy background (#01121F), cyan/teal accent color (#00D2D7), white text, rounded card components.

Generate the following 4 slides:

---

Slide 1 title: "VLM Processing Pipeline"
Subtitle: "영상 분석 자동화 처리 흐름"
Layout: Horizontal flowchart with 6 connected steps, each step as a dark card with cyan border and arrow connectors.

Step 1 — CCTV Input
  Icon: camera
  Description: CCTV 영상 입력

Step 2 — YOLOv8 / YOLO-World
  Icon: detection/radar
  Role: Object Detection
  Detail: 인물 · 차량 · 사물 탐지

Step 3 — VideoMAE (fine-tuned)
  Icon: film/video
  Role: Video Classification
  Detail: 7-class · val_acc 99.3%

Step 4 — CLIP ViT-B/32
  Icon: image layers
  Role: Image Embedding
  Detail: 객체 이미지 임베딩

Step 5 — EasyOCR
  Icon: text scan
  Role: Timestamp OCR
  Detail: CCTV 시각 정보 추출

Step 6 — GPT-4o Vision
  Icon: AI star
  Role: Frame Analysis & Description
  Detail: 이벤트 설명 자동 생성

Footer: "Ultralytics · HuggingFace · OpenAI"

---

Slide 2 title: "NLP Processing Pipeline"
Subtitle: "자연어 질의 처리 및 보안 보고서 생성 흐름"
Layout: Horizontal flowchart with 6 connected steps, teal/green (#48D29B) accent color for this slide.

Step 1 — 사용자 질의
  Icon: microphone / chat bubble
  Description: 음성 또는 텍스트 입력

Step 2 — KoBART
  Icon: text correction
  Role: STT 교정
  Detail: 음성 인식 후 텍스트 보정

Step 3 — KoELECTRA (fine-tuned)
  Icon: classification/tag
  Role: Intent Classification
  Detail: 6-class 의도 분류

Step 4 — KR-SBERT
  Icon: vector/graph
  Role: Korean Text Embedding
  Detail: snunlp/KR-SBERT-V40K

Step 5 — FAISS
  Icon: search/magnifier
  Role: Vector Similarity Search
  Detail: 이벤트 DB 벡터 검색

Step 6 — GPT-4o
  Icon: document / AI
  Role: Security Report Generation
  Detail: 보안 보고서 자동 생성

Footer: "HuggingFace · Meta AI · OpenAI"

---

Slide 3 title: "Intent Classification — KoELECTRA"
Subtitle: "6종 의도 분류 · fine-tuned on security domain"
Layout: 2-column 3-row card grid. Each card has a colored top badge with intent name, example user query, and DB routing method.

Card 1 (cyan border)
  Badge: COUNTING
  Example: "몇 명이 지나갔어? / 차량 몇 대야?"
  Routing: SQLite COUNT 쿼리

Card 2 (blue border)
  Badge: SUMMARIZATION
  Example: "어제 무슨 일 있었어?"
  Routing: FAISS 벡터 검색 + RAG

Card 3 (purple border)
  Badge: LOCALIZATION
  Example: "지금 주차장 어때?"
  Routing: SQLite 최신 레코드

Card 4 (orange border)
  Badge: BEHAVIORAL
  Example: "수상한 사람 없었어?"
  Routing: 이벤트 필터 + FAISS

Card 5 (red border)
  Badge: CAUSAL
  Example: "왜 알림이 울렸어?"
  Routing: SQLite + FAISS 결합

Card 6 (gray border)
  Badge: CHITCHAT
  Example: "안녕 / 뭐해?"
  Routing: GPT-4o 직접 응답

---

Slide 4 title: "VideoMAE — 영상 이벤트 분류"
Subtitle: "MCG-NJU/videomae-base · fine-tuned · 7-class"
Layout: Left 60% shows 7 classification class badges in vertical list. Right 40% shows model performance metrics card.

Left — 7 class badges (each a wide rounded pill with colored left border and icon):
  assault    — 폭행 / 충돌
  break      — 파손 / 기물 손괴
  theft      — 절도 / 도난
  smoking    — 흡연 감지
  falling    — 낙상 / 쓰러짐
  disaster   — 재난 / 화재
  normal     — 정상 상황

Right — Performance metrics card (dark card, cyan numbers):
  Validation Accuracy : 99.3%
  Best Epoch          : 17
  Num Frames / Clip   : 16
  Input Resolution    : 224 x 224
  Training Videos     : 1,400+
  Classes             : 7
```

---

## 슬라이드 추가 작성란

### [슬라이드 5]
```
Slide 5 title: "Software & Frameworks"
Subtitle: "SearchLight 시스템 구성 기술 스택"
Layout: 2 main columns (VLM, NLP) and 1 bottom strip for Common Infrastructure/Frontend.

Left Column (VLM) - Cyan border (#00D2D7):
- YOLOv8 / YOLO-World (Object Detection)
- VideoMAE (Video Classification, 7-class, 99.3%)
- CLIP ViT-B/32 (Image Embedding)
- EasyOCR (CCTV Timestamp OCR)
- GPT-4o Vision (Frame Analysis)

Right Column (NLP) - Green border (#48D29B):
- KoELECTRA (Intent Classification, 6-class)
- KR-SBERT (Korean Text Embedding)
- KoBART (STT Post-correction)
- GPT-4o (Security Report Generation)

Bottom Strip (Common/Infra):
- Backend: FastAPI
- Cloud DB: Supabase
- Event DB: SQLite
- Vector DB: FAISS
- Frontend/UI: React, Tailwind CSS, Recharts, Framer Motion
- Dev Tools: VS Code, GitHub
```

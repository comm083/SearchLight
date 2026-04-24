# 🤖 AI 의도 분류 모델(KoELECTRA) 개발 계획

이 문서는 SearchLight 프로젝트의 KoELECTRA 기반 의도 분류 모델을 우리 CCTV 도메인에 맞게 학습시키기 위한 향후 작업 단계를 정리한 문서입니다.

---

## 📌 Phase 1: 학습 데이터 구축 및 증강 (Data Augmentation)

현재 엉뚱한 의도 분류 결과를 내는 원인은 학습 데이터의 부족 및 도메인 불일치입니다. 이를 해결하기 위해 CCTV 도메인에 맞는 맞춤형 데이터를 구축해야 합니다.

- **작업 파일**: `ai/intent_classifier/data_augmentation.py`
- **주요 작업 내용**:
  1. **카테고리 정의**: `조회`, `위험`, `장애`, `출입`, `일상` 5가지 카테고리 확립.
  2. **시드 데이터 작성**: 각 카테고리별로 실제 사용자가 자주 검색할 법한 기본 질문들을 수동으로 일부 작성합니다.
  3. **GPT 데이터 증강**: OpenAI API(GPT-3.5/4)를 활용해 카테고리별로 충분한 양의 질문(발화) 데이터를 자동 생성(Augmentation)합니다.
  4. **데이터셋 완성**: 수동 데이터와 증강 데이터를 결합하여 최종 학습용 데이터셋인 `intent_dataset.csv`를 생성합니다.

> [!TIP]
> API 호출 비용 절감을 위해 처음에는 소규모(클래스당 20~30개)로 증강하여 형태를 확인한 후, 이상이 없으면 본격적으로 대량(클래스당 100~200개) 생성하는 것을 권장합니다.

---

## 🛠️ Phase 2: KoELECTRA 모델 파인튜닝 (Fine-Tuning)

완성된 데이터셋을 바탕으로 KoELECTRA 모델을 재학습시킵니다.

- **추가/작업할 파일**: `ai/intent_classifier/train.py` (신규 생성 필요)
- **주요 작업 내용**:
  1. **데이터 전처리**: `intent_dataset.csv`를 불러와 HuggingFace 토크나이저를 사용해 텍스트를 토큰화합니다.
  2. **모델 학습**: `transformers` 라이브러리의 `Trainer`를 활용하여 KoELECTRA(`monologg/koelectra-base-v3-discriminator` 등) 모델을 학습시킵니다.
  3. **모델 평가 및 저장**: 정확도(Accuracy) 등 성능을 검증한 뒤, 가장 성능이 좋은 모델 가중치와 토크나이저를 로컬 폴더(예: `ai/models/koelectra_finetuned`)에 저장합니다.

> [!WARNING]
> 학습 환경은 GPU가 지원되는 환경(로컬 GPU 또는 Google Colab)에서 진행하는 것이 속도 면에서 유리합니다.

---

## 🔗 Phase 3: 백엔드 시스템 연동 (Integration & Test)

학습이 끝난 모델을 실제 서비스 백엔드에 연동합니다.

- **작업 파일**: `backend/app/services/intent_classifier.py`
- **주요 작업 내용**:
  1. 기존에 기본 모델이나 임시 로직으로 구현되어 있던 코드를 방금 학습하고 저장한 파인튜닝 모델로 교체합니다.
  2. 서버 시작 시 해당 모델을 로드하도록 설정합니다.
  3. API 엔드포인트(`/api/search`)를 호출하여 `"빨간 옷 입은 사람 찾아줘"`와 같은 쿼리가 정상적으로 `조회(SEARCH)`로 분류되는지 최종 테스트합니다.

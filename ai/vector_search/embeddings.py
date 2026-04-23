from sentence_transformers import SentenceTransformer

def run_test_embedding():
    # 1. 한국어 텍스트 임베딩에 적합한 사전학습 모델 로드 (허깅페이스)
    # 'snunlp/KR-SBERT-V40K-klueNLI-augSTS' 는 한국어 검색/유사도에 성능이 좋은 가벼운 모델입니다.
    print("모델을 로드하는 중입니다... (최초 실행 시 모델 다운로드로 인해 시간이 조금 걸릴 수 있습니다)")
    model = SentenceTransformer('snunlp/KR-SBERT-V40K-klueNLI-augSTS')

    # 2. 테스트용 더미 데이터 (CCTV 장면 묘사 텍스트)
    sample_descriptions = [
        "빨간색 패딩을 입은 남자가 골목길을 급하게 뛰어감",
        "검은색 세단이 신호를 위반하고 교차로를 지나감",
        "파란색 모자를 쓴 사람이 자전거를 타고 횡단보도를 건넘",
        "두 사람이 편의점 앞에서 대화를 나누고 있음",
        "밤늦게 한 여성이 스마트폰을 보며 걸어가고 있음"
    ]

    print(f"\n총 {len(sample_descriptions)}개의 텍스트를 벡터로 변환합니다...")

    # 3. 텍스트를 벡터(임베딩)로 변환
    embeddings = model.encode(sample_descriptions)

    # 4. 결과 확인
    print("\n=== 벡터 변환(임베딩) 완료 ===")
    print(f"생성된 벡터의 형태(Shape): {embeddings.shape}")
    print(f" -> {embeddings.shape[0]}개의 문장이 각각 {embeddings.shape[1]}차원의 숫자 배열로 변환되었습니다.")

    print("\n첫 번째 텍스트('빨간색 패딩을 입은 남자가...')의 벡터 값 일부 미리보기:")
    print(embeddings[0][:5], "... (생략)")

if __name__ == "__main__":
    run_test_embedding()

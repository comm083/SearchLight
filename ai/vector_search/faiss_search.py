import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

def run_faiss_search():
    print("1. 모델 로드 중...")
    model = SentenceTransformer('snunlp/KR-SBERT-V40K-klueNLI-augSTS')

    # 데이터베이스에 저장될 기존 CCTV 데이터(문장들)
    db_descriptions = [
        "빨간색 패딩을 입은 남자가 골목길을 급하게 뛰어감",
        "검은색 세단이 신호를 위반하고 교차로를 지나감",
        "파란색 모자를 쓴 사람이 자전거를 타고 횡단보도를 건넘",
        "두 사람이 편의점 앞에서 대화를 나누고 있음",
        "밤늦게 한 여성이 스마트폰을 보며 걸어가고 있음"
    ]

    print("2. 기존 데이터베이스 문장들을 벡터로 변환 중...")
    # FAISS는 numpy의 float32 타입을 사용해야 합니다.
    db_embeddings = model.encode(db_descriptions).astype('float32')
    
    # 3. FAISS 인덱스 생성
    dimension = db_embeddings.shape[1] # 768차원
    index = faiss.IndexFlatL2(dimension) # 유클리디안 거리(거리값이 작을수록 유사) 기반 검색
    
    # 4. 벡터 데이터를 FAISS에 추가
    index.add(db_embeddings)
    print(f"-> FAISS 인덱스에 {index.ntotal}개의 데이터가 성공적으로 저장되었습니다.\n")

    # 5. 새로운 사용자 검색어 입력
    query_text = "빨간 옷 입고 뛰어가는 사람"
    print(f"▶ 검색어: '{query_text}'")
    
    # 검색어를 동일하게 벡터로 변환
    query_embedding = model.encode([query_text]).astype('float32')

    # 6. FAISS에서 가장 유사한 문장 찾기 (상위 2개 추출)
    k = 2
    distances, indices = index.search(query_embedding, k)

    print("\n=== 검색 결과 ===")
    for i in range(k):
        # indices[0][i] : 가장 유사한 문장의 원본 리스트 내 위치(인덱스)
        # distances[0][i] : 얼마나 비슷한지를 나타내는 거리 점수 (낮을수록 비슷함)
        idx = indices[0][i]
        distance = distances[0][i]
        print(f"[순위 {i+1}] {db_descriptions[idx]} (거리 점수: {distance:.4f})")

if __name__ == "__main__":
    run_faiss_search()

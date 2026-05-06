from ultralytics import YOLO

def detect_with_yolov8(image_path: str, model_path: str = "yolov8n.pt"):
    """
    YOLOv8 기본/파인튜닝 모델을 이용한 객체 탐지 함수
    
    Args:
        image_path (str): 분석할 이미지의 경로
        model_path (str): 사용할 YOLOv8 모델 가중치 경로 
            (기본값인 yolov8n.pt는 80개 기본 클래스(사람 등)만 탐지합니다.
             직접 '열린 문' 사진을 모아서 학습시킨 후에는 생성된 'best.pt' 경로로 이 값을 변경해야 합니다.)
             
    Returns:
        결과 객체(Results). 바운딩 박스 정보 및 결과 이미지를 포함합니다.
    """
    print(f"[YOLOv8] 모델({model_path})을 로드합니다...")
    model = YOLO(model_path)
    
    print(f"[YOLOv8] '{image_path}' 이미지를 분석합니다...")
    # confidence 0.25 이상인 객체만 탐지
    results = model(image_path, conf=0.25)
    
    # 분석된 이미지를 저장합니다. (results[0].show() 로 화면에 바로 띄울 수도 있습니다)
    for result in results:
        # 결과 이미지 파일명 생성 (예: yolov8_result_test.jpg)
        filename = image_path.split('\\')[-1].split('/')[-1]
        save_path = f"yolov8_result_{filename}"
        result.save(filename=save_path)
        
        print(f"[YOLOv8] 분석 완료! 찾은 객체 수: {len(result.boxes)}")
        print(f"[YOLOv8] 결과 이미지가 '{save_path}'에 저장되었습니다.\n")
        
    return results

if __name__ == "__main__":
    # [사용 예시]
    # 아래 주석을 풀고 테스트용 이미지 경로를 넣어서 실행해보세요.
    # detect_with_yolov8("sample_image.jpg")
    pass

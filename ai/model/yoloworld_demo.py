from ultralytics import YOLOWorld

def detect_with_yoloworld(image_path: str, custom_classes: list = ["person", "open door", "closed door"]):
    """
    YOLO-World 모델을 이용한 텍스트 프롬프트 기반 Zero-Shot 객체 탐지 함수
    별도의 데이터 학습 없이, 텍스트(영문)만으로 원하는 객체를 즉시 탐지할 때 사용합니다.
    
    Args:
        image_path (str): 분석할 이미지의 경로
        custom_classes (list): 찾고자 하는 객체들의 영어 텍스트 리스트
        
    Returns:
        결과 객체(Results). 바운딩 박스 정보 및 결과 이미지를 포함합니다.
    """
    print("[YOLO-World] 모델(yolov8s-world.pt)을 로드합니다. (최초 실행 시 다운로드됨)...")
    # yolov8s-world.pt (Small) 모델 사용
    model = YOLOWorld("yolov8s-world.pt")
    
    print(f"[YOLO-World] 찾을 객체(클래스) 설정: {custom_classes}")
    model.set_classes(custom_classes)
    
    print(f"[YOLO-World] '{image_path}' 이미지를 분석합니다...")
    # confidence 0.1 이상의 객체 탐지 (텍스트 기반이므로 임계치를 조금 낮게 주는 것이 유리할 수 있음)
    results = model(image_path, conf=0.1)
    
    # 분석된 이미지를 저장합니다. (results[0].show() 로 화면에 바로 띄울 수도 있습니다)
    for result in results:
        # 결과 이미지 파일명 생성 (예: yoloworld_result_test.jpg)
        filename = image_path.split('\\')[-1].split('/')[-1]
        save_path = f"yoloworld_result_{filename}"
        result.save(filename=save_path)
        
        print(f"[YOLO-World] 분석 완료! 찾은 객체 수: {len(result.boxes)}")
        print(f"[YOLO-World] 결과 이미지가 '{save_path}'에 저장되었습니다.\n")
        
    return results

if __name__ == "__main__":
    # [사용 예시]
    # 아래 주석을 풀고 테스트용 이미지 경로와 찾고 싶은 텍스트를 입력해서 실행해보세요.
    # detect_with_yoloworld("sample_image.jpg", ["person", "open door", "laptop"])
    pass

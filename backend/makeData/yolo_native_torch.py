import cv2
import numpy as np
import time
import torch
from ultralytics import YOLO

def get_device():
    """PyTorch 2.9+ 네이티브 XPU 장치 감지"""
    if hasattr(torch, "xpu") and torch.xpu.is_available():
        return torch.device("xpu")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")

def main():
    # 1. 장치 설정
    device = get_device()
    print(f"\n" + "="*40)
    print(f"활성화된 추론 장치: {device}")
    print("="*40 + "\n")

    # 2. 모델 로드 및 최적화
    pt_weights = "yolov5su.pt"
    try:
        # YOLOv5 정수(su) 모델 로드 및 XPU 이동
        yolo = YOLO(pt_weights)
        model = yolo.model.to(device)
        model.eval()

            
        classes = yolo.names
    except Exception as e:
        print(f"모델 초기화 중 오류 발생: {e}")
        return

    # 3. 카메라 설정
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("카메라를 감지할 수 없습니다.")
        return

    prev_time = 0
    print(f"--- 실시간 추론 시작 (Device: {device}) ---")

    while True:
        ret, frame = cap.read()
        if not ret: break

        raw_h, raw_w = frame.shape[:2]
        
        # 4. 전처리 (PyTorch 표준 텐서 규격)
        # 640x640 리사이즈 -> BGR2RGB -> HWC to CHW -> Float32 변환 및 정규화
        input_img = cv2.resize(frame, (640, 640))
        input_img = cv2.cvtColor(input_img, cv2.COLOR_BGR2RGB)
        input_img = input_img.transpose(2, 0, 1)
        
        # 텐서 생성 및 선택된 장치(XPU)로 전송
        input_tensor = torch.from_numpy(input_img).to(device).float() / 255.0
        input_tensor = input_tensor.unsqueeze(0)  # [1, 3, 640, 640]

        # 5. 추론 실행
        with torch.no_grad():
            # XPU 환경에서의 네이티브 추론
            results = model(input_tensor)
            
            # 결과값 정제 (YOLO 출력 텐서 처리)
            if isinstance(results, (list, tuple)):
                detections = results[0]
            else:
                detections = results

            # 후처리를 위해 데이터 가공 (CPU로 이동 후 넘파이 변환)
            detections = detections[0].detach().cpu().numpy().T 

        # 6. 후처리 (박스 좌표 복원 및 NMS)
        boxes, confidences, class_ids = [], [], []
        for row in detections:
            # row 구성: [x, y, w, h, class_0_score, class_1_score, ...]
            score = row[4:]
            conf = np.max(score)
            
            if conf > 0.4:  # 신뢰도 임계값
                class_id = np.argmax(score)
                cx, cy, w, h = row[:4]
                
                # 좌표 변환: Center -> Top-Left 및 원본 해상도 맵핑
                x1 = int((cx - w/2) * raw_w / 640)
                y1 = int((cy - h/2) * raw_h / 640)
                w_box = int(w * raw_w / 640)
                h_box = int(h * raw_h / 640)
                
                boxes.append([x1, y1, w_box, h_box])
                confidences.append(float(conf))
                class_ids.append(class_id)

        # OpenCV NMSBoxes를 활용한 중복 제거
        indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.4, 0.45)

        # 7. 시각화
        if len(indices) > 0:
            for i in indices.flatten():
                x, y, w, h = boxes[i]
                label = f"{classes[class_ids[i]]}: {confidences[i]:.2f}"
                
                # 객체 박스 및 텍스트 렌더링
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, label, (x, y - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # 8. FPS 및 장치 정보 출력
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if prev_time != 0 else 0
        prev_time = curr_time
        
        display_text = f"FPS: {fps:.1f} | Device: {device.type.upper()}"
        cv2.putText(frame, display_text, (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow("PyTorch Native XPU Inference (v2.9+)", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
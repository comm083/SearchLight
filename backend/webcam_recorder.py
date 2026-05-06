"""
웹캠 녹화 스크립트
- 웹캠 영상을 녹화하여 backend/static/webcamData 에 저장
- 영상 좌측 상단에 현재 시간 표시
- 저장 파일명: webcam_YYYYMMDD_HHMMSS.mp4
- 종료: q 키 또는 창 닫기
"""

import cv2
import os
from datetime import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "static", "webcamData")
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.7
FONT_COLOR = (255, 255, 255)
FONT_THICKNESS = 2
SHADOW_COLOR = (0, 0, 0)
FPS = 30.0


def get_output_path() -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(OUTPUT_DIR, f"webcam_{timestamp}.mp4")


def draw_timestamp(frame):
    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    x, y = 10, 30
    # 그림자 효과로 가독성 향상
    cv2.putText(frame, now, (x + 1, y + 1), FONT, FONT_SCALE, SHADOW_COLOR, FONT_THICKNESS + 1, cv2.LINE_AA)
    cv2.putText(frame, now, (x, y), FONT, FONT_SCALE, FONT_COLOR, FONT_THICKNESS, cv2.LINE_AA)
    return frame


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[오류] 웹캠을 열 수 없습니다. 연결 상태를 확인하세요.")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    output_path = get_output_path()
    out = cv2.VideoWriter(output_path, fourcc, FPS, (width, height))

    print(f"[녹화 시작] 저장 경로: {output_path}")
    print("종료하려면 영상 창에서 'q' 키를 누르세요.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[오류] 프레임을 읽을 수 없습니다.")
            break

        frame = draw_timestamp(frame)
        out.write(frame)
        cv2.imshow("Webcam Recording (q: 종료)", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print(f"[녹화 완료] 저장됨: {output_path}")


if __name__ == "__main__":
    main()

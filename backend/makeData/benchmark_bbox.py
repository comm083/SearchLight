"""
바운딩 박스 방식 벤치마크: 매 프레임 YOLO vs 인터벌 캐싱
"""
import time
import cv2
from ultralytics import YOLO

VIDEO_PATH = r"c:\SearchLight\backend\static\mp4Data\samplevideo.mp4"
BOX_INTERVAL = 30   # 인터벌 캐싱: 30프레임(~1초)마다 YOLO
TEST_FRAMES  = 300  # 비교할 프레임 수 (고정)
CONF         = 0.1

model = YOLO("yolov8n.pt")
CLIP_BOX_CLASSES = {"person", "fire", "smoke", "open door", "door"}

def draw_boxes(frame, result):
    for box in result.boxes:
        cls_name = model.names[int(box.cls)]
        if cls_name not in CLIP_BOX_CLASSES:
            continue
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    return frame

# ── 방법 A: 매 프레임 YOLO (현재) ──
cap = cv2.VideoCapture(VIDEO_PATH)
yolo_calls_a = 0
t0 = time.time()
for _ in range(TEST_FRAMES):
    ok, frm = cap.read()
    if not ok:
        break
    result = model(frm, conf=CONF, verbose=False)
    draw_boxes(frm, result[0])
    yolo_calls_a += 1
elapsed_a = time.time() - t0
cap.release()

# ── 방법 B: 인터벌 캐싱 (1번 제안) ──
cap = cv2.VideoCapture(VIDEO_PATH)
cached = None
yolo_calls_b = 0
t0 = time.time()
for i in range(TEST_FRAMES):
    ok, frm = cap.read()
    if not ok:
        break
    if i % BOX_INTERVAL == 0:
        result = model(frm, conf=CONF, verbose=False)
        cached = result[0]
        yolo_calls_b += 1
    if cached is not None:
        draw_boxes(frm, cached)
elapsed_b = time.time() - t0
cap.release()

fps = TEST_FRAMES / elapsed_a

print(f"\n{'='*50}")
print(f"  테스트 프레임: {TEST_FRAMES}장  (약 {TEST_FRAMES/fps:.1f}초 분량, {fps:.1f}fps)")
print(f"  인터벌: {BOX_INTERVAL}프레임마다 탐지")
print(f"{'='*50}")
print(f"  [현재] 매 프레임 YOLO  : {elapsed_a:.2f}초  ({yolo_calls_a}회 호출)")
print(f"  [제안] 인터벌 캐싱     : {elapsed_b:.2f}초  ({yolo_calls_b}회 호출)")
print(f"  → 속도 향상            : {elapsed_a/elapsed_b:.1f}배 빠름")
print(f"  → YOLO 호출 감소       : {yolo_calls_a}회 → {yolo_calls_b}회 ({(1-yolo_calls_b/yolo_calls_a)*100:.0f}% 감소)")

# 클립 60초 기준 외삽
clip_sec = 60
frames_60s = int(fps * clip_sec)
t_current = elapsed_a / TEST_FRAMES * frames_60s
t_cached  = elapsed_b / TEST_FRAMES * frames_60s
print(f"\n  [60초 클립 예상]")
print(f"  현재    : {t_current:.0f}초 ({t_current/60:.1f}분)")
print(f"  인터벌  : {t_cached:.0f}초 ({t_cached/60:.1f}분)")
print(f"{'='*50}\n")

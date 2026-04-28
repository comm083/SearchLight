import base64
import json
import random
from datetime import datetime, timedelta
from PIL import Image
from io import BytesIO
from openai import OpenAI
import cv2
import os
import sys
from dotenv import load_dotenv
import matplotlib
matplotlib.use('Agg') # GUI 방지용
from matplotlib import pyplot as plt

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

def get_random_timestamp():
    # 현재 날짜 기준 1주일 이내 랜덤 시간 생성
    now = datetime.now()
    random_days = random.randint(0, 6)
    random_hours = random.randint(0, 23)
    random_minutes = random.randint(0, 59)
    random_seconds = random.randint(0, 59)
    
    random_date = now - timedelta(days=random_days, hours=random_hours, minutes=random_minutes, seconds=random_seconds)
    return random_date.strftime("%Y-%m-%d %H:%M:%S")

def encode_video(video_name):
    video = cv2.VideoCapture(video_name)
    fps = video.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 3.0

    interval_normal = max(1, int(fps * 10))  # 10초마다 (기본)
    interval_person = max(1, int(fps * 5))   # 5초마다 (사람 감지 시)

    # HOG 사람 감지기
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    candidates = []  # (frame_index, buffer, has_person)
    cur = 0

    while video.isOpened():
        success, frame = video.read()
        if not success:
            break

        if cur % interval_person == 0:
            small = cv2.resize(frame, (320, 240))
            rects, _ = hog.detectMultiScale(small, winStride=(8, 8))
            has_person = len(rects) > 0

            _, buffer = cv2.imencode(".jpg", frame)
            candidates.append((cur, buffer, has_person))

        cur += 1

    video.release()

    # 사람이 감지된 프레임은 5초 간격, 아니면 10초 간격만 유지
    base64frames = []
    for frame_idx, buffer, has_person in candidates:
        if has_person or frame_idx % interval_normal == 0:
            base64frames.append(base64.b64encode(buffer).decode("utf-8"))

    return base64frames


def img_classification(prompt, image_list):
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일이나 환경 변수를 확인해주세요.")
        
    client = OpenAI(api_key=api_key)

    contents=[]
    for i in range(len(image_list)):
        contents.append({
            "type": "image_url",
            "image_url":{
                "url": f"data:image/jpeg;base64,{image_list[i]}"
            }
        })

    contents.append({
        "type": "text",
        "text": prompt
    })

    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[
            {
                "role": "user",
                "content": contents
            }
        ]
    )
    return response.choices[0].message.content


prompt2 = """
당신은 프로 경비원입니다. 동영상의 프레임이 순서대로 주어집니다. 각 프레임 간의 차이점을 알려주고, 문제가 발생하는지 분석해야합니다.
경비원의 입장에서 상황을 설명하고 프레임 간 변화 요약, 의도 요약, timestamp에 영상이 찍힌 시간, 사람(person)들, 사람들의 복장, 상황 설명을 JSON으로 출력하세요.
note 설명은 한국어로 작성해주세요. 사람마다 고유한 번호를 부여하고, 옷을 입은 사람들의 복장을 정확하게 묘사하세요.
출력 예:
{
  "summary": "...",
  "frames": [
    {"timestamp": "05:12:03", "timestamp_sec": 0.0, "person": 0, "notes": "..."}
  ]
}
"""

def process_all_videos():
    # 경로 설정
    video_dir = os.path.join(os.path.dirname(__file__), "..", "static", "mp4Data")
    output_path = os.path.join(os.path.dirname(__file__), "..", "..", "ai", "data", "mp4_JsonData.json")
    
    # 디렉토리 존재 확인
    if not os.path.exists(video_dir):
        print(f"오류: 영상 디렉토리를 찾을 수 없습니다: {video_dir}")
        return

    # 기존 데이터 로드 (증분 처리용)
    all_data = []
    processed_filenames = set()
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
                processed_filenames = {item["video_filename"] for item in all_data}
            print(f"기존 데이터를 불러왔습니다. ({len(all_data)}건)")
        except Exception as e:
            print(f"기존 데이터 로드 중 오류 발생: {e}")

    # 영상 파일 목록 (mp4)
    video_files = [f for f in os.listdir(video_dir) if f.lower().endswith('.mp4')]
    new_videos = [f for f in video_files if f not in processed_filenames]
    
    if not new_videos:
        print("새로 처리할 영상이 없습니다.")
        return

    print(f"총 {len(video_files)}개의 영상 중 {len(new_videos)}개의 새로운 영상을 처리합니다.")

    for i, video_file in enumerate(new_videos):
        video_path = os.path.join(video_dir, video_file)
        print(f"[{i+1}/{len(new_videos)}] 처리 중: {video_file}...")
        
        try:
            frames = encode_video(video_path)
            raw_response = img_classification(prompt2, frames)
            
            # JSON 파싱 및 정제
            json_str = raw_response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:-3].strip()
            elif json_str.startswith("```"):
                json_str = json_str[3:-3].strip()
            
            video_info = json.loads(json_str)
            video_info["video_filename"] = video_file
            video_info["event_date"] = get_random_timestamp()
            
            all_data.append(video_info)
            
            # 매 영상 처리 후 즉시 저장
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            print(f" -> 성공: {video_file}")
            
        except Exception as e:
            print(f" -> 실패: {video_file} (오류: {e})")

    print(f"\n모든 작업이 완료되었습니다. 결과 저장: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    process_all_videos()

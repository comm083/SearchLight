import os
import json
from image_captioning import ImageCaptioner

def main():
    # 경로 설정
    image_dir = os.path.join("..", "..", "backend", "static", "images")
    output_path = os.path.join("..", "..", "ai", "data", "auto_generated_descriptions.json")
    
    # 캡셔너 초기화
    captioner = ImageCaptioner()
    
    # 이미지 목록 가져오기
    if not os.path.exists(image_dir):
        print(f"이미지 디렉토리를 찾을 수 없습니다: {os.path.abspath(image_dir)}")
        return
        
    image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    print(f"총 {len(image_files)}개의 이미지를 발견했습니다.")
    
    results = []
    
    for i, filename in enumerate(image_files):
        img_path = os.path.join(image_dir, filename)
        print(f"[{i+1}/{len(image_files)}] 처리 중: {filename}...")
        
        description = captioner.describe_image(img_path)
        
        # 웹 경로 형식으로 저장
        web_path = f"/static/images/{filename}"
        
        results.append({
            "id": i + 1,
            "filename": filename,
            "description": description,
            "image_path": web_path
        })
        
        # 중간 저장 (혹시 모를 오류 대비)
        if (i + 1) % 10 == 0:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f" -> {i+1}개 완료 및 중간 저장됨.")

    # 최종 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"\n모든 작업이 완료되었습니다!")
    print(f"결과 저장 위치: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    main()

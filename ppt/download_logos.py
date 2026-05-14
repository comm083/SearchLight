"""
download_logos.py  -  py -3.10 ppt/download_logos.py
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests, os
from PIL import Image
from io import BytesIO

LOGO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logos")
os.makedirs(LOGO_DIR, exist_ok=True)

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
GH = "https://avatars.githubusercontent.com/u/{}?s=400&v=4"

# 키 -> URL 목록 (순서대로 시도)
SOURCES = {
    # ── VLM ──────────────────────────────────────────────────────────
    "yolo":      [GH.format(26833433)],                            # Ultralytics
    "videomae":  [GH.format(25720743)],                            # HuggingFace
    "clip":      [GH.format(14957082), "https://openai.com/favicon.ico"],  # OpenAI
    "easyocr":   [GH.format(13304978)],                            # JaidedAI
    "gpt4o":     [GH.format(14957082), "https://openai.com/favicon.ico"],  # OpenAI
    # ── NLP ──────────────────────────────────────────────────────────
    "koelectra": [GH.format(25720743)],                            # HuggingFace
    "krsbert":   [GH.format(25720743)],                            # HuggingFace
    "kobart":    [GH.format(25720743)],                            # HuggingFace
    # ── 공통 ─────────────────────────────────────────────────────────
    "fastapi":   ["https://fastapi.tiangolo.com/img/favicon.png"],
    "supabase":  ["https://supabase.com/favicon/favicon-96x96.png"],
    "sqlite":    [GH.format(1062538)],                             # SQLite
    "faiss":     [GH.format(16943930)],                            # facebookresearch
    "react":     ["https://react.dev/apple-touch-icon.png"],
    "tailwind":  ["https://tailwindcss.com/favicons/apple-touch-icon.png"],
    "recharts":  [GH.format(4459235)],                             # recharts org
    "framer":    [GH.format(1764836)],                             # Framer
    "vscode":    ["https://code.visualstudio.com/apple-touch-icon.png",
                  GH.format(6154722)],                             # microsoft
    "github":    ["https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"],
}

def download_one(key, urls):
    out = os.path.join(LOGO_DIR, f"{key}.png")
    for url in urls:
        try:
            r = requests.get(url, headers=H, timeout=12)
            r.raise_for_status()
            img = Image.open(BytesIO(r.content))
            # ICO: 가장 큰 크기 선택
            if hasattr(img, 'size') and getattr(img, 'format', '') == 'ICO':
                sizes = img.info.get('sizes', [img.size])
                best = max(sizes, key=lambda s: s[0] * s[1])
                img.size = best
            img = img.convert("RGBA")
            img.save(out, "PNG")
            print(f"  {key:<12}  OK   {img.size[0]}x{img.size[1]}")
            return True
        except Exception:
            continue
    print(f"  {key:<12}  FAIL -> 배지")
    return False

print("로고 다운로드 중...\n")
ok = sum(download_one(k, v) for k, v in SOURCES.items())
print(f"\n완료: {ok}/{len(SOURCES)}  ->  ppt/logos/")

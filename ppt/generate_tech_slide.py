"""
generate_tech_slide.py
======================
Software & Frameworks 슬라이드 PNG 생성 (기존 PPT 다크 네이비 스타일)

로고 사용 방법:
  ppt/logos/{키이름}.png 파일을 넣고 재실행하면 자동으로 로고 이미지를 사용합니다.
  파일이 없으면 브랜드 컬러 배지로 대체됩니다.

키이름 목록:
  VLM : yolo, videomae, clip, easyocr, gpt4o
  NLP : koelectra, krsbert, kobart, gpt4o
  공통: fastapi, supabase, sqlite, faiss, react, tailwind, recharts, framer, vscode, github

실행:
  py -3.10 ppt/generate_tech_slide.py
"""

from PIL import Image, ImageDraw, ImageFont
import os

W, H    = 1920, 1080
_DIR    = os.path.dirname(os.path.abspath(__file__))
LOGO_DIR = os.path.join(_DIR, "logos")
IMG_DIR  = os.path.join(_DIR, "slides_img")
OUT      = os.path.join(IMG_DIR, "tech_stack.png")
os.makedirs(LOGO_DIR, exist_ok=True)
os.makedirs(IMG_DIR,  exist_ok=True)

# ── 색상 ──────────────────────────────────────────────────────────────
BG       = (1, 18, 31)
HDR_BG   = (3, 25, 45)
CYAN     = (0, 210, 215)
GREEN    = (72, 210, 155)
WHITE    = (255, 255, 255)
LGRAY    = (155, 165, 175)
DIVIDER  = (30, 52, 72)

BORDER_V = (0, 185, 205)
BORDER_N = (55, 195, 140)
BORDER_C = (40, 70, 100)

# 기술별 브랜드 배지 색상
BADGE = {
    "yolo":      (0,  180, 200),
    "videomae":  (255, 149,  0),
    "clip":      (16,  163, 127),
    "easyocr":   (66,  133, 244),
    "gpt4o":     (16,  163, 127),
    "koelectra": (255, 149,  0),
    "krsbert":   (255, 149,  0),
    "kobart":    (255, 149,  0),
    "fastapi":   (0,  150, 136),
    "supabase":  (62,  207, 142),
    "sqlite":    (0,   84, 166),
    "faiss":     (4,  103, 223),
    "react":     (97,  218, 251),
    "tailwind":  (56,  189, 248),
    "recharts":  (136,  84, 208),
    "framer":    (0,   85, 255),
    "vscode":    (0,  122, 204),
    "github":    (165, 165, 165),
}

# ── 슬라이드 데이터 ────────────────────────────────────────────────────
VLM = [
    ("yolo",      "YOLOv8 / YOLO-World",   "Object Detection",               "YOLO"),
    ("videomae",  "VideoMAE (fine-tuned)",  "Video Classification · 7-class · 99.3%", "MAE"),
    ("clip",      "CLIP ViT-B/32",          "Image Embedding",                "CLIP"),
    ("easyocr",   "EasyOCR",                "CCTV Timestamp OCR",             "OCR"),
    ("gpt4o",     "GPT-4o Vision",          "Frame Analysis & Description",   "GPT"),
]

NLP = [
    ("koelectra", "KoELECTRA (fine-tuned)", "Intent Classification · 6-class", "KoE"),
    ("krsbert",   "KR-SBERT",               "Korean Text Embedding",            "SBT"),
    ("kobart",    "KoBART",                 "STT Post-correction",              "KoB"),
    ("gpt4o",     "GPT-4o",                 "Security Report Generation",       "GPT"),
]

COMMON = [
    ("fastapi",  "FastAPI",       "FA"),
    ("supabase", "Supabase",      "SB"),
    ("sqlite",   "SQLite",        "SQL"),
    ("faiss",    "FAISS",         "FS"),
    ("react",    "React",         "⚛"),
    ("tailwind", "Tailwind CSS",  "TW"),
    ("recharts", "Recharts",      "RC"),
    ("framer",   "Framer Motion", "FM"),
    ("vscode",   "VS Code",       "VS"),
    ("github",   "GitHub",        "GH"),
]

COMMON_LABEL = {
    "fastapi": "Backend",  "supabase": "Cloud DB", "sqlite": "Event DB",
    "faiss": "Vector",     "react": "Frontend",    "tailwind": "UI",
    "recharts": "Charts",  "framer": "Motion",     "vscode": "Dev",
    "github": "Git",
}


# ── 폰트 ──────────────────────────────────────────────────────────────
_FONT_CACHE = {}

def F(size, bold=False):
    key = (size, bold)
    if key not in _FONT_CACHE:
        candidates = (
            ["C:/Windows/Fonts/malgunbd.ttf"] if bold else []
        ) + ["C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/segoeui.ttf",
             "C:/Windows/Fonts/arial.ttf"]
        for p in candidates:
            try:
                _FONT_CACHE[key] = ImageFont.truetype(p, size)
                break
            except OSError:
                pass
        else:
            _FONT_CACHE[key] = ImageFont.load_default()
    return _FONT_CACHE[key]


# ── 헬퍼 ──────────────────────────────────────────────────────────────
def badge_or_logo(img, draw, cx, cy, size, key, abbr):
    """cx, cy 중심 기준으로 로고(흰 배경 아이콘) 또는 배지 그리기"""
    x, y = cx - size // 2, cy - size // 2
    path = os.path.join(LOGO_DIR, f"{key}.png")
    if os.path.exists(path):
        try:
            logo = Image.open(path).convert("RGBA")
            pad = max(6, size // 7)
            inner = size - pad * 2
            logo = logo.resize((inner, inner), Image.LANCZOS)
            # 흰 배경 둥근 사각형 컨테이너
            box = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            bd  = ImageDraw.Draw(box)
            bd.rounded_rectangle([0, 0, size-1, size-1], radius=11, fill=(255, 255, 255, 255))
            box.paste(logo, (pad, pad), logo)
            # 알파 마스크로 합성 (둥근 모서리 유지)
            img.paste(box.convert("RGB"), (x, y), box.split()[3])
            return
        except Exception as e:
            print(f"  logo error ({key}): {e}")
    color = BADGE.get(key, (65, 85, 105))
    draw.rounded_rectangle([x, y, x+size, y+size], radius=12, fill=color)
    draw.text((cx, cy), abbr, fill=WHITE, font=F(max(11, size//3), bold=True), anchor="mm")


def card(draw, rx, ry, rw, rh, label, border_col):
    draw.rounded_rectangle([rx, ry, rx+rw, ry+rh], radius=16, fill=(4, 26, 46))
    draw.rounded_rectangle([rx, ry, rx+rw, ry+rh], radius=16, outline=border_col, width=2)
    # 섹션 레이블 배지
    f = F(22, bold=True)
    lw = int(draw.textlength(label, font=f)) + 36
    draw.rounded_rectangle([rx+24, ry-16, rx+24+lw, ry+20], radius=8, fill=border_col)
    draw.text((rx+24 + lw//2, ry+2), label, fill=WHITE, font=f, anchor="mm")


def hline(draw, x1, x2, y):
    draw.line([x1, y, x2, y], fill=DIVIDER, width=1)


# ── 레이아웃 상수 ─────────────────────────────────────────────────────
PAD      = 44          # 좌우 여백
GAP      = 18          # 카드 간격
HDR_H    = 70          # 헤더 높이
CARD_TOP = 195         # 카드 시작 y
CARD_H   = 620         # 카드 높이
CARD_W   = (W - PAD*2 - GAP) // 2
COM_TOP  = CARD_TOP + CARD_H + 28
COM_H    = 190
INNER    = 22          # 카드 내부 좌우 패딩


def draw_items(img, draw, items, cx_offset, cy_start, cy_end, badge_sz=50):
    n = len(items)
    slot = (cy_end - cy_start) // n
    for i, row in enumerate(items):
        key, name, desc, abbr = row
        mid_y = cy_start + i * slot + slot // 2
        badge_or_logo(img, draw, cx_offset + badge_sz // 2 + INNER, mid_y, badge_sz, key, abbr)
        tx = cx_offset + INNER + badge_sz + 18
        draw.text((tx, mid_y - 17), name, fill=WHITE,   font=F(23, bold=True))
        draw.text((tx, mid_y + 10), desc, fill=LGRAY,   font=F(17))
        if i < n - 1:
            hline(draw, cx_offset + INNER, cx_offset + CARD_W - INNER, mid_y + slot//2)


# ── 생성 ──────────────────────────────────────────────────────────────
def generate():
    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # 헤더 바
    draw.rectangle([0, 0, W, HDR_H], fill=HDR_BG)
    draw.rectangle([0, HDR_H, W, HDR_H+4], fill=CYAN)
    draw.text((PAD, HDR_H//2), "AI SECURITY / REPORT",
              fill=CYAN, font=F(19, bold=True), anchor="lm")
    draw.text((W-PAD, HDR_H//2), "YOON-E-VERSE  |  기술 스택",
              fill=WHITE, font=F(19), anchor="rm")

    # 타이틀
    draw.text((PAD+4, 90),  "Software & Frameworks", fill=WHITE, font=F(50, bold=True))
    draw.text((PAD+6, 152), "SearchLight 시스템 구성 기술 스택 (최종)",
              fill=LGRAY, font=F(21))

    # VLM 카드 (좌)
    VX = PAD
    card(draw, VX, CARD_TOP, CARD_W, CARD_H, "  VLM  ", BORDER_V)
    draw_items(img, draw, VLM, VX, CARD_TOP+44, CARD_TOP+CARD_H-12)

    # NLP 카드 (우)
    NX = PAD + CARD_W + GAP
    card(draw, NX, CARD_TOP, CARD_W, CARD_H, "  NLP  ", BORDER_N)
    draw_items(img, draw, NLP, NX, CARD_TOP+44, CARD_TOP+CARD_H-12)

    # 공통 스트립
    draw.rounded_rectangle([PAD, COM_TOP, W-PAD, COM_TOP+COM_H], radius=14, fill=(3, 22, 40))
    draw.rounded_rectangle([PAD, COM_TOP, W-PAD, COM_TOP+COM_H], radius=14,
                           outline=BORDER_C, width=1)
    draw.text((PAD+20, COM_TOP+16), "공통  ·  Infrastructure  /  Frontend  /  Dev Tools",
              fill=LGRAY, font=F(18, bold=True))

    n = len(COMMON)
    slot_w = (W - PAD*2 - 20) // n
    badge_sz = 46
    for i, (key, name, abbr) in enumerate(COMMON):
        bx = PAD + 10 + i * slot_w + slot_w // 2
        by = COM_TOP + 60 + badge_sz // 2
        badge_or_logo(img, draw, bx, by, badge_sz, key, abbr)
        short = name.replace(" CSS", "").replace(" Motion", "")
        draw.text((bx, by + badge_sz//2 + 14), short,
                  fill=WHITE, font=F(14, bold=True), anchor="mm")
        draw.text((bx, by + badge_sz//2 + 32), COMMON_LABEL.get(key, ""),
                  fill=LGRAY, font=F(13), anchor="mm")

    img.save(OUT)
    print(f"생성 완료: {OUT}")
    print()
    print("로고 추가 방법:")
    print(f"  ppt/logos/{{키이름}}.png 파일 넣고 재실행")
    print(f"  키 목록: {', '.join(BADGE.keys())}")


if __name__ == "__main__":
    generate()

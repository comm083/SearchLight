"""
add_slide.py
============
이미지 하나를 PPTX 슬라이드로 추가합니다.

사용법:
  py -3.10 ppt/add_slide.py <pptx파일> <이미지파일>           # 맨 뒤에 추가
  py -3.10 ppt/add_slide.py <pptx파일> <이미지파일> --pos 3   # 3번째 위치에 삽입

예시:
  py -3.10 ppt/add_slide.py presentation.pptx ppt/slides_img/tech_stack.png
  py -3.10 ppt/add_slide.py presentation.pptx screenshot.png --pos 5
"""

import sys, os, shutil, zipfile, tempfile, re
sys.stdout.reconfigure(encoding='utf-8')

from lxml import etree

# ── 인수 파싱 ─────────────────────────────────────────────────────────
args = sys.argv[1:]
if len(args) < 2:
    print(__doc__)
    sys.exit(1)

PPTX_PATH  = args[0]
IMAGE_PATH = args[1]
INSERT_POS = None  # None = 맨 뒤

if '--pos' in args:
    idx = args.index('--pos')
    INSERT_POS = int(args[idx + 1])  # 1-based

if not os.path.exists(PPTX_PATH):
    print(f"오류: PPTX 파일을 찾을 수 없습니다 → {PPTX_PATH}")
    sys.exit(1)
if not os.path.exists(IMAGE_PATH):
    print(f"오류: 이미지 파일을 찾을 수 없습니다 → {IMAGE_PATH}")
    sys.exit(1)

# ── 이미지 확장자 → MIME 타입 ─────────────────────────────────────────
EXT_MIME = {
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif":  "image/gif",
    ".bmp":  "image/bmp",
    ".webp": "image/webp",
}
img_ext  = os.path.splitext(IMAGE_PATH)[1].lower()
img_mime = EXT_MIME.get(img_ext, "image/png")

# ── XML 네임스페이스 ──────────────────────────────────────────────────
PML  = "http://schemas.openxmlformats.org/presentationml/2006/main"
DML  = "http://schemas.openxmlformats.org/drawingml/2006/main"
REL  = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG  = "http://schemas.openxmlformats.org/package/2006/relationships"
CT   = "http://schemas.openxmlformats.org/package/2006/content-types"

SLIDE_CT   = "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"
SLIDE_REL  = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
IMAGE_REL  = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
LAYOUT_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout"

# ── 슬라이드 XML 템플릿 ───────────────────────────────────────────────
def make_slide_xml(cx, cy):
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="{DML}" xmlns:p="{PML}" xmlns:r="{REL}">
  <p:cSld><p:spTree>
    <p:nvGrpSpPr>
      <p:cNvPr id="1" name=""/>
      <p:cNvGrpSpPr/>
      <p:nvPr/>
    </p:nvGrpSpPr>
    <p:grpSpPr>
      <a:xfrm>
        <a:off x="0" y="0"/>
        <a:ext cx="0" cy="0"/>
        <a:chOff x="0" y="0"/>
        <a:chExt cx="0" cy="0"/>
      </a:xfrm>
    </p:grpSpPr>
    <p:pic>
      <p:nvPicPr>
        <p:cNvPr id="2" name="SlideImage"/>
        <p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr>
        <p:nvPr/>
      </p:nvPicPr>
      <p:blipFill>
        <a:blip r:embed="rId1"/>
        <a:stretch><a:fillRect/></a:stretch>
      </p:blipFill>
      <p:spPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="{cx}" cy="{cy}"/>
        </a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
      </p:spPr>
    </p:pic>
  </p:spTree></p:cSld>
</p:sld>'''.encode('utf-8')

def make_slide_rels(img_name):
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PKG}">
  <Relationship Id="rId1" Type="{IMAGE_REL}"  Target="../media/{img_name}"/>
  <Relationship Id="rId2" Type="{LAYOUT_REL}" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>'''.encode('utf-8')


# ── 메인 처리 ─────────────────────────────────────────────────────────
tmp_dir = tempfile.mkdtemp()
tmp_zip = PPTX_PATH + ".work"
shutil.copy(PPTX_PATH, tmp_zip)

try:
    with zipfile.ZipFile(tmp_zip, 'r') as zin:
        names = zin.namelist()

        # 1) 임시 폴더에 전체 압축 해제
        for name in names:
            out_path = os.path.join(tmp_dir, name.replace('/', os.sep))
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with zin.open(name) as f:
                with open(out_path, 'wb') as g:
                    g.write(f.read())

        # 2) 슬라이드 번호 파악
        existing = [n for n in names if re.match(r'ppt/slides/slide\d+\.xml$', n)]
        nums = [int(re.search(r'slide(\d+)\.xml', n).group(1)) for n in existing]
        next_num = max(nums) + 1 if nums else 1
        print(f"  현재 슬라이드 수: {len(nums)}  →  새 슬라이드 번호: {next_num}")

        # 3) 이미지 파일명 중복 방지
        media_names = {n.split('/')[-1] for n in names if n.startswith('ppt/media/')}
        img_basename = f"slide{next_num}_img{img_ext}"
        if img_basename in media_names:
            img_basename = f"added_{next_num}{img_ext}"

        # 4) 슬라이드 크기 읽기 (presentation.xml)
        prs_path = os.path.join(tmp_dir, 'ppt', 'presentation.xml')
        prs_tree = etree.parse(prs_path)
        prs_root = prs_tree.getroot()

        sz_el = prs_root.find(f'.//{{{PML}}}sldSz')
        cx = int(sz_el.get('cx')) if sz_el is not None else 12192000
        cy = int(sz_el.get('cy')) if sz_el is not None else 6858000
        print(f"  슬라이드 크기: {cx} × {cy} EMU")

    # 5) 새 파일 생성
    slide_path     = os.path.join(tmp_dir, 'ppt', 'slides', f'slide{next_num}.xml')
    slide_rels_dir = os.path.join(tmp_dir, 'ppt', 'slides', '_rels')
    slide_rels_path = os.path.join(slide_rels_dir, f'slide{next_num}.xml.rels')
    media_path     = os.path.join(tmp_dir, 'ppt', 'media', img_basename)

    os.makedirs(slide_rels_dir, exist_ok=True)

    with open(slide_path, 'wb') as f:
        f.write(make_slide_xml(cx, cy))
    with open(slide_rels_path, 'wb') as f:
        f.write(make_slide_rels(img_basename))
    shutil.copy(IMAGE_PATH, media_path)

    # 6) presentation.xml.rels 에 새 슬라이드 관계 추가
    prs_rels_path = os.path.join(tmp_dir, 'ppt', '_rels', 'presentation.xml.rels')
    rels_tree = etree.parse(prs_rels_path)
    rels_root = rels_tree.getroot()

    existing_ids = [el.get('Id', '') for el in rels_root]
    rId_nums = [int(re.search(r'rId(\d+)', rid).group(1))
                for rid in existing_ids if re.search(r'rId(\d+)', rid)]
    new_rId = f"rId{max(rId_nums) + 1 if rId_nums else 1}"

    etree.SubElement(rels_root, 'Relationship', {
        'Id': new_rId,
        'Type': SLIDE_REL,
        'Target': f'slides/slide{next_num}.xml',
    })
    rels_tree.write(prs_rels_path, xml_declaration=True, encoding='UTF-8', standalone=True)

    # 7) presentation.xml sldIdLst 에 슬라이드 추가 (위치 조정)
    sldIdLst = prs_root.find(f'.//{{{PML}}}sldIdLst')
    existing_ids_el = list(sldIdLst)
    sld_ids = [int(el.get('id', 256)) for el in existing_ids_el]
    new_sld_id = max(sld_ids) + 1 if sld_ids else 256

    new_sld = etree.Element(f'{{{PML}}}sldId', {
        'id': str(new_sld_id),
        f'{{{REL}}}id': new_rId,
    })

    if INSERT_POS is None:
        sldIdLst.append(new_sld)
        print(f"  슬라이드 삽입 위치: 맨 뒤 ({len(existing_ids_el) + 1}번째)")
    else:
        pos = max(0, min(INSERT_POS - 1, len(existing_ids_el)))
        sldIdLst.insert(pos, new_sld)
        print(f"  슬라이드 삽입 위치: {INSERT_POS}번째")

    prs_tree.write(prs_path, xml_declaration=True, encoding='UTF-8', standalone=True)

    # 8) [Content_Types].xml 에 새 슬라이드 타입 추가
    ct_path = os.path.join(tmp_dir, '[Content_Types].xml')
    ct_tree = etree.parse(ct_path)
    ct_root = ct_tree.getroot()

    etree.SubElement(ct_root, 'Override', {
        'PartName': f'/ppt/slides/slide{next_num}.xml',
        'ContentType': SLIDE_CT,
    })
    ct_tree.write(ct_path, xml_declaration=True, encoding='UTF-8', standalone=True)

    # 9) 새 PPTX 빌드
    with zipfile.ZipFile(PPTX_PATH, 'w', zipfile.ZIP_DEFLATED) as zout:
        for root, dirs, files in os.walk(tmp_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                arc_name = os.path.relpath(abs_path, tmp_dir).replace(os.sep, '/')
                zout.write(abs_path, arc_name)

    print(f"\n완료: {PPTX_PATH}")
    print(f"  추가된 이미지: {img_basename}  ({img_mime})")

finally:
    shutil.rmtree(tmp_dir)
    if os.path.exists(tmp_zip):
        os.remove(tmp_zip)

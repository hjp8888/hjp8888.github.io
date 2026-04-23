import json, os, glob, re, shutil, zipfile, tempfile
from datetime import datetime

# ── 설정 ──────────────────────────────
FILES = {
    'index.html':  'docs',
    'index2.html': 'docs2',
    'index3.html': 'docs3',
    'index4.html': 'docs4',
    'index5.html': 'docs5',
}
BACKUP_DIR  = 'backup'
MAX_BACKUPS = 2  # 파일당 최대 백업 개수
# ──────────────────────────────────────

# docs/docs2~5 폴더명은 태그 제외 대상
ROOT_FOLDERS = {'docs', 'docs2', 'docs3', 'docs4', 'docs5'}


def get_store(html):
    marker = '<script class="tiddlywiki-tiddler-store" type="application/json">['
    si = html.index(marker) + len(marker) - 1
    tiddlers, end = json.JSONDecoder().raw_decode(html[si:])
    return tiddlers, si, si + end


def parse_frontmatter(text):
    """md 파일의 frontmatter(title, tags) 파싱"""
    match = re.match(r'^---\n(.*?)\n---\n?', text, re.DOTALL)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, text[match.end():]


def now_tw():
    return datetime.now().strftime('%Y%m%d%H%M%S') + '000'


def find_tiddler_start(json_str, title):
    for pat in ['"title":"' + title + '"',
                '"title":' + json.dumps(title, ensure_ascii=True)]:
        idx = json_str.find(pat)
        if idx == -1:
            continue
        for i in range(idx, max(0, idx - 5000), -1):
            if json_str[i] == '{' and json_str[i-1] in (',', '[', '\n'):
                try:
                    t, end = json.JSONDecoder().raw_decode(json_str[i:])
                    if t.get('title') == title:
                        return i, i + end
                except:
                    pass
    return -1, -1


def upsert(json_str, title, text, tags, modified, tiddler_type='text/markdown'):
    start, end = find_tiddler_start(json_str, title)
    if start != -1:
        t, _ = json.JSONDecoder().raw_decode(json_str[start:])
        t['text']     = text
        t['tags']     = tags
        t['modified'] = modified
        t['type']     = tiddler_type
        new_str = json.dumps(t, ensure_ascii=False, separators=(',', ':'))
        return json_str[:start] + new_str + json_str[end:], '수정'
    else:
        new_t = {
            "created":  modified,
            "modified": modified,
            "title":    title,
            "tags":     tags,
            "type":     tiddler_type,
            "text":     text
        }
        new_str = ',\n' + json.dumps(new_t, ensure_ascii=False, separators=(',', ':'))
        return json_str[:-1] + new_str + ']', '추가'


def get_html_tags(path, docs_folder, tmp_prefix):
    """
    .html 파일 전용 태그 자동 추출 (폴더 경로 기반)
    .md 파일은 이 함수 사용 안 함 — frontmatter로 직접 지정

    일반 파일:
      docs/여행/부산/해운대.html → "여행 부산"
      docs/파일.html             → ""

    ZIP 압축 해제 파일:
      docs/html/test.zip 안 여행/부산/test.html → "html 여행 부산"
      docs/html/test.zip 안 test.html           → "html"
      docs/test.zip      안 여행/test.html       → "여행"
    """
    for tmp_dir, prefix in tmp_prefix.items():
        if path.startswith(tmp_dir):
            # ZIP 내부 폴더 태그
            rel     = os.path.relpath(path, tmp_dir).replace('\\', '/')
            folders = rel.split('/')[:-1]  # 파일명 제외
            inner   = ' '.join(f for f in folders if f)
            # zip 위치 태그 + 내부 폴더 태그 합산
            parts   = [p for p in [prefix, inner] if p]
            return ' '.join(parts)

    # 일반 파일 — docs 기준 상위 폴더
    rel     = os.path.relpath(path, docs_folder).replace('\\', '/')
    folders = rel.split('/')[:-1]
    folders = [f for f in folders if f and f not in ROOT_FOLDERS]
    return ' '.join(folders)


def extract_zip(zip_path, docs_folder):
    """
    ZIP 파일 압축 해제 후 (임시폴더, zip위치태그) 반환
    한글 파일명 EUC-KR 자동 대응
    """
    tmp_dir = tempfile.mkdtemp()

    # zip 위치 태그: docs 기준 zip 파일의 상위 폴더
    zip_rel = os.path.relpath(os.path.dirname(zip_path), docs_folder)
    zip_rel = zip_rel.replace('\\', '/')
    prefix  = '' if zip_rel == '.' else zip_rel.replace('/', ' ')

    print(f"  📦 ZIP: {os.path.basename(zip_path)}" +
          (f" → 위치 태그: [{prefix}]" if prefix else ""))

    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            for info in z.infolist():
                try:
                    fname = info.filename.encode('cp437').decode('euc-kr')
                except:
                    fname = info.filename
                target = os.path.join(tmp_dir, fname)
                if info.is_dir():
                    os.makedirs(target, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(target), exist_ok=True)
                    with z.open(info) as src, open(target, 'wb') as dst:
                        dst.write(src.read())
    except Exception as e:
        print(f"  ⚠ ZIP 오류: {e}")

    return tmp_dir, prefix


# ── 1. 백업 (파일당 MAX_BACKUPS개 유지) ──
os.makedirs(BACKUP_DIR, exist_ok=True)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

for html_file in FILES:
    if not os.path.exists(html_file):
        continue
    pattern  = os.path.join(BACKUP_DIR, f'*_{html_file}')
    existing = sorted(glob.glob(pattern))
    while len(existing) >= MAX_BACKUPS:
        os.remove(existing.pop(0))
    backup_name = f"{timestamp}_{html_file}"
    shutil.copy(html_file, os.path.join(BACKUP_DIR, backup_name))
    print(f"✓ 백업: {backup_name}")

print()

# ── 2. 메인 루프 ──────────────────────
total_add = total_mod = total_export = 0

for html_file, docs_folder in FILES.items():
    if not os.path.exists(html_file):
        print(f"⚠ {html_file} 없음, 건너뜀\n")
        continue

    os.makedirs(docs_folder, exist_ok=True)

    # ── ZIP 압축 해제 ──
    # { tmp_dir: prefix_tag } — .html 태그 추출 시 사용
    tmp_prefix = {}
    for zip_path in glob.glob(os.path.join(docs_folder, '**/*.zip'), recursive=True):
        tmp_dir, prefix = extract_zip(zip_path, docs_folder)
        tmp_prefix[tmp_dir] = prefix

    tmp_dirs = list(tmp_prefix.keys())

    # ── 파일 수집 ──
    # .md 파일 (일반 + ZIP 안)
    md_files = sorted(glob.glob(os.path.join(docs_folder, '**/*.md'), recursive=True))
    for tmp_dir in tmp_dirs:
        md_files += sorted(glob.glob(os.path.join(tmp_dir, '**/*.md'), recursive=True))

    # .html 파일 (일반 + ZIP 안)
    html_src = sorted(glob.glob(os.path.join(docs_folder, '**/*.html'), recursive=True))
    for tmp_dir in tmp_dirs:
        html_src += sorted(glob.glob(os.path.join(tmp_dir, '**/*.html'), recursive=True))

    # ── html 파일 읽기 ──
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    tiddlers, si, ep = get_store(html)
    result_json = html[si:ep]

    # ── 수집: { title: (body, tags, type) } ──
    all_titles = {}

    # .md → frontmatter에서 title/tags 직접 파싱 (폴더 경로 무관)
    for path in md_files:
        with open(path, 'r', encoding='utf-8') as f:
            raw = f.read()
        meta, body = parse_frontmatter(raw)
        fname = os.path.splitext(os.path.basename(path))[0]
        title = meta.get('title', fname)
        tags  = meta.get('tags', '')  # frontmatter 우선, 없으면 빈값
        all_titles[title] = (body, tags, 'text/markdown')

    # .html → 파일명이 title, 폴더 경로에서 tags 자동 추출
    # 같은 title이면 .html이 .md 무조건 덮어씀
    for path in html_src:
        with open(path, 'r', encoding='utf-8') as f:
            body = f.read()
        title = os.path.splitext(os.path.basename(path))[0]
        tags  = get_html_tags(path, docs_folder, tmp_prefix)
        all_titles[title] = (body, tags, 'text/html')

    # ── html 기존 티들러 수집 (내보내기용) ──
    html_titles = {}
    for t in tiddlers:
        if t.get('type') in ('text/markdown', 'text/html') \
                and not t.get('title', '').startswith('$:/'):
            tags = t.get('tags', '')
            if isinstance(tags, list):
                tags = ' '.join(tags)
            html_titles[t['title']] = {
                'text': t.get('text', ''),
                'tags': tags,
                'type': t.get('type', 'text/markdown')
            }

    print(f"── {html_file} ({docs_folder}) ──")
    print(f"  기존 티들러: {len(html_titles)}개")
    print(f"  .md 파일:   {len([v for v in all_titles.values() if v[2]=='text/markdown'])}개")
    print(f"  .html 파일: {len([v for v in all_titles.values() if v[2]=='text/html'])}개")

    count = {'추가': 0, '수정': 0}

    # docs → html (upsert)
    for title, (body, tags, ttype) in all_titles.items():
        result_json, action = upsert(result_json, title, body, tags, now_tw(), ttype)
        count[action] += 1
        tag_str = f"[{tags}] " if tags else ""
        ext = '.html' if ttype == 'text/html' else '.md'
        print(f"  {action}({ext}): {tag_str}{title}")

    # html → docs (없는 티들러 → .md 파일로 내보내기)
    for title, data in html_titles.items():
        if title not in all_titles:
            safe_name = re.sub(r'[\\/*?:"<>|]', '_', title)
            out_path  = os.path.join(docs_folder, f"{safe_name}.md")
            content   = f"---\ntitle: \"{title}\"\ntags: \"{data['tags']}\"\n---\n{data['text']}"
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(content)
            total_export += 1
            print(f"  내보내기: {title} → {out_path}")

    # 검증 후 저장
    json.loads(result_json)
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html[:si] + result_json + html[ep:])

    # 임시 폴더 정리
    for tmp_dir in tmp_dirs:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"  → 추가 {count['추가']}개 / 수정 {count['수정']}개\n")
    total_add += count['추가']
    total_mod += count['수정']

print(f"✓ 완료! 추가 {total_add} / 수정 {total_mod} / 내보내기 {total_export}")


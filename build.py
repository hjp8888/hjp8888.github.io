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
MAX_BACKUPS = 2
# ──────────────────────────────────────

ROOT_FOLDERS = {'docs', 'docs2', 'docs3', 'docs4', 'docs5'}

def get_store(html):
    marker = '<script class="tiddlywiki-tiddler-store" type="application/json">['
    si = html.index(marker) + len(marker) - 1
    tiddlers, end = json.JSONDecoder().raw_decode(html[si:])
    return tiddlers, si, si + end

def parse_frontmatter(text):
    match = re.match(r'^---\n(.*?)\n---\n?', text, re.DOTALL)
    if not match: return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, text[match.end():]

def now_tw():
    return datetime.now().strftime('%Y%m%d%H%M%S') + '000'

def find_tiddler_start(json_str, title):
    for pat in ['"title":"' + title + '"', '"title": "' + title + '"',
                '"title":' + json.dumps(title, ensure_ascii=True),
                '"title": ' + json.dumps(title, ensure_ascii=True)]:
        idx = json_str.find(pat)
        if idx == -1: continue
        for i in range(idx, max(0, idx - 5000), -1):
            if json_str[i] == '{':
                prev = json_str[i-1] if i > 0 else '['
                if prev in (',', '[', '\n', '\r', '\t', ' '):
                    try:
                        t, end = json.JSONDecoder().raw_decode(json_str[i:])
                        if t.get('title') == title: return i, i + end
                    except: pass
    return -1, -1

def upsert(json_str, title, text, tags, modified, tiddler_type='text/markdown'):
    start, end = find_tiddler_start(json_str, title)
    if start != -1:
        t, _ = json.JSONDecoder().raw_decode(json_str[start:])
        t['text'], t['tags'], t['modified'], t['type'] = text, tags, modified, tiddler_type
        new_str = json.dumps(t, ensure_ascii=False, separators=(',', ':'))
        return json_str[:start] + new_str + json_str[end:], '수정'
    else:
        last_bracket = json_str.rfind(']')
        new_t = {"created": modified, "modified": modified, "title": title,
                 "tags": tags, "type": tiddler_type, "text": text}
        new_str = ',\n' + json.dumps(new_t, ensure_ascii=False, separators=(',', ':'))
        return json_str[:last_bracket] + new_str + ']', '추가'

def get_folder_tags(path, base_folder):
    """파일 경로에서 상위 폴더명들을 추출하여 태그 리스트로 반환
    폴더명에 하이픈(-) 있으면 여러 태그로 분리
    ex) docs/여행-부산/해운대.md → ['여행', '부산']
    ex) docs/여행/부산/해운대.md → ['여행', '부산']
    """
    rel = os.path.relpath(path, base_folder).replace('\\', '/')
    parts = rel.split('/')[:-1]
    tags = []
    for p in parts:
        if p and p not in ROOT_FOLDERS:
            tags.extend(p.split('-'))  # 하이픈으로 분리
    return tags

def extract_zip(zip_path, docs_folder):
    """
    ZIP 압축 해제 → (tmp_dir, prefix_tags) 반환
    prefix_tags: zip 파일 자체의 상위 폴더 태그 (하이픈 분리 포함)
    ex) docs/여행/부산/파일.zip  → prefix_tags: ['여행', '부산']
    ex) docs/여행-부산/파일.zip  → prefix_tags: ['여행', '부산']
    """
    tmp_dir = tempfile.mkdtemp()
    zip_rel = os.path.relpath(os.path.dirname(zip_path), docs_folder).replace('\\', '/')
    # zip 위치 폴더 태그 — /와 - 모두 분리
    prefix_tags = []
    if zip_rel != '.':
        for p in zip_rel.split('/'):
            if p and p not in ROOT_FOLDERS:
                prefix_tags.extend(p.split('-'))
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
    return tmp_dir, prefix_tags


# ── 1. 백업 ──
os.makedirs(BACKUP_DIR, exist_ok=True)
for html_file in FILES:
    if not os.path.exists(html_file): continue
    pattern = os.path.join(BACKUP_DIR, f'*_{html_file}')
    existing = sorted(glob.glob(pattern))
    while len(existing) >= MAX_BACKUPS: os.remove(existing.pop(0))
    shutil.copy(html_file, os.path.join(BACKUP_DIR, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{html_file}"))

# ── 2. 메인 루프 ──────────────────────
total_add = total_mod = total_export = 0

for html_file, docs_folder in FILES.items():
    if not os.path.exists(html_file): continue
    os.makedirs(docs_folder, exist_ok=True)

    # ── ZIP 압축 해제 ──
    # { tmp_dir: prefix_tags } — prefix_tags: zip 위치 폴더 태그
    tmp_info = {}
    for zip_path in glob.glob(os.path.join(docs_folder, '**/*.zip'), recursive=True):
        tmp_dir, prefix_tags = extract_zip(zip_path, docs_folder)
        tmp_info[tmp_dir] = prefix_tags
        print(f"  📦 ZIP: {os.path.basename(zip_path)}" +
              (f" → prefix: {prefix_tags}" if prefix_tags else ""))

    # ── .md 파일 수집 ──
    # docs 직접 파일 + ZIP 안 파일
    md_files = sorted(glob.glob(os.path.join(docs_folder, '**/*.md'), recursive=True))
    for tmp_dir in tmp_info:
        md_files += sorted(glob.glob(os.path.join(tmp_dir, '**/*.md'), recursive=True))

    with open(html_file, 'r', encoding='utf-8') as f: html_content = f.read()
    tiddlers, si, ep = get_store(html_content)
    result_json = html_content[si:ep]

    all_titles = {}

    # [수집] .md 파일
    # 태그: frontmatter 태그 + 폴더 태그 병합
    # ZIP 안 파일이면: zip 위치 태그(prefix) + zip 내부 폴더 태그도 합산
    for path in md_files:
        with open(path, 'r', encoding='utf-8') as f: raw = f.read()
        meta, body = parse_frontmatter(raw)
        title = meta.get('title', os.path.splitext(os.path.basename(path))[0])
        tags_in_file = meta.get('tags', '').split()

        # ZIP 안 파일 여부 확인
        zip_extra = []
        for tmp_dir, prefix_tags in tmp_info.items():
            if path.startswith(tmp_dir):
                # zip 위치 태그 (prefix)
                zip_extra += prefix_tags
                # zip 내부 폴더 태그
                zip_extra += get_folder_tags(path, tmp_dir)
                break
        else:
            # 일반 파일: docs 기준 폴더 태그
            zip_extra = get_folder_tags(path, docs_folder)

        final_tags = " ".join(sorted(set(tags_in_file + zip_extra)))
        all_titles[title] = (body, final_tags, 'text/markdown')

    # 위키 내 기존 데이터 수집 (내보내기용)
    wiki_data = {}
    for t in tiddlers:
        if not t.get('title', '').startswith('$:/'):
            ts = t.get('tags', '')
            wiki_data[t['title']] = {
                'text': t.get('text', ''),
                'tags': ' '.join(ts) if isinstance(ts, list) else str(ts)
            }

    print(f"── {html_file} ──")
    count = {'추가': 0, '수정': 0}

    # [업데이트] 로컬 MD → 위키
    for title, (body, tags, ttype) in all_titles.items():
        result_json, action = upsert(result_json, title, body, tags, now_tw(), ttype)
        count[action] += 1
        print(f"  {action}: [{tags}] {title}")

    # [내보내기] 위키 전용 티들러 → 로컬 MD
    # 태그 전체를 하이픈으로 연결한 폴더명 하나로 저장
    # ex) tags: "여행 부산" → docs/여행-부산/파일.md
    for title, data in wiki_data.items():
        if title not in all_titles:
            tag_list = data['tags'].split()
            # 태그 전체를 하이픈으로 연결 → 폴더명 하나
            subfolder = '-'.join(tag_list) if tag_list else ""
            target_dir = os.path.join(docs_folder, subfolder)
            os.makedirs(target_dir, exist_ok=True)
            # 폴더명으로 태그를 표현하므로 frontmatter tags는 비움
            safe_name = re.sub(r'[\\/*?:"<>|]', '_', title)
            out_path = os.path.join(target_dir, f"{safe_name}.md")
            content = f"---\ntitle: \"{title}\"\ntags: \"\"\n---\n{data['text']}"
            with open(out_path, 'w', encoding='utf-8') as f: f.write(content)
            total_export += 1
            print(f"  내보내기: {title} → {os.path.relpath(out_path, docs_folder)}")

    # 최종 저장 및 검증
    json.loads(result_json)
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content[:si] + result_json + html_content[ep:])

    for tmp_dir in tmp_info:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    total_add += count['추가']; total_mod += count['수정']

print(f"\n✓ 완료! 추가 {total_add} / 수정 {total_mod} / 내보내기 {total_export}")

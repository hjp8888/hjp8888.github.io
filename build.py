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
                '"title": "' + title + '"',
                '"title":' + json.dumps(title, ensure_ascii=True),
                '"title": ' + json.dumps(title, ensure_ascii=True)]:
        idx = json_str.find(pat)
        if idx == -1:
            continue
        for i in range(idx, max(0, idx - 5000), -1):
            if json_str[i] == '{':
                prev = json_str[i-1] if i > 0 else '['
                if prev in (',', '[', '\n', '\r', '\t', ' '):
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
        last_bracket = json_str.rfind(']')
        new_t = {
            "created":  modified,
            "modified": modified,
            "title":    title,
            "tags":     tags,
            "type":     tiddler_type,
            "text":     text
        }
        new_str = ',\n' + json.dumps(new_t, ensure_ascii=False, separators=(',', ':'))
        return json_str[:last_bracket] + new_str + ']', '추가'


def extract_zip(zip_path, docs_folder):
    tmp_dir = tempfile.mkdtemp()
    zip_rel = os.path.relpath(os.path.dirname(zip_path), docs_folder)
    zip_rel = zip_rel.replace('\\', '/')
    prefix  = '' if zip_rel == '.' else zip_rel.replace('/', ' ')
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


# ── 1. 백업 ──
os.makedirs(BACKUP_DIR, exist_ok=True)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
for html_file in FILES:
    if not os.path.exists(html_file): continue
    pattern  = os.path.join(BACKUP_DIR, f'*_{html_file}')
    existing = sorted(glob.glob(pattern))
    while len(existing) >= MAX_BACKUPS: os.remove(existing.pop(0))
    shutil.copy(html_file, os.path.join(BACKUP_DIR, f"{timestamp}_{html_file}"))

# ── 2. 메인 루프 ──────────────────────
total_add = total_mod = total_export = 0

for html_file, docs_folder in FILES.items():
    if not os.path.exists(html_file): continue
    os.makedirs(docs_folder, exist_ok=True)

    # ZIP 처리
    tmp_prefix = {}
    for zip_path in glob.glob(os.path.join(docs_folder, '**/*.zip'), recursive=True):
        tmp_dir, _ = extract_zip(zip_path, docs_folder)
        tmp_prefix[tmp_dir] = ""

    md_files = sorted(glob.glob(os.path.join(docs_folder, '**/*.md'), recursive=True))
    for tmp_dir in tmp_prefix.keys():
        md_files += sorted(glob.glob(os.path.join(tmp_dir, '**/*.md'), recursive=True))

    html_src = sorted(glob.glob(os.path.join(docs_folder, '**/*.html'), recursive=True))

    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    tiddlers, si, ep = get_store(html_content)
    result_json = html_content[si:ep]

    all_titles = {}

    # [수집] .md 파일
    for path in md_files:
        with open(path, 'r', encoding='utf-8') as f:
            raw = f.read()
        meta, body = parse_frontmatter(raw)
        title = meta.get('title', os.path.splitext(os.path.basename(path))[0])
        tags  = meta.get('tags', '')
        all_titles[title] = (body, tags, 'text/markdown')

    # [수집] .html 파일 (iframe 방식 + 태그 체크)
    for path in html_src:
        title    = os.path.splitext(os.path.basename(path))[0]
        rel      = os.path.relpath(path, docs_folder).replace('\\', '/')
        
        # 상위 폴더 구조로 태그 리스트 생성
        tag_list = [f for f in rel.split('/')[:-1] if f and f not in ROOT_FOLDERS]
        
        # ⭐ if 문 사용: 'html' 태그가 리스트에 없으면 추가
        if 'html' not in tag_list:
            tag_list.append('html')
        
        tags = ' '.join(tag_list)
        rel_path = os.path.relpath(path, '.').replace('\\', '/')
        body     = f'<iframe src="./{rel_path}" style="width:100%; height:80vh; border:none;" allowfullscreen></iframe>'
        
        all_titles[title] = (body, tags, 'text/markdown')

    # [내보내기 준비] 기존 위키 티들러
    html_titles = {}
    for t in tiddlers:
        if not t.get('title', '').startswith('$:/'):
            ts = t.get('tags', '')
            ts_str = ' '.join(ts) if isinstance(ts, list) else str(ts)
            html_titles[t['title']] = {'text': t.get('text', ''), 'tags': ts_str}

    print(f"── {html_file} ──")
    count = {'추가': 0, '수정': 0}

    # 위키 업데이트 (Upsert)
    for title, (body, tags, ttype) in all_titles.items():
        result_json, action = upsert(result_json, title, body, tags, now_tw(), ttype)
        count[action] += 1
        print(f"  {action}: [{tags}] {title}")

    # 로컬로 내보내기 (Export)
    for title, data in html_titles.items():
        if title not in all_titles:
            # ⭐ 태그에 'html'이 포함된 경우 내보내지 않음
            if 'html' in data['tags'].split():
                continue
                
            safe_name = re.sub(r'[\\/*?:"<>|]', '_', title)
            out_path  = os.path.join(docs_folder, f"{safe_name}.md")
            content   = f"---\ntitle: \"{title}\"\ntags: \"{data['tags']}\"\n---\n{data['text']}"
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(content)
            total_export += 1
            print(f"  내보내기: {title} → {out_path}")

    # 최종 저장
    json.loads(result_json) # JSON 검증
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content[:si] + result_json + html_content[ep:])

    for tmp_dir in tmp_prefix.keys():
        shutil.rmtree(tmp_dir, ignore_errors=True)

    total_add += count['추가']; total_mod += count['수정']

print(f"\n✓ 완료! 추가 {total_add} / 수정 {total_mod} / 내보내기 {total_export}")

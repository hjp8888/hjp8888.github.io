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

def get_store(html):
    marker = '<script class="tiddlywiki-tiddler-store" type="application/json">['
    si = html.index(marker) + len(marker) - 1
    tiddlers, end = json.JSONDecoder().raw_decode(html[si:])
    return tiddlers, si, si + end

def parse_frontmatter(text):
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
        new_str = json.dumps(t, ensure_ascii=False, separators=(',',':'))
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
        new_str = ',\n' + json.dumps(new_t, ensure_ascii=False, separators=(',',':'))
        return json_str[:-1] + new_str + ']', '추가'

# ── 1. 백업 (파일당 MAX_BACKUPS개 유지) ──
os.makedirs(BACKUP_DIR, exist_ok=True)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

for html_file in FILES:
    if not os.path.exists(html_file):
        continue

    pattern = os.path.join(BACKUP_DIR, f'*_{html_file}')
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

    # ── ZIP 파일 자동 인식 및 압축 해제 ──
    # docs 폴더 안에 .zip 파일이 있으면 임시 폴더에 풀어서 md 파일 수집
    zip_files = glob.glob(os.path.join(docs_folder, '*.zip'))
    tmp_dirs = []  # 나중에 정리할 임시 폴더 목록

    for zip_path in zip_files:
        tmp_dir = tempfile.mkdtemp()
        tmp_dirs.append(tmp_dir)
        print(f"  📦 ZIP 발견: {os.path.basename(zip_path)} → 임시 압축 해제 중...")
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                # 한글 파일명 EUC-KR 대응
                def decode_name(name):
                    try:
                        return name.encode('cp437').decode('euc-kr')
                    except:
                        return name

                for info in z.infolist():
                    fname = decode_name(info.filename)
                    target = os.path.join(tmp_dir, fname)
                    if info.is_dir():
                        os.makedirs(target, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(target), exist_ok=True)
                        with z.open(info) as src, open(target, 'wb') as dst:
                            dst.write(src.read())
        except Exception as e:
            print(f"  ⚠ ZIP 오류: {e}")

    # ── docs 루트 폴더명 목록 (태그 제외 대상) ──
    ROOT_FOLDERS = {'docs', 'docs2', 'docs3', 'docs4', 'docs5'}

    def get_tags_from_path(path, base_folder):
        """
        경로에서 태그 추출
        - base_folder (docs 등) 는 제외
        - 파일명 직전 폴더들만 태그로 사용
        ex) docs/1/2/279.html → 태그: "1 2"
        ex) docs/124.md       → 태그: ""
        """
        rel = os.path.relpath(path, base_folder)      # 1/2/279.html
        parts = rel.replace('\\', '/').split('/')      # ['1', '2', '279.html']
        folders = parts[:-1]                           # ['1', '2']
        # tmp_dir 기반 경로면 base_folder가 tmp_dir인 경우도 있으므로 ROOT_FOLDERS 제외
        folders = [f for f in folders if f not in ROOT_FOLDERS]
        return ' '.join(folders)

    # docs의 모든 .md 파일 수집 (일반 + ZIP 압축 해제)
    md_files = sorted(glob.glob(os.path.join(docs_folder, '**/*.md'), recursive=True))
    for tmp_dir in tmp_dirs:
        md_files += sorted(glob.glob(os.path.join(tmp_dir, '**/*.md'), recursive=True))

    # docs의 모든 .html 파일 수집 (일반 + ZIP 압축 해제)
    html_src_files = sorted(glob.glob(os.path.join(docs_folder, '**/*.html'), recursive=True))
    for tmp_dir in tmp_dirs:
        html_src_files += sorted(glob.glob(os.path.join(tmp_dir, '**/*.html'), recursive=True))

    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()

    tiddlers, si, ep = get_store(html)
    result_json = html[si:ep]

    # ── .md 파일에서 title 목록 수집 ──
    # { title: (path, body, tags, type) }
    all_titles = {}

    for path in md_files:
        with open(path, 'r', encoding='utf-8') as f:
            raw = f.read()
        meta, body = parse_frontmatter(raw)
        fname = os.path.splitext(os.path.basename(path))[0]
        title = meta.get('title', fname)

        # 태그: frontmatter 우선, 없으면 폴더 경로에서 추출
        base = docs_folder if docs_folder in path else next(
            (td for td in tmp_dirs if path.startswith(td)), docs_folder)
        tags = meta.get('tags') or get_tags_from_path(path, base)

        all_titles[title] = (path, body, tags, 'text/markdown')

    # ── .html 파일에서 title 목록 수집 (md보다 나중에 → 같은 title이면 덮어씀) ──
    for path in html_src_files:
        with open(path, 'r', encoding='utf-8') as f:
            body = f.read()
        fname = os.path.splitext(os.path.basename(path))[0]
        title = fname  # html은 파일명이 title

        # 태그: 폴더 경로에서 자동 추출
        base = docs_folder if docs_folder in path else next(
            (td for td in tmp_dirs if path.startswith(td)), docs_folder)
        tags = get_tags_from_path(path, base)

        # 같은 title이 md에 있어도 html이 무조건 덮어씀
        all_titles[title] = (path, body, tags, 'text/html')

    # html 티들러 목록 수집 (마크다운 + html 타입, 태그 포함)
    html_titles = {}
    for t in tiddlers:
        if t.get('type') in ('text/markdown', 'text/html') and not t.get('title','').startswith('$:/'):
            tags = t.get('tags', '')
            if isinstance(tags, list):
                tags = ' '.join(tags)
            html_titles[t['title']] = {
                'text': t.get('text', ''),
                'tags': tags,
                'type': t.get('type', 'text/markdown')
            }

    print(f"── {html_file} ({docs_folder}) ──")
    print(f"  html 티들러: {len(html_titles)}개")
    print(f"  docs .md 파일: {len([v for v in all_titles.values() if v[3]=='text/markdown'])}개")
    print(f"  docs .html 파일: {len([v for v in all_titles.values() if v[3]=='text/html'])}개")

    count = {'추가': 0, '수정': 0}

    # docs → html (upsert) — md/html 통합
    for title, (path, body, tags, ttype) in all_titles.items():
        result_json, action = upsert(result_json, title, body, tags, now_tw(), ttype)
        count[action] += 1
        tag_str = f"[{tags}] " if tags else ""
        ext = '.html' if ttype == 'text/html' else '.md'
        print(f"  {action}({ext}): {tag_str}{title}")

    # html → docs (없는 티들러 md 파일로 내보내기, 태그 포함)
    for title, data in html_titles.items():
        if title not in all_titles:
            safe_name = re.sub(r'[\\/*?:"<>|]', '_', title)
            out_path = os.path.join(docs_folder, f"{safe_name}.md")
            content = f"---\ntitle: \"{title}\"\ntags: \"{data['tags']}\"\n---\n{data['text']}"
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


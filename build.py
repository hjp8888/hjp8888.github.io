import json, os, glob, re, shutil
from datetime import datetime

# ── 설정 ──────────────────────────────
FILES = {
    'index.html':  'docs',
    'index2.html': 'docs2',
    'index3.html': 'docs3',
    'index4.html': 'docs4',
    'index5.html': 'docs5',
}
BACKUP_DIR = 'backup'
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

def upsert(json_str, title, text, tags, modified):
    start, end = find_tiddler_start(json_str, title)
    if start != -1:
        t, _ = json.JSONDecoder().raw_decode(json_str[start:])
        t['text']     = text
        t['tags']     = tags
        t['modified'] = modified
        t['type']     = 'text/markdown'
        new_str = json.dumps(t, ensure_ascii=False, separators=(',',':'))
        return json_str[:start] + new_str + json_str[end:], '수정'
    else:
        new_t = {
            "created":  modified,
            "modified": modified,
            "title":    title,
            "tags":     tags,
            "type":     "text/markdown",
            "text":     text
        }
        new_str = ',\n' + json.dumps(new_t, ensure_ascii=False, separators=(',',':'))
        return json_str[:-1] + new_str + ']', '추가'

# ── 1. 백업 ───────────────────────────
os.makedirs(BACKUP_DIR, exist_ok=True)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

for html_file in FILES:
    if os.path.exists(html_file):
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

    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()

    tiddlers, si, ep = get_store(html)
    result_json = html[si:ep]

    # ── docs의 모든 .md 파일 수집 (하위폴더 포함) ──
    md_files = sorted(glob.glob(os.path.join(docs_folder, '**/*.md'), recursive=True))

    # md 파일에서 title 목록 수집
    md_titles = {}  # title → (path, text, tags)
    for path in md_files:
        with open(path, 'r', encoding='utf-8') as f:
            raw = f.read()
        meta, body = parse_frontmatter(raw)
        fname = os.path.splitext(os.path.basename(path))[0]
        title = meta.get('title', fname)
        tags  = meta.get('tags', '')
        md_titles[title] = (path, body, tags)

    # ── html 티들러 목록 수집 (마크다운 타입만) ──
    html_titles = {}
    for t in tiddlers:
        if t.get('type') == 'text/markdown' and not t.get('title','').startswith('$:/'):
            html_titles[t['title']] = t.get('text', '')

    print(f"── {html_file} ({docs_folder}) ──")
    print(f"  html 마크다운 티들러: {len(html_titles)}개")
    print(f"  docs .md 파일: {len(md_titles)}개")

    count = {'추가': 0, '수정': 0}

    # ── docs → html (upsert) ──
    for title, (path, body, tags) in md_titles.items():
        result_json, action = upsert(result_json, title, body, tags, now_tw())
        count[action] += 1
        tag_str = f"[{tags}] " if tags else ""
        print(f"  {action}: {tag_str}{title}")

    # ── html → docs (없는 티들러 md 파일로 내보내기) ──
    for title, text in html_titles.items():
        if title not in md_titles:
            # docs 루트에 md 파일 생성
            safe_name = re.sub(r'[\\/*?:"<>|]', '_', title)
            out_path = os.path.join(docs_folder, f"{safe_name}.md")
            content = f"---\ntitle: \"{title}\"\ntags: \"\"\n---\n{text}"
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(content)
            total_export += 1
            print(f"  내보내기: {title} → {out_path}")

    # ── 검증 후 저장 ──
    json.loads(result_json)
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html[:si] + result_json + html[ep:])

    print(f"  → 추가 {count['추가']}개 / 수정 {count['수정']}개\n")
    total_add += count['추가']
    total_mod += count['수정']

print(f"✓ 완료! 추가 {total_add} / 수정 {total_mod} / 내보내기 {total_export}")

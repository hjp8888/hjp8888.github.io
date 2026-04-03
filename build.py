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
BACKUP_FOLDER = 'backup'
# ──────────────────────────────────────
# 폴더 구조 예시:
#
# docs/                    → index.html
# ├── 파일.md              → 태그 없음
# └── 일상/
#     └── 파일.md          → 태그: 일상
#
# docs3/                   → index3.html
# ├── 파일.md              → 태그 없음
# └── 독서/
#     └── 파일.md          → 태그: 독서
# ──────────────────────────────────────

def get_store(html):
    marker = '<script class="tiddlywiki-tiddler-store" type="application/json">['
    si = html.index(marker) + len(marker) - 1
    tiddlers, end = json.JSONDecoder().raw_decode(html[si:])
    return tiddlers, si, si + end

def parse_frontmatter(text):
    match = re.match(r'^---\n(.*?)\n---\n', text, re.DOTALL)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip()
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

# ── 백업 폴더 생성 ──
os.makedirs(BACKUP_FOLDER, exist_ok=True)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

total_add = total_mod = 0

for html_file, docs_folder in FILES.items():
    if not os.path.exists(html_file):
        print(f"⚠ {html_file} 없음, 건너뜀")
        continue
    if not os.path.exists(docs_folder):
        print(f"⚠ {docs_folder} 없음, 건너뜀")
        continue

    # 백업
    backup_name = f"{timestamp}_{html_file}"
    shutil.copy(html_file, os.path.join(BACKUP_FOLDER, backup_name))

    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()

    tiddlers, si, ep = get_store(html)
    result_json = html[si:ep]

    md_files = sorted(glob.glob(os.path.join(docs_folder, '**/*.md'), recursive=True))
    if not md_files:
        print(f"⚠ {docs_folder} 에 .md 파일 없음")
        continue

    count = {'추가': 0, '수정': 0}
    print(f"\n── {html_file} ({docs_folder}) ──")

    for path in md_files:
        parts = os.path.normpath(path).split(os.sep)
        # docs/파일.md           → 태그 없음
        # docs/태그폴더/파일.md  → 태그: 폴더명
        if len(parts) == 2:
            tag = ''          # 루트 직접 파일 → 태그 없음
        else:
            tag = parts[1]    # 하위 폴더명 → 태그

        with open(path, 'r', encoding='utf-8') as f:
            raw = f.read()

        meta, text = parse_frontmatter(raw)
        title    = meta.get('title', os.path.splitext(parts[-1])[0])
        tags     = meta.get('tags', tag)
        modified = now_tw()

        result_json, action = upsert(result_json, title, text, tags, modified)
        count[action] += 1
        tag_str = f"[{tags}] " if tags else ""
        print(f"  {action}: {tag_str}{title}")

    json.loads(result_json)
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html[:si] + result_json + html[ep:])

    print(f"  → 추가 {count['추가']}개 / 수정 {count['수정']}개")
    total_add += count['추가']
    total_mod += count['수정']

print(f"\n✓ 전체 완료! 추가 {total_add}개 / 수정 {total_mod}개")
print(f"✓ 백업 위치: {BACKUP_FOLDER}/")

import json, os, glob, re, shutil, csv
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

# --- 인코딩 문제를 해결한 CSV 읽기 함수 ---
def csv_to_json_text(path):
    # utf-8-sig (엑셀 BOM 대응) -> utf-8 -> cp949 순서로 시도
    encodings = ['utf-8-sig', 'utf-8', 'cp949']
    for enc in encodings:
        try:
            with open(path, 'r', encoding=enc) as f:
                reader = csv.DictReader(f)
                data = [row for row in reader]
                return json.dumps(data, ensure_ascii=False, indent=2)
        except (UnicodeDecodeError, Exception):
            continue
    return "[]" # 실패 시 빈 리스트 반환

def json_to_csv_file(json_str, path):
    try:
        data = json.loads(json_str)
        if data and isinstance(data, list) and len(data) > 0:
            with open(path, 'w', encoding='utf-8-sig', newline='') as f: # 엑셀 호환을 위해 utf-8-sig 사용
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
    except Exception as e:
        print(f"  CSV Export Error ({path}): {e}")

def upsert(json_list, title, text, tags, time_str):
    found = False
    action = '추가'
    for t in json_list:
        if t.get('title') == title:
            if t.get('text') != text or t.get('tags') != tags:
                t['text'] = text
                t['tags'] = tags
                t['modified'] = time_str
                action = '수정'
            else:
                action = '유지'
            found = True
            break
    if not found:
        new_t = {
            'title': title,
            'text': text,
            'tags': tags,
            'created': time_str,
            'modified': time_str
        }
        if "CSVData" in tags:
            new_t['type'] = "application/json"
        json_list.append(new_t)
    return json_list, action

if __name__ == "__main__":
    if not os.path.exists(BACKUP_DIR): os.makedirs(BACKUP_DIR)

    for html_file, docs_folder in FILES.items():
        if not os.path.exists(html_file): continue
        if not os.path.exists(docs_folder): os.makedirs(docs_folder)

        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        tiddlers, start, end = get_store(html_content)
        
        md_titles = {}
        # 1. 마크다운 스캔
        for fpath in glob.glob(os.path.join(docs_folder, '*.md')):
            with open(fpath, 'r', encoding='utf-8') as f:
                meta, body = parse_frontmatter(f.read())
                title = meta.get('title', os.path.basename(fpath).replace('.md', ''))
                tags = meta.get('tags', '')
                md_titles[title] = (fpath, body, tags)
        
        # 2. CSV 스캔 (에러 방지 로직 포함)
        for fpath in glob.glob(os.path.join(docs_folder, '*.csv')):
            title = os.path.basename(fpath).replace('.csv', '')
            body = csv_to_json_text(fpath)
            md_titles[title] = (fpath, body, "CSVData")

        html_titles = {}
        for t in tiddlers:
            tags = t.get('tags', '')
            if isinstance(tags, list): tags = ' '.join(tags)
            html_titles[t['title']] = {'text': t.get('text', ''), 'tags': tags}

        print(f"── {html_file} ──")
        result_json = tiddlers
        
        # docs -> html
        for title, (path, body, tags) in md_titles.items():
            result_json, action = upsert(result_json, title, body, tags, now_tw())

        # html -> docs
        for title, data in html_titles.items():
            if title not in md_titles:
                safe_name = re.sub(r'[\\/*?:"<>|]', '_', title)
                if "CSVData" in (data['tags'] or ""):
                    out_path = os.path.join(docs_folder, f"{safe_name}.csv")
                    json_to_csv_file(data['text'], out_path)
                else:
                    out_path = os.path.join(docs_folder, f"{safe_name}.md")
                    content = f"---\ntitle: \"{title}\"\ntags: \"{data['tags']}\"\n---\n{data['text']}"
                    with open(out_path, 'w', encoding='utf-8') as f:
                        f.write(content)

        new_store_json = json.dumps(result_json, separators=(',', ':'), ensure_ascii=False)
        new_html = html_content[:start] + new_store_json + html_content[end:]
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(new_html)
        print(f"  동기화 완료")

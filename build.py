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

# --- CSV 변환 함수 추가 ---
def csv_to_json_text(path):
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return json.dumps([row for row in reader], ensure_ascii=False, indent=2)

def json_to_csv_file(json_str, path):
    try:
        data = json.loads(json_str)
        if data and isinstance(data, list) and len(data) > 0:
            with open(path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
    except Exception as e:
        print(f"  CSV 변환 에러 ({path}): {e}")

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
        # CSV 데이터인 경우 티들리위키가 JSON으로 인식하도록 타입 설정
        if "CSVData" in tags:
            new_t['type'] = "application/json"
        json_list.append(new_t)
    return json_list, action

# ── 메인 실행 ──────────────────────────────
if __name__ == "__main__":
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    for html_file, docs_folder in FILES.items():
        if not os.path.exists(html_file): continue
        if not os.path.exists(docs_folder): os.makedirs(docs_folder)

        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        tiddlers, start, end = get_store(html_content)
        
        # 1. 로컬 파일 스캔 (MD + CSV)
        md_titles = {}
        # 마크다운 스캔
        for fpath in glob.glob(os.path.join(docs_folder, '*.md')):
            with open(fpath, 'r', encoding='utf-8') as f:
                meta, body = parse_frontmatter(f.read())
                title = meta.get('title', os.path.basename(fpath).replace('.md', ''))
                tags = meta.get('tags', '')
                md_titles[title] = (fpath, body, tags)
        
        # CSV 스캔 추가
        for fpath in glob.glob(os.path.join(docs_folder, '*.csv')):
            title = os.path.basename(fpath).replace('.csv', '')
            body = csv_to_json_text(fpath)
            md_titles[title] = (fpath, body, "CSVData")

        # 2. HTML 내 티들러 스캔
        html_titles = {}
        for t in tiddlers:
            tags = t.get('tags', '')
            if isinstance(tags, list): tags = ' '.join(tags)
            html_titles[t['title']] = {'text': t.get('text', ''), 'tags': tags}

        print(f"── {html_file} ({docs_folder}) ──")
        result_json = tiddlers
        count = {'추가': 0, '수정': 0, '유지': 0}

        # docs → html (Upsert)
        for title, (path, body, tags) in md_titles.items():
            result_json, action = upsert(result_json, title, body, tags, now_tw())
            if action != '유지': count[action] += 1

        # html → docs (Export)
        for title, data in html_titles.items():
            if title not in md_titles:
                safe_name = re.sub(r'[\\/*?:"<>|]', '_', title)
                # CSVData 태그가 있으면 .csv로 내보내기
                if "CSVData" in data['tags']:
                    out_path = os.path.join(docs_folder, f"{safe_name}.csv")
                    json_to_csv_file(data['text'], out_path)
                    print(f"  Export CSV: {title}")
                else:
                    out_path = os.path.join(docs_folder, f"{safe_name}.md")
                    content = f"---\ntitle: \"{title}\"\ntags: \"{data['tags']}\"\n---\n{data['text']}"
                    with open(out_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  Export MD: {title}")

        # 파일 저장 및 백업
        new_store_json = json.dumps(result_json, indent=None, separators=(',', ':'), ensure_ascii=False)
        new_html = html_content[:start] + new_store_json + html_content[end:]
        
        # 백업 로직 (기존 유지)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        bak_name = f"{os.path.splitext(html_file)[0]}_{timestamp}.html"
        shutil.copy(html_file, os.path.join(BACKUP_DIR, bak_name))
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(new_html)
        
        print(f"  완료 (추가:{count['추가']}, 수정:{count['수정']})")

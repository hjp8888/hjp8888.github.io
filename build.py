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

def read_csv_safe(path):
    """인코딩 에러를 방지하며 CSV 파일 내용을 그대로 읽음"""
    for enc in ['utf-8-sig', 'utf-8', 'cp949']:
        try:
            with open(path, 'r', encoding=enc) as f:
                return f.read()
        except:
            continue
    return ""

def upsert(json_list, title, text, tags, time_str, tiddler_type=None):
    found = False
    for t in json_list:
        if t.get('title') == title:
            t['text'] = text
            t['tags'] = tags
            t['modified'] = time_str
            if tiddler_type:
                t['type'] = tiddler_type
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
        if tiddler_type:
            new_t['type'] = tiddler_type
        json_list.append(new_t)
    return json_list

if __name__ == "__main__":
    for html_file, docs_folder in FILES.items():
        if not os.path.exists(html_file): continue
        if not os.path.exists(docs_folder): os.makedirs(docs_folder)

        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        tiddlers, start, end = get_store(html_content)
        
        # 로컬 파일 스캔
        md_titles = {}
        # 1. MD 파일
        for fpath in glob.glob(os.path.join(docs_folder, '*.md')):
            with open(fpath, 'r', encoding='utf-8') as f:
                meta, body = parse_frontmatter(f.read())
                title = meta.get('title', os.path.basename(fpath).replace('.md', ''))
                tags = meta.get('tags', '')
                md_titles[title] = (body, tags, None)
        
        # 2. CSV 파일 (요청하신 대로 파일명=제목, 타입=text/csv 설정)
        for fpath in glob.glob(os.path.join(docs_folder, '*.csv')):
            title = os.path.basename(fpath).replace('.csv', '')
            body = read_csv_safe(fpath)
            # 'CSVData' 태그를 자동으로 부여하여 관리 용이하게 설정
            md_titles[title] = (body, "CSVData", "text/csv")

        print(f"── {html_file} 업데이트 중... ──")
        result_json = tiddlers
        for title, (body, tags, t_type) in md_titles.items():
            result_json = upsert(result_json, title, body, tags, now_tw(), t_type)

        # 저장
        new_store_json = json.dumps(result_json, separators=(',', ':'), ensure_ascii=False)
        new_html = html_content[:start] + new_store_json + html_content[end:]
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(new_html)

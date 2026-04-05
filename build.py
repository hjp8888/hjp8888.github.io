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
# ──────────────────────────────────────

def get_store(html):
    marker = '<script class="tiddlywiki-tiddler-store" type="application/json">['
    try:
        si = html.index(marker) + len(marker) - 1
        tiddlers, end = json.JSONDecoder().raw_decode(html[si:])
        return tiddlers, si, si + end
    except:
        return [], -1, -1

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

def read_file_safe(path):
    """CSV/MD 읽기 시 인코딩 에러 방지"""
    for enc in ['utf-8-sig', 'utf-8', 'cp949']:
        try:
            with open(path, 'r', encoding=enc) as f:
                return f.read()
        except:
            continue
    return ""

def upsert(json_list, title, text, tags, time_str, t_type=None):
    found = False
    for t in json_list:
        if t.get('title') == title:
            t['text'] = text
            t['tags'] = tags
            t['modified'] = time_str
            if t_type: t['type'] = t_type
            else: t.pop('type', None) # 일반 MD는 type 제거
            found = True
            break
    if not found:
        new_t = {'title': title, 'text': text, 'tags': tags, 'created': time_str, 'modified': time_str}
        if t_type: new_t['type'] = t_type
        json_list.append(new_t)
    return json_list

if __name__ == "__main__":
    for html_file, docs_folder in FILES.items():
        if not os.path.exists(html_file): continue
        if not os.path.exists(docs_folder): os.makedirs(docs_folder)

        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        tiddlers, start, end = get_store(html_content)
        if start == -1: continue
        
        # 1. 로컬(docs) 파일 스캔 (우선순위: docs에 있으면 위키를 덮어씀)
        local_titles = {}
        
        # 마크다운(.md) 스캔
        for fpath in glob.glob(os.path.join(docs_folder, '*.md')):
            content = read_file_safe(fpath)
            meta, body = parse_frontmatter(content)
            title = meta.get('title', os.path.basename(fpath).replace('.md', ''))
            local_titles[title] = (body, meta.get('tags', ''), None)
        
        # CSV(.csv) 스캔
        for fpath in glob.glob(os.path.join(docs_folder, '*.csv')):
            title = os.path.basename(fpath).replace('.csv', '')
            body = read_file_safe(fpath)
            # 파일명이 제목, 태그는 CSVData, 타입은 text/csv로 고정
            local_titles[title] = (body, "CSVData", "text/csv")

        # 2. 기존 HTML 내 티들러 스캔 (내보내기 용)
        html_titles = {}
        for t in tiddlers:
            tags = t.get('tags', '')
            if isinstance(tags, list): tags = ' '.join(tags)
            html_titles[t['title']] = {
                'text': t.get('text', ''), 
                'tags': tags, 
                'type': t.get('type', '')
            }

        print(f"── {html_file} 동기화 진행 중 ──")
        result_json = tiddlers

        # [방향 1] docs 폴더 기준 -> HTML 업데이트 (덮어씌우기)
        for title, (body, tags, t_type) in local_titles.items():
            result_json = upsert(result_json, title, body, tags, now_tw(), t_type)

        # [방향 2] HTML 기준 -> docs에 없는 파일 생성 (내보내기)
        for title, data in html_titles.items():
            if title not in local_titles:
                # 파일명으로 쓸 수 없는 문자 치환
                safe_name = re.sub(r'[\\/*?:"<>|]', '_', title)
                
                # 타입이 text/csv이거나 태그에 CSVData가 있으면 .csv로 생성
                if data['type'] == "text/csv" or "CSVData" in (data['tags'] or ""):
                    out_path = os.path.join(docs_folder, f"{safe_name}.csv")
                    with open(out_path, 'w', encoding='utf-8-sig') as f:

# 티들리위키 빌드 시스템 — 로컬 / 서버 운영 가이드

GitHub Pages 없이 로컬 또는 서버에서 운영할 때 필요한 정보예요.

---

## 📋 필요한 것

- Python 3.x
- 웹브라우저
- 서버 운영 시: nginx 또는 Apache

---

## 🖥️ 로컬 운영

### 폴더 구조
```
프로젝트/
├── index.html ~ index5.html
├── can.html, can5.html     ← 깡통 html (초기화용 예비)
├── build.py
├── backup/
├── docs/ ~ docs5/
└── img/
```

### 사용법

1. `docs/` 폴더에 `.md` 파일 작성
2. 빌드 실행
```bash
python build.py
```
3. 브라우저에서 열기
```bash
# Windows
start index.html

# Mac
open index.html

# Linux
xdg-open index.html
```

### 자동 빌드 (파일 변경 감지)

`watchdog` 으로 md 저장 시 자동 빌드 가능해요.

```bash
pip install watchdog
```

```python
# watch.py
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess

class Handler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.md'):
            print(f"변경 감지: {event.src_path}")
            subprocess.run(['python', 'build.py'])

if __name__ == '__main__':
    observer = Observer()
    for folder in ['docs', 'docs2', 'docs3', 'docs4', 'docs5']:
        observer.schedule(Handler(), folder, recursive=True)
    observer.start()
    print("감시 중... (Ctrl+C 종료)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
```

```bash
python watch.py
```

---

## 🤖 안드로이드 (Termux)

안드로이드에서도 build.py를 직접 실행할 수 있어요.

### 설치

Play Store 말고 **F-Droid**에서 Termux를 설치해야 해요.

```bash
pkg install python git
```

### 사용법

```bash
# 레포 클론
git clone https://github.com/hjp8888/hjp8888.github.io.git wiki
cd wiki

# md 파일 작성 후 빌드
python build.py

# 커밋 & 푸시
git add .
git commit -m "글 추가"
git push
```

> GitHub Actions가 자동으로 빌드하므로 안드로이드에서는 git push만 해도 돼요.
> build.py 직접 실행은 푸시 없이 로컬에서 확인할 때만 필요해요.

---

## 🐧 리눅스 서버 운영 (nginx)

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install nginx python3

# CentOS/RHEL
sudo yum install nginx python3
```

```bash
sudo cp -r 프로젝트/ /var/www/html/wiki/
sudo chown -R www-data:www-data /var/www/html/wiki/
```

```nginx
# /etc/nginx/sites-available/wiki
server {
    listen 80;
    server_name 도메인 또는 IP;
    root /var/www/html/wiki;
    index index.html;
    location / {
        try_files $uri $uri/ =404;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/wiki /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx
```

### 자동 빌드 (cron)

```bash
crontab -e
```

```
# 5분마다 빌드
*/5 * * * * cd /var/www/html/wiki && python3 build.py >> /var/log/wiki-build.log 2>&1
```

또는 watchdog 백그라운드 실행:
```bash
nohup python3 watch.py &
```

---

## 🐧 리눅스 서버 운영 (Apache)

```bash
sudo apt install apache2 python3
```

```apache
# /etc/apache2/sites-available/wiki.conf
<VirtualHost *:80>
    ServerName 도메인 또는 IP
    DocumentRoot /var/www/html/wiki
    <Directory /var/www/html/wiki>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
```

```bash
sudo a2ensite wiki.conf && sudo systemctl restart apache2
```

---

## 🪟 Windows 로컬 운영

### Python 설치
```
python.org → Downloads → Python 3.x → 설치
설치 시 "Add Python to PATH" 반드시 체크
```

### 실행
```bash
# 명령 프롬프트 or PowerShell
cd C:\Users\이름\프로젝트폴더
python build.py
start index.html
```

### 자동 빌드
```bash
pip install watchdog
python watch.py
```

---

## 🍎 Mac 로컬 운영

### Python 설치
```bash
brew install python3
# 또는 python.org에서 직접 설치
```

### 실행
```bash
cd ~/프로젝트폴더
python3 build.py
open index.html
```

---

## 🔄 GitHub → 로컬/서버 마이그레이션

```bash
# 1. 레포 클론
git clone https://github.com/hjp8888/hjp8888.github.io.git wiki
cd wiki

# 2. GitHub Actions 제거 (로컬 운영 시 불필요)
rm -rf .github/

# 3. 빌드 실행
python3 build.py

# 4. 브라우저로 열기 or 웹서버로 서빙
```

---

## 🌐 다른 웹호스팅으로 운영

### Netlify
1. GitHub 레포 연결
2. Build command: `python build.py`
3. Publish directory: `.`
4. 단, Netlify는 Python 빌드 후 배포 방식이라 GitHub Actions 불필요

### Cloudflare Pages
1. GitHub 레포 연결
2. Framework preset: None
3. Build command: `python build.py`
4. Build output directory: `/`

### 자체 서버 (VPS)
- nginx 또는 Apache로 정적 파일 서빙
- cron 또는 watchdog으로 자동 빌드
- HTTPS: Let's Encrypt + certbot 권장

---

## 📁 build.py 주요 설정

```python
FILES = {
    'index.html':  'docs',
    'index2.html': 'docs2',
    'index3.html': 'docs3',
    'index4.html': 'docs4',
    'index5.html': 'docs5',
}
BACKUP_DIR  = 'backup'
MAX_BACKUPS = 2   # 파일당 최대 백업 개수
```

---

## ⚠️ 주의사항

- 한글 파일명: Windows/Linux/Mac 모두 UTF-8 인코딩 환경 필요
- 방화벽: 서버 운영 시 80(http), 443(https) 포트 개방 필요
- HTTPS: 외부 접속 시 Let's Encrypt(`certbot`) 권장
- `$:/config/AutoSave = no` 설정으로 localStorage 자동저장 비활성화
  - 로컬에서 직접 수정 시 `Ctrl+S` 수동 저장 필요

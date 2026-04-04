# 티들리위키 빌드 시스템 — 로컬 / 리눅스 서버 운영 가이드

GitHub 없이 로컬 또는 리눅스 서버에서 운영할 때 필요한 정보예요.

---

## 📋 필요한 것

- Python 3.x
- 웹브라우저 (로컬 파일 열기)
- 리눅스 서버의 경우 웹서버 (nginx 또는 apache)

---

## 🖥️ 로컬 운영

### 폴더 구조
```
프로젝트/
├── index.html ~ index5.html
├── build.py
├── backup/
├── docs/ ~ docs5/
└── img/
```

### 사용법

1. md 파일 작성
```
docs/ 폴더에 .md 파일 작성
```

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

`watchdog` 라이브러리로 파일 변경 시 자동 빌드 가능해요.

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
    print("파일 감시 중... (Ctrl+C 로 종료)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
```

실행:
```bash
python watch.py
```

이렇게 하면 md 파일 저장할 때마다 자동으로 build.py 실행돼요.

---

## 🐧 리눅스 서버 운영 (nginx)

### nginx 설치 및 설정

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx python3

# CentOS/RHEL
sudo yum install nginx python3
```

### 프로젝트 배포
```bash
# 프로젝트 폴더를 웹서버 루트에 복사
sudo cp -r 프로젝트/ /var/www/html/wiki/

# 권한 설정
sudo chown -R www-data:www-data /var/www/html/wiki/
```

### nginx 설정
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
# 설정 활성화
sudo ln -s /etc/nginx/sites-available/wiki /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 자동 빌드 (cron)

md 파일 수정 후 자동으로 빌드되게 cron 설정이에요.

```bash
crontab -e
```

```
# 5분마다 빌드 실행
*/5 * * * * cd /var/www/html/wiki && python3 build.py >> /var/log/wiki-build.log 2>&1
```

또는 watchdog으로 실시간 감지:
```bash
# 백그라운드 실행
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
sudo a2ensite wiki.conf
sudo systemctl restart apache2
```

---

## 🔄 GitHub → 로컬/서버 마이그레이션

### 1. 레포 클론
```bash
git clone https://github.com/hjp8888/hjp8888.github.io.git wiki
cd wiki
```

### 2. GitHub Actions 불필요 → 제거
```bash
rm -rf .github/
```

### 3. 로컬에서 build.py 실행
```bash
python3 build.py
```

### 4. 웹서버로 서빙
위의 nginx 또는 Apache 설정 참고

---

## 📁 build.py 설정 변경

로컬/서버에서는 백업 폴더 경로 변경 가능해요.

```python
# build.py 상단 설정 부분
FILES = {
    'index.html':  'docs',
    'index2.html': 'docs2',
    'index3.html': 'docs3',
    'index4.html': 'docs4',
    'index5.html': 'docs5',
}
BACKUP_DIR = 'backup'  # 백업 폴더 경로 변경 가능
```

---

## ⚠️ 주의사항

- 리눅스 서버에서 한글 파일명 사용 시 UTF-8 인코딩 설정 확인
- 방화벽에서 80(http) 또는 443(https) 포트 개방 필요
- HTTPS 적용 시 Let's Encrypt 추천 (`certbot` 사용)
- 외부 접속 허용 시 보안 설정 필수

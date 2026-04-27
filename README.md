# 💡 I/O Switcher Local Server

회사가 사라져 공식 앱을 사용할 수 없는 **아이오 스위처(I/O Switcher)**를 위한 독립형 로컬 제어 서버입니다.
공식 서버 없이도 맥북 또는 윈도우 PC를 통해 1구 및 2구 스위처를 완벽하게 제어하고 예약할 수 있습니다.

> **⚠️ iOS 사용자 안내**
> iOS의 블루투스 정책 제한으로 아이폰 브라우저에서는 BLE 기기 직접 제어가 불가능합니다.
> 반드시 **컴퓨터(맥/윈도우)를 서버로 함께 사용**해야 합니다. 컴퓨터가 절전 모드여도 서버는 정상 작동합니다.

---

## ✨ 주요 기능

- **1구 & 2구 지원** — 2구 스위처의 스위치 1, 2를 각각 독립적으로 제어
- **요일별 예약 & 타이머** —
- **배터리 잔량 확인** —
- **간편한 장치 등록** — 웹 UI에서 블루투스 스캔으로 장치 등록

---

## 📁 프로젝트 구조

```
io-switcher-local/
├── .gitignore
├── README.md
└── switcher/
    ├── __init__.py
    ├── main.py
    ├── ble.py
    ├── routes.py
    ├── scheduler.py
    ├── storage.py
    └── static/
        └── ui.html
```

---

## 🚀 시작하기

### 🍎 macOS

터미널을 열고 아래 명령어를 순서대로 입력하세요.

```bash
# 1. Homebrew 설치 (이미 있다면 스킵)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Python 3.11 설치
brew install python@3.11

# 3. 필요 라이브러리 설치
python3.11 -m pip install fastapi uvicorn bleak zeroconf
```

### 🪟 Windows

[Python 공식 홈페이지](https://www.python.org/downloads/)에서 Python 3.11 이상을 설치합니다.
설치 시 **"Add Python to PATH"** 를 반드시 체크하세요.

이후 명령 프롬프트(CMD) 또는 PowerShell에서:

```bash
pip install fastapi uvicorn bleak zeroconf
```

---

## ▶️ 서버 실행

터미널이나 CMD에서 프로젝트 폴더(`io-switcher-local`)로 이동한 뒤 실행하세요.

```bash
python -m switcher.main
```

> macOS에서 버전 충돌이 생기면 `python3.11`을 사용

실행 후 터미널에 아래와 같이 뜨면 성공입니다.

```
✅ 서버 시작!
📱 접속 주소: http://switcher.local:5001
   (IP 직접:  http://192.168.x.x:5001)
```

---

## 📱 사용 방법

1. 서버 실행 후 터미널에 표시된 IP 주소를 **폰 브라우저 주소창에 직접 입력**합니다.
   (`http://` 포함 필수. `https`로 자동 변환되면 접속이 안 됩니다.)
2. 하단 **장치 설정** 메뉴에서 `주변 장치 스캔`을 눌러 스위처를 찾아 저장합니다.
3. 메인 화면에서 ON/OFF, 예약, 타이머를 자유롭게 사용하면 됩니다.

---

## ⚙️ 자동 시작 설정 (부팅 시 자동 실행)

### 🍎 macOS — LaunchAgent

`~/Library/LaunchAgents/com.switcher.server.plist` 파일을 생성합니다.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.switcher.server</string>
  <key>ProgramArguments</key>
  <array>
    <string>/opt/homebrew/bin/python3.11</string>
    <string>-m</string>
    <string>switcher.main</string>
  </array>
  <key>WorkingDirectory</key>
  <string>/Users/YOUR_USERNAME/Desktop/io-switcher-local</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
</dict>
</plist>
```

`YOUR_USERNAME` 부분을 본인 맥 사용자 이름으로 바꾼 뒤 터미널에서 등록합니다.

```bash
launchctl load ~/Library/LaunchAgents/com.switcher.server.plist
```

### 🪟 Windows — 시작프로그램 등록

`Win + R` 키를 누르고 `shell:startup` 입력 → 시작프로그램 폴더가 열립니다.
해당 폴더에 `main.py`의 바로가기를 만들면 부팅 시 자동 실행됩니다.

---

## ⚠️ 주의사항

- **같은 Wi-Fi 필수** — 서버(컴퓨터)와 클라이언트(폰)가 반드시 같은 네트워크에 있어야 합니다.
- **IP 고정 권장** — 공유기 재부팅 시 IP가 바뀌면 폰 즐겨찾기가 안 먹힐 수 있습니다. 맥 시스템 설정에서 수동 IP를 설정해두면 편합니다.
- **방화벽** — 접속이 안 될 경우 시스템 설정에서 Python의 네트워크 접근을 허용하세요.

---

버그 제보나 기능 제안은 **Issues** 탭을 이용해 주세요.

# 채널톡 에스컬레이션 슬랙봇

채널톡 고객 메시지를 실시간으로 분석하여 에스컬레이션이 필요한 내용을 슬랙봇으로 즉시 알립니다.

## 에스컬레이션 레벨

| 레벨 | 트리거 | 알림 대상 |
|------|--------|-----------|
| 🚨 CRITICAL | 소송, 고소, 법무, 내용증명, 변호사, 형사, 경찰 등 | 법무팀 / 경영진 |
| ⚠️ HIGH | 사기, 협박, 언론 제보, SNS 공개 위협, 환불 거부 등 | 팀장 |
| 📢 MEDIUM | 반복 불만, 감정 격화, 응답 없음, 대기 불만 등 | 시니어 상담원 |

## 로컬 실행

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경변수 설정
cp .env.example .env
# .env 파일에 SLACK_BOT_TOKEN, SLACK_CHANNEL_ID 입력

# 3. 서버 실행
python app.py
```

## 슬랙 앱 설정

1. [api.slack.com/apps](https://api.slack.com/apps) 에서 앱 생성
2. **OAuth & Permissions** → Scopes → Bot Token Scopes에 `chat:write` 추가
3. 앱을 워크스페이스에 설치 후 `xoxb-` 토큰 복사
4. 알림 받을 채널에 봇 초대: `/invite @봇이름`
5. 채널 ID 복사 (채널 우클릭 → 채널 ID 복사)

## 채널톡 Webhook 설정

1. 채널톡 관리자 콘솔 → 설정 → Webhook
2. Webhook URL 입력: `https://your-server.com/webhook/channeltalk`
3. 이벤트: `message_created` 선택

## 배포 (Railway / Render)

```bash
# Railway
railway up

# Render: render.yaml로 자동 배포
```

환경변수는 배포 플랫폼의 대시보드에서 설정하세요.

"""
슬랙봇 알림 모듈 — Slack Block Kit 기반 리치 메시지 전송
"""
import logging
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


LEVEL_COLOR = {
    "CRITICAL": "#FF0000",  # 빨강
    "HIGH":     "#FF8C00",  # 주황
    "MEDIUM":   "#FFD700",  # 노랑
}

LEVEL_LABEL = {
    "CRITICAL": "🚨 즉시 에스컬레이션 (법무/경영진)",
    "HIGH":     "⚠️  긴급 에스컬레이션 (팀장)",
    "MEDIUM":   "📢 모니터링 필요 (시니어 상담원)",
}


class SlackBot:
    def __init__(self, token: str, channel: str):
        self.client = WebClient(token=token)
        self.channel = channel

    def send_escalation_alert(self, message_data: dict, detection: dict) -> bool:
        """에스컬레이션 알림 슬랙 메시지 전송"""
        level = detection["level"]
        color = LEVEL_COLOR.get(level, "#808080")
        label = LEVEL_LABEL.get(level, "알림")
        keywords = detection["triggered_keywords"] + detection["triggered_patterns"]
        keyword_str = " · ".join([f"`{k}`" for k in keywords]) if keywords else "패턴 감지"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        chat_url = message_data.get("chat_url", "")
        chat_link = f"<{chat_url}|채널톡에서 보기 →>" if chat_url else "채널톡 링크 없음"

        # 메시지 미리보기 (최대 200자)
        text_preview = message_data.get("text", "")[:200]
        if len(message_data.get("text", "")) > 200:
            text_preview += "..."

        blocks = [
            # ── 헤더 ──
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{detection['level_emoji']} CX 에스컬레이션 알림",
                    "emoji": True
                }
            },
            # ── 에스컬레이션 레벨 ──
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*레벨:* {label}\n*감지 사유:* {detection['reason']}"
                }
            },
            {"type": "divider"},
            # ── 고객 정보 ──
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*👤 고객명*\n{message_data.get('customer_name', '알 수 없음')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*🏢 회사*\n{message_data.get('company', '-') or '-'}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*💬 문의 제목*\n{message_data.get('chat_title', '-')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*👨‍💼 담당 상담원*\n{message_data.get('assignee', '미배정')}"
                    },
                ]
            },
            # ── 트리거 키워드 ──
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🔑 감지된 키워드/패턴*\n{keyword_str}"
                }
            },
            # ── 메시지 내용 ──
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📝 고객 메시지*\n```{text_preview}```"
                }
            },
            {"type": "divider"},
            # ── 액션 버튼 ──
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "채널톡에서 보기", "emoji": True},
                        "url": chat_url or "https://desk.channel.io",
                        "style": "primary"
                    }
                ]
            },
            # ── 푸터 ──
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🤖 CX Escalation Bot  |  {now}"
                    }
                ]
            }
        ]

        # attachment로 색상 표시 (레거시 색상 사이드바)
        attachments = [{"color": color, "blocks": blocks}]

        try:
            self.client.chat_postMessage(
                channel=self.channel,
                text=f"{detection['level_emoji']} [{level}] CX 에스컬레이션: {message_data.get('customer_name')} 고객",
                attachments=attachments,
            )
            logger.info(f"슬랙 알림 전송 완료: channel={self.channel}")
            return True
        except SlackApiError as e:
            logger.error(f"슬랙 전송 실패: {e.response['error']}")
            return False

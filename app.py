"""
채널톡 Webhook → 에스컬레이션 감지 → 슬랙봇 알림 서버
"""
import hmac
import hashlib
import json
import logging
from flask import Flask, request, jsonify
from detector import EscalationDetector
from slack_bot import SlackBot
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
config = Config()
detector = EscalationDetector()
slack = SlackBot(token=config.SLACK_BOT_TOKEN, channel=config.SLACK_CHANNEL_ID)


def verify_channeltalk_signature(body: bytes, signature: str) -> bool:
    """채널톡 Webhook 서명 검증 (HMAC-SHA256)"""
    token = config.CHANNELTALK_WEBHOOK_TOKEN or config.CHANNELTALK_SECRET
    if not token:
        logger.warning("서명 검증 토큰 미설정 → 검증 건너뜀")
        return True
    expected = hmac.new(
        token.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "channeltalk-escalation-bot"})


@app.route("/webhook/channeltalk", methods=["POST"])
def channeltalk_webhook():
    """채널톡 Webhook 수신 엔드포인트"""
    # 서명 검증
    signature = request.headers.get("X-Signature", "")
    if not verify_channeltalk_signature(request.data, signature):
        logger.warning("서명 검증 실패")
        return jsonify({"error": "Unauthorized"}), 401

    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    event_type = payload.get("type", "unknown")
    logger.info(f"수신된 이벤트 전체: {json.dumps(payload, ensure_ascii=False)[:500]}")

    # 메시지 이벤트만 처리 (채널톡 실제 타입에 맞게 확장)
    MESSAGE_TYPES = (
        "message_created", "message_added",
        "userChat", "userChatMessage",
        "message", "chat_message",
    )
    if event_type not in MESSAGE_TYPES:
        logger.info(f"무시된 이벤트 타입: {event_type}")
        return jsonify({"status": "ignored", "reason": f"event type={event_type}"}), 200

    # 고객 메시지만 처리 (상담원 메시지 제외)
    entity = payload.get("entity", {})
    author = entity.get("author", {})
    if author.get("type") in ("manager", "bot"):
        return jsonify({"status": "ignored", "reason": "manager/bot message"}), 200

    # 메시지 파싱
    message_text = entity.get("plainText", "") or entity.get("text", "")
    refers = payload.get("refers", {})
    chat_info = refers.get("chat", {})
    user_info = refers.get("user", {})

    message_data = {
        "message_id": entity.get("id", ""),
        "chat_id": entity.get("chatId", chat_info.get("id", "")),
        "chat_title": chat_info.get("title", "문의"),
        "chat_url": chat_info.get("url", ""),
        "customer_name": author.get("name") or user_info.get("name", "알 수 없음"),
        "company": user_info.get("profile", {}).get("company", ""),
        "text": message_text,
        "assignee": chat_info.get("assignee", {}).get("name", "미배정"),
    }

    # 에스컬레이션 감지
    result = detector.analyze(message_data["text"])

    if result["should_escalate"]:
        logger.info(f"[에스컬레이션 감지] 레벨={result['level']}, 키워드={result['triggered_keywords']}")
        slack.send_escalation_alert(message_data, result)
    else:
        logger.info("에스컬레이션 불필요")

    return jsonify({"status": "ok", "escalated": result["should_escalate"]}), 200


if __name__ == "__main__":
    port = int(config.PORT)
    logger.info(f"서버 시작: port={port}")
    app.run(host="0.0.0.0", port=port, debug=False)

"""
환경변수 기반 설정 관리
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # 채널톡
    CHANNELTALK_ACCESS_KEY: str = os.getenv("CHANNELTALK_ACCESS_KEY", "69c78ac84aec23cf0dfd")
    CHANNELTALK_SECRET: str     = os.getenv("CHANNELTALK_SECRET", "99a1257ec39a1a867e2c015af9a69435")

    # 슬랙봇
    SLACK_BOT_TOKEN: str   = os.getenv("SLACK_BOT_TOKEN", "")      # xoxb-...
    SLACK_CHANNEL_ID: str  = os.getenv("SLACK_CHANNEL_ID", "")     # C1234567890

    # 서버
    PORT: int = int(os.getenv("PORT", "8000"))

    def validate(self):
        errors = []
        if not self.SLACK_BOT_TOKEN:
            errors.append("SLACK_BOT_TOKEN이 설정되지 않았습니다.")
        if not self.SLACK_CHANNEL_ID:
            errors.append("SLACK_CHANNEL_ID가 설정되지 않았습니다.")
        if errors:
            raise ValueError("\n".join(errors))

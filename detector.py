"""
에스컬레이션 감지 모듈
- Level 1 CRITICAL : 즉시 법무/경영진 에스컬레이션
- Level 2 HIGH     : 팀장 에스컬레이션
- Level 3 MEDIUM   : 시니어 상담원 전달
"""
import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class DetectionResult:
    should_escalate: bool
    level: str                          # CRITICAL / HIGH / MEDIUM / NONE
    level_emoji: str
    triggered_keywords: List[str]
    triggered_patterns: List[str]
    reason: str
    score: int


# ── 키워드 정의 ──────────────────────────────────────────────
KEYWORD_MAP = {
    "CRITICAL": {
        "keywords": [
            "소송", "고소", "법무", "내용증명", "변호사", "형사", "민사",
            "경찰", "고발", "법적 조치", "법적조치", "검찰", "소비자원",
            "공정위", "개인정보위", "집단소송",
        ],
        "score": 100,
        "reason": "법적 조치 / 기관 신고 관련 발언 감지",
    },
    "HIGH": {
        "keywords": [
            "사기", "협박", "욕설", "언론", "기자", "뉴스", "방송",
            "SNS 공개", "SNS공개", "인스타", "유튜브", "블로그 올림",
            "개인정보 유출", "개인정보유출", "환불 거부", "환불거부",
            "결제 취소 안됨", "먹튀", "신고", "피해", "피해자",
        ],
        "score": 70,
        "reason": "고위험 민원 / 외부 공개 위협 감지",
    },
    "MEDIUM": {
        "keywords": [
            "몇 번이나", "몇번이나", "계속 안됨", "계속안됨", "반복",
            "또 오류", "또오류", "답답", "화나", "화남", "짜증",
            "무시", "응답 없", "응답없", "해결 안됨", "해결안됨",
            "어이없", "황당", "실망", "최악", "최하",
        ],
        "score": 40,
        "reason": "반복 불만 / 감정 격화 감지",
    },
}

# ── 패턴(정규식) 정의 ─────────────────────────────────────────
PATTERN_MAP = {
    "CRITICAL": [
        (r"법적\s*(대응|조치|절차)", "법적 대응 언급"),
        (r"소송\s*(걸|제기|진행)", "소송 제기 언급"),
        (r"(내용|통지)\s*증명", "내용증명 언급"),
    ],
    "HIGH": [
        (r"(SNS|인스타|트위터|유튜브|블로그).{0,10}(올|공개|퍼|알릴)", "SNS 공개 위협"),
        (r"(기자|언론|방송).{0,10}(연락|제보|알릴)", "언론 제보 위협"),
        (r"환불.{0,10}(안|못|거부|거절)", "환불 거부 불만"),
    ],
    "MEDIUM": [
        (r"\d+\s*번.{0,5}(문의|연락|요청|말)", "반복 문의 횟수 언급"),
        (r"(오래|얼마나|언제까지).{0,10}(기다|걸리|안되)", "대기 불만"),
    ],
}


class EscalationDetector:
    def analyze(self, text: str) -> dict:
        if not text or not text.strip():
            return self._no_escalation()

        score = 0
        triggered_keywords: List[str] = []
        triggered_patterns: List[str] = []
        highest_level = "NONE"

        for level, cfg in KEYWORD_MAP.items():
            for kw in cfg["keywords"]:
                if kw in text:
                    triggered_keywords.append(kw)
                    score = max(score, cfg["score"])
                    if self._level_priority(level) > self._level_priority(highest_level):
                        highest_level = level

        for level, patterns in PATTERN_MAP.items():
            for pattern, desc in patterns:
                if re.search(pattern, text):
                    triggered_patterns.append(desc)
                    level_score = KEYWORD_MAP[level]["score"]
                    score = max(score, level_score)
                    if self._level_priority(level) > self._level_priority(highest_level):
                        highest_level = level

        should_escalate = score >= 40
        reason = KEYWORD_MAP.get(highest_level, {}).get("reason", "")

        return DetectionResult(
            should_escalate=should_escalate,
            level=highest_level,
            level_emoji=self._level_emoji(highest_level),
            triggered_keywords=triggered_keywords,
            triggered_patterns=triggered_patterns,
            reason=reason,
            score=score,
        ).__dict__

    @staticmethod
    def _level_priority(level: str) -> int:
        return {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "NONE": 0}.get(level, 0)

    @staticmethod
    def _level_emoji(level: str) -> str:
        return {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "📢", "NONE": "✅"}.get(level, "")

    @staticmethod
    def _no_escalation() -> dict:
        return DetectionResult(
            should_escalate=False,
            level="NONE",
            level_emoji="✅",
            triggered_keywords=[],
            triggered_patterns=[],
            reason="",
            score=0,
        ).__dict__

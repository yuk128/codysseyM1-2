import openai
from openai import OpenAI

from config import GEMINI_API_KEY, GEMINI_MODEL

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
MAX_TOKENS = 1000
HISTORY_LIMIT = 10  # AI에 전달할 이전 메시지 개수

_client = None


class AIServiceError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise AIServiceError("서버에 AI API 키가 설정되지 않았습니다.", 500)
        _client = OpenAI(api_key=GEMINI_API_KEY, base_url=GEMINI_BASE_URL, timeout=30)
    return _client


def build_system_prompt(summary: dict) -> str:
    """데이터 요약을 시스템 프롬프트에 주입한다 (컨텍스트 주입)."""
    if not summary.get("count"):
        data_part = "- 저장된 데이터가 없습니다."
        last_date = "알 수 없음"
    else:
        m = summary["metrics"]
        last_date = summary["period"].split(" ~ ")[-1]
        data_part = (
            f"- 데이터 기간: {summary['period']}\n"
            f"- 총 레코드: {summary['count']}개 (서울 일별 평균기온, 단위 °C)\n"
            f"- 전체 평균: {m['average']}°C\n"
            f"- 최고: {m['max']['value']}°C ({m['max']['date']})\n"
            f"- 최저: {m['min']['value']}°C ({m['min']['date']})\n"
            f"- 최근 7일 평균: {m['recent_7d_average']}°C\n"
            f"- 최근 30일 평균: {m['recent_30d_average']}°C\n"
            f"- 최근 트렌드: {summary['trend']}"
        )

    return (
        "당신은 서울 일별 기온 데이터를 분석해 주는 데이터 분석 비서입니다.\n\n"
        "[사용자 데이터 요약]\n"
        f"{data_part}\n\n"
        "[답변 규칙]\n"
        "- 위 요약을 근거로 한국어로 간결하게(3~5문장) 답하세요.\n"
        f"- '오늘', '이번 달', '최근'은 실제 현재가 아니라 데이터의 마지막 날짜({last_date}) 기준으로 "
        "해석하고, 그 기준임을 답변에 밝히세요.\n"
        "- 기온은 계절의 영향을 받으므로 '최근 트렌드'는 계절 변화를 감안해 설명하세요. "
        "(예: 가을에서 겨울로 갈 때의 하락은 자연스러운 현상입니다.)\n"
        "- 요약에 없는 값(특정 날짜의 기온, 월별 평균 등)은 지어내지 말고 "
        "'현재 요약에는 없는 정보'라고 말하세요.\n"
        "- 기온 데이터와 무관한 질문에는 정중히 기온 관련 질문을 유도하세요."
    )


def generate_reply(summary: dict, history: list[dict], user_message: str) -> str:
    messages = [{"role": "system", "content": build_system_prompt(summary)}]
    messages += history[-HISTORY_LIMIT:]
    messages.append({"role": "user", "content": user_message})

    client = _get_client()
    kwargs = dict(model=GEMINI_MODEL, messages=messages, max_tokens=MAX_TOKENS)

    try:
        try:
            res = client.chat.completions.create(reasoning_effort="low", **kwargs)
        except openai.BadRequestError:
            # 모델이 reasoning_effort를 지원하지 않는 경우 옵션 없이 재시도
            res = client.chat.completions.create(**kwargs)
    except openai.RateLimitError:
        raise AIServiceError("AI 무료 사용 한도에 도달했어요. 잠시 후 다시 시도해 주세요.", 429)
    except (openai.AuthenticationError, openai.PermissionDeniedError):
        raise AIServiceError("AI API 키가 올바르지 않습니다. 서버 설정을 확인해 주세요.", 500)
    except openai.APITimeoutError:
        raise AIServiceError("AI 응답이 너무 늦어지고 있어요. 잠시 후 다시 시도해 주세요.", 504)
    except openai.APIConnectionError:
        raise AIServiceError("AI 서버에 연결하지 못했어요. 잠시 후 다시 시도해 주세요.", 503)
    except openai.APIStatusError:
        raise AIServiceError("AI 서버에서 오류가 발생했어요. 잠시 후 다시 시도해 주세요.", 502)

    text = (res.choices[0].message.content or "").strip() if res.choices else ""
    if not text:
        raise AIServiceError("AI가 빈 응답을 돌려줬어요. 질문을 바꿔서 다시 시도해 주세요.", 502)
    return text
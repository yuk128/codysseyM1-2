import time

import requests

BASE = "http://127.0.0.1:8000"
CHAT = f"{BASE}/api/chat"
CONV = f"{BASE}/api/conversations"
results = []


def check(name, ok, detail=""):
    print(("[PASS] " if ok else "[FAIL] ") + name, detail)
    results.append(bool(ok))


def wait_for_chat_route(timeout=40):
    end = time.time() + timeout
    while time.time() < end:
        try:
            paths = requests.get(f"{BASE}/openapi.json", timeout=3).json().get("paths", {})
            if "/api/chat" in paths:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


if not wait_for_chat_route():
    print("서버에서 /api/chat 을 찾지 못했습니다. 서버 터미널의 에러 로그를 확인해 주세요.")
    raise SystemExit(1)

before = len(requests.get(CONV, params={"limit": 1000}, timeout=30).json())

# 1. 새 대화
r = requests.post(CHAT, json={"message": "가장 추웠던 날은 언제였어?"}, timeout=60)
if r.status_code == 429:
    print("AI 무료 한도에 걸렸습니다. 1~2분 뒤 다시 실행해 주세요:", r.json().get("detail"))
    raise SystemExit(1)
body = r.json() if r.status_code == 200 else {}
conv_id = body.get("conversation_id")
check("챗봇 응답 (200, 답변·대화 id)", r.status_code == 200 and body.get("reply") and conv_id,
      f"status={r.status_code}")
print("   AI:", (body.get("reply") or r.text)[:300].replace("\n", " "))

# 2. 데이터 요약이 답변에 반영됐는지 (최저 -14.9°C)
check("답변에 데이터 반영 (최저 -14.9)", "14.9" in (body.get("reply") or ""))

# 3. 이어서 질문
r2 = requests.post(CHAT, json={"message": "그럼 가장 더웠던 날은?", "conversation_id": conv_id}, timeout=60)
b2 = r2.json() if r2.status_code == 200 else {}
check("이어서 질문 (같은 대화 id 유지)", r2.status_code == 200 and b2.get("conversation_id") == conv_id,
      f"status={r2.status_code}")
print("   AI:", (b2.get("reply") or r2.text)[:300].replace("\n", " "))

# 4. 자동 저장
conv = requests.get(f"{CONV}/{conv_id}", timeout=30).json()
roles = [m["role"] for m in conv.get("messages", [])]
check("대화 자동 저장 (4개, user/assistant 순서)",
      roles == ["user", "assistant", "user", "assistant"], f"roles={roles}")

# 5. 검증 / 오류 처리
r = requests.post(CHAT, json={"message": ""}, timeout=30)
check("빈 메시지 거절 (422)", r.status_code == 422)
r = requests.post(CHAT, json={"message": "   "}, timeout=30)
check("공백 메시지 거절 (422)", r.status_code == 422)
r = requests.post(CHAT, json={"message": "안녕", "conversation_id": "not-exist-0000"}, timeout=30)
check("없는 대화 id (404)", r.status_code == 404)

# 6. 정리
requests.delete(f"{CONV}/{conv_id}", timeout=30)
after = len(requests.get(CONV, params={"limit": 1000}, timeout=30).json())
check("테스트 대화 정리", after == before, f"count={after}")

print()
print(f"결과: {sum(results)}/{len(results)} 통과")
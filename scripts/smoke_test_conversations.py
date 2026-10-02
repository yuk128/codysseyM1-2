import requests

BASE = "http://127.0.0.1:8000"
URL = f"{BASE}/api/conversations"
results = []
created = []


def check(name, ok, detail=""):
    print(("[PASS] " if ok else "[FAIL] ") + name, detail)
    results.append(bool(ok))


def total():
    return len(requests.get(URL, params={"limit": 1000}, timeout=30).json())


before = total()

msgs = [
    {"role": "user", "content": "가장 추웠던 날은 언제야?"},
    {"role": "assistant", "content": "2023년 1월 24일에 가장 추웠어요."},
]

# 1. 저장 (제목 자동 생성)
r = requests.post(URL, json={"messages": msgs}, timeout=30)
conv_id = r.json().get("id")
created.append(conv_id)
check("대화 저장 (201)", r.status_code == 201 and conv_id, f"id={conv_id}")
check("제목 자동 생성", r.json().get("title", "").startswith("가장 추웠던 날"), f"title={r.json().get('title')}")

# 2. 제목 직접 지정 + 빈 메시지
r = requests.post(URL, json={"title": "직접 지은 제목"}, timeout=30)
created.append(r.json().get("id"))
check("제목 지정 / 빈 메시지 저장 (201)", r.status_code == 201 and r.json().get("title") == "직접 지은 제목")

# 3. 검증 실패
r = requests.post(URL, json={"messages": [{"role": "admin", "content": "안녕"}]}, timeout=30)
check("잘못된 role 거절 (422)", r.status_code == 422)
r = requests.post(URL, json={"messages": [{"role": "user", "content": ""}]}, timeout=30)
check("빈 content 거절 (422)", r.status_code == 422)

# 4. 목록
r = requests.get(URL, timeout=30)
items = r.json()
mine = next((i for i in items if i["id"] == conv_id), None)
check("목록 조회 (200, 최신순)", r.status_code == 200 and items and items[0]["id"] in created)
check("목록에 messages 미포함 + 개수 표시", mine and "messages" not in mine and mine["message_count"] == 2)

# 5. 상세 (대화 불러오기)
r = requests.get(f"{URL}/{conv_id}", timeout=30)
body = r.json()
check("대화 불러오기 (200, 메시지 2개)", r.status_code == 200 and len(body.get("messages", [])) == 2)
check("메시지 내용 일치", body.get("messages") == msgs)

# 6. 없는 id
r = requests.get(f"{URL}/not-exist-0000", timeout=30)
check("없는 대화 조회 (404)", r.status_code == 404)

# 7. 삭제
r = requests.delete(f"{URL}/{conv_id}", timeout=30)
check("대화 삭제 (200)", r.status_code == 200)
r = requests.get(f"{URL}/{conv_id}", timeout=30)
check("삭제 후 조회 (404)", r.status_code == 404)
r = requests.delete(f"{URL}/{conv_id}", timeout=30)
check("없는 id 삭제 (404)", r.status_code == 404)

# 8. 정리
for cid in created:
    requests.delete(f"{URL}/{cid}", timeout=30)
check("테스트 데이터 정리 후 개수 원래대로", total() == before, f"count={total()}")

print()
print(f"결과: {sum(results)}/{len(results)} 통과")
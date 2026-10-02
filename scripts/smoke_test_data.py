import requests

BASE = "http://127.0.0.1:8000"
TEST_DATE = "2099-01-01"
results = []


def check(name, ok, detail=""):
    print(("[PASS] " if ok else "[FAIL] ") + name, detail)
    results.append(bool(ok))


def count():
    return requests.get(f"{BASE}/api/data/summary", timeout=30).json()["count"]


# 0. 이전 테스트 찌꺼기 정리
old = requests.get(f"{BASE}/api/data", params={"start_date": TEST_DATE, "end_date": TEST_DATE}, timeout=30).json()
for item in old:
    requests.delete(f"{BASE}/api/data/{item['id']}", timeout=30)

# 1. 요약 조회
r = requests.get(f"{BASE}/api/data/summary", timeout=30)
before = r.json().get("count")
check("요약 조회 (200, 731건 이상)", r.status_code == 200 and before >= 731, f"count={before}")

# 2. 목록 조회
r = requests.get(f"{BASE}/api/data", params={"limit": 5}, timeout=30)
check("목록 조회 (5건, 최신순)", r.status_code == 200 and len(r.json()) == 5, f"첫 항목={r.json()[0]['date']}")

# 3. 추가
body = {"date": TEST_DATE, "value": -3.2, "memo": "자동 테스트"}
r = requests.post(f"{BASE}/api/data", json=body, timeout=30)
doc_id = r.json().get("id")
check("추가 (201)", r.status_code == 201 and doc_id, f"id={doc_id}")

# 4. 같은 날짜 중복
r = requests.post(f"{BASE}/api/data", json=body, timeout=30)
check("중복 날짜 거절 (409)", r.status_code == 409)

# 5. 값 범위 초과
r = requests.post(f"{BASE}/api/data", json={**body, "date": "2099-01-02", "value": 999}, timeout=30)
check("값 범위 초과 거절 (422)", r.status_code == 422)

# 6. 잘못된 날짜
r = requests.post(f"{BASE}/api/data", json={**body, "date": "2099-13-45"}, timeout=30)
check("잘못된 날짜 거절 (422)", r.status_code == 422)

# 7. 요약이 바로 갱신되는지 (캐시 무효화)
check("추가 후 요약 개수 +1", count() == before + 1)

# 8. 수정
r = requests.put(f"{BASE}/api/data/{doc_id}", json={"memo": "수정됨"}, timeout=30)
check("수정 (200, memo 변경)", r.status_code == 200 and r.json().get("memo") == "수정됨")

# 9. 빈 수정
r = requests.put(f"{BASE}/api/data/{doc_id}", json={}, timeout=30)
check("빈 수정 거절 (400)", r.status_code == 400)

# 10. 삭제
r = requests.delete(f"{BASE}/api/data/{doc_id}", timeout=30)
check("삭제 (200)", r.status_code == 200)

# 11. 없는 id 삭제
r = requests.delete(f"{BASE}/api/data/{doc_id}", timeout=30)
check("없는 id 삭제 (404)", r.status_code == 404)

# 12. 원상 복구 확인
check("삭제 후 요약 개수 원래대로", count() == before, f"count={count()}")

print()
print(f"결과: {sum(results)}/{len(results)} 통과")
from database import db

ref = db.collection("test").document("hello")
ref.set({"msg": "연결 성공"})
print(ref.get().to_dict())
ref.delete()  # 테스트 문서는 바로 정리
print("정리 완료")
import pandas as pd

from database import db

CSV_PATH = "data/temperature_seoul_2023_2024.csv"
BATCH_SIZE = 400  # Firestore 배치 한도(500) 이하

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
col = db.collection("data")

batch = db.batch()
count = 0
for row in df.itertuples():
    # 문서 ID를 날짜로 지정 -> 여러 번 실행해도 중복 생성되지 않음
    batch.set(
        col.document(row.date),
        {
            "date": row.date,
            "value": float(row.temp_mean),
            "memo": f"최고 {row.temp_max}°C / 최저 {row.temp_min}°C",
        },
    )
    count += 1
    if count % BATCH_SIZE == 0:
        batch.commit()
        batch = db.batch()
batch.commit()

total = len(list(col.stream()))
print(f"업로드 완료: {count}건 / 컬렉션 문서 수: {total}건")
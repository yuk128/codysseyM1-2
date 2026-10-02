import json
import pandas as pd
from services.analysis import compute_summary

df = pd.read_csv("data/temperature_seoul_2023_2024.csv", encoding="utf-8-sig")

records = [
    {
        "date": row.date,
        "value": row.temp_mean,
        "memo": f"최고 {row.temp_max}°C / 최저 {row.temp_min}°C",
    }
    for row in df.itertuples()
]

print(f"레코드 수: {len(records)}")
print(json.dumps(compute_summary(records), ensure_ascii=False, indent=2))
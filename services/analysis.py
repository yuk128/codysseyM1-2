from statistics import mean


def compute_summary(records: list[dict]) -> dict:
    """records: [{"date": "2023-01-01", "value": -2.5, "memo": "..."}, ...]"""
    if not records:
        return {"period": None, "count": 0, "metrics": {}, "trend": "데이터 없음"}

    rows = sorted(records, key=lambda r: r["date"])
    values = [r["value"] for r in rows]
    hottest = max(rows, key=lambda r: r["value"])
    coldest = min(rows, key=lambda r: r["value"])

    recent = values[-30:]
    previous = values[-60:-30]

    if previous:
        diff = round(mean(recent) - mean(previous), 1)
        if diff >= 0.5:
            trend = f"상승 (최근 30일 평균이 직전 30일보다 {diff:+}°C)"
        elif diff <= -0.5:
            trend = f"하락 (최근 30일 평균이 직전 30일보다 {diff:+}°C)"
        else:
            trend = f"유지 (직전 30일 대비 {diff:+}°C)"
    else:
        trend = "비교 데이터 부족"

    return {
        "period": f"{rows[0]['date']} ~ {rows[-1]['date']}",
        "count": len(rows),
        "metrics": {
            "average": round(mean(values), 1),
            "max": {"value": hottest["value"], "date": hottest["date"]},
            "min": {"value": coldest["value"], "date": coldest["date"]},
            "recent_7d_average": round(mean(values[-7:]), 1),
            "recent_30d_average": round(mean(recent), 1),
        },
        "trend": trend,
    }
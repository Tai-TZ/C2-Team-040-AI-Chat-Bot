"""OpenWeatherMap forecast for trip planning."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta
from typing import Any

import requests

from src.utils.text import normalize_text

GEO_URL = "https://api.openweathermap.org/geo/1.0/direct"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

# Fallback coordinates for VinWonders regions (geocode can be ambiguous)
REGION_COORDS: dict[str, tuple[float, float, str]] = {
    "nha trang": (12.2388, 109.1967, "Nha Trang"),
    "phu quoc": (10.2899, 103.984, "Phú Quốc"),
    "ha noi": (21.0278, 105.8342, "Hà Nội"),
    "nghe an": (18.6796, 105.6813, "Nghệ An"),
    "ha tinh": (18.3559, 105.8877, "Hà Tĩnh"),
    "da nang": (16.0544, 108.2022, "Đà Nẵng"),
    "hoi an": (15.8801, 108.338, "Hội An"),
    "hai phong": (20.8449, 106.6881, "Hải Phòng"),
    "ho chi minh": (10.8231, 106.6297, "TP. Hồ Chí Minh"),
    "tp ho chi minh": (10.8231, 106.6297, "TP. Hồ Chí Minh"),
}


def _api_key() -> str:
    key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    if not key:
        raise ValueError("OPENWEATHER_API_KEY is not set in .env")
    return key


def _parse_dd_mm_yyyy(date: str) -> datetime:
    if re.match(r"^\d{2}-\d{2}-\d{4}$", date):
        d, m, y = date.split("-")
        return datetime(int(y), int(m), int(d), 12, 0, 0)
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        y, m, d = date.split("-")
        return datetime(int(y), int(m), int(d), 12, 0, 0)
    raise ValueError("using_date must be DD-MM-YYYY or YYYY-MM-DD")


def _geocode(location: str) -> tuple[float, float, str]:
    norm = normalize_text(location)
    for key, (lat, lon, label) in REGION_COORDS.items():
        if key in norm or norm in key:
            return lat, lon, label

    resp = requests.get(
        GEO_URL,
        params={"q": f"{location},VN", "limit": 1, "appid": _api_key()},
        timeout=15,
    )
    resp.raise_for_status()
    rows = resp.json()
    if not rows:
        raise ValueError(f"Không tìm thấy tọa độ cho '{location}'")
    row = rows[0]
    name = row.get("local_names", {}).get("vi") or row.get("name", location)
    return float(row["lat"]), float(row["lon"]), name


def _rain_from_entry(entry: dict[str, Any]) -> bool:
    weather_list = entry.get("weather") or []
    main = (weather_list[0].get("main") or "").lower() if weather_list else ""
    desc = (weather_list[0].get("description") or "").lower() if weather_list else ""
    pop = float(entry.get("pop") or 0)
    if main in ("rain", "drizzle", "thunderstorm"):
        return True
    if pop >= 0.45:
        return True
    if "mua" in desc or "rain" in desc or "drizzle" in desc:
        return True
    return False


def _pick_forecast_slot(forecast_list: list[dict], target: datetime) -> dict[str, Any] | None:
    target_ts = target.timestamp()
    best = None
    best_diff = 10**9
    for item in forecast_list:
        dt = datetime.fromtimestamp(item["dt"])
        diff = abs(dt.timestamp() - target_ts)
        if diff < best_diff:
            best_diff = diff
            best = item
    return best


def get_weather_forecast(location: str, using_date: str) -> str:
    """
    Forecast for a location on visit date (DD-MM-YYYY).
    Returns JSON with rain flags and reschedule hints.
    """
    target = _parse_dd_mm_yyyy(using_date)
    lat, lon, place_name = _geocode(location)

    resp = requests.get(
        FORECAST_URL,
        params={
            "lat": lat,
            "lon": lon,
            "appid": _api_key(),
            "units": "metric",
            "lang": "vi",
            "cnt": 40,
        },
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    forecast_list = data.get("list") or []

    slot = _pick_forecast_slot(forecast_list, target)
    if not slot:
        return json.dumps(
            {"error": "Không có dự báo cho ngày này", "location": place_name},
            ensure_ascii=False,
        )

    weather = (slot.get("weather") or [{}])[0]
    has_rain = _rain_from_entry(slot)
    temp = slot.get("main", {}).get("temp")
    feels = slot.get("main", {}).get("feels_like")
    humidity = slot.get("main", {}).get("humidity")
    wind = slot.get("wind", {}).get("speed")
    pop = round(float(slot.get("pop") or 0) * 100)

    next_day = target + timedelta(days=1)
    next_slot = _pick_forecast_slot(forecast_list, next_day)
    next_has_rain = _rain_from_entry(next_slot) if next_slot else None

    if has_rain:
        recommendation = (
            "Dự báo có mưa/rủi ro mưa. Nên cân nhắc dời sang ngày khác hoặc mang áo mưa; "
            "ưu tiên hoạt động trong nhà (show, spa, Aquafield)."
        )
        suggest_reschedule = True
    elif pop >= 30:
        recommendation = (
            "Khả năng mưa rải rác. Nên theo dõi sát và chuẩn bị phương án trong nhà."
        )
        suggest_reschedule = False
    else:
        recommendation = "Thời tiết thuận lợi cho vui chơi ngoài trời tại VinWonders."
        suggest_reschedule = False

    payload = {
        "location": place_name,
        "usingDate": using_date,
        "tempC": round(temp, 1) if temp is not None else None,
        "feelsLikeC": round(feels, 1) if feels is not None else None,
        "description": weather.get("description", ""),
        "icon": weather.get("icon", "01d"),
        "humidity": humidity,
        "windMs": round(wind, 1) if wind is not None else None,
        "popPercent": pop,
        "hasRain": has_rain,
        "rainRisk": "high" if has_rain else ("medium" if pop >= 30 else "low"),
        "recommendation": recommendation,
        "suggestReschedule": suggest_reschedule,
        "nextDayDate": next_day.strftime("%d-%m-%Y"),
        "nextDayHasRain": next_has_rain,
        "lat": lat,
        "lon": lon,
    }
    return json.dumps(payload, ensure_ascii=False)

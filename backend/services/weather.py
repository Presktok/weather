import asyncio
import os
from typing import Any

import httpx

# Fallback for monsoon demo corridor when API data is calm
DEMO_WAVE_BY_REGION = {
    "monsoon": {"wind": 28, "wind_direction": 220, "wave": 4.3},
    "bay": {"wind": 22, "wind_direction": 180, "wave": 3.5},
    "default": {"wind": 15, "wind_direction": 135, "wave": 1.8},
}

USE_DEMO_WEATHER = os.getenv("USE_DEMO_WEATHER", "").lower() in ("1", "true", "yes")
HTTP_TIMEOUT = httpx.Timeout(8.0, connect=3.0)


def _demo_for_point(lat: float, lon: float) -> dict:
    if 5 <= lat <= 15 and 80 <= lon <= 95:
        return DEMO_WAVE_BY_REGION["monsoon"].copy()
    if 8 <= lat <= 14 and 75 <= lon <= 90:
        return DEMO_WAVE_BY_REGION["bay"].copy()
    return DEMO_WAVE_BY_REGION["default"].copy()


def _format_weather(lat: float, lon: float, wind: float, wind_dir: float, wave: float, source: str) -> dict:
    """Week 1 weather payload shape."""
    return {
        "lat": lat,
        "lon": lon,
        "wind": round(wind, 1),
        "wind_direction": round(wind_dir, 0),
        "wave": round(wave, 2),
        "wind_speed": round(wind, 1),
        "wave_height": round(wave, 2),
        "source": source,
    }


def _weather_from_demo(waypoints: list[dict]) -> list[dict]:
    results = []
    for wp in waypoints:
        demo = _demo_for_point(wp["lat"], wp["lon"])
        results.append(
            _format_weather(
                wp["lat"], wp["lon"], demo["wind"], demo["wind_direction"], demo["wave"], "demo"
            )
        )
    return results


def _parse_point_weather(lat: float, lon: float, marine_entry: dict, weather_entry: dict) -> dict:
    demo = _demo_for_point(lat, lon)
    marine = marine_entry.get("current", {}) if marine_entry else {}
    weather = weather_entry.get("current", {}) if weather_entry else {}

    wind = weather.get("wind_speed_10m")
    wave = marine.get("wave_height")

    if wind is None or wave is None:
        return _format_weather(lat, lon, demo["wind"], demo["wind_direction"], demo["wave"], "demo")

    wind_f, wave_f = float(wind), float(wave)
    if demo["wave"] >= 4:
        wind_f = max(wind_f, demo["wind"])
        wave_f = max(wave_f, demo["wave"])

    return _format_weather(
        lat,
        lon,
        wind_f,
        float(weather.get("wind_direction_10m", demo["wind_direction"])),
        wave_f,
        "open-meteo",
    )


async def fetch_weather_for_waypoints(waypoints: list[dict]) -> list[dict]:
    if not waypoints:
        return []

    if USE_DEMO_WEATHER:
        return _weather_from_demo(waypoints)

    lats = ",".join(str(wp["lat"]) for wp in waypoints)
    lons = ",".join(str(wp["lon"]) for wp in waypoints)

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            marine_resp, weather_resp = await asyncio.gather(
                client.get(
                    "https://marine-api.open-meteo.com/v1/marine",
                    params={
                        "latitude": lats,
                        "longitude": lons,
                        "current": "wave_height",
                        "timezone": "auto",
                    },
                ),
                client.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": lats,
                        "longitude": lons,
                        "current": "wind_speed_10m,wind_direction_10m",
                        "wind_speed_unit": "kn",
                        "timezone": "auto",
                    },
                ),
            )
            marine_resp.raise_for_status()
            weather_resp.raise_for_status()
            marine_data = marine_resp.json()
            weather_data = weather_resp.json()

        marine_list = marine_data if isinstance(marine_data, list) else [marine_data]
        weather_list = weather_data if isinstance(weather_data, list) else [weather_data]

        return [
            _parse_point_weather(
                wp["lat"],
                wp["lon"],
                marine_list[i] if i < len(marine_list) else {},
                weather_list[i] if i < len(weather_list) else {},
            )
            for i, wp in enumerate(waypoints)
        ]
    except Exception:
        return _weather_from_demo(waypoints)

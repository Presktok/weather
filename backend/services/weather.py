import asyncio
import os
from datetime import datetime

import httpx

# Regional fallbacks when API data is missing or calm in monsoon corridor
DEMO_WAVE_BY_REGION = {
    "monsoon_peak": {"wind": 28, "wind_direction": 220, "wave": 4.5},
    "monsoon_moderate": {"wind": 20, "wind_direction": 200, "wave": 2.8},
    "monsoon_calm": {"wind": 14, "wind_direction": 160, "wave": 1.6},
    "bay_peak": {"wind": 22, "wind_direction": 180, "wave": 3.6},
    "bay_moderate": {"wind": 16, "wind_direction": 170, "wave": 2.2},
    "default": {"wind": 15, "wind_direction": 135, "wave": 1.8},
}

USE_DEMO_WEATHER = os.getenv("USE_DEMO_WEATHER", "").lower() in ("1", "true", "yes")
HTTP_TIMEOUT = httpx.Timeout(8.0, connect=3.0)

# June–September SW monsoon peak in Bay of Bengal / Andaman corridor
MONSOON_PEAK_MONTHS = {6, 7, 8, 9}
MONSOON_SHOULDER_MONTHS = {5, 10}


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def monsoon_season_label(departure_time: str | None) -> str:
    """Human-readable monsoon phase for UI."""
    phase = _monsoon_season(departure_time)
    return {
        "peak": "Jun–Sep SW monsoon (peak risk in Bay of Bengal)",
        "shoulder": "May / Oct (transition)",
        "off": "Oct–May (typically lower monsoon risk)",
    }[phase]


def _monsoon_season(departure_time: str | None) -> str:
    """peak | shoulder | off — based on voyage departure month."""
    if departure_time:
        month = datetime.strptime(departure_time, "%Y-%m-%d").month
    else:
        month = datetime.now().month
    if month in MONSOON_PEAK_MONTHS:
        return "peak"
    if month in MONSOON_SHOULDER_MONTHS:
        return "shoulder"
    return "off"


def _in_monsoon_corridor(lat: float, lon: float) -> bool:
    return 5 <= lat <= 15 and 80 <= lon <= 95


def _in_bay_corridor(lat: float, lon: float) -> bool:
    return 8 <= lat <= 14 and 75 <= lon <= 90


def _demo_for_point(lat: float, lon: float, departure_time: str | None = None) -> dict:
    season = _monsoon_season(departure_time)
    if _in_monsoon_corridor(lat, lon) or _in_bay_corridor(lat, lon):
        if season == "peak":
            key = "monsoon_peak" if _in_monsoon_corridor(lat, lon) else "bay_peak"
        elif season == "shoulder":
            key = "monsoon_moderate" if _in_monsoon_corridor(lat, lon) else "bay_moderate"
        else:
            key = "monsoon_calm"
        return DEMO_WAVE_BY_REGION[key].copy()
    return DEMO_WAVE_BY_REGION["default"].copy()


def _format_weather(
    lat: float,
    lon: float,
    wind: float,
    wind_dir: float,
    wave: float,
    source: str,
    season: str | None = None,
) -> dict:
    payload = {
        "lat": lat,
        "lon": lon,
        "wind": round(wind, 1),
        "wind_direction": round(wind_dir, 0),
        "wave": round(wave, 2),
        "wind_speed": round(wind, 1),
        "wave_height": round(wave, 2),
        "source": source,
    }
    if season:
        payload["monsoon_season"] = season
    return payload


def _weather_from_demo(waypoints: list[dict], departure_time: str | None = None) -> list[dict]:
    season = _monsoon_season(departure_time)
    results = []
    for wp in waypoints:
        demo = _demo_for_point(wp["lat"], wp["lon"], departure_time)
        results.append(
            _format_weather(
                wp["lat"],
                wp["lon"],
                demo["wind"],
                demo["wind_direction"],
                demo["wave"],
                "demo",
                season=season,
            )
        )
    return results


def _parse_point_weather(
    lat: float,
    lon: float,
    marine_entry: dict,
    weather_entry: dict,
    departure_time: str | None = None,
) -> dict:
    season = _monsoon_season(departure_time)
    demo = _demo_for_point(lat, lon, departure_time)
    marine = marine_entry.get("current", {}) if marine_entry else {}
    weather = weather_entry.get("current", {}) if weather_entry else {}

    wind = _safe_float(weather.get("wind_speed_10m"), demo["wind"])
    wave = _safe_float(marine.get("wave_height"), demo["wave"])

    if weather.get("wind_speed_10m") is None or marine.get("wave_height") is None:
        return _format_weather(
            lat, lon, demo["wind"], demo["wind_direction"], demo["wave"], "demo", season=season
        )

    # Seasonal floor only in monsoon corridor (Open-Meteo can be calm off-season)
    if (_in_monsoon_corridor(lat, lon) or _in_bay_corridor(lat, lon)) and season in ("peak", "shoulder"):
        wind = max(wind, demo["wind"])
        wave = max(wave, demo["wave"])

    wind_dir = _safe_float(weather.get("wind_direction_10m"), demo["wind_direction"])

    return _format_weather(lat, lon, wind, wind_dir, wave, "open-meteo", season=season)


async def fetch_weather_for_waypoints(
    waypoints: list[dict],
    departure_time: str | None = None,
) -> list[dict]:
    if not waypoints:
        return []

    if USE_DEMO_WEATHER:
        return _weather_from_demo(waypoints, departure_time)

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
                departure_time,
            )
            for i, wp in enumerate(waypoints)
        ]
    except Exception:
        return _weather_from_demo(waypoints, departure_time)

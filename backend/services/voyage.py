import asyncio
from datetime import datetime, timedelta

from data.routes import ROUTES, ROTTERDAM_SINGAPORE
from services.calculations import (
    assess_laycan_risk,
    assess_weather_risk,
    build_business_impact,
    build_high_risk_zones,
    build_charter_laycan_warning,
    build_operational_advice,
    build_recommendation_detail,
    build_score_breakdown,
    build_weather_impact_summary,
    is_laycan_badly_missed,
    route_weather_severity,
    summarize_weather_sources,
    calculate_speed_loss,
    calculate_sog,
    fuel_consumption_mt_per_day,
    haversine_nm,
    laycan_metric,
    risk_color,
    risk_metric,
    route_display_scores,
    route_quality_score_100,
    score_component_points,
    weighted_route_score,
)
from services.weather import fetch_weather_for_waypoints


def _build_route_points(route: dict) -> list[dict]:
    points = [route["departure"], *route["waypoints"], route["destination"]]
    return [{"name": p.get("name", "Point"), "lat": p["lat"], "lon": p["lon"]} for p in points]


def get_route_geometry(route_id: str) -> dict:
    route = ROUTES.get(route_id, ROTTERDAM_SINGAPORE)
    points = _build_route_points(route)
    return {
        "id": route["id"],
        "name": route["name"],
        "departure": route["departure"],
        "destination": route["destination"],
        "waypoints": route["waypoints"],
        "path": [{"lat": p["lat"], "lon": p["lon"], "name": p["name"]} for p in points],
    }


async def analyze_voyage(
    route_id: str = "rotterdam-singapore",
    commanded_speed: float = 12.0,
    laycan_start: str = "2026-09-19",
    laycan_end: str = "2026-09-20",
    bunker_price: float = 600.0,
    departure_time: str = "2026-08-22",
) -> dict:
    route = ROUTES.get(route_id, ROTTERDAM_SINGAPORE)
    points = _build_route_points(route)
    weather_data = await fetch_weather_for_waypoints(route["waypoints"])

    legs = []
    total_distance = 0.0
    total_hours = 0.0
    total_fuel = 0.0
    ideal_hours = 0.0
    ideal_fuel = 0.0

    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i + 1]
        dist = haversine_nm(p1["lat"], p1["lon"], p2["lat"], p2["lon"])
        total_distance += dist

        weather = weather_data[i] if i < len(weather_data) else weather_data[-1]
        wave = weather["wave_height"]
        wind = weather.get("wind_speed", weather.get("wind", 0))
        risk = assess_weather_risk(wave, wind)
        speed_loss = calculate_speed_loss(wave_height=wave, wind_speed=wind)
        sog = calculate_sog(commanded_speed, speed_loss)
        hours = dist / sog if sog > 0 else 0
        total_hours += hours

        ideal_leg_hours = dist / commanded_speed
        ideal_hours += ideal_leg_hours

        fuel_rate = fuel_consumption_mt_per_day(sog)
        leg_fuel = fuel_rate * (hours / 24)
        total_fuel += leg_fuel

        ideal_fuel_rate = fuel_consumption_mt_per_day(commanded_speed)
        ideal_fuel += ideal_fuel_rate * (ideal_leg_hours / 24)

        legs.append({
            "from": p1["name"],
            "to": p2["name"],
            "from_lat": p1["lat"],
            "from_lon": p1["lon"],
            "to_lat": p2["lat"],
            "to_lon": p2["lon"],
            "distance_nm": round(dist, 1),
            "weather": weather,
            "risk": risk,
            "risk_color": risk_color(risk),
            "commanded_speed_kn": commanded_speed,
            "speed_loss_kn": speed_loss,
            "stw_kn": commanded_speed,
            "sog_kn": sog,
            "leg_hours": round(hours, 2),
            "fuel_mt": round(leg_fuel, 2),
            "fuel_cost_usd": round(leg_fuel * bunker_price, 0),
        })

    delay_hours = max(total_hours - ideal_hours, 0)
    extra_fuel = max(total_fuel - ideal_fuel, 0)
    laycan = assess_laycan_risk(total_hours, laycan_start, laycan_end, departure_time)

    dep = datetime.strptime(departure_time, "%Y-%m-%d")
    waypoint_etas = []
    cumulative = 0.0
    for leg in legs:
        cumulative += leg["leg_hours"]
        waypoint_etas.append({
            "waypoint": leg["to"],
            "eta": (dep + timedelta(hours=cumulative)).isoformat(),
            "hours_from_departure": round(cumulative, 1),
        })

    summary = {
        "total_distance_nm": round(total_distance, 1),
        "total_voyage_hours": round(total_hours, 2),
        "total_voyage_days": round(total_hours / 24, 1),
        "commanded_speed_kn": commanded_speed,
        "average_sog_kn": round(total_distance / total_hours, 2) if total_hours else 0,
        "total_fuel_mt": round(total_fuel, 0),
        "ideal_fuel_mt": round(ideal_fuel, 0),
        "extra_fuel_mt": round(extra_fuel, 1),
        "extra_fuel_cost_usd": round(extra_fuel * bunker_price, 0),
        "total_fuel_cost_usd": round(total_fuel * bunker_price, 0),
        "bunker_price_usd_per_mt": bunker_price,
        "weather_delay_hours": round(delay_hours, 1),
        "destination_eta": waypoint_etas[-1]["eta"] if waypoint_etas else None,
    }

    analysis = {
        "route": get_route_geometry(route_id),
        "legs": legs,
        "summary": summary,
        "waypoint_etas": waypoint_etas,
        "laycan": laycan,
        "weather_severity": route_weather_severity(legs),
        "business_impact": build_business_impact({"summary": summary, "laycan": laycan}),
        "high_risk_zones": build_high_risk_zones(legs, commanded_speed),
    }
    return analysis


async def compare_routes(
    laycan_start: str = "2026-09-19",
    laycan_end: str = "2026-09-20",
    commanded_speed: float = 12.0,
    bunker_price: float = 600.0,
    departure_time: str = "2026-08-22",
) -> dict:
    route_a, route_b = await asyncio.gather(
        analyze_voyage(
            "rotterdam-singapore", commanded_speed, laycan_start, laycan_end, bunker_price, departure_time
        ),
        analyze_voyage(
            "rotterdam-singapore-alt", commanded_speed, laycan_start, laycan_end, bunker_price, departure_time
        ),
    )

    metrics_a = {
        "cost": route_a["summary"]["total_fuel_cost_usd"],
        "delay": route_a["summary"]["weather_delay_hours"],
        "risk": risk_metric(route_a),
        "laycan": laycan_metric(route_a),
    }
    metrics_b = {
        "cost": route_b["summary"]["total_fuel_cost_usd"],
        "delay": route_b["summary"]["weather_delay_hours"],
        "risk": risk_metric(route_b),
        "laycan": laycan_metric(route_b),
    }

    score_a_raw = weighted_route_score(**metrics_a, other=metrics_b)
    score_b_raw = weighted_route_score(**metrics_b, other=metrics_a)
    if score_b_raw < score_a_raw:
        recommended, loser = route_b, route_a
        label = "Route B"
    elif score_a_raw < score_b_raw:
        recommended, loser = route_a, route_b
        label = "Route A"
    elif metrics_b["risk"] < metrics_a["risk"]:
        recommended, loser = route_b, route_a
        label = "Route B"
    elif metrics_a["risk"] < metrics_b["risk"]:
        recommended, loser = route_a, route_b
        label = "Route A"
    elif metrics_b["cost"] <= metrics_a["cost"]:
        recommended, loser = route_b, route_a
        label = "Route B"
    else:
        recommended, loser = route_a, route_b
        label = "Route A"

    alternative = loser
    baseline = route_a  # Route A = main path (baseline for optimization narrative)
    rec_sum = recommended["summary"]
    alt_sum = alternative["summary"]
    base_sum = baseline["summary"]
    fuel_delta = base_sum["total_fuel_cost_usd"] - rec_sum["total_fuel_cost_usd"]
    delay_delta = base_sum["weather_delay_hours"] - rec_sum["weather_delay_hours"]
    fuel_mt_delta = base_sum["total_fuel_mt"] - rec_sum["total_fuel_mt"]

    charter_warning = build_charter_laycan_warning(route_a, route_b)
    rec_detail = build_recommendation_detail(
        recommended, alternative, label, charter_warning=charter_warning
    )

    score_a_pct, score_b_pct = route_display_scores(
        metrics_a, metrics_b, route_a=route_a, route_b=route_b
    )

    dist_a = route_a["summary"]["total_distance_nm"]
    dist_b = route_b["summary"]["total_distance_nm"]
    extra_nm = round(dist_b - dist_a, 1)

    return {
        "route_a": {"label": "Route A — Main", "analysis": route_a},
        "route_b": {"label": "Route B — Detour", "analysis": route_b},
        "weather_impact": build_weather_impact_summary(route_a),
        "weather_sources": summarize_weather_sources(route_a, route_b),
        "high_risk_zones": route_a["high_risk_zones"],
        "distance": {
            "route_a_nm": dist_a,
            "route_b_nm": dist_b,
            "extra_nm": extra_nm,
        },
        "operational_advice": build_operational_advice(recommended, charter_warning),
        "comparison": {
            "metrics": [
                {
                    "metric": "Distance",
                    "route_a": f"{dist_a:,.0f} nm",
                    "route_b": f"{dist_b:,.0f} nm",
                },
                {
                    "metric": "Weather severity",
                    "route_a": f"{route_a['weather_severity']}/100",
                    "route_b": f"{route_b['weather_severity']}/100",
                },
                {
                    "metric": "Voyage time",
                    "route_a": f"{route_a['summary']['total_voyage_days']}d",
                    "route_b": f"{route_b['summary']['total_voyage_days']}d",
                },
                {
                    "metric": "Destination ETA",
                    "route_a": route_a["laycan"]["predicted_eta_display"],
                    "route_b": route_b["laycan"]["predicted_eta_display"],
                },
                {
                    "metric": "Fuel",
                    "route_a": f"{route_a['summary']['total_fuel_mt']} MT",
                    "route_b": f"{route_b['summary']['total_fuel_mt']} MT",
                },
                {
                    "metric": "Cost",
                    "route_a": f"${route_a['summary']['total_fuel_cost_usd']:,}",
                    "route_b": f"${route_b['summary']['total_fuel_cost_usd']:,}",
                },
                {
                    "metric": "Laycan",
                    "route_a": route_a["laycan"]["risk"],
                    "route_b": route_b["laycan"]["risk"],
                },
                {
                    "metric": "Delay (hrs)",
                    "route_a": route_a["summary"]["weather_delay_hours"],
                    "route_b": route_b["summary"]["weather_delay_hours"],
                },
            ],
        },
        "charter_warning": charter_warning,
        "route_scores": {
            "route_a": score_a_pct,
            "route_b": score_b_pct,
            "route_a_pct": score_a_pct,
            "route_b_pct": score_b_pct,
            "score_gap": abs(score_b_pct - score_a_pct),
            "laycan_penalty_applied": bool(
                charter_warning
                or is_laycan_badly_missed(route_a["laycan"])
                or is_laycan_badly_missed(route_b["laycan"])
            ),
            "laycan_penalty_note": (
                "Scores capped at 70 max with -30 laycan penalty (charter window badly missed)"
                if charter_warning
                else None
            ),
            "weights": {"cost": 0.4, "delay": 0.3, "risk": 0.2, "laycan": 0.1},
            "raw": {"route_a": round(score_a_raw, 3), "route_b": round(score_b_raw, 3)},
            "components": {
                "route_a": {
                    "cost": score_component_points(metrics_a["cost"], metrics_b["cost"], 40),
                    "delay": score_component_points(metrics_a["delay"], metrics_b["delay"], 30),
                    "risk": score_component_points(metrics_a["risk"], metrics_b["risk"], 20),
                    "laycan": score_component_points(metrics_a["laycan"], metrics_b["laycan"], 10),
                },
                "route_b": {
                    "cost": score_component_points(metrics_b["cost"], metrics_a["cost"], 40),
                    "delay": score_component_points(metrics_b["delay"], metrics_a["delay"], 30),
                    "risk": score_component_points(metrics_b["risk"], metrics_a["risk"], 20),
                    "laycan": score_component_points(metrics_b["laycan"], metrics_a["laycan"], 10),
                },
            },
            "breakdown": build_score_breakdown(
                metrics_b if label == "Route B" else metrics_a,
                metrics_a if label == "Route B" else metrics_b,
                charter_warning=charter_warning,
            ),
        },
        "laycan_context": {
            "departure": departure_time,
            "laycan_start": laycan_start,
            "laycan_end": laycan_end,
            "route_a": route_a["laycan"],
            "route_b": route_b["laycan"],
        },
        "savings": {
            "baseline_label": "Route A — Main (baseline)",
            "recommended_label": f"Recommended — {label}",
            "without_optimization": {
                "label": "Route A — Main (baseline)",
                "fuel_cost_usd": base_sum["total_fuel_cost_usd"],
                "fuel_mt": base_sum["total_fuel_mt"],
                "delay_hours": base_sum["weather_delay_hours"],
            },
            "with_recommended": {
                "label": f"Recommended — {label}",
                "fuel_cost_usd": rec_sum["total_fuel_cost_usd"],
                "fuel_mt": rec_sum["total_fuel_mt"],
                "delay_hours": rec_sum["weather_delay_hours"],
            },
            "vs_alternative": {
                "label": f"{label} vs other route",
                "fuel_cost_usd": round(alt_sum["total_fuel_cost_usd"] - rec_sum["total_fuel_cost_usd"], 0),
                "fuel_mt": round(alt_sum["total_fuel_mt"] - rec_sum["total_fuel_mt"], 0),
                "delay_hours": round(alt_sum["weather_delay_hours"] - rec_sum["weather_delay_hours"], 1),
            },
            "net_impact": {
                "fuel_cost_usd": round(abs(fuel_delta), 0),
                "fuel_cost_is_savings": fuel_delta >= 0,
                "fuel_mt": round(abs(fuel_mt_delta), 0),
                "fuel_mt_is_savings": fuel_mt_delta >= 0,
                "delay_hours": round(abs(delay_delta), 1),
                "delay_is_reduction": delay_delta >= 0,
                "extra_fuel_cost_avoided_usd": round(
                    max(
                        baseline["business_impact"]["extra_fuel_cost_usd"]
                        - recommended["business_impact"]["extra_fuel_cost_usd"],
                        0,
                    ),
                    0,
                ),
            },
        },
        "recommendation": {
            "route_id": recommended["route"]["id"],
            "route_label": label,
            "route_name": recommended["route"]["name"],
            "alternative_label": "Route B" if label == "Route A" else "Route A",
            **rec_detail,
            "scores": {
                "route_a": score_a_pct,
                "route_b": score_b_pct,
            },
        },
    }

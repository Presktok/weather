import math
from typing import Literal

RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]
LaycanStatus = Literal["SAFE", "EARLY", "HIGH RISK"]

BASE_SPEED_KN = 12.0
BASE_FUEL_MT_PER_DAY = 32.0


def haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in nautical miles between two coordinates."""
    r = 3440.065
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def assess_weather_risk(wave_height: float, wind_speed: float = 0.0) -> RiskLevel:
    """Week 1 risk engine — wave height (m) and wind speed (kn)."""
    if wave_height > 4 or wind_speed > 25:
        return "HIGH"
    if wave_height > 2 or wind_speed > 15:
        return "MEDIUM"
    return "LOW"


def risk_color(risk: RiskLevel) -> str:
    return {"LOW": "#22c55e", "MEDIUM": "#eab308", "HIGH": "#ef4444"}[risk]


def calculate_speed_loss(wave_height: float, wind_speed: float = 0.0) -> float:
    """Week 2: speed loss from wave and wind."""
    return round(wave_height * 0.20 + wind_speed * 0.01, 2)


def leg_weather_severity(weather: dict) -> int:
    """0–100 severity index from wave (m) and wind (kn)."""
    wave = float(weather.get("wave_height", weather.get("wave", 0)))
    wind = float(weather.get("wind_speed", weather.get("wind", 0)))
    raw = (wave / 5) * 0.7 + (wind / 30) * 0.3
    return min(100, round(100 * raw))


def route_weather_severity(legs: list) -> dict:
    """Average reflects voyage-wide conditions; peak is worst single leg."""
    if not legs:
        return {"average": 0, "peak": 0}
    severities = [leg_weather_severity(leg["weather"]) for leg in legs]
    return {
        "average": round(sum(severities) / len(severities)),
        "peak": max(severities),
    }


def leg_weather_delay_hours(leg: dict, commanded_speed: float) -> float:
    ideal = leg["distance_nm"] / commanded_speed if commanded_speed else 0
    return max(leg["leg_hours"] - ideal, 0)


def summarize_leg_weather_delays(legs: list, commanded_speed: float) -> dict:
    total = 0.0
    high_risk = 0.0
    severe = 0.0
    for leg in legs:
        d = leg_weather_delay_hours(leg, commanded_speed)
        total += d
        if leg["risk"] == "HIGH":
            high_risk += d
        if leg["risk"] in ("HIGH", "MEDIUM"):
            severe += d
    return {
        "weather_delay_hours": round(total, 1),
        "high_risk_weather_delay_hours": round(high_risk, 1),
        "severe_weather_delay_hours": round(severe, 1),
    }


def summarize_weather_sources(*analyses: dict) -> dict:
    open_meteo = 0
    demo = 0
    for analysis in analyses:
        for leg in analysis.get("legs", []):
            if leg["weather"].get("source") == "open-meteo":
                open_meteo += 1
            else:
                demo += 1
    total = open_meteo + demo
    if open_meteo and demo:
        primary, fallback = "Open-Meteo API", "Demo Monsoon Model"
    elif open_meteo:
        primary, fallback = "Open-Meteo API", None
    else:
        primary, fallback = "Demo Monsoon Model", None
    return {
        "primary": primary,
        "fallback": fallback,
        "legs_open_meteo": open_meteo,
        "legs_demo": demo,
        "total_legs": total,
    }


def build_laycan_ui_advice(laycan: dict, remediation: dict) -> dict:
    """Status-specific laycan line for the operational advice panel."""
    status = laycan["risk"]
    if status == "SAFE":
        return {
            "laycan_status": status,
            "laycan_advice_label": "Laycan compliance",
            "laycan_advice_value": "Within window",
        }
    if status == "EARLY":
        days = laycan.get("days_early")
        if days is None:
            days = round(laycan.get("expected_miss_hours", 0) / 24, 1)
        return {
            "laycan_status": status,
            "laycan_advice_label": "Laycan buffer",
            "laycan_advice_value": f"{days} days",
        }
    return {
        "laycan_status": status,
        "laycan_advice_label": "Required speed for laycan",
        "laycan_advice_value": f"{remediation['estimated_speed_required_kn']} kn",
        "required_speed_kn": remediation["estimated_speed_required_kn"],
        "required_departure_before": remediation["required_departure_before"],
        "remediation_note": remediation.get("note"),
    }


def build_operational_advice(recommended: dict, charter_warning: dict | None = None) -> dict:
    s = recommended["summary"]
    lc = recommended["laycan"]
    remediation = build_laycan_remediation(recommended)
    advice = {
        "current_average_sog_kn": s["average_sog_kn"],
        "commanded_speed_kn": s["commanded_speed_kn"],
        "predicted_eta": lc.get("predicted_eta_display"),
        **build_laycan_ui_advice(lc, remediation),
        "remediation": remediation,
    }
    if charter_warning:
        advice["laycan_critical"] = True
    return advice


def calculate_sog(commanded_speed: float, speed_loss: float) -> float:
    """SOG = STW - weather loss"""
    return round(max(commanded_speed - speed_loss, 1.0), 2)


def fuel_consumption_mt_per_day(
    speed_kn: float,
    base_speed: float = BASE_SPEED_KN,
    base_fuel: float = BASE_FUEL_MT_PER_DAY,
) -> float:
    """Week 3: fuel = base_fuel * (speed / 12)^3"""
    if speed_kn <= 0:
        return base_fuel
    return round(base_fuel * (speed_kn / base_speed) ** 3, 2)


def assess_laycan_risk(
    predicted_eta_hours: float,
    laycan_start: str,
    laycan_end: str,
    departure_time: str | None = None,
) -> dict:
    """Laycan window check: SAFE (in window), EARLY (before open), HIGH RISK (missed)."""
    from datetime import datetime, timedelta

    fmt = "%Y-%m-%d"
    start = datetime.strptime(laycan_start, fmt)
    end = datetime.strptime(laycan_end, fmt).replace(hour=23, minute=59)
    dep = datetime.strptime(departure_time, fmt) if departure_time else datetime.now()
    eta = dep + timedelta(hours=predicted_eta_hours)
    voyage_days = round(predicted_eta_hours / 24, 1)

    days_early = None
    if start <= eta <= end:
        status: LaycanStatus = "SAFE"
        offset_hours = 0.0
        detail = "Arrival within laycan window"
    elif eta < start:
        status = "EARLY"
        offset_hours = round((start - eta).total_seconds() / 3600, 1)
        days_early = round(offset_hours / 24, 1)
        miss_days = 0
        detail = (
            f"ETA {eta.strftime('%d %b %Y')} is {days_early} days before laycan opens "
            f"({laycan_start}) — vessel may wait at anchorage"
        )
    else:
        status = "HIGH RISK"
        offset_hours = round((eta - end).total_seconds() / 3600, 1)
        detail = (
            f"ETA {eta.strftime('%d %b %Y')} misses laycan end ({laycan_end}) "
            f"by {round(offset_hours / 24, 1)} days"
        )

    if status == "HIGH RISK":
        miss_days = round(offset_hours / 24, 0)
    elif status != "EARLY":
        miss_days = 0

    return {
        "laycan_start": laycan_start,
        "laycan_end": laycan_end,
        "departure_time": departure_time,
        "predicted_eta": eta.isoformat(),
        "predicted_eta_display": eta.strftime("%d %b %Y"),
        "voyage_days": voyage_days,
        "risk": status,
        "expected_miss_hours": offset_hours,
        "miss_days": miss_days,
        "days_early": days_early if status == "EARLY" else None,
        "detail": detail,
    }


LAYCAN_BAD_MISS_DAYS = 7
LAYCAN_SCORE_PENALTY = 30
LAYCAN_SCORE_CAP = 70


def laycan_miss_days(laycan: dict) -> float:
    if laycan.get("risk") != "HIGH RISK":
        return 0.0
    if "miss_days" in laycan:
        return float(laycan["miss_days"])
    return round(laycan.get("expected_miss_hours", 0) / 24, 0)


def is_laycan_badly_missed(laycan: dict) -> bool:
    return laycan.get("risk") == "HIGH RISK" and laycan_miss_days(laycan) >= LAYCAN_BAD_MISS_DAYS


def apply_laycan_score_penalty(score: int, laycan: dict) -> int:
    """Penalize scores when charter window is missed badly (cap 70, -30 pts)."""
    if is_laycan_badly_missed(laycan):
        return min(max(score - LAYCAN_SCORE_PENALTY, 0), LAYCAN_SCORE_CAP)
    if laycan.get("risk") == "HIGH RISK":
        return min(score - 10, 85)
    if laycan.get("risk") == "EARLY":
        return min(score - 5, 90)
    return score


def build_laycan_remediation(reference_route: dict) -> dict:
    """Estimate speed or departure change needed to hit laycan end from current plan."""
    from datetime import datetime, timedelta

    summary = reference_route["summary"]
    lc = reference_route["laycan"]
    distance = summary["total_distance_nm"]
    commanded = summary["commanded_speed_kn"] or BASE_SPEED_KN
    fmt = "%Y-%m-%d"
    dep = datetime.strptime(lc["departure_time"], fmt)
    end = datetime.strptime(lc["laycan_end"], fmt).replace(hour=23, minute=59)

    hours_available = max((end - dep).total_seconds() / 3600, 1)
    required_sog = distance / hours_available
    ideal_hours = distance / commanded
    required_dep = end - timedelta(hours=ideal_hours)

    note = None
    if required_sog > 25:
        note = "Required speed exceeds 25 kn — earlier departure is the realistic fix"
    elif required_sog > commanded * 1.5:
        note = "Significant speed-up or earlier departure needed vs current plan"

    return {
        "estimated_speed_required_kn": round(required_sog, 1),
        "required_departure_before": required_dep.strftime("%d %b %Y"),
        "current_commanded_speed_kn": commanded,
        "reference_distance_nm": round(distance, 0),
        "note": note,
    }


def build_charter_laycan_warning(route_a: dict, route_b: dict) -> dict | None:
    lc_a, lc_b = route_a["laycan"], route_b["laycan"]
    miss_a, miss_b = laycan_miss_days(lc_a), laycan_miss_days(lc_b)
    bad_a, bad_b = is_laycan_badly_missed(lc_a), is_laycan_badly_missed(lc_b)

    if not (bad_a and bad_b):
        return None

    avg_miss = round((miss_a + miss_b) / 2)
    ref_route = (
        route_a
        if route_a["summary"]["total_distance_nm"] <= route_b["summary"]["total_distance_nm"]
        else route_b
    )
    remediation = build_laycan_remediation(ref_route)

    return {
        "severity": "critical",
        "title": "WARNING: Charter laycan not achievable on either route",
        "message": (
            f"Both routes miss the laycan window by approximately {avg_miss} days "
            f"(Route A: {int(miss_a)}d, Route B: {int(miss_b)}d). "
            "Speed increase or departure adjustment required before sailing."
        ),
        "route_a_miss_days": int(miss_a),
        "route_b_miss_days": int(miss_b),
        "remediation": remediation,
        "actions": [
            f"Increase speed to ~{remediation['estimated_speed_required_kn']} kn (vs {remediation['current_commanded_speed_kn']} kn commanded)",
            f"Depart before {remediation['required_departure_before']}",
            "Renegotiate laycan window with charterer",
        ],
    }


def risk_metric(analysis: dict) -> float:
    """0 = all LOW, 1 = all HIGH (for recommendation score)."""
    legs = analysis.get("legs", [])
    if not legs:
        return 0.0
    total = 0.0
    for leg in legs:
        if leg["risk"] == "HIGH":
            total += 1.0
        elif leg["risk"] == "MEDIUM":
            total += 0.5
    return total / len(legs)


def laycan_metric(analysis: dict) -> float:
    status = analysis["laycan"]["risk"]
    if status == "SAFE":
        return 0.0
    if status == "EARLY":
        return 0.25
    return 1.0


def normalize_pair(value: float, other: float) -> float:
    lo, hi = min(value, other), max(value, other)
    if hi == lo:
        return 0.0
    return (value - lo) / (hi - lo)


def weighted_route_score(
    cost: float,
    delay: float,
    risk: float,
    laycan: float,
    other: dict,
) -> float:
    """Week 3: lower score is better."""
    return (
        0.4 * normalize_pair(cost, other["cost"])
        + 0.3 * normalize_pair(delay, other["delay"])
        + 0.2 * normalize_pair(risk, other["risk"])
        + 0.1 * normalize_pair(laycan, other["laycan"])
    )


def build_recommendation_reasons(winner: dict, loser: dict) -> list[str]:
    reasons = []
    w, l = winner["summary"], loser["summary"]
    if w["total_fuel_cost_usd"] < l["total_fuel_cost_usd"]:
        reasons.append("Lower cost")
    if risk_metric(winner) < risk_metric(loser):
        reasons.append("Lower risk")
    if winner["laycan"]["risk"] == "SAFE" and loser["laycan"]["risk"] != "SAFE":
        reasons.append("Laycan safe")
    if w["weather_delay_hours"] < l["weather_delay_hours"]:
        reasons.append("Less weather delay")
    if w["total_voyage_days"] < l["total_voyage_days"]:
        reasons.append("Faster ETA")
    return reasons or ["Best overall weighted score"]


def _composite_quality(metrics: dict, other: dict) -> float:
    """0–1 composite; higher is better vs the other route."""

    def component_score(value: float, other_value: float) -> float:
        hi, lo = max(value, other_value), min(value, other_value)
        if hi == lo:
            return 1.0
        return 1.0 - (value - lo) / (hi - lo)

    return (
        0.4 * component_score(metrics["cost"], other["cost"])
        + 0.3 * component_score(metrics["delay"], other["delay"])
        + 0.2 * component_score(metrics["risk"], other["risk"])
        + 0.1 * component_score(metrics["laycan"], other["laycan"])
    )


def route_quality_score_100(metrics: dict, other: dict) -> int:
    """Legacy 0–100 score (relative comparison)."""
    return round(100 * _composite_quality(metrics, other))


def route_display_scores(
    metrics_a: dict,
    metrics_b: dict,
    route_a: dict | None = None,
    route_b: dict | None = None,
) -> tuple[int, int]:
    """
    Display scores from weighted route comparison (62-90 scale), then laycan
    penalties (-30 pts, max 70) when charter window is badly missed.
    """
    comp_a = _composite_quality(metrics_a, metrics_b)
    comp_b = _composite_quality(metrics_b, metrics_a)
    lo, hi = min(comp_a, comp_b), max(comp_a, comp_b)

    def map_score(composite: float) -> int:
        if hi == lo:
            return 75
        return round(62 + 28 * (composite - lo) / (hi - lo))

    score_a, score_b = map_score(comp_a), map_score(comp_b)

    if route_a and route_b:
        score_a = apply_laycan_score_penalty(score_a, route_a["laycan"])
        score_b = apply_laycan_score_penalty(score_b, route_b["laycan"])

    return score_a, score_b


def build_weather_impact_summary(analysis: dict) -> dict:
    """Route-specific weather cost vs ideal baseline (commanded speed, no weather loss)."""
    legs = analysis.get("legs", [])
    summary = analysis["summary"]
    commanded = summary["commanded_speed_kn"]
    bunker_price = summary.get("bunker_price_usd_per_mt", 600)

    ideal_fuel = 0.0
    high_risk_legs = 0
    max_wave = 0.0

    for leg in legs:
        ideal_hours = leg["distance_nm"] / commanded if commanded else 0
        ideal_fuel += fuel_consumption_mt_per_day(commanded) * (ideal_hours / 24)
        if leg["risk"] == "HIGH":
            high_risk_legs += 1
        wave = leg["weather"].get("wave", leg["weather"].get("wave_height", 0))
        max_wave = max(max_wave, float(wave))

    actual_fuel = sum(leg["fuel_mt"] for leg in legs)
    fuel_penalty = round(max(actual_fuel - ideal_fuel, summary.get("extra_fuel_mt", 0)), 1)
    fuel_cost_penalty = round(fuel_penalty * bunker_price, 0)
    delay_hours = summary["weather_delay_hours"]
    voyage_hours = summary["total_voyage_hours"] or 1
    hourly_voyage_cost = summary["total_fuel_cost_usd"] / voyage_hours
    delay_cost_usd = round(delay_hours * hourly_voyage_cost, 0)

    return {
        "route_label": analysis["route"]["name"],
        "average_speed_loss_kn": round(commanded - summary["average_sog_kn"], 2),
        "total_weather_delay_hours": delay_hours,
        "high_risk_weather_delay_hours": summary.get("high_risk_weather_delay_hours", 0),
        "high_risk_leg_count": high_risk_legs,
        "weather_severity_average": analysis.get("weather_severity", 0),
        "weather_severity_peak": analysis.get("weather_severity_peak", 0),
        "max_wave_height_m": round(max_wave, 2),
        "weather_fuel_penalty_mt": fuel_penalty,
        "weather_fuel_cost_penalty_usd": fuel_cost_penalty,
        "weather_delay_cost_usd": delay_cost_usd,
        "laycan_status": analysis["laycan"]["risk"],
        "baseline_note": "Compared to ideal baseline (commanded speed, no weather speed loss)",
    }


def build_business_impact(analysis: dict) -> dict:
    """Kept for internal savings math; UI uses build_weather_impact_summary."""
    s = analysis["summary"]
    stw = s["commanded_speed_kn"]
    avg_sog = s["average_sog_kn"]
    return {
        "average_speed_loss_kn": round(stw - avg_sog, 2),
        "total_weather_delay_hours": s["weather_delay_hours"],
        "extra_fuel_mt": round(s.get("extra_fuel_mt", 0), 1),
        "extra_fuel_cost_usd": round(s.get("extra_fuel_cost_usd", 0), 0),
        "laycan_status": analysis["laycan"]["risk"],
    }


def build_high_risk_zones(legs: list, commanded_speed: float) -> list[dict]:
    zones = []
    for leg in legs:
        if leg["risk"] != "HIGH":
            continue
        ideal_hours = leg["distance_nm"] / commanded_speed if commanded_speed else 0
        leg_delay = max(leg["leg_hours"] - ideal_hours, 0)
        w = leg["weather"]
        zones.append({
            "waypoint": leg["to"],
            "wave_height_m": w.get("wave", w.get("wave_height")),
            "wind_speed_kn": w.get("wind", w.get("wind_speed")),
            "expected_speed_loss_kn": leg["speed_loss_kn"],
            "expected_delay_hours": round(leg_delay, 1),
            "risk_level": leg["risk"],
        })
    return zones


def score_component_points(value: float, other_value: float, weight: int) -> int:
    hi, lo = max(value, other_value), min(value, other_value)
    if hi == lo:
        return weight
    return round(weight * (1.0 - (value - lo) / (hi - lo)))


def build_score_breakdown(
    winner_metrics: dict,
    loser_metrics: dict,
    charter_warning: dict | None = None,
) -> dict:
    """Explain how the recommended route scores vs the alternative (signed point deltas)."""
    dimensions = [
        ("cost", 40, "Fuel / cost"),
        ("delay", 30, "Weather delay"),
        ("risk", 20, "Weather risk"),
        ("laycan", 10, "Laycan"),
    ]
    components = []
    for key, weight, label in dimensions:
        if key == "laycan" and charter_warning:
            components.append({
                "dimension": "laycan",
                "label": "Laycan failed on both routes",
                "points": -LAYCAN_SCORE_PENALTY,
                "winner_points": 0,
                "loser_points": 0,
                "max_points": weight,
                "detail": (
                    f"Penalty applied equally (-{LAYCAN_SCORE_PENALTY} pts each, "
                    f"max score {LAYCAN_SCORE_CAP})"
                ),
                "penalty_applied_each": True,
            })
            continue

        winner_pts = score_component_points(winner_metrics[key], loser_metrics[key], weight)
        loser_pts = score_component_points(loser_metrics[key], winner_metrics[key], weight)
        delta = winner_pts - loser_pts
        if delta > 0:
            short = {
                "cost": "Cost advantage",
                "delay": "Delay reduction",
                "risk": "Risk reduction",
                "laycan": "Laycan advantage",
            }[key]
            entry_label = short
        elif delta < 0:
            short = {
                "cost": "Fuel penalty",
                "delay": "Delay penalty",
                "risk": "Risk penalty",
                "laycan": "Laycan penalty",
            }[key]
            entry_label = short
        elif key == "laycan" and winner_metrics[key] == loser_metrics[key] == 1.0:
            entry_label = "Laycan failed on both routes"
            delta = -LAYCAN_SCORE_PENALTY
        else:
            entry_label = f"{label} (neutral)"
        components.append({
            "dimension": key,
            "label": entry_label,
            "points": delta,
            "winner_points": winner_pts,
            "loser_points": loser_pts,
            "max_points": weight,
            "detail": label,
        })

    return {
        "weights": {"cost": 0.4, "delay": 0.3, "risk": 0.2, "laycan": 0.1},
        "components": components,
        "net_points": sum(
            c["points"] for c in components if not c.get("penalty_applied_each")
        ),
    }


def _high_risk_leg_count(analysis: dict) -> int:
    return sum(1 for leg in analysis.get("legs", []) if leg["risk"] == "HIGH")


def _high_risk_counts_route_a_b(winner: dict, loser: dict) -> tuple[int, int]:
    high_a, high_b = 0, 0
    for analysis in (winner, loser):
        count = _high_risk_leg_count(analysis)
        if analysis["route"]["id"] == "rotterdam-singapore":
            high_a = count
        else:
            high_b = count
    return high_a, high_b


def build_recommendation_detail(
    winner: dict,
    loser: dict,
    winner_label: str,
    charter_warning: dict | None = None,
) -> dict:
    w_sum, l_sum = winner["summary"], loser["summary"]
    benefits = []
    tradeoffs = []
    secondary = []

    w_risk = risk_metric(winner)
    l_risk = risk_metric(loser)
    w_high = _high_risk_leg_count(winner)
    l_high = _high_risk_leg_count(loser)
    delay_save_total = round(l_sum["weather_delay_hours"] - w_sum["weather_delay_hours"], 1)
    delay_save_high_risk = round(
        l_sum.get("high_risk_weather_delay_hours", 0) - w_sum.get("high_risk_weather_delay_hours", 0),
        1,
    )
    delay_save = delay_save_high_risk if delay_save_high_risk >= 0.5 else delay_save_total
    fuel_diff = round(w_sum["total_fuel_mt"] - l_sum["total_fuel_mt"], 0)
    cost_diff = round(w_sum["total_fuel_cost_usd"] - l_sum["total_fuel_cost_usd"], 0)

    high_a, high_b = _high_risk_counts_route_a_b(winner, loser)

    if "alt" in winner["route"]["id"] or "avoidance" in winner["route"]["name"].lower():
        benefits.append("Avoids high-risk weather corridor (monsoon detour)")

    recommendation_reasons = []
    if "alt" in winner["route"]["id"] or "avoidance" in winner["route"]["name"].lower():
        recommendation_reasons.append("Avoids Bay of Bengal Monsoon Corridor")
    if l_high > w_high:
        recommendation_reasons.append(f"High-risk legs reduced from {l_high} to {w_high}")
    if delay_save_high_risk >= 0.5:
        recommendation_reasons.append(
            f"Reduces high-risk weather delay by {delay_save_high_risk} hrs"
        )
    elif delay_save_total >= 0.5:
        recommendation_reasons.append(f"Reduces total weather delay by {delay_save_total} hrs")

    recommendation_tradeoffs = []
    if fuel_diff > 0:
        recommendation_tradeoffs.append(f"+{fuel_diff:.0f} MT Fuel")
    if cost_diff > 0:
        recommendation_tradeoffs.append(f"+${cost_diff:,.0f} Cost")

    benefits.append(f"High-risk legs: Route A = {high_a}, Route B = {high_b}")
    if l_high > w_high and l_high > 0:
        pct = round(100 * (l_high - w_high) / l_high)
        benefits.append(f"High-risk exposure reduced by {pct}% on {winner_label}")
    elif w_high == 0 and l_high > 0:
        benefits.append("High-risk exposure reduced by 100% on recommended route")
    elif w_risk < l_risk:
        benefits.append(
            f"Lower weather-risk index ({round(w_risk * 100)}% vs {round(l_risk * 100)}% leg exposure)"
        )

    if winner["laycan"]["risk"] == "SAFE" and loser["laycan"]["risk"] != "SAFE":
        benefits.append("Maintains laycan compliance")
    elif winner["laycan"]["risk"] == "EARLY" and loser["laycan"]["risk"] == "HIGH RISK":
        benefits.append("Better laycan outcome vs missing window")

    voyage_days_diff = round(w_sum["total_voyage_days"] - l_sum["total_voyage_days"], 1)
    timing_note = None
    delay_for_timing = delay_save_high_risk if delay_save_high_risk >= 0.5 else delay_save_total
    if delay_for_timing > 0 and voyage_days_diff > 0:
        delay_label = (
            "high-risk weather-delay"
            if delay_save_high_risk >= 0.5
            else "net weather-delay"
        )
        timing_note = (
            f"{winner_label} saves {delay_for_timing} hr on {delay_label} legs but travels "
            f"a longer distance (+{voyage_days_diff} days overall voyage)."
        )
    elif delay_save_high_risk >= 2:
        secondary.append(f"High-risk weather delay reduced by {delay_save_high_risk} hr")
    elif delay_save_total > 0 and delay_save_high_risk >= 0.5 and not timing_note:
        secondary.append(
            f"High-risk leg delay down {delay_save_high_risk} hr; total route delay differs by "
            f"{delay_save_total} hr (detour distance adds baseline voyage time)"
        )
    elif delay_save > 0 and not timing_note:
        secondary.append(f"Minor delay improvement: {delay_save} hr (not the main driver)")

    if w_sum["total_fuel_cost_usd"] < l_sum["total_fuel_cost_usd"]:
        savings = l_sum["total_fuel_cost_usd"] - w_sum["total_fuel_cost_usd"]
        benefits.append(f"Lower fuel cost (saves ${savings:,.0f})")

    if cost_diff > 0:
        tradeoffs.append(
            "Accepted tradeoff: higher cost for materially safer operations"
        )

    if not benefits:
        benefits.append("Best overall weighted score (cost, delay, risk, laycan)")

    winner_metrics = {
        "cost": w_sum["total_fuel_cost_usd"],
        "delay": w_sum["weather_delay_hours"],
        "risk": w_risk,
        "laycan": laycan_metric(winner),
    }
    loser_metrics = {
        "cost": l_sum["total_fuel_cost_usd"],
        "delay": l_sum["weather_delay_hours"],
        "risk": l_risk,
        "laycan": laycan_metric(loser),
    }

    safety_rationale = None
    if w_high < l_high or w_risk < l_risk:
        safety_rationale = (
            "Safety is prioritized over minimum cost in this recommendation "
            "(fewer high-risk legs and lower weather-risk index outweigh additional fuel spend)."
        )
    if cost_diff > 0 and (w_risk < l_risk or w_high < l_high):
        safety_rationale = (
            "Recommended because weather risk reduction is weighted above fuel cost "
            f"(+${cost_diff:,.0f} accepted for materially safer operations)."
        )

    if charter_warning:
        summary = (
            f"{winner_label} recommended for voyage safety (best option, but neither route "
            "meets laycan — operational changes required)"
        )
    elif cost_diff > 0 and (w_risk < l_risk or w_high < l_high):
        summary = (
            f"{winner_label} recommended — safety prioritized over cost"
            + (f" (+${cost_diff:,.0f} fuel vs alternative)" if cost_diff > 0 else "")
        )
    else:
        summary = f"{winner_label} is recommended based on weighted voyage score"

    return {
        "route_label": winner_label,
        "route_name": winner["route"]["name"],
        "benefits": benefits,
        "secondary_benefits": secondary,
        "tradeoffs": tradeoffs,
        "summary": summary,
        "timing_note": timing_note,
        "charter_warning": charter_warning,
        "high_risk_legs": {"route_a": high_a, "route_b": high_b},
        "delay_comparison": {
            "total_hours_saved": delay_save_total,
            "high_risk_hours_saved": delay_save_high_risk,
            "winner_total_delay_hours": w_sum["weather_delay_hours"],
            "loser_total_delay_hours": l_sum["weather_delay_hours"],
            "winner_high_risk_delay_hours": w_sum.get("high_risk_weather_delay_hours", 0),
            "loser_high_risk_delay_hours": l_sum.get("high_risk_weather_delay_hours", 0),
        },
        "recommendation_card": {
            "reasons": recommendation_reasons,
            "tradeoffs": recommendation_tradeoffs,
        },
        "primary_driver": "operational_safety",
        "safety_rationale": safety_rationale,
        "score_breakdown": build_score_breakdown(
            winner_metrics, loser_metrics, charter_warning=charter_warning
        ),
    }

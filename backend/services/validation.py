"""Request validation for voyage API inputs."""
from datetime import datetime


def _parse_date(value: str, field: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be YYYY-MM-DD") from exc


def validate_voyage_inputs(
    departure_time: str,
    laycan_start: str,
    laycan_end: str,
) -> list[str]:
    """Return human-readable warnings; raises ValueError on hard failures."""
    dep = _parse_date(departure_time, "departure_time")
    start = _parse_date(laycan_start, "laycan_start")
    end = _parse_date(laycan_end, "laycan_end")

    if end < start:
        raise ValueError("Laycan end must be on or after laycan start")
    if start < dep:
        raise ValueError(
            f"Laycan start ({laycan_start}) cannot be before departure ({departure_time})"
        )

    warnings: list[str] = []
    if (end - dep).days > 120:
        warnings.append("Laycan window is more than 120 days after departure — check dates")
    return warnings

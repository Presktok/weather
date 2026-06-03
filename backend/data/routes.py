"""Predefined voyage routes and waypoints."""

# Shared segment: Mediterranean → Suez → Red Sea (stays over water on map)
_MEDITERRANEAN_SUEZ_RED_SEA = [
    {"name": "WP6 - Central Mediterranean", "lat": 35.0, "lon": 15.0},
    {"name": "WP6A - Crete Passage", "lat": 35.0, "lon": 24.0},
    {"name": "WP6B - Eastern Mediterranean", "lat": 33.5, "lon": 29.0},
    {"name": "WP7 - Suez Approach", "lat": 31.5, "lon": 32.0},
    {"name": "WP7A - Gulf of Suez", "lat": 28.0, "lon": 33.0},
    {"name": "WP7B - Red Sea Entrance", "lat": 24.0, "lon": 35.0},
    {"name": "WP8 - Red Sea North", "lat": 22.0, "lon": 38.5},
]

_ATLANTIC_TO_GIBRALTAR = [
    {"name": "WP1 - North Sea", "lat": 52.5, "lon": 3.0},
    {"name": "WP2 - English Channel", "lat": 49.5, "lon": -2.0},
    {"name": "WP3 - Bay of Biscay", "lat": 44.0, "lon": -5.0},
    {"name": "WP4 - Off Portugal", "lat": 38.0, "lon": -10.0},
    {"name": "WP5 - Strait of Gibraltar", "lat": 36.0, "lon": -5.5},
]

ROTTERDAM_SINGAPORE = {
    "id": "rotterdam-singapore",
    "name": "Rotterdam → Singapore",
    "departure": {"name": "Rotterdam", "lat": 51.9225, "lon": 4.4792},
    "destination": {"name": "Singapore", "lat": 1.3521, "lon": 103.8198},
    "waypoints": [
        *_ATLANTIC_TO_GIBRALTAR,
        *_MEDITERRANEAN_SUEZ_RED_SEA,
        {"name": "WP9 - Bab el-Mandeb", "lat": 12.5, "lon": 43.5},
        {"name": "WP10 - Arabian Sea", "lat": 15.0, "lon": 62.0},
        {"name": "WP11 - Off India West", "lat": 12.0, "lon": 72.0},
        {"name": "WP12 - Bay of Bengal", "lat": 10.0, "lon": 82.0},
        {"name": "WP13 - Monsoon Zone", "lat": 8.0, "lon": 88.0},
        {"name": "WP14 - Andaman Sea", "lat": 7.0, "lon": 94.0},
        {"name": "WP15 - Malacca Approach", "lat": 4.0, "lon": 99.0},
        {"name": "WP16 - Singapore Approach", "lat": 2.0, "lon": 102.0},
    ],
}

# Alternative route: detour south of monsoon zone
ROTTERDAM_SINGAPORE_ALT = {
    "id": "rotterdam-singapore-alt",
    "name": "Rotterdam → Singapore (Weather Avoidance)",
    "departure": {"name": "Rotterdam", "lat": 51.9225, "lon": 4.4792},
    "destination": {"name": "Singapore", "lat": 1.3521, "lon": 103.8198},
    "waypoints": [
        *_ATLANTIC_TO_GIBRALTAR,
        *_MEDITERRANEAN_SUEZ_RED_SEA,
        {"name": "WP9 - Bab el-Mandeb", "lat": 12.5, "lon": 43.5},
        {"name": "WP10 - Arabian Sea", "lat": 15.0, "lon": 62.0},
        {"name": "WP11 - Off India West", "lat": 8.0, "lon": 72.0},
        {"name": "WP12 - South of Sri Lanka", "lat": 4.0, "lon": 78.0},
        {"name": "WP13 - Equatorial Detour", "lat": 4.0, "lon": 85.0},
        {"name": "WP14 - South Indian Ocean", "lat": 4.0, "lon": 92.0},
        {"name": "WP15 - Malacca South", "lat": 2.5, "lon": 98.0},
        {"name": "WP16 - Singapore Approach", "lat": 2.0, "lon": 102.0},
    ],
}

ROUTES = {
    "rotterdam-singapore": ROTTERDAM_SINGAPORE,
    "rotterdam-singapore-alt": ROTTERDAM_SINGAPORE_ALT,
}

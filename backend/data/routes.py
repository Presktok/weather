"""Predefined voyage routes and waypoints."""

# Western Med → Suez Canal → Red Sea (dense points for map / leg geometry)
_MEDITERRANEAN_TO_RED_SEA = [
    {"name": "WP5A - Western Mediterranean", "lat": 37.0, "lon": 5.0},
    {"name": "WP5B - Central Mediterranean", "lat": 35.5, "lon": 15.0},
    {"name": "WP5C - Eastern Mediterranean", "lat": 33.5, "lon": 28.0},
    {"name": "WP7 - Port Said", "lat": 31.26, "lon": 32.30},
    {"name": "WP7A - Suez Canal North", "lat": 30.70, "lon": 32.35},
    {"name": "WP7B - Great Bitter Lake", "lat": 30.30, "lon": 32.40},
    {"name": "WP7C - Gulf of Suez", "lat": 29.60, "lon": 32.55},
    {"name": "WP8 - Red Sea North", "lat": 27.50, "lon": 34.80},
]

_ATLANTIC_TO_GIBRALTAR = [
    {"name": "WP1 - North Sea", "lat": 52.5, "lon": 3.0},
    {"name": "WP2 - English Channel", "lat": 49.5, "lon": -2.0},
    {"name": "WP3 - Bay of Biscay", "lat": 44.0, "lon": -5.0},
    {"name": "WP4 - Off Portugal", "lat": 38.0, "lon": -10.0},
    {"name": "WP5 - Strait of Gibraltar", "lat": 36.0, "lon": -5.5},
]

# Malacca → Singapore (stays in strait water, avoids Malaysia landmass on map)
_MALACCA_TO_SINGAPORE = [
    {"name": "WP15 - Malacca Strait", "lat": 5.0, "lon": 99.5},
    {"name": "WP16 - South Malacca", "lat": 3.0, "lon": 101.0},
    {"name": "WP17 - Singapore Approach", "lat": 2.0, "lon": 102.0},
]

_MALACCA_TO_SINGAPORE_SOUTH = [
    {"name": "WP15 - Malacca Approach", "lat": 3.0, "lon": 97.5},
    {"name": "WP16 - Malacca Strait", "lat": 5.0, "lon": 99.5},
    {"name": "WP17 - South Malacca", "lat": 3.0, "lon": 101.0},
    {"name": "WP18 - Singapore Approach", "lat": 2.0, "lon": 102.0},
]

_INDIAN_OCEAN_MAIN = [
    {"name": "WP9 - Bab el-Mandeb", "lat": 12.5, "lon": 43.5},
    {"name": "WP10 - Arabian Sea", "lat": 15.0, "lon": 62.0},
    {"name": "WP11 - Off India West", "lat": 11.0, "lon": 69.0},
    {"name": "WP11A - Off Kerala", "lat": 9.0, "lon": 75.0},
    {"name": "WP12 - Bay of Bengal", "lat": 10.0, "lon": 82.0},
    {"name": "WP13 - Monsoon Zone", "lat": 8.0, "lon": 88.0},
    {"name": "WP14 - Andaman Sea", "lat": 7.0, "lon": 94.0},
    *_MALACCA_TO_SINGAPORE,
]

_INDIAN_OCEAN_AVOIDANCE = [
    {"name": "WP9 - Bab el-Mandeb", "lat": 12.5, "lon": 43.5},
    {"name": "WP10 - Arabian Sea", "lat": 15.0, "lon": 62.0},
    {"name": "WP11 - Off SW India", "lat": 10.0, "lon": 67.0},
    {"name": "WP11A - South of India", "lat": 7.0, "lon": 74.0},
    {"name": "WP12 - South of Sri Lanka", "lat": 5.0, "lon": 79.0},
    {"name": "WP13 - Equatorial Indian Ocean", "lat": 2.5, "lon": 86.0},
    {"name": "WP14 - South of Sumatra", "lat": 0.0, "lon": 92.5},
    *_MALACCA_TO_SINGAPORE_SOUTH,
]

ROTTERDAM_SINGAPORE = {
    "id": "rotterdam-singapore",
    "name": "Rotterdam → Singapore",
    "departure": {"name": "Rotterdam", "lat": 51.9225, "lon": 4.4792},
    "destination": {"name": "Singapore", "lat": 1.3521, "lon": 103.8198},
    "waypoints": [
        *_ATLANTIC_TO_GIBRALTAR,
        *_MEDITERRANEAN_TO_RED_SEA,
        *_INDIAN_OCEAN_MAIN,
    ],
}

ROTTERDAM_SINGAPORE_ALT = {
    "id": "rotterdam-singapore-alt",
    "name": "Rotterdam → Singapore (Weather Avoidance)",
    "departure": {"name": "Rotterdam", "lat": 51.9225, "lon": 4.4792},
    "destination": {"name": "Singapore", "lat": 1.3521, "lon": 103.8198},
    "waypoints": [
        *_ATLANTIC_TO_GIBRALTAR,
        *_MEDITERRANEAN_TO_RED_SEA,
        *_INDIAN_OCEAN_AVOIDANCE,
    ],
}

ROUTES = {
    "rotterdam-singapore": ROTTERDAM_SINGAPORE,
    "rotterdam-singapore-alt": ROTTERDAM_SINGAPORE_ALT,
}

# ⚓ Voyage Optimizer
### Smart Weather Voyage Optimization

> **Turn live ocean weather into actionable voyage decisions** — compare routes, quantify fuel and delay, protect laycan compliance, and recommend the safest operational path.

| | |
|---|---|
| 🌊 **Weather Risk** | Leg-level LOW / MEDIUM / HIGH from wind & wave |
| ⛽ **Fuel Cost** | Speed–fuel cube law with bunker pricing |
| ⏱️ **ETA** | Weather-adjusted SOG per leg |
| 📅 **Laycan** | SAFE · EARLY · HIGH RISK with status-specific advice |
| 🗺️ **Route Comparison** | Route A (shortest) vs Route B (weather avoidance) |

**[Live Demo](https://weather-kohl-seven.vercel.app)** · **[Repository](https://github.com/Presktok/weather)**

---

## Problem Statement

Maritime operators plan voyages using static distances and assumed speeds. In reality, **weather changes everything**.

| Challenge | Impact |
|-----------|--------|
| **Traditional planning** | Great-circle or fixed waypoints ignore waves, wind, and seasonal monsoon corridors |
| **Weather exposure** | High sea states reduce speed-over-ground (SOG), inflate voyage time, and increase fuel burn |
| **Laycan windows** | Charter contracts require arrival within a date range — missing laycan triggers penalties and disputes |
| **Route trade-offs** | The shortest path is not always the safest or most economical when weather is severe |

Without integrated weather intelligence, teams rely on spreadsheets and intuition. **Voyage Optimizer** closes that gap by binding meteorology, hydrodynamics-style speed loss, fuel physics, and laycan logic into one decision surface.

---

## Solution

**Voyage Optimizer** is a weather-aware voyage comparison platform for long-haul shipping (demo: **Rotterdam → Singapore**).

It:

1. **Ingests weather** at every waypoint (Open-Meteo marine + forecast APIs, with seasonal monsoon modelling in the Indian Ocean).
2. **Classifies operational risk** per leg and visualizes routes on an interactive map.
3. **Computes voyage economics** — fuel, delay, ETA, and laycan status for each route.
4. **Recommends a route** using a transparent weighted score (cost, delay, risk, laycan), with **safety-first** explanations when the detour costs more but reduces high-risk exposure.

Operators move from *“Which line looks shorter?”* to *“Which voyage is safer, cheaper, and laycan-compliant under today’s ocean conditions?”*

---

## Key Features

| Feature | Description |
|---------|-------------|
| 🗺️ **Interactive route visualization** | Route A vs Route B on Leaflet; risk-colored legs; focus & overlay modes |
| 🌦️ **Weather-aware routing** | Wind and wave per waypoint; seasonal monsoon sensitivity by departure date |
| ⏱️ **ETA prediction** | Cumulative leg hours with weather-adjusted SOG |
| 📋 **Laycan risk assessment** | SAFE, EARLY, or HIGH RISK with buffer days or required-speed remediation |
| ⛽ **Fuel consumption estimation** | Cubic speed–fuel relationship summed per leg |
| ⏳ **Weather delay calculation** | Total and high-risk-leg delay vs ideal commanded-speed baseline |
| ⚖️ **Route comparison** | Side-by-side metrics table (distance, fuel, cost, severity, laycan) |
| 🎯 **Recommendation engine** | Weighted scoring + plain-language reasons and tradeoffs |

---

## Innovation

What sets Voyage Optimizer apart from generic map or weather apps:

| Differentiator | Detail |
|----------------|--------|
| **Business-native output** | Not just a weather map — fuel USD, laycan status, and charter-style warnings |
| **Dual-route narrative** | Explicit shortest vs avoidance story (monsoon detour) judges and operators understand immediately |
| **Seasonal intelligence** | Monsoon corridor severity scales with **departure month** (Jun–Sep peak), not static fake storms year-round |
| **Status-aware laycan UX** | Shows buffer when early, compliance when safe, required speed **only** when at risk |
| **Transparent scoring** | Published weights and score drivers — no black-box “AI pick” |
| **Representative sea corridors** | Dense waypoints + great-circle display curves keep polylines offshore for credible demos |

---

## System Architecture

```
                              ┌─────────────────────────┐
                              │         User            │
                              │   (Browser / Demo)      │
                              └───────────┬─────────────┘
                                          │
                                          ▼
                    ┌─────────────────────────────────────────┐
                    │     React + Leaflet Frontend            │
                    │  Map · Dashboard · Voyage Parameters    │
                    └─────────────────────┬───────────────────┘
                                          │  REST /api
                                          ▼
                    ┌─────────────────────────────────────────┐
                    │           FastAPI Backend               │
                    │  ┌─────────────┐  ┌──────────────────┐  │
                    │  │   Weather   │  │   Risk Engine    │  │
                    │  │   Service   │  │  (wave + wind)   │  │
                    │  └──────┬──────┘  └────────┬─────────┘  │
                    │         │    ┌─────────────┴─────────┐  │
                    │         │    │  Speed · Fuel · ETA   │  │
                    │         │    │  Laycan Analyzer      │  │
                    │         │    │  Recommendation Engine│  │
                    │         │    └───────────────────────┘  │
                    └─────────┼────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
     ┌──────────────┐  ┌─────────────┐  ┌──────────────┐
     │ Open-Meteo   │  │  Route Data │  │   Vercel /   │
     │ Marine +     │  │  (Waypoints)│  │   Local API  │
     │ Forecast API │  │             │  │   Host       │
     └──────────────┘  └─────────────┘  └──────────────┘
```

---

## Workflow

End-to-end analysis pipeline for each voyage comparison:

```
 ① Route Selection          Rotterdam → Singapore (Route A & B waypoints)
        │
        ▼
 ② Weather Collection       Open-Meteo per waypoint + seasonal monsoon model
        │
        ▼
 ③ Risk Assessment           LOW / MEDIUM / HIGH per leg
        │
        ▼
 ④ Speed Loss Calculation    wave & wind → SOG reduction
        │
        ▼
 ⑤ ETA Prediction            Σ (distance / SOG) → arrival date
        │
        ▼
 ⑥ Fuel Estimation           cubic fuel law × leg duration
        │
        ▼
 ⑦ Laycan Check              SAFE · EARLY · HIGH RISK
        │
        ▼
 ⑧ Route Recommendation      Weighted score + safety narrative
```

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, Vite, Tailwind CSS, Leaflet / React-Leaflet |
| **Backend** | Python 3, FastAPI, Pydantic, httpx |
| **Weather data** | [Open-Meteo](https://open-meteo.com/) Marine & Forecast APIs |
| **Deployment** | Vercel (Services: Vite frontend + FastAPI at `/api`) |
| **Optional static host** | GitHub Pages (`/docs`) + Render for API |

---

## Project Structure

```
weather/
├── backend/
│   ├── main.py                 # FastAPI routes
│   ├── data/routes.py          # Route A & B waypoints
│   ├── services/
│   │   ├── weather.py          # Open-Meteo + monsoon model
│   │   ├── voyage.py           # Voyage analysis & compare
│   │   ├── calculations.py     # Risk, fuel, laycan, scoring
│   │   └── validation.py       # Input validation
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── VoyageMap.jsx
│   │   │   └── Dashboard.jsx
│   │   └── utils/routeGeometry.js
│   └── package.json
├── api/index.py                # Vercel serverless entry
├── vercel.json
├── render.yaml                 # Optional API on Render
└── README.md
```

---

## Installation and Local Setup

### Prerequisites

- Python **3.11+**
- Node.js **18+**

### 1. Clone the repository

```bash
git clone https://github.com/Presktok/weather.git
cd weather
```

### 2. Backend

```bash
cd backend
python -m venv venv
```

**Windows:**
```powershell
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**macOS / Linux:**
```bash
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API available at `http://localhost:8000/api`

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** (proxies `/api` → port 8000).

### Optional environment

| Variable | Purpose |
|----------|---------|
| `USE_DEMO_WEATHER=true` | Force demo monsoon model (offline / consistent demos) |

---

## Deploy on Vercel

1. Import repo at [vercel.com/new](https://vercel.com/new)
2. **Preset:** Services · **Root:** repository root
3. Confirm `vercel.json`: `frontend` → `/`, `backend` → `/api`
4. Deploy

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/` | Health check |
| `GET` | `/api/routes` | List available routes |
| `GET` | `/api/route/{route_id}` | Route geometry & waypoints |
| `POST` | `/api/voyage/analyze` | Single-route analysis |
| `POST` | `/api/voyage/compare` | **Route A vs B + recommendation** |
| `GET` | `/api/demo/rotterdam-singapore` | Default comparison demo |

### Compare request example

```json
{
  "commanded_speed": 12,
  "departure_time": "2026-08-22",
  "laycan_start": "2026-09-19",
  "laycan_end": "2026-09-20",
  "bunker_price": 600
}
```

| Field | Rules |
|-------|-------|
| `commanded_speed` | **6–18 kn** (operational demo range) |
| `departure_time` | `YYYY-MM-DD` |
| `laycan_start` | ≥ `departure_time` |
| `laycan_end` | ≥ `laycan_start` |

---

## Models and Formulas

### Weather risk model

```
HIGH    if  wave_height > 4 m  OR  wind_speed > 25 kn
MEDIUM  if  wave_height > 2 m  OR  wind_speed > 15 kn
LOW     otherwise
```

### Speed loss model

```
speed_loss_kn = wave_height × 0.20 + wind_speed × 0.01
SOG_kn        = max(commanded_speed − speed_loss_kn, 1.0)
```

### ETA model

```
leg_hours      = distance_nm / SOG_kn
voyage_hours   = Σ leg_hours
weather_delay  = voyage_hours − Σ (distance_nm / commanded_speed)
```

### Fuel model

```
fuel_mt_per_day = 32 × (SOG_kn / 12)³
leg_fuel_mt     = fuel_mt_per_day × (leg_hours / 24)
total_cost_usd  = total_fuel_mt × bunker_price_per_mt
```

### Laycan model

| Status | Condition |
|--------|-----------|
| **SAFE** | Predicted ETA within `[laycan_start, laycan_end]` |
| **EARLY** | ETA before laycan opens → buffer days shown |
| **HIGH RISK** | ETA after laycan end → required speed & remediation |

### Recommendation scoring

Lower weighted score wins:

```
score = 0.40 × cost + 0.30 × delay + 0.20 × risk + 0.10 × laycan
```

Display scores (0–100) are **relative between Route A and B** for the same inputs — higher means better *within that comparison*, not an absolute industry grade.

---

## Example Results

*Sample output: departure **22 Aug 2026**, laycan **19–20 Sep 2026**, commanded speed **12 kn**, bunker **$600/MT**, monsoon season.*

### Route A — Main (shortest)

| Metric | Value |
|--------|-------|
| Distance | ~8,300 nm |
| Voyage time | ~14.8 days |
| Fuel | ~420 MT |
| Fuel cost | ~$252,000 |
| Weather delay | ~9 hrs |
| High-risk legs | **3–4** (Bay of Bengal / monsoon corridor) |
| Laycan | Often **HIGH RISK** or tight |

### Route B — Weather avoidance (detour)

| Metric | Value |
|--------|-------|
| Distance | ~8,500 nm (+extra nm) |
| Voyage time | ~15.0 days |
| Fuel | ~475 MT |
| Fuel cost | ~$285,000 |
| Weather delay | ~8 hrs (less on high-risk legs) |
| High-risk legs | **0–1** (southern Indian Ocean arc) |
| Laycan | Improved vs Route A in severe monsoon |

### Recommendation (typical monsoon departure)

> **Route B recommended — safety prioritized over cost** (+~$30,000 fuel vs Route A)

**Reasons:**

- Avoids Bay of Bengal monsoon corridor  
- High-risk legs reduced from **4 → 1**  
- High-risk weather delay reduced by **~3–5 hours**  

**Tradeoff:** Additional fuel and ~0.2 days longer voyage accepted for materially safer operations.

---

## Business Impact

| Stakeholder | Benefit |
|-------------|---------|
| **Ship operators** | Earlier visibility into SOG loss and delay before committing to a route |
| **Chartering teams** | Laycan buffer / compliance / remediation messaging aligned to contract risk |
| **Shipping companies** | Quantified cost–risk tradeoff between shortest and avoidance routes |

Decisions shift from reactive weather routing to **proactive, data-backed voyage selection**.

---

## Sustainability Impact

- **Fuel optimization** — Identifying weather delay and speed loss reduces unnecessary steaming at inefficient SOG.
- **Route efficiency** — Comparing detour vs shortest path with full fuel accounting avoids “false savings” from ignoring weather.
- **Future CO₂ modelling** — Fuel MT totals can be converted to emissions factors (e.g. tCO₂/MT fuel) for ESG reporting and carbon-aware routing.

---

## Future Scope

| Enhancement | Description |
|-------------|-------------|
| 🛰️ **AIS integration** | Real vessel positions and historical tracks |
| 📊 **Historical weather** | Climatology and hindcast datasets for route planning |
| 🌊 **Ocean current modelling** | Current-assisted SOG and net weather resistance |
| 🌱 **Carbon optimization** | Explicit CO₂ / CII objectives in scoring |
| 🤖 **Machine learning** | Learned risk and fuel models from voyage outcomes |
| 🗺️ **Multi-port planning** | Network routing beyond single origin–destination pairs |

---

## Hackathon Value Proposition

| Question | Answer |
|----------|--------|
| **What problem is solved?** | Operators cannot easily see how **live weather** turns into **fuel, delay, laycan risk, and route choice**. |
| **Why does it matter?** | Weather drives millions in fuel and charter exposure; wrong routes increase risk and contractual penalties. |
| **What innovation is demonstrated?** | End-to-end pipeline from **Open-Meteo** → **per-leg risk** → **economics** → **explainable recommendation** in one polished web product. |

Built to be demo-ready in minutes: run analysis, toggle routes on the map, and read a recommendation card that judges and industry users understand without reading code.

---

## Map Disclaimer

**Route geometry** shown on the map is a **representative sea corridor** for voyage comparison and demonstration. Waypoints are placed to keep display paths offshore; geometry is **not intended for navigation** and does not replace official charting or professional passage planning.

---

## License

This project is provided for **demonstration, hackathon, and educational use**.

You may fork and extend it with attribution. No warranty is provided for operational maritime navigation decisions.

---

<p align="center">
  <strong>Voyage Optimizer</strong> — Weather intelligence for smarter shipping decisions
</p>

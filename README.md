# Voyage Optimizer

Weather-aware voyage planning for long-distance shipping. Compare two route options (shortest vs weather-avoidance), assess risk along each leg, estimate fuel and delay, and check laycan compliance.

**Live demo:** Deploy via [Vercel](#deploy-on-vercel) (frontend + API).  
**Example route:** Rotterdam → Singapore (Route A main path, Route B monsoon detour).

---

## Features

- **Interactive map** — Route A and Route B with risk-colored segments (LOW / MEDIUM / HIGH), toggle visibility, and focus per route
- **Live weather** — Wind and wave at each waypoint ([Open-Meteo](https://open-meteo.com/)); seasonal monsoon model in the Indian Ocean corridor based on departure date
- **Voyage metrics** — Distance, ETA, fuel consumption, weather delay, and laycan status (SAFE / EARLY / HIGH RISK)
- **Route comparison** — Side-by-side metrics and a weighted recommendation (cost, delay, risk, laycan)
- **Operational advice** — Context-specific laycan messaging (buffer when early, required speed only when at risk)

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, Vite, Tailwind CSS, Leaflet |
| Backend | Python 3, FastAPI, httpx |
| Deploy | Vercel (Services preset) or local dev with Uvicorn |

---

## Project structure

```
weather/
├── backend/           # FastAPI app, voyage logic, weather, calculations
│   ├── data/routes.py # Waypoints for Route A & B
│   └── services/
├── frontend/          # React UI
├── api/               # Vercel serverless entry (re-exports FastAPI app)
├── docs/              # Static build for GitHub Pages (optional)
└── vercel.json        # Vercel deployment config
```

---

## Run locally

### Prerequisites

- Python 3.11+
- Node.js 18+

### Backend

```bash
cd backend
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**macOS / Linux:**
```bash
source venv/bin/activate
```

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API base: `http://localhost:8000/api`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — the dev server proxies `/api` to port 8000.

### Optional: demo weather only

```bash
set USE_DEMO_WEATHER=true   # Windows
export USE_DEMO_WEATHER=true  # macOS / Linux
```

---

## Deploy on Vercel

1. Import this repository at [vercel.com/new](https://vercel.com/new).
2. **Application Preset:** Services (frontend + FastAPI).
3. **Root directory:** repository root (`.`).
4. Confirm `vercel.json`:
   - `frontend` → `/`
   - `backend` → `/api`
5. Deploy.

The app uses `/api` on the same domain for voyage analysis.

**CLI:**
```bash
npm i -g vercel
vercel
vercel --prod
```

### GitHub Pages (frontend only)

Settings → Pages → branch `main` → folder `/docs` → `https://<user>.github.io/weather/`

Requires a separate API host (e.g. [Render](https://render.com/deploy?repo=https://github.com/Presktok/weather) via `render.yaml`).

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/route/{route_id}` | Route geometry and waypoints |
| `GET` | `/api/routes` | List available routes |
| `POST` | `/api/voyage/analyze` | Analyze a single route |
| `POST` | `/api/voyage/compare` | Compare Route A vs Route B + recommendation |
| `GET` | `/api/demo/rotterdam-singapore` | Quick compare with default parameters |

### Compare request body

```json
{
  "commanded_speed": 12,
  "departure_time": "2026-08-22",
  "laycan_start": "2026-09-19",
  "laycan_end": "2026-09-20",
  "bunker_price": 600
}
```

| Field | Constraints |
|-------|-------------|
| `commanded_speed` | 6–18 kn |
| `departure_time` | ISO date `YYYY-MM-DD` |
| `laycan_start` | Must be ≥ `departure_time` |
| `laycan_end` | Must be ≥ `laycan_start` |

---

## Models and formulas

### Weather risk (per leg)

```
HIGH    if wave > 4 m OR wind > 25 kn
MEDIUM  if wave > 2 m OR wind > 15 kn
LOW     otherwise
```

### Speed and delay

```
speed_loss = wave × 0.20 + wind × 0.01
SOG = commanded_speed − speed_loss
leg_hours = distance_nm / SOG
weather_delay = actual voyage hours − ideal hours at commanded speed
```

### Fuel

```
fuel_mt_per_day = 32 × (SOG / 12)³
leg_fuel = fuel_mt_per_day × (leg_hours / 24)
```

### Route recommendation score

Weighted comparison (lower raw score = better): **40% cost · 30% delay · 20% risk · 10% laycan**

Display scores (0–100) are **relative between Route A and Route B** for the same voyage inputs, not an absolute grade.

### Monsoon season (Indian Ocean demo corridor)

| Departure month | Effect |
|-----------------|--------|
| Jun–Sep | Peak monsoon conditions |
| May, Oct | Transition |
| Oct–May | Typically lower |

---

## Map note

Routes use dense sea waypoints and great-circle interpolation for display. Geometry is a **representative corridor for comparison**, not for navigation.

---

## License

This project is provided as-is for demonstration and educational use.

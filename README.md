# Voyage Optimizer — MVP Build Guide

Build in this order. Do not skip ahead to later weeks until the current week works.

## Week 1 — Core Demo (Map + Weather + Risk)

| Step | Goal | Status |
|------|------|--------|
| 1. Map | Rotterdam → Singapore route, waypoints, polyline | `GET /api/route/rotterdam-singapore` |
| 2. Weather | Wind + wave at each waypoint (Open-Meteo) | `POST /api/voyage/analyze` |
| 3. Risk | LOW / MEDIUM / HIGH colored segments on map | wave/wind thresholds below |

**Risk rules (backend):**
```
if wave > 4 or wind > 25 kn:  HIGH
elif wave > 2 or wind > 18 kn: MEDIUM
else:                         LOW
```

**Map colors:** Green = Low · Yellow = Medium · Red = High

---

## Week 2 — Business Logic

| Step | Goal | Formula |
|------|------|---------|
| 4. Speed loss | Weather affects SOG | `speed_loss = wave * 0.20 + wind * 0.01`, `SOG = 12 - speed_loss` |
| 5. ETA | Per leg + total | `hours = distance_nm / SOG` |
| 6. Laycan | SAFE or HIGH RISK | Compare predicted ETA to laycan window |

---

## Week 3 — What Judges Care About

| Step | Goal | Formula |
|------|------|---------|
| 7. Fuel | Bunker cost | `fuel = 32 * (speed/12)³` per day, summed per leg |
| 8. Compare | Route A vs Route B table | `POST /api/voyage/compare` |
| 9. Recommend | Weighted score (lower wins) | `0.4×cost + 0.3×delay + 0.2×risk + 0.1×laycan` |

---

## Run locally

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

---

## Deploy on Vercel (recommended)

Full stack: React frontend + FastAPI API on one Vercel project.

### Deploy from GitHub

1. Go to [vercel.com/new](https://vercel.com/new) and sign in with GitHub.
2. Import **Presktok/weather**.
3. **Application Preset:** **Services** (Vercel detects frontend + backend).
4. **Root Directory:** `./` (repo root) — click **Refresh** if `vercel.json` was just updated.
5. Confirm [`vercel.json`](vercel.json) shows:
   - `frontend` → `/`
   - `backend` → `/api` (not `/_/backend`)
6. Click **Deploy**.

Your live URL will be like `https://weather-xxxx.vercel.app`. The app calls `/api` on the same domain.

### Optional: Vercel CLI

```bash
npm i -g vercel
cd weather
vercel
vercel --prod
```

### GitHub Pages (alternative)

Static-only hosting: **Settings → Pages → branch `main` → folder `/docs`** → https://presktok.github.io/weather/ (API must be hosted separately, e.g. Render).

---

## API (by week)

| Week | Endpoint | Purpose |
|------|----------|---------|
| 1 | `GET /api/route/{id}` | Route geometry only |
| 1–2 | `POST /api/voyage/analyze` | Single route + weather + ETA + laycan |
| 3 | `POST /api/voyage/compare` | Route A vs B + recommendation |

---

## Hackathon demo script

1. Map loads with **risk-colored route segments**
2. Click waypoint → see **wind, wave, SOG**
3. Dashboard shows **ETA**, **fuel cost**, **laycan SAFE / HIGH RISK**
4. Comparison table: **Route A vs Route B**
5. **Recommended Route** card with reasons (Lower cost, Lower risk, Laycan safe)

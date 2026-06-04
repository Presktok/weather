import os

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from data.routes import ROUTES
from services.validation import validate_voyage_inputs
from services.voyage import analyze_voyage, compare_routes, get_route_geometry

app = FastAPI(
    title="Smart Weather Voyage Optimization API",
    description="Weather-aware voyage optimization, ETA, laycan risk, and route comparison",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()


class VoyageRequest(BaseModel):
    route_id: str = "rotterdam-singapore"
    commanded_speed: float = Field(12.0, ge=6, le=18, description="Operational SOG range 6–18 kn")
    laycan_start: str = "2026-09-19"
    laycan_end: str = "2026-09-20"
    bunker_price: float = Field(600.0, ge=0)
    departure_time: str = "2026-08-22"


class CompareRequest(BaseModel):
    commanded_speed: float = Field(12.0, ge=6, le=18, description="Operational SOG range 6–18 kn")
    laycan_start: str = "2026-09-19"
    laycan_end: str = "2026-09-20"
    bunker_price: float = Field(600.0, ge=0)
    departure_time: str = "2026-08-22"


@app.get("/")
def root():
    return {"status": "ok", "service": "Voyage Optimization API"}


@router.get("/route/{route_id}")
def route_geometry(route_id: str):
    """Week 1: map route + waypoints only (no weather)."""
    if route_id not in ROUTES:
        raise HTTPException(status_code=404, detail="Route not found")
    return get_route_geometry(route_id)


@router.get("/routes")
def list_routes():
    return {
        rid: {
            "id": r["id"],
            "name": r["name"],
            "departure": r["departure"],
            "destination": r["destination"],
            "waypoint_count": len(r["waypoints"]),
        }
        for rid, r in ROUTES.items()
    }


@router.post("/voyage/analyze")
async def voyage_analyze(req: VoyageRequest):
    try:
        warnings = validate_voyage_inputs(
            req.departure_time, req.laycan_start, req.laycan_end
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result = await analyze_voyage(
        route_id=req.route_id,
        commanded_speed=req.commanded_speed,
        laycan_start=req.laycan_start,
        laycan_end=req.laycan_end,
        bunker_price=req.bunker_price,
        departure_time=req.departure_time,
    )
    result["input_warnings"] = warnings
    return result


@router.post("/voyage/compare")
async def voyage_compare(req: CompareRequest):
    try:
        warnings = validate_voyage_inputs(
            req.departure_time, req.laycan_start, req.laycan_end
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result = await compare_routes(
        laycan_start=req.laycan_start,
        laycan_end=req.laycan_end,
        commanded_speed=req.commanded_speed,
        bunker_price=req.bunker_price,
        departure_time=req.departure_time,
    )
    result["input_warnings"] = warnings
    return result


@router.get("/demo/rotterdam-singapore")
async def demo_voyage():
    """Quick demo endpoint for hackathon flow."""
    return await compare_routes()


# Vercel Services mounts this app at /api (routes omit the prefix). Local dev uses /api prefix.
if os.getenv("VERCEL"):
    app.include_router(router)
else:
    app.include_router(router, prefix="/api")

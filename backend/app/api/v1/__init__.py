"""API v1 router bundle for Hydra."""

from fastapi import APIRouter

from app.api.v1.admissions import router as admissions_router
from app.api.v1.data_sources import router as data_sources_router
from app.api.v1.franchises import router as franchises_router
from app.api.v1.health import router as health_router
from app.api.v1.interests import router as interests_router
from app.api.v1.oracle import router as oracle_router
from app.api.v1.planner import router as planner_router
from app.api.v1.programmes import router as programmes_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.referee import router as referee_router
from app.api.v1.simulation import router as simulation_router
from app.api.v1.twin import router as twin_router

api_v1_router = APIRouter()
api_v1_router.include_router(programmes_router)
api_v1_router.include_router(recommendations_router)
api_v1_router.include_router(data_sources_router)
api_v1_router.include_router(admissions_router)
api_v1_router.include_router(twin_router)
api_v1_router.include_router(franchises_router)
api_v1_router.include_router(planner_router)
api_v1_router.include_router(simulation_router)
api_v1_router.include_router(interests_router)
api_v1_router.include_router(oracle_router)
api_v1_router.include_router(referee_router)


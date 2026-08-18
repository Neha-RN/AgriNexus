from fastapi import APIRouter

from app.api.v1.countries import router as countries_router
from app.api.v1.fields import router as fields_router

router = APIRouter()

router.include_router(countries_router)
router.include_router(fields_router)
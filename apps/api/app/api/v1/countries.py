from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.country import CountryRead
from app.services.country_service import list_countries

router = APIRouter(
    prefix="/countries",
    tags=["countries"],
)


@router.get("", response_model=list[CountryRead])
def get_countries(
    db: Session = Depends(get_db),
) -> list[CountryRead]:
    return list_countries(db)
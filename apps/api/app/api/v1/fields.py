from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.field import FieldRead
from app.services.field_service import list_fields

router = APIRouter(
    prefix="/fields",
    tags=["fields"],
)


@router.get("", response_model=list[FieldRead])
def get_fields(
    db: Session = Depends(get_db),
) -> list[FieldRead]:
    return list_fields(db)
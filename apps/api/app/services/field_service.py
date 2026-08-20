from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.field import Field


def list_fields(db: Session) -> list[Field]:
    statement = select(Field).order_by(Field.id)
    return list(db.scalars(statement).all())

def get_field(db: Session, field_id: int) -> Field | None:
    return db.query(Field).filter(Field.id == field_id).first()

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.country import Country


def list_countries(db: Session) -> list[Country]:
    statement = select(Country).order_by(Country.name)
    return list(db.scalars(statement).all())
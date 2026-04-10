from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from auth import require_role
from models import User, Country

class CountryIn(BaseModel):
    id:      str
    name_ja: str
    lat:     float
    lng:     float

router = APIRouter(prefix="/api", tags=["trade"])

@router.post("/countries")
def add_country(
    body:         CountryIn,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_role("admin")),
):
    existing = db.query(Country).filter(Country.id == body.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="すでに登録済みのIDです")
    country = Country(**body.model_dump())
    db.add(country)
    db.commit()
    return country

@router.delete("/countries/{country_id}")
def delete_country(
    country_id:   str,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_role("admin")),
):
    country = db.query(Country).filter(Country.id == country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="国が見つかりません")
    db.delete(country)
    db.commit()
    return {"message": f"{country_id} を削除しました"}

@router.get("/trade-links")
def get_trade_links(
    category: str = None,
    year:     int  = 2023,
    db:       Session = Depends(get_db)
):
    query = """
        SELECT from_country AS "from", to_country AS "to",
               value, category, year
        FROM trade_links
        WHERE year = :year
    """
    params = {"year": year}
    if category:
        query += " AND category = :category"
        params["category"] = category

    rows = db.execute(text(query), params)
    return [dict(row._mapping) for row in rows]

@router.get("/countries")
def get_countries(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT id, name_ja, lat, lng FROM countries"))
    return [dict(row._mapping) for row in rows]
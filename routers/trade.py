from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

router = APIRouter(prefix="/api", tags=["trade"])

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
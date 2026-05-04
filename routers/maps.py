from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from auth import require_role
from models import User, Country

class CountryIn(BaseModel):
    iso_id:   str
    name:     str
    name_ja:  str
    lat:      float
    lng:      float

router = APIRouter(prefix="/api", tags=["trade"])

@router.post("/countries")
def add_country(
    body:         CountryIn,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_role("admin")),
):
    existing = db.query(Country).filter(Country.iso_id == body.iso_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="すでに登録済みのIDです")
    country = Country(
        iso_id=body.iso_id,
        name=body.name,
        name_ja=body.name_ja,
        lat=body.lat,
        lng=body.lng
    )
    db.add(country)
    db.commit()
    db.refresh(country)
    return {
        "iso_id": country.iso_id,
        "name": country.name,
        "name_ja": country.name_ja,
        "lat": float(country.lat),
        "lng": float(country.lng)
    }

@router.delete("/countries/{country_id}")
def delete_country(
    country_id:   str,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_role("admin")),
):
    country = db.query(Country).filter(Country.iso_id == country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="国が見つかりません")
    db.delete(country)
    db.commit()
    return {"message": f"{country_id} を削除しました"}

@router.get("/countries")
def get_countries(db: Session = Depends(get_db)):
    """全国を取得する"""
    countries = db.query(Country).all()
    return [
        {
            "iso_id": c.iso_id,
            "name": c.name,
            "name_ja": c.name_ja,
            "lat": float(c.lat),
            "lng": float(c.lng)
        }
        for c in countries
    ]
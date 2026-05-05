from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from auth import require_role
from models import Point, User, Country
from routers import points
from routers.points import PointIn

class CountryIn(BaseModel):
    iso_id:   str
    name:     str
    name_ja:  str
    lat:      float
    lng:      float
    exist_from : datetime
    exist_until : datetime


router = APIRouter(prefix="/api", tags=["countries"])

@router.post("/countries")
def add_country(
    body:         CountryIn,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_role("admin")),
):
    existing = db.query(Country).filter(Country.iso_id == body.iso_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="すでに登録済みのIDです")
    point = points.add_point(PointIn(name=body.name, name_ja=body.name_ja, lat=body.lat, lng=body.lng), db, current_user)
    country = Country(
        iso_id=body.iso_id,
        name=body.name,
        name_ja=body.name_ja,
        capital_point_id=point.id,
        exist_from=body.exist_from,
        exist_until=body.exist_until
    )
    db.add(country)
    db.commit()
    db.refresh(country)
    return {
        "iso_id": country.iso_id,
        "name": country.name,
        "name_ja": country.name_ja,
        "capital_point_id": country.capital_point_id,
        "exist_from": country.exist_from.isoformat() if country.exist_from else None,
        "exist_until": country.exist_until.isoformat() if country.exist_until else None
    }

@router.put("/countries/{country_id}")
def update_country(
    country_id:   str,
    body:         CountryIn,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_role("admin")),
):
    country = db.query(Country).filter(Country.iso_id == country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="国が見つかりません")
    
    # 首都ポイントの更新
    points.update_point_name(country.capital_point_id, body.name, body.name_ja, db, current_user)
    points.update_point_coordinates(country.capital_point_id, body.lat, body.lng, db, current_user)    
    # 国の情報を更新
    country.name = body.name
    country.name_ja = body.name_ja
    country.exist_from = body.exist_from
    country.exist_until = body.exist_until
    
    db.add(country)
    db.commit()
    db.refresh(country)
    
    return {
        "iso_id": country.iso_id,
        "name": country.name,
        "name_ja": country.name_ja,
        "capital_point_id": country.capital_point_id,
        "exist_from": country.exist_from.isoformat() if country.exist_from else None,
        "exist_until": country.exist_until.isoformat() if country.exist_until else None
    }

@router.patch("/countries/{country_id}/summary")
def update_summary(
    country_id:   str,
    summary:      str,
    summary_jp:   str,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_role("admin")),
):
    country = db.query(Country).filter(Country.iso_id == country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="国が見つかりません")
    
    # 要約情報を更新
    country.summary = summary
    country.summary_jp = summary_jp

    db.add(country)
    db.commit()
    db.refresh(country)

    return {
        "iso_id": country.iso_id,
        "name": country.name,
        "name_ja": country.name_ja,
        "capital_point_id": country.capital_point_id,
        "exist_from": country.exist_from.isoformat() if country.exist_from else None,
        "exist_until": country.exist_until.isoformat() if country.exist_until else None,
        "summary": country.summary,
        "summary_jp": country.summary_jp
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
    points.delete_point(country.capital_point_id, db, current_user)
    db.delete(country)
    db.commit()
    return {"message": f"{country.name} を削除しました"}

@router.get("/countries/{country_id}/coordinates")
def get_coordinates(
    country_id: str,
    db: Session = Depends(get_db)
):
    country = db.query(Country).filter(Country.iso_id == country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="国が見つかりません")
    point = db.query(Point).filter(Point.id == country.capital_point_id).first()
    if not point:
        raise HTTPException(status_code=404, detail="首都の座標が見つかりません")
    return {
        "lat": point.lat,
        "lng": point.lng
    }

@router.get("/countries/{country_id}")
def get_country(
    country_id: str,
    db: Session = Depends(get_db)
):
    country = db.query(Country).filter(Country.iso_id == country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="国が見つかりません")
    return {
        "iso_id": country.iso_id,
        "name": country.name,
        "name_ja": country.name_ja,
        "capital_point_id": country.capital_point_id,
        "exist_from": country.exist_from.isoformat() if country.exist_from else None,
        "exist_until": country.exist_until.isoformat() if country.exist_until else None,
        "summary": country.summary,
        "summary_jp": country.summary_jp
    }

@router.get("/countries")
def get_countries(db: Session = Depends(get_db)):
    """すべての国を取得する"""
    countries = db.query(Country).all()
    return [
        {
            "iso_id": c.iso_id,
            "name": c.name,
            "name_ja": c.name_ja,
            "capital_point_id": c.capital_point_id,
            "exist_from": c.exist_from.isoformat() if c.exist_from else None,
            "exist_until": c.exist_until.isoformat() if c.exist_until else None,
            "summary": c.summary,
            "summary_jp": c.summary_jp
        }
        for c in countries
    ]
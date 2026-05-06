from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import require_role
from database import get_db
from models import Point, User


class PointIn(BaseModel):
    name: str
    name_ja: str
    lat: float
    lng: float


#abstract class points
def add_point(
    body: PointIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("editor")),
):
    point = Point(
        name=body.name,
        name_ja=body.name_ja,
        lat=body.lat,
        lng=body.lng,
    )
    
    db.add(point)
    db.commit()
    db.refresh(point)
    return {
        "id": point.id,
        "name": point.name,
        "name_ja": point.name_ja,
        "lat": float(point.lat),
        "lng": float(point.lng),
    }


def update_name(
    point_id: int,
    name: str,
    name_ja: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    point = db.query(Point).filter(Point.id == point_id).first()
    if not point:
        raise HTTPException(status_code=404, detail="地点が見つかりません")
    point.name = name
    point.name_ja = name_ja
    db.add(point)
    db.commit()
    db.refresh(point)
    return (
        {
            "id": point.id,
            "name": point.name,
            "name_ja": point.name_ja,
            "lat": float(point.lat),
            "lng": float(point.lng),
        }
    )


def update_coordinates(
    point_id: int,
    lat: float,
    lng: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    point = db.query(Point).filter(Point.id == point_id).first()
    if not point:
        raise HTTPException(status_code=404, detail="地点が見つかりません")
    point.lat = lat
    point.lng = lng
    db.add(point)
    db.commit()
    db.refresh(point)
    return (
        {
            "id": point.id,
            "name": point.name,
            "name_ja": point.name_ja,
            "lat": float(point.lat),
            "lng": float(point.lng),
        }
    )

def delete_point(
    point_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    point = db.query(Point).filter(Point.id == point_id).first()
    name = point.name if point else "不明な地点"
    if not point:
        raise HTTPException(status_code=404, detail="地点が見つかりません")
    db.delete(point)
    db.commit()
    return {"message": f"{name}を削除しました"}


def get_point(point_id: int, db: Session = Depends(get_db)):
    point = db.query(Point).filter(Point.id == point_id).first()
    if not point:
        raise HTTPException(status_code=404, detail="地点が見つかりません")
    return {
        "id": point.id,
        "name": point.name,
        "name_ja": point.name_ja,
        "lat": float(point.lat),
        "lng": float(point.lng),
    }


from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import require_role
from database import get_db
from models import MapPoint, Point, User


class PointIn(BaseModel):
    id: Optional[int] = None
    name: str
    name_ja: str
    lat: float
    lng: float


router = APIRouter(prefix="/api", tags=["points"])


@router.patch("/maps/{map_id}/map_points/{map_point_id}")
def update_map_point(
    map_id: int,
    map_point_id: int,
    color: str,
    db: Session = Depends(get_db)
):
    map_point = db.query(MapPoint).filter(MapPoint.map_id == map_id, MapPoint.id == map_point_id).first()
    if not map_point:
        raise HTTPException(status_code=404, detail="地点が見つかりません")
    map_point.color = color
    db.commit()
    db.refresh(map_point)
    return {
        "id": map_point.id,
        "map_id": map_point.map_id,
        "point_id": map_point.point_id,
        "color": map_point.color,
    }


@router.get("/maps/{map_id}/map_points")
def get_map_points(
    map_id: int,
    db: Session = Depends(get_db)
):
    map_points = db.query(MapPoint).filter(MapPoint.map_id == map_id).all()
    return [
        {
            "id": mp.id,
            "map_id": mp.map_id,
            "point_id": mp.point_id,
            "color": mp.color,
        }
        for mp in map_points
    ]


@router.post("/points")
def add_point(
    body: PointIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    if body.id is not None:
        existing = db.query(Point).filter(Point.id == body.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="すでに登録済みの地点IDです")

    point = Point(
        name=body.name,
        name_ja=body.name_ja,
        lat=body.lat,
        lng=body.lng,
    )
    if body.id is not None:
        point.id = body.id

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


@router.patch("/points/{point_id}")
def update_point_name(
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
    return True


@router.patch("/points/{point_id}")
def update_point_coordinates(
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
    return True


@router.delete("/points/{point_id}")
def delete_point(
    point_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    point = db.query(Point).filter(Point.id == point_id).first()
    if not point:
        raise HTTPException(status_code=404, detail="地点が見つかりません")
    db.delete(point)
    db.commit()
    return {"message": f"{point_id} を削除しました"}


@router.get("/points/{point_id}")
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


@router.get("/points")
def get_points(db: Session = Depends(get_db)):
    points = db.query(Point).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "name_ja": p.name_ja,
            "lat": float(p.lat),
            "lng": float(p.lng),
        }
        for p in points
    ]
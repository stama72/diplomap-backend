from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import require_role
from database import get_db
from models import Map, MapPoint, Point, User
from routers import maps, points
from routers.points import PointIn

router = APIRouter(prefix="/api", tags=["points"])

@router.post("/maps/{map_id}/map_points")
def add_map_point(
    map_id: int,
    color: str,
    body: PointIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("editor"))
):
    is_map_editable = maps.can_edit_map(map_id, user, db)
    if not is_map_editable:
        raise HTTPException(status_code=403, detail="このマップを編集する権限がありません")
    point = points.add_point(body=body, db=db, current_user=user)
    map_point = MapPoint(
        map_id=map_id,
        point_id=point.id,
        color=color
    )
    db.add(map_point)
    db.commit()
    db.refresh(map_point)
    return {
        "id": map_point.id,
        "map_id": map_point.map_id,
        "point_id": map_point.point_id,
        "color": map_point.color,
    }

@router.patch("/maps/{map_id}/map_points/{map_point_id}/color")
def update_color(
    map_id: int,
    map_point_id: int,
    color: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("editor"))
):
    is_map_editable = maps.can_edit_map(map_id, user, db)
    if not is_map_editable:
        raise HTTPException(status_code=403, detail="このマップを編集する権限がありません")
    map_point = db.query(MapPoint).filter(MapPoint.map_id == map_id, MapPoint.id == map_point_id).first()
    if not map_point:
        raise HTTPException(status_code=404, detail="地点が見つかりません")
    map_point.color = color

    db.add(map_point)
    db.commit()
    db.refresh(map_point)
    return {
        "id": map_point.id,
        "map_id": map_point.map_id,
        "point_id": map_point.point_id,
        "color": map_point.color,
    }

@router.patch("/maps/{map_id}/map_points/{map_point_id}/name")
def update_name(
    map_id: int,
    map_point_id: int,
    name: str,
    name_ja: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("editor"))
):
    is_map_editable = maps.can_edit_map(map_id, user, db)
    if not is_map_editable:
        raise HTTPException(status_code=403, detail="このマップを編集する権限がありません")
    map_point = db.query(MapPoint).filter(MapPoint.map_id == map_id, MapPoint.id == map_point_id).first()
    if not map_point:
        raise HTTPException(status_code=404, detail="地点が見つかりません")
    points.update_name(point_id=map_point.point_id, name=name, name_ja=name_ja, db=db, current_user=user)
    return {
        "id": map_point.id,
        "map_id": map_point.map_id,
        "point_id": map_point.point_id,
        "color": map_point.color,
    }

@router.patch("/maps/{map_id}/map_points/{map_point_id}/coordinates")
def update_coordinates(
    map_id: int,
    map_point_id: int,
    lat: float,
    lng: float,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("editor"))
):
    is_map_editable = maps.can_edit_map(map_id, user, db)
    if not is_map_editable:
        raise HTTPException(status_code=403, detail="このマップを編集する権限がありません")
    map_point = db.query(MapPoint).filter(MapPoint.map_id == map_id, MapPoint.id == map_point_id).first()
    if not map_point:
        raise HTTPException(status_code=404, detail="地点が見つかりません")
    points.update_coordinates(point_id=map_point.point_id, lat=lat, lng=lng, db=db, current_user=user)
    return {
        "id": map_point.id,
        "map_id": map_point.map_id,
        "point_id": map_point.point_id,
        "color": map_point.color,
    }

@router.delete("/maps/{map_id}/map_points/{map_point_id}")
def delete_map_point(   
    map_id: int,
    map_point_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("editor"))
):
    map_point = db.query(MapPoint).filter(MapPoint.map_id == map_id, MapPoint.id == map_point_id).first()
    if not map_point:
        raise HTTPException(status_code=404, detail="地点が見つかりません")
    if not maps.can_edit_map(map_id, user, db):
        raise HTTPException(status_code=403, detail="このマップを編集する権限がありません")
    point = db.query(Point).filter(Point.id == map_point.point_id).first()
    name = point.name if point else "不明な地点" 
 
    points.delete_point(map_point.point_id, db, user)
    db.delete(map_point)
    db.commit()
    return {"message": f"マップ地点 {name} を削除しました"}


@router.get("/maps/{map_id}/map_points/{map_point_id}")
def get_map_point(
    map_id: int,
    map_point_id: int,
    db: Session = Depends(get_db)
):
    map_point = db.query(MapPoint).filter(MapPoint.map_id == map_id, MapPoint.id == map_point_id).first()
    if not map_point:
        raise HTTPException(status_code=404, detail="地点が見つかりません")
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
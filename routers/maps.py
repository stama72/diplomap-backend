from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user, require_role
from models import Link, LinkType, Map, MapPoint, Point, User, Country
from routers.points import PointIn, add_point


class MapIn(BaseModel):
    name: str
    name_ja: str
    owner_id: int
    read_permission: str
    edit_permission: str
    exist_from: datetime
    exist_until: datetime
    time_scale: str
    summary: str
    summary_jp: str
    regulations: str

class LinkTypeIn(BaseModel):
    name: str
    name_ja: str
    map_id: int
    color: str
    animated: bool


router = APIRouter(prefix="/api", tags=["maps"])


def can_edit_map(
    map_id: int,
    user: User,
    db: Session = Depends(get_db)
):
    map = db.query(Map).filter(Map.id == map_id).first()
    if not map:
        raise HTTPException(status_code=404, detail="マップが見つかりません")
    if map.edit_permission == "public":
        return True
    if map.edit_permission == "shared":
        #追加で招待リンクが正しいかの確認が必要
        return True
    if map.edit_permission == "private" and map.owner == user.id:
        return True
    return False


@router.get("/maps/{map_id}/editable")
def get_map_editable(
    map_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return {"editable": can_edit_map(map_id, current_user, db)}


@router.post("/maps")
def create_map(
    map: MapIn,
    db: Session = Depends(get_db)
):
    new_map = Map(
        name=map.name,
        name_ja=map.name_ja,
        owner=map.owner_id,
        read_permission=map.read_permission,
        edit_permission=map.edit_permission,
        exist_from=map.exist_from,
        exist_until=map.exist_until,
        time_scale=map.time_scale,
        summary=map.summary,
        summary_jp=map.summary_jp,
        regulations=map.regulations
    )
    db.add(new_map)
    db.commit()
    db.refresh(new_map)
    return {
        "id": new_map.id,
        "name": new_map.name,
        "name_ja": new_map.name_ja,
        "owner": new_map.owner,
        "read_permission": new_map.read_permission,
        "edit_permission": new_map.edit_permission,
        "exist_from": new_map.exist_from.isoformat(),
        "exist_until": new_map.exist_until.isoformat(),
        "time_scale": new_map.time_scale,
        "summary": new_map.summary,
        "summary_jp": new_map.summary_jp,
        "regulations": new_map.regulations
    }

@router.put("/maps/{map_id}")
def update_map(
    map_id: int,
    map_update: MapIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    map = db.query(Map).filter(Map.id == map_id).first()
    if not map:
        raise HTTPException(status_code=404, detail="マップが見つかりません")
    if not can_edit_map(map_id, current_user, db):
        raise HTTPException(status_code=403, detail="このマップを更新する権限がありません")
    for key, value in map_update.dict().items():
        setattr(map, key, value)
    db.commit()
    db.refresh(map)
    return {
        "id": map.id,
        "name": map.name,
        "name_ja": map.name_ja,
        "owner": map.owner,
        "read_permission": map.read_permission,
        "edit_permission": map.edit_permission,
        "exist_from": map.exist_from.isoformat(),
        "exist_until": map.exist_until.isoformat(),
        "time_scale": map.time_scale,
        "summary": map.summary,
        "summary_jp": map.summary_jp,
        "regulations": map.regulations
    }

@router.delete("/maps/{map_id}")
def delete_map(
    map_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    map = db.query(Map).filter(Map.id == map_id).first()
    if not map:
        raise HTTPException(status_code=404, detail="マップが見つかりません")
    if not can_edit_map(map_id, current_user, db):
        raise HTTPException(status_code=403, detail="このマップを削除する権限がありません")
    db.delete(map)
    db.commit()
    return {"detail": "マップが削除されました"}

@router.get("/maps/{map_id}")
def get_map(
    map_id: int,
    db: Session = Depends(get_db)
):
    map = db.query(Map).filter(Map.id == map_id).first()
    if not map:
        raise HTTPException(status_code=404, detail="マップが見つかりません")
    if map.read_permission == "private":
        raise HTTPException(status_code=403, detail="このマップを閲覧する権限がありません")
    if map.read_permission == "shared":
        #追加で招待リンクが正しいかの確認が必要
        pass
    if map.read_permission == "public":
        pass
    return {
        "id": map.id,
        "name": map.name,
        "name_ja": map.name_ja,
        "owner": map.owner,
        "read_permission": map.read_permission,
        "edit_permission": map.edit_permission,
        "exist_from": map.exist_from.isoformat(),
        "exist_until": map.exist_until.isoformat(),
        "time_scale": map.time_scale,
        "summary": map.summary,
        "summary_jp": map.summary_jp,
        "regulations": map.regulations
    }

@router.get("/maps")
def get_maps(
    db: Session = Depends(get_db)
):
    maps = db.query(Map).all()
    return [
        {
            "id": m.id,
            "name": m.name,
            "name_ja": m.name_ja,
            "owner": m.owner,
            "read_permission": m.read_permission,
            "edit_permission": m.edit_permission,
            "exist_from": m.exist_from.isoformat(),
            "exist_until": m.exist_until.isoformat(),
            "time_scale": m.time_scale,
            "summary": m.summary,
            "summary_jp": m.summary_jp,
            "regulations": m.regulations
        }
        for m in maps
    ]


@router.post("/maps/{map_id}/map_points")
def create_map_point(
    map_id: int,
    color: str,
    PointIn: PointIn,
    db: Session = Depends(get_db)
):
    point = add_point(
        body=PointIn,
        db=db
    )
    new_map_point = MapPoint(
        map_id=map_id,
        point_id=point["id"],
        color=color
    )
    db.add(new_map_point)
    db.commit()
    db.refresh(new_map_point)
    return {
        "id": new_map_point.id,
        "map_id": new_map_point.map_id,
        "point_id": new_map_point.point_id,
        "color": new_map_point.color
    }

@router.patch("/maps/{map_id}/map_points/{map_point_id}")
def update_map_point(
    map_id: int,
    map_point_id: int,
    color: str,
    db: Session = Depends(get_db)
):
    map_point = db.query(MapPoint).filter(MapPoint.id == map_point_id, MapPoint.map_id == map_id).first()
    if not map_point:
        raise HTTPException(status_code=404, detail="マップポイントが見つかりません")
    map_point.color = color
    db.commit()
    db.refresh(map_point)
    return {
        "id": map_point.id,
        "map_id": map_point.map_id,
        "point_id": map_point.point_id,
        "color": map_point.color
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
            "color": mp.color
        }
        for mp in map_points
    ]


@router.post("/link_types")
def create_link_type(
    link_type: LinkTypeIn,
    db: Session = Depends(get_db)
):
    new_link_type = LinkType(
        name=link_type.name,
        name_ja=link_type.name_ja,
        map_id=link_type.map_id,
        color=link_type.color,
        animated=link_type.animated
    )
    db.add(new_link_type)
    db.commit()
    db.refresh(new_link_type)
    return {
        "id": new_link_type.id,
        "name": new_link_type.name,
        "name_ja": new_link_type.name_ja,
        "map_id": new_link_type.map_id,
        "color": new_link_type.color,
        "animated": new_link_type.animated
    }

@router.put("/link_types")
def update_link_type(
    link_type_id: int,
    map_id: int,
    link_type: LinkTypeIn,
    db: Session = Depends(get_db)
):
    existing = db.query(LinkType).filter(
        LinkType.id == link_type_id,
        LinkType.map_id == map_id
    ).first()
    if not existing:
        raise HTTPException(status_code=404, detail="リンクタイプが見つかりません")
    existing.color = link_type.color
    existing.animated = link_type.animated
    existing.name = link_type.name
    existing.name_ja = link_type.name_ja
    db.commit()
    db.refresh(existing)
    return {
        "id": existing.id,
        "name": existing.name,
        "name_ja": existing.name_ja,
        "map_id": existing.map_id,
        "color": existing.color,
        "animated": existing.animated
    }


@router.delete("/link_types")
def delete_link_type(
    link_type_id: int,
    map_id: int,
    db: Session = Depends(get_db)
):
    existing = db.query(LinkType).filter(
        LinkType.id == link_type_id,
        LinkType.map_id == map_id
    ).first()
    if not existing:
        raise HTTPException(status_code=404, detail="リンクタイプが見つかりません")
    db.delete(existing)
    db.commit()
    return {"detail": "リンクタイプが削除されました"}

@router.get("/link_types")
def get_link_types(
    map_id: int,
    db: Session = Depends(get_db)
):
    link_types = db.query(LinkType).filter(LinkType.map_id == map_id).all()
    return [
        {
            "id": lt.id,
            "name": lt.name,
            "name_ja": lt.name_ja,
            "map_id": lt.map_id,
            "color": lt.color,
            "animated": lt.animated
        }
        for lt in link_types
    ]



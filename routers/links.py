from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
from models import Link, User
from routers import maps

router = APIRouter(prefix="/api", tags=["links"])

class LinkIn(BaseModel):
    map_id: int
    link_type: int
    from_country: int
    to_country: int
    exist_from: datetime
    exist_until: datetime

class LinkDetailsIn(BaseModel):
    link_id: int
    summary: str
    summary_ja: str
    source_url: str

@router.post("/links")
def create_link(
    link: LinkIn,
    db: Session = Depends(get_db)
):
    new_link = Link(
        from_country=link.from_country,
        to_country=link.to_country,
        link_type=link.link_type,
        exist_from=link.exist_from,
        exist_until=link.exist_until,
        map_id=link.map_id
    )
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return {
        "id": new_link.id,
        "from_country": new_link.from_country,
        "to_country": new_link.to_country,
        "link_type": new_link.link_type,
        "exist_from": new_link.exist_from.isoformat(),
        "exist_until": new_link.exist_until.isoformat(),
        "map_id": new_link.map_id
    }

@router.put("/links/{link_id}")
def update_link(
    link_id: int,
    link_update: LinkIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    link = db.query(Link).filter(Link.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="リンクが見つかりません")
    if not maps.can_edit_map(link.map_id, user, db):
        raise HTTPException(status_code=403, detail="このリンクを更新する権限がありません")
    for key, value in link_update.model_dump().items():
        setattr(link, key, value)
    db.commit()
    db.refresh(link)
    return {
        "id": link.id,
        "from_country": link.from_country,
        "to_country": link.to_country,
        "link_type": link.link_type,
        "exist_from": link.exist_from.isoformat(),
        "exist_until": link.exist_until.isoformat(),
        "map_id": link.map_id
    }

@router.delete("/links/{link_id}")
def delete_link(
    link_id: int,
    db: Session = Depends(get_db)
):
    link = db.query(Link).filter(Link.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="リンクが見つかりません")
    db.delete(link)
    db.commit()
    return {"detail": "リンクが削除されました"}

@router.get("/links/{map_id}")
def get_links(
    map_id: int,
    link_type: int,
    date: datetime,
    db: Session = Depends(get_db)
):
    rows = db.query(Link).filter(Link.map_id == map_id, Link.link_type == link_type).all()

    date_qualified_rows = []
    for row in rows:
        if date:
            exist_from = row.exist_from
            exist_until = row.exist_until
            if exist_from and date < exist_from:
                continue
            if exist_until and date > exist_until:
                continue
            date_qualified_rows.append(row)

    return [
        {
            "id": row.id,
            "map_id": row.map_id,
            "link_type": row.link_type,
            "from_country": row.from_country,
            "to_country": row.to_country,
            "exist_from": row.exist_from.isoformat() if row.exist_from else None,
            "exist_until": row.exist_until.isoformat() if row.exist_until else None,
        }
        for row in date_qualified_rows
    ]

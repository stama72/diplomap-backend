from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
from models import Link, LinkDetails, LinkType, User
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
    summary: str
    summary_ja: str
    source_url: str


def _serialize_link(link: Link):
    return {
        "id": link.id,
        "from_country": link.from_country,
        "to_country": link.to_country,
        "link_type": link.link_type,
        "exist_from": link.exist_from.isoformat() if link.exist_from else None,
        "exist_until": link.exist_until.isoformat() if link.exist_until else None,
        "map_id": link.map_id,
    }


def _require_edit_access(link: Link, user: User, db: Session):
    if not maps.can_edit_map(link.map_id, user, db):
        raise HTTPException(status_code=403, detail="このリンクを編集する権限がありません")

@router.post("/links")
def create_link(
    link: LinkIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not maps.can_edit_map(link.map_id, user, db):
        raise HTTPException(status_code=403, detail="このマップにリンクを追加する権限がありません")

    link_type = db.query(LinkType).filter(LinkType.id == link.link_type, LinkType.map_id == link.map_id).first()
    if not link_type:
        raise HTTPException(status_code=404, detail="リンクタイプが見つかりません")

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
    return _serialize_link(new_link)

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
    _require_edit_access(link, user, db)

    link_type = db.query(LinkType).filter(LinkType.id == link_update.link_type, LinkType.map_id == link.map_id).first()
    if not link_type:
        raise HTTPException(status_code=404, detail="リンクタイプが見つかりません")

    for key, value in link_update.model_dump().items():
        setattr(link, key, value)
    db.commit()
    db.refresh(link)
    return _serialize_link(link)

@router.delete("/links/{link_id}")
def delete_link(
    link_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    link = db.query(Link).filter(Link.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="リンクが見つかりません")
    _require_edit_access(link, user, db)
    db.delete(link)
    db.commit()
    return {"detail": "リンクが削除されました"}


@router.get("/links/{link_id}/details")
def get_link_details(
    link_id: int,
    db: Session = Depends(get_db)
):
    details = db.query(LinkDetails).filter(LinkDetails.link_id == link_id).first()
    if not details:
        raise HTTPException(status_code=404, detail="リンク詳細が見つかりません")
    return {
        "link_id": details.link_id,
        "summary": details.summary,
        "summary_ja": details.summary_ja,
        "source_url": details.source_url,
    }


@router.post("/links/{link_id}/details")
def create_link_details(
    link_id: int,
    details_in: LinkDetailsIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    link = db.query(Link).filter(Link.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="リンクが見つかりません")
    _require_edit_access(link, user, db)

    existing = db.query(LinkDetails).filter(LinkDetails.link_id == link_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="リンク詳細は既に存在します")

    details = LinkDetails(
        link_id=link_id,
        summary=details_in.summary,
        summary_ja=details_in.summary_ja,
        source_url=details_in.source_url,
    )
    db.add(details)
    db.commit()
    return {
        "link_id": details.link_id,
        "summary": details.summary,
        "summary_ja": details.summary_ja,
        "source_url": details.source_url,
    }


@router.put("/links/{link_id}/details")
def update_link_details(
    link_id: int,
    details_in: LinkDetailsIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    link = db.query(Link).filter(Link.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="リンクが見つかりません")
    _require_edit_access(link, user, db)

    details = db.query(LinkDetails).filter(LinkDetails.link_id == link_id).first()
    if not details:
        details = LinkDetails(link_id=link_id)
        db.add(details)

    details.summary = details_in.summary
    details.summary_ja = details_in.summary_ja
    details.source_url = details_in.source_url
    db.commit()
    db.refresh(details)
    return {
        "link_id": details.link_id,
        "summary": details.summary,
        "summary_ja": details.summary_ja,
        "source_url": details.source_url,
    }

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
            exist_from = datetime.combine(row.exist_from, datetime.min.time()).replace(tzinfo=timezone.utc)
            exist_until = datetime.combine(row.exist_until, datetime.min.time()).replace(tzinfo=timezone.utc)
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

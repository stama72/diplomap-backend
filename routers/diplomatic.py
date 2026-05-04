from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import User, DiplomaticProposal, EditHistory
from auth import get_current_user, require_role

router = APIRouter(prefix="/api/diplomatic", tags=["diplomatic"])

class ProposalIn(BaseModel):
    country_a:     str  # iso_id format
    country_b:     str  # iso_id format
    relation_type: str
    summary:       str
    source_url:    str
    source_note:   str = ""

class ReviewIn(BaseModel):
    action:  str   # "approve" or "reject"
    comment: str = ""

@router.get("/")
def list_proposals(
    status: str = None,
    db:     Session = Depends(get_db),
    _:      User    = Depends(get_current_user)
):
    """
    提案を一覧取得（ステータスでフィルタ可能）
    """
    q = db.query(DiplomaticProposal)
    if status:
        q = q.filter(DiplomaticProposal.status == status)
    
    return q.order_by(DiplomaticProposal.created_at.desc()).all()

@router.post("/")
def create_proposal(
    body:         ProposalIn,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    """提案を作成する"""
    proposal = DiplomaticProposal(
        country_a=body.country_a,
        country_b=body.country_b,
        relation_type=body.relation_type,
        summary=body.summary,
        source_url=body.source_url,
        source_note=body.source_note,
        proposed_by=current_user.id,
        status="pending"
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal

@router.post("/{proposal_id}/review")
def review_proposal(
    proposal_id:  int,
    body:         ReviewIn,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(
        require_role("reviewer", "admin")
    )
):
    """提案をレビューする（承認 or 差し戻し）"""
    proposal = db.query(DiplomaticProposal).filter(
        DiplomaticProposal.id == proposal_id
    ).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="提案が見つかりません")
    if proposal.status != "pending":
        raise HTTPException(status_code=400, detail="すでにレビュー済みです")

    if body.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action は approve か reject")

    proposal.status        = "approved" if body.action == "approve" else "rejected"
    proposal.reviewed_by   = current_user.id
    proposal.review_comment = body.comment
    proposal.reviewed_at   = datetime.utcnow()
    
    db.commit()
    db.refresh(proposal)
    
    # 変更履歴を記録
    history = EditHistory(
        relation_id=proposal.id,
        changed_by=current_user.id,
        before_data={"status": "pending"},
        after_data={"status": proposal.status},
        comment=f"Reviewed by {current_user.display_name}: {body.comment}"
    )
    db.add(history)
    db.commit()
    
    return proposal

@router.get("/approved")
def get_approved_relations(db: Session = Depends(get_db)):
    """承認済みの外交提案を返す（認証不要・地図表示用）"""
    proposals = db.query(DiplomaticProposal).filter(
        DiplomaticProposal.status == "approved"
    ).all()
    return [
        {
            "id":            p.id,
            "country_a":     p.country_a,
            "country_b":     p.country_b,
            "relation_type": p.relation_type,
            "summary":       p.summary,
            "source_url":    p.source_url,
        }
        for p in proposals
    ]

@router.get("/history")
def get_history(
    db: Session = Depends(get_db),
    _:  User    = Depends(get_current_user)
):
    """承認・差し戻し済みの提案を履歴として返す"""
    proposals = db.query(DiplomaticProposal).filter(
        DiplomaticProposal.status != "pending"
    ).order_by(DiplomaticProposal.reviewed_at.desc()).all()

    return [
        {
            "id":             p.id,
            "country_a":      p.country_a,
            "country_b":      p.country_b,
            "relation_type":  p.relation_type,
            "summary":        p.summary,
            "source_url":     p.source_url,
            "source_note":    p.source_note,
            "status":         p.status,
            "review_comment": p.review_comment,
            "proposed_by":    p.proposed_by,
            "reviewed_by":    p.reviewed_by,
            "created_at":     p.created_at.isoformat() if p.created_at else None,
            "reviewed_at":    p.reviewed_at.isoformat() if p.reviewed_at else None,
        }
        for p in proposals
    ]
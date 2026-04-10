from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import User, DiplomaticProposal, EditHistory
from auth import get_current_user, require_role

router = APIRouter(prefix="/api/diplomatic", tags=["diplomatic"])

class ProposalIn(BaseModel):
    country_a:     str
    country_b:     str
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
    proposal = DiplomaticProposal(
        **body.model_dump(),
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
    return proposal
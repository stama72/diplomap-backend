from sqlalchemy import Column, Float, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base


class Country(Base):
    __tablename__ = "countries"
    __table_args__ = {"extend_existing": True}
    id      = Column(String(10), primary_key=True)
    name_ja = Column(String(100), nullable=False)
    lat     = Column(Float, nullable=False)
    lng     = Column(Float, nullable=False)

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True)
    email         = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name  = Column(String(100), nullable=False)
    role          = Column(String(20), default="editor")
    created_at    = Column(DateTime, server_default=func.now())

class DiplomaticProposal(Base):
    __tablename__ = "diplomatic_proposals"
    id             = Column(Integer, primary_key=True)
    country_a      = Column(String(10), ForeignKey("countries.id"))
    country_b      = Column(String(10), ForeignKey("countries.id"))
    relation_type  = Column(String(50), nullable=False)
    summary        = Column(Text, nullable=False)
    source_url     = Column(Text, nullable=False)
    source_note    = Column(Text)
    status         = Column(String(20), default="pending")
    proposed_by    = Column(Integer, ForeignKey("users.id"))
    reviewed_by    = Column(Integer, ForeignKey("users.id"))
    review_comment = Column(Text)
    created_at     = Column(DateTime, server_default=func.now())
    reviewed_at    = Column(DateTime)

class EditHistory(Base):
    __tablename__ = "edit_history"
    id          = Column(Integer, primary_key=True)
    relation_id = Column(Integer, ForeignKey("diplomatic_relations.id"))
    changed_by  = Column(Integer, ForeignKey("users.id"))
    before_data = Column(JSONB)
    after_data  = Column(JSONB)
    comment     = Column(Text)
    changed_at  = Column(DateTime, server_default=func.now())
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, ForeignKey, Boolean, Numeric, Date, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base


# ========== System ==========

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}
    
    id            = Column(Integer, primary_key=True)
    name          = Column(String(255), unique=True, nullable=False)
    email         = Column(String(255), unique=True)
    display_name  = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role          = Column(String(20), default="editor", nullable=False)
    created_at    = Column(DateTime, server_default=func.now())


# ========== Geographic & Political Entities ==========

class Point(Base):
    __tablename__ = "points"
    __table_args__ = {"extend_existing": True}
    
    id         = Column(String(255), primary_key=True)
    name       = Column(String(255), nullable=False)
    name_ja    = Column(String(255))
    lat        = Column(Numeric(10, 6), nullable=False)
    lng        = Column(Numeric(10, 6), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Country(Base):
    __tablename__ = "countries"
    __table_args__ = {"extend_existing": True}
    
    iso_id             = Column(String(16), primary_key=True)
    name               = Column(String(255), nullable=False)
    name_ja            = Column(String(255), nullable=False)
    capital_point_id   = Column(String(255), ForeignKey("points.id"))
    exist_from         = Column(Date)
    exist_until        = Column(Date)
    summary            = Column(Text)
    summary_jp         = Column(Text)
    created_at         = Column(DateTime, server_default=func.now())


class InternationalOrg(Base):
    __tablename__ = "international_orgs"
    __table_args__ = {"extend_existing": True}
    
    id                    = Column(String(255), primary_key=True)
    name                  = Column(String(255), nullable=False)
    name_ja               = Column(String(255), nullable=False)
    headquarters_point_id = Column(String(255), ForeignKey("points.id"), nullable=False)
    exist_from            = Column(Date)
    exist_until           = Column(Date)
    summary               = Column(Text)
    summary_jp            = Column(Text)
    created_at            = Column(DateTime, server_default=func.now())


class MemberCountry(Base):
    __tablename__ = "member_countries"
    __table_args__ = {"extend_existing": True}
    
    id                = Column(Integer, primary_key=True)
    org_id            = Column(String(255), ForeignKey("international_orgs.id"), nullable=False)
    country_id        = Column(String(255), ForeignKey("countries.iso_id"), nullable=False)
    joined_at         = Column(Date)
    belonged_to_until = Column(Date)
    status            = Column(String(50))
    status_jp         = Column(String(50))
    created_at        = Column(DateTime, server_default=func.now())


class MemberOrg(Base):
    __tablename__ = "member_orgs"
    __table_args__ = {"extend_existing": True}
    
    id                = Column(Integer, primary_key=True)
    greater_org_id    = Column(String(255), ForeignKey("international_orgs.id"), nullable=False)
    member_org_id     = Column(String(255), ForeignKey("international_orgs.id"), nullable=False)
    joined_at         = Column(Date)
    belonged_to_until = Column(Date)
    status            = Column(String(50))
    status_jp         = Column(String(50))
    created_at        = Column(DateTime, server_default=func.now())


class LocalOrg(Base):
    __tablename__ = "local_orgs"
    __table_args__ = {"extend_existing": True}
    
    id                    = Column(String(255), primary_key=True)
    name_en               = Column(String(255), nullable=False)
    name_ja               = Column(String(255), nullable=False)
    headquarters_point_id = Column(String(255), ForeignKey("points.id"))
    exist_from            = Column(Date)
    exist_until           = Column(Date)
    summary               = Column(Text)
    summary_jp            = Column(Text)
    created_at            = Column(DateTime, server_default=func.now())


# ========== Trade ==========

class TradeLink(Base):
    __tablename__ = "trade_links"
    __table_args__ = {"extend_existing": True}
    
    id           = Column(Integer, primary_key=True)
    from_country = Column(String(255), ForeignKey("countries.iso_id"), nullable=False)
    to_country   = Column(String(255), ForeignKey("countries.iso_id"), nullable=False)
    value        = Column(Numeric(15, 2), nullable=False)
    category     = Column(String(50), nullable=False)
    year         = Column(Integer, nullable=False)
    created_at   = Column(DateTime, server_default=func.now())
    updated_at   = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ========== Diplomatic Relations ==========
"""
class DiplomaticRelation(Base):
    __tablename__ = "diplomatic_relations"
    __table_args__ = {"extend_existing": True}
    
    id            = Column(Integer, primary_key=True)
    country_a     = Column(String(255), ForeignKey("countries.iso_id"), nullable=False)
    country_b     = Column(String(255), ForeignKey("countries.iso_id"), nullable=False)
    relation_type = Column(String(50), nullable=False)
    summary       = Column(Text, nullable=False)
    source_url    = Column(Text)
    created_at    = Column(DateTime, server_default=func.now())
    updated_at    = Column(DateTime, server_default=func.now(), onupdate=func.now())


class DiplomaticProposal(Base):
    __tablename__ = "diplomatic_proposals"
    __table_args__ = {"extend_existing": True}
    
    id             = Column(Integer, primary_key=True)
    country_a      = Column(String(255), ForeignKey("countries.iso_id"), nullable=False)
    country_b      = Column(String(255), ForeignKey("countries.iso_id"), nullable=False)
    relation_type  = Column(String(50), nullable=False)
    summary        = Column(Text, nullable=False)
    source_url     = Column(Text, nullable=False)
    source_note    = Column(Text)
    status         = Column(String(20), default="pending", nullable=False)
    proposed_by    = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewed_by    = Column(Integer, ForeignKey("users.id"))
    review_comment = Column(Text)
    created_at     = Column(DateTime, server_default=func.now())
    reviewed_at    = Column(DateTime)


class EditHistory(Base):
    __tablename__ = "edit_history"
    __table_args__ = {"extend_existing": True}
    
    id          = Column(Integer, primary_key=True)
    relation_id = Column(Integer, ForeignKey("diplomatic_proposals.id"), nullable=False)
    changed_by  = Column(Integer, ForeignKey("users.id"), nullable=False)
    before_data = Column(JSONB)
    after_data  = Column(JSONB)
    comment     = Column(Text)
    changed_at  = Column(DateTime, server_default=func.now())
"""

# ========== Maps & Links ==========

class Map(Base):
    __tablename__ = "maps"
    __table_args__ = {"extend_existing": True}
    
    id                    = Column(String(255), primary_key=True)
    name                  = Column(String(255), nullable=False)
    name_ja               = Column(String(255), nullable=False)
    owner                 = Column(Integer, ForeignKey("users.id"), nullable=False)
    publishing_permission = Column(String(20), nullable=False)
    editing_permission    = Column(String(20), nullable=False)
    exist_from            = Column(Date, nullable=False)
    exist_until           = Column(Date, nullable=False)
    time_scale            = Column(String(20), nullable=False)
    summary               = Column(Text)
    summary_jp            = Column(Text)
    source_url            = Column(Text)
    created_at            = Column(DateTime, server_default=func.now())
    updated_at            = Column(DateTime, server_default=func.now(), onupdate=func.now())


class LinkDesign(Base):
    __tablename__ = "link_designs"
    __table_args__ = {"extend_existing": True}
    
    link_type  = Column(String(255), primary_key=True)
    map_id     = Column(String(255), ForeignKey("maps.id"), nullable=False)
    color      = Column(Integer)
    animated   = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


class Link(Base):
    __tablename__ = "links"
    __table_args__ = {"extend_existing": True}
    
    id           = Column(Integer, primary_key=True)
    map_id       = Column(String(255), ForeignKey("maps.id"), nullable=False)
    link_type    = Column(String(255), ForeignKey("link_designs.link_type"), nullable=False)
    from_country = Column(String(255), ForeignKey("countries.iso_id"), nullable=False)
    to_country   = Column(String(255), ForeignKey("countries.iso_id"), nullable=False)
    exist_from   = Column(Date)
    exist_until  = Column(Date)
    created_at   = Column(DateTime, server_default=func.now())
    updated_at   = Column(DateTime, server_default=func.now(), onupdate=func.now())


class LinkDetailsJa(Base):
    __tablename__ = "link_details_ja"
    __table_args__ = {"extend_existing": True}
    
    id         = Column(Integer, primary_key=True)
    link_id    = Column(Integer, ForeignKey("links.id"), nullable=False)
    summary_ja = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())





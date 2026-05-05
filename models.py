from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import synonym
from sqlalchemy.sql import func
from database import Base


# ========== System ==========

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'reviewer', 'editor', 'viewer')", name="role_check"),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, server_default=text("'editor'"))
    email = Column(String(255), unique=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

# ========== Geographic & Political Entities ==========

class Point(Base):
    __tablename__ = "points"
    __table_args__ = (
        Index("idx_points_name", "name"),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    name_ja = Column(String(255), nullable=False)
    lat = Column(Numeric(10, 6), nullable=False)
    lng = Column(Numeric(10, 6), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Country(Base):
    __tablename__ = "countries"
    __table_args__ = (
        Index("idx_countries_name", "name"),
    )

    iso_id = Column(String(16), primary_key=True)
    name = Column(String(255), nullable=False)
    name_ja = Column(String(255), nullable=False)
    capital_point_id = Column(Integer, ForeignKey("points.id"))
    exist_from = Column(Date)
    exist_until = Column(Date)
    summary = Column(Text)
    summary_jp = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class InternationalOrg(Base):
    __tablename__ = "international_orgs"
    __table_args__ = (
        Index("idx_international_orgs_name", "name"),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    name_ja = Column(String(255), nullable=False)
    headquarters_point_id = Column(Integer, ForeignKey("points.id"), nullable=False)
    exist_from = Column(Date)
    exist_until = Column(Date)
    summary = Column(Text)
    summary_jp = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class MemberCountry(Base):
    __tablename__ = "member_countries"
    __table_args__ = (
        UniqueConstraint("org_id", "country_id", "joined_at", name="member_countries_org_id_country_id_joined_at_key"),
        Index("idx_member_countries_org_id", "org_id"),
        Index("idx_member_countries_country_id", "country_id"),
    )

    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("international_orgs.id"), nullable=False)
    country_id = Column(String(255), ForeignKey("countries.iso_id"), nullable=False)
    joined_at = Column(Date)
    belonged_to_until = Column(Date)
    status = Column(String(50))
    status_jp = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class MemberOrg(Base):
    __tablename__ = "member_orgs"
    __table_args__ = (
        CheckConstraint("greater_org_id <> member_org_id", name="no_self_membership"),
        Index("idx_member_orgs_greater_org_id", "greater_org_id"),
        Index("idx_member_orgs_member_org_id", "member_org_id"),
    )

    id = Column(Integer, primary_key=True)
    greater_org_id = Column(Integer, ForeignKey("international_orgs.id"), nullable=False)
    member_org_id = Column(Integer, ForeignKey("international_orgs.id"), nullable=False)
    joined_at = Column(Date)
    belonged_to_until = Column(Date)
    status = Column(String(50))
    status_jp = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class LocalOrg(Base):
    __tablename__ = "local_forces"
    __table_args__ = (
        Index("idx_local_forces_name", "name"),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    name_ja = Column(String(255), nullable=False)
    headquarters_point_id = Column(Integer, ForeignKey("points.id"))
    exist_from = Column(Date)
    exist_until = Column(Date)
    summary = Column(Text)
    summary_jp = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())



# ========== Maps & Links ==========

class Map(Base):
    __tablename__ = "maps"
    __table_args__ = (
        CheckConstraint(
            "read_permission IN ('private', 'shared', 'public') AND edit_permission IN ('private', 'shared', 'public')",
            name="permission_check",
        ),
        CheckConstraint(
            "time_scale IN ('hundred_years', 'ten_years', 'five_years', 'one_year', 'one_month', 'one_week', 'one_day')",
            name="time_scale_check",
        ),
        Index("idx_maps_owner", "owner")
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    name_ja = Column(String(255), nullable=False)
    owner = Column(Integer, ForeignKey("users.id"), nullable=False)
    read_permission = Column(String(20), nullable=False)
    edit_permission = Column(String(20), nullable=False)
    exist_from = Column(Date, nullable=False)
    exist_until = Column(Date, nullable=False)
    time_scale = Column(String(20), nullable=False)
    summary = Column(Text)
    summary_jp = Column(Text)
    regulations = Column(Text)
    source_url = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class MapPoint(Base):
    __tablename__ = "map_points"
    __table_args__ = (
        UniqueConstraint("map_id", "point_id", name="map_points_map_id_point_id_key"),
    )

    id = Column(Integer, primary_key=True)
    map_id = Column(Integer, ForeignKey("maps.id"), nullable=False)
    point_id = Column(Integer, ForeignKey("points.id"), nullable=False)
    color = Column(String(16))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class LinkType(Base):
    __tablename__ = "link_types"
    __table_args__ = (
        Index("idx_link_types_map_id", "map_id"),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    map_id = Column(Integer, ForeignKey("maps.id"), nullable=False)
    color = Column(String(16))
    animated = Column(Boolean, server_default=text("false"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    link_type = synonym("name")


class Link(Base):
    __tablename__ = "links"
    __table_args__ = (
        UniqueConstraint(
            "map_id",
            "link_type",
            "point_from",
            "point_to",
            "exist_from",
            name="links_map_id_link_type_point_from_point_to_exist_from_key",
        ),
        Index("idx_links_map_id", "map_id"),
        Index("idx_links_point_from", "point_from"),
        Index("idx_links_point_to", "point_to"),
        Index("idx_links_link_type", "link_type"),
    )

    id = Column(Integer, primary_key=True)
    map_id = Column(Integer, ForeignKey("maps.id"), nullable=False)
    link_type = Column(Integer, ForeignKey("link_types.id"), nullable=False)
    point_from = Column(Integer, ForeignKey("points.id"), nullable=False)
    point_to = Column(Integer, ForeignKey("points.id"), nullable=False)
    exist_from = Column(Date, nullable=False)
    exist_until = Column(Date, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    from_country = synonym("point_from")
    to_country = synonym("point_to")


class LinkDetails(Base):
    __tablename__ = "link_details"

    link_id = Column(Integer, ForeignKey("links.id", ondelete="CASCADE"), primary_key=True)
    summary = Column(Text, nullable=False)
    summary_ja = Column(Text, nullable=False)
    source_url = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


LinkDetailsJa = LinkDetails





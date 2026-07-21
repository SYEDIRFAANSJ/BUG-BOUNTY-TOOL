from typing import List, Optional, Any
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Text, ForeignKey, TIMESTAMP, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shared.database import Base
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid

class Platform(Base):
    __tablename__ = "platforms"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    api_base_url: Mapped[Optional[str]] = mapped_column(Text)
    rate_limit_per_min: Mapped[int] = mapped_column(Integer, nullable=False)
    last_polled_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    poll_interval_minutes: Mapped[Optional[int]] = mapped_column(Integer, default=60)
    circuit_open_until: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)

    programs: Mapped[List["Program"]] = relationship(back_populates="platform")


class Program(Base):
    __tablename__ = "programs"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform_id: Mapped[Optional[int]] = mapped_column(ForeignKey("platforms.id"))
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[Optional[str]] = mapped_column(String(20), default="active")
    offers_bounty: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    scope_hash: Mapped[Optional[str]] = mapped_column(String(64))
    raw_scope_json: Mapped[Optional[Any]] = mapped_column(JSONB)
    first_seen: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, server_default=func.now())
    last_updated: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, server_default=func.now())
    last_change_type: Mapped[Optional[str]] = mapped_column(String(20))

    platform: Mapped[Optional["Platform"]] = relationship(back_populates="programs")
    scopes: Mapped[List["Scope"]] = relationship(back_populates="program", cascade="all, delete-orphan")
    reports: Mapped[List["Report"]] = relationship(back_populates="program")
    watchers: Mapped[List["UserWatchlist"]] = relationship(back_populates="program", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("platform_id", "external_id", name="uq_platform_external"),
        Index("idx_programs_platform_status", "platform_id", "status"),
    )


class Scope(Base):
    __tablename__ = "scopes"

    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[Optional[int]] = mapped_column(ForeignKey("programs.id", ondelete="CASCADE"))
    asset_identifier: Mapped[str] = mapped_column(String(500), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(30), nullable=False)
    in_scope: Mapped[bool] = mapped_column(Boolean, nullable=False)
    eligible_for_bounty: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    severity_max: Mapped[Optional[str]] = mapped_column(String(20))
    instructions: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, server_default=func.now())

    program: Mapped[Optional["Program"]] = relationship(back_populates="scopes")
    assets: Mapped[List["Asset"]] = relationship(back_populates="scope", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_scopes_program_id", "program_id"),
    )


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    scope_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scopes.id", ondelete="CASCADE"))
    subdomain: Mapped[Optional[str]] = mapped_column(String(500))
    resolved_ip: Mapped[Optional[str]] = mapped_column(String(45))
    is_live: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    http_status: Mapped[Optional[int]] = mapped_column(Integer)
    tech_stack: Mapped[Optional[Any]] = mapped_column(JSONB)
    title: Mapped[Optional[str]] = mapped_column(Text)
    screenshot_path: Mapped[Optional[str]] = mapped_column(Text)
    discovered_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, server_default=func.now())
    last_checked: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)

    scope: Mapped[Optional["Scope"]] = relationship(back_populates="assets")
    endpoints: Mapped[List["Endpoint"]] = relationship(back_populates="asset", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_assets_scope_id", "scope_id"),
    )


class Endpoint(Base):
    __tablename__ = "endpoints"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"))
    url: Mapped[str] = mapped_column(Text, nullable=False)
    method: Mapped[Optional[str]] = mapped_column(String(10), default="GET")
    params: Mapped[Optional[Any]] = mapped_column(JSONB)
    status_code: Mapped[Optional[int]] = mapped_column(Integer)
    content_type: Mapped[Optional[str]] = mapped_column(String(100))
    discovered_via: Mapped[Optional[str]] = mapped_column(String(30))
    test_tags: Mapped[Optional[Any]] = mapped_column(JSONB)
    risk_priority: Mapped[Optional[str]] = mapped_column(String(10), default="medium")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    discovered_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, server_default=func.now())

    asset: Mapped[Optional["Asset"]] = relationship(back_populates="endpoints")

    __table_args__ = (
        Index("idx_endpoints_asset_id", "asset_id"),
        Index("idx_endpoints_risk_priority", "risk_priority"),
    )


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[Optional[int]] = mapped_column(ForeignKey("programs.id"))
    generated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, server_default=func.now())
    total_assets: Mapped[Optional[int]] = mapped_column(Integer)
    total_endpoints: Mapped[Optional[int]] = mapped_column(Integer)
    high_priority_count: Mapped[Optional[int]] = mapped_column(Integer)
    summary_json: Mapped[Optional[Any]] = mapped_column(JSONB)
    pdf_path: Mapped[Optional[str]] = mapped_column(Text)
    emailed: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    program: Mapped[Optional["Program"]] = relationship(back_populates="reports")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    notify_instant: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    digest_freq: Mapped[Optional[str]] = mapped_column(String(20), default="instant")
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, server_default=func.now())

    watchlist: Mapped[List["UserWatchlist"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserWatchlist(Base):
    __tablename__ = "user_watchlist"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id", ondelete="CASCADE"), primary_key=True)
    muted: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="watchlist")
    program: Mapped["Program"] = relationship(back_populates="watchers")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    correlation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    program_id: Mapped[Optional[int]] = mapped_column(Integer)
    asset_id: Mapped[Optional[int]] = mapped_column(Integer)
    detail: Mapped[Optional[Any]] = mapped_column(JSONB)
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("idx_audit_log_correlation_id", "correlation_id"),
        Index("idx_audit_log_program_id", "program_id"),
    )

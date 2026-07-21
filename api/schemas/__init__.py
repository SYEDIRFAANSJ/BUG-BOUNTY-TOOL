from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

# Programs
class PlatformResponse(BaseModel):
    id: int
    name: str
    api_base_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ScopeResponse(BaseModel):
    id: int
    asset_identifier: str
    asset_type: str
    in_scope: bool
    eligible_for_bounty: bool
    severity_max: Optional[str] = None
    instructions: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ProgramListItem(BaseModel):
    id: int
    platform: Optional[PlatformResponse] = None
    external_id: Optional[str] = None
    name: str
    url: Optional[str] = None
    status: str
    offers_bounty: bool
    first_seen: datetime
    last_updated: datetime
    last_change_type: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ProgramDetail(ProgramListItem):
    scopes: List[ScopeResponse] = []
    raw_scope_json: Optional[Dict[str, Any]] = None
    model_config = ConfigDict(from_attributes=True)

class ProgramListResponse(BaseModel):
    programs: List[ProgramListItem]
    total: int
    model_config = ConfigDict(from_attributes=True)

# Assets
class AssetResponse(BaseModel):
    id: int
    subdomain: str
    resolved_ip: Optional[str] = None
    is_live: bool
    http_status: Optional[int] = None
    tech_stack: Optional[List[str]] = None
    title: Optional[str] = None
    screenshot_path: Optional[str] = None
    discovered_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Endpoints  
class EndpointResponse(BaseModel):
    id: int
    url: str
    method: str
    params: Optional[List[str]] = None
    status_code: Optional[int] = None
    content_type: Optional[str] = None
    discovered_via: Optional[str] = None
    test_tags: Optional[List[str]] = None
    risk_priority: Optional[str] = None
    notes: Optional[str] = None
    discovered_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Reports
class ReportResponse(BaseModel):
    id: int
    generated_at: datetime
    total_assets: int
    total_endpoints: int
    high_priority_count: int
    summary_json: Optional[Dict[str, Any]] = None
    pdf_path: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# Auth
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    email: str
    password: str
    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'
    model_config = ConfigDict(from_attributes=True)

# User
class UserPreferences(BaseModel):
    notify_instant: bool
    digest_freq: str
    model_config = ConfigDict(from_attributes=True)

class WatchlistRequest(BaseModel):
    program_id: int
    muted: bool = False
    model_config = ConfigDict(from_attributes=True)

class WatchlistResponse(BaseModel):
    program_id: int
    program_name: Optional[str] = None
    muted: bool
    model_config = ConfigDict(from_attributes=True)

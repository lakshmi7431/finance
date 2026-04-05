from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
from app.models import RoleEnum, RecordTypeEnum


# ─── Auth Schemas ────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ─── User Schemas ─────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: RoleEnum = RoleEnum.viewer

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 2:
            raise ValueError("Password must be at least 2 characters")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[RoleEnum] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: RoleEnum
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Financial Record Schemas ─────────────────────────────────────────────────

class RecordCreate(BaseModel):
    amount: float
    type: RecordTypeEnum
    category: str
    date: datetime
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

    @field_validator("category")
    @classmethod
    def category_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Category cannot be empty")
        return v.strip()


class RecordUpdate(BaseModel):
    amount: Optional[float] = None
    type: Optional[RecordTypeEnum] = None
    category: Optional[str] = None
    date: Optional[datetime] = None
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v


class RecordResponse(BaseModel):
    id: int
    amount: float
    type: RecordTypeEnum
    category: str
    date: datetime
    notes: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class RecordListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    records: list[RecordResponse]


# ─── Dashboard Schemas ────────────────────────────────────────────────────────

class CategorySummary(BaseModel):
    category: str
    total: float


class MonthlyTrend(BaseModel):
    month: str
    income: float
    expense: float


class DashboardSummary(BaseModel):
    total_income: float
    total_expenses: float
    net_balance: float
    record_count: int
    category_totals: list[CategorySummary]
    recent_records: list[RecordResponse]
    monthly_trends: list[MonthlyTrend]
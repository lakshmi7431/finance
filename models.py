from sqlalchemy import Column, String, Boolean, DateTime, Enum, Text, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import BIGINT
from app.database import Base
import enum


# 🔹 Common ID type (IMPORTANT — use everywhere)
UserID = BIGINT(unsigned=True)


# 🔹 Enums
class RoleEnum(str, enum.Enum):
    viewer = "viewer"
    analyst = "analyst"
    admin = "admin"


class RecordTypeEnum(str, enum.Enum):
    income = "income"
    expense = "expense"


# 🔹 User Table
class User(Base):
    __tablename__ = "users"

    id = Column(UserID, primary_key=True, autoincrement=True)

    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.viewer, nullable=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    records = relationship("FinancialRecord", back_populates="created_by_user")


# 🔹 Financial Records Table
class FinancialRecord(Base):
    __tablename__ = "financial_records"

    id = Column(UserID, primary_key=True, autoincrement=True)

    created_by = Column(
        UserID,
        ForeignKey("users.id"),
        nullable=False
    )

    amount = Column(DECIMAL(10, 2), nullable=False)  # better than FLOAT
    type = Column(Enum(RecordTypeEnum), nullable=False)
    category = Column(String(100), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)

    notes = Column(Text)
    is_deleted = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    created_by_user = relationship("User", back_populates="records")
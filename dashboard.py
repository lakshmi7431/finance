from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from typing import Optional
from app.database import get_db
from app import models, schemas
from app.security import require_analyst_or_admin, require_any_role
# from app.auth import require_analyst_or_admin, require_any_role

router = APIRouter()


@router.get("/summary", response_model=schemas.DashboardSummary)
def get_summary(
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_analyst_or_admin)
):
    """
    Full dashboard summary: income, expenses, net balance, category totals,
    recent records, and monthly trends.
    Analyst and Admin only.
    """
    base_query = db.query(models.FinancialRecord).filter(
        models.FinancialRecord.is_deleted == False
    )
    if start_date:
        base_query = base_query.filter(models.FinancialRecord.date >= start_date)
    if end_date:
        base_query = base_query.filter(models.FinancialRecord.date <= end_date)

    all_records = base_query.all()

    # ── Totals ──────────────────────────────────────────────────────────────
    total_income = sum(r.amount for r in all_records if r.type == models.RecordTypeEnum.income)
    total_expenses = sum(r.amount for r in all_records if r.type == models.RecordTypeEnum.expense)
    net_balance = total_income - total_expenses

    # ── Category Totals ──────────────────────────────────────────────────────
    category_map: dict[str, float] = {}
    for r in all_records:
        category_map[r.category] = category_map.get(r.category, 0) + r.amount
    category_totals = [
        {"category": cat, "total": round(total, 2)}
        for cat, total in sorted(category_map.items(), key=lambda x: -x[1])
    ]

    # ── Recent Records (last 5) ──────────────────────────────────────────────
    recent = (
        db.query(models.FinancialRecord)
        .filter(models.FinancialRecord.is_deleted == False)
        .order_by(models.FinancialRecord.date.desc())
        .limit(5)
        .all()
    )

    # ── Monthly Trends (last 6 months) ───────────────────────────────────────
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    trend_records = (
        db.query(models.FinancialRecord)
        .filter(
            models.FinancialRecord.is_deleted == False,
            models.FinancialRecord.date >= six_months_ago
        )
        .all()
    )

    monthly: dict[str, dict] = {}
    for r in trend_records:
        key = r.date.strftime("%Y-%m")
        if key not in monthly:
            monthly[key] = {"month": key, "income": 0.0, "expense": 0.0}
        if r.type == models.RecordTypeEnum.income:
            monthly[key]["income"] += r.amount
        else:
            monthly[key]["expense"] += r.amount

    monthly_trends = [
        {
            "month": v["month"],
            "income": round(v["income"], 2),
            "expense": round(v["expense"], 2)
        }
        for v in sorted(monthly.values(), key=lambda x: x["month"])
    ]

    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net_balance": round(net_balance, 2),
        "record_count": len(all_records),
        "category_totals": category_totals,
        "recent_records": recent,
        "monthly_trends": monthly_trends
    }


@router.get("/balance", response_model=dict)
def get_quick_balance(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_any_role)
):
    """
    Quick balance overview. Available to all authenticated users.
    """
    records = db.query(models.FinancialRecord).filter(
        models.FinancialRecord.is_deleted == False
    ).all()

    total_income = sum(r.amount for r in records if r.type == models.RecordTypeEnum.income)
    total_expenses = sum(r.amount for r in records if r.type == models.RecordTypeEnum.expense)

    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net_balance": round(total_income - total_expenses, 2)
    }


@router.get("/recent", response_model=list[schemas.RecordResponse])
def get_recent_activity(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_any_role)
):
    """
    Get the most recent financial records.
    Available to all authenticated users.
    """
    return (
        db.query(models.FinancialRecord)
        .filter(models.FinancialRecord.is_deleted == False)
        .order_by(models.FinancialRecord.date.desc())
        .limit(limit)
        .all()
    )
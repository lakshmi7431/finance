from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import Optional
from app.database import get_db
from app import models, schemas
# from app.auth import  require_admin
from app.security import require_analyst_or_admin, require_any_role,require_admin,get_current_user
# from app.auth import get_current_user, require_admin, require_any_role

router = APIRouter()


def get_record_or_404(record_id: int, db: Session) -> models.FinancialRecord:
    record = db.query(models.FinancialRecord).filter(
        models.FinancialRecord.id == record_id,
        models.FinancialRecord.is_deleted == False
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.get("/", response_model=schemas.RecordListResponse)
def list_records(
    # Filters
    type: Optional[models.RecordTypeEnum] = Query(None, description="Filter by income or expense"),
    category: Optional[str] = Query(None, description="Filter by category name"),
    start_date: Optional[datetime] = Query(None, description="Filter records from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter records up to this date"),
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Records per page"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_any_role)
):
    """
    List financial records with optional filtering and pagination.
    All authenticated users can view records.
    """
    query = db.query(models.FinancialRecord).filter(
        models.FinancialRecord.is_deleted == False
    )

    if type:
        query = query.filter(models.FinancialRecord.type == type)
    if category:
        query = query.filter(models.FinancialRecord.category.ilike(f"%{category}%"))
    if start_date:
        query = query.filter(models.FinancialRecord.date >= start_date)
    if end_date:
        query = query.filter(models.FinancialRecord.date <= end_date)

    total = query.count()
    records = query.order_by(models.FinancialRecord.date.desc()) \
                   .offset((page - 1) * page_size) \
                   .limit(page_size) \
                   .all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "records": records
    }


@router.get("/{record_id}", response_model=schemas.RecordResponse)
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_any_role)
):
    """Get a single record by ID. All authenticated users can view."""
    return get_record_or_404(record_id, db)


@router.post("/", response_model=schemas.RecordResponse, status_code=201)
def create_record(
    data: schemas.RecordCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """
    Create a new financial record. Admin only.
    """
    record = models.FinancialRecord(
        amount=data.amount,
        type=data.type,
        category=data.category,
        date=data.date,
        notes=data.notes,
        created_by=current_user.id
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.patch("/{record_id}", response_model=schemas.RecordResponse)
def update_record(
    record_id: int,
    updates: schemas.RecordUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Update a financial record. Admin only."""
    record = get_record_or_404(record_id, db)

    if updates.amount is not None:
        record.amount = updates.amount
    if updates.type is not None:
        record.type = updates.type
    if updates.category is not None:
        record.category = updates.category
    if updates.date is not None:
        record.date = updates.date
    if updates.notes is not None:
        record.notes = updates.notes

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{record_id}", status_code=204)
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """
    Soft-delete a financial record. Admin only.
    The record is marked as deleted but remains in the database.
    """
    record = get_record_or_404(record_id, db)
    record.is_deleted = True
    db.commit()
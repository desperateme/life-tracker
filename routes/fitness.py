"""健身记录 CRUD"""
from datetime import date as date_type
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from logger import log
from auth import require_auth
from models import FitnessRecord

router = APIRouter()


@router.get("/fitness")
def fitness_page(request: Request, db: Session = Depends(get_db)):
    today = date_type.today()
    records = db.query(FitnessRecord).filter(
        FitnessRecord.date == today
    ).order_by(FitnessRecord.created_at.desc()).all()

    return request.app.state.templates.TemplateResponse("fitness.html", {
        "request": request,
        "records": records,
        "today": today.isoformat(),
    })


@router.post("/fitness")
def add_fitness(
    request: Request,
    db: Session = Depends(get_db),
    _auth=Depends(require_auth),
    exercise_type: str = Form(""),
    duration_minutes: int = Form(0),
    weight_kg: str = Form(""),
    notes: str = Form(""),
    record_date: str = Form(""),
):
    d = date_type.fromisoformat(record_date) if record_date else date_type.today()
    w = float(weight_kg) if weight_kg.strip() else None

    record = FitnessRecord(
        date=d,
        exercise_type=exercise_type,
        duration_minutes=min(duration_minutes, 120),
        weight_kg=w,
        notes=notes,
    )
    db.add(record)
    log("info", "健身", "新增记录", f"{exercise_type} | {duration_minutes}分钟")
    db.commit()

    from scoring import sync_daily_effort
    sync_daily_effort(db, d)

    return RedirectResponse(url="/fitness", status_code=303)


@router.post("/fitness/{record_id}/delete")
def delete_fitness(record_id: int, db: Session = Depends(get_db), _auth=Depends(require_auth)):
    record = db.query(FitnessRecord).filter(FitnessRecord.id == record_id).first()
    if record:
        db.delete(record)
        log("info", "健身", "删除记录", f"id={record_id}")
        db.commit()
        from scoring import sync_daily_effort
        sync_daily_effort(db, record.date)
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/fitness", status_code=303)

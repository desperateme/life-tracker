"""戒律记录 CRUD"""
from datetime import date as date_type
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from logger import log
from auth import require_auth
from models import DisciplineRecord

router = APIRouter()

HABIT_TYPES = ["垃圾食品", "含糖饮料", "自慰", "熬夜", "刷手机", "游戏", "其他"]


@router.get("/discipline")
def discipline_page(request: Request, db: Session = Depends(get_db)):
    today = date_type.today()
    records = db.query(DisciplineRecord).filter(
        DisciplineRecord.date == today
    ).order_by(DisciplineRecord.created_at.desc()).all()

    return request.app.state.templates.TemplateResponse("discipline.html", {
        "request": request,
        "records": records,
        "habit_types": HABIT_TYPES,
        "today": today.isoformat(),
    })


@router.post("/discipline")
def add_discipline(
    request: Request,
    db: Session = Depends(get_db),
    _auth=Depends(require_auth),
    habit_type: str = Form("其他"),
    count: int = Form(1),
    duration_minutes: str = Form(""),
    notes: str = Form(""),
    record_date: str = Form(""),
):
    d = date_type.fromisoformat(record_date) if record_date else date_type.today()
    dur = int(duration_minutes) if duration_minutes.strip() else None

    record = DisciplineRecord(
        date=d,
        habit_type=habit_type,
        count=count,
        duration_minutes=dur,
        notes=notes,
    )
    db.add(record)
    dur_str = f" {duration_minutes}分钟" if duration_minutes else ""
    log("info", "戒律", "记录破戒", f"{habit_type} x{count}{dur_str}")
    db.commit()

    from scoring import sync_daily_effort
    sync_daily_effort(db, d)

    return RedirectResponse(url="/discipline", status_code=303)


@router.post("/discipline/{record_id}/delete")
def delete_discipline(record_id: int, db: Session = Depends(get_db), _auth=Depends(require_auth)):
    record = db.query(DisciplineRecord).filter(DisciplineRecord.id == record_id).first()
    if record:
        db.delete(record)
        log("info", "戒律", "删除记录", f"id={record_id}")
        db.commit()
        from scoring import sync_daily_effort
        sync_daily_effort(db, record.date)
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/discipline", status_code=303)

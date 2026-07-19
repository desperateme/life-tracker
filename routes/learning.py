"""学习记录 CRUD"""
from datetime import date as date_type, datetime
from fastapi import APIRouter, Request, Depends, Form
from sqlalchemy.orm import Session
from database import get_db
from logger import log
from models import LearningRecord

router = APIRouter()


@router.get("/learning")
def learning_page(request: Request, db: Session = Depends(get_db)):
    today = date_type.today()
    records = db.query(LearningRecord).filter(
        LearningRecord.date == today
    ).order_by(LearningRecord.created_at.desc()).all()

    return request.app.state.templates.TemplateResponse("learning.html", {
        "request": request,
        "records": records,
        "today": today.isoformat(),
    })


@router.post("/learning")
def add_learning(
    request: Request,
    db: Session = Depends(get_db),
    topic: str = Form(""),
    description: str = Form(""),
    duration_minutes: int = Form(0),
    record_date: str = Form(""),
):
    d = date_type.fromisoformat(record_date) if record_date else date_type.today()

    record = LearningRecord(
        date=d,
        topic=topic,
        description=description,
        duration_minutes=min(duration_minutes, 180),
    )
    db.add(record)
    log("info", "学习", "新增记录", f"{topic} | {duration_minutes}分钟")
    db.commit()

    from scoring import sync_daily_effort
    sync_daily_effort(db, d)

    return learning_page(request, db)


@router.post("/learning/{record_id}/delete")
def delete_learning(record_id: int, db: Session = Depends(get_db)):
    record = db.query(LearningRecord).filter(LearningRecord.id == record_id).first()
    if record:
        db.delete(record)
        log("info", "学习", "删除记录", f"id={record_id}")
        db.commit()
        from scoring import sync_daily_effort
        sync_daily_effort(db, record.date)
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/learning", status_code=303)

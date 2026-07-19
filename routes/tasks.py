"""任务系统 CRUD + 逾期检测"""
from datetime import datetime, date as date_type
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import asc
from database import get_db
from logger import log
from models import TaskRecord

router = APIRouter()


@router.get("/tasks")
def tasks_page(request: Request, db: Session = Depends(get_db)):
    now = datetime.now()

    # 先标记所有逾期任务
    overdue = db.query(TaskRecord).filter(
        TaskRecord.deadline < now,
        TaskRecord.status == "待办"
    ).all()
    for t in overdue:
        t.status = "已逾期"
    if overdue:
        db.commit()

    # 逾期任务置顶，然后按截止时间排序
    overdue_tasks = db.query(TaskRecord).filter(
        TaskRecord.status == "已逾期"
    ).order_by(asc(TaskRecord.deadline)).all()

    pending_tasks = db.query(TaskRecord).filter(
        TaskRecord.status == "待办"
    ).order_by(asc(TaskRecord.deadline)).all()

    completed_tasks = db.query(TaskRecord).filter(
        TaskRecord.status == "已完成"
    ).order_by(TaskRecord.completed_at.desc()).limit(20).all()

    return request.app.state.templates.TemplateResponse("tasks.html", {
        "request": request,
        "overdue_tasks": overdue_tasks,
        "pending_tasks": pending_tasks,
        "completed_tasks": completed_tasks,
        "now": now,
    })


@router.post("/tasks")
def add_task(
    request: Request,
    db: Session = Depends(get_db),
    title: str = Form(""),
    description: str = Form(""),
    priority: str = Form("medium"),
    deadline: str = Form(""),
):
    dl = datetime.fromisoformat(deadline) if deadline else datetime.now()
    task = TaskRecord(
        title=title,
        description=description,
        priority=priority,
        deadline=dl,
    )
    db.add(task)
    log("info", "任务", "创建任务", f"{title} | 优先级={priority} | 截止={dl}")
    db.commit()

    from scoring import sync_daily_effort
    sync_daily_effort(db)

    return RedirectResponse(url="/tasks", status_code=303)


@router.post("/tasks/{task_id}/complete")
def complete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(TaskRecord).filter(TaskRecord.id == task_id).first()
    if task and task.status != "已完成":
        task.status = "已完成"
        log("info", "任务", "完成任务", f"id={task_id}")
        task.completed_at = datetime.now()
        db.commit()
        from scoring import sync_daily_effort
        sync_daily_effort(db)
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/tasks", status_code=303)


@router.post("/tasks/{task_id}/extend")
def extend_task(
    task_id: int,
    db: Session = Depends(get_db),
    new_deadline: str = Form(""),
):
    task = db.query(TaskRecord).filter(TaskRecord.id == task_id).first()
    if task and task.status != "已逾期" and new_deadline:
        task.deadline = datetime.fromisoformat(new_deadline)
        db.commit()
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/tasks", status_code=303)


@router.post("/tasks/{task_id}/delete")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(TaskRecord).filter(TaskRecord.id == task_id).first()
    if task:
        db.delete(task)
        log("info", "任务", "删除任务", f"id={task_id}")
        db.commit()
        from scoring import sync_daily_effort
        sync_daily_effort(db)
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/tasks", status_code=303)

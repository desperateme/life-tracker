"""赚钱记录 CRUD + 粉丝里程碑"""
from datetime import date as date_type
from fastapi import APIRouter, Request, Depends, Form
from sqlalchemy.orm import Session
from database import get_db
from logger import log
from models import EarningRecord, LifeProgress

router = APIRouter()


@router.get("/earning")
def earning_page(request: Request, db: Session = Depends(get_db)):
    today = date_type.today()
    records = db.query(EarningRecord).filter(
        EarningRecord.date == today
    ).order_by(EarningRecord.created_at.desc()).all()

    progress = db.query(LifeProgress).filter(LifeProgress.id == 1).first()

    return request.app.state.templates.TemplateResponse("earning.html", {
        "request": request,
        "records": records,
        "progress": progress,
        "today": today.isoformat(),
    })


@router.post("/earning")
def add_earning(
    request: Request,
    db: Session = Depends(get_db),
    platform: str = Form(""),
    activity_type: str = Form(""),
    description: str = Form(""),
    time_spent_minutes: int = Form(0),
    followers_gained: int = Form(0),
    revenue: float = Form(0.0),
    notes: str = Form(""),
    record_date: str = Form(""),
):
    d = date_type.fromisoformat(record_date) if record_date else date_type.today()

    record = EarningRecord(
        date=d,
        platform=platform,
        activity_type=activity_type,
        description=description,
        time_spent_minutes=min(time_spent_minutes, 180),
        followers_gained=followers_gained,
        revenue=revenue,
        notes=notes,
    )
    db.add(record)
    log("info", "赚钱", "新增记录", f"{platform} | {activity_type} | {time_spent_minutes}分钟 | +{followers_gained}粉")

    # 更新粉丝总数并检查里程碑
    if followers_gained > 0:
        progress = db.query(LifeProgress).filter(LifeProgress.id == 1).first()
        if progress:
            from scoring import check_follower_milestone
            progress.current_followers += followers_gained
            bonus, name = check_follower_milestone(
                progress.current_followers, progress.follower_milestones
            )
            if bonus and name:
                reached = set(progress.follower_milestones.split(",")) if progress.follower_milestones else set()
                reached.add(name)
                log("info", "里程碑", "达成粉丝里程碑", f"{name} | 奖励 +{bonus}")
                progress.follower_milestones = ",".join(sorted(reached))
                progress.total_effort += bonus
                # 记录到 request state 用于弹窗提示
                request.app.state.last_milestone = {
                    "type": "follower",
                    "name": name,
                    "bonus": bonus,
                }

    db.commit()

    from scoring import sync_daily_effort
    sync_daily_effort(db, d)

    return earning_page(request, db)


@router.post("/earning/{record_id}/delete")
def delete_earning(record_id: int, db: Session = Depends(get_db)):
    record = db.query(EarningRecord).filter(EarningRecord.id == record_id).first()
    if record:
        db.delete(record)
        log("info", "赚钱", "删除记录", f"id={record_id}")
        db.commit()
        from scoring import sync_daily_effort
        sync_daily_effort(db, record.date)
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/earning", status_code=303)


@router.post("/api/followers/update")
def update_followers(
    current_followers: int = Form(0),
    db: Session = Depends(get_db),
):
    from fastapi.responses import RedirectResponse
    from scoring import check_follower_milestone

    progress = db.query(LifeProgress).filter(LifeProgress.id == 1).first()
    if progress:
        old = progress.current_followers
        progress.current_followers = current_followers
        bonus, name = check_follower_milestone(current_followers, progress.follower_milestones)
        if bonus and name:
            reached = set(progress.follower_milestones.split(",")) if progress.follower_milestones else set()
            reached.add(name)
            progress.follower_milestones = ",".join(sorted(reached))
            progress.total_effort += bonus
            progress.current_followers = current_followers
            log("info", "里程碑", "达成粉丝里程碑", f"{name} | 奖励 +{bonus}")
        db.commit()
    return RedirectResponse(url="/earning", status_code=303)

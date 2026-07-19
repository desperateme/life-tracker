"""境界查询 + 趋势数据 + 历史记录"""
from datetime import date, timedelta
from fastapi import APIRouter, Request, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db

router = APIRouter()


@router.get("/api/progress")
def api_progress(db: Session = Depends(get_db)):
    from models import LifeProgress
    from scoring import get_realm_and_stage
    p = db.query(LifeProgress).filter(LifeProgress.id == 1).first()
    if not p:
        return {"error": "no progress"}
    realm_info = get_realm_and_stage(p.total_effort)
    return {
        "total_effort": p.total_effort,
        "target_effort": p.target_effort,
        "realm": realm_info,
        "streak_days": p.streak_days,
        "clean_streak_days": p.clean_streak_days,
        "current_followers": p.current_followers,
        "follower_milestones": p.follower_milestones,
        "current_savings": p.current_savings,
        "savings_milestones": p.savings_milestones,
    }


@router.get("/api/trend")
def api_trend(days: int = Query(default=30), db: Session = Depends(get_db)):
    """返回最近 N 天的每日努力值趋势（简化版：按记录日期聚合时长估算）"""
    from models import LearningRecord, FitnessRecord, EarningRecord, ExpenseRecord
    from scoring import minutes_to_score
    today = date.today()
    start = today - timedelta(days=days - 1)

    trend = []
    for i in range(days):
        d = start + timedelta(days=i)
        # 简化趋势：只统计正向维度
        learn_m = db.query(func.coalesce(func.sum(LearningRecord.duration_minutes), 0)) \
            .filter(LearningRecord.date == d).scalar()
        fit_m = db.query(func.coalesce(func.sum(FitnessRecord.duration_minutes), 0)) \
            .filter(FitnessRecord.date == d).scalar()
        earn_m = db.query(func.coalesce(func.sum(EarningRecord.time_spent_minutes), 0)) \
            .filter(EarningRecord.date == d).scalar()

        score = minutes_to_score(learn_m) + minutes_to_score(fit_m) + minutes_to_score(earn_m)

        # 财务加分
        has_fin = db.query(ExpenseRecord).filter(ExpenseRecord.date == d).first() is not None
        if has_fin:
            score += 5

        trend.append({"date": d.isoformat(), "score": score})

    return {"trend": trend}


@router.get("/history")
def history_page(
    request: Request,
    db: Session = Depends(get_db),
    month: str = Query(default=""),
):
    from models import LearningRecord, FitnessRecord, EarningRecord, DisciplineRecord, ExpenseRecord

    today = date.today()
    if month:
        y, m = month.split("-")
        year, mon = int(y), int(m)
    else:
        year, mon = today.year, today.month

    start_date = date(year, mon, 1)
    if mon == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, mon + 1, 1)

    # 获取该月所有有记录的日期
    dates_set = set()
    for model in [LearningRecord, FitnessRecord, EarningRecord, DisciplineRecord, ExpenseRecord]:
        rows = db.query(model.date).filter(
            model.date >= start_date, model.date < end_date
        ).distinct().all()
        for r in rows:
            dates_set.add(r[0])

    # 按日期排序并计算每日分数
    daily_scores = []
    for d in sorted(dates_set, reverse=True):
        learn_m = db.query(func.coalesce(func.sum(LearningRecord.duration_minutes), 0)) \
            .filter(LearningRecord.date == d).scalar()
        fit_m = db.query(func.coalesce(func.sum(FitnessRecord.duration_minutes), 0)) \
            .filter(FitnessRecord.date == d).scalar()
        earn_m = db.query(func.coalesce(func.sum(EarningRecord.time_spent_minutes), 0)) \
            .filter(EarningRecord.date == d).scalar()

        from scoring import minutes_to_score
        score = minutes_to_score(learn_m) + minutes_to_score(fit_m) + minutes_to_score(earn_m)

        daily_scores.append({
            "date": d.isoformat(),
            "learning_min": learn_m,
            "fitness_min": fit_m,
            "earning_min": earn_m,
            "score": score,
        })

    return request.app.state.templates.TemplateResponse("history.html", {
        "request": request,
        "daily_scores": daily_scores,
        "current_month": f"{year}-{mon:02d}",
    })

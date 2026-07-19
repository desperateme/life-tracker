"""仪表盘首页"""
from datetime import date
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from database import get_db
from logger import log
from scoring import calc_daily_score, sync_daily_effort

router = APIRouter()


@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    import traceback
    try:
        today = date.today()
        # 1. 结算所有「昨天及之前」未结算的日子
        sync_result = sync_daily_effort(db)
        if sync_result:
            log("info", "结算", "结算完成", "结算至 " + sync_result.get("synced_until", "?"))
        # 2. 实时计算今天的分数（只读，不锁死）
        result = calc_daily_score(db, today)
        # 如果今天刚结算了昨天，用最新进度重新算境界
        if sync_result and sync_result.get("breakthrough"):
            result["breakthrough"] = True
            result["realm"] = sync_result["realm"]

        from models import LifeProgress
        progress = db.query(LifeProgress).filter(LifeProgress.id == 1).first()

        # 里程碑信息
        follower_milestone = ""
        savings_milestone = ""
        if progress:
            from scoring import FOLLOWER_MILESTONES, SAVINGS_MILESTONES
            reached_f = set(progress.follower_milestones.split(",")) if progress.follower_milestones else set()
            for th, name, _ in FOLLOWER_MILESTONES:
                if name not in reached_f:
                    follower_milestone = str(progress.current_followers) + " / " + str(th)
                    break

            reached_s = set(progress.savings_milestones.split(",")) if progress.savings_milestones else set()
            for th, name, _ in SAVINGS_MILESTONES:
                if name not in reached_s:
                    savings_milestone = str(int(progress.current_savings)) + " / " + str(th)
                    break

        return request.app.state.templates.TemplateResponse("index.html", {
            "request": request,
            "result": result,
            "progress": progress,
            "follower_milestone": follower_milestone or (str(progress.current_followers if progress else 0) + " / 100000"),
            "savings_milestone": savings_milestone or (str(int(progress.current_savings if progress else 0)) + " / 50000"),
        })
    except Exception as e:
        return request.app.state.templates.TemplateResponse("index.html", {
            "request": request,
            "error": str(e) + "\n" + traceback.format_exc(),
            "result": {"learning":0,"fitness":0,"earning":0,"finance":0,"discipline":0,"total":0,"comment":"加载失败","realm":{"realm":"??","stage":"","color":"#666","emoji":"❌","progress_pct":0,"points_to_next":0,"next_realm":"?"},"streak_days":0,"clean_streak_days":0,"base_total":0,"streak_bonus":0,"is_clean":False,"overdue_tasks":0,"game_overtime":0,"breakthrough":False},
            "progress": None,
            "follower_milestone": "? / 100000",
            "savings_milestone": "? / 50000",
        })

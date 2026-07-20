"""努力值计算引擎 + 境界判定 + 里程碑检测"""
from datetime import date, datetime, timedelta
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from logger import log


# ===== 修仙境界定义 =====
REALMS = [
    {"name": "炼气", "start": 0, "end": 5000, "color": "#9e9e9e", "emoji": "⚪"},
    {"name": "筑基", "start": 5000, "end": 12500, "color": "#4caf50", "emoji": "🟢"},
    {"name": "金丹", "start": 12500, "end": 22500, "color": "#2196f3", "emoji": "🔵"},
    {"name": "元婴", "start": 22500, "end": 35000, "color": "#9c27b0", "emoji": "🟣"},
    {"name": "化神", "start": 35000, "end": 50000, "color": "#ff9800", "emoji": "🟡"},
]

STAGES = ["初期", "中期", "后期", "圆满"]
TARGET_EFFORT = 50000

# ===== 里程碑定义 =====
FOLLOWER_MILESTONES = [
    (100000, "10w", 500),
    (200000, "20w", 1000),
    (500000, "50w", 2500),
    (1000000, "100w", 5000),
]

SAVINGS_MILESTONES = [
    (50000, "5w", 300),
    (100000, "10w", 500),
    (200000, "20w", 1000),
    (500000, "50w", 2000),
    (1000000, "100w", 4000),
]


def minutes_to_score(minutes: int, step: int = 15, points_per_step: int = 5) -> int:
    """将分钟数转换为修为值：每 step 分钟 = points_per_step 点，向下取整"""
    return (minutes // step) * points_per_step


def calc_learning_score(db: Session, target_date: date) -> int:
    """计算学习维度修为"""
    from models import LearningRecord
    total_minutes = db.query(func.coalesce(func.sum(LearningRecord.duration_minutes), 0)) \
        .filter(LearningRecord.date == target_date).scalar()
    return minutes_to_score(total_minutes, step=15, points_per_step=5)


def calc_fitness_score(db: Session, target_date: date) -> int:
    """计算健身维度修为"""
    from models import FitnessRecord
    total_minutes = db.query(func.coalesce(func.sum(FitnessRecord.duration_minutes), 0)) \
        .filter(FitnessRecord.date == target_date).scalar()
    return minutes_to_score(total_minutes, step=15, points_per_step=5)


def calc_earning_score(db: Session, target_date: date) -> int:
    """计算赚钱维度修为"""
    from models import EarningRecord
    total_minutes = db.query(func.coalesce(func.sum(EarningRecord.time_spent_minutes), 0)) \
        .filter(EarningRecord.date == target_date).scalar()
    return minutes_to_score(total_minutes, step=15, points_per_step=5)


def calc_finance_score(db: Session, target_date: date) -> int:
    """计算财务维度修为：收入加分，支出扣分（每50元±5分）"""
    from models import ExpenseRecord, IncomeRecord
    total_expense = db.query(func.coalesce(func.sum(ExpenseRecord.amount), 0)) \
        .filter(ExpenseRecord.date == target_date).scalar()
    total_income = db.query(func.coalesce(func.sum(IncomeRecord.amount), 0)) \
        .filter(IncomeRecord.date == target_date).scalar()
    income_score = int(total_income // 50) * 5
    expense_score = int(total_expense // 50) * 5
    return income_score - expense_score


def get_realm_and_stage(effort: int) -> dict:
    """根据努力值获取当前境界信息"""
    for i, realm in enumerate(REALMS):
        if effort < realm["end"]:
            range_start = realm["start"]
            range_end = realm["end"]
            realm_size = range_end - range_start
            progress_in_realm = effort - range_start
            stage_index = min(progress_in_realm * 4 // realm_size, 3)
            progress_pct = round(progress_in_realm / realm_size * 100, 1)

            next_realm = REALMS[i + 1] if i + 1 < len(REALMS) else None

            return {
                "realm": realm["name"],
                "stage": STAGES[stage_index],
                "color": realm["color"],
                "emoji": realm["emoji"],
                "progress_pct": progress_pct,
                "realm_start": range_start,
                "realm_end": range_end,
                "points_in_realm": progress_in_realm,
                "points_to_next": range_end - effort,
                "next_realm": next_realm["name"] if next_realm else "飞升",
            }

    # 已飞升
    return {
        "realm": "飞升",
        "stage": "",
        "color": "#ffd700",
        "emoji": "🏆",
        "progress_pct": 100,
        "realm_start": 50000,
        "realm_end": 50000,
        "points_in_realm": 0,
        "points_to_next": 0,
        "next_realm": "已飞升",
    }


def check_breakthrough(progress, streak_days: int) -> bool:
    """检查是否可以突破大境界"""
    realm = progress["realm"]
    if realm == "飞升":
        return False
    # 达到当前境界圆满 + 连续3天努力值为正
    return progress["progress_pct"] >= 100 and streak_days >= 3


def check_follower_milestone(current: int, reached_str: str) -> Tuple[Optional[int], Optional[str]]:
    """检测是否达成新的粉丝里程碑，返回(奖励值, 里程碑名)"""
    reached = set()
    if reached_str:
        reached = set(reached_str.split(","))
    for threshold, name, bonus in FOLLOWER_MILESTONES:
        if current >= threshold and name not in reached:
            return bonus, name
    return None, None


def check_savings_milestone(current: float, reached_str: str) -> Tuple[Optional[int], Optional[str]]:
    """检测是否达成新的储蓄里程碑，返回(奖励值, 里程碑名)"""
    reached = set()
    if reached_str:
        reached = set(reached_str.split(","))
    for threshold, name, bonus in SAVINGS_MILESTONES:
        if current >= threshold and name not in reached:
            return bonus, name
    return None, None


def calc_streak_bonus(streak_days: int, clean_streak_days: int) -> int:
    """计算连续加成"""
    bonus = 0
    if streak_days >= 30:
        bonus += 30
    elif streak_days >= 7:
        bonus += 10
    elif streak_days >= 3:
        bonus += 5

    if clean_streak_days >= 30:
        bonus += 80
    elif clean_streak_days >= 7:
        bonus += 20

    return bonus


def get_daily_comment(score: int) -> str:
    """获取每日评语"""
    if score >= 120:
        return "今日修炼大成，天道酬勤 🔥🔥🔥"
    elif score >= 70:
        return "勤勉有加，仙途可期 ✨"
    elif score >= 30:
        return "略有懈怠，还需加把劲 💪"
    elif score >= 1:
        return "险些走火入魔，明日补过 ⚠️"
    elif score >= -30:
        return "道心蒙尘，修为倒退 💀"
    else:
        return "心魔肆虐，修为暴跌！！☠️"


def calc_daily_score(db: Session, target_date: date = None) -> dict:
    """
    纯计算每日分数，只读，不修改数据库
    可以反复调用，不会产生副作用
    """
    from models import LifeProgress, TaskRecord

    if target_date is None:
        target_date = date.today()

    learning = calc_learning_score(db, target_date)
    fitness = calc_fitness_score(db, target_date)
    earning = calc_earning_score(db, target_date)
    finance = calc_finance_score(db, target_date)

    # 戒律计算（含任务逾期检测，但不提交到 progress）
    discipline, is_clean, game_overtime = _calc_discipline_penalty(db, target_date)

    # 基础总分
    base_total = learning + fitness + earning + finance + discipline

    # 躺平惩罚
    if learning == 0 and fitness == 0 and earning == 0 and finance == 0 and discipline <= 0:
        base_total -= 20

    # 获取进度信息（只读）
    progress = db.query(LifeProgress).filter(LifeProgress.id == 1).first()
    streak_bonus = calc_streak_bonus(progress.streak_days if progress else 0,
                                     progress.clean_streak_days if progress else 0)

    total = base_total + streak_bonus
    realm_info = get_realm_and_stage(progress.total_effort if progress else 0)

    # 逾期任务数
    overdue_count = db.query(TaskRecord).filter(
        TaskRecord.status == "已逾期"
    ).count()

    comment = get_daily_comment(total)

    return {
        "date": target_date.isoformat(),
        "learning": learning,
        "fitness": fitness,
        "earning": earning,
        "finance": finance,
        "discipline": discipline,
        "base_total": base_total,
        "streak_bonus": streak_bonus,
        "total": total,
        "is_clean": is_clean,
        "game_overtime": game_overtime,
        "comment": comment,
        "realm": realm_info,
        "breakthrough": False,
        "streak_days": progress.streak_days if progress else 0,
        "clean_streak_days": progress.clean_streak_days if progress else 0,
        "overdue_tasks": overdue_count,
    }


def _calc_discipline_penalty(db: Session, target_date: date):
    """计算戒律惩罚（不含进度更新），返回 (score, is_clean, game_overtime)"""
    from models import DisciplineRecord, TaskRecord

    records = db.query(DisciplineRecord).filter(DisciplineRecord.date == target_date).all()
    bad_count = 0
    game_overtime_minutes = 0
    is_clean = True

    for r in records:
        if r.habit_type == "游戏":
            if r.duration_minutes and r.duration_minutes > 60:
                overtime = r.duration_minutes - 60
                game_overtime_minutes += overtime
                bad_count += 1
                is_clean = False
        else:
            bad_count += (r.count or 1)
            is_clean = False

    if bad_count >= 3:
        bad_penalty = -40
    elif bad_count == 2:
        bad_penalty = -20
    elif bad_count == 1:
        bad_penalty = -10
    else:
        bad_penalty = 0

    game_penalty = (game_overtime_minutes // 15) * -5 if game_overtime_minutes else 0

    # 任务逾期扣分
    now = datetime.now()
    penalty_map = {"high": -50, "medium": -30, "low": -20}
    task_penalty = 0

    overdue_tasks = db.query(TaskRecord).filter(
        TaskRecord.deadline < now,
        TaskRecord.status != "已完成",
        TaskRecord.penalty_applied == False
    ).all()

    for task in overdue_tasks:
        task.status = "已逾期"
        if task.deadline.date() <= target_date and not task.penalty_applied:
            task_penalty += penalty_map.get(task.priority, -30)
            task.penalty_applied = True

    if overdue_tasks:
        db.flush()

    clean_bonus = 10 if is_clean else 0
    return clean_bonus + bad_penalty + game_penalty + task_penalty, is_clean, game_overtime_minutes


def sync_daily_effort(db: Session, target_date: date = None):
    """
    结算所有未结算的「昨天及之前」的日子。
    当天（today）的分数只实时预览，不锁死；过了 24 点才会锁死昨天。

    如果 target_date 是已经被结算过的过去日期（补录场景），
    则单独重新计算该日分数并更新 DailySummary，同时向前传播连锁反应。

    调用时机：每次打开首页 / 增删记录时都可以调用，不会重复结算。
    """
    from models import LifeProgress, DailySummary

    if target_date is None:
        target_date = date.today()

    progress = db.query(LifeProgress).filter(LifeProgress.id == 1).first()
    if not progress:
        return None

    today = date.today()

    # 确定需要结算的日期范围
    if progress.last_effort_date is None:
        progress.last_effort_date = today - timedelta(days=1)
        progress.last_effort_amount = 0
        db.commit()
        return None

    last_date = progress.last_effort_date

    # ---- 补录旧日期：target_date 是已结算过的过去日期 ----
    if target_date < today and target_date <= last_date:
        _resync_single_day(db, progress, target_date)
        # 连锁结算该日期之后到昨天的所有日子（因为总分变化可能影响连续天数）
        _resync_forward(db, progress, target_date + timedelta(days=1), today - timedelta(days=1))
        return None

    # ---- 正常结算：从 last_date+1 到 yesterday ----
    start = last_date
    end = today - timedelta(days=1)

    breakthrough_occurred = False
    while start < end:
        start += timedelta(days=1)
        day_result = calc_daily_score(db, start)
        day_effort = day_result["total"]
        day_clean = day_result["is_clean"]

        log("info", "结算", f"结算 {start}", f"总分={day_effort} 学习={day_result['learning']} 戒律={day_result['discipline']}")
        existing = db.query(DailySummary).filter(DailySummary.date == start).first()
        if not existing:
            db.add(DailySummary(
                date=start,
                learning_score=day_result["learning"],
                fitness_score=day_result["fitness"],
                earning_score=day_result["earning"],
                finance_score=day_result["finance"],
                discipline_score=day_result["discipline"],
                streak_bonus=day_result["streak_bonus"],
                total_score=day_effort,
                is_clean=day_clean,
                comment=day_result["comment"],
            ))

        progress.total_effort += day_effort

        if day_effort > 0:
            progress.streak_days += 1
        else:
            progress.streak_days = 0

        if day_clean:
            progress.clean_streak_days += 1
        else:
            progress.clean_streak_days = 0

    progress.last_effort_date = end if end >= last_date else last_date
    if progress.total_effort < 0:
        progress.total_effort = 0

    realm_info = get_realm_and_stage(progress.total_effort)
    old_realm = progress.current_realm
    progress.current_realm = realm_info["realm"]
    progress.current_stage = realm_info["stage"]
    progress.updated_at = datetime.now()

    if realm_info["realm"] != old_realm and old_realm != "飞升" and realm_info["realm"] != "飞升":
        breakthrough_occurred = True
        progress.last_breakthrough_date = end

    db.commit()

    return {
        "synced_until": end.isoformat() if end >= last_date else last_date.isoformat(),
        "breakthrough": breakthrough_occurred,
        "realm": realm_info,
    }


def _resync_single_day(db: Session, progress, target_date: date):
    """重新结算单个已结算日期的分数，更新 total_effort 差值"""
    from models import DailySummary

    day_result = calc_daily_score(db, target_date)
    new_score = day_result["total"]
    new_clean = day_result["is_clean"]

    existing = db.query(DailySummary).filter(DailySummary.date == target_date).first()
    old_score = existing.total_score if existing else 0

    if existing:
        existing.learning_score = day_result["learning"]
        existing.fitness_score = day_result["fitness"]
        existing.earning_score = day_result["earning"]
        existing.finance_score = day_result["finance"]
        existing.discipline_score = day_result["discipline"]
        existing.streak_bonus = day_result["streak_bonus"]
        existing.total_score = new_score
        existing.is_clean = new_clean
        existing.comment = day_result["comment"]
    else:
        db.add(DailySummary(
            date=target_date,
            learning_score=day_result["learning"],
            fitness_score=day_result["fitness"],
            earning_score=day_result["earning"],
            finance_score=day_result["finance"],
            discipline_score=day_result["discipline"],
            streak_bonus=day_result["streak_bonus"],
            total_score=new_score,
            is_clean=new_clean,
            comment=day_result["comment"],
        ))

    delta = new_score - old_score
    if delta != 0:
        progress.total_effort += delta
        if progress.total_effort < 0:
            progress.total_effort = 0
        log("info", "补录", f"重算 {target_date}", f"旧分={old_score} 新分={new_score} 差值={delta}")

    db.flush()


def _resync_forward(db: Session, progress, from_date: date, to_date: date):
    """从 from_date 到 to_date 逐日重新结算（处理补录后的连锁反应）"""
    from models import DailySummary

    d = from_date - timedelta(days=1)
    while d < to_date:
        d += timedelta(days=1)
        _resync_single_day(db, progress, d)

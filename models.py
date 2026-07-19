"""SQLAlchemy ORM 模型 — 10 张表"""
from datetime import date as date_type
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, Boolean, func
from database import Base


class LearningRecord(Base):
    __tablename__ = "learning_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, default=func.current_date(), nullable=False)
    topic = Column(String(100), default="")
    description = Column(Text, default="")
    duration_minutes = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now())


class FitnessRecord(Base):
    __tablename__ = "fitness_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, default=func.current_date(), nullable=False)
    exercise_type = Column(String(50), default="")
    duration_minutes = Column(Integer, default=0, nullable=False)
    weight_kg = Column(Float, nullable=True)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=func.now())


class DisciplineRecord(Base):
    __tablename__ = "discipline_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, default=func.current_date(), nullable=False)
    habit_type = Column(String(30), nullable=False)
    count = Column(Integer, default=1)
    duration_minutes = Column(Integer, nullable=True)  # 仅游戏类
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=func.now())


class TaskRecord(Base):
    __tablename__ = "task_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    priority = Column(String(10), default="medium")  # high / medium / low
    deadline = Column(DateTime, nullable=False)
    status = Column(String(15), default="待办")  # 待办 / 已完成 / 已逾期
    penalty_applied = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())


class EarningRecord(Base):
    __tablename__ = "earning_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, default=func.current_date(), nullable=False)
    platform = Column(String(50), default="")
    activity_type = Column(String(50), default="")
    description = Column(Text, default="")
    time_spent_minutes = Column(Integer, default=0, nullable=False)
    followers_gained = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=func.now())


class ExpenseRecord(Base):
    __tablename__ = "expense_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, default=func.current_date(), nullable=False)
    category = Column(String(30), default="其他")
    amount = Column(Float, default=0.0, nullable=False)
    description = Column(String(200), default="")
    created_at = Column(DateTime, default=func.now())


class IncomeRecord(Base):
    __tablename__ = "income_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, default=func.current_date(), nullable=False)
    source = Column(String(50), default="其他")
    amount = Column(Float, default=0.0, nullable=False)
    description = Column(String(200), default="")
    created_at = Column(DateTime, default=func.now())


class BorrowRecord(Base):
    __tablename__ = "borrow_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, default=func.current_date(), nullable=False)
    type = Column(String(20), default="我欠别人")  # 我欠别人 / 别人欠我
    person = Column(String(50), default="")
    amount = Column(Float, default=0.0, nullable=False)
    repaid_amount = Column(Float, default=0.0)
    status = Column(String(20), default="未还清")
    due_date = Column(Date, nullable=True)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=func.now())


class InvestmentRecord(Base):
    __tablename__ = "investment_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, default=func.current_date(), nullable=False)
    invest_type = Column(String(30), default="其他")
    name = Column(String(100), default="")
    buy_price = Column(Float, default=0.0)
    current_value = Column(Float, default=0.0)
    status = Column(String(10), default="持有中")
    sell_price = Column(Float, nullable=True)
    profit_loss = Column(Float, nullable=True)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=func.now())


class LifeProgress(Base):
    __tablename__ = "life_progress"

    id = Column(Integer, primary_key=True, default=1)
    total_effort = Column(Integer, default=0)
    target_effort = Column(Integer, default=50000)
    current_realm = Column(String(20), default="炼气")
    current_stage = Column(String(10), default="初期")
    current_followers = Column(Integer, default=0)
    follower_milestones = Column(String(200), default="")
    current_savings = Column(Float, default=0.0)
    savings_milestones = Column(String(200), default="")
    streak_days = Column(Integer, default=0)
    clean_streak_days = Column(Integer, default=0)
    last_effort_date = Column(Date, nullable=True)
    last_effort_amount = Column(Integer, default=0)
    last_breakthrough_date = Column(Date, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class DailySummary(Base):
    """每日结算记录 — 过了24点后锁死并存入"""
    __tablename__ = "daily_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True, nullable=False)
    learning_score = Column(Integer, default=0)
    fitness_score = Column(Integer, default=0)
    earning_score = Column(Integer, default=0)
    finance_score = Column(Integer, default=0)
    discipline_score = Column(Integer, default=0)
    streak_bonus = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    is_clean = Column(Boolean, default=False)
    comment = Column(String(100), default="")
    created_at = Column(DateTime, default=func.now())

"""Pydantic 请求/响应模型"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


# ===== 学习 =====
class LearningCreate(BaseModel):
    date: Optional[str] = None
    topic: str = ""
    description: str = ""
    duration_minutes: int = Field(ge=0, le=180, default=0)


# ===== 健身 =====
class FitnessCreate(BaseModel):
    date: Optional[str] = None
    exercise_type: str = ""
    duration_minutes: int = Field(ge=0, le=120, default=0)
    weight_kg: Optional[float] = None
    notes: str = ""


# ===== 戒律 =====
class DisciplineCreate(BaseModel):
    date: Optional[str] = None
    habit_type: str = "其他"
    count: int = Field(ge=1, default=1)
    duration_minutes: Optional[int] = None
    notes: str = ""


# ===== 任务 =====
class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"  # high / medium / low
    deadline: str  # "YYYY-MM-DDTHH:MM"


class TaskExtend(BaseModel):
    new_deadline: str


# ===== 赚钱 =====
class EarningCreate(BaseModel):
    date: Optional[str] = None
    platform: str = ""
    activity_type: str = ""
    description: str = ""
    time_spent_minutes: int = Field(ge=0, le=180, default=0)
    followers_gained: int = Field(ge=0, default=0)
    revenue: float = Field(ge=0, default=0.0)
    notes: str = ""


# ===== 财务 =====
class ExpenseCreate(BaseModel):
    date: Optional[str] = None
    category: str = "其他"
    amount: float = Field(gt=0)
    description: str = ""


class IncomeCreate(BaseModel):
    date: Optional[str] = None
    source: str = "其他"
    amount: float = Field(gt=0)
    description: str = ""


class BorrowCreate(BaseModel):
    date: Optional[str] = None
    type: str = "我欠别人"
    person: str
    amount: float = Field(gt=0)
    due_date: Optional[str] = None
    notes: str = ""


class BorrowRepay(BaseModel):
    amount: float = Field(gt=0)


class InvestmentCreate(BaseModel):
    date: Optional[str] = None
    invest_type: str = "其他"
    name: str
    buy_price: float = Field(gt=0)
    current_value: Optional[float] = None
    notes: str = ""


class InvestmentUpdate(BaseModel):
    current_value: float = Field(ge=0)


# ===== 里程碑 =====
class FollowersUpdate(BaseModel):
    current_followers: int = Field(ge=0)


class SavingsUpdate(BaseModel):
    current_savings: float = Field(ge=0)

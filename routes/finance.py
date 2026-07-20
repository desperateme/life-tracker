"""财务管理 — 支出/收入/借贷/投资 + 储蓄里程碑"""
from datetime import date as date_type, datetime, timedelta
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from logger import log
from auth import require_auth
from models import ExpenseRecord, IncomeRecord, BorrowRecord, InvestmentRecord, LifeProgress

router = APIRouter()

CATEGORIES = ["餐饮", "交通", "购物", "娱乐", "房租", "水电", "学习", "医疗", "其他"]
INVEST_TYPES = ["股票", "基金", "加密货币", "定期", "其他"]


@router.get("/finance")
def finance_page(request: Request, db: Session = Depends(get_db)):
    today = date_type.today()
    month_start = today.replace(day=1)

    # 本月汇总
    total_expense = db.query(func.coalesce(func.sum(ExpenseRecord.amount), 0)) \
        .filter(ExpenseRecord.date >= month_start, ExpenseRecord.date <= today).scalar()
    total_income = db.query(func.coalesce(func.sum(IncomeRecord.amount), 0)) \
        .filter(IncomeRecord.date >= month_start, IncomeRecord.date <= today).scalar()

    today_expenses = db.query(ExpenseRecord).filter(ExpenseRecord.date == today) \
        .order_by(ExpenseRecord.created_at.desc()).all()
    today_incomes = db.query(IncomeRecord).filter(IncomeRecord.date == today) \
        .order_by(IncomeRecord.created_at.desc()).all()

    borrows = db.query(BorrowRecord).order_by(BorrowRecord.status.asc(), BorrowRecord.created_at.desc()).all()
    investments = db.query(InvestmentRecord).filter(InvestmentRecord.status == "持有中") \
        .order_by(InvestmentRecord.created_at.desc()).all()

    progress = db.query(LifeProgress).filter(LifeProgress.id == 1).first()

    return request.app.state.templates.TemplateResponse("finance.html", {
        "request": request,
        "total_expense": total_expense or 0,
        "total_income": total_income or 0,
        "today_expenses": today_expenses,
        "today_incomes": today_incomes,
        "borrows": borrows,
        "investments": investments,
        "categories": CATEGORIES,
        "invest_types": INVEST_TYPES,
        "progress": progress,
        "today": today.isoformat(),
    })


# ===== 支出 =====
@router.post("/finance/expense")
def add_expense(
    request: Request,
    db: Session = Depends(get_db),
    _auth=Depends(require_auth),
    category: str = Form("其他"),
    amount: float = Form(0),
    description: str = Form(""),
    record_date: str = Form(""),
):
    d = date_type.fromisoformat(record_date) if record_date else date_type.today()
    db.add(ExpenseRecord(date=d, category=category, amount=amount, description=description))
    log("info", "财务", "记支出", f"{category} | ¥{amount} | {description}")
    db.commit()
    from scoring import sync_daily_effort
    sync_daily_effort(db, d)
    return RedirectResponse(url="/finance", status_code=303)


@router.post("/finance/expense/{record_id}/delete")
def delete_expense(record_id: int, db: Session = Depends(get_db), _auth=Depends(require_auth)):
    record = db.query(ExpenseRecord).filter(ExpenseRecord.id == record_id).first()
    if record:
        db.delete(record)
        db.commit()
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/finance", status_code=303)


# ===== 收入 =====
@router.post("/finance/income")
def add_income(
    request: Request,
    db: Session = Depends(get_db),
    _auth=Depends(require_auth),
    source: str = Form("其他"),
    amount: float = Form(0),
    description: str = Form(""),
    record_date: str = Form(""),
):
    d = date_type.fromisoformat(record_date) if record_date else date_type.today()
    db.add(IncomeRecord(date=d, source=source, amount=amount, description=description))
    log("info", "财务", "记收入", f"{source} | ¥{amount} | {description}")

    # 更新储蓄并检查里程碑
    progress = db.query(LifeProgress).filter(LifeProgress.id == 1).first()
    if progress:
        progress.current_savings += amount
        from scoring import check_savings_milestone
        bonus, name = check_savings_milestone(progress.current_savings, progress.savings_milestones)
        if bonus and name:
            reached = set(progress.savings_milestones.split(",")) if progress.savings_milestones else set()
            reached.add(name)
            log("info", "里程碑", "达成储蓄里程碑", f"{name} | 奖励 +{bonus}")
            progress.savings_milestones = ",".join(sorted(reached))
            progress.total_effort += bonus

    db.commit()
    from scoring import sync_daily_effort
    sync_daily_effort(db, d)
    return RedirectResponse(url="/finance", status_code=303)


@router.post("/finance/income/{record_id}/delete")
def delete_income(record_id: int, db: Session = Depends(get_db), _auth=Depends(require_auth)):
    record = db.query(IncomeRecord).filter(IncomeRecord.id == record_id).first()
    if record:
        db.delete(record)
        db.commit()
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/finance", status_code=303)


# ===== 借贷 =====
@router.post("/finance/borrow")
def add_borrow(
    request: Request,
    db: Session = Depends(get_db),
    _auth=Depends(require_auth),
    type: str = Form("我欠别人"),
    person: str = Form(""),
    amount: float = Form(0),
    due_date: str = Form(""),
    notes: str = Form(""),
    record_date: str = Form(""),
):
    d = date_type.fromisoformat(record_date) if record_date else date_type.today()
    dd = date_type.fromisoformat(due_date) if due_date else None
    db.add(BorrowRecord(date=d, type=type, person=person, amount=amount, due_date=dd, notes=notes))
    log("info", "财务", "新增借贷", f"{type} | {person} | ¥{amount}")
    db.commit()
    return RedirectResponse(url="/finance", status_code=303)


@router.post("/finance/borrow/{record_id}/repay")
def repay_borrow(
    record_id: int,
    db: Session = Depends(get_db),
    _auth=Depends(require_auth),
    amount: float = Form(0),
):
    record = db.query(BorrowRecord).filter(BorrowRecord.id == record_id).first()
    if record and amount > 0:
        record.repaid_amount += amount
        if record.repaid_amount >= record.amount:
            record.status = "已还清"
            record.repaid_amount = record.amount
        db.commit()
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/finance", status_code=303)


@router.post("/finance/borrow/{record_id}/delete")
def delete_borrow(record_id: int, db: Session = Depends(get_db), _auth=Depends(require_auth)):
    record = db.query(BorrowRecord).filter(BorrowRecord.id == record_id).first()
    if record:
        db.delete(record)
        db.commit()
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/finance", status_code=303)


# ===== 投资 =====
@router.post("/finance/investment")
def add_investment(
    request: Request,
    db: Session = Depends(get_db),
    _auth=Depends(require_auth),
    invest_type: str = Form("其他"),
    name: str = Form(""),
    buy_price: float = Form(0),
    current_value: float = Form(0),
    notes: str = Form(""),
    record_date: str = Form(""),
):
    d = date_type.fromisoformat(record_date) if record_date else date_type.today()
    cv = current_value if current_value > 0 else buy_price
    log("info", "财务", "新增投资", f"{invest_type} | {name} | ¥{buy_price}")
    db.add(InvestmentRecord(
        date=d, invest_type=invest_type, name=name,
        buy_price=buy_price, current_value=cv, notes=notes,
    ))
    db.commit()
    return RedirectResponse(url="/finance", status_code=303)


@router.post("/finance/investment/{record_id}/update")
def update_investment(
    record_id: int,
    db: Session = Depends(get_db),
    _auth=Depends(require_auth),
    current_value: float = Form(0),
):
    record = db.query(InvestmentRecord).filter(InvestmentRecord.id == record_id).first()
    if record:
        record.current_value = current_value
        db.commit()
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/finance", status_code=303)


@router.post("/finance/investment/{record_id}/sell")
def sell_investment(
    record_id: int,
    db: Session = Depends(get_db),
    _auth=Depends(require_auth),
    sell_price: float = Form(0),
):
    record = db.query(InvestmentRecord).filter(InvestmentRecord.id == record_id).first()
    if record:
        record.status = "已卖出"
        record.sell_price = sell_price
        record.profit_loss = sell_price - record.buy_price
        db.commit()
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/finance", status_code=303)


@router.post("/finance/investment/{record_id}/delete")
def delete_investment(record_id: int, db: Session = Depends(get_db), _auth=Depends(require_auth)):
    record = db.query(InvestmentRecord).filter(InvestmentRecord.id == record_id).first()
    if record:
        db.delete(record)
        db.commit()
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/finance", status_code=303)


# ===== 储蓄更新 =====
@router.post("/api/savings/update")
def update_savings(
    current_savings: float = Form(0),
    db: Session = Depends(get_db),
    _auth=Depends(require_auth),
):
    from fastapi.responses import RedirectResponse
    from scoring import check_savings_milestone

    progress = db.query(LifeProgress).filter(LifeProgress.id == 1).first()
    if progress:
        progress.current_savings = current_savings
        bonus, name = check_savings_milestone(current_savings, progress.savings_milestones)
        if bonus and name:
            reached = set(progress.savings_milestones.split(",")) if progress.savings_milestones else set()
            reached.add(name)
            progress.savings_milestones = ",".join(sorted(reached))
            progress.total_effort += bonus
            log("info", "里程碑", "达成储蓄里程碑", f"{name} | 奖励 +{bonus}")
        db.commit()
    return RedirectResponse(url="/finance", status_code=303)


# ===== 财务数据 API（供图表使用）=====
@router.get("/api/finance/summary")
def api_finance_summary(db: Session = Depends(get_db)):
    """返回财务汇总数据 JSON"""
    today = date_type.today()
    month_start = today.replace(day=1)
    delta = timedelta

    total_expense = db.query(func.coalesce(func.sum(ExpenseRecord.amount), 0)) \
        .filter(ExpenseRecord.date >= month_start, ExpenseRecord.date <= today).scalar() or 0
    total_income = db.query(func.coalesce(func.sum(IncomeRecord.amount), 0)) \
        .filter(IncomeRecord.date >= month_start, IncomeRecord.date <= today).scalar() or 0

    cat_rows = db.query(ExpenseRecord.category, func.sum(ExpenseRecord.amount).label("total")) \
        .filter(ExpenseRecord.date >= month_start, ExpenseRecord.date <= today) \
        .group_by(ExpenseRecord.category).order_by(func.sum(ExpenseRecord.amount).desc()).all()
    categories = [{"name": r[0], "total": float(r[1])} for r in cat_rows]

    daily_data = []
    for i in range(29, -1, -1):
        d = today - delta(days=i)
        de = db.query(func.coalesce(func.sum(ExpenseRecord.amount), 0)) \
            .filter(ExpenseRecord.date == d).scalar() or 0
        di = db.query(func.coalesce(func.sum(IncomeRecord.amount), 0)) \
            .filter(IncomeRecord.date == d).scalar() or 0
        daily_data.append({"date": d.isoformat(), "expense": float(de), "income": float(di)})

    progress = db.query(LifeProgress).filter(LifeProgress.id == 1).first()
    savings = float(progress.current_savings) if progress else 0

    expenses = db.query(ExpenseRecord).order_by(ExpenseRecord.date.desc(), ExpenseRecord.created_at.desc()).limit(50).all()
    incomes = db.query(IncomeRecord).order_by(IncomeRecord.date.desc(), IncomeRecord.created_at.desc()).limit(50).all()
    transactions = []
    for e in expenses:
        transactions.append({"date": str(e.date), "type": "支出", "category": e.category, "desc": e.description or "", "amount": float(e.amount)})
    for inc in incomes:
        transactions.append({"date": str(inc.date), "type": "收入", "category": inc.source or "其他", "desc": inc.description or "", "amount": float(inc.amount)})
    transactions.sort(key=lambda x: x["date"], reverse=True)

    return {
        "total_expense": float(total_expense), "total_income": float(total_income),
        "net": float(total_income) - float(total_expense), "savings": savings,
        "categories": categories, "daily": daily_data, "transactions": transactions[:50],
    }

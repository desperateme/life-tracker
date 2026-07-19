"""数据库连接和初始化"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Railway 会自动注入 DATABASE_URL（PostgreSQL），本地开发用 SQLite
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # PostgreSQL: Railway 提供的连接字符串
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL, echo=False)
else:
    # SQLite: 本地开发
    DATA_DIR = "/data" if os.path.isdir("/data") else "."
    engine = create_engine(
        f"sqlite:///{DATA_DIR}/life_tracker.db",
        echo=False,
        connect_args={"check_same_thread": False},
    )

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def init_db():
    """创建所有表，并初始化 life_progress 默认行"""
    from models import LifeProgress  # noqa: F811
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if not db.query(LifeProgress).filter(LifeProgress.id == 1).first():
            db.add(LifeProgress(id=1))
            db.commit()
    finally:
        db.close()


def get_db():
    """FastAPI 依赖注入"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

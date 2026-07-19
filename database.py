"""数据库连接和初始化"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

import os
# Railway 提供持久化目录 /data，本地用当前目录
DATA_DIR = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", ".")
DATABASE_URL = f"sqlite:///{DATA_DIR}/life_tracker.db"

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
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

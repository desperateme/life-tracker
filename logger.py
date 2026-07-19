"""全局日志系统 — 所有操作记录到 logs/ 目录"""
import logging
import os
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"

# 操作日志
op_logger = logging.getLogger("life_tracker")
op_logger.setLevel(logging.DEBUG)

# 文件 handler — 每天一个日志文件
if not op_logger.handlers:
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = LOG_DIR / f"tracker_{datetime.now().strftime('%Y%m%d')}.log"
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-5s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    op_logger.addHandler(fh)

    # 控制台 handler（仅英文，避免 Windows GBK 乱码）
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)  # 控制台只显示警告和错误
    ch.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s", datefmt="%H:%M:%S"
    ))
    op_logger.addHandler(ch)


def log(level: str, module: str, action: str, detail: str = ""):
    """统一日志接口"""
    msg = f"[{module}] {action}"
    if detail:
        msg += f" | {detail}"
    getattr(op_logger, level)(msg)

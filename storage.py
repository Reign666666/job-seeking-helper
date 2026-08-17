"""本地存储：模型配置 + 分析历史。

全部数据落在项目目录 data/ 下，不设账号、无云同步。
config.json   —— 大模型配置（含 API Key，仅本机）
history.json  —— 分析历史记录（可一键清除）
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

from llm import LLMConfig

DATA_DIR = Path(__file__).resolve().parent / "data"
CONFIG_PATH = DATA_DIR / "config.json"
HISTORY_PATH = DATA_DIR / "history.json"

_lock = threading.Lock()


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def _write_json(path: Path, data) -> None:
    _ensure_dir()
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


# ---------------- 配置 ----------------

def load_config() -> LLMConfig:
    """配置优先级：UI 保存的 config.json ＞ 环境变量 ＞ 默认值。

    UI（模型设置弹窗）是 Base URL / 模型名 / API Key 的唯一入口；
    环境变量仅在 config.json 缺失或对应字段为空时兜底（如云端部署时
    API Key 由 PM_SCOUT_API_KEY 提供，避免进入代码仓库）。
    """
    cfg = _read_json(CONFIG_PATH, {})
    return LLMConfig(
        base_url=cfg.get("base_url") or os.environ.get("PM_SCOUT_BASE_URL") or "https://api.deepseek.com/v1",
        api_key=cfg.get("api_key") or os.environ.get("PM_SCOUT_API_KEY") or "",
        model=cfg.get("model") or os.environ.get("PM_SCOUT_MODEL") or "deepseek-chat",
    )


def save_config(cfg: LLMConfig) -> None:
    with _lock:
        _write_json(CONFIG_PATH, asdict(cfg))


def config_public() -> dict:
    """返回给前端的配置（Key 打码）。"""
    cfg = load_config()
    key = cfg.api_key
    masked = (key[:4] + "****" + key[-4:]) if len(key) > 8 else ("已设置" if key else "")
    return {
        "base_url": cfg.base_url,
        "model": cfg.model,
        "api_key_masked": masked,
        "ready": cfg.is_ready(),
    }


# ---------------- 历史 ----------------

@dataclass
class HistoryItem:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    time: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    score: int = 0
    tier: str = ""
    jd_excerpt: str = ""
    sanitized: bool = True
    resume_text: str = ""
    jd_text: str = ""
    result: dict = field(default_factory=dict)


def add_history(item: HistoryItem) -> None:
    with _lock:
        items = _read_json(HISTORY_PATH, [])
        items.insert(0, asdict(item))
        items = items[:200]  # 最多保留 200 条
        _write_json(HISTORY_PATH, items)


def list_history() -> list[dict]:
    items = _read_json(HISTORY_PATH, [])
    return [
        {
            "id": it.get("id"),
            "time": it.get("time"),
            "score": it.get("score"),
            "tier": it.get("tier"),
            "jd_excerpt": it.get("jd_excerpt", ""),
            "sanitized": it.get("sanitized", True),
        }
        for it in items
    ]


def get_history(item_id: str) -> dict | None:
    for it in _read_json(HISTORY_PATH, []):
        if it.get("id") == item_id:
            return it
    return None


def delete_history(item_id: str) -> bool:
    with _lock:
        items = _read_json(HISTORY_PATH, [])
        remaining = [it for it in items if it.get("id") != item_id]
        if len(remaining) == len(items):
            return False
        _write_json(HISTORY_PATH, remaining)
        return True


def clear_history() -> int:
    with _lock:
        items = _read_json(HISTORY_PATH, [])
        count = len(items)
        if items:
            _write_json(HISTORY_PATH, [])
        return count

"""PM 智投 · 第一期 · 本地网页服务

一条命令启动：  python main.py
浏览器自动打开 http://127.0.0.1:8765
"""
from __future__ import annotations

import os
import webbrowser
import threading

from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import llm as llm_mod
import parsers
import prompts
import sanitize
import storage
from llm import LLMConfig

APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(APP_DIR, "static")
# 本地默认 127.0.0.1:8765；云端部署通过环境变量覆盖（PM_SCOUT_HOST / PORT / PM_SCOUT_PORT）
HOST = os.environ.get("PM_SCOUT_HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", os.environ.get("PM_SCOUT_PORT", "8765")))

app = FastAPI(title="PM 智投", docs_url=None, redoc_url=None)

# 本地工具：放开 CORS，避免从预览面板/其他端口打开页面时被浏览器拦截
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态资源（前端页面）
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/api/health")
def health():
    return {"ok": True, "service": "pm-scout", "version": "0.1.0"}


# ---------------- 配置 ----------------

@app.get("/api/config")
def get_config():
    return storage.config_public()


class ConfigIn(BaseModel):
    base_url: str = Field(default="https://api.deepseek.com/v1", max_length=300)
    api_key: str = Field(default="", max_length=200)
    model: str = Field(default="deepseek-chat", max_length=100)


@app.post("/api/config")
def set_config(body: ConfigIn):
    cfg = LLMConfig(
        base_url=(body.base_url or "https://api.deepseek.com/v1").strip(),
        api_key=body.api_key.strip(),
        model=(body.model or "deepseek-chat").strip(),
    )
    if not cfg.api_key:
        raise HTTPException(400, "API Key 不能为空")
    storage.save_config(cfg)
    return {"ok": True, **storage.config_public()}


@app.post("/api/test_llm")
def test_llm():
    cfg = storage.load_config()
    if not cfg.is_ready():
        raise HTTPException(400, "尚未配置 API Key")
    try:
        msg = llm_mod.ping(cfg)
        return {"ok": True, "message": msg}
    except llm_mod.LLMError as e:
        raise HTTPException(502, str(e))


# ---------------- 简历解析 ----------------

@app.post("/api/parse_resume")
async def parse_resume(file: UploadFile = File(...)):
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(400, "文件超过 10MB 上限")
    try:
        text = parsers.extract_text(file.filename or "", data)
    except parsers.ParseError as e:
        raise HTTPException(400, str(e))
    summary = sanitize.sanitize_preview(text)
    return {
        "filename": file.filename,
        "chars": len(text),
        "sensitive": summary["sensitive"],
        "sanitized_text": summary["sanitized_text"],
        "preview": summary["preview"],
        "text": text,
    }


# ---------------- 核心分析 ----------------

class AnalyzeIn(BaseModel):
    resume_text: str = Field(min_length=20, max_length=30000)
    jd_text: str = Field(min_length=20, max_length=12000)
    sanitize: bool = True
    mask_name: bool = True


def _safe_int(v) -> int:
    """模型可能返回 87 / '87' / '87.5' / '87分' 等，一律安全转 int。"""
    if isinstance(v, bool):
        return int(v)
    try:
        return int(float(str(v).strip().rstrip("分")))
    except (TypeError, ValueError):
        return 0


def _normalize_result(data: dict) -> dict:
    """对模型输出做兜底规范化，确保前端渲染不崩。"""
    match = data.get("match") or {}
    dims = match.get("dimensions") or []
    if not isinstance(dims, list):
        dims = list(dims.values()) if isinstance(dims, dict) else []
    if len(dims) != 5:
        default_names = ["硬技能", "经验", "行业", "方向", "软性"]
        weights = [0.30, 0.25, 0.15, 0.15, 0.15]
        dims = [
            d if isinstance(d, dict) and d.get("name") else {
                "name": default_names[i] if i < 5 else f"维度{i+1}",
                "weight": weights[i] if i < 5 else 0.2,
                "score": _safe_int((d or {}).get("score", 60)) if isinstance(d, dict) else 60,
                "evidence": (d or {}).get("evidence", "") if isinstance(d, dict) else "",
                "gap": (d or {}).get("gap", "") if isinstance(d, dict) else "",
            }
            for i, d in enumerate(dims)
        ][:5]
    data.setdefault("match", {})
    data["match"]["dimensions"] = dims
    data["match"]["score"] = _safe_int(match.get("score", 0))
    data["match"]["tier"] = match.get("tier") or ("recommend" if data["match"]["score"] >= 85 else "watch")
    data.setdefault("resume_tips", {"keywords": {"hit": [], "miss": [], "suggest": []}, "rewrites": [], "highlights": [], "cuts": []})
    data.setdefault("greetings", {"concise": "", "professional": "", "enthusiastic": ""})
    data.setdefault("interview", {"questions": [], "probe_points": [], "materials": []})
    return data


@app.post("/api/analyze")
def analyze(body: AnalyzeIn):
    cfg = storage.load_config()
    if not cfg.is_ready():
        raise HTTPException(400, "尚未配置大模型 API Key，请先点击右上角「模型设置」完成配置。")

    resume_text = body.resume_text.strip()
    jd_text = body.jd_text.strip()

    if body.sanitize:
        used_text, hits = sanitize.sanitize(resume_text, mask_name=body.mask_name)
    else:
        used_text, hits = resume_text, []

    try:
        data = llm_mod.chat(cfg, prompts.SYSTEM_PROMPT, prompts.build_user_prompt(used_text, jd_text))
    except llm_mod.LLMError as e:
        raise HTTPException(502, str(e))

    try:
        data = _normalize_result(data)
        score = _safe_int((data.get("match") or {}).get("score", 0))
        tier = data["match"]["tier"]
    except Exception as e:  # noqa: BLE001  —— 模型输出再怪也不允许裸 500
        import traceback

        traceback.print_exc()
        raise HTTPException(500, f"分析结果处理异常，请重试。{e}")

    # 本地保存历史（仅本机）
    storage.add_history(storage.HistoryItem(
        score=score,
        tier=tier,
        jd_excerpt=jd_text[:120].replace("\n", " "),
        sanitized=body.sanitize,
        resume_text=resume_text,
        jd_text=jd_text,
        result=data,
    ))

    return {
        "ok": True,
        "result": data,
        "used_resume_text": used_text,
        "sensitive_hits": [{"kind": h.kind, "count": h.count} for h in hits],
        "score": score,
        "tier": tier,
    }


# ---------------- 历史 ----------------

@app.get("/api/history")
def history_list():
    return {"items": storage.list_history()}


@app.get("/api/history/{item_id}")
def history_get(item_id: str):
    it = storage.get_history(item_id)
    if not it:
        raise HTTPException(404, "记录不存在")
    return {"item": it}


@app.delete("/api/history/{item_id}")
def history_delete(item_id: str):
    return {"ok": storage.delete_history(item_id)}


@app.delete("/api/history")
def history_clear():
    return {"ok": True, "removed": storage.clear_history()}


# ---------------- 启动 ----------------

def _open_browser() -> None:
    webbrowser.open(f"http://{HOST}:{PORT}")


if __name__ == "__main__":
    import uvicorn

    deployed = os.environ.get("PM_SCOUT_HOST", "") not in ("", "127.0.0.1")
    print("=" * 52)
    print("  PM 智投 · 第一期" + ("（云端部署模式）" if deployed else " · 本地服务"))
    print(f"  访问地址: http://{HOST}:{PORT}")
    print("  数据仅保存在 data/ 目录，关闭窗口即停止服务" if not deployed else "  API Key 来自环境变量 PM_SCOUT_API_KEY")
    print("=" * 52)
    if not deployed:
        threading.Timer(1.2, _open_browser).start()
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")

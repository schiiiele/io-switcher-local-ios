"""
routes.py
FastAPI 라우터 — HTTP 요청/응답만 담당.
비즈니스 로직(BLE, 스케줄 상태)은 주입된 의존성(app.state)을 통해 접근.
"""
import time
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

router = APIRouter()

_BASE_DIR = Path(__file__).parent
_UI_PATH = _BASE_DIR / "ui.html"
if not _UI_PATH.exists():
    _UI_PATH = _BASE_DIR / "static" / "ui.html"
UI_HTML = _UI_PATH.read_text(encoding="utf-8")


# ── 헬퍼 ──────────────────────────────────────
def _state(request: Request):
    return request.app.state


# ── UI ────────────────────────────────────────
@router.get("/", response_class=HTMLResponse)
async def index():
    return UI_HTML


# ── Config ────────────────────────────────────
@router.get("/config")
async def get_config(request: Request):
    return _state(request).config

@router.post("/config")
async def set_config(request: Request):
    s = _state(request)
    data = await request.json()
    s.config["device_address"] = data.get("address")
    s.config["device_name"]    = data.get("name")
    s.config["device_type"]    = int(data.get("device_type", 1))
    s.save_config()
    return {"ok": True}


# ── BLE 스캔 ──────────────────────────────────
@router.post("/scan")
async def scan(request: Request):
    import asyncio
    from . import ble
    try:
        # scan_devices는 동기 함수 → 스레드풀에서 실행해 이벤트 루프 블로킹 방지
        loop    = asyncio.get_running_loop()
        devices = await loop.run_in_executor(None, lambda: ble.scan_devices(10))
        return {"ok": True, "devices": devices}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


# ── 스위치 ────────────────────────────────────
@router.post("/switch/{action}")
async def switch(action: str, request: Request, index: int = 1):
    import asyncio
    from . import ble
    s = _state(request)
    addr = s.config.get("device_address")
    if not addr:
        return JSONResponse({"ok": False, "error": "장치 미설정"}, status_code=400)
    device_type = s.config.get("device_type", 1)
    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, lambda: ble.send_command(addr, action, device_type, index)
        )
        return {"ok": True}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


# ── 배터리 ────────────────────────────────────
@router.get("/battery")
async def battery(request: Request):
    import asyncio
    from . import ble
    s    = _state(request)
    addr = s.config.get("device_address")
    if not addr:
        return JSONResponse({"ok": False, "error": "장치 미설정"}, status_code=400)
    try:
        loop  = asyncio.get_running_loop()
        level = await loop.run_in_executor(None, lambda: ble.read_battery(addr))
        return {"ok": True, "level": level}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


# ── 스케줄 ────────────────────────────────────
@router.get("/schedules")
async def get_schedules(request: Request):
    return _state(request).schedules

@router.post("/schedule/daily")
async def add_daily(request: Request):
    s    = _state(request)
    data = await request.json()
    entry = {
        "id":      s.schedule_counter,
        "type":    "daily",
        "enabled": True,
        "action":  data.get("action", "off"),
        "hour":    int(data.get("hour", 23)),
        "minute":  int(data.get("minute", 0)),
        "days":    data.get("days", list(range(7))),
        "index":   int(data.get("index", 1)),
    }
    s.schedule_counter += 1
    s.schedules.append(entry)
    s.save_schedules()
    return {"ok": True}

@router.post("/schedule/timer")
async def add_timer(request: Request):
    s       = _state(request)
    data    = await request.json()
    minutes = int(data.get("minutes", 30))
    action  = data.get("action", "off")
    trigger_at = time.time() + minutes * 60
    label = f"{minutes}분 후 ({datetime.fromtimestamp(trigger_at).strftime('%H:%M')} 실행)"
    entry = {
        "id":         s.schedule_counter,
        "type":       "timer",
        "action":     action,
        "trigger_at": trigger_at,
        "label":      label,
        "index":      int(data.get("index", 1)),
    }
    s.schedule_counter += 1
    s.schedules.append(entry)
    s.save_schedules()
    return {"ok": True}

@router.delete("/schedule/{sid}")
async def delete_schedule(sid: int, request: Request):
    s = _state(request)
    s.schedules[:] = [x for x in s.schedules if x["id"] != sid]
    s.save_schedules()
    return {"ok": True}

@router.post("/schedule/{sid}/toggle")
async def toggle_schedule(sid: int, request: Request):
    s = _state(request)
    for x in s.schedules:
        if x["id"] == sid:
            x["enabled"] = not x.get("enabled", True)
            s.save_schedules()
            return {"ok": True, "enabled": x["enabled"]}
    return JSONResponse({"ok": False}, status_code=404)

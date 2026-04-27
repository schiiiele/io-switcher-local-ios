"""
main.py
서버 진입점.

역할:
  1. 설정·스케줄 로드 (storage)
  2. FastAPI 앱 생성, 공유 상태 주입
  3. 스케줄러 백그라운드 시작
  4. mDNS 등록 (zeroconf 없으면 조용히 스킵)
  5. uvicorn 으로 서버 기동

실행:
  python -m switcher.main          # 패키지 모드
  python main.py                   # 단독 실행 (switcher/ 폴더 안에서)
"""
import platform
import socket
import os
import sys

import uvicorn
from fastapi import FastAPI

from . import ble          # noqa: F401  — 임포트 시 전역 루프 스레드 시작
from .routes    import router
from .scheduler import Scheduler
from .storage   import (
    load_config, save_config as _save_config,
    load_schedules, save_schedules as _save_schedules,
)

# ── FastAPI 앱 ────────────────────────────────
app = FastAPI(title="Switcher")
app.include_router(router)


# ── 공유 상태 초기화 (lifespan) ───────────────
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(application: FastAPI):
    # 시작
    cfg, (scheds, counter) = load_config(), load_schedules()

    application.state.config           = cfg
    application.state.schedules        = scheds
    application.state.schedule_counter = counter

    def _save_cfg():
        _save_config(application.state.config)

    def _save_sch():
        _save_schedules(application.state.schedules,
                        application.state.schedule_counter)

    def _rm_schedule(sid):
        application.state.schedules[:] = [
            s for s in application.state.schedules if s["id"] != sid
        ]

    def _ble_cmd(action: str, index: int = 1):
        addr = application.state.config.get("device_address")
        if not addr:
            print(f"[scheduler] 장치 미설정 — {action} 건너뜀")
            return
        dtype = application.state.config.get("device_type", 1)
        ble.send_command(addr, action, dtype, index)

    application.state.save_config    = _save_cfg
    application.state.save_schedules = _save_sch

    sched = Scheduler(
        get_schedules  = lambda: application.state.schedules,
        remove_schedule= _rm_schedule,
        save_fn        = _save_sch,
        command_fn     = _ble_cmd,
    )
    sched.start()

    _register_mdns(5001)
    _print_start_info()

    yield
    # 종료 훅 — 필요시 여기서 정리

app.router.lifespan_context = lifespan


# ── mDNS ──────────────────────────────────────
def _register_mdns(port: int = 5001):
    try:
        from zeroconf import ServiceInfo, Zeroconf
        local_ip = socket.gethostbyname(socket.gethostname())
        info = ServiceInfo(
            "_http._tcp.local.",
            "switcher._http._tcp.local.",
            addresses=[socket.inet_aton(local_ip)],
            port=port,
            properties={"path": "/"},
            server="switcher.local.",
        )
        zc = Zeroconf()
        zc.register_service(info)
        print(f"🌐 mDNS 등록 완료: http://switcher.local:{port}")
    except Exception as e:
        print(f"[mDNS 등록 실패, 무시됨] {e}")


# ── 시작 안내 ─────────────────────────────────
def _print_start_info():
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        local_ip = "127.0.0.1"

    print(f"\n✅ 서버 시작!")
    print(f"📱 접속 주소: http://switcher.local:5001")
    print(f"   (IP 직접:  http://{local_ip}:5001)\n")

    os_name = platform.system()
    print("── 자동 시작 설정 ──────────────────────────")
    if os_name == "Darwin":
        plist = os.path.expanduser(
            "~/Library/LaunchAgents/com.switcher.server.plist"
        )
        print(f"macOS: LaunchAgent → {plist}")
    elif os_name == "Windows":
        print("Windows: Win+R → shell:startup → 바로가기 생성")
        print(f"  대상: python \"{os.path.abspath(__file__)}\"")
    else:
        print("Linux: systemd 서비스 또는 crontab @reboot")
    print("─────────────────────────────────────────\n")


# ── 단독 실행 ─────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "switcher.main:app",
        host="0.0.0.0",
        port=5001,
        log_level="info",
    )

"""
storage.py
config.json / schedules.json 읽기·쓰기 담당.
상태(state)는 이 모듈이 소유하지 않는다 — 호출자가 관리.
"""
import json
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE   = os.path.join(BASE_DIR, "config.json")
SCHEDULE_FILE = os.path.join(BASE_DIR, "schedules.json")


def _atomic_save_json(target_path: str, data, *, ensure_ascii: bool, indent=None) -> None:
    tmp_path = f"{target_path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, target_path)


# ── config ──────────────────────────────────────
def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return {"device_address": None, "device_name": None, "device_type": 1}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(data: dict) -> None:
    _atomic_save_json(CONFIG_FILE, data, ensure_ascii=False, indent=2)


# ── schedules ───────────────────────────────────
def load_schedules() -> tuple[list, int]:
    """(schedules, id_counter) 반환. 만료된 타이머는 자동 제거."""
    if not os.path.exists(SCHEDULE_FILE):
        return [], 1
    try:
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        counter  = data.get("counter", 1)
        loaded   = data.get("schedules", [])
        now      = time.time()
        filtered = [s for s in loaded
                    if not (s["type"] == "timer" and s["trigger_at"] <= now)]
        return filtered, counter
    except Exception as e:
        print(f"[storage] 예약 불러오기 실패: {e}")
        return [], 1

def save_schedules(schedules: list, counter: int) -> None:
    _atomic_save_json(
        SCHEDULE_FILE,
        {"counter": counter, "schedules": schedules},
        ensure_ascii=False,
    )

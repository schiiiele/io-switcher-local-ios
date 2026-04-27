"""
scheduler.py
백그라운드 스케줄러.

- 1초 간격으로 schedules 리스트를 순회해 조건이 맞으면 BLE 명령 실행.
- 상태(schedules, counter, config)는 외부에서 주입받는다.
  → 순환 import 없음, 테스트 용이.
- 타이머 완료 후 목록 정리 및 영속화(save_fn 호출).
"""
import time
import threading
from datetime import datetime


class Scheduler:
    def __init__(self, get_schedules, remove_schedule, save_fn, command_fn):
        """
        get_schedules  : () -> list  — 현재 스케줄 목록 반환
        remove_schedule: (id) -> None — 타이머 완료 후 제거
        save_fn        : () -> None  — 변경 후 저장
        command_fn     : (action: str) -> None — BLE 명령 실행
        """
        self._get   = get_schedules
        self._rm    = remove_schedule
        self._save  = save_fn
        self._cmd   = command_fn
        self._fired: set = set()        # (id, hour, minute) — 같은 분에 중복 방지

    # ── 메인 루프 ────────────────────────────────
    def _loop(self):
        while True:
            try:
                self._tick()
            except Exception as e:
                print(f"[scheduler] 오류: {e}")
            time.sleep(1)

    def _tick(self):
        now     = datetime.now()
        weekday = now.weekday()
        hm      = (now.hour, now.minute)
        to_remove = []

        for s in self._get():
            if not s.get("enabled", True):
                continue

            if s["type"] == "daily":
                if weekday not in s.get("days", list(range(7))):
                    continue
                fire_key = (s["id"], hm)
                if now.hour == s["hour"] and now.minute == s["minute"] \
                        and fire_key not in self._fired:
                    self._fired.add(fire_key)
                    print(f"[scheduler] daily {s['action']} "
                          f"({s['hour']:02d}:{s['minute']:02d})")
                    threading.Thread(
                        target=self._cmd, args=(s["action"], s.get("index", 1)), daemon=True
                    ).start()

            elif s["type"] == "timer":
                if time.time() >= s["trigger_at"]:
                    print(f"[scheduler] timer {s['action']}")
                    threading.Thread(
                        target=self._cmd, args=(s["action"], s.get("index", 1)), daemon=True
                    ).start()
                    to_remove.append(s["id"])

        if to_remove:
            for sid in to_remove:
                self._rm(sid)
            self._save()

    # ── 시작 ─────────────────────────────────────
    def start(self):
        threading.Thread(target=self._loop, daemon=True).start()

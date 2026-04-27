"""
ble.py
블루투스(BLE) 통신 전담 모듈.

핵심 설계:
  - asyncio 전역 루프를 별도 스레드에서 영구 실행.
  - 모든 BLE 호출은 asyncio.run_coroutine_threadsafe() 로 그 루프에 던짐.
  - 루프 자체는 절대 닫지 않는다 → 매 요청마다 new_event_loop() 하는
    안티패턴 완전 제거.
  - 동시 BLE 접속 충돌 방지를 위해 asyncio.Lock 사용 (threading.Lock 아님).
"""
import asyncio
import binascii
import threading

from bleak import BleakClient, BleakScanner

# ── BLE 상수 ────────────────────────────────────
CHAR_UUID    = "000015ba-0000-1000-8000-00805f9b34fb"
BATTERY_UUID = "000015aa-0000-1000-8000-00805f9b34fb"

_KEYS = {
    (1, 1, "on"):  binascii.a2b_hex("00"),
    (1, 1, "off"): binascii.a2b_hex("01"),
    (2, 1, "on"):  binascii.a2b_hex("02"),
    (2, 1, "off"): binascii.a2b_hex("03"),
    (2, 2, "on"):  binascii.a2b_hex("04"),
    (2, 2, "off"): binascii.a2b_hex("05"),
}

# ── 전역 이벤트 루프 (앱 수명 내내 살아 있음) ────
_loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
_ble_lock: asyncio.Lock          = asyncio.Lock()   # 루프 안에서만 사용

def _start_loop(loop: asyncio.AbstractEventLoop) -> None:
    """데몬 스레드에서 루프를 영구 실행."""
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=_start_loop, args=(_loop,), daemon=True).start()


def _run(coro):
    """코루틴을 전역 루프에 제출하고 결과를 동기적으로 기다린다."""
    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    return future.result()          # 기본 timeout 없음 — 필요시 future.result(timeout=N)


# ── BLE 코루틴 ──────────────────────────────────
async def _send_command(address: str, key: bytes) -> None:
    async with _ble_lock:
        async with BleakClient(address) as client:
            await client.write_gatt_char(CHAR_UUID, key)

async def _read_battery(address: str) -> int:
    async with _ble_lock:
        async with BleakClient(address) as client:
            val = await client.read_gatt_char(BATTERY_UUID)
            return val[0]

async def _scan(duration: float = 10.0) -> list[dict]:
    devices = await BleakScanner.discover(timeout=duration)
    result = [
        {
            "address": d.address,
            "name":    d.name or "(이름 없음)",
            "rssi":    d.rssi if hasattr(d, "rssi") else None,
        }
        for d in devices
    ]
    result.sort(key=lambda x: x["rssi"] or -999, reverse=True)
    return result


# ── 공개 API (동기 인터페이스) ───────────────────
def send_command(address: str, action: str, device_type: int = 1, switch_index: int = 1) -> None:
    if device_type == 1:
        switch_index = 1
    key = _KEYS.get((device_type, switch_index, action))
    if key is None:
        raise ValueError(
            f"알 수 없는 action/device_type/switch_index: {action}/{device_type}/{switch_index}"
        )
    _run(_send_command(address, key))

def read_battery(address: str) -> int:
    return _run(_read_battery(address))

def scan_devices(duration: float = 10.0) -> list[dict]:
    return _run(_scan(duration))

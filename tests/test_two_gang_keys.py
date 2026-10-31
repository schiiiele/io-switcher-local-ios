"""
2구 스위처 명령 바이트 검증 (기기 없이 실행).

기준은 공식 안드로이드 앱(kr.switcher.switcherm v3.28.3) 디컴파일 소스다.
  - kr/switcher/device/switcher/Switcher.java
      ON_1WAY = 0, OFF_1WAY = 1, ON_2WAY = 2, OFF_2WAY = 3
  - kr/switcher/switcherm/ui/main/event/SwitcherOnOffController.java
      onTwoSetOneOn  -> 0   (2구 첫 번째 스위치 켜기)
      onTwoSetOneOff -> 1   (2구 첫 번째 스위치 끄기)
      onTwoSetTwoOn  -> 2   (2구 두 번째 스위치 켜기)
      onTwoSetTwoOff -> 3   (2구 두 번째 스위치 끄기)
앱은 0~3 말고는 보내지 않는다. 4·5는 공식 명령이 아니다.

실행: python3 -m unittest discover -s tests
"""
import os
import sys
import types
import unittest

# bleak 없이도 돌도록 가짜 모듈을 끼워 넣는다 (BLE 통신은 시험하지 않는다).
_fake_bleak = types.ModuleType("bleak")
_fake_bleak.BleakClient = object
_fake_bleak.BleakScanner = object
sys.modules.setdefault("bleak", _fake_bleak)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from switcher import ble  # noqa: E402

OFFICIAL = {
    # (device_type, switch_index, action): 공식 앱이 보내는 바이트
    (1, 1, "on"):  0x00,
    (1, 1, "off"): 0x01,
    (2, 1, "on"):  0x00,
    (2, 1, "off"): 0x01,
    (2, 2, "on"):  0x02,
    (2, 2, "off"): 0x03,
}


class TwoGangKeyTest(unittest.TestCase):
    def setUp(self):
        self.sent = []
        self._orig = (ble._run, ble._send_command)
        ble._send_command = lambda address, key: (address, key)
        ble._run = lambda result: self.sent.append(result)

    def tearDown(self):
        ble._run, ble._send_command = self._orig

    def test_each_button_sends_official_byte(self):
        for (dtype, idx, action), byte in OFFICIAL.items():
            with self.subTest(device_type=dtype, switch=idx, action=action):
                self.sent.clear()
                ble.send_command("AA:BB", action, dtype, idx)
                self.assertEqual(self.sent, [("AA:BB", bytes([byte]))])

    def test_switch1_and_switch2_never_share_a_byte(self):
        sw1 = {ble._KEYS[(2, 1, a)] for a in ("on", "off")}
        sw2 = {ble._KEYS[(2, 2, a)] for a in ("on", "off")}
        self.assertFalse(sw1 & sw2)

    def test_no_unofficial_bytes(self):
        for k, v in ble._KEYS.items():
            with self.subTest(key=k):
                self.assertIn(v[0], (0x00, 0x01, 0x02, 0x03))


if __name__ == "__main__":
    unittest.main()

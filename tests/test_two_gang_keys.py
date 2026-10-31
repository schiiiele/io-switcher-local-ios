"""
스위처 명령 바이트 검증 (기기 없이 실행).

기준은 공식 안드로이드 앱(kr.switcher.switcherm v3.28.3) 디컴파일 소스다.
  - kr/switcher/device/switcher/Switcher.java
      ON_1WAY = 0, OFF_1WAY = 1, ON_2WAY = 2, OFF_2WAY = 3
  - kr/switcher/switcherm/ui/main/event/SwitcherOnOffController.java
      onTwoSetOneOn -> 0, onTwoSetOneOff -> 1   (2구 첫 번째 스위치)
      onTwoSetTwoOn -> 2, onTwoSetTwoOff -> 3   (2구 두 번째 스위치)
앱은 0~3 말고는 보내지 않는다. 예전에 쓰던 05 는 공식 명령이 아니다
(다른 사람의 2구 실기기 시험에서는 02 처럼 두 번째 스위치를 켰지만, 펌웨어가 보장하는 값은 아니다).

V2 는 2구일 때 두 번째 스위치만 켜고 끈다.

실행: python3 -m unittest discover -s tests
"""
import os
import sys
import types
import unittest

# flask·bleak 없이도 돌도록 가짜 모듈을 끼워 넣는다 (서버·BLE 통신은 시험하지 않는다).
_fake_bleak = types.ModuleType("bleak")
_fake_bleak.BleakClient = object
_fake_bleak.BleakScanner = object


class _FakeFlask:
    def __init__(self, *a, **kw):
        pass

    def route(self, *a, **kw):
        return lambda f: f


_fake_flask = types.ModuleType("flask")
_fake_flask.Flask = _FakeFlask
_fake_flask.jsonify = _fake_flask.request = _fake_flask.Response = None
sys.modules.setdefault("bleak", _fake_bleak)
sys.modules.setdefault("flask", _fake_flask)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import switcher_server as ss  # noqa: E402


class SwitchKeyTest(unittest.TestCase):
    def setUp(self):
        self.sent = []
        self._orig = (ss._run_ble, ss._send_command, dict(ss.config))
        ss._send_command = lambda key: key
        ss._run_ble = lambda key: self.sent.append(key)

    def tearDown(self):
        ss._run_ble, ss._send_command = self._orig[:2]
        ss.config.clear()
        ss.config.update(self._orig[2])

    def _send(self, device_type, action):
        ss.config["device_type"] = device_type
        self.sent.clear()
        ss.run_command(action)
        return self.sent

    def test_one_gang(self):
        self.assertEqual(self._send(1, "on"), [b"\x00"])
        self.assertEqual(self._send(1, "off"), [b"\x01"])

    def test_two_gang_uses_official_switch2_bytes(self):
        self.assertEqual(self._send(2, "on"), [b"\x02"])
        self.assertEqual(self._send(2, "off"), [b"\x03"])

    def test_no_unofficial_bytes(self):
        for name in ("ON_KEY1", "OFF_KEY1", "ON_KEY2", "OFF_KEY2"):
            with self.subTest(key=name):
                self.assertIn(getattr(ss, name)[0], (0x00, 0x01, 0x02, 0x03))


if __name__ == "__main__":
    unittest.main()

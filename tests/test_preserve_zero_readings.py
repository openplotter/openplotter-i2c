import importlib.util
import sys
import types
import json
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load_module(relative, stubs=None, name="tested_module"):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, stubs or {}):
        spec.loader.exec_module(module)
    return module


def settings_stubs():
    settings = types.ModuleType("openplotterSettings")
    for name in ("conf", "platform", "language"):
        setattr(settings, name, types.SimpleNamespace())
    return {"openplotterSettings": settings, "ujson": json}


def reader():
    stubs = settings_stubs()
    stubs["board"] = types.ModuleType("board")
    stubs["websocket"] = types.SimpleNamespace(create_connection=mock.Mock())
    stubs["openplotterSignalkInstaller"] = types.SimpleNamespace(
        connections=mock.Mock()
    )
    return load_module("openplotterI2c/openplotterI2cRead.py", stubs)


class ZeroReadingsTest(unittest.TestCase):
    def test_scaled_and_raw_zero_are_values(self):
        module = reader()
        self.assertEqual(
            module.getPaths([], 0, 0, "sensor", 5, 2, True),
            [{"path": "sensor", "value": 5}, {"path": "sensor.raw", "value": 0}],
        )

    def test_adc_zero_with_raw_enabled(self):
        module = reader()
        result = module.getPaths2([], [[[0, 10], [0, 100]]], 0, 0, "sensor", 0, 1, True)
        self.assertEqual(
            result,
            [
                {"path": "sensor", "value": 0},
                {"path": "sensor.raw", "value": {"value": 0, "voltage": 0}},
            ],
        )

    def test_missing_reading_remains_null(self):
        self.assertEqual(
            reader().getPaths([], "", "", "sensor", 0, 1, True),
            [{"path": "sensor", "value": None}, {"path": "sensor.raw", "value": None}],
        )


if __name__ == "__main__":
    unittest.main()

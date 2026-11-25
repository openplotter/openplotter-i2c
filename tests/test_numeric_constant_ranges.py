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


class ConstantRangeTest(unittest.TestCase):
    def test_constant_range_is_numeric_and_scalable(self):
        module = reader()
        ranges = module.getRanges({"range1": "0|100 -> 2.5"})
        self.assertEqual(ranges, [[[0, 100], 2.5]])
        self.assertEqual(
            module.getPaths2([], ranges, 50, 1.0, "sensor", 1, 2.0, False),
            [{"path": "sensor", "value": 6.0}],
        )

    def test_interpolated_ranges_remain_numeric(self):
        self.assertEqual(
            reader().getRanges({"range1": "0|100 -> -2|2"}), [[[0, 100], [-2.0, 2.0]]]
        )


if __name__ == "__main__":
    unittest.main()

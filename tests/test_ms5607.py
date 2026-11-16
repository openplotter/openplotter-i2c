"""MS5607 numerical checks run without opening an I2C device."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'openplotterI2c' / 'ms5607.py'
SPEC = importlib.util.spec_from_file_location('ms5607_test_driver', SCRIPT)
driver = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, {'smbus': types.SimpleNamespace(SMBus=lambda bus: object())}):
    SPEC.loader.exec_module(driver)


class Ms5607Test(unittest.TestCase):
    def setUp(self):
        self.sensor = driver.Ms5607.__new__(driver.Ms5607)
        # TE MS5607-02BA03 datasheet example PROM coefficients.
        self.sensor.coefficients = [46372, 43981, 29059, 27842, 31553, 28165]

    def test_pressure_unit_conversions(self):
        self.assertAlmostEqual(self.sensor.hectoPascalToInHg(1013.25), 29.9212524, places=6)
        self.assertAlmostEqual(self.sensor.inHgToHectoPascal(1), 33.86389, places=5)
        self.assertEqual(self.sensor.hectoPascalToInHg(0), 0)

    def test_second_order_compensation(self):
        # Independent rational-arithmetic evaluation of datasheet figures 2 and 3.
        cases = [
            (8077636, 20.002283120155333, 110002.95763915726),
            (7500000, -0.9453920412063599, 105063.66539938124),
            (7000000, -21.586704044342042, 100347.8774082371),
        ]
        for raw, temperature, pressure in cases:
            with self.subTest(raw=raw):
                self.sensor.getDigitalTemperature = lambda value=raw: value
                self.assertAlmostEqual(self.sensor.getTemperature(), temperature, places=6)

    def test_second_order_pressure_compensation(self):
        for raw, expected in [(8077636, 110002.95763915726), (7500000, 105063.66539938124), (7000000, 100347.8774082371)]:
            with self.subTest(raw=raw):
                self.assertAlmostEqual(self.sensor.convertPressureTemperature(6465444, raw), expected, places=5)


if __name__ == '__main__':
    unittest.main()

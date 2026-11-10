import unittest

from desktop import BurstTrigger, match_color
from vision import PROFILES


class DesktopTest(unittest.TestCase):
    def test_windows_colorref_channels(self):
        self.assertEqual(match_color(0x1CD5FF, PROFILES), 'amarelo')
        self.assertEqual(match_color(0xFF3FA6, PROFILES), 'roxo')
        self.assertEqual(match_color(0x3E2BF0, PROFILES), 'vermelho')
        self.assertIsNone(match_color(0xFFFFFFFF, PROFILES))
        self.assertIsNone(match_color(0xCCCCCC, PROFILES))

    def test_delay_interval_limit_and_reset(self):
        gate = BurstTrigger(0.05, 0.2, 2)
        self.assertFalse(gate.ready(True, False, 0))
        self.assertFalse(gate.ready(True, True, 0))
        self.assertTrue(gate.ready(True, True, 0.06))
        self.assertFalse(gate.ready(True, True, 0.20))
        self.assertTrue(gate.ready(True, True, 0.27))
        self.assertFalse(gate.ready(True, True, 0.60))
        self.assertFalse(gate.ready(False, True, 0.61))
        self.assertFalse(gate.ready(True, True, 0.62))
        self.assertTrue(gate.ready(True, True, 0.68))

    def test_continuous_stops_when_disarmed(self):
        gate = BurstTrigger(0, 0.1, 0)
        self.assertTrue(gate.ready(True, True, 0))
        self.assertTrue(gate.ready(True, True, 0.11))
        self.assertFalse(gate.ready(True, False, 0.22))
        self.assertTrue(gate.ready(True, True, 0.23))

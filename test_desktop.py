import unittest

from desktop import EntryTrigger, match_color
from vision import PROFILES


class DesktopTest(unittest.TestCase):
    def test_windows_colorref_channels(self):
        self.assertEqual(match_color(0x1CD5FF, PROFILES), 'amarelo')
        self.assertEqual(match_color(0xFF3FA6, PROFILES), 'roxo')
        self.assertEqual(match_color(0x3E2BF0, PROFILES), 'vermelho')
        self.assertIsNone(match_color(0xFFFFFFFF, PROFILES))
        self.assertIsNone(match_color(0xCCCCCC, PROFILES))

    def test_one_click_per_entry_and_cooldown(self):
        gate = EntryTrigger(0.2)
        self.assertFalse(gate.ready(True, False, 0))
        self.assertTrue(gate.ready(True, True, 0))
        self.assertFalse(gate.ready(True, True, 1))
        self.assertFalse(gate.ready(False, True, 1))
        self.assertTrue(gate.ready(True, True, 1))
        self.assertFalse(gate.ready(False, True, 1.05))
        self.assertFalse(gate.ready(True, True, 1.10))
        self.assertTrue(gate.ready(True, True, 1.25))

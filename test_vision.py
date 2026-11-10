import unittest

import numpy as np

from vision import PROFILES, aim_step, detect


class VisionTest(unittest.TestCase):
    def test_aim_picks_nearest_within_circular_fov(self):
        near = ('roxo', 116, 96, 8, 8)
        far = ('amarelo', 96, 126, 8, 8)
        corner = ('vermelho', 120, 120, 8, 8)
        self.assertEqual(aim_step([far, near], 100, 100, 32, 5), (4, 0))
        self.assertIsNone(aim_step([corner], 100, 100, 30, 5))
        centered = ('roxo', 96, 96, 8, 8)
        self.assertIsNone(aim_step([near, centered], 100, 100, 32, 5))

    def test_all_profiles_and_red_wrap(self):
        image = np.zeros((120, 200, 3), dtype=np.uint8)
        image[30:50, 20:40] = (255, 213, 28)
        image[50:70, 90:110] = (166, 63, 255)
        image[30:50, 150:170] = (240, 43, 62)
        image[70:90, 150:170] = (240, 45, 30)
        boxes, aim = detect(image, PROFILES)
        self.assertCountEqual([box[0] for box in boxes], ['amarelo', 'roxo', 'vermelho', 'vermelho'])
        self.assertTrue(aim)
        self.assertFalse(detect(image, ['amarelo'])[1])

    def test_noise_and_hollow_box_do_not_trigger(self):
        image = np.zeros((120, 200, 3), dtype=np.uint8)
        image[45:75, 85:115] = (255, 0, 0)
        image[50:70, 90:110] = (0, 0, 0)
        image[60, 100] = (255, 0, 0)
        boxes, aim = detect(image, ['vermelho'])
        self.assertEqual(len(boxes), 1)
        self.assertFalse(aim)


if __name__ == '__main__':
    unittest.main()

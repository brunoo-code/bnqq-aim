import cv2
import numpy as np

# OpenCV's 8-bit hue scale is 0–179. Red wraps around zero.
PROFILES = {
    'amarelo': ((19, 36),),
    'roxo': ((125, 158),),
    'vermelho': ((0, 9), (170, 179)),
}


def detect(rgb, profiles, min_area=55):
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    boxes = []
    center_x, center_y = rgb.shape[1] // 2, rgb.shape[0] // 2
    on_target = False
    for name in profiles:
        mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for low, high in PROFILES[name]:
            mask |= cv2.inRange(hsv, (low, 115, 115), (high, 255, 255))
        # Remove isolated pixels before labeling the components.
        clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        _, labels, stats, _ = cv2.connectedComponentsWithStats(clean, connectivity=8)
        patch = labels[max(0, center_y-3):center_y+4, max(0, center_x-3):center_x+4]
        for index, (x, y, w, h, area) in enumerate(stats[1:], start=1):
            if area < min_area or w > rgb.shape[1] * 0.5 or h > rgb.shape[0] * 0.5:
                continue
            boxes.append((name, int(x), int(y), int(w), int(h)))
            # A pixel from the accepted component must be near the crosshair.
            on_target |= bool(np.any(patch == index))
    return boxes, on_target

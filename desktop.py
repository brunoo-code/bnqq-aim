"""Monitor the pixel under the Windows cursor and run a configurable burst."""

import argparse
from colorsys import rgb_to_hsv
import ctypes as C
from ctypes import wintypes as W
import json
from pathlib import Path
import sys
from threading import Event
import time

import numpy as np
from PIL import ImageGrab

from overlay import BUTTON_FLAGS, click, move_relative, windows_api
from vision import PROFILES, aim_step, detect

KEYS = {f'F{i}': 0x6F + i for i in range(1, 13) if i != 9}
KEYS.update({key: ord(key) for key in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'})
KEYS.update({'SHIFT': 0x10, 'CTRL': 0x11, 'ALT': 0x12, 'MOUSE4': 0x05, 'MOUSE5': 0x06})
DEFAULTS = {'colors': ['amarelo'], 'key': 'F8', 'button': 'esquerdo',
            'delay_ms': 40, 'interval_ms': 180, 'burst': 3,
            'aim_enabled': False, 'aim_key': 'F7', 'fov_px': 100, 'smoothing': 5}


def match_color(pixel, profiles):
    if pixel == 0xFFFFFFFF:
        return None
    rgb = [(pixel >> shift & 255) / 255 for shift in (0, 8, 16)]
    hue, saturation, value = rgb_to_hsv(*rgb)
    if saturation < 115/255 or value < 115/255:
        return None
    hue = round(hue * 180) % 180
    return next((name for name in profiles if any(low <= hue <= high
                 for low, high in PROFILES[name])), None)


class BurstTrigger:
    def __init__(self, delay, interval, limit):
        self.delay, self.interval, self.limit = delay, interval, limit
        self.next_click = None
        self.last_click = float('-inf')
        self.shots = 0

    def ready(self, matching, armed, now):
        if not matching or not armed:
            self.next_click = None
            self.shots = 0
            return False
        if self.next_click is None:
            self.next_click = max(now + self.delay, self.last_click + self.interval)
        if now < self.next_click or (self.limit and self.shots >= self.limit):
            return False
        self.next_click = now + self.interval
        self.last_click = now
        self.shots += 1
        return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, help='arquivo JSON com o perfil do trigger')
    parser.add_argument('--colors', nargs='+', choices=PROFILES)
    parser.add_argument('--trigger', action='store_true', help='permite clique enquanto a tecla estiver pressionada')
    parser.add_argument('--key', type=str.upper, choices=KEYS)
    parser.add_argument('--button', choices=BUTTON_FLAGS)
    parser.add_argument('--delay-ms', type=int)
    parser.add_argument('--interval-ms', '--cooldown', type=int)
    parser.add_argument('--burst', type=int, help='cliques por entrada na cor; 0 mantém a repetição')
    parser.add_argument('--aim-enabled', action='store_true', default=None)
    parser.add_argument('--aim-key', type=str.upper, choices=KEYS)
    parser.add_argument('--fov-px', type=int)
    parser.add_argument('--smoothing', type=int)
    args = parser.parse_args()
    if sys.platform != 'win32':
        parser.error('use Windows')
    settings = DEFAULTS.copy()
    if args.config:
        try:
            profile = json.loads(args.config.read_text(encoding='utf-8-sig'))
        except (OSError, ValueError) as exc:
            parser.error(f'perfil inválido: {exc}')
        if not isinstance(profile, dict) or profile.keys() - settings.keys():
            parser.error('o JSON deve conter somente os campos do perfil padrão')
        settings.update(profile)
    settings.update({name: getattr(args, name) for name in settings if getattr(args, name) is not None})
    colors, key, button = (settings[name] for name in ('colors', 'key', 'button'))
    delay, interval, burst = (settings[name] for name in ('delay_ms', 'interval_ms', 'burst'))
    aim_enabled, aim_key = settings['aim_enabled'], settings['aim_key']
    radius, smoothing = settings['fov_px'], settings['smoothing']
    if (not isinstance(colors, list) or not colors or
            any(not isinstance(color, str) or color not in PROFILES for color in colors) or
            not isinstance(key, str) or key not in KEYS or
            not isinstance(button, str) or button not in BUTTON_FLAGS or
            any(type(value) is not int for value in (delay, interval, burst)) or
            delay < 0 or interval < 50 or burst < 0 or type(aim_enabled) is not bool or
            not isinstance(aim_key, str) or aim_key not in KEYS or
            type(radius) is not int or not 25 <= radius <= 240 or
            type(smoothing) is not int or not 1 <= smoothing <= 12):
        parser.error('confira cores, tecla, botão e tempos. O intervalo mínimo é 50 ms.')

    run(settings, args.trigger, Event())


def run(settings, trigger, stop, key_down=None):
    colors, key, button = (settings[name] for name in ('colors', 'key', 'button'))
    delay, interval, burst = (settings[name] for name in ('delay_ms', 'interval_ms', 'burst'))
    aim_enabled, aim_key = settings['aim_enabled'], settings['aim_key']
    radius, smoothing = settings['fov_px'], settings['smoothing']
    user = windows_api()
    if key_down is None:
        def key_down(code):
            return bool(user.GetAsyncKeyState(code) & 0x8000)
    user.GetDC.argtypes, user.GetDC.restype = (W.HWND,), W.HDC
    user.ReleaseDC.argtypes, user.ReleaseDC.restype = (W.HWND, W.HDC), C.c_int
    get_pixel = C.WinDLL('gdi32', use_last_error=True).GetPixel
    get_pixel.argtypes, get_pixel.restype = (W.HDC, C.c_int, C.c_int), W.DWORD
    dc = user.GetDC(None)
    if not dc:
        raise RuntimeError('Não foi possível acessar a área de trabalho.')
    state = BurstTrigger(delay / 1000, interval / 1000, burst)
    cursor = W.POINT()
    previous = None
    last_aim = 0.0
    print('Monitorando: ' + ', '.join(colors), flush=True)
    print(f'Segure {key} para armar (se habilitado). F9 encerra.', flush=True)
    try:
        while not stop.is_set() and not key_down(0x78):
            color = None
            if user.GetCursorPos(C.byref(cursor)):
                color = match_color(get_pixel(dc, cursor.x, cursor.y), colors)
                now = time.monotonic()
                if aim_enabled and now - last_aim >= 0.045 and key_down(KEYS[aim_key]):
                    last_aim = now
                    x, y = cursor.x, cursor.y
                    frame = ImageGrab.grab(bbox=(x-radius, y-radius, x+radius+1, y+radius+1), all_screens=True)
                    boxes, _ = detect(np.asarray(frame), colors, min_area=18)
                    step = aim_step(boxes, radius, radius, radius, smoothing)
                    if step and not stop.is_set() and key_down(KEYS[aim_key]):
                        current = W.POINT()
                        if user.GetCursorPos(C.byref(current)) and (current.x, current.y) == (x, y):
                            if move_relative(user, *step):
                                color = (match_color(get_pixel(dc, current.x, current.y), colors)
                                         if user.GetCursorPos(C.byref(current)) else None)
            if color and color != previous:
                print(f'{color.upper()} em ({cursor.x}, {cursor.y})', flush=True)
            previous = color
            armed = trigger and not stop.is_set() and key_down(KEYS[key])
            if state.ready(color is not None, armed, time.monotonic()):
                if click(user, button):
                    print('Clique enviado.', flush=True)
                else:
                    raise RuntimeError('O Windows bloqueou o envio do clique.')
            stop.wait(0.02)
    except KeyboardInterrupt:
        pass
    finally:
        user.ReleaseDC(None, dc)


if __name__ == '__main__':
    main()

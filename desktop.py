"""Monitor the pixel under the Windows cursor and click once per color entry."""

import argparse
from colorsys import rgb_to_hsv
import ctypes as C
from ctypes import wintypes as W
import sys
import time

from overlay import click, windows_api
from vision import PROFILES


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


class EntryTrigger:
    def __init__(self, cooldown):
        self.cooldown = cooldown
        self.latched = False
        self.last_click = float('-inf')

    def ready(self, matching, armed, now):
        if not matching or not armed:
            self.latched = False
            return False
        if self.latched or now - self.last_click < self.cooldown:
            return False
        self.latched = True
        self.last_click = now
        return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--colors', nargs='+', choices=PROFILES, default=['amarelo'])
    parser.add_argument('--trigger', action='store_true', help='permite clique enquanto F8 estiver pressionado')
    parser.add_argument('--cooldown', type=int, default=180, help='intervalo mínimo em ms')
    args = parser.parse_args()
    if sys.platform != 'win32' or args.cooldown < 100:
        parser.error('use Windows e um intervalo de pelo menos 100 ms')

    user = windows_api()
    user.GetDC.argtypes, user.GetDC.restype = (W.HWND,), W.HDC
    user.ReleaseDC.argtypes, user.ReleaseDC.restype = (W.HWND, W.HDC), C.c_int
    get_pixel = C.WinDLL('gdi32', use_last_error=True).GetPixel
    get_pixel.argtypes, get_pixel.restype = (W.HDC, C.c_int, C.c_int), W.DWORD
    dc = user.GetDC(None)
    if not dc:
        raise RuntimeError('Não foi possível acessar a área de trabalho.')
    state = EntryTrigger(args.cooldown / 1000)
    cursor = W.POINT()
    previous = None
    print('Monitorando: ' + ', '.join(args.colors), flush=True)
    print('Segure F8 para armar o clique (se habilitado). F9 encerra.', flush=True)
    try:
        while not user.GetAsyncKeyState(0x78) & 0x8000:
            color = None
            if user.GetCursorPos(C.byref(cursor)):
                color = match_color(get_pixel(dc, cursor.x, cursor.y), args.colors)
            if color and color != previous:
                print(f'{color.upper()} em ({cursor.x}, {cursor.y})', flush=True)
            previous = color
            armed = args.trigger and bool(user.GetAsyncKeyState(0x77) & 0x8000)
            if state.ready(color is not None, armed, time.monotonic()):
                if click(user):
                    print('Clique enviado.', flush=True)
                else:
                    args.trigger = False
                    print('Clique bloqueado pelo Windows. Modo visual mantido.', file=sys.stderr)
            time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    finally:
        user.ReleaseDC(None, dc)


if __name__ == '__main__':
    main()

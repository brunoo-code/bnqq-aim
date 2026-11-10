import argparse
import ctypes as C
from ctypes import wintypes as W
import sys
import time
import tkinter as tk

import numpy as np
from PIL import ImageGrab

from vision import PROFILES, detect

INK = '#00f5d4'
KEY = '#010203'


class MouseInput(C.Structure):
    _fields_ = [('dx', W.LONG), ('dy', W.LONG), ('data', W.DWORD),
                ('flags', W.DWORD), ('time', W.DWORD), ('extra', C.c_size_t)]


class Input(C.Structure):
    _fields_ = [('kind', W.DWORD), ('mouse', MouseInput)]


def windows_api():
    user = C.WinDLL('user32', use_last_error=True)
    signatures = {
        'FindWindowW': ((W.LPCWSTR, W.LPCWSTR), W.HWND),
        'GetForegroundWindow': ((), W.HWND),
        'GetClientRect': ((W.HWND, C.POINTER(W.RECT)), W.BOOL),
        'ClientToScreen': ((W.HWND, C.POINTER(W.POINT)), W.BOOL),
        'GetCursorPos': ((C.POINTER(W.POINT),), W.BOOL),
        'GetAncestor': ((W.HWND, W.UINT), W.HWND),
        'SetWindowPos': ((W.HWND, W.HWND, C.c_int, C.c_int, C.c_int, C.c_int, W.UINT), W.BOOL),
        'GetWindowLongW': ((W.HWND, C.c_int), W.LONG),
        'SetWindowLongW': ((W.HWND, C.c_int, W.LONG), W.LONG),
        'GetAsyncKeyState': ((C.c_int,), C.c_short),
        'SendInput': ((W.UINT, C.POINTER(Input), C.c_int), W.UINT),
    }
    for name, (arguments, result) in signatures.items():
        function = getattr(user, name)
        function.argtypes, function.restype = arguments, result
    user.SetProcessDpiAwarenessContext.argtypes = (C.c_void_p,)
    user.SetProcessDpiAwarenessContext.restype = W.BOOL
    user.SetProcessDpiAwarenessContext(C.c_void_p(-4))
    return user


def bounds(user, window):
    area, origin = W.RECT(), W.POINT()
    if not user.GetClientRect(window, C.byref(area)) or not user.ClientToScreen(window, C.byref(origin)):
        return None
    if area.right < 80 or area.bottom < 80:
        return None
    return origin.x, origin.y, origin.x + area.right, origin.y + area.bottom


def click(user):
    events = (Input * 2)(Input(0, MouseInput(flags=2)), Input(0, MouseInput(flags=4)))
    count = user.SendInput(2, events, C.sizeof(Input))
    if count == 1:
        user.SendInput(1, C.byref(events[1]), C.sizeof(Input))
    return count == 2


def cursor_inside(user, region):
    cursor = W.POINT()
    left, top, right, bottom = region
    return bool(user.GetCursorPos(C.byref(cursor)) and
                left <= cursor.x < right and top <= cursor.y < bottom)


def run(user, target, args):
    root = tk.Tk()
    root.withdraw()
    root.overrideredirect(True)
    root.attributes('-transparentcolor', KEY)
    canvas = tk.Canvas(root, bg=KEY, bd=0, highlightthickness=0)
    canvas.pack(fill='both', expand=True)
    root.update_idletasks()
    wrapper = user.GetAncestor(root.winfo_id(), 2)
    if not wrapper:
        root.destroy()
        raise RuntimeError('Não foi possível criar a janela do overlay.')
    user.SetWindowLongW(wrapper, -20, user.GetWindowLongW(wrapper, -20) | 0x08000020)
    geometry = None
    last_click = 0.0
    error = None

    def tick():
        nonlocal geometry, last_click, error
        try:
            if user.GetAsyncKeyState(0x78) & 0x8000:  # F9
                root.destroy()
                return
            region = bounds(user, target) if user.GetForegroundWindow() == target else None
            if region is None:
                if geometry is not None:
                    root.withdraw()
                    geometry = None
            else:
                rgb = np.asarray(ImageGrab.grab(bbox=region, all_screens=True, include_layered_windows=False))
                boxes, aim = detect(rgb, args.colors, args.min_area)
                if geometry != region:
                    x, y, right, bottom = region
                    root.geometry(f'{right-x}x{bottom-y}')
                    root.deiconify()
                    root.update_idletasks()
                    user.SetWindowPos(wrapper, W.HWND(-1), x, y, right-x, bottom-y, 0x0010)
                    geometry = region
                canvas.delete('all')
                for name, x, y, w, h in boxes:
                    canvas.create_rectangle(x-3, y-3, x+w+3, y+h+3, outline=INK, width=2)
                    canvas.create_text(x, max(4, y-18), text=name.upper(), fill=INK, anchor='nw')
                armed = args.trigger and bool(user.GetAsyncKeyState(0x77) & 0x8000)
                status = 'ALVO NA MIRA' if aim else f'{len(boxes)} alvo(s)'
                canvas.create_text(12, 12, anchor='nw', fill=INK,
                                   text=f'PIXEL AIM LAB   |   {status}   |   {"ARMADO" if armed else "VISUAL"}')
                now = time.monotonic()
                if (aim and armed and now-last_click >= args.cooldown / 1000
                        and cursor_inside(user, region) and user.GetForegroundWindow() == target
                        and user.GetAsyncKeyState(0x77) & 0x8000):
                    last_click = now
                    if not click(user):
                        args.trigger = False
                        print('O Windows bloqueou o clique. Modo visual mantido.', file=sys.stderr)
            root.after(30, tick)
        except Exception as exc:
            error = exc
            root.destroy()

    root.after(0, tick)
    root.mainloop()
    if error:
        raise error


def main():
    parser = argparse.ArgumentParser(description='Overlay por cor para janelas no Windows.')
    parser.add_argument('--window', required=True, help='título exato da janela alvo')
    parser.add_argument('--colors', nargs='+', choices=PROFILES, default=list(PROFILES))
    parser.add_argument('--trigger', action='store_true', help='habilita clique enquanto F8 estiver pressionado')
    parser.add_argument('--cooldown', type=int, default=180, help='intervalo mínimo entre cliques em ms')
    parser.add_argument('--min-area', type=int, default=55, help='área mínima de um alvo, em pixels')
    args = parser.parse_args()
    if sys.platform != 'win32':
        parser.error('a captura e o overlay requerem Windows')
    if args.cooldown < 100 or args.min_area < 1:
        parser.error('use cooldown de pelo menos 100 ms e área mínima positiva')
    user = windows_api()
    target = user.FindWindowW(None, args.window)
    if not target:
        parser.error(f'janela não encontrada: {args.window!r}')
    print('Clique na janela alvo. F8 arma o clique se habilitado; F9 encerra.', flush=True)
    run(user, target, args)


if __name__ == '__main__':
    main()

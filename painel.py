"""Configuration panel for the separate desktop trigger process."""

import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Event
import tkinter as tk
from tkinter import messagebox, ttk

from demo import open_demo
from desktop import DEFAULTS, KEYS, run
from overlay import BUTTON_FLAGS, windows_api
from vision import PROFILES


def main():
    import os
    profile = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'BNQQ Aim' / 'trigger.json'
    settings = DEFAULTS.copy()
    try:
        settings.update(json.loads(profile.read_text(encoding='utf-8')))
    except (OSError, ValueError, TypeError):
        pass
    windows_api()
    root = tk.Tk()
    root.title('BNQQ Aim | Configuração')
    root.resizable(False, False)
    root.configure(bg='#0d1320')
    style = ttk.Style(root)
    style.theme_use('clam')
    bg, card, fg, accent = '#0d1320', '#161f31', '#e7edf8', '#9bc7ff'
    style.configure('.', background=card, foreground=fg, font=('Segoe UI', 10))
    style.configure('TEntry', fieldbackground=bg, foreground=fg, insertcolor=fg)
    style.configure('TCombobox', fieldbackground=bg, selectbackground=bg, selectforeground=fg)
    style.map('TCombobox', fieldbackground=[('readonly', bg)], foreground=[('readonly', fg)])
    style.configure('Accent.TButton', background='#275bc0', foreground='white', padding=8)
    style.map('Accent.TButton', background=[('disabled', '#243148'), ('active', '#356ddd')])
    style.map('TCheckbutton', background=[('active', card)], foreground=[('active', accent)])
    tk.Label(root, text='BNQQ AIM', bg=bg, fg=fg, font=('Segoe UI', 24, 'bold')).grid(row=0, columnspan=2, sticky='w', padx=24, pady=(15, 0))
    tk.Label(root, text='MIRA POR COR   /   WINDOWS', bg=bg, fg=accent, font=('Segoe UI', 9, 'bold')).grid(row=1, columnspan=2, sticky='w', padx=25, pady=(0, 14))
    panel = ttk.Frame(root, padding=18)
    panel.grid(row=2, column=0, sticky='nsew', padx=(24, 10), pady=(0, 18))
    ttk.Label(panel, text='TRIGGER  /  CONTROLES', foreground=accent).grid(row=0, columnspan=2, sticky='w')
    ttk.Label(panel, text='Cores monitoradas').grid(row=1, columnspan=2, sticky='w', pady=(10, 5))
    swatches = ttk.Frame(panel)
    swatches.grid(row=2, columnspan=2, sticky='w', pady=(0, 12))
    colors = {color: tk.BooleanVar(value=color in settings['colors']) for color in PROFILES}
    for color, variable in colors.items():
        ttk.Checkbutton(swatches, text=color.capitalize(), variable=variable).pack(side='left', padx=(0, 13))
    values = {}
    fields = [('key', 'Tecla para segurar', list(KEYS)), ('button', 'Botão do mouse', list(BUTTON_FLAGS)),
              ('delay_ms', 'Atraso inicial (ms)', None), ('interval_ms', 'Intervalo (ms)', None),
              ('burst', 'Cliques (0 = contínuo)', None)]
    for row, (name, label, options) in enumerate(fields, 3):
        ttk.Label(panel, text=label).grid(row=row, column=0, sticky='w', pady=3)
        value = values[name] = tk.StringVar(value=str(settings[name]))
        control = (ttk.Combobox(panel, textvariable=value, values=options, state='readonly', width=16)
                   if options else ttk.Entry(panel, textvariable=value, width=19))
        control.grid(row=row, column=1, sticky='ew', padx=(16, 0))

    aim_panel = ttk.Frame(root, padding=18)
    aim_panel.grid(row=2, column=1, sticky='nsew', padx=(0, 24), pady=(0, 18))
    ttk.Label(aim_panel, text='AIM COLOR  /  CAMPO DE VISÃO', foreground=accent).grid(row=0, columnspan=2, sticky='w')
    aim_enabled = tk.BooleanVar(value=settings['aim_enabled'])
    trigger_enabled = tk.BooleanVar(value=True)
    ttk.Checkbutton(panel, text='Habilitar disparo', variable=trigger_enabled).grid(row=8, columnspan=2, sticky='w', pady=(10, 0))
    ttk.Checkbutton(aim_panel, text='Habilitar mira por cor', variable=aim_enabled).grid(row=1, columnspan=2, sticky='w', pady=(8, 0))
    preview = tk.Canvas(aim_panel, width=248, height=128, bg=bg, highlightthickness=0)
    preview.grid(row=2, columnspan=2, pady=8)
    values['aim_key'] = tk.StringVar(value=settings['aim_key'])
    ttk.Label(aim_panel, text='Tecla da mira').grid(row=3, column=0, sticky='w')
    ttk.Combobox(aim_panel, textvariable=values['aim_key'], values=list(KEYS), state='readonly', width=10).grid(row=3, column=1, sticky='e')
    for row, (name, label, low, high) in enumerate((('fov_px', 'Raio FOV', 25, 240), ('smoothing', 'Suavização', 1, 12)), 4):
        values[name] = tk.IntVar(value=settings[name])
        ttk.Label(aim_panel, textvariable=values[name], foreground=accent).grid(row=row, column=1, sticky='e')
        slider = tk.Scale(aim_panel, label=label, variable=values[name], from_=low, to=high, showvalue=False,
                          orient='horizontal', length=200, bg=card, fg=fg, troughcolor=bg,
                          activebackground=accent, highlightthickness=0, bd=0)
        slider.grid(row=row, column=0, sticky='w')

    def redraw(*_):
        preview.delete('all')
        r = 13 + values['fov_px'].get() * 0.19
        preview.create_oval(124-r, 64-r, 124+r, 64+r, outline=accent, width=2)
        preview.create_line(114, 64, 134, 64, fill=fg)
        preview.create_line(124, 54, 124, 74, fill=fg)
        for name, x, y, ink in (('amarelo', 88, 57, '#ffd51c'), ('roxo', 151, 45, '#a63fff'), ('vermelho', 143, 91, '#f02b3e')):
            preview.create_oval(x-5, y-5, x+5, y+5, fill=ink if colors[name].get() else '#344259', outline='')

    for variable in (*colors.values(), values['fov_px']):
        variable.trace_add('write', redraw)
    redraw()

    status = tk.StringVar(value='Parado · F9 encerra o processo externo')
    worker = None
    stop_event = Event()
    executor = ThreadPoolExecutor(max_workers=1)

    def start():
        nonlocal worker
        config = {name: value.get() for name, value in values.items()}
        config['colors'] = [name for name, selected in colors.items() if selected.get()]
        config['aim_enabled'] = aim_enabled.get()
        try:
            for name in ('delay_ms', 'interval_ms', 'burst'):
                config[name] = int(config[name])
            if (not config['colors'] or config['delay_ms'] < 0 or
                    config['interval_ms'] < 50 or config['burst'] < 0 or
                    not (trigger_enabled.get() or config['aim_enabled'])):
                raise ValueError
            profile.parent.mkdir(parents=True, exist_ok=True)
            profile.write_text(json.dumps(config, indent=2), encoding='utf-8')
            stop_event.clear()
            worker = executor.submit(run, config, trigger_enabled.get(), stop_event)
        except ValueError:
            messagebox.showerror('Confira a configuração', 'Escolha uma cor e informe números válidos. Intervalo mínimo de 50 ms.')
            return
        except OSError as error:
            messagebox.showerror('Falha ao iniciar', str(error))
            return
        start_button.state(['disabled'])
        stop_button.state(['!disabled'])
        status.set('Ativo · segure a tecla de cada função · F9 encerra')
        root.iconify()

    def stop():
        stop_event.set()

    def poll():
        nonlocal worker
        if worker is not None and worker.done():
            error = worker.exception()
            worker = None
            start_button.state(['!disabled'])
            stop_button.state(['disabled'])
            status.set('Parado · F9 encerra o processo externo')
            if error:
                root.deiconify()
                messagebox.showerror('BNQQ Aim', str(error), parent=root)
        root.after(250, poll)

    def close():
        stop()
        executor.shutdown(wait=False)
        root.destroy()

    start_button = ttk.Button(panel, text='Iniciar BNQQ Aim', command=start, style='Accent.TButton')
    start_button.grid(row=9, column=0, sticky='ew', pady=(15, 4))
    stop_button = ttk.Button(panel, text='Parar', command=stop, state='disabled')
    stop_button.grid(row=9, column=1, sticky='ew', padx=(16, 0), pady=(15, 4))
    ttk.Label(panel, textvariable=status).grid(row=10, columnspan=2, sticky='w', pady=(7, 0))
    ttk.Button(aim_panel, text='Abrir demo de alvos', command=lambda: open_demo(root)).grid(row=6, columnspan=2, sticky='ew', pady=(8, 0))
    root.protocol('WM_DELETE_WINDOW', close)
    poll()
    root.mainloop()


if __name__ == '__main__':
    main()

import tkinter as tk


def open_demo(parent=None):
    window = tk.Toplevel(parent) if parent is not None else tk.Tk()
    window.title('Pixel Aim Lab Demo')
    window.geometry('760x440')
    canvas = tk.Canvas(window, bg='#141d29', highlightthickness=0)
    canvas.pack(fill='both', expand=True)
    colors = ('#ffd51c', '#a63fff', '#f02b3e')
    shots = 0

    def paint(_=None):
        canvas.delete('all')
        w, h = canvas.winfo_width(), canvas.winfo_height()
        canvas.create_text(w/2, 60, text='BNQQ AIM  /  DEMO', fill='#e1e8f0', font=('Consolas', 18))
        for index, color in enumerate(colors, 1):
            x, y = w * index / 4, h / 2
            canvas.create_oval(x-30, y-30, x+30, y+30, fill=color, outline='')
        canvas.create_text(w/2, h-62, text=f'Cliques recebidos: {shots}', fill='#e1e8f0', font=('Consolas', 16))

    def fired(_):
        nonlocal shots
        shots += 1
        paint()

    canvas.bind('<Configure>', paint)
    canvas.bind('<Button-1>', fired)
    return window, canvas


if __name__ == '__main__':
    demo, _ = open_demo()
    demo.mainloop()

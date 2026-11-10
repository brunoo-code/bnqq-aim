import tkinter as tk


def open_demo(parent=None):
    window = tk.Toplevel(parent) if parent is not None else tk.Tk()
    window.title('Pixel Aim Lab Demo')
    window.geometry('760x440')
    canvas = tk.Canvas(window, bg='#141d29', highlightthickness=0)
    canvas.pack(fill='both', expand=True)
    target_color = '#f02b3e'
    radius = 5
    hits = 0
    misses = 0

    def paint(_=None):
        canvas.delete('all')
        w, h = canvas.winfo_width(), canvas.winfo_height()
        canvas.create_text(w/2, 60, text='BNQQ AIM  /  DEMO', fill='#e1e8f0', font=('Consolas', 18))
        for x, y in target_centers():
            canvas.create_oval(x-radius, y-radius, x+radius, y+radius, fill=target_color, outline='')
        canvas.create_text(w/2, h-62, text=f'Acertos: {hits}   |   Fora: {misses}', fill='#e1e8f0', font=('Consolas', 16))

    def target_centers():
        w, h = canvas.winfo_width(), canvas.winfo_height()
        return [(w * index // 4, h // 2) for index in range(1, 4)]

    def fired(event):
        nonlocal hits, misses
        if any((event.x-x)**2 + (event.y-y)**2 <= radius**2 for x, y in target_centers()):
            hits += 1
        else:
            misses += 1
        paint()

    canvas.bind('<Configure>', paint)
    canvas.bind('<Button-1>', fired)
    return window, canvas


if __name__ == '__main__':
    demo, _ = open_demo()
    demo.mainloop()

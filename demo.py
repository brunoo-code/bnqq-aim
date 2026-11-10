import tkinter as tk


root = tk.Tk()
root.title('Pixel Aim Lab Demo')
root.geometry('760x440')
canvas = tk.Canvas(root, bg='#141d29', highlightthickness=0)
canvas.pack(fill='both', expand=True)
colors = ('#ffd51c', '#a63fff', '#f02b3e')
shots = 0


def paint(_=None):
    canvas.delete('all')
    w, h = canvas.winfo_width(), canvas.winfo_height()
    canvas.create_text(w/2, 60, text='PIXEL AIM LAB  /  TEST RANGE', fill='#e1e8f0', font=('Consolas', 18))
    for index in range(3):
        x = w * (index+1) / 4
        y = h / 2
        canvas.create_oval(x-30, y-30, x+30, y+30, fill=colors[(index+shots)%3], outline='')
    canvas.create_text(w/2, h-62, text=f'Cliques recebidos: {shots}', fill='#e1e8f0', font=('Consolas', 16))


def fired(_):
    global shots
    shots += 1
    paint()


canvas.bind('<Configure>', paint)
canvas.bind('<Button-1>', fired)
root.mainloop()

import tkinter as tk
import tkinter.messagebox as msgbox
dif=None
def chose(root,difficulty:str):
    global dif
    dif=difficulty
    root.destroy()

def ui():
    root = tk.Tk()
    root.geometry("1200x600")
    root.title("Flappy Bird")
    box=tk.Frame(root)
    box.pack()
    label1=tk.Label(box,text="Flappy Bird",font=("",50))
    label2=tk.Label(box,text="选择难度开始游戏",font=("",30))
    button1=tk.Button(box,text="新手",command=lambda:chose(root,"新手"))
    button2=tk.Button(box,text="简单",command=lambda:chose(root,"简单"))
    button3=tk.Button(box,text="普通",command=lambda:chose(root,"普通"))
    button4=tk.Button(box,text="困难",command=lambda:chose(root,"困难"))
    button5=tk.Button(box,text="地狱",command=lambda:chose(root,"地狱"))
    label1.grid(column=0,row=1)
    label2.grid(column=0,row=2)
    button1.grid(column=0,row=3)
    button2.grid(column=0,row=4)
    button3.grid(column=0,row=5)
    button4.grid(column=0,row=6)
    button5.grid(column=0,row=7)
    root.mainloop()
    return dif

if __name__ == '__main__':
    print(ui())
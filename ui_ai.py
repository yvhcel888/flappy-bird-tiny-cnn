import tkinter as tk

def chose(root, difficulty, bird_num, ai_mode):
    """
    点击开始游戏后触发的函数
    解决 alloc: invalid block 的关键在于安全地清理 Canvas
    """
    # 1. 先清空 Canvas 上的所有绘制元素（释放图片和图形的底层内存）
    if hasattr(root, 'canvas'):
        root.canvas.delete("all")

    # 2. 强制处理完挂起的事件
    root.update()

    # 3. 安全退出 mainloop 并销毁窗口
    root.quit()
    root.destroy()

    # 4. 记录返回值
    root.result = (difficulty, bird_num, ai_mode)


def ui():
    root = tk.Tk()
    root.geometry("1200x600")
    root.title("Flappy Bird - 准备出发")
    root.resizable(False, False)

    # 处理右上角关闭按钮
    root.result = (None, None, None) # 默认返回 None
    root.protocol("WM_DELETE_WINDOW", lambda: chose(root, None, None, None))

    # 深色背景
    canvas = tk.Canvas(root, width=1200, height=600, bg="#1E293B", highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    root.canvas = canvas  # 挂载到 root 上，方便在 chose 中清理

    # 标题
    canvas.create_text(600, 60, text="Flappy Bird", font=("微软雅黑", 50, "bold"), fill="#F8FAFC")
    canvas.create_text(600, 130, text="请选择你的小鸟和难度", font=("微软雅黑", 18), fill="#94A3B8")

    state = {
        "bird": 1,
        "diff": "普通",
        "ai_mode": tk.BooleanVar(value=False) # AI 模式状态
    }

    # ================= 1. 左侧：选鸟 =================
    bird_images = {}  # 必须保留引用，否则图片不显示
    bird_cards = []

    # 请确保这些路径下有你对应的 png 图片！
    bird_paths = {
        1: "./img/bird/Transparent/Blue Bird/PNG/frame-1.png",
        2: "./img/bird/Transparent/Green Bird/PNG/frame-1.png",
        3: "./img/bird/Transparent/Pink Bird/PNG/frame-1.png",
        4: "./img/bird/Transparent/Yellow Bird/PNG/frame-1.png"
    }
    bird_names = {1: "蓝鸟", 2: "绿鸟", 3: "粉鸟", 4: "黄鸟"}

    canvas.create_text(300, 190, text="选择小鸟", font=("微软雅黑", 20, "bold"), fill="#E2E8F0")

    for i, b_id in enumerate([1, 2, 3, 4]):
        x = 150 + i * 100
        y = 280

        # 卡片背景
        border_color = "#3B82F6" if b_id == 1 else "#475569"
        card = canvas.create_rectangle(x - 40, y - 40, x + 40, y + 40, fill="#334155", outline=border_color, width=3,
                                       tags=f"bird_{b_id}")

        # 加载图片
        try:
            img = tk.PhotoImage(file=bird_paths[b_id])
            # 缩小图片，4 表示缩小到 1/4。如果还是太大，改成 5 或 6
            img = img.subsample(20, 20)
            bird_images[b_id] = img
            canvas.create_image(x, y, image=img, tags=f"bird_{b_id}")
        except Exception as e:
            print(f"加载鸟图片失败 {bird_paths[b_id]}: {e}")
            # 图片找不到时，画个圆代替
            canvas.create_oval(x - 20, y - 20, x + 20, y + 20, fill="red", tags=f"bird_{b_id}")

        canvas.create_text(x, y + 60, text=bird_names[b_id], font=("微软雅黑", 14), fill="#CBD5E1")
        bird_cards.append((b_id, card))

    def select_bird(b_id):
        state["bird"] = b_id
        for cid, card_item in bird_cards:
            if cid == b_id:
                canvas.itemconfig(card_item, outline="#3B82F6", width=4)
            else:
                canvas.itemconfig(card_item, outline="#475569", width=2)

    for b_id, _ in bird_cards:
        canvas.tag_bind(f"bird_{b_id}", "<Button-1>", lambda e, bid=b_id: select_bird(bid))
        canvas.tag_bind(f"bird_{b_id}", "<Enter>", lambda e: canvas.config(cursor="hand2"))
        canvas.tag_bind(f"bird_{b_id}", "<Leave>", lambda e: canvas.config(cursor=""))

    # ================= 2. 右侧：选难度 =================
    canvas.create_text(900, 190, text="选择难度", font=("微软雅黑", 20, "bold"), fill="#E2E8F0")

    difficulties = ["新手", "简单", "普通", "困难", "地狱"]
    diff_buttons = []

    for i, d_name in enumerate(difficulties):
        y = 240 + i * 65
        is_selected = (d_name == state["diff"])
        bg_color = "#3B82F6" if is_selected else "#334155"

        rect = canvas.create_rectangle(750, y - 25, 1050, y + 25, fill=bg_color, outline="", tags=f"diff_{i}")
        text = canvas.create_text(900, y, text=d_name, font=("微软雅黑", 16, "bold"), fill="white", tags=f"diff_{i}")
        diff_buttons.append((d_name, rect, text))

    def select_diff(d_name):
        state["diff"] = d_name
        for btn_name, rect_item, text_item in diff_buttons:
            if btn_name == d_name:
                canvas.itemconfig(rect_item, fill="#3B82F6")
            else:
                canvas.itemconfig(rect_item, fill="#334155")

    for i, (d_name, rect, text) in enumerate(diff_buttons):
        canvas.tag_bind(f"diff_{i}", "<Button-1>", lambda e, d=d_name: select_diff(d))
        canvas.tag_bind(f"diff_{i}", "<Enter>", lambda e: canvas.config(cursor="hand2"))
        canvas.tag_bind(f"diff_{i}", "<Leave>", lambda e: canvas.config(cursor=""))

    # ================= 3. 底部：AI勾选框 =================
    ai_check = tk.Checkbutton(
        canvas, text="启用 AI 游玩", variable=state["ai_mode"],
        bg="#1E293B", fg="#F8FAFC", selectcolor="#334155",
        font=("微软雅黑", 16), activebackground="#1E293B", activeforeground="#F8FAFC"
    )
    # 用 create_window 将 Tkinter 原生组件放入 Canvas
    canvas.create_window(600, 480, window=ai_check)

    # ================= 4. 底部：开始游戏按钮 =================
    start_btn_bg = canvas.create_rectangle(450, 520, 750, 580, fill="#10B981", outline="", tags="start_btn")
    canvas.create_text(600, 550, text="开始游戏", font=("微软雅黑", 22, "bold"), fill="white", tags="start_btn")

    # 绑定点击事件，传入 AI 模式的状态值
    canvas.tag_bind("start_btn", "<Button-1>", lambda e: chose(root, state["diff"], state["bird"], state["ai_mode"].get()))
    canvas.tag_bind("start_btn", "<Enter>",
                    lambda e: [canvas.itemconfig(start_btn_bg, fill="#059669"), canvas.config(cursor="hand2")])
    canvas.tag_bind("start_btn", "<Leave>",
                    lambda e: [canvas.itemconfig(start_btn_bg, fill="#10B981"), canvas.config(cursor="")])

    # 窗口居中
    root.update_idletasks()
    x = (root.winfo_screenwidth() - 1200) // 2
    y = (root.winfo_screenheight() - 600) // 2
    root.geometry(f"+{x}+{y}")

    root.mainloop()
    return root.result


if __name__ == '__main__':
    # 测试：运行菜单，打印结果
    result = ui()
    print("用户选择:", result)
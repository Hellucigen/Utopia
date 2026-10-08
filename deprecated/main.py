# main.py (GUI version with Tkinter, full modified version with immediate refresh)
from utils import normalize_concept, generate_node_id
import threading
import time
import sys
import queue  # For thread-safe communication
import tkinter as tk
from tkinter import scrolledtext
from attention_framework import AttentionFramework

# 全局标志位，控制线程退出
RUNNING = True


def cognitive_heartbeat(af, update_queue):
    """
    后台认知线程：模拟大脑的实时运作。
    将状态更新放入队列，由主线程处理UI更新。
    """
    global RUNNING

    while RUNNING:
        time.sleep(1.0)  # 模拟 1 秒的时间流逝

        # --- 1. 执行认知步 (扩散 & 衰减 & 模式回归) ---
        af.step()

        # --- 2. DMN 游荡逻辑 ---
        drift_msg = None
        if af.am.lambda_mode < 0.4:
            drift_msg = af.am.drift()

        # --- 3. 获取当前状态 ---
        mode_val = af.am.lambda_mode
        mode_str = "🔥 CEN (专注)" if mode_val > 0.5 else "💤 DMN (游荡)"

        top_node_id = af.am.get_top_node()
        focus_name = "无"
        if top_node_id:
            node = af.graph.get_node(top_node_id)
            focus_name = node.attributes.get("name", top_node_id)
            activation = af.am.get_activation(top_node_id)
            focus_str = f"{focus_name} ({activation:.2f})"
        else:
            focus_str = "放空"

        # --- 4. 准备状态行并放入队列 ---
        status_line = f"[状态] {mode_str} | 🧠 焦点: {focus_str}"
        if drift_msg:
            status_line += f" | {drift_msg}"
        update_queue.put(status_line + "\n")


def main_gui():
    global RUNNING

    # 初始化认知架构
    af = AttentionFramework()

    # 创建队列用于线程通信
    update_queue = queue.Queue()

    # 启动后台认知线程
    t = threading.Thread(target=cognitive_heartbeat, args=(af, update_queue), daemon=True)
    t.start()

    # 创建Tkinter GUI
    root = tk.Tk()
    root.title("Haru 认知系统 (实时版)")
    root.geometry("600x400")

    # 上部：状态显示区（滚动文本框）
    status_label = tk.Label(root, text="系统状态（思维过程）：")
    status_label.pack(anchor="w", padx=10, pady=5)

    status_text = scrolledtext.ScrolledText(root, height=15, wrap=tk.WORD, state='normal')
    status_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    # 下部：输入区
    input_frame = tk.Frame(root)
    input_frame.pack(fill=tk.X, padx=10, pady=10)

    input_label = tk.Label(input_frame, text="🗣️ 输入：")
    input_label.pack(side=tk.LEFT)

    entry = tk.Entry(input_frame)
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def submit_input():
        user_input = entry.get().strip()
        entry.delete(0, tk.END)  # 清空输入框
        if user_input.lower() in ["quit", "exit", "q"]:
            RUNNING = False
            root.quit()
            return
        if user_input:
            af.inject_text(user_input)
            # 可选：将用户输入也显示到状态区
            status_text.insert(tk.END, f"用户输入: {user_input}\n")
            status_text.see(tk.END)

            # 新增：立即计算并显示新状态，确保焦点切换
            mode_str = "🔥 CEN (专注)" if af.am.lambda_mode > 0.5 else "💤 DMN (游荡)"
            top_node_id = af.am.get_top_node()
            focus_str = "放空" if not top_node_id else f"{af.graph.get_node(top_node_id).attributes.get('name', top_node_id)} ({af.am.get_activation(top_node_id):.2f})"
            status_line = f"[状态] {mode_str} | 🧠 焦点: {focus_str}"
            status_text.insert(tk.END, status_line + "\n")
            status_text.see(tk.END)

    submit_button = tk.Button(input_frame, text="提交", command=submit_input)
    submit_button.pack(side=tk.LEFT, padx=5)

    # 绑定Enter键提交
    entry.bind("<Return>", lambda event: submit_input())

    # 主循环：检查队列并更新UI
    def check_queue():
        try:
            while not update_queue.empty():
                msg = update_queue.get_nowait()
                status_text.insert(tk.END, msg)
                status_text.see(tk.END)  # 滚动到最新
        except queue.Empty:
            pass
        if RUNNING:
            root.after(100, check_queue)  # 每100ms检查一次

    # 启动队列检查
    check_queue()

    # 初始消息
    status_text.insert(tk.END, "=== Haru 认知系统 (实时版) ===\n")
    status_text.insert(tk.END, "系统正在后台思考。你可以随时输入文字打断它。\n")
    status_text.insert(tk.END, "当你不说话时，它会自己进入 DMN 模式游荡。\n")
    status_text.see(tk.END)

    # 运行GUI主循环
    root.mainloop()

    # 清理
    RUNNING = False
    print("\n👋 系统关闭。")


if __name__ == "__main__":
    main_gui()
# -*- coding: utf-8 -*-
"""
主程序（UI 界面 + 动画控制 + 事件响应）。
基于 Tkinter 实现，不依赖第三方库，开箱即运行。
运行方式：python main.py
"""
import random
import tkinter as tk
from tkinter import ttk

from sorters import ALGORITHMS, ALGO_INFO

# 各状态对应的柱子颜色
COLOR_DEFAULT = "#4FC3F7"   # 普通未排序柱：浅蓝
COLOR_COMPARE = "#FF9800"   # 正在比较：橙色
COLOR_SWAP = "#F44336"      # 正在交换：红色
COLOR_SORTED = "#4CAF50"    # 已排序：绿色
COLOR_PIVOT = "#9C27B0"     # 快速排序基准：紫色


class SortVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("排序算法可视化演示器")
        self.root.geometry("900x650")
        self.root.minsize(760, 560)

        # 运行状态
        self.data = []            # 当前数组
        self.original_data = []   # 初始数组快照（用于重置）
        self.gen = None           # 当前排序生成器
        self.playing = False      # 是否正在自动播放
        self.compare_count = 0    # 比较次数
        self.swap_count = 0       # 交换次数
        self.sorted_set = set()   # 已排序的下标
        self.highlight = {}       # 临时高亮 {下标: 颜色}
        self.current_step = ""    # 当前步骤说明文字

        self._build_controls()
        self._build_canvas()
        self.generate_data()

    # ---------------- 控件区 ----------------
    def _build_controls(self):
        bar = ttk.Frame(self.root, padding=(8, 6))
        bar.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(bar, text="算法：").pack(side=tk.LEFT)
        self.algo_var = tk.StringVar(value="冒泡排序")
        self.algo_box = ttk.Combobox(
            bar, textvariable=self.algo_var, state="readonly",
            values=list(ALGORITHMS.keys()), width=10
        )
        self.algo_box.pack(side=tk.LEFT, padx=(0, 8))
        self.algo_box.bind("<<ComboboxSelected>>", lambda e: self.reset())

        ttk.Button(bar, text="随机生成", command=self.generate_data).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text="开始", command=self.start).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text="暂停", command=self.pause).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text="单步", command=self.step_once).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text="重置", command=self.reset).pack(side=tk.LEFT, padx=2)

        # 速度滑块：数值越大越快（延迟越小）
        ttk.Label(bar, text="速度").pack(side=tk.LEFT, padx=(12, 2))
        self.speed = tk.IntVar(value=5)
        ttk.Scale(bar, from_=1, to=10, variable=self.speed,
                  orient=tk.HORIZONTAL, length=90).pack(side=tk.LEFT)

        # 数据数量滑块
        ttk.Label(bar, text="数量").pack(side=tk.LEFT, padx=(12, 2))
        self.size = tk.IntVar(value=25)
        ttk.Scale(bar, from_=8, to=60, variable=self.size,
                  orient=tk.HORIZONTAL, length=90,
                  command=lambda e: self.generate_data()).pack(side=tk.LEFT)

        # 底部信息栏
        self.info = ttk.Label(self.root, text="", padding=(8, 4))
        self.info.pack(side=tk.BOTTOM, fill=tk.X)

    def _build_canvas(self):
        self.canvas = tk.Canvas(self.root, bg="#FAFAFA", highlightthickness=0)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # ---------------- 数据与绘制 ----------------
    def generate_data(self):
        """随机生成一组新数据并停止当前排序。"""
        n = int(self.size.get())
        self.data = [random.randint(10, 100) for _ in range(n)]
        self.original_data = list(self.data)
        self.reset()

    def reset(self):
        """恢复到初始未排序状态，准备重新排序。"""
        self.playing = False
        self.data = list(self.original_data)
        self.gen = None
        self.compare_count = 0
        self.swap_count = 0
        self.sorted_set = set()
        self.highlight = {}
        self.current_step = "就绪：选择算法后点击“开始”或“单步”。"
        self.draw_bars()
        self.update_info()

    def draw_bars(self):
        """根据 self.data 重绘柱状图。"""
        self.canvas.delete("all")
        cw = self.canvas.winfo_width() or 860
        ch = self.canvas.winfo_height() or 480
        n = len(self.data)
        if n == 0:
            return
        bar_w = cw / n
        max_val = max(self.data)

        for i, value in enumerate(self.data):
            x0 = i * bar_w
            x1 = x0 + bar_w - 1
            h = (value / max_val) * (ch - 30)
            y1 = ch - 20
            y0 = y1 - h

            if i in self.highlight:
                color = self.highlight[i]
            elif i in self.sorted_set:
                color = COLOR_SORTED
            else:
                color = COLOR_DEFAULT
            self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")
    # ---------------- 动画控制 ----------------
    def _ensure_generator(self):
        """若生成器尚未创建，则按所选算法基于当前数据创建。"""
        if self.gen is None:
            algo_name = self.algo_var.get()
            self.gen = ALGORITHMS[algo_name](self.data)
            self.current_step = "开始执行：" + algo_name

    def start(self):
        """开始自动播放。"""
        self._ensure_generator()
        if not self.playing:
            self.playing = True
            self._tick()

    def pause(self):
        """暂停自动播放。"""
        self.playing = False

    def step_once(self):
        """单步执行一个动作（不自动连续播放）。"""
        self.playing = False
        self._ensure_generator()
        self._run_one_step()

    def _tick(self):
        """自动播放的时间片：每执行一步后按速度决定下次调度。"""
        if not self.playing:
            return
        done = self._run_one_step()
        if done:
            return
        # 速度 1~10 映射为延迟 280ms ~ 40ms
        delay = max(40, 300 - self.speed.get() * 26)
        self.root.after(delay, self._tick)

    def _run_one_step(self):
        """从生成器取出下一个动作并应用。返回 True 表示排序结束。"""
        try:
            action = next(self.gen)
        except StopIteration:
            self.playing = False
            self.sorted_set = set(range(len(self.data)))
            self.highlight = {}
            self.current_step = "排序完成！"
            self.draw_bars()
            self.update_info()
            return True
        self.apply_action(action)
        self.draw_bars()
        self.update_info()
        return False

    def apply_action(self, action):
        """把一个排序动作翻译成颜色高亮与计数。"""
        # 每个新动作先清除上一帧的临时高亮（已排序集合保留）
        self.highlight = {}
        t = action["type"]

        if t == "compare":
            i, j = action["i"], action["j"]
            self.compare_count += 1
            self.highlight[i] = COLOR_COMPARE
            self.highlight[j] = COLOR_COMPARE
            self.current_step = f"比较：下标 {i} 与下标 {j}"

        elif t == "swap":
            i, j = action["i"], action["j"]
            self.swap_count += 1
            self.highlight[i] = COLOR_SWAP
            self.highlight[j] = COLOR_SWAP
            self.current_step = f"交换：下标 {i} 与下标 {j}"

        elif t == "overwrite":
            i = action["i"]
            self.highlight[i] = COLOR_SWAP
            self.current_step = f"写入：位置 {i} = {action['value']}"

        elif t == "pivot":
            i = action["i"]
            self.highlight[i] = COLOR_PIVOT
            self.current_step = f"选择基准（pivot）：下标 {i}"

        elif t == "mark_sorted":
            i = action["i"]
            self.sorted_set.add(i)
            self.current_step = f"下标 {i} 已就位"

    def update_info(self):
        """更新底部信息栏。"""
        algo = self.algo_var.get()
        info = ALGO_INFO.get(algo, "")
        text = (f"算法：{algo}    {info}    "
                f"比较次数：{self.compare_count}    交换次数：{self.swap_count}    "
                f"| {self.current_step}")
        self.info.config(text=text)


def main():
    root = tk.Tk()
    app = SortVisualizer(root)
    # 窗口大小变化时重绘，让柱状图自适应
    root.bind("<Configure>", lambda e: app.draw_bars() if e.widget == root else None)
    root.mainloop()


if __name__ == "__main__":
    main()
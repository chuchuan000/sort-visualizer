# -*- coding: utf-8 -*-
"""
排序算法模块（algorithms）。
每个排序算法都是一个生成器（generator），在关键步骤 yield 出动作字典，
供动画控制模块逐步渲染。这样算法逻辑与界面逻辑解耦，
也方便实现暂停、单步、调速。

动作字典格式：
    {"type": "compare",     "i": i, "j": j}        # 比较下标 i 与 j
    {"type": "swap",        "i": i, "j": j}        # 交换下标 i 与 j
    {"type": "overwrite",   "i": i, "value": v}    # 把下标 i 位置写为 v（插入排序用）
    {"type": "pivot",       "i": i}                # 标记 i 为快速排序基准
    {"type": "mark_sorted", "i": i}                # 标记 i 已排好序
"""


def bubble_sort(data):
    """冒泡排序：相邻元素两两比较，较大者逐步"冒泡"到末尾。"""
    n = len(data)
    for i in range(n - 1):
        for j in range(n - 1 - i):
            yield {"type": "compare", "i": j, "j": j + 1}
            if data[j] > data[j + 1]:
                data[j], data[j + 1] = data[j + 1], data[j]
                yield {"type": "swap", "i": j, "j": j + 1}
        yield {"type": "mark_sorted", "i": n - 1 - i}
    if n > 0:
        yield {"type": "mark_sorted", "i": 0}


def selection_sort(data):
    """选择排序：每轮在未排序区选出最小值，放到前面。"""
    n = len(data)
    for i in range(n - 1):
        min_idx = i
        for j in range(i + 1, n):
            yield {"type": "compare", "i": min_idx, "j": j}
            if data[j] < data[min_idx]:
                min_idx = j
        if min_idx != i:
            data[i], data[min_idx] = data[min_idx], data[i]
            yield {"type": "swap", "i": i, "j": min_idx}
        yield {"type": "mark_sorted", "i": i}
    if n > 0:
        yield {"type": "mark_sorted", "i": n - 1}


def insertion_sort(data):
    """插入排序：把未排序元素逐个插入到已排序区的正确位置。"""
    n = len(data)
    if n == 0:
        return
    for i in range(1, n):
        key = data[i]
        j = i - 1
        while j >= 0:
            yield {"type": "compare", "i": j, "j": i}
            if data[j] > key:
                data[j + 1] = data[j]
                yield {"type": "overwrite", "i": j + 1, "value": data[j]}
                j -= 1
            else:
                break
        data[j + 1] = key
        yield {"type": "overwrite", "i": j + 1, "value": key}
    for i in range(n):
        yield {"type": "mark_sorted", "i": i}


def _quick_sort(data, low, high):
    """快速排序递归主体（Lomuto 分区方案）。"""
    if low > high:
        return
    if low == high:
        yield {"type": "mark_sorted", "i": low}
        return
    pivot = data[high]
    yield {"type": "pivot", "i": high}
    i = low  # i 指向"小于基准"区域的下一个空位
    for j in range(low, high):
        yield {"type": "compare", "i": j, "j": high}
        if data[j] < pivot:
            data[i], data[j] = data[j], data[i]
            yield {"type": "swap", "i": i, "j": j}
            i += 1
    data[i], data[high] = data[high], data[i]
    yield {"type": "swap", "i": i, "j": high}
    yield {"type": "mark_sorted", "i": i}
    yield from _quick_sort(data, low, i - 1)
    yield from _quick_sort(data, i + 1, high)


def quick_sort(data):
    """快速排序对外入口。"""
    yield from _quick_sort(data, 0, len(data) - 1)


# 算法注册表：界面通过名称选择对应生成器
ALGORITHMS = {
    "冒泡排序": bubble_sort,
    "选择排序": selection_sort,
    "插入排序": insertion_sort,
    "快速排序": quick_sort,
}

# 各算法的复杂度与说明信息（用于界面展示）
ALGO_INFO = {
    "冒泡排序": "平均 O(n^2)，稳定；相邻两两比较，最大值沉到末尾。",
    "选择排序": "平均 O(n^2)，不稳定；每轮选最小值放到前面。",
    "插入排序": "平均 O(n^2)，稳定；近乎有序时接近 O(n)。",
    "快速排序": "平均 O(n log n)，不稳定；选基准分区，递归处理。",
}
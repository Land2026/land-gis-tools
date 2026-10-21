# -*- coding: utf-8 -*-
"""export_raster_inventory.py —— 影像/数据文件清单盘点（零依赖，纯 Python）

干什么用：
    把一个文件夹（含子文件夹）里的影像、矢量等文件盘点成一张 CSV 清单，
    顺带算出总容量。常用于：影像入库前清点、交给作业单位前核对、
    年底统计数据量、查哪些年份缺影像。

特点：
    - 不需要 ArcGIS，不需要装任何库，命令行直接跑
    - Python 2.7 / 3.x 都能跑（ArcMap 和 ArcGIS Pro 自带的都行）
    - 输出 utf-8-sig 编码，Excel 双击打开不乱码

怎么用（两步）：
    1. 用记事本打开本文件，改下面「参数区」的三行
    2. 命令行执行：  python export_raster_inventory.py
"""

from __future__ import print_function, unicode_literals

import csv
import os
import sys
import time

# ===================== 参数区：只改这里 =====================

# 要盘点的文件夹（Windows 路径前面加 r，或用双斜杠）
SCAN_DIR = r"D:\影像\2025年第二批"

# 清单输出到哪（CSV，可用 Excel 直接打开）
OUT_CSV = r"D:\影像\2025年第二批_清单.csv"

# 只统计这些后缀；留空 [] 表示全部文件
EXT_FILTER = [".tif", ".img", ".shp", ".tiff"]

# ===================== 参数区结束 =====================


def human_size(size_bytes):
    """把字节数转成人看得懂的 KB / MB / GB"""
    size_bytes = float(size_bytes)
    if size_bytes >= 1024 * 1024 * 1024:
        return "%.2f GB" % (size_bytes / 1024.0 / 1024.0 / 1024.0)
    if size_bytes >= 1024 * 1024:
        return "%.2f MB" % (size_bytes / 1024.0 / 1024.0)
    return "%.1f KB" % (size_bytes / 1024.0)


def open_csv_writer(path):
    """兼容 py2 / py3 的 CSV 写入方式，编码 utf-8-sig 防 Excel 乱码"""
    if sys.version_info[0] >= 3:
        return open(path, "w", newline="", encoding="utf-8-sig")
    import codecs
    return codecs.open(path, "w", encoding="utf-8-sig")


def main():
    if not os.path.isdir(SCAN_DIR):
        print("找不到文件夹，请检查 SCAN_DIR：%s" % SCAN_DIR)
        sys.exit(1)

    wanted = [e.lower() for e in EXT_FILTER]
    rows = []
    total_bytes = 0
    ext_count = {}

    print("开始扫描：%s" % SCAN_DIR)
    for root, dirs, files in os.walk(SCAN_DIR):
        for name in files:
            ext = os.path.splitext(name)[1].lower()
            if wanted and ext not in wanted:
                continue
            full_path = os.path.join(root, name)
            try:
                st = os.stat(full_path)
            except OSError:
                continue
            total_bytes += st.st_size
            ext_count[ext] = ext_count.get(ext, 0) + 1
            rows.append({
                "文件名": name,
                "所在文件夹": root,
                "大小": human_size(st.st_size),
                "字节数": st.st_size,
                "修改时间": time.strftime("%Y-%m-%d %H:%M:%S",
                                         time.localtime(st.st_mtime)),
                "后缀": ext,
            })

    # 按文件夹 + 文件名排序，方便核对
    rows.sort(key=lambda r: (r["所在文件夹"], r["文件名"]))

    out_dir = os.path.dirname(OUT_CSV)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    fields = ["文件名", "所在文件夹", "大小", "字节数", "修改时间", "后缀"]
    f = open_csv_writer(OUT_CSV)
    try:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    finally:
        f.close()

    print("")
    print("盘完了，共 %d 个文件" % len(rows))
    for ext, cnt in sorted(ext_count.items()):
        print("  %-6s %d 个" % (ext, cnt))
    print("合计容量：%s" % human_size(total_bytes))
    print("清单已导出：%s" % OUT_CSV)


if __name__ == "__main__":
    main()

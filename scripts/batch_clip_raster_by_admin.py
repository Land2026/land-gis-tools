# -*- coding: utf-8 -*-
"""batch_clip_raster_by_admin.py —— 按行政区批量裁剪影像（arcpy）

干什么用：
    手上一幅（或一批）影像，要按乡镇 / 行政村切成一块一块分头下发。
    手工做法是：选中一个村 → 裁剪 → 改名 → 再选下一个，几十个村能干一下午。
    这个脚本一次跑完，输出文件名就是行政区名，直接能发。

特点：
    - 用的是 Clip_management（数据管理工具），不需要 Spatial Analyst 扩展
    - 自动跳过「影像盖不到的行政区」，不会报错中断
    - 文件名自动清洗非法字符，不会被 Windows 拒收
    - 全程中文日志，跑完写一份 log 文件，方便回头核对
    - Python 2.7（ArcMap 10.x）/ 3.x（ArcGIS Pro）都能跑

怎么用：
    1. 记事本打开本文件，改「参数区」
    2. 用 ArcGIS 自带的 Python 跑（ArcMap 用 IDLE 或命令行；Pro 用 Python 命令提示符）：
           python batch_clip_raster_by_admin.py
"""

from __future__ import print_function, unicode_literals

import os
import re
import sys
import time

import arcpy

# ===================== 参数区：只改这里 =====================

# 待裁剪影像：可以填一个文件夹（自动找里面的 tif/img），也可以填单幅影像路径
IN_RASTER_DIR = r"D:\影像\2025年第二批"
IN_RASTER_FILE = ""                    # 填了这一行就只裁这一幅，留空裁上面整个文件夹

# 行政区矢量（乡镇界 / 村界都行）
ADMIN_SHP = r"D:\基础数据\秋渠乡行政村.shp"

# 用哪个字段的值当输出文件名（村名 / 乡镇名字段）
NAME_FIELD = "村名"

# 只做这几个行政区；留空 [] 表示全部都做
ONLY_THESE = []

# 输出文件夹
OUT_DIR = r"D:\影像\按村裁剪成果"

# 输出格式后缀： .tif 或 .img
OUT_EXT = ".tif"

# 已存在的文件是否覆盖：True 覆盖，False 跳过（省时间）
OVERWRITE = False

# ===================== 参数区结束 =====================

ILLEGAL_CHARS = r'\/:*?"<>|'


def safe_name(name):
    """把行政区名里的非法字符换掉，避免 Windows 存不了"""
    name = str(name).strip()
    for ch in ILLEGAL_CHARS:
        name = name.replace(ch, "_")
    name = re.sub(r"\s+", "", name)
    return name or "未命名"


def log(lines, log_path, text):
    """屏幕打印 + 记进日志"""
    print(text)
    lines.append(text)
    with open(log_path, "a") as f:
        f.write((text + "\n").encode("utf-8") if sys.version_info[0] < 3
                else text + "\n")


def list_rasters():
    """收集待裁剪的影像"""
    if IN_RASTER_FILE and os.path.isfile(IN_RASTER_FILE):
        return [IN_RASTER_FILE]
    if not os.path.isdir(IN_RASTER_DIR):
        raise RuntimeError("找不到影像文件夹：%s" % IN_RASTER_DIR)
    out = []
    for name in sorted(os.listdir(IN_RASTER_DIR)):
        if os.path.splitext(name)[1].lower() in (".tif", ".tiff", ".img"):
            out.append(os.path.join(IN_RASTER_DIR, name))
    return out


def get_admin_names(log_path, lines):
    """读出行政区名列表，并检查字段存在"""
    fields = [f.name for f in arcpy.ListFields(ADMIN_SHP)]
    if NAME_FIELD not in fields:
        raise RuntimeError("矢量里没有「%s」这个字段，现有字段：%s"
                           % (NAME_FIELD, "、".join(fields)))

    names = []
    seen = set()
    with arcpy.da.SearchCursor(ADMIN_SHP, [NAME_FIELD]) as cur:
        for row in cur:
            val = row[0]
            if val is None:
                continue
            key = str(val).strip()
            if not key or key in seen:
                continue
            seen.add(key)
            names.append(key)

    if ONLY_THESE:
        wanted = set(str(x).strip() for x in ONLY_THESE)
        names = [n for n in names if n in wanted]
        miss = wanted - set(names)
        if miss:
            log(lines, log_path, "注意：矢量里找不到这些名字 -> %s" % "、".join(sorted(miss)))
    return names


def main():
    arcpy.env.overwriteOutput = True
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)

    log_path = os.path.join(OUT_DIR, "裁剪日志_%s.txt"
                            % time.strftime("%Y%m%d_%H%M%S"))
    lines = []
    t0 = time.time()

    rasters = list_rasters()
    names = get_admin_names(log_path, lines)
    log(lines, log_path, "影像 %d 幅，行政区 %d 个，共 %d 次裁剪"
        % (len(rasters), len(names), len(rasters) * len(names)))

    ok, skip, fail = 0, 0, 0
    layer = "admin_lyr"

    for raster in rasters:
        base = os.path.splitext(os.path.basename(raster))[0]
        sub_dir = OUT_DIR if len(rasters) == 1 else os.path.join(OUT_DIR, base)
        if not os.path.isdir(sub_dir):
            os.makedirs(sub_dir)

        for raw_name in names:
            out_name = safe_name(raw_name) + OUT_EXT
            out_path = os.path.join(sub_dir, out_name)

            if os.path.exists(out_path) and not OVERWRITE:
                skip += 1
                log(lines, log_path, "跳过（已存在）：%s" % out_name)
                continue

            # 选中这一个行政区
            sql = "\"%s\" = '%s'" % (NAME_FIELD, raw_name.replace("'", "''"))
            try:
                arcpy.MakeFeatureLayer_management(ADMIN_SHP, layer)
                arcpy.SelectLayerByAttribute_management(layer, "NEW_SELECTION", sql)
                cnt = int(arcpy.GetCount_management(layer).getOutput(0))
                if cnt == 0:
                    skip += 1
                    log(lines, log_path, "跳过（矢量里查无此名）：%s" % raw_name)
                    continue

                arcpy.Clip_management(
                    in_raster=raster,
                    rectangle="#",
                    out_raster=out_path,
                    in_template_dataset=layer,
                    nodata_value="0",
                    clipping_geometry="ClippingGeometry",
                )
            except Exception as e:
                fail += 1
                log(lines, log_path, "失败：%s / %s -> %s" % (base, raw_name, e))
                continue
            finally:
                try:
                    arcpy.Delete_management(layer)
                except Exception:
                    pass

            if os.path.exists(out_path):
                ok += 1
                log(lines, log_path, "完成：%s" % os.path.relpath(out_path, OUT_DIR))
            else:
                skip += 1
                log(lines, log_path, "跳过（影像盖不到，无输出）：%s" % raw_name)

    cost = time.time() - t0
    log(lines, log_path, "")
    log(lines, log_path, "全部跑完：成功 %d，跳过 %d，失败 %d，用时 %.1f 分钟"
        % (ok, skip, fail, cost / 60.0))
    log(lines, log_path, "日志：%s" % log_path)


if __name__ == "__main__":
    main()

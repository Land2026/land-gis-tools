# land-gis-tools

国土 / 测绘日常业务的 GIS 批处理脚本集。

想法很简单：**把基层自然资源所里那些重复的、点鼠标点到手酸的活儿，写成脚本一次跑完。**

## 脚本清单

| 脚本 | 干什么 | 依赖 |
|---|---|---|
| `scripts/batch_clip_raster_by_admin.py` | 按乡镇 / 行政村批量裁剪影像，输出文件名直接是行政区名 | arcpy（ArcMap / ArcGIS Pro 均可） |
| `scripts/export_raster_inventory.py` | 盘点文件夹里的影像、矢量，导出 CSV 清单 + 总容量 | 无（纯 Python，装了 Python 就能跑） |

## 怎么用

每个脚本顶部都有「参数区」，只改那几行，其余不用动：

```bat
python export_raster_inventory.py
python batch_clip_raster_by_admin.py
```

- ArcMap 10.x：用它自带的 Python 2.7（IDLE 或命令行）
- ArcGIS Pro：用「Python 命令提示符」
- 纯 Python 脚本：任意 Python 3 都能跑

## 合规声明

本仓库**只放通用工具代码，不放任何真实业务数据**。

不上传、不记录：卫星影像、遥感图斑、国土调查数据、规划矢量、
带真实地名 / 坐标的成果文件，以及任何未公开的内部文件。
使用者同样请勿将涉密或敏感数据提交到本仓库。

## 后续计划

- 批量投影转换 / 坐标系批量定义
- 图斑台账与 Excel 双向同步
- 影像按标准分幅批量命名
- 年度变更调查数据批量质检

## 许可

MIT。拿去用、拿去改都行，注明出处即可。

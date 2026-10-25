# -*- coding: utf-8 -*-
"""
股票预测总表 · 生成母版（空白模板）
------------------------------------------------
用途：仓库里 `股票预测/股票预测总表.xlsx` 若被误删/结构损坏，用本脚本重建一张只有表头+说明的空表。
日常不要用它覆盖已有总表——日常只走 scripts/append_row.py 追加行。

用法：
  python3 templates/build_master_xlsx.py            # 输出 ./股票预测总表.xlsx
  python3 templates/build_master_xlsx.py out.xlsx
"""
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

OUT = sys.argv[1] if len(sys.argv) > 1 else "股票预测总表.xlsx"

HEADERS = [
    "序号", "日期", "上证开盘预测", "创业板开盘预测", "恒指开盘预测", "恒科开盘预测",
    "上一交易日预测结果", "今日关键依据", "当日MD", "图1复盘", "图2要闻", "图3预测", "状态",
]
WIDTHS = [6, 12, 22, 22, 24, 24, 40, 46, 26, 30, 30, 30, 30]

HEADER_FILL = PatternFill("solid", fgColor="FFF2F2F2")
THIN = Side(style="thin", color="FFD9D9D9")
TEXT = Font(color="FF1A1A1A")

wb = Workbook()
wb.properties.title = "股票预测总表"
ws = wb.active
ws.title = "每日总览"
ws.append(HEADERS)
for i, h in enumerate(HEADERS, 1):
    c = ws.cell(1, i)
    c.fill = HEADER_FILL
    c.font = Font(bold=True, color="FF1A1A1A")
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.column_dimensions[get_column_letter(i)].width = WIDTHS[i - 1]
ws.row_dimensions[1].height = 28
ws.freeze_panes = "C2"
ws.sheet_view.showGridLines = False
ws.auto_filter.ref = f"A1:M1"
t = Table(displayName="DailyStockPrediction", ref="A1:M1")
t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
ws.add_table(t)

note = wb.create_sheet("说明")
notes = [
    "股票预测总表使用说明",
    "1. 每个执行日追加一行（scripts/append_row.py 自动追加，勿手工插在中间）。",
    "2. 若上证与中国香港同日休市，当日不执行、不新增行；任一开市即执行。",
    "3. 开盘方向与收盘方向分开验证：状态列写“开盘 x/4、收盘 y/4、综合 n/6”。",
    "4. 月目录为 YYYYMM（如 202610），每期仅归档 1 个 MD + 3 张 JPG。",
    "5. 涨红跌绿为中国市场习惯；所有预测仅供复盘，不构成投资建议。",
]
for i, v in enumerate(notes, 1):
    c = note.cell(i, 1, v)
    c.alignment = Alignment(vertical="top", wrap_text=True)
    c.font = Font(bold=(i == 1), size=14 if i == 1 else 11, color="FF1A1A1A")
note.column_dimensions["A"].width = 105
note.sheet_view.showGridLines = False

wb.save(OUT)
print(OUT)

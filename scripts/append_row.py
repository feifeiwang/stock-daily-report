#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测总表 · 追加一行（含校验）
------------------------------------------------
职责：把当日预测写进 `股票预测/股票预测总表.xlsx` 的「每日总览」sheet，
      并顺带回填"上一交易日那行"的验证结果（如果上期状态还是"待验证"）。

用法：
  python3 scripts/append_row.py --repo <仓库根> --data day.json \
      [--prev-result "10-26：开盘3/4，收盘2/4，综合3/6"] [--dry-run]

day.json 复用 templates/day_template.json 的字段，另需（可缺省）：
  XLSX_PREV_RESULT  上一交易日预测结果（写在本行"上一交易日预测结果"列）
  XLSX_BASIS        今日关键依据（3~5 个变量，短句）
  XLSX_STATUS       状态，默认"待验证"

行为：
  - 同日期已存在 → 拒绝追加（防重复），退出码 4
  - --prev-result 且上一行状态含"待验证" → 回填到上一行 M 列（状态），并在 G 列补结果
  - 行格式（日期/超链接/底色/底边框）与历史行保持一致
"""
import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

try:
    import openpyxl
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
except ImportError:  # noqa: BLE001
    print("缺少 openpyxl：pip3 install openpyxl", file=sys.stderr)
    sys.exit(2)

LINK_FONT = Font(color="FF0563C1", underline="single")
RED = PatternFill("solid", fgColor="FFFDE9E7")
GREEN = PatternFill("solid", fgColor="FFE2F0D9")
THIN = Side(style="thin", color="FFD9D9D9")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--prev-result", default="")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    d = json.loads(Path(a.data).read_text(encoding="utf-8"))
    xlsx = Path(a.repo) / "股票预测" / "股票预测总表.xlsx"
    if not xlsx.exists():
        print(f"总表不存在：{xlsx}（先用 templates/build_master_xlsx.py 重建）", file=sys.stderr)
        sys.exit(2)

    wb = openpyxl.load_workbook(xlsx)
    ws = wb["每日总览"]
    today = datetime.strptime(d["DATE"], "%Y-%m-%d").date()
    ym = d["DATE"].replace("-", "")[:6]
    day = d["DATE"]

    # ---- 防重复 ----
    for r in range(2, ws.max_row + 1):
        v = ws.cell(r, 2).value
        v = v.date() if isinstance(v, datetime) else v
        if v == today:
            print(f"已存在 {day} 的行（第 {r} 行），不重复追加", file=sys.stderr)
            sys.exit(4)

    # ---- 回填上一行 ----
    last = ws.max_row
    if a.prev_result and last >= 2 and "待验证" in str(ws.cell(last, 13).value or ""):
        # G 列写"上一日结果摘要"，M 列状态改为验证摘要（与历史行口径一致）
        ws.cell(last, 7, a.prev_result)
        ws.cell(last, 13, f"已验证：{a.prev_result.split('：', 1)[-1]}")
        ws.cell(last, 13).fill = GREEN
        print(f"  回填上一行（第 {last} 行）：{a.prev_result}")

    # ---- 追加本行 ----
    r = ws.max_row + 1
    row = [
        r - 1, today,
        f'{d["SZ_OPEN_DIR"]} {int(d["SZ_OPEN_LO"])}~{int(d["SZ_OPEN_HI"])}',
        f'{d["CYB_OPEN_DIR"]} {int(d["CYB_OPEN_LO"])}~{int(d["CYB_OPEN_HI"])}',
        f'{d["HSI_OPEN_DIR"]} {int(d["HSI_OPEN_LO"])}~{int(d["HSI_OPEN_HI"])}',
        f'{d["HSTECH_OPEN_DIR"]} {int(d["HSTECH_OPEN_LO"])}~{int(d["HSTECH_OPEN_HI"])}',
        d.get("XLSX_PREV_RESULT", ""),
        d.get("XLSX_BASIS", ""),
        f"{ym}/{day}.md", f"{ym}/{day}_1.jpg", f"{ym}/{day}_2.jpg", f"{ym}/{day}_3.jpg",
        d.get("XLSX_STATUS", "待验证"),
    ]
    for c, v in enumerate(row, 1):
        cell = ws.cell(r, c, v)
        cell.border = Border(bottom=THIN)
        if c == 2:
            cell.number_format = "yyyy-mm-dd"
            cell.alignment = Alignment(horizontal="center", vertical="top")
        elif c in (1, 13):
            cell.alignment = Alignment(horizontal="center", vertical="top", wrap_text=True)
        else:
            cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
    for c in range(9, 13):
        cell = ws.cell(r, c)
        cell.hyperlink = cell.value
        cell.font = LINK_FONT
    ws.cell(r, 13).fill = GREEN if "已验证" in str(row[12]) else RED
    # 表格范围与筛选同步扩展
    try:
        tbl = ws.tables["DailyStockPrediction"]
        tbl.ref = f"A1:M{r}"
    except KeyError:
        ws.auto_filter.ref = f"A1:M{r}"

    if a.dry_run:
        print("  [dry-run] 将追加：", row)
        return
    wb.save(xlsx)
    print(f"  已追加第 {r} 行：{day}  {row[2]} / {row[3]} / {row[4]} / {row[5]}")


if __name__ == "__main__":
    main()

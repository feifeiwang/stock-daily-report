#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
finalize_prev_day.py — 把「上一交易日预测」一次定稿并回填总表最后一行（A29/A34/A42）。

设计目标（用户要求「做成模板，后面直接改数字和文字就能跑」）：
  * 每天只改 templates/prev-day-verify.tpl.py 这一个纯值表（cp 成 work/{日期}/prev_day_verify.py）；
  * 机械算分 + 回填 Excel + 生成可贴进 runbook 的快照，一条命令完成；
  * **只改 M 列（状态）+ 置绿底 FFE2F0D9；G 列绝对不动**（A34/A42）。
    G 列语义是「该行自己的上一交易日结果」，休市日回填若覆写 G 列会把它改成
    该行自身结果，破坏语义（11-04 曾踩过）。本脚本从代码层面杜绝。

用法（跨调用一律写绝对路径，见 A35）：
  python3 scripts/finalize_prev_day.py \
      --repo /tmp/sdr \
      --values /workspace/stock-daily-report-tool/work/2026-11-07/prev_day_verify.py \
      --snapshot-out /workspace/stock-daily-report-tool/work/2026-11-07/runbook-snapshot.md \
      [--dry-run]

评分口径（固化，见 references/excel-spec.md 4.1/4.3；A41 统一了历史漂移）：
  单项：实际值落在预测区间内(含端点) = 1.0；预测方向与实际方向一致但出区间 = 0.5；方向相反 = 0
  综合 /6 = 开盘总分÷2 + 收盘总分÷2 + 板块(0/0.5/1) + 个股(0/0.5/1)
  方向由 *_pred_sign(-1/0/1) 与 sign(actual - prev_close) 机械比较，不做主观幅度判断。
"""
import argparse
import importlib.util
import os
import sys

try:
    import openpyxl
    from openpyxl.styles import PatternFill
except ImportError:
    print("需要 openpyxl：sudo pip3 install openpyxl", file=sys.stderr)
    sys.exit(2)

GREEN = "FFE2F0D9"  # 已验证行的绿底（A29）


def load_values(path):
    spec = importlib.util.spec_from_file_location("prev_day_verify", path)
    if spec is None or spec.loader is None:
        print(f"无法加载值表：{path}", file=sys.stderr)
        sys.exit(2)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fmt(x):
    """2.0 -> '2'，2.5 -> '2.5'，0.5 -> '0.5'。"""
    return str(int(x)) if float(x).is_integer() else str(x)


def sign(x):
    return 1 if x > 0 else (-1 if x < 0 else 0)


def one_score(lo, hi, pred_sign, actual, prev_close):
    """返回 (得分, 判定文案)。"""
    in_range = lo <= actual <= hi
    act_sign = sign(actual - prev_close)
    if in_range:
        return 1.0, "✅ 落区间"
    if pred_sign == act_sign and pred_sign != 0:
        return 0.5, "◐ 方向对、出区间"
    return 0.0, "❌ 方向反/未兑现"


def compute(v):
    rows = []
    open_total = close_total = 0.0
    for d in v.INDEXES:
        os_, omark = one_score(d["open_pred"][0], d["open_pred"][1],
                               d["open_pred_sign"], d["actual_open"], d["prev_close"])
        cs, cmark = one_score(d["close_pred"][0], d["close_pred"][1],
                              d["close_pred_sign"], d["actual_close"], d["prev_close"])
        open_total += os_
        close_total += cs
        rows.append(dict(d, open_score=os_, open_mark=omark,
                         close_score=cs, close_mark=cmark))
    total = open_total / 2 + close_total / 2 + v.SECTOR_SCORE + v.STOCK_SCORE
    cum_num = v.CUM_NUM_BEFORE + total
    cum_den = v.CUM_DEN_BEFORE + 6
    return rows, open_total, close_total, total, cum_num, cum_den


def summary(v, ot, ct, total):
    return (f"{v.PREV_LABEL}：开盘{fmt(ot)}/4；收盘{fmt(ct)}/4；"
            f"板块{fmt(v.SECTOR_SCORE)}、个股{fmt(v.STOCK_SCORE)}；综合{fmt(total)}/6")


def status(v, ot, ct, total):
    return "已验证：" + summary(v, ot, ct, total).split("：", 1)[1]


def write_back(repo, v, status_text, dry_run):
    xlsx = os.path.join(repo, "股票预测", "股票预测总表.xlsx")
    wb = openpyxl.load_workbook(xlsx)
    ws = wb["每日总览"]
    r = ws.max_row
    b = ws.cell(r, 2).value
    date_str = b.strftime("%Y-%m-%d") if hasattr(b, "strftime") else str(b)[:10]
    m = ws.cell(r, 13).value
    print(f"  目标行：第 {r} 行，B{r}={date_str}，M{r}={m}")
    if date_str != v.DATE:
        print(f"  [拒绝] 总表最后一行日期 {date_str} != 值表 DATE {v.DATE}", file=sys.stderr)
        return False
    if not m or "待验证" not in str(m):
        print(f"  [拒绝] M{r} 不含「待验证」，可能已回填过，避免重复写入", file=sys.stderr)
        return False
    # 只动 M 列；G 列（第7列）保持原值不动 —— A34/A42 硬约束
    g_before = ws.cell(r, 7).value
    if dry_run:
        print(f"  [dry-run] 将写 M{r} = {status_text}")
        return True
    ws.cell(r, 13).value = status_text
    ws.cell(r, 13).fill = PatternFill(fill_type="solid", fgColor=GREEN)
    wb.save(xlsx)
    wb2 = openpyxl.load_workbook(xlsx)
    ws2 = wb2["每日总览"]
    assert ws2.cell(r, 13).value == status_text, "M 列回读失败"
    assert ws2.cell(r, 7).value == g_before, "G 列被意外改动（严重）"
    print(f"  [OK] 已写 M{r} 并置绿底；G{r} 保持「{g_before}」未改动")
    return True


def snapshot_md(v, rows, ot, ct, total, cum_num, cum_den, status_text, summary_text):
    L = []
    L.append(f"#### {v.DATE} 定稿快照（预取于 {v.SNAPSHOT_DATE}，下一开盘日 {v.NEXT_OPEN}）")
    L.append("")
    L.append("| 指数 | 昨收 | 实际开盘 | 开盘涨跌幅 | 实际收盘 | 收盘涨跌幅 | 数据来源 |")
    L.append("|---|---:|---:|---:|---:|---:|---|")
    for d in rows:
        L.append(f"| {d['name']} | {d['prev_close']} | {d['actual_open']} | "
                 f"{d['open_pct']:+.2f}% | {d['actual_close']} | {d['close_pct']:+.2f}% | {d['sources']} |")
    L.append("")
    L.append("机械判定（口径见 excel-spec 4.1/4.3，A41 统一）：")
    L.append("")
    L.append("| 指数 | 预测开盘 | 实际开盘 | 开盘 | 预测收盘 | 实际收盘 | 收盘 |")
    L.append("|---|---:|---:|:--:|---:|---:|:--:|")
    for d in rows:
        L.append(f"| {d['name']} | {d['open_pred'][0]}~{d['open_pred'][1]}（{d['open_pred_label']}） | "
                 f"{d['actual_open']} | {d['open_mark']} | "
                 f"{d['close_pred'][0]}~{d['close_pred'][1]}（{d['close_pred_label']}） | "
                 f"{d['actual_close']} | {d['close_mark']} |")
    L.append("")
    L.append(f"- **开盘 {fmt(ot)}/4、收盘 {fmt(ct)}/4、板块 {fmt(v.SECTOR_SCORE)}、"
             f"个股 {fmt(v.STOCK_SCORE)} → 综合 {fmt(total)}/6**；"
             f"累计 {fmt(v.CUM_NUM_BEFORE)}/{v.CUM_DEN_BEFORE} + {fmt(total)}/6 → "
             f"**{cum_num}/{cum_den} ≈ {cum_num / cum_den * 100:.1f}%**。")
    L.append("")
    L.append(f"- **板块（{fmt(v.SECTOR_SCORE)}）**：{v.SECTOR_NOTE}")
    L.append(f"- **个股（{fmt(v.STOCK_SCORE)}）**：{v.STOCK_NOTE}")
    L.append(f"- **根因/经验**：{v.ROOT_CAUSE}")
    L.append("")
    if getattr(v, "SECTOR_DETAIL", None):
        L.append("板块逐条核对：")
        L.append("")
        for x in v.SECTOR_DETAIL:
            L.append(f"- {x}")
        L.append("")
    if getattr(v, "STOCK_DETAIL", None):
        L.append("个股逐条核对：")
        L.append("")
        for x in v.STOCK_DETAIL:
            L.append(f"- {x}")
        L.append("")
    L.append("数据来源（A30：收盘只认次日早报/新华社通稿）：")
    L.append("")
    for x in v.SOURCES:
        L.append(f"- {x}")
    L.append("")
    L.append(f"- **总表回填**：M 列写 `{status_text}`（绿底 FFE2F0D9）；"
             f"**G 列不动**（A34/A42）。")
    L.append(f"- **下一开盘日 {v.NEXT_OPEN} 提示**：`--prev-result` 不再生效（上一行已非「待验证」），"
             f"改把下面这串写进 `day.json` 的 `XLSX_PREV_RESULT` →")
    L.append(f"  `{summary_text}`")
    L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="仓库根目录（绝对路径）")
    ap.add_argument("--values", required=True, help="纯值表 .py（绝对路径）")
    ap.add_argument("--snapshot-out", default=None, help="输出可贴进 runbook 的快照 md")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    v = load_values(a.values)
    rows, ot, ct, total, cum_num, cum_den = compute(v)
    s = summary(v, ot, ct, total)
    st = status(v, ot, ct, total)

    print("=" * 72)
    print(f"定稿对象 {v.DATE}　下一开盘日 {v.NEXT_OPEN}")
    print("-" * 72)
    for d in rows:
        print(f"  {d['name']:<8} 开 {d['actual_open']:>9} {d['open_mark']:<14} "
              f"收 {d['actual_close']:>9} {d['close_mark']:<14} "
              f"(开{d['open_score']} 收{d['close_score']})")
    print("-" * 72)
    print(f"  开盘 {fmt(ot)}/4　收盘 {fmt(ct)}/4　板块 {fmt(v.SECTOR_SCORE)}　"
          f"个股 {fmt(v.STOCK_SCORE)}　→ 综合 {fmt(total)}/6")
    print(f"  累计 {fmt(v.CUM_NUM_BEFORE)}/{v.CUM_DEN_BEFORE} + {fmt(total)}/6 "
          f"= {cum_num}/{cum_den} ≈ {cum_num / cum_den * 100:.1f}%")
    print(f"  G列摘要串(XLSX_PREV_RESULT)：{s}")
    print(f"  M列状态串：{st}")
    print("=" * 72)

    if not write_back(a.repo, v, st, a.dry_run):
        sys.exit(1)

    if a.snapshot_out:
        md = snapshot_md(v, rows, ot, ct, total, cum_num, cum_den, st, s)
        with open(a.snapshot_out, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"  快照已写：{a.snapshot_out}")


if __name__ == "__main__":
    main()

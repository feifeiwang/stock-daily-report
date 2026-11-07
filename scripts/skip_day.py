#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skip_day.py — 休市日幂等守卫（A45，2026-11-08 新增）。

解决的问题：
  SKILL.md「休市日标准动作」原本无条件要求「预取上一交易日数据 → 一次定稿 → 回填总表」，
  但每个周末都有周六、周日两个休市日，**第二天的上一交易日仍是同一个、且已在第一天定稿**。
  照流程无脑跑 `finalize_prev_day.py` 会被「M 列不含待验证」拒绝（脚本有保护但会报错退出），
  更糟的是可能重复联网搜索、或人为覆写已回填的 M 列 / 重复写快照。

本脚本一条命令给出机器可读决策，日常无需改代码，只按输出走：

  python3 scripts/skip_day.py --repo /tmp/sdr --date 2026-11-08 \
      --log-out /workspace/stock-daily-report-tool/work/2026-11-08/runbook-entry.md

输出的 KEY=VALUE（供后续步骤或人直接读）：
  VERDICT=SKIP | TRADE                 今日是否两地同休
  NEXT_OPEN=YYYY-MM-DD               下一开盘日
  MONTH_DIR=股票预测/YYYYMM          下一开盘日对应月份目录（附 EXISTS=yes/no）
  LAST_ROW / LAST_DATE               总表末行行号与日期
  FINALIZE_STATE=ALREADY_FINALIZED | PENDING | MISMATCH
  ACTION=SKIP_ONLY | FINALIZE_THEN_LOG | REVIEW_MISMATCH
  XLSX_PREV_RESULT=...               下一开盘日新行 G 列要写的摘要串（ALREADY_FINALIZED 时给出）

ACTION 语义（写进 SKILL.md 休市日标准动作第 0 步）：
  SKIP_ONLY          仅写运行日志 + 推送 Skill 改动；不采集、不回填、不新建行、不建日期文件
  FINALIZE_THEN_LOG  按休市日标准动作第 2~3 步预取数据 + 跑 finalize_prev_day.py 定稿回填
  REVIEW_MISMATCH    总表末行日期与最近交易日不一致，人工复核后再动手

跨调用一律绝对路径（A35）。token 与本脚本无关，推送仍走 gh_sync.py。
"""
import argparse
import os
import sys
from datetime import date

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import holidays  # noqa: E402

try:
    import openpyxl
except ImportError:
    print("需要 openpyxl：sudo pip3 install openpyxl", file=sys.stderr)
    sys.exit(2)

WEEKDAY_CN = "一二三四五六日"


def prev_market_day(d):
    """从 d（不含）往前找最近一个 A股或港股开市日。"""
    x = date.fromordinal(d.toordinal() - 1)
    while True:
        if holidays.sh_trading_day(x) or holidays.hk_trading_day(x):
            return x
        x = date.fromordinal(x.toordinal() - 1)


def next_market_days(d, n=3):
    wd = WEEKDAY_CN
    out = []
    for x, sh, hk in holidays.next_trading_days(d, n):
        tag = "A股+港股同开" if (sh and hk) else ("仅A股" if sh else "仅港股")
        out.append((x, f"星期{wd[x.weekday()]}", tag))
    return out


def read_last_row(repo):
    xlsx = os.path.join(repo, "股票预测", "股票预测总表.xlsx")
    if not os.path.exists(xlsx):
        return None
    wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    ws = wb["每日总览"]
    r = ws.max_row
    b = ws.cell(r, 2).value
    d = b.strftime("%Y-%m-%d") if hasattr(b, "strftime") else str(b)[:10]
    m = ws.cell(r, 13).value or ""
    g = ws.cell(r, 7).value or ""
    n = ws.cell(r, 14).value or ""
    wb.close()
    return dict(row=r, date=d, m=str(m), g=str(g), n=str(n))


def prev_result_from_m(date_str, m):
    """从已回填的 M 列反推下一开盘日新行 G 列摘要串（A34/A42）。"""
    body = m.split("已验证：", 1)[-1].strip()
    if not body or body == m:
        return ""
    return f"{date_str[5:]}：{body}"


def render_log(tpl_path, vals):
    if not tpl_path or not os.path.exists(tpl_path):
        return None
    with open(tpl_path, encoding="utf-8") as f:
        s = f.read()
    for k, v in vals.items():
        s = s.replace("{" + k + "}", str(v))
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="仓库根目录（绝对路径）")
    ap.add_argument("--date", default=None, help="YYYY-MM-DD，默认今天")
    ap.add_argument("--next", dest="n_next", type=int, default=3)
    ap.add_argument("--log-out", default=None, help="输出可贴进 runbook 的日志骨架 md")
    ap.add_argument("--tpl", default=None, help="日志模板路径，默认 ../templates/skip-day-log.tpl.md")
    a = ap.parse_args()

    d = date.fromisoformat(a.date) if a.date else date.today()
    sh, hk = holidays.sh_trading_day(d), holidays.hk_trading_day(d)
    wd = f"星期{WEEKDAY_CN[d.weekday()]}"
    nxt = next_market_days(d, a.n_next)
    next_open = nxt[0][0].isoformat() if nxt else ""
    month_dir = "股票预测/" + next_open[:7].replace("-", "")
    month_exists = os.path.isdir(os.path.join(a.repo, month_dir))

    holiday_out = (f"{d.isoformat()} A股={'开市' if sh else '休市'} "
                   f"港股={'开市' if hk else '休市'}")
    if not sh:
        holiday_out += f"（A股：{holidays.holiday_source(d) or '非交易日'}）"
    if not hk:
        holiday_out += f"（港股：{holidays.hk_holiday_source(d) or '非交易日'}）"

    print("=" * 72)
    print(f"休市日幂等守卫 A45　{d.isoformat()} {wd}")
    print("-" * 72)
    print(holiday_out)

    if sh or hk:
        print("VERDICT=TRADE")
        print("ACTION=REGULAR_FLOW")
        print("  今日至少一地开市，本脚本不适用；请按 SKILL.md「每日执行清单」跑常规流程。")
        print("=" * 72)
        return 0

    print("VERDICT=SKIP")
    print(f"NEXT_OPEN={next_open}")
    for x, w, tag in nxt:
        print(f"  下一开盘日 {x.isoformat()} {w}（{tag}）")
    print(f"MONTH_DIR={month_dir}")
    print(f"MONTH_EXISTS={'yes' if month_exists else 'no'}")

    pm = prev_market_day(d)
    print(f"PREV_MARKET_DAY={pm.isoformat()}")
    last = read_last_row(a.repo)
    if last is None:
        print("LAST_ROW=NONE")
        print("FINALIZE_STATE=MISMATCH")
        print("ACTION=REVIEW_MISMATCH")
        print("  未找到总表，人工复核后再动手（A25：先 git clone / gh_sync pull）。")
        print("=" * 72)
        return 0

    print(f"LAST_ROW={last['row']}")
    print(f"LAST_DATE={last['date']}")
    print(f"LAST_M={last['m']}")
    print(f"LAST_G={last['g'][:80]}")

    is_pending = "待验证" in last["m"]
    date_ok = last["date"] == pm.isoformat()
    if not date_ok:
        state, action = "MISMATCH", "REVIEW_MISMATCH"
    elif is_pending:
        state, action = "PENDING", "FINALIZE_THEN_LOG"
    else:
        state, action = "ALREADY_FINALIZED", "SKIP_ONLY"
    print(f"FINALIZE_STATE={state}")
    print(f"ACTION={action}")

    prev_result = ""
    if state == "ALREADY_FINALIZED":
        prev_result = prev_result_from_m(last["date"], last["m"])
        print(f"XLSX_PREV_RESULT={prev_result}")
        print("  → 仅写运行日志 + 推送 Skill 改动；不采集、不回填、不新建行、不建日期文件。")
    elif state == "PENDING":
        print("  → 按休市日标准动作第 2~3 步：预取上一交易日数据 → cp 值表 → "
              "finalize_prev_day.py 定稿回填 → 写日志推送。")
        print("  → 摘要串由 finalize_prev_day.py 打印，不要手填。")
    else:
        print(f"  → 最近交易日 {pm.isoformat()} 与总表末行 {last['date']} 不一致，人工复核。")
    print("=" * 72)

    if a.log_out:
        tpl = a.tpl or os.path.normpath(
            os.path.join(_HERE, "..", "templates", "skip-day-log.tpl.md"))
        vals = dict(
            DATE=d.isoformat(), WEEKDAY=wd, HOLIDAY_OUT=holiday_out,
            NEXT_OPEN=next_open, NEXT_WEEKDAY=nxt[0][1] if nxt else "",
            MONTH_DIR=month_dir, MONTH_EXISTS="已存在" if month_exists else "需新建",
            PREV_MARKET_DAY=pm.isoformat(), LAST_ROW=last["row"],
            LAST_DATE=last["date"], LAST_M=last["m"], LAST_G=last["g"],
            FINALIZE_STATE=state, ACTION=action,
            XLSX_PREV_RESULT=prev_result or "（待 finalize_prev_day.py 打印）",
            N_COL=last["n"][:100].replace("\n", " "),
        )
        md = render_log(tpl, vals)
        if md is None:
            print(f"  [WARN] 模板不存在，跳过日志骨架：{tpl}", file=sys.stderr)
        else:
            os.makedirs(os.path.dirname(os.path.abspath(a.log_out)), exist_ok=True)
            with open(a.log_out, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"  日志骨架已写：{a.log_out}")
    return 0


if __name__ == "__main__":
    main()

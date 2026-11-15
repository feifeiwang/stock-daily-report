#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
出图前区间硬预检（2026-11-16 固化，配合 build_charts.py 的四项硬校验）
=====================================================================
为什么需要：build_charts.py 的 validate() 会在渲染前拒绝违规区间，但报错发生在
「渲染阶段」；本脚本把同一套规则前移到「填完 day_values.py、出图之前」，一次
打印四指数的 收盘宽 / 开盘宽 / 全天宽 / 全天包含 四项，避免来回改数字再重跑渲染。

规则（与 scripts/build_charts.py validate() 完全一致，A8/A20）：
  1. 收盘区间宽 (CLOSE_HI-CLOSE_LO) ≤ 昨收 × 1.0%
  2. 开盘区间宽 (OPEN_HI-OPEN_LO)/昨收 × 100 ≤ 1.0 pct
  3. 全天区间宽 (DAY_HI-DAY_LO)/昨收 × 100 ≤ 1.5 pct
  4. 全天区间必须完整包含开盘与收盘区间：
     DAY_LO ≤ min(CLOSE_LO, OPEN_LO) 且 max(CLOSE_HI, OPEN_HI) ≤ DAY_HI
  另附：涨跌幅相对昨收的位置（供 A41 次日机械判定 pred_sign 参考）。

用法（路径一律写绝对路径，A35）：
  python3 scripts/precheck_intervals.py --values work/{日期}/day_values.py
  python3 scripts/precheck_intervals.py --data   work/{日期}/day.json
  # 也可不带参数，默认读当前目录 day_values.py

退出码：0 = 全部通过；1 = 有违规项（打印 ✗ 明细）。「改数字就能出图」的前置门禁。
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

IDXS = ("SZ", "CYB", "HSI", "HSTECH")
NAMES = {"SZ": "上证指数", "CYB": "创业板指", "HSI": "恒生指数", "HSTECH": "恒生科技"}


def load_values(path):
    p = Path(path).resolve()
    if not p.exists():
        sys.exit("值表不存在：" + str(p))
    spec = importlib.util.spec_from_file_location("precheck_" + p.stem, str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.VALS


def load_json(path):
    p = Path(path).resolve()
    if not p.exists():
        sys.exit("day.json 不存在：" + str(p))
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser(description="出图前四项硬校验预检")
    ap.add_argument("--values", help="day_values.py 路径（读 VALS）")
    ap.add_argument("--data", help="day.json 路径（图阶段或 xlsx 阶段皆可）")
    a = ap.parse_args()

    if a.values:
        v = load_values(a.values)
    elif a.data:
        v = load_json(a.data)
    else:
        v = load_values("day_values.py")

    bad = 0
    print("=" * 72)
    print("出图前区间硬预检（build_charts.py 同款规则）")
    print("=" * 72)
    for p in IDXS:
        try:
            prev = float(v[p + "_PREV_CLOSE"])
            clo, chi = float(v[p + "_CLOSE_LO"]), float(v[p + "_CLOSE_HI"])
            olo, ohi = float(v[p + "_OPEN_LO"]), float(v[p + "_OPEN_HI"])
            dlo, dhi = float(v[p + "_DAY_LO"]), float(v[p + "_DAY_HI"])
        except (KeyError, ValueError) as e:
            print(f"[缺失] {NAMES[p]} 键值不全：{e}")
            bad += 1
            continue

        r1 = (chi - clo) <= prev * 0.01 + 1e-9 and chi > clo
        r2 = (ohi - olo) / prev * 100 <= 1.0 + 1e-9
        r3 = (dhi - dlo) / prev * 100 <= 1.5 + 1e-9
        r4 = dlo <= min(clo, olo) and max(chi, ohi) <= dhi
        ok = r1 and r2 and r3 and r4
        if not ok:
            bad += 1
        flag = "OK " if ok else "✗  "
        # 开盘方向（相对昨收），供 A41 pred_sign 参考
        if ohi < prev:
            sign = "-1(低开)"
        elif olo > prev:
            sign = "+1(高开)"
        else:
            sign = " 0(平/跨昨收)"
        print(
            f"{flag}{NAMES[p]:<6} 昨收{prev:>10.2f} | "
            f"收盘宽{chi-clo:>7.2f}(≤{prev*0.01:.2f}){'✓' if r1 else '✗'} | "
            f"开盘宽{(ohi-olo)/prev*100:>5.3f}pct(≤1.0){'✓' if r2 else '✗'} | "
            f"全天宽{(dhi-dlo)/prev*100:>5.3f}pct(≤1.5){'✓' if r3 else '✗'} | "
            f"全天包含={'✓' if r4 else '✗'} | 开盘符号 {sign}"
        )
    print("-" * 72)
    if bad:
        print(f"结论：{bad} 个指数违规，请先改 day_values.py 再出图。")
        sys.exit(1)
    print("结论：四指数四项硬校验全部通过，可运行 build_charts.py。")
    sys.exit(0)


if __name__ == "__main__":
    main()

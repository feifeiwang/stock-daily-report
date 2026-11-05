#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板 → day.json 生成器（"改数字和文字就能出图"）
=====================================================
把每天要改的东西收敛到**一个值表文件** day_values.py（模板见
templates/day_values.tpl.py），脚本本身每天不用动：

  - VALS      : 三张图里的数字与文案（键名必须已存在于 day_template.json）
  - XLSX_VALS : 总表专用三字段（只给 append_row.py 用，绝不出图）

两阶段对应 runbook A15 / A33：
  阶段 1（出图前）  --stage chart → day.json 只含模板键，绝不含 XLSX_*
  阶段 2（出图成功）--stage xlsx  → 向同一 day.json 注入 XLSX_* 三个键

用法（路径一律写绝对路径，见 A35）：
  python3 /tmp/sdr/scripts/make_day_json.py \
      --template /tmp/sdr/templates/day_template.json \
      --values   /workspace/stock-daily-report-tool/work/{日期}/day_values.py \
      --out      /workspace/stock-daily-report-tool/work/{日期}/day.json \
      --stage chart

  python3 /tmp/sdr/scripts/make_day_json.py \
      --values /workspace/.../day_values.py \
      --out    /workspace/.../day.json --stage xlsx

硬规则（脚本强制，违反直接退出码 1）：
  1. VALS 里不允许出现模板中不存在的键 → 防止 build_charts 报"多余键"（A15）
  2. 图阶段不允许出现 XLSX_* → 防止把总表字段塞进 day.json（A33）
  3. xlsx 阶段 XLSX_VALS 必须恰为三个指定键，且 day.json 已存在
  4. 只覆盖值、不增删键；注释键（下划线开头）原样保留
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

XLSX_KEYS = ("XLSX_PREV_RESULT", "XLSX_BASIS", "XLSX_STATUS")


def load_values(path):
    p = Path(path).resolve()
    if not p.exists():
        sys.exit("值表不存在：" + str(p))
    spec = importlib.util.spec_from_file_location("day_values_" + p.stem, str(p))
    if spec is None or spec.loader is None:
        sys.exit("无法加载值表：" + str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser(description="day_template.json + 值表 → day.json")
    ap.add_argument("--template", help="day_template.json 路径（chart 阶段必填）")
    ap.add_argument("--values", required=True, help="当日 day_values.py 路径（每天只改这个）")
    ap.add_argument("--out", required=True, help="day.json 输出路径")
    ap.add_argument("--stage", choices=("chart", "xlsx"), default="chart")
    a = ap.parse_args()

    out = Path(a.out)
    mod = load_values(a.values)

    if a.stage == "chart":
        if not a.template:
            sys.exit("chart 阶段必须给 --template")
        tpl = json.loads(Path(a.template).read_text(encoding="utf-8"))
        vals = dict(getattr(mod, "VALS", {}))
        if not vals:
            sys.exit("值表里没有 VALS（或为空）")
        banned = sorted(k for k in vals if k.startswith("XLSX_"))
        if banned:
            sys.exit("图阶段禁止 XLSX_*（A15/A33）：" + ", ".join(banned))
        unknown = sorted(k for k in vals if k not in tpl)
        if unknown:
            sys.exit("模板中不存在的键（禁止新增）：" + ", ".join(unknown))
        d = dict(tpl)
        d.update(vals)
        out.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[chart] {out} 已生成：{len(d)} 键（模板 {len(tpl)} + 覆盖 {len(vals)}）")
        return

    # ---- xlsx 阶段 ----
    xv = dict(getattr(mod, "XLSX_VALS", {}))
    missing = sorted(set(XLSX_KEYS) - set(xv))
    extra = sorted(set(xv) - set(XLSX_KEYS))
    if missing or extra:
        sys.exit("XLSX_VALS 键不正确：缺 " + str(missing) + " / 多 " + str(extra))
    if not out.exists():
        sys.exit("xlsx 阶段要求 day.json 已存在（先跑 chart 并成功出图）")
    d = json.loads(out.read_text(encoding="utf-8"))
    if any(k.startswith("XLSX_") for k in d):
        print("  [warn] day.json 已含 XLSX_*，本次覆盖")
    d.update(xv)
    out.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[xlsx] {out} 已注入 {len(XLSX_KEYS)} 个总表字段：{len(d)} 键（供 append_row.py）")


if __name__ == "__main__":
    main()

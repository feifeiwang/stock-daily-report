#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测 Skill · 一键出三图（模板 → 数据 → PNG → JPG → 测高门禁）

设计目的：把"每日只改数字和文字"这件事做成硬约束。
数据全部写在 JSON 里，Python 模板（CSS/track/donut/main）一个字都不用手碰。

用法：
  python3 build_charts.py --data day.json --out ./out [--repo <克隆的仓库根>] [--keep-png]

输入：
  --data  JSON 文件，键 = gen3_images.data.py 里的 {{占位符}}（全部必填，缺一个就报错并列出）
  --repo  仓库根（默认 = 本脚本所在目录往上两级，即仓库根）；找不到 templates/ 时回退到脚本目录下 templates/
  --out   输出目录，产出 {date}_1.jpg / _2.jpg / _3.jpg（--keep-png 时保留 PNG）

退出码：0 成功；2 数据校验失败（缺占位符/类型错误/区间规则违规）；3 渲染或测高失败
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import pathlib

IDX = ["SZ", "CYB", "HSI", "HSTECH"]
IDX_CN = {"SZ": "上证指数", "CYB": "创业板指", "HSI": "恒生指数", "HSTECH": "恒生科技"}


def die(code, msg):
    print(f"[build_charts] 失败：{msg}", file=sys.stderr)
    sys.exit(code)


def find_templates(repo):
    """返回 (骨架tpl, 数据tpl, scripts目录)。"""
    cands = []
    if repo:
        cands.append(pathlib.Path(repo) / "scripts")
    here = pathlib.Path(__file__).resolve()
    cands.append(here.parent)                                  # 模板放在 scripts/ 下时
    cands.append(here.parent.parent / "scripts")               # 模板放在 <repo>/scripts/templates 时
    for c in cands:
        tpl = c / "templates" / "gen3_images.tpl.py"
        dat = c / "templates" / "gen3_images.data.py"
        if tpl.exists() and dat.exists():
            return tpl, dat, c
    die(3, "找不到 scripts/templates/gen3_images.tpl.py 与 gen3_images.data.py，请指定 --repo <仓库根>")


def validate(d, tpl_text, dat_text):
    """① 占位符齐全 ② 数值类型 ③ 区间规则。返回错误列表。"""
    errs = []
    need = sorted(set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", dat_text)))
    miss = [k for k in need if k not in d]
    # 由 derive() 自动生成的键也算"模板需要的键"，不算多余
    auto = {f"{p}_ACT_SPAN" for p in IDX} | {f"{p}_ACTUAL" for p in IDX} | {f"{p}_PCT" for p in IDX}
    extra = [k for k in d if k not in need and k not in auto and not k.startswith("_")]
    if miss:
        errs.append("缺少占位符：" + ", ".join(miss))
    if extra:
        errs.append("多余键（模板里没有，检查拼写）：" + ", ".join(extra))

    def num(k):
        try:
            return float(d[k])
        except Exception:
            errs.append(f"{k} 必须是数字，当前={d.get(k)!r}")
            return None

    for p in IDX:
        prev, clo, chi = num(f"{p}_PREV_CLOSE"), num(f"{p}_CLOSE_LO"), num(f"{p}_CLOSE_HI")
        dlo, dhi = num(f"{p}_DAY_LO"), num(f"{p}_DAY_HI")
        olo, ohi = num(f"{p}_OPEN_LO"), num(f"{p}_OPEN_HI")
        if None in (prev, clo, chi, dlo, dhi, olo, ohi):
            continue
        name = IDX_CN[p]
        # 硬规则 25：收盘区间宽度 ≤ 昨收 1%
        if (chi - clo) > prev * 0.01 + 1e-9:
            errs.append(f"{name} 收盘区间宽 {chi-clo:.2f} > 昨收1%={prev*0.01:.2f}")
        if chi <= clo:
            errs.append(f"{name} 收盘区间上界必须大于下界")
        # 硬规则：全天区间 ≤1.5pct 且完整包含收盘区间与开盘区间
        if (dhi - dlo) / prev * 100 > 1.5 + 1e-9:
            errs.append(f"{name} 全天区间宽 {(dhi-dlo)/prev*100:.2f}pct > 1.5pct")
        if not (dlo <= min(clo, olo) and max(chi, ohi) <= dhi):
            errs.append(f"{name} 全天区间未完整包含收盘区间与开盘区间（{dlo}~{dhi} vs 收盘{clo}~{chi} / 开盘{olo}~{ohi}）")
        if (ohi - olo) / prev * 100 > 1.0 + 1e-9:
            errs.append(f"{name} 开盘区间宽 {(ohi-olo)/prev*100:.2f}pct > 1.0pct（开盘区间也应收窄）")

    # 图1/图2 条数需与模板行数一致，否则多出的行会被静默丢弃
    for key, cnt in (("BRIEF%d_T", 4), ("OTHER%d", 5), ("NEWS%d_T", 6)):
        for i in range(1, cnt + 1):
            k = key % i
            if k in need:
                for suf in ("_D",):
                    if k + suf in need and k + suf not in d:
                        errs.append(f"缺少占位符：{k}{suf}")

    # 图1 的 4 行复盘：标签类必须合法；涨跌方向由 {p}_ACTUAL / {p}_PCT 自动生成
    # （历史坑：模板里写死 up+▲，跌的日子会显示"▼-0.19%"仍标红）
    for p in IDX:
        tag_k = f"{p}_TAG"
        if tag_k in need and d.get(tag_k) not in ("tag-ok", "tag-half", "tag-bad"):
            errs.append(f"{tag_k} 只能是 tag-ok / tag-half / tag-bad，当前={d.get(tag_k)!r}")
    return errs, need


def derive(d, d_key_set):
    """由实际点位与涨跌幅推出图1 的彩色 span（up 红/down 绿 + ▲▼），避免手写 HTML 出错。"""
    for p in IDX:
        s = f"{p}_ACT_SPAN"
        if s not in d_key_set:
            continue
        try:
            pct = float(str(d[f"{p}_PCT"]).replace("%", ""))
        except Exception:  # noqa: BLE001
            d[s] = ""  # 让校验器报出缺字段，而不是 KeyError
            continue
        up = pct >= 0
        d[s] = ('<span class="rev-act %s">%s<span>%s%s%%</span></span>'
                % ("up" if up else "down", d.get(f"{p}_ACTUAL", ""), "▲" if up else "▼", d[f"{p}_PCT"]))
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--repo", default=None)
    ap.add_argument("--keep-png", action="store_true")
    a = ap.parse_args()

    try:
        d = json.loads(pathlib.Path(a.data).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        die(2, f"读取数据 JSON 失败：{e}")

    tpl, dat, scripts_dir = find_templates(a.repo)
    tpl_text, dat_text = tpl.read_text(encoding="utf-8"), dat.read_text(encoding="utf-8")
    need = sorted(set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", dat_text)))
    d = derive(d, set(need))
    errs, need = validate(d, tpl_text, dat_text)
    if errs:
        print("[build_charts] 数据校验未通过：", file=sys.stderr)
        for e in errs:
            print("  - " + e, file=sys.stderr)
        sys.exit(2)

    # 渲染：骨架 + 数据模板（逐占位符替换；{{ }} 是模板变量，不能被 str.format 吃掉）
    body = dat_text
    for k in need:
        v = str(d[k])
        if k.endswith("_ACT_SPAN"):
            # 含引号的 HTML，必须按 Python 字面量转义后嵌入（直接替换会破坏语法）
            v = repr(v)[1:-1]  # 只借 repr 做转义，外层引号由模板提供
        elif any(q in v for q in ('"', "'", "\\")):
            # A21：值里带引号/反斜杠会截断 Python 字面量（NEWS*_D 曾是双引号包裹）。
            # 统一做 repr 转义，模板外层一律单引号，等于"值里能放任何引号"。
            v = repr(v)[1:-1]
        body = body.replace("{{%s}}" % k, v)
    left = re.findall(r"\{\{[A-Z0-9_]+\}\}", body)
    if left:
        die(2, "仍有未替换占位符：" + ", ".join(sorted(set(left))))

    out_dir = pathlib.Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="gen3_"))
    gen = tmp / "gen3_images.py"
    gen.write_text(tpl_text.replace("# @@DATA@@", body), encoding="utf-8")

    png_dir = tmp / "png"
    png_dir.mkdir()
    r = subprocess.run([sys.executable, str(gen), str(png_dir)], capture_output=True, text=True)
    print(r.stdout[-2000:] if r.stdout else "", end="")
    if r.returncode != 0:
        print(r.stderr[-3000:], file=sys.stderr)
        die(3, "渲染失败（多为文案过长导致溢出或 HTML 标签不配对）")

    # 测高门禁：gen3 母版把三屏 HTML 写在 /tmp/img1~3.html（页脚模式，间隙 ≥2px 才安全）
    mh = scripts_dir / "measure_heights.py"
    htmls = [f"/tmp/img{i}.html" for i in (1, 2, 3)]
    if mh.exists() and all(os.path.exists(h) for h in htmls):
        r2 = subprocess.run([sys.executable, str(mh), *htmls], capture_output=True, text=True)
        print(r2.stdout[-1500:], end="")
        if r2.returncode != 0:
            print(r2.stderr[-1500:], file=sys.stderr)
            die(3, "测高未通过（内容溢出页脚），请压缩文案后重跑")

    # PNG → JPG（quality 90），并校验 1080×1920
    try:
        from PIL import Image
    except ImportError:
        die(3, "缺少 pillow：pip3 install pillow")
    date = d["DATE"]
    for i in (1, 2, 3):
        png = png_dir / f"{date}_{i}.png"
        if not png.exists():
            die(3, f"渲染产物缺失：{png}")
        im = Image.open(png).convert("RGB")
        if im.size != (1080, 1920):
            die(3, f"{png.name} 尺寸 {im.size} != (1080, 1920)")
        im.save(out_dir / f"{date}_{i}.jpg", "JPEG", quality=90, subsampling=0)
        if a.keep_png:
            shutil.copy2(png, out_dir / png.name)
        print(f"  [JPG] {out_dir / (date + '_' + str(i) + '.jpg')}")
    shutil.rmtree(tmp, ignore_errors=True)
    print("[build_charts] 完成")


if __name__ == "__main__":
    main()

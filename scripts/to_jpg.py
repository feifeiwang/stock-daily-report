#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PNG -> JPG 批量转换（GitHub 归档统一用 JPG，禁 PNG：PNG 体积过大占用仓库空间）。

用法:
  python3 to_jpg.py 输出目录            # 转换目录下全部 *_1.png/_2.png/_3.png/*.png 为同名 .jpg
  python3 to_jpg.py 输出目录 file.png    # 只转指定文件

规则:
  - 质量 quality=90, subsampling=0(4:4:4), optimize=True —— 文字/细线不糊
  - 统一转 RGB（PNG 可能是 RGBA，JPG 不支持透明）
  - 已存在同名 .jpg 且不强制则跳过（-f 可覆盖）
"""
import os
import sys

from PIL import Image

QUALITY = 90


def convert(path, force=False):
    jpg = os.path.splitext(path)[0] + ".jpg"
    if os.path.exists(jpg) and not force:
        print("skip (exists)", jpg)
        return jpg
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", im.size, (7, 10, 20))
        im = im.convert("RGBA")
        bg.paste(im, mask=im.split()[-1])
        im = bg
    else:
        im = im.convert("RGB")
    im.save(jpg, "JPEG", quality=QUALITY, subsampling=0, optimize=True)
    src = os.path.getsize(path)
    dst = os.path.getsize(jpg)
    print("OK %s -> %s  %.0fKB -> %.0fKB (-%.0f%%)" % (
        os.path.basename(path), os.path.basename(jpg),
        src / 1024, dst / 1024, (1 - dst / src) * 100 if src else 0))
    return jpg


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    force = "-f" in sys.argv
    args = [a for a in sys.argv[1:] if a != "-f"]
    if len(args) >= 2 and os.path.isfile(args[1]):
        convert(args[1], force)
        return
    d = args[0]
    files = sorted(f for f in os.listdir(d) if f.lower().endswith(".png"))
    if not files:
        print("no png in", d)
        return
    for f in files:
        convert(os.path.join(d, f), force)


if __name__ == "__main__":
    main()

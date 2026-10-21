# -*- coding: utf-8 -*-
"""对 {日期}.html 逐屏截图并纵向拼接为竖屏长图。

用法: python3 shot_long.py [工作目录] [日期]
  工作目录: 存放 {日期}.html 的目录，默认当前目录
  日期:     形如 2026-10-20；缺省时自动取工作目录里最新的 {日期}.html

视口 405x720 + device_scale_factor=2.6666667 -> 每屏 1080x1920，
逐屏 element.screenshot() 后用 PIL 纵向拼接到色底 (7,10,20) 画布。
"""
import glob
import os
import shutil
import sys
import tempfile
from playwright.sync_api import sync_playwright
from PIL import Image

WORK = sys.argv[1] if len(sys.argv) > 1 else "."
if len(sys.argv) > 2:
    date = sys.argv[2]
else:
    cands = sorted(glob.glob(os.path.join(WORK, "????-??-??.html")))
    if not cands:
        sys.exit("未在 %s 找到 {日期}.html；用法: python3 shot_long.py [工作目录] [日期]" % WORK)
    date = os.path.basename(cands[-1])[:-5]
HTML = "file://" + os.path.abspath(os.path.join(WORK, date + ".html"))
OUT = os.path.join(WORK, date + ".png")

with sync_playwright() as p:
    try:
        browser = p.chromium.launch()
    except Exception as e:
        print("default launch failed:", e)
        browser = p.chromium.launch(executable_path="/usr/bin/google-chrome")
    page = browser.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=2.6666667)
    page.goto(HTML)
    page.wait_for_timeout(900)
    # 停掉动画，保证截图稳定
    page.add_style_tag(content="*{animation:none!important;transition:none!important}")
    page.wait_for_timeout(300)
    secs = page.query_selector_all(".screen")
    print("screens found:", len(secs))
    tmpdir = tempfile.mkdtemp(prefix="shotlong_")
    paths = []
    for i, s in enumerate(secs):
        path = os.path.join(tmpdir, f"shot_{i}.png")
        s.screenshot(path=path)
        paths.append(path)
        print("shot", i, os.path.getsize(path))
    browser.close()

imgs = [Image.open(p) for p in paths]
w = max(im.width for im in imgs)
total_h = sum(im.height for im in imgs)
canvas = Image.new("RGB", (w, total_h), (7, 10, 20))
y = 0
for im in imgs:
    canvas.paste(im, (0, y))
    y += im.height
canvas.save(OUT, optimize=True)
shutil.rmtree(tmpdir, ignore_errors=True)
print("final:", OUT, canvas.size, os.path.getsize(OUT), "bytes")

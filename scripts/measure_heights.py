# -*- coding: utf-8 -*-
"""每日行情图表屏高实测工具（固化避坑 #9/#19/#20 的验证手段）。

两种屏型自动识别：
- HTML 长图 reel（.screen 无页脚）：安全线=698（720-22 底padding）。
  bottom==698 为 margin-top:auto 的设计吸附位（不算溢出）；>698 才是溢出。
- gen3 单屏（含 .ft 绝对定位页脚）：gap = 页脚top - 内容bottom，需 >=2px。

用法: python3 measure_heights.py <html路径> [更多html...]
退出码: 全部通过=0, 有溢出=1（便于串到生成脚本后自动把关）。
"""
import sys
from playwright.sync_api import sync_playwright

JS = r"""
(idxs) => {
  const out = [];
  document.querySelectorAll('.screen').forEach((s, i) => {
    const sr = s.getBoundingClientRect();
    const ft = s.querySelector('.ft');
    let maxB = -1e9, who = '';
    s.querySelectorAll('*').forEach(el => {
      if (ft && (ft.contains(el) || el === ft)) return;
      const r = el.getBoundingClientRect();
      if (r.height === 0 && r.width === 0) return;
      const b = r.bottom - sr.top;
      if (b > maxB) { maxB = b; who = (el.className || el.tagName).toString().slice(0, 36); }
    });
    if (ft) {
      const gap = ft.getBoundingClientRect().top - maxB;
      out.push({i, mode: 'ft', gap: Math.round(gap * 10) / 10, who});
    } else {
      out.push({i, mode: 'line', bottom: Math.round(maxB * 10) / 10, who});
    }
  });
  return out;
}
"""

def main(paths):
    bad = 0
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as e:
            print("default launch failed:", e)
            browser = p.chromium.launch(executable_path="/usr/bin/google-chrome")
        page = browser.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=1)
        for path in paths:
            print("==", path)
            page.goto("file://" + path)
            page.wait_for_timeout(700)
            page.add_style_tag(content="*{animation:none!important;transition:none!important}")
            page.wait_for_timeout(200)
            for d in page.evaluate(JS):
                if d["mode"] == "ft":
                    ok = d["gap"] >= 2
                    print(f"  屏{d['i']}: 内容→页脚间隙={d['gap']}px {'OK' if ok else '!!! 溢出/遮挡'}  最深={d['who']}")
                else:
                    over = d["bottom"] > 698
                    print(f"  屏{d['i']}: 内容bottom={d['bottom']}（安全线698） "
                          f"{'!!! 溢出' if over else 'OK（吸附位）'}  最深={d['who']}")
                if d["mode"] == "ft" and d["gap"] < 2:
                    bad += 1
                if d["mode"] == "line" and d["bottom"] > 698:
                    bad += 1
        browser.close()
    if bad:
        print(f"共 {bad} 屏溢出：先压缩（见 pitfalls #9 压缩菜单）再重新生成")
        sys.exit(1)
    print("全部通过")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1:])

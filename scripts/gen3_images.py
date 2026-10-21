#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成三张 1080x1920 竖屏图：图1=上一开盘日预测复盘, 图2=昨日要闻, 图3=今日预测
内容严格取自既有 {日期}.md，不重新预测。

每日用法（唯一改动 = 顶部 D 数据字典）：
  cp gen3_images_{昨天}.py gen3_images_{今天}.py
  # 改 D 里的日期/数据（各键注释见下），然后：
  python3 gen3_images_{今天}.py ./输出目录
  # 跑完必做高度实测（SKILL.md Step 5 / pitfalls #9）
CSS / track() / donut() / main() 为固化模板，禁止改动。
"""
import asyncio
from playwright.async_api import async_playwright

import sys
OUT = sys.argv[1] if len(sys.argv) > 1 else "."  # 用法: python3 gen3_images.py [输出目录]

CSS = """
*{margin:0;padding:0;box-sizing:border-box;}
html,body{background:#070a14;}
body{font-family:"Noto Sans CJK SC","Noto Sans SC",sans-serif;-webkit-font-smoothing:antialiased;}
.screen{width:405px;height:720px;position:relative;overflow:hidden;background:
  radial-gradient(120% 60% at 50% -10%, #16203c 0%, #0a0f20 45%, #070a14 100%);color:#e9edf6;}
/* ---------- header ---------- */
.hd{display:flex;justify-content:space-between;align-items:flex-end;padding:11px 16px 6px;}
.hd-t{font-size:23px;font-weight:700;letter-spacing:.5px;}
.hd-t em{font-style:normal;color:#f5c542;}
.hd-s{font-size:11px;color:#8a94ac;margin-top:3px;letter-spacing:.3px;}
.hd-badge{font-size:10px;color:#f5c542;border:1px solid rgba(245,197,66,.45);border-radius:20px;
  padding:3px 9px;background:rgba(245,197,66,.08);white-space:nowrap;margin-bottom:2px;}
.hd-line{height:1px;background:linear-gradient(90deg,transparent,#f5c54255 20%,#f5c54222 60%,transparent);margin:0 16px;}
/* ---------- generic ---------- */
.sec-t{font-size:13.5px;font-weight:700;color:#cfd7e6;margin:7px 16px 5px;display:flex;align-items:center;gap:6px;}
.sec-t::before{content:"";width:3px;height:12px;background:#f5c542;border-radius:2px;}
/* ---------- screen1 ---------- */
.acc-band{display:flex;align-items:center;gap:13px;margin:5px 16px 1px;padding:6px 12px;
  background:linear-gradient(135deg,rgba(245,197,66,.10),rgba(19,27,49,.6));border:1px solid rgba(245,197,66,.28);border-radius:13px;}
.acc-r{margin-left:auto;text-align:right;}
.acc-big{font-size:16px;font-weight:700;}
.acc-sub{font-size:9.5px;color:#8a94ac;margin-top:2px;line-height:1.45;}
.rev{margin:0 16px 4px;padding:5px 11px;background:rgba(19,27,49,.6);border:1px solid #1e2a45;border-radius:10px;}
.rev-top{display:flex;align-items:center;gap:8px;}
.rev-name{font-size:13px;font-weight:700;min-width:62px;}
.rev-act{font-size:12.5px;font-weight:700;}
.rev-act span{font-size:10.5px;font-weight:700;margin-left:2px;}
.rev-tag{margin-left:auto;font-size:9.5px;font-weight:700;padding:2px 8px;border-radius:10px;white-space:nowrap;}
.tag-ok{color:#0ecb81;background:rgba(14,203,129,.12);border:1px solid rgba(14,203,129,.4);}
.tag-half{color:#f5c542;background:rgba(245,197,66,.12);border:1px solid rgba(245,197,66,.4);}
.rev-pred{font-size:10px;color:#9aa4ba;margin-top:3px;line-height:1.4;}
.rev-pred b{color:#c4cdde;font-weight:600;}
.brief{margin:2px 16px 0;padding:6px 11px;background:rgba(19,27,49,.45);border:1px dashed #2a3a5e;border-radius:10px;}
.brief-t{font-size:10.5px;font-weight:700;color:#cfd7e6;margin-bottom:3px;}
.brief li{font-size:10px;color:#9aa4ba;line-height:1.45;list-style:none;padding-left:10px;position:relative;}
.brief li::before{content:"·";position:absolute;left:2px;color:#f5c542;font-weight:700;}
.brief li b{color:#d5dce9;font-weight:600;}
/* ---------- screen2 ---------- */
.news{margin:0 16px 7px;padding:9px 13px 9px 11px;background:rgba(19,27,49,.72);border:1px solid #22304f;
  border-radius:12px;display:flex;gap:9px;}
.news-no{flex:0 0 26px;height:26px;border-radius:8px;background:linear-gradient(135deg,#f5c542,#e0a92e);
  color:#1a1405;font-size:13px;font-weight:800;display:flex;align-items:center;justify-content:center;margin-top:1px;}
.news-b{flex:1;}
.news-t{font-size:12.5px;font-weight:700;line-height:1.35;}
.news-t .hl{color:#f5c542;}
.news-d{font-size:10.5px;color:#9aa4ba;line-height:1.5;margin-top:3px;}
.news-d b{color:#d5dce9;font-weight:600;}
/* ---------- screen3 ---------- */
.mk{margin:0 16px 3px;padding:4px 12px 4px;background:rgba(19,27,49,.72);border:1px solid #22304f;border-radius:11px;}
.mk-top{display:flex;align-items:baseline;gap:7px;}
.mk-name{font-size:13px;font-weight:800;}
.mk-dir{font-size:10px;font-weight:700;padding:1px 6px;border-radius:7px;background:rgba(245,197,66,.12);
  color:#f5c542;border:1px solid rgba(245,197,66,.35);}
.mk-close{margin-left:auto;font-size:10.5px;color:#cfd7e6;font-weight:700;}
.mk-close b{color:#f5c542;font-size:12.5px;font-weight:800;}
.mk-track{margin:3px 2px 2px;}
.mk-meta{display:flex;justify-content:space-between;font-size:9.5px;color:#aab3c6;}
.mk-meta b{color:#e9edf6;font-weight:700;}
.mk-meta .rng{color:#f6465d;font-weight:700;}
.mk-meta .act{color:#f5c542;font-weight:700;}
.stk{margin:0 16px 4px;padding:4px 11px;background:rgba(19,27,49,.6);border:1px solid #1e2a45;border-radius:10px;}
.stk-row{display:flex;gap:7px;font-size:9.5px;line-height:1.38;align-items:flex-start;}
.stk-row + .stk-row{margin-top:3px;border-top:1px dashed #26334f;padding-top:3px;}
.stk-mkt{flex:0 0 42px;font-weight:800;font-size:10.5px;padding-top:1px;}
.stk-body{flex:1;}
.stk-lab{display:inline-block;font-size:8.5px;font-weight:700;border-radius:5px;padding:0 4px;margin-right:4px;}
.lab-focus{color:#0ecb81;background:rgba(14,203,129,.13);border:1px solid rgba(14,203,129,.35);}
.lab-avoid{color:#f6465d;background:rgba(246,70,93,.13);border:1px solid rgba(246,70,93,.35);}
.stk-body p{margin:1px 0 0;}
.stk-body p b{color:#d5dce9;font-weight:600;}
/* ---------- footer ---------- */
.ft{position:absolute;left:0;right:0;bottom:0;height:28px;display:flex;align-items:center;justify-content:center;
  background:linear-gradient(180deg,rgba(7,10,20,0),rgba(7,10,20,.95) 40%);font-size:10px;color:#7d879c;letter-spacing:.5px;}
.ft b{color:#aab3c6;font-weight:600;}
"""

def track(lo_scale, hi_scale, pred_lo, pred_hi, prev, label_lo, label_hi):
    """SVG 预测区间轨: pred_lo~pred_hi 金色高亮, prev 昨收白色标线"""
    W, H = 340, 22
    def x(v):
        return (v - lo_scale) / (hi_scale - lo_scale) * W
    xl, xh, xp = x(pred_lo), x(pred_hi), x(prev)
    # 昨收标签加深色底 pill，避免被标线穿过、提高可读性；靠边时收拢防裁切
    cx = min(max(xp, 31), W - 31)
    # 端点标签必须完整落在金色区内：黑字(#1a1405)一半压深色轨道底会"黑字黑底"不可读（避坑18）。
    # lo 用 start 锚在左缘内侧、hi 用 end 锚在右缘内侧；带宽不足时合并"lo~hi"居中防叠字。
    PAD, CW = 5, 5.4  # CW: 每位数字约 5.4 个 viewBox 单位（font-size 8.5）
    wl, wh = len(label_lo) * CW + 2, len(label_hi) * CW + 2
    if xh - xl >= 2 * PAD + wl + wh + 4:
        lab_lo = (f'<text x="{xl + PAD:.1f}" y="11" fill="#1a1405" font-size="8.5" font-weight="700"'
                  f' text-anchor="start" font-family="Noto Sans CJK SC">{label_lo}</text>')
        lab_hi = (f'<text x="{xh - PAD:.1f}" y="11" fill="#1a1405" font-size="8.5" font-weight="700"'
                  f' text-anchor="end" font-family="Noto Sans CJK SC">{label_hi}</text>')
    else:
        mid = (xl + xh) / 2
        lab_lo = (f'<text x="{mid:.1f}" y="11" fill="#1a1405" font-size="8.5" font-weight="700"'
                  f' text-anchor="middle" font-family="Noto Sans CJK SC">{label_lo}~{label_hi}</text>')
        lab_hi = ""
    return (
        f'<svg width="100%" height="{H}" viewBox="0 0 {W} {H}" preserveAspectRatio="none" style="display:block;">'
        f'<rect x="0" y="3" width="{W}" height="10" rx="5" fill="#1b2540"/>'
        f'<rect x="{xl:.1f}" y="1.5" width="{xh-xl:.1f}" height="13" rx="6.5" fill="url(#gg)"/>'
        f'<line x1="{xp:.1f}" y1="0" x2="{xp:.1f}" y2="12.5" stroke="#e9edf6" stroke-width="2"/>'
        f'<rect x="{cx-30:.1f}" y="14" width="60" height="8.5" rx="4.2" fill="#0d1322" fill-opacity="0.92"/>'
        f'<text x="{cx:.1f}" y="21" fill="#e9edf6" font-size="8.5" text-anchor="middle" font-family="Noto Sans CJK SC">昨收{prev}</text>'
        f'{lab_lo}{lab_hi}'
        f'<defs><linearGradient id="gg" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="#f5c542"/><stop offset="1" stop-color="#f0b73a"/></linearGradient></defs></svg>'
    )

def donut(pct):
    r, C = 46, 2 * 3.14159 * 46
    dash = C * pct / 100
    return (
        f'<svg width="88" height="88" viewBox="0 0 104 104">'
        f'<circle cx="52" cy="52" r="{r}" fill="none" stroke="#1b2540" stroke-width="10"/>'
        f'<circle cx="52" cy="52" r="{r}" fill="none" stroke="#f5c542" stroke-width="10" stroke-linecap="round"'
        f' stroke-dasharray="{dash:.1f} {C-dash:.1f}" transform="rotate(-90 52 52)"/>'
        f'<text x="52" y="50" fill="#f5c542" font-size="24" font-weight="800" text-anchor="middle" font-family="Noto Sans CJK SC">{pct}%</text>'
        f'<text x="52" y="65" fill="#8a94ac" font-size="9" text-anchor="middle" font-family="Noto Sans CJK SC">综合准确率</text></svg>'
    )

FT = '<div class="ft">AI预测，仅供参考，<b>不构成投资建议</b></div>'

# ---------- 行模板（结构固化，勿改） ----------
def rev_row(n, act, tc, tt, pred):
    """图1 指数复盘行: act=实际值HTML(up/down/待验证), tc=tag类, tt=tag文字"""
    return (f'<div class="rev"><div class="rev-top"><span class="rev-name">{n}</span>'
            f'{act}<span class="rev-tag {tc}">{tt}</span></div>'
            f'<div class="rev-pred">{pred}</div></div>')

def news_row(i, t, d):
    """图2 新闻卡"""
    return (f'<div class="news"><div class="news-no">{i}</div><div class="news-b">'
            f'<div class="news-t">{t}</div><div class="news-d">{d}</div></div></div>')

def mk_card(name, direction, lo, hi, prev, lab_lo, lab_hi, slo, shi, rng, sup, press):
    """图3 大盘卡: lo~hi=预测收盘区间, prev=昨收, slo~shi=区间轨刻度
    "预测收盘"标签 + "实际收盘 待定"占位（pitfalls #20，用户 2026-10-20 反馈）"""
    return (f'<div class="mk">'
            f'<div class="mk-top"><span class="mk-name">{name}</span><span class="mk-dir">{direction}</span>'
            f'<span class="mk-close">预测收盘 <b>{lab_lo}~{lab_hi}</b></span></div>'
            f'<div class="mk-track">{track(slo, shi, lo, hi, prev, lab_lo, lab_hi)}</div>'
            f'<div class="mk-meta"><span>全天 <span class="rng">{rng}</span> · 实际收盘 <span class="act">待定</span></span>'
            f'<span>支撑 <b>{sup}</b> · 压力 <b>{press}</b></span></div></div>')

def stk_row(mkt, color, focus, avoid):
    """图3 个股行: focus/avoid=标签后的 HTML"""
    return (f'<div class="stk-row"><span class="stk-mkt" style="color:{color};">{mkt}</span>'
            f'<div class="stk-body"><span class="stk-lab lab-focus">关注</span>{focus}'
            f'<p><span class="stk-lab lab-avoid">回避</span>{avoid}</p></div></div>')

# ============================================================
# 数据区（每日唯一需要修改的地方；{} 内为当日数据示例）
# ============================================================
D = {
  "date": "2026-10-20",   # 决定输出文件名 {date}_1/2/3.png
  # ---------- 图1：上一开盘日预测复盘 ----------
  "s1": {
    "d": "10·19",                       # 标题日期(短)
    "sub": "上一开盘日 · 2026-10-19 周一",  # 副标题(中性模板, 禁休市/假期状态→pitfalls#19)
    "badge": "累计准确率 87.5%",
    "pct": 87.5,                        # 综合准确率(圆环)
    "big": "14 / 16", "big_note": "项判定准确",
    "sub2": "10-15：92% · 10-16：83% · 10-17主版已验证3.5项<br>恒指/恒生科技今晚收盘后回填终判",
    "sec1": "指数预测 vs 实际",
    # (名称, 实际值HTML, tag类, tag文字, 预测回顾HTML)；待验证行用金色 act + tag-half
    "rev": [
      ("上证指数", '<span class="rev-act up">3730.92<span>▲0.39%</span></span>', "tag-ok", "✓ 准确",
       "预测：<b>企稳偏强</b> · 收盘3690~3745 → 低开高走收3730.92，方向/区间/幅度全兑现"),
      ("创业板指", '<span class="rev-act down">2746.29<span>▼0.94%</span></span>', "tag-ok", "✓ 准确",
       "预测：<b>探底企稳</b> · 收盘2730~2780 → 盘中一度跌超2%后收窄，落在区间内，兑现"),
      ("恒生指数", '<span class="rev-act" style="color:#f5c542;">今晚验证<span>10-20收盘后</span></span>', "tag-half", "◌ 待验证",
       "预测：<b>低开回踩·24000防守后企稳</b> · 收盘24050~24400 → 今晚收盘后回填判定"),
      ("恒生科技", '<span class="rev-act" style="color:#f5c542;">今晚验证<span>10-20收盘后</span></span>', "tag-half", "◌ 待验证",
       "预测：<b>探底企稳·修复非反转</b> · 收盘4070~4150 → 今晚收盘后回填判定"),
    ],
    "extra_top": ('<div class="rev-top" style="font-size:10.5px;color:#9aa4ba;">'
                  '<span class="rev-name" style="font-size:11px;">板块</span><span class="rev-tag tag-ok">✓ 准确</span>'
                  '<span class="rev-name" style="font-size:11px;margin-left:14px;">个股</span><span class="rev-tag tag-half">◐ 部分准确</span></div>'),
    "extra_pred": "军工+2.99%/银行新高/涨价链/半导体存储承压均兑现；偏差：人形机器人新主线未预见、德明利+6.40%逆势反弹",
    "brief_t": "上一开盘日速览",
    "brief": [
      "<li><b>A股低开高走</b>：沪指+0.39%站上3730，工行/建行创历史新高</li>",
      "<li><b>人形机器人午后爆发</b>：宇树科技+16.15%，十余股涨停</li>",
      "<li><b>科创50 -2.17%</b>：半导体/存储补跌，长鑫科技-7.77%</li>",
      "<li><b>GDP+4.6%</b>（Q3回升至+4.5%），金融街论坛央行五项安排</li>",
      "<li><b>成交1.44万亿</b>缩量1179亿，主力净卖出116亿</li>",
    ],
  },
  # ---------- 图2：昨日要闻 ----------
  "s2": {
    "sub": "2026-10-19 全天 ~ 10-20 早间 · 影响市场的关键事件",
    "badge": "6 条精选",
    # (标题HTML, 描述HTML)；标题金色高亮用 <span class="hl">
    "news": [
      ('前三季度GDP <span class="hl">+4.6%</span>，Q3单季回升至+4.5%',
       "GDP总量107.11万亿；规上工业增加值+5.3%；<b>工业机器人产量+29.1%</b>、3D打印+62.5%；70城新房环比涨价城市增至17个"),
      ('金融街论坛：央行<span class="hl">五项安排</span>落地',
       "设立应对非银机构大额赎回的<b>流动性支持工具</b>、SLF扩容、债市互联互通、退出存贷款基准利率方向已定；证监会六方面部署"),
      ('工行/建行<span class="hl">创历史新高</span>，机器人午后爆发',
       "工行3.07万亿<b>重夺A股市值第一</b>、建行3.03万亿；21家银行中期分红超2600亿；宇树科技+16.15%创上市以来最大单日涨幅"),
      ('隔夜费半<span class="hl">终结八连跌</span>，存储暴涨',
       "纳指+1.11%；西部数据+6.09%、闪迪+5.53%、美光+2.97%；10Y美债+7.5bp至5.148%；WTI+2.22%报103.66美元"),
      ('今日<span class="hl">解禁高峰</span>+情绪退潮信号',
       "颀中科技解禁69.23%约<b>108.74亿</b>、本周合计952.83亿（明日单日643.84亿）；新华传媒11连板终结、连板高度降至三板"),
      ('<span class="hl">产业与政策</span>动态',
       "商务部对无人机/盾构机出口管制；工信部水泥稳增长座谈（反内卷）；H酸+6.67%创反弹新高；首批18只主动ETF获批近360亿"),
    ],
    "other_t": "其他动态",
    "other": [
      "<li>今日9:00 LPR（预期按兵不动）+<b>英伟达GTC柏林</b>+APEC财长会中国香港（10-20~21）</li>",
      "<li>宁德时代/中国移动三季报今日盘后；Meta/特斯拉10-21盘后检验AI资本开支</li>",
      "<li>恒指夜期24112（-0.19%、低水75点）；A50期指夜盘-0.09%</li>",
      "<li>人民币在岸收6.6817创四年新高；现货金4140.5美元</li>",
      "<li>亨通光电/生益科技三季报预增150%+/160%+；长鑫科技-7.77%居净卖出首位</li>",
    ],
  },
  # ---------- 图3：今日预测 ----------
  "s3": {
    "d": "10·20",
    "sub": "2026-10-20 周二 · 大盘 / 板块 / 个股 · 晨间观点记录",  # 副标题(中性模板, 禁休市/假期状态→pitfalls#19)
    "badge": "含收盘价与波动范围",
    "sec1": "大盘（预测收盘价 + 波动范围）",
    # (名称, 方向, 收盘lo, 收盘hi, 昨收, 标签lo, 标签hi, 轨lo, 轨hi, 波动, 支撑, 压力)
    "mk": [
      ("上证指数", "高开震荡·量能定高度", 3725, 3775, 3730.92, "3725", "3775", 3700, 3800, "-0.5%~+1.0%", "3715/3700", "3750~3770"),
      ("创业板指", "高开修复·存储链领涨", 2720, 2770, 2746.29, "2720", "2770", 2690, 2830, "-0.9%~+0.6%", "2720/2730", "2785~2800"),
      ("恒生指数", "平开震荡·修复反弹", 24050, 24400, 24186.83, "24050", "24400", 23900, 24500, "-1.0%~+0.5%", "24000~24100", "24350~24500"),
      ("恒生科技", "探底回升·修复非反转", 4070, 4150, 4108.24, "4070", "4150", 4030, 4180, "-1.0%~+0.5%", "4040~4060", "4160~4180"),
    ],
    "sec2": "个股（关注 / 回避）",
    # (市场, 颜色, 关注HTML, 回避HTML)；每市场关注/回避各≤5条、括注≤10字(防溢出)
    "stk": [
      ("港股", "#f5c542",
       '<b>宁德时代</b>（03750三季报）/ <b>中国移动</b>（00941三季报+高息）/ <b>腾讯</b>（00700防御+AI）/ <b>中芯国际</b>（00981国产替代）/ <b>山东黄金</b>（01787金价高位）',
       '<b>联想</b>（00992 +8%勿追）/ <b>赣锋锂业</b>（01772 Q3环比-68%）/ <b>中海油</b>（00883油价回吐）/ <b>药明生物</b>（02269）/ 纯概念算力股'),
      ("上证", "#f6465d",
       '<b>工商银行</b>（601398新高+分红）/ <b>建设银行</b>（601939）/ <b>亨通光电</b>（600487预增150%）/ <b>生益科技</b>（600183预增160%）/ <b>顺鑫农业</b>（000860白酒修复）',
       '<b>长鑫科技</b>（688825 -7.77%）/ <b>新华传媒</b>（600825连板终结）/ <b>招商南油</b>（601975）/ <b>荣丰控股</b>（000668）/ <b>颀中科技</b>（688352今日解禁）'),
      ("创业板", "#0ecb81",
       '<b>佰维存储</b>（688525）/ <b>兆易创新</b>（603986）存储修复 / <b>兆威机电</b>（003021机器人）/ <b>四会富仕</b>（300852 PCB）/ <b>澜起科技</b>（688008回购）/ <b>江苏新能</b>（603693电力）',
       '<b>新易盛</b>（300502）/ <b>中际旭创</b>（300308）/ <b>天孚通信</b>（300394）易中天 / <b>胜宏科技</b>（300476）/ <b>宁德时代</b>（300750盘后财报）'),
    ],
  },
}

S1, S2, S3 = D["s1"], D["s2"], D["s3"]
rev_cards = "".join(rev_row(*r) for r in S1["rev"])
news_cards = "".join(news_row(i + 1, t, d) for i, (t, d) in enumerate(S2["news"]))
mk_cards = "".join(mk_card(*m) for m in S3["mk"])
stk_cards = "".join(stk_row(*s) for s in S3["stk"])

# ================= 图1：上一开盘日预测复盘 =================
SCREEN1 = f"""
<div class="screen">
  <div class="hd">
    <div>
      <div class="hd-t">{S1['d']} <em>预测复盘</em></div>
      <div class="hd-s">{S1['sub']}</div>
    </div>
    <div class="hd-badge">{S1['badge']}</div>
  </div>
  <div class="hd-line"></div>

  <div class="acc-band">
    {donut(S1['pct'])}
    <div class="acc-r">
      <div class="acc-big">{S1['big']} <span style="font-size:11px;color:#8a94ac;">{S1['big_note']}</span></div>
      <div class="acc-sub">{S1['sub2']}</div>
    </div>
  </div>

  <div class="sec-t">{S1['sec1']}</div>
  {rev_cards}
  <div class="rev" style="padding:6px 12px;">
    {S1['extra_top']}
    <div class="rev-pred">{S1['extra_pred']}</div>
  </div>

  <div class="sec-t">{S1['brief_t']}</div>
  <div class="brief">
    {''.join(S1['brief'])}
  </div>
  {FT}
</div>
"""

# ================= 图2：昨日要闻 =================
SCREEN2 = f"""
<div class="screen">
  <div class="hd">
    <div>
      <div class="hd-t">昨日<em>要闻</em></div>
      <div class="hd-s">{S2['sub']}</div>
    </div>
    <div class="hd-badge">{S2['badge']}</div>
  </div>
  <div class="hd-line"></div>

  {news_cards}

  <div class="brief" style="margin-top:4px;">
    <div class="brief-t">{S2['other_t']}</div>
    {''.join(S2['other'])}
  </div>
  {FT}
</div>
"""

# ================= 图3：今日预测 =================
SCREEN3 = f"""
<div class="screen">
  <div class="hd">
    <div>
      <div class="hd-t">{S3['d']} <em>今日预测</em></div>
      <div class="hd-s">{S3['sub']}</div>
    </div>
    <div class="hd-badge">{S3['badge']}</div>
  </div>
  <div class="hd-line"></div>

  <div class="sec-t">{S3['sec1']}</div>
  {mk_cards}

  <div class="sec-t">{S3['sec2']}</div>
  <div class="stk">
    {stk_cards}
  </div>
  {FT}
</div>
"""


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 405, "height": 720},
                                      device_scale_factor=2.6666667)
        for i, scr in enumerate([SCREEN1, SCREEN2, SCREEN3], 1):
            html = ("<html><head><meta charset='utf-8'><style>" + CSS +
                    "</style></head><body>" + scr + "</body></html>")
            path = f"/tmp/img{i}.html"
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            await page.goto(f"file://{path}")
            await page.add_style_tag(content="*{animation:none!important;transition:none!important}")
            await page.wait_for_timeout(120)
            out = f"{OUT}/{D['date']}_{i}.png"
            await page.screenshot(path=out)
            print("saved", out)
        await browser.close()

asyncio.run(main())

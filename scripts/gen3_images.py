#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成三张 1080x1920 竖屏图：图1=上一开盘日预测复盘, 图2=昨日要闻, 图3=今日预测
内容严格取自既有 {日期}.md，不重新预测。

每日用法（唯一改动 = 顶部 D 数据字典）：
  cp gen3_images_{昨天}.py gen3_images_{今天}.py
  # 改 D 里的日期/数据（各键注释见下），然后：
  python3 gen3_images_{今天}.py ./输出目录
  # 跑完必做高度实测（SKILL.md Step 5 / pitfalls #9）
  # 产出为 PNG，交付归档前用 scripts/to_jpg.py 统一转 JPG（见 SKILL.md 硬性规则 #12）
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
.tag-bad{color:#8a94ac;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.2);}
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
.mk-meta b.pc{color:#f5c542;}
.mk-meta b.pd{color:#e9edf6;}
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

def track(prev, pred_lo, pred_hi, day_lo, day_hi):
    """SVG 预测区间轨（2026-10-21 重设计，修"涨幅百分比与数值不符/黄条比例失真"反馈）:
    刻度统一为昨收±2%——四卡同一比例尺，金条宽度即涨幅百分比、跨卡可比；
    day_lo~day_hi 全天波动带(淡金，须包含收盘区) → pred_lo~pred_hi 预测收盘区(金) → prev 昨收白色标线。
    条内不放端点标签：数值在卡头"预测收盘"与 meta"较昨收"已双显，避免窄带叠字（避坑18）。"""
    W, H = 340, 22
    lo_scale, hi_scale = prev * 0.98, prev * 1.02
    def x(v):
        return (v - lo_scale) / (hi_scale - lo_scale) * W
    xil, xih = x(day_lo), x(day_hi)
    xl, xh, xp = x(pred_lo), x(pred_hi), x(prev)
    # 昨收标签加深色底 pill，避免被标线穿过、提高可读性；靠边时收拢防裁切
    cx = min(max(xp, 31), W - 31)
    return (
        f'<svg width="100%" height="{H}" viewBox="0 0 {W} {H}" preserveAspectRatio="none" style="display:block;">'
        f'<rect x="0" y="3" width="{W}" height="10" rx="5" fill="#1b2540"/>'
        f'<rect x="{xil:.1f}" y="3.5" width="{max(xih - xil, 4):.1f}" height="9" rx="4.5" fill="rgba(245,197,66,.22)"/>'
        f'<rect x="{xl:.1f}" y="1.5" width="{xh - xl:.1f}" height="13" rx="6.5" fill="url(#gg)"/>'
        f'<line x1="{xp:.1f}" y1="0" x2="{xp:.1f}" y2="12.5" stroke="#e9edf6" stroke-width="2"/>'
        f'<rect x="{cx - 30:.1f}" y="14" width="60" height="8.5" rx="4.2" fill="#0d1322" fill-opacity="0.92"/>'
        f'<text x="{cx:.1f}" y="21" fill="#e9edf6" font-size="8.5" text-anchor="middle" font-family="Noto Sans CJK SC">昨收{prev}</text>'
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

def mk_card(name, direction, lo, hi, day_lo, day_hi, prev, sup, press):
    """图3 大盘卡（2026-10-21 重设计）: lo~hi=预测收盘区(宽度≤昨收1%),
    day_lo~day_hi=全天波动区(≤1.5pct且必须包含lo~hi), prev=昨收。
    涨幅百分比一律由数值实时计算(_p)，禁手填字符串——2026-10-21 用户反馈：手填"全天+0%"
    与"预测收盘3955~4035"(昨收3994.77应为-1.0%~+1.0%)自相矛盾。
    "预测收盘"标签 + "实际收盘 待定"占位（pitfalls #20，用户 2026-10-20 反馈）。
    press=压力位：本卡宽度放不下（meta 两行会折行），压力位只在 MD/HTML 呈现，故卡上不展示。"""
    def _p(v):
        r = round((v - prev) / prev * 100, 1)
        return "%+.1f" % (r if r != 0 else 0.0)  # 防 -0.0%
    return (f'<div class="mk">'
            f'<div class="mk-top"><span class="mk-name">{name}</span><span class="mk-dir">{direction}</span>'
            f'<span class="mk-close">预测收盘 <b>{lo}~{hi}</b></span></div>'
            f'<div class="mk-track">{track(prev, lo, hi, day_lo, day_hi)}</div>'
            f'<div class="mk-meta"><span>较昨收 <b class="pc">{_p(lo)}~{_p(hi)}</b> · 实际收盘 <span class="act">待定</span></span>'
            f'<span>全天 <b class="pd">{_p(day_lo)}~{_p(day_hi)}</b> · 支撑 <b>{sup}</b></span></div></div>')

def stk_row(mkt, color, focus, avoid):
    """图3 个股行: focus/avoid=标签后的 HTML"""
    return (f'<div class="stk-row"><span class="stk-mkt" style="color:{color};">{mkt}</span>'
            f'<div class="stk-body"><span class="stk-lab lab-focus">关注</span>{focus}'
            f'<p><span class="stk-lab lab-avoid">回避</span>{avoid}</p></div></div>')

# ============================================================
# 数据区（每日唯一需要修改的地方；{} 内为当日数据示例）
# ============================================================
D = {
  "date": "2026-10-21",   # 决定输出文件名 {date}_1/2/3.png
  # ---------- 图1：上一开盘日预测复盘 ----------
  "s1": {
    "d": "10·20",
    "sub": "上一开盘日 · 2026-10-20 周二",
    "badge": "累计准确率 70.8%",
    "pct": 70.8,
    "big": "17 / 24", "big_note": "项判定准确",
    "sub2": "10-15：92% · 10-16：83% · 10-17主版：3.5项 · 10-20：3项<br>恒指/恒科 10-20 收盘验证：双双跌破区间下限",
    "sec1": "指数预测 vs 实际",
    "rev": [
      ("上证指数", '<span class="rev-act up">3735.37<span>▲0.12%</span></span>', "tag-ok", "✓ 准确",
       "预测：<b>高开震荡·量能定高度</b> · 收盘3725~3775 → 高开震荡收3735.37，落在区间内，兑现"),
      ("创业板指", '<span class="rev-act down">2739.20<span>▼0.26%</span></span>', "tag-ok", "✓ 准确",
       "预测：<b>高开修复·存储链领涨</b> · 收盘2720~2770 → 高开整理收2739.20，落在区间内，兑现"),
      ("恒生指数", '<span class="rev-act down">23867.74<span>▼1.32%</span></span>', "tag-bad", "✗ 不准确",
       "预测：<b>平开震荡·修复反弹</b> · 收盘24050~24400 → 锂电/大模型高位股独立杀跌，跌破区间下限约0.8pct"),
      ("恒生科技", '<span class="rev-act down">4045.91<span>▼1.52%</span></span>', "tag-bad", "✗ 不准确",
       "预测：<b>探底回升·修复非反转</b> · 收盘4070~4150 → 与恒指共振走弱，跌破区间下限约0.6pct"),
    ],
    "extra_top": ('<div class="rev-top" style="font-size:10.5px;color:#9aa4ba;">'
                  '<span class="rev-name" style="font-size:11px;">板块</span><span class="rev-tag tag-half">◐ 部分准确</span>'
                  '<span class="rev-name" style="font-size:11px;margin-left:14px;">个股</span><span class="rev-tag tag-half">◐ 部分准确</span></div>'),
    "extra_pred": "科技修复链+机器人/医疗美容/消费电子涨幅居前兑现；偏差：煤炭/保险/航海装备跌幅居前与“涨价链/红利占优”判断相反",
    "brief_t": "上一开盘日速览",
    "brief": [
      "<li><b>A股高开震荡</b>：沪指+0.12%收3735.37，两市成交1.46万亿放量186亿</li>",
      "<li><b>超3700股上涨</b>：医疗美容/机器人/消费电子/半导体涨幅居前</li>",
      "<li><b>科创综指+2.13%</b>：机器人/端侧芯片/折叠屏领涨，错杀修复兑现</li>",
      "<li><b>港股独立走弱</b>：恒指-1.32%，锂电/大模型杀跌，南向净卖出17.23亿</li>",
      "<li><b>宽基ETF尾盘放量</b>：上证50ETF华夏 75.3亿创1月29日以来天量</li>",
    ],
  },
  # ---------- 图2：昨日要闻 ----------
  "s2": {
    "sub": "2026-10-20 全天 ~ 10-21 · 影响市场的关键事件",
    "badge": "6 条精选",
    "news": [
      ('宁德时代<span class="hl">暴跌 12%</span>：增收不增利+评级下调',
       "Q3净利+14.54%远低于营收+58.58%；<b>摩根大通H股目标价725→500港元</b>；出口退税13%→9%；碳酸锂跌破10万"),
      ('国家数据集团成立，<span class="hl">数据要素</span>引暴',
       "落地雄安；数据确权/DRG-DIP概念领涨；金融街论坛：<b>北证50ETF推进</b>、市值配售改革、优化上市审核支持新兴产业"),
      ('LPR连续17个月不变，央行<span class="hl">切换隔夜逆回购</span>',
       "1Y 3.00%/5Y+ 3.50%按兵不动；潘功胜表态<b>退出存贷款基准利率</b>；10-21起连续开展隔夜逆回购、每日不超1万亿"),
      ('美制裁DeepSeek等5家中企，<span class="hl">国产模型密集迭代</span>',
       "商务部回应；DeepSeek开源<b>DeepInfer</b>+更新V4.1 Flash；智谱发布法律专用模型、阶跃披露长程Agent训练方案"),
      ('道指<span class="hl">独涨1.02%</span>，医疗地产领涨',
       "道指52495.88(+1.02%)、标普+0.28%、纳指-0.02%；3M+5.78%领涨；SpaceX盘后涨超6%；Meta-1.59%；美伊协议传闻反复"),
      ('<span class="hl">ETF放量托底</span>+主动ETF周五开售',
       "10-20上证50ETF华夏 75.3亿创天量；<b>10-21创业板ETF易方达成交破100亿</b>；首承18只主动ETF 10-23开售（近360亿）"),
    ],
    "other_t": "其他动态",
    "other": [
      "<li><b>今夜特斯拉+Meta财报</b>：AI资本开支指引被机构视为“比盈利更重要的压力测试”</li>",
      "<li>Anthropic半年营收163亿美元、亏损807亿美元；周小川就AI风险发出警示</li>",
      "<li>通用汽车200亿美元回购；布油109美元高位、美伊“七日计划”谈判反复</li>",
      "<li>工信部：“十五五”期间建设一批专精特新赋能中心；发改委扩大内需方案(2026-2030)</li>",
      "<li>南向资金10-21净卖出44.34亿港元、<b>连续6日净卖出</b>；腾讯-17.06亿居净卖出首位</li>",
    ],
  },
  # ---------- 图3：今日预测 ----------
  "s3": {
    "d": "10·22",
    "sub": "2026-10-22 周四 · 大盘 / 板块 / 个股 · 观点记录",
    "badge": "含收盘价与波动范围",
    "sec1": "大盘（预测收盘价 + 波动范围）",
    "mk": [
      # (名称, 方向, 收盘lo, 收盘hi, 全天lo, 全天hi, 昨收, 支撑, 压力)；涨幅%由mk_card实时计算
      # 硬规则：收盘区宽度≤昨收1%、全天区≤1.5pct且含收盘区（2026-10-21 用户定稿）
      ("上证指数", "低开震荡·拉锯整理", 3688, 3723, 3678, 3733, 3713.03, "3700/3680", "3735~3750"),
      ("创业板指", "低开探底·企稳修复", 2680, 2706, 2666, 2706, 2694.71, "2660/2650", "2720~2740"),
      ("恒生指数", "低开震荡·弱势整理", 23540, 23770, 23490, 23830, 23651.87, "23400~23500", "23850~24000"),
      ("恒生科技", "低开探底·弱势拉锯", 3976, 4013, 3966, 4024, 3994.77, "3950~3970", "4035~4060"),
    ],
    "sec2": "个股（关注 / 回避）",
    "stk": [
      ("港股", "#f5c542",
       '<b>联想集团</b>（00992财报超预期）/ <b>长飞光纤</b>（06869净中2.5亿）/ <b>中国海洋石油</b>（00883净中1.7亿）/ <b>百济神州</b>（06160创新药）',
       '<b>宁德时代</b>（03750 -11.4%）/ <b>中国移动</b>（00941 A/H双杀）/ <b>泡泡玛特</b>（09992）/ <b>福耀玻璃</b>（03606特斯拉链）'),
      ("上证", "#f6465d",
       '<b>数据要素</b>（政策主线）/ <b>国产算力链</b>（ASIC+2.54%）/ <b>亨通光电</b>（600487激光通信）/ <b>工商银行</b>（601398红利防御）/ <b>养殖</b>（猪肉）',
       '<b>中国移动</b>（600941 -5.09%）/ <b>煤炭饮酒</b>（今日领跌）/ <b>新易盛</b>（300502流出8亿）/ 电池链联动'),
      ("创业板", "#0ecb81",
       '<b>ASIC芯片</b>（+2.54%逆势）/ <b>利亚德</b>（300296观察）/ <b>激光通信</b>（MCP/电子布）/ <b>创业板ETF</b>（成交破百亿）',
       '<b>宁德时代</b>（300750 -12.03%）/ <b>固态电池</b>（钻电/六氟）/ <b>新易盛</b>（300502）/ <b>阳光电源</b>（300274流出6.9亿）'),
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

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
  "date": "2026-10-26",   # 决定中间文件名 {date}_1/2/3.png；归档前由 to_jpg.py 转为 JPG
  # ---------- 图1：上一开盘日预测复盘 ----------
  "s1": {
    "d": "10·23",
    "sub": "上一开盘日 · 2026-10-23 周五",
    "badge": "累计准确率 52.8%",
    "pct": 52.8,
    "big": "19 / 36", "big_note": "六项制累计得分",
    "sub2": "本期开盘2/4命中 · 收盘0/4命中 · 板块0.5 · 个股0.5<br>开盘方向与收盘方向分开验证，避免以开盘命中替代全天命中",
    "sec1": "开盘预测 / 收盘预测 vs 实际",
    "rev": [
      ("上证指数", '<span class="rev-act up">3690.48<span>▲0.89%</span></span>', "tag-half", "◐ 开准收错",
       "预测：<b>低开下探·弱势企稳</b> · 实际低开0.94%命中；午后深V收3690.48，突破收盘区间上限"),
      ("创业板指", '<span class="rev-act up">2684.10<span>▲4.16%</span></span>', "tag-half", "◐ 开准收错",
       "预测：<b>低开探底·弱势整理</b> · 实际低开1.66%命中；午后反攻收涨4.16%，反弹弹性明显低估"),
      ("恒生指数", '<span class="rev-act up">23093.37<span>▲0.69%</span></span>', "tag-bad", "✗ 不准确",
       "预测：<b>低开弱势整理</b> · 实际高开0.41%，收23093.37，高于22760~22980预测区间"),
      ("恒生科技", '<span class="rev-act up">3871.66<span>▲2.05%</span></span>', "tag-bad", "✗ 不准确",
       "预测：<b>低开探底·弱势拉锯</b> · 实际高开0.51%，收涨2.05%，科技修复力度被低估"),
    ],
    "extra_top": ('<div class="rev-top" style="font-size:10.5px;color:#9aa4ba;">'
                  '<span class="rev-name" style="font-size:11px;">板块</span><span class="rev-tag tag-half">◐ 部分准确</span>'
                  '<span class="rev-name" style="font-size:11px;margin-left:14px;">个股</span><span class="rev-tag tag-half">◐ 部分准确</span></div>'),
    "extra_pred": "机器人/AI应用兑现；但半导体与成长链午后强反攻，红利防御和多数回避判断偏差，综合1/6",
    "brief_t": "上一开盘日速览",
    "brief": [
      "<li><b>A股深V反攻</b>：沪指盘中3574.27后收3690.48，创业板收涨4.16%</li>",
      "<li><b>量能放大</b>：两市成交1.96万亿，较上日放量4276亿，4526股上涨</li>",
      "<li><b>机器人爆发</b>：人形机器人/软件/半导体领涨，银行逆势收跌</li>",
      "<li><b>港股同步修复</b>：恒指+0.69%、恒科+2.05%，南向仍净卖出16.70亿</li>",
      "<li><b>经验修订</b>：开盘与收盘分开计分，ETF承接纳入日内反转因子</li>",
    ],
  },
  # ---------- 图2：昨日要闻 ----------
  "s2": {
    "sub": "2026-10-23 收盘 ~ 10-26 06:19 · 影响开盘的关键事件",
    "badge": "6 条精选",
    "news": [
      ('美股期指走强，<span class="hl">纳指100期货+0.66%</span>',
       "道指/标普500期货分别+0.34%/+0.48%；<b>WTI今晨回落0.99%</b>至102.246美元，亚洲风险偏好边际改善"),
      ('央行今日开展<span class="hl">7000亿元MLF</span>',
       "期限1年，意在保持银行体系流动性充裕；10月到期9000亿元，月度口径仍需关注净回笼影响"),
      ('上证指数、科创综指<span class="hl">编制新规落地</span>',
       "单个样本权重上限15%；风险警示证券剔除时点调整；<b>10月26日起正式实施</b>"),
      ('A股上周五<span class="hl">深V放量反攻</span>',
       "沪指+0.89%、创业板+4.16%；成交1.96万亿、放量4276亿；机器人/软件/半导体领涨，周一面临兑现检验"),
      ('美股收跌但<span class="hl">费半+0.44%</span>',
       "道指-1.23%、标普-0.52%、纳指-0.21%；金龙指数-0.84%；AI硬件情绪边际修复但尚未反转"),
      ('AI就业、<span class="hl">6G与存储</span>政策催化',
       "国办提出强化AI就业创造；信息化规划提出适时启动6G商用；机构认为存储短缺或持续至2028年"),
    ],
    "other_t": "其他动态",
    "other": [
      "<li><b>南向连续8日净卖出</b>：10-23净卖出16.70亿港元，但流出规模显著收窄</li>",
      "<li>腾讯获南向净买入12.96亿港元；阿里/中芯分别净卖出14.06亿/7.99亿</li>",
      "<li>美联储10月27~28日议息，油价高位与美债收益率仍压制成长估值</li>",
      "<li>前三季度造船完工/新接/手持订单全球份额63.6%/81.8%/72.4%</li>",
      "<li>三季报密集披露+本周约千亿解禁，指数企稳不等于个股风险消失</li>",
    ],
  },
  # ---------- 图3：今日预测 ----------
  "s3": {
    "d": "10·26",
    "sub": "2026-10-26 周一 · 开盘方向优先 · 附收盘与日内区间",
    "badge": "开盘区间优先",
    "sec1": "大盘（开盘区间写入方向标签）",
    "mk": [
      # (名称, 方向, 收盘lo, 收盘hi, 全天lo, 全天hi, 昨收, 支撑, 压力)；涨幅%由mk_card实时计算
      # 硬规则：收盘区宽度≤昨收1%、全天区≤1.5pct且含收盘区
      ("上证指数", "开3688~3702·平开偏强", 3680, 3712, 3666, 3720, 3690.48, "3674/3666", "3700~3720"),
      ("创业板指", "开2688~2704·小幅高开", 2672, 2698, 2664, 2704, 2684.10, "2660/2640", "2700~2720"),
      ("恒生指数", "开23030~23120·平开略弱", 22950, 23150, 22880, 23220, 23093.37, "22900/22800", "23150~23220"),
      ("恒生科技", "开3865~3900·平开偏强", 3845, 3882, 3842, 3900, 3871.66, "3835/3800", "3900~3920"),
    ],
    "sec2": "个股（观察 / 谨慎）",
    "stk": [
      ("港股", "#f5c542",
       '<b>腾讯</b>（00700南向净买）/ <b>中海油</b>（00883油价）/ <b>小米</b>（01810科技修复）',
       '<b>阿里</b>（09988净卖14亿）/ <b>中芯</b>（00981等回流）/ 高估值无盈利科技'),
      ("上证", "#f6465d",
       '<b>寒武纪</b>（688256业绩）/ <b>中国船舶</b>（600150订单）/ <b>移远通信</b>（603236 6G）/ <b>鸣志电器</b>（603728机器人）',
       '连续涨停机器人前排 / <b>黄金珠宝</b> / 航空运输 / 业绩不及预期股'),
      ("创业板", "#0ecb81",
       '<b>汇川技术</b>（300124机器人）/ <b>江龙船艇</b>（300589）/ <b>信维通信</b>（300136 6G）/ <b>东方财富</b>（300059证券IT）',
       '周五低点抄底后浮盈过大品种 / 解禁压力股 / 纯题材高估值股'),
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

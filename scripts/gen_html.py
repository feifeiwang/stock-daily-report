# -*- coding: utf-8 -*-
"""生成 2026-10-21 手机竖屏（抖音可刷）HTML 行情速览。
设计基准 405x720（9:16），截图 DSF=2.6666667 -> 1080x1920/屏。
所有图表为内联 SVG，无外部依赖；数据均为已核实公开数据。
"""
import math
import sys

W = 307.0  # 卡片内容宽 = 屏405 - 左padding26 - 右padding44 - 卡padding28；改屏padding务必同步此值

# ---------- SVG 组件 ----------

def diverging_chart(rows, max_abs, label_w=60, val_w=60, row_h=30):
    n = len(rows)
    tick_h = 20
    H = n * row_h + tick_h
    bar_x0 = label_w + 4
    bar_x1 = W - val_w
    bar_w = bar_x1 - bar_x0
    zero = bar_x0 + bar_w / 2
    half = bar_w / 2
    p = ['<svg viewBox="0 0 %.0f %d" width="%.0f" height="%d" xmlns="http://www.w3.org/2000/svg">' % (W, H, W, H)]
    p.append('<line x1="%.1f" y1="2" x2="%.1f" y2="%d" stroke="rgba(255,255,255,.28)" stroke-width="1" stroke-dasharray="3 3"/>' % (zero, zero, n * row_h))
    for i, (lab, v) in enumerate(rows):
        y = i * row_h + row_h / 2
        p.append('<text x="%d" y="%.1f" text-anchor="end" font-size="12.5" fill="#aab3c6">%s</text>' % (label_w - 6, y + 4.3, lab))
        L = abs(v) / max_abs * half
        col = "#f6465d" if v > 0 else "#0ecb81"
        arrow = "▲" if v > 0 else "▼"
        txt = "%s%.2f%%" % (arrow, abs(v))
        if v >= 0:
            p.append('<rect x="%.1f" y="%.1f" width="%.1f" height="14" rx="3.5" fill="%s"/>' % (zero, y - 7, L, col))
        else:
            p.append('<rect x="%.1f" y="%.1f" width="%.1f" height="14" rx="3.5" fill="%s"/>' % (zero - L, y - 7, L, col))
        p.append('<text x="%.0f" y="%.1f" text-anchor="end" font-size="12" font-weight="700" fill="%s">%s</text>' % (W - 2, y + 4.3, col, txt))
    ty = n * row_h + 13
    for frac, lab in [(-1, "-%g%%" % max_abs), (0, "0"), (1, "+%g%%" % max_abs)]:
        x = zero + frac * half
        p.append('<text x="%.1f" y="%d" text-anchor="middle" font-size="9.5" fill="rgba(255,255,255,.38)">%s</text>' % (x, ty, lab))
    p.append('</svg>')
    return "".join(p)


def range_card(name, tag, lo, hi, amp, prev, sup, press, up):
    # amp 参数保留兼容数据元组，但不再上图（百分比振幅与 lo~hi 点区间冗余，详见 MD 日报）
    inner = W

    def _fmt(v, d=0):  # 千分位逗号仅用于 >=10000，与金融惯例一致
        s = format(v, ",.%df" % d)
        return s if abs(v) >= 10000 else s.replace(",", "")
    pad = (hi - lo) * 0.22
    def x(v):
        return (v - (lo - pad)) / (hi - lo + 2 * pad) * inner
    H = 46
    col = "#f6465d" if up else "#0ecb81"
    xlo, xhi, xp = x(lo), x(hi), x(prev)
    xp = min(max(xp, 6), inner - 6)
    p = ['<svg viewBox="0 0 %.0f %d" width="%.0f" height="%d" xmlns="http://www.w3.org/2000/svg">' % (inner, H, inner, H)]
    p.append('<rect x="0" y="16" width="%.0f" height="9" rx="4.5" fill="rgba(255,255,255,.09)"/>' % inner)
    p.append('<rect x="%.1f" y="16" width="%.1f" height="9" rx="4.5" fill="%s" opacity=".85"/>' % (xlo, max(xhi - xlo, 4), col))
    p.append('<line x1="%.1f" y1="10" x2="%.1f" y2="31" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>' % (xp, xp))
    p.append('<circle cx="%.1f" cy="31" r="3" fill="#ffffff"/>' % xp)
    lab = "昨收 %s" % _fmt(prev, 2 if prev < 10000 else 0)
    tx = min(max(xp, 34), inner - 34)
    p.append('<text x="%.1f" y="8" text-anchor="middle" font-size="10" font-weight="700" fill="#ffffff">%s</text>' % (tx, lab))
    p.append('<text x="%.1f" y="%d" text-anchor="middle" font-size="10" fill="rgba(255,255,255,.55)">%s</text>' % (xlo, H - 3, _fmt(lo)))
    p.append('<text x="%.1f" y="%d" text-anchor="middle" font-size="10" fill="rgba(255,255,255,.55)">%s</text>' % (xhi, H - 3, _fmt(hi)))
    p.append('</svg>')
    svg = "".join(p)
    lo_lab, hi_lab = _fmt(lo), _fmt(hi)
    return (
        '<div class="rcard">'
        '<div class="rc-hd"><span class="rc-name">%s</span><span class="rc-tag">%s</span>'
        '<span class="rc-close">预测收盘 <b>%s~%s</b></span></div>'
        '%s'
        '<div class="rc-ft">支撑 <b>%s</b>　·　压力 <b>%s</b>　·　实际收盘 <span class="act">待定</span></div>'
        '</div>' % (name, tag, lo_lab, hi_lab, svg, sup, press)
    )


def donut(pct, size=118, r=50, sw=13):
    c = 2 * math.pi * r
    dash = c * pct / 100
    return (
        '<svg viewBox="0 0 %d %d" width="%d" height="%d" xmlns="http://www.w3.org/2000/svg">'
        '<circle cx="%d" cy="%d" r="%d" fill="none" stroke="rgba(255,255,255,.10)" stroke-width="%d"/>'
        '<circle cx="%d" cy="%d" r="%d" fill="none" stroke="#f5c542" stroke-width="%d" stroke-linecap="round" '
        'stroke-dasharray="%.1f %.1f" transform="rotate(-90 %d %d)"/>'
        '<text x="%d" y="%d" text-anchor="middle" font-size="27" font-weight="900" fill="#f5c542">%g%%</text>'
        '<text x="%d" y="%d" text-anchor="middle" font-size="10.5" fill="rgba(255,255,255,.55)">6项判定</text>'
        '</svg>'
        % (size, size, size, size, size // 2, size // 2, r, sw,
           size // 2, size // 2, r, sw, dash, c - dash, size // 2, size // 2,
           size // 2, size // 2 + 2, pct, size // 2, size // 2 + 20)
    )


# ---------- 数据（均已核实，10-21 收盘 / 隔夜美股 10-20） ----------
idx_rows = [
    ("上证指数", -0.60), ("深证成指", -0.82), ("创业板指", -1.62), ("科创50", 0.06),
    ("科创综指", -0.08), ("北证50", -0.72), ("恒生指数", -0.90), ("恒生科技", -1.26),
    ("国企指数", -1.08), ("道琼斯", 1.02), ("标普500", 0.28), ("纳斯达克", -0.02),
]
news = [
    ("榜", "#f5c542", "LPR连续17个月不变，央行切换隔夜逆回购", "1Y 3.00%/5Y+ 3.50%不变；退出存贷款基准利率；10-21起隔夜逆回购每日不超1万亿"),
    ("数", "#0ecb81", "国家数据集团成立，数据要素引爆", "落地雄安；数据确权/DRG-DIP领涨；金融街论坛：北证50ETF推进+市值配售改革"),
    ("宁", "#f6465d", "宁德时代暴跌12%：增收不增利+评级下调", "Q3净利212.46亿(+14.54%)远低于营收(+58.58%)；摩根大通H股目标价725→500港元；出口退税13%→9%"),
    ("芯", "#f6465d", "美制裁DeepSeek等5家中企，国产模型密集迭代", "商务部回应；DeepSeek开源DeepInfer+V4.1 Flash；智谱/阶跃迭代；ASIC芯片+2.54%逆势吸金"),
    ("资", "#f5c542", "ETF放量托底：创业板ETF成交破百亿", "10-21创业板ETF易方达成交破100亿；首批18只主动ETF 10-23开售（近360亿）"),
]
review = [
    ("上证指数", "预测 高开震荡·量能定高度 · 3725~3775", "3735.37", "▲0.12%", True),
    ("创业板指", "预测 高开修复·存储链领涨 · 2720~2770", "2739.20", "▼0.26%", True),
    ("恒生指数", "预测 平开震荡·修复反弹 · 24050~24400", "23867.74", "▼1.32%", False),
    ("恒生科技", "预测 探底回升·修复非反转 · 4070~4150", "4045.91", "▼1.52%", False),
]
forecasts = [
    ("上证指数", "低开震荡·拉锯整理", 3688, 3723, "-0.9%~+0.5%", 3713.03, "3700/3680", "3735~3750", True),
    ("创业板指", "低开探底·企稳修复", 2680, 2706, "-1.1%~+0.4%", 2694.71, "2660/2650", "2720~2740", False),
    ("恒生指数", "低开震荡·弱势整理", 23540, 23770, "-0.7%~+0.8%", 23651.87, "23400~23500", "23850~24000", False),
    ("恒生科技", "低开探底·弱势拉锯", 3976, 4013, "-0.7%~+0.7%", 3994.77, "3950~3970", "4035~4060", False),
]

# ---------- 各屏 ----------
screens = []

screens.append('''
<section class="screen cover">
  <div class="cover-top">
    <span class="badge">AI 每日市场速览</span>
    <span class="badge dim-badge">周三 · VOL.021</span>
  </div>
  <div class="cover-mid">
    <div class="cover-date">10.21</div>
    <div class="cover-title">每日行情速览</div>
    <div class="cover-sub">10·21 A股/港股收盘复盘　×　美股10·20　×　明日盘面前瞻<br>A股 · 港股 · 大盘 / 板块 / 个股 · 观点记录</div>
  </div>
  <div class="cover-chips">
    <div class="cchip"><div class="cc-m">上证指数</div><div class="cc-v">3713.03</div><div class="cc-c down">▼0.60%</div></div>
    <div class="cchip"><div class="cc-m">恒生指数</div><div class="cc-v">23651.87</div><div class="cc-c down">▼0.90%</div></div>
    <div class="cchip"><div class="cc-m">纳斯达克</div><div class="cc-v">26424.82</div><div class="cc-c down">▼0.02%</div></div>
  </div>
  <div class="cover-hint"><span class="hint-arrow">↑</span> 上滑 · 开启今日速览</div>
  <div class="cover-note">数据截至 10-21 收盘 · 美股为美东 10-20</div>
</section>''')

screens.append(f'''
<section class="screen">
  <div class="hd"><div class="kicker">RECAP · 10月21日 收盘</div><h1>缩量分化，电池链雪崩</h1></div>
  <div class="card">
    <div class="card-t">主要指数涨跌幅（10-21 收盘 · 美股为美东 10-20）</div>
    {diverging_chart(idx_rows, 1.7, row_h=24)}
  </div>
  <div class="stat-strip">
    <div class="stat"><div class="stat-v">1.44万亿</div><div class="stat-l">沪深北成交 · 较上日缩量</div></div>
    <div class="stat"><div class="stat-v">1981:3364</div><div class="stat-l">上涨:下跌 · 约50家涨停</div></div>
    <div class="stat"><div class="stat-v">-87.8亿</div><div class="stat-l">主力资金净流出</div></div>
  </div>
  <div class="note">沪指<span class="down">▼0.60%</span>失守3730：宁德时代<span class="down">-12.03%</span>砸塌电池链、电信运营商<span class="down">-4.15%</span>领跌；科创50<span class="up">▲0.06%</span>逆势翻红、ASIC芯片<span class="up">+2.54%</span>、数据确权/DRG领涨；创业板ETF易方达尾盘放量破百亿；隔夜道指<span class="up">▲1.02%</span>独涨、纳指<span class="down">▼0.02%</span></div>
</section>''')

screens.append(f'''
<section class="screen">
  <div class="hd"><div class="kicker">SECTORS · 板块结构（10-21）</div><h1>芯片吸金，电池崩塌</h1></div>
  <div class="card two-col">
    <div class="tc">
      <div class="tc-t up-t">领涨 · 政策+硬科技</div>
      <div class="tc-r"><span>DRG/DIP(医保)</span><b class="up">近+3%</b></div>
      <div class="tc-r"><span>ASIC芯片</span><b class="up">+2.54%</b></div>
      <div class="tc-r"><span>数据确权</span><b class="up">主线爆发</b></div>
      <div class="tc-r"><span>养殖/猪肉</span><b class="up">涨幅居前</b></div>
    </div>
    <div class="tc">
      <div class="tc-t down-t">领跌 · 事件冲击</div>
      <div class="tc-r"><span>宁德时代</span><b class="down">-12.03%</b></div>
      <div class="tc-r"><span>电信运营商</span><b class="down">-4.15%</b></div>
      <div class="tc-r"><span>锂电池</span><b class="down">-3.75%</b></div>
      <div class="tc-r"><span>中国移动</span><b class="down">-5.09%</b></div>
    </div>
  </div>
  <div class="card">
    <div class="card-t">行业与概念结构</div>
    <div class="tc-r"><span>领涨概念</span><b>DRG/DIP · 数据确权 · 短剧游戏 · AI营销 · 激光通信</b></div>
    <div class="tc-r"><span>领跌概念</span><b>固态电池 · 钠电池 · 六氟磷酸锂 · 电池回收 · 能源金属</b></div>
    <div class="tc-r"><span>个股流出前三</span><b>宁德时代 -13.1亿 · 新易盛 -8.1亿 · 阳光电源 -6.9亿</b></div>
  </div>
  <div class="stat-strip">
    <div class="stat"><div class="stat-v">约50 / 5</div><div class="stat-l">涨停 / 跌停</div></div>
    <div class="stat"><div class="stat-v">+112.8亿</div><div class="stat-l">小单净流入 · 大单撤退</div></div>
    <div class="stat"><div class="stat-v">324亿</div><div class="stat-l">宁德时代成交居首</div></div>
  </div>
  <div class="note">宁德时代Q3“增收不增利”（净利+14.54% vs 营收+58.58%）+摩根大通下调H股目标价+出口退税13%→9%集中引爆；资金“弃旧迎新”——从高位拥挤的电池链腾挪至数据要素与国产芯片</div>
</section>''')

review_cards = ""
for name, pred, close, chg, ok in review:
    if ok is True:
        badge = '<span class="pill ok">✓ 准确</span>'
    elif ok is False:
        badge = '<span class="pill bad">✗ 不准确</span>'
    else:
        badge = '<span class="pill" style="color:#f5c542;background:rgba(245,197,66,.12)">◌ 今晚验证</span>'
    cls = "down" if chg.startswith("▼") else "up"
    review_cards += (
        '<div class="rv"><div class="rv-hd"><span class="rv-name">%s</span>%s</div>'
        '<div class="rv-pred">%s</div><div class="rv-act">%s <span class="%s">%s</span></div></div>'
        % (name, badge, pred, close, cls, chg)
    )
chips = ('<span class="chipv ok">上证 ✓</span><span class="chipv ok">创业板 ✓</span>'
         '<span class="chipv bad">恒指 ✗</span>'
         '<span class="chipv bad">恒科 ✗</span>'
         '<span class="chipv part">板块 ◐</span><span class="chipv part">个股 ◐</span>')

screens.append(f'''
<section class="screen">
  <div class="hd"><div class="kicker">REVIEW · 昨日预测复盘（10-20 A股 / 港股）</div><h1>A股兑现，港股误判</h1></div>
  <div class="donut-row">
    <div class="donut-box">{donut(70.8)}</div>
    <div class="donut-side">
      <div class="ds-t">累计综合判定</div>
      <div class="ds-v">17/24项 · 70.8%</div>
      <div class="chipv-row">{chips}</div>
    </div>
  </div>
  <div class="rv-grid">{review_cards}</div>
  <div class="note">10-20版预测验证：上证3735.37(+0.12%)、创业板2739.20(-0.26%)双双落在预测区间内；恒指23867.74(-1.32%)、恒科4045.91(-1.52%)双双跌破区间下限——连续两版误判港股修复力度，盲区在低估南向连续净卖出与锂电/大模型高位股独立杀跌的压制</div>
</section>''')

news_cards = ""
for tag, col, t, sub in news:
    news_cards += (
        '<div class="ncard"><div class="nicon" style="background:%s22;border-color:%s66;color:%s">%s</div>'
        '<div class="nbody"><div class="nt">%s</div><div class="ns">%s</div></div></div>'
        % (col, col, col, tag, t, sub)
    )
screens.append(f'''
<section class="screen">
  <div class="hd"><div class="kicker">NEWS · 消息面（10-20 ~ 10-21）</div><h1>五条关键消息</h1></div>
  <div class="news-list">{news_cards}</div>
  <div class="note">其他：道指+1.02%独涨、3M+5.78%领涨、SpaceX盘后涨超6%（Q3营收超预期）；美伊“七日计划”谈判反复、布油109美元高位；今夜特斯拉+Meta财报为AI资本开支“压力测试”；Anthropic半年营收163亿美元/亏807亿；通用汽车200亿回购</div>
</section>''')

fc_cards = "".join(range_card(*f) for f in forecasts)
screens.append(f'''
<section class="screen">
  <div class="hd"><div class="kicker">FORECAST · 明日（10-22 A股 / 港股）</div><h1>低开拉锯，轻指数重结构</h1></div>
  {fc_cards}
  <div class="sec-block">
    <div class="sb-row"><span class="sb-t">A股占优</span><span class="chips-in">数据要素 · 国产AI链 · AI应用 · 激光通信 · 红利 · 养殖</span></div>
    <div class="sb-row"><span class="sb-t">A股承压</span><span class="chips-in dim-in">电池链 · 电信运营商 · AI高位股 · 煤炭酿酒</span></div>
    <div class="sb-row"><span class="sb-t">港股</span><span class="chips-in">占优：联想 · 创新药 · 高股息 · 光通信</span><span class="chips-in dim-in">｜承压：电池 · 科网权重 · 算力概念</span></div>
  </div>
</section>''')


def stock_group(title, watch, avoid):
    w = "".join('<span class="stk w">%s<i>%s</i></span>' % (n, c) for n, c in watch)
    a = "".join('<span class="stk a">%s<i>%s</i></span>' % (n, c) for n, c in avoid)
    return (
        '<div class="card gcard"><div class="g-t">%s</div>'
        '<div class="g-row"><span class="g-lab w-t">★ 关注</span><div class="g-stks">%s</div></div>'
        '<div class="g-row"><span class="g-lab a-t">× 回避</span><div class="g-stks">%s</div></div></div>'
        % (title, w, a)
    )


screens.append(f'''
<section class="screen">
  <div class="hd"><div class="kicker">STOCKS · 个股线索（仅港股与A股）</div><h1>关注与回避名单</h1></div>
  {stock_group("港股", [("联想集团", "00992·财报超预期"), ("长飞光纤", "06869·净买2.5亿"), ("中国海洋石油", "00883·净买1.7亿"), ("百济神州", "06160·+2.66%")],
                [("宁德时代", "03750·-11.4%"), ("中国移动", "00941·A/H双杀"), ("泡泡玛特", "09992·-4.8%"), ("福耀玻璃", "03606·特斯拉链")])}
  {stock_group("上证（主板）", [("数据要素", "政策主线"), ("亨通光电", "600487·激光通信"), ("长飞光纤", "601869·光通信"), ("工商银行", "601398·红利防御")],
                [("中国移动", "600941·-5.09%"), ("煤炭酿酒", "今日领跌"), ("新易盛", "300502·流出8亿"), ("电池链联动", "宁德事件")])}
  {stock_group("创业板", [("ASIC芯片", "+2.54%逆势"), ("利亚德", "300296·观察"), ("激光通信", "MCP/电子布"), ("创业板ETF", "成交破百亿")],
                [("宁德时代", "300750·-12.03%"), ("固态电池", "钠电/六氟"), ("新易盛", "300502"), ("阳光电源", "300274·流出6.9亿")])}
  <div class="note">今日调整是结构性而非系统性——指数跌幅有限但电池链单点爆破，科创50逆势翻红+ETF放量承接显示资金“弃旧迎新”；明日看宁德止跌信号、早盘量能与今夜特斯拉/Meta财报</div>
</section>''')

screens.append('''
<section class="screen end">
  <div class="end-mid">
    <div class="end-big">下一个交易日<br>再见</div>
    <div class="end-sub">每日行情汇报系列 · 次日开盘前复盘验证</div>
  </div>
  <div class="disc">
    <div class="disc-t">⚠ 免责声明</div>
    <div class="disc-b">本页面由 <b>AI 自动生成</b>，所有信息整理自公开渠道，仅供信息参考，<b>不构成投资建议</b>。市场有风险，投资需谨慎，决策请独立判断。</div>
  </div>
  <div class="end-src">数据来源：新华财经 · 中财网 · 同花顺 · 东方财富 · 证券时报 · 新华社 · 财联社 · 金投网 等公开报道<br>生成时间：2026-10-21 晚间（周三版）</div>
</section>''')

dots = "".join('<i class="dot" data-i="%d"></i>' % i for i in range(len(screens)))

CSS = '''
:root{--vh:1vh;--up:#f6465d;--down:#0ecb81;--gold:#f5c542;--tx:#eef1f8;--dim:#aab3c6;--card:rgba(255,255,255,.055);--line:rgba(255,255,255,.09);}
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{height:100%;overflow:hidden}
body{background:#070a14;color:var(--tx);font-family:'Noto Sans CJK SC','PingFang SC','Microsoft YaHei',sans-serif;font-variant-numeric:tabular-nums}
.reel{height:100dvh;height:calc(var(--vh)*100);overflow-y:scroll;scroll-snap-type:y mandatory;overscroll-behavior:none;scrollbar-width:none}
.reel::-webkit-scrollbar{display:none}
.screen{position:relative;height:calc(var(--vh)*100);min-height:560px;scroll-snap-align:start;scroll-snap-stop:always;overflow:hidden;padding:20px 44px 22px 26px;display:flex;flex-direction:column}
.cover{background:radial-gradient(900px 620px at 85% -8%,#232c63 0%,#0c1128 52%,#070a14 100%)}
.screen:not(.cover):not(.end){background:linear-gradient(180deg,#0d1327 0%,#080b16 100%)}
.end{background:radial-gradient(800px 600px at 50% 110%,#2a2350 0%,#0b0e20 55%,#070a14 100%)}
.screen::before{content:"";position:absolute;top:0;left:26px;right:44px;height:1px;background:linear-gradient(90deg,transparent,rgba(245,197,66,.35),transparent)}
.cover::before,.end::before{display:none}
.hd{margin-bottom:14px}
.kicker{font-size:10.5px;font-weight:700;letter-spacing:2.5px;color:var(--gold);opacity:.9}
h1{font-size:23px;font-weight:900;margin-top:5px;letter-spacing:.3px}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:13px 14px;margin-bottom:12px}
.card-t{font-size:12px;font-weight:700;color:var(--dim);margin-bottom:8px;letter-spacing:.5px}
.note{font-size:11px;line-height:1.55;color:var(--dim);margin-top:auto;padding-top:10px;border-top:1px dashed rgba(255,255,255,.10)}
.up{color:var(--up)}.down{color:var(--down)}
.cover-top{display:flex;justify-content:space-between;align-items:center}
.badge{font-size:10.5px;font-weight:700;letter-spacing:1.5px;color:#0a0d1a;background:var(--gold);padding:5px 10px;border-radius:20px}
.dim-badge{background:rgba(255,255,255,.10);color:var(--dim)}
.cover-mid{flex:1;display:flex;flex-direction:column;justify-content:center}
.cover-date{font-size:96px;font-weight:900;line-height:1;background:linear-gradient(135deg,#fff 20%,#f5c542 90%);-webkit-background-clip:text;background-clip:text;color:transparent;letter-spacing:-2px}
.cover-title{font-size:30px;font-weight:900;margin-top:10px;letter-spacing:6px}
.cover-sub{font-size:12.5px;color:var(--dim);margin-top:12px;line-height:1.6}
.cover-chips{display:flex;gap:9px}
.cchip{flex:1;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:11px 10px;text-align:center}
.cc-m{font-size:10.5px;color:var(--dim)}
.cc-v{font-size:15.5px;font-weight:900;margin-top:3px}
.cc-c{font-size:12px;font-weight:700;margin-top:2px}
.cover-hint{margin-top:20px;text-align:center;font-size:12px;color:var(--gold);font-weight:700;letter-spacing:1px}
.hint-arrow{display:inline-block;animation:bounce 1.4s infinite}
@keyframes bounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}
.cover-note{text-align:center;font-size:10px;color:rgba(255,255,255,.35);margin-top:8px}
.stat-strip{display:flex;gap:9px;margin-bottom:12px}
.stat{flex:1;background:rgba(255,255,255,.04);border:1px solid var(--line);border-radius:13px;padding:10px 8px;text-align:center}
.stat-v{font-size:16px;font-weight:900}
.stat-l{font-size:9.5px;color:var(--dim);margin-top:3px;line-height:1.35}
.two-col{display:flex;gap:12px}
.tc{flex:1}
.tc-t{font-size:11.5px;font-weight:900;margin-bottom:8px}
.up-t{color:var(--up)}.down-t{color:var(--down)}
.tc-r{display:flex;justify-content:space-between;font-size:12px;padding:5.5px 0;border-bottom:1px solid rgba(255,255,255,.05)}
.tc-r:last-child{border-bottom:none}
.tc-r b{font-weight:900}
.donut-row{display:flex;align-items:center;gap:16px;margin-bottom:13px}
.donut-box{filter:drop-shadow(0 0 18px rgba(245,197,66,.25))}
.ds-t{font-size:11px;color:var(--dim);letter-spacing:1px}
.ds-v{font-size:19px;font-weight:900;margin:5px 0 10px}
.chipv-row{display:flex;flex-wrap:wrap;gap:6px}
.chipv{font-size:10.5px;font-weight:700;padding:4px 8px;border-radius:8px}
.chipv.ok{color:var(--down);background:rgba(14,203,129,.12);border:1px solid rgba(14,203,129,.35)}
.chipv.part{color:var(--gold);background:rgba(245,197,66,.10);border:1px solid rgba(245,197,66,.35)}
.chipv.bad{color:#8a94ac;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.18)}
.rv-grid{display:grid;grid-template-columns:1fr 1fr;gap:9px}
.rv{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:10px 11px}
.rv-hd{display:flex;justify-content:space-between;align-items:center}
.rv-name{font-size:13px;font-weight:900}
.pill{font-size:9.5px;font-weight:700;padding:3px 7px;border-radius:7px}
.pill.ok{color:var(--down);background:rgba(14,203,129,.13)}
.pill.part{color:var(--gold);background:rgba(245,197,66,.12)}
.pill.bad{color:#8a94ac;background:rgba(255,255,255,.08)}
.rv-pred{font-size:10px;color:var(--dim);margin-top:6px;line-height:1.4}
.rv-act{font-size:15px;font-weight:900;margin-top:5px}
.rv-act span{font-size:12px}
.news-list{display:flex;flex-direction:column;gap:9px}
.ncard{display:flex;gap:12px;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:15px;padding:12px 14px}
.nicon{width:40px;height:40px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:900;border:1px solid;flex:none}
.nt{font-size:14px;font-weight:900}
.ns{font-size:10.5px;color:var(--dim);margin-top:4px;line-height:1.5}
.rcard{background:var(--card);border:1px solid var(--line);border-radius:15px;padding:10px 14px 6px;margin-bottom:6px}
.rc-hd{display:flex;align-items:baseline;gap:6px}
.rc-name{font-size:14.5px;font-weight:900}
.rc-tag{font-size:10px;color:var(--gold);font-weight:700;background:rgba(245,197,66,.10);padding:3px 7px;border-radius:7px}
.rc-close{margin-left:auto;font-size:10.5px;color:var(--dim);white-space:nowrap}
.rc-close b{color:var(--gold);font-weight:900;font-size:11px}
.rc-ft{font-size:10px;color:var(--dim);margin-top:2px}
.rc-ft b{color:rgba(255,255,255,.75);font-weight:700}
.rc-ft .act{color:var(--gold);font-weight:700}
.sec-block{margin-top:auto;padding-top:6px}
.sb-row{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:6.5px 0;border-bottom:1px solid rgba(255,255,255,.05)}
.sb-t{font-size:11px;font-weight:900;color:var(--gold);width:58px;flex:none}
.chips-in{font-size:11px;font-weight:700}
.dim-in{color:var(--dim);font-weight:400}
.gcard{margin-bottom:6px}
.g-t{font-size:13px;font-weight:900;margin-bottom:6px;color:var(--gold)}
.g-row{display:flex;gap:8px;margin-top:4px}
.g-lab{font-size:10.5px;font-weight:900;width:44px;flex:none;padding-top:4px}
.w-t{color:var(--up)}.a-t{color:var(--down)}
.g-stks{display:flex;flex-wrap:wrap;gap:5px}
.stk{font-size:10.5px;padding:3px 7px;border-radius:8px;line-height:1.2}
.stk i{font-style:normal;font-size:8.5px;color:var(--dim);margin-left:3px}
.stk.w{background:rgba(246,70,93,.12);border:1px solid rgba(246,70,93,.30)}
.stk.a{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12);color:var(--dim)}
.end-mid{flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center}
.end-big{font-size:38px;font-weight:900;line-height:1.35;letter-spacing:3px;background:linear-gradient(135deg,#fff 30%,#f5c542 95%);-webkit-background-clip:text;background-clip:text;color:transparent}
.end-sub{font-size:11.5px;color:var(--dim);margin-top:14px;letter-spacing:1px}
.disc{border:1px solid rgba(245,197,66,.45);background:rgba(245,197,66,.07);border-radius:15px;padding:14px 15px}
.disc-t{font-size:13px;font-weight:900;color:var(--gold);margin-bottom:6px}
.disc-b{font-size:11px;line-height:1.7;color:rgba(255,255,255,.82)}
.end-src{text-align:center;font-size:9px;line-height:1.6;color:rgba(255,255,255,.35);margin-top:12px}
.dots{position:fixed;right:9px;top:50%;transform:translateY(-50%);display:flex;flex-direction:column;gap:7px;z-index:10}
.dot{width:5px;height:5px;border-radius:3px;background:rgba(255,255,255,.28);transition:all .25s}
.dot.on{height:16px;background:var(--gold)}
'''

JS = '''
(function(){
  var setVh=function(){document.documentElement.style.setProperty('--vh',(window.innerHeight/100)+'px');};
  setVh();window.addEventListener('resize',setVh);window.addEventListener('orientationchange',setVh);
  var reel=document.getElementById('reel');
  var secs=Array.prototype.slice.call(reel.querySelectorAll('.screen'));
  var dots=Array.prototype.slice.call(document.querySelectorAll('.dot'));
  function setActive(i){dots.forEach(function(d,j){d.classList.toggle('on',j===i);});}
  if('IntersectionObserver' in window){
    var io=new IntersectionObserver(function(es){
      es.forEach(function(e){if(e.isIntersecting){setActive(secs.indexOf(e.target));}});
    },{root:reel,threshold:0.55});
    secs.forEach(function(s){io.observe(s);});
  }
  setActive(0);
})();
'''

html = (
    '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    '<meta name="theme-color" content="#070a14">\n'
    '<title>每日行情速览 · 2026-10-21</title>\n<style>' + CSS + '</style>\n</head>\n<body>\n'
    '<div class="reel" id="reel">' + "".join(screens) + '</div>\n'
    '<nav class="dots" id="dots">' + dots + '</nav>\n'
    '<script>' + JS + '</script>\n</body>\n</html>'
)

out = sys.argv[1] if len(sys.argv) > 1 else "./output.html"  # 用法: python3 gen_html.py [输出.html]
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("written", out, len(html), "bytes, screens:", len(screens))

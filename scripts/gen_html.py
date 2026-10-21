# -*- coding: utf-8 -*-
"""生成 2026-10-20 手机竖屏（抖音可刷）HTML 行情速览。
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


# ---------- 数据（均已核实，10-19 收盘 / 隔夜消息） ----------
idx_rows = [
    ("上证指数", 0.39), ("深证成指", 0.13), ("创业板指", -0.94), ("科创50", -2.17),
    ("沪深300", 0.09), ("中证500", 0.41), ("北证50", -0.41), ("恒生指数", 0.52),
    ("恒生科技", 1.16), ("道琼斯", -0.07), ("标普500", 0.41), ("纳斯达克", 1.11),
]
news = [
    ("GDP", "#0ecb81", "前三季度GDP+4.6%，Q3回升至4.5%", "GDP总量107.11万亿；规上工业增加值+5.3%；工业机器人产量+29.1%、3D打印+62.5%；70城新房环比涨价城市增至17个"),
    ("坛", "#f5c542", "金融街论坛：央行五项安排落地", "设立非银机构大额赎回流动性支持工具、SLF扩容、债市互联互通、退出存贷款基准利率方向已定；证监会六方面部署；首批18只主动ETF获批近360亿"),
    ("行", "#0ecb81", "工行/建行创历史新高，机器人午后爆发", "工行3.07万亿重夺A股市值第一、建行3.03万亿；21家银行中期分红超2600亿；宇树科技+16.15%创上市以来最大单日涨幅、十余股涨停"),
    ("芯", "#f6465d", "隔夜费半终结八连跌、存储暴涨", "纳指+1.11%、费半+1.61%；西数+6.09%/闪迪+5.53%/美光+2.97%；10Y美债+7.5bp至5.148%；WTI+2.22%报103.66美元"),
    ("险", "#f6465d", "今日解禁高峰+情绪退潮信号", "颀中科技解禁69.23%约108.74亿、本周合计952.83亿（明日单日643.84亿）；新华传媒11连板终结、连板高度降至三板、封板率68.7%"),
]
review = [
    ("上证指数", "预测 企稳偏强 · 3690~3745", "3730.92", "▲0.39%", True),
    ("创业板指", "预测 探底企稳 · 2730~2780", "2746.29", "▼0.94%", True),
    ("恒生指数", "预测 低开回踩·关口防守 · 24050~24400", "今晚验证", "10-20今日", None),
    ("恒生科技", "预测 探底企稳·修复非反转 · 4070~4150", "今晚验证", "10-20今日", None),
]
forecasts = [
    ("上证指数", "高开震荡·量能定高度", 3725, 3775, "-0.5%~+1.0%", 3730.92, "3715/3700", "3750~3770", True),
    ("创业板指", "高开修复·存储链领涨", 2720, 2770, "-0.9%~+0.6%", 2746.29, "2720/2730", "2785~2800", True),
    ("恒生指数", "平开低走·震荡修复", 24050, 24400, "-1.0%~+0.5%", 24186.83, "24000~24100", "24350~24500", True),
    ("恒生科技", "探底回升·修复非反转", 4070, 4150, "-1.0%~+0.5%", 4108.24, "4040~4060", "4160~4180", True),
]

# ---------- 各屏 ----------
screens = []

screens.append('''
<section class="screen cover">
  <div class="cover-top">
    <span class="badge">AI 每日市场速览</span>
    <span class="badge dim-badge">周二 · VOL.020</span>
  </div>
  <div class="cover-mid">
    <div class="cover-date">10.20</div>
    <div class="cover-title">每日行情速览</div>
    <div class="cover-sub">上一开盘日 10·19 A股复盘　×　美股10·19　×　今日盘前前瞻<br>A股 · 港股 · 大盘 / 板块 / 个股 · 晨间观点记录</div>
  </div>
  <div class="cover-chips">
    <div class="cchip"><div class="cc-m">上证指数</div><div class="cc-v">3730.92</div><div class="cc-c up">▲0.39%</div></div>
    <div class="cchip"><div class="cc-m">恒生指数</div><div class="cc-v">24186.83</div><div class="cc-c up">▲0.52%</div></div>
    <div class="cchip"><div class="cc-m">纳斯达克</div><div class="cc-v">26430.89</div><div class="cc-c up">▲1.11%</div></div>
  </div>
  <div class="cover-hint"><span class="hint-arrow">↑</span> 上滑 · 开启今日速览</div>
  <div class="cover-note">数据截至 10-19 收盘 · 美股为美东 10-19 · 港股为 10-16 收盘</div>
</section>''')

screens.append(f'''
<section class="screen">
  <div class="hd"><div class="kicker">RECAP · 上一开盘日 10月19日</div><h1>低开高走，银行创新高</h1></div>
  <div class="card">
    <div class="card-t">主要指数涨跌幅（10-19 收盘 · 港股为10-16）</div>
    {diverging_chart(idx_rows, 2.2, row_h=24)}
  </div>
  <div class="stat-strip">
    <div class="stat"><div class="stat-v">1.44万亿</div><div class="stat-l">沪深成交 · 缩量1179亿</div></div>
    <div class="stat"><div class="stat-v">2270:3126</div><div class="stat-l">上涨:下跌 · 约50家涨停</div></div>
    <div class="stat"><div class="stat-v">-116亿</div><div class="stat-l">主力资金净卖出</div></div>
  </div>
  <div class="note">沪指<span class="up">▲0.39%</span>站上3730：工行/建行创历史新高、机器人午后爆发、军工+2.99%；科创50<span class="down">▼2.17%</span>补跌、长鑫-7.77%；GDP+4.6%落地+金融街论坛央行五项安排；隔夜纳指<span class="up">▲1.11%</span>、费半终结八连跌</div>
</section>''')

screens.append(f'''
<section class="screen">
  <div class="hd"><div class="kicker">SECTORS · 板块结构（10-19）</div><h1>银行搭台，机器人接棒</h1></div>
  <div class="card two-col">
    <div class="tc">
      <div class="tc-t up-t">领涨 · 权重+事件</div>
      <div class="tc-r"><span>国防军工(申万)</span><b class="up">+2.99%</b></div>
      <div class="tc-r"><span>宇树科技</span><b class="up">+16.15%</b></div>
      <div class="tc-r"><span>银行(工行/建行)</span><b class="up">历史新高</b></div>
      <div class="tc-r"><span>四会富仕(PCB)</span><b class="up">20cm涨停</b></div>
    </div>
    <div class="tc">
      <div class="tc-t down-t">领跌 · 成长退潮</div>
      <div class="tc-r"><span>半导体(概念)</span><b class="down">-2.07%</b></div>
      <div class="tc-r"><span>长鑫科技</span><b class="down">-7.77%</b></div>
      <div class="tc-r"><span>金健米业</span><b class="down">-9.99%</b></div>
      <div class="tc-r"><span>宁德时代</span><b class="down">-3.60%</b></div>
    </div>
  </div>
  <div class="card">
    <div class="card-t">行业与概念结构</div>
    <div class="tc-r"><span>领涨行业</span><b>国防军工 · 家用电器 · 银行 · 煤炭 · 石化</b></div>
    <div class="tc-r"><span>领跌行业</span><b>房地产 · 综合 · 农林牧渔 · 电子 · 社服</b></div>
    <div class="tc-r"><span>领跌概念</span><b>种业 · 乳业 · 粮食 · CRO · 半导体 · 电池</b></div>
  </div>
  <div class="stat-strip">
    <div class="stat"><div class="stat-v">约50 / 25</div><div class="stat-l">涨停 / 跌停</div></div>
    <div class="stat"><div class="stat-v">-0.38%</div><div class="stat-l">涨跌中位数 · 个股跌多涨少</div></div>
    <div class="stat"><div class="stat-v">19.33亿</div><div class="stat-l">亨通光电净流入居首</div></div>
  </div>
  <div class="note">银行创新高是“防守定价”、机器人是“超跌+国标+产量+29.1%”的事件驱动；主力净卖出116亿、电子净流出27.66亿——存量博弈下热点轮动加快，追高容错率低</div>
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
         '<span class="chipv" style="color:#f5c542;background:rgba(245,197,66,.10);border:1px solid rgba(245,197,66,.35)">恒指 ◌今晚</span>'
         '<span class="chipv" style="color:#f5c542;background:rgba(245,197,66,.10);border:1px solid rgba(245,197,66,.35)">恒科 ◌今晚</span>'
         '<span class="chipv ok">板块 ✓</span><span class="chipv part">个股 ◐</span>')

screens.append(f'''
<section class="screen">
  <div class="hd"><div class="kicker">REVIEW · 昨日预测复盘（A股 10-19）</div><h1>大盘A股两项兑现</h1></div>
  <div class="donut-row">
    <div class="donut-box">{donut(87.5)}</div>
    <div class="donut-side">
      <div class="ds-t">累计综合判定</div>
      <div class="ds-v">14/16项 · 87.5%</div>
      <div class="chipv-row">{chips}</div>
    </div>
  </div>
  <div class="rv-grid">{review_cards}</div>
  <div class="note">10-17/18/19三版同对象预测验证：上证3730.92(+0.39%)落在3690~3745、创业板2746.29(-0.94%)探底企稳落在2730~2780，方向/区间/幅度全兑现；板块多数兑现（军工/银行/涨价链占优、半导体/存储/CRO/农业承压），偏差为人形机器人新主线未预见+德明利+6.40%逆势反弹；恒指/恒科今晚收盘后回填</div>
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
  <div class="hd"><div class="kicker">NEWS · 消息面（10-19 全天 ~ 10-20 早间）</div><h1>五条关键消息</h1></div>
  <div class="news-list">{news_cards}</div>
  <div class="note">其他：首批18只主动管理型ETF获批（近360亿）；亨通光电三季报预增150%+、生益科技预增160%+；商务部对无人机/盾构机出口管制；珠海航展门票开售（12-7~13）；今日9:00 LPR+英伟达GTC柏林+APEC财长会香港+宁德/移动三季报</div>
</section>''')

fc_cards = "".join(range_card(*f) for f in forecasts)
screens.append(f'''
<section class="screen">
  <div class="hd"><div class="kicker">FORECAST · 今日（10-20 A股 / 港股）</div><h1>高开修复，量能定高度</h1></div>
  {fc_cards}
  <div class="sec-block">
    <div class="sb-row"><span class="sb-t">A股占优</span><span class="chips-in">存储 · 机器人 · PCB · 券商 · 银行 · 涨价链</span></div>
    <div class="sb-row"><span class="sb-t">A股承压</span><span class="chips-in dim-in">农业 · 地产 · CRO · AI高位股 · 解禁股</span></div>
    <div class="sb-row"><span class="sb-t">港股</span><span class="chips-in">占优：存储 · 高股息 · 创新药 · 预增龙头</span><span class="chips-in dim-in">｜承压：算力 · 能源 · 保险 · CRO</span></div>
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
  {stock_group("港股", [("宁德时代", "03750·财报"), ("中国移动", "00941·财报"), ("腾讯", "00700"), ("中芯国际", "00981·存储")],
                [("联想集团", "00992·勿追"), ("赣锋锂业", "01772"), ("药明生物", "02269"), ("中国海洋石油", "00883·油价")])}
  {stock_group("上证（主板）", [("工商银行", "601398·新高"), ("建设银行", "601939·新高"), ("亨通光电", "600487·流入19亿"), ("生益科技", "600183·预增160%")],
                [("长鑫科技", "688825·卖出12亿"), ("新华传媒", "600825·连板终"), ("招商南油", "601975"), ("颀中科技", "688352·解禁69%")])}
  {stock_group("创业板", [("佰维存储", "688525·存储"), ("兆威机电", "003021·机器人"), ("四会富仕", "300852·PCB"), ("澜起科技", "688008·回调")],
                [("新易盛", "300502"), ("中际旭创", "300308"), ("天孚通信", "300394"), ("胜宏科技", "300476")])}
  <div class="note">隔夜存储暴涨直接映射A股存储链，科创50（-2.17%）系被错杀、今日有修复动能；“易中天”本周主力净流出百亿+Meta/特斯拉10-21财报周，AI硬件以“修复非反转”对待</div>
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
  <div class="end-src">数据来源：新华财经 · 金融界 · 中证指数公司 · 证券时报 · 澎湃新闻 · 财联社 · 环球市场播报 · 同花顺 · 东方财富 等公开报道<br>生成时间：2026-10-20 早间（周二版）</div>
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
    '<title>每日行情速览 · 2026-10-20</title>\n<style>' + CSS + '</style>\n</head>\n<body>\n'
    '<div class="reel" id="reel">' + "".join(screens) + '</div>\n'
    '<nav class="dots" id="dots">' + dots + '</nav>\n'
    '<script>' + JS + '</script>\n</body>\n</html>'
)

out = sys.argv[1] if len(sys.argv) > 1 else "./output.html"  # 用法: python3 gen_html.py [输出.html]
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("written", out, len(html), "bytes, screens:", len(screens))

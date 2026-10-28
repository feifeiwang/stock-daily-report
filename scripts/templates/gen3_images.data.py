# =============================================================================
# 2026-10-26 快照（即日常模板）：每日只改这个 D 字典 + 下面"占位符替换"表
# 图 1 = 上一开盘日复盘；图 2 = 昨日要闻；图 3 = 今日开盘预测
# 语义说明见 DATA-SCHEMA.md；CSS / track() / donut() / main() 禁改。
# =============================================================================
D = {
  "date": "{{DATE}}",   # 决定中间文件名 {date}_1/2/3.png；归档前由 to_jpg.py 转为 JPG
  # ---------- 图1：上一开盘日预测复盘 ----------
  "s1": {
    "d": "{{PREV_MD}}",                              # 上一开盘日，如 10·23
    "sub": "上一开盘日 · {{PREV_DATE_WEEK}}",        # 如 2026-10-23 周五（中性措辞，禁写休市/首开）
    "badge": "累计准确率 {{ACC_PCT}}%",
    "pct": {{ACC_PCT}},                              # 数字，用于圆环，如 52.8
    "big": "{{ACC_SCORE}}", "big_note": "六项制累计得分",   # 如 19 / 36
    "sub2": "{{REV_SUMMARY_LINE1}}<br>{{REV_SUMMARY_LINE2}}",
    "sec1": "开盘预测 / 收盘预测 vs 实际",
    # (名称, 实际收盘span, 标签类, 标签文字, 说明)；标签类 tag-ok / tag-half / tag-bad
    "rev": [
      ("上证指数", '{{SZ_ACT_SPAN}}', '{{SZ_TAG}}', '{{SZ_TAG_TXT}}',
       "预测：<b>{{SZ_PREV_PRED}}</b> · {{SZ_REV_NOTE}}"),
      ("创业板指", '{{CYB_ACT_SPAN}}', '{{CYB_TAG}}', '{{CYB_TAG_TXT}}',
       "预测：<b>{{CYB_PREV_PRED}}</b> · {{CYB_REV_NOTE}}"),
      ("恒生指数", '{{HSI_ACT_SPAN}}', '{{HSI_TAG}}', '{{HSI_TAG_TXT}}',
       "预测：<b>{{HSI_PREV_PRED}}</b> · {{HSI_REV_NOTE}}"),
      ("恒生科技", '{{HSTECH_ACT_SPAN}}', '{{HSTECH_TAG}}', '{{HSTECH_TAG_TXT}}',
       "预测：<b>{{HSTECH_PREV_PRED}}</b> · {{HSTECH_REV_NOTE}}"),
    ],
    # 板块/个股两行判定（标签类可与上面不同）
    "extra_top": ('<div class="rev-top" style="font-size:10.5px;color:#9aa4ba;">'
                  '<span class="rev-name" style="font-size:11px;">板块</span><span class="rev-tag {{SECTOR_TAG}}">◐ {{SECTOR_JUDGE}}</span>'
                  '<span class="rev-name" style="font-size:11px;margin-left:14px;">个股</span><span class="rev-tag {{STOCK_TAG}}">◐ {{STOCK_JUDGE}}</span></div>'),
    "extra_pred": "{{EXTRA_NOTE}}",
    "brief_t": "上一开盘日速览",
    # 3~5 条，每条 <li>；禁用 emoji
    "brief": [
      "<li><b>{{BRIEF1_T}}</b>：{{BRIEF1_D}}</li>",
      "<li><b>{{BRIEF2_T}}</b>：{{BRIEF2_D}}</li>",
      "<li><b>{{BRIEF3_T}}</b>：{{BRIEF3_D}}</li>",
      "<li><b>{{BRIEF4_T}}</b>：{{BRIEF4_D}}</li>",
    ],
  },
  # ---------- 图2：昨日要闻 ----------
  "s2": {
    "sub": "{{NEWS_SUB}}",                    # 如 2026-10-23 收盘 ~ 10-26 06:19 · 影响开盘的关键事件
    "badge": "{{NEWS_COUNT}} 条精选",
    # (标题, 正文)；标题里用 <span class="hl">强调数字</span>，正文用 <b>
    "news": [
      ('{{NEWS1_T}}', '{{NEWS1_D}}'),
      ('{{NEWS2_T}}', '{{NEWS2_D}}'),
      ('{{NEWS3_T}}', '{{NEWS3_D}}'),
      ('{{NEWS4_T}}', '{{NEWS4_D}}'),
      ('{{NEWS5_T}}', '{{NEWS5_D}}'),
      ('{{NEWS6_T}}', '{{NEWS6_D}}'),
    ],
    "other_t": "其他动态",
    # 4~5 条，每条 <li>
    "other": [
      "<li>{{OTHER1}}</li>",
      "<li>{{OTHER2}}</li>",
      "<li>{{OTHER3}}</li>",
      "<li>{{OTHER4}}</li>",
      "<li>{{OTHER5}}</li>",
    ],
  },
  # ---------- 图3：今日预测 ----------
  "s3": {
    "d": "{{TODAY_MD}}",                                        # 如 10·26
    "sub": "{{TODAY_DATE}} {{TODAY_WEEK}} · 开盘方向优先 · 附收盘与日内区间",
    "badge": "开盘区间优先",
    "sec1": "大盘（开盘区间写入方向标签）",
    # (名称, 方向标签, 收盘lo, 收盘hi, 全天lo, 全天hi, 昨收, 支撑, 压力)；涨幅%由 mk_card 实时计算
    # 硬规则：收盘区宽度 ≤ 昨收1%、全天区 ≤1.5pct 且含收盘区
    "mk": [
      ("上证指数", "开{{SZ_OPEN_LO}}~{{SZ_OPEN_HI}}·{{SZ_OPEN_DIR}}", {{SZ_CLOSE_LO}}, {{SZ_CLOSE_HI}}, {{SZ_DAY_LO}}, {{SZ_DAY_HI}}, {{SZ_PREV_CLOSE}}, "{{SZ_SUP}}", "{{SZ_PRESS}}"),
      ("创业板指", "开{{CYB_OPEN_LO}}~{{CYB_OPEN_HI}}·{{CYB_OPEN_DIR}}", {{CYB_CLOSE_LO}}, {{CYB_CLOSE_HI}}, {{CYB_DAY_LO}}, {{CYB_DAY_HI}}, {{CYB_PREV_CLOSE}}, "{{CYB_SUP}}", "{{CYB_PRESS}}"),
      ("恒生指数", "开{{HSI_OPEN_LO}}~{{HSI_OPEN_HI}}·{{HSI_OPEN_DIR}}", {{HSI_CLOSE_LO}}, {{HSI_CLOSE_HI}}, {{HSI_DAY_LO}}, {{HSI_DAY_HI}}, {{HSI_PREV_CLOSE}}, "{{HSI_SUP}}", "{{HSI_PRESS}}"),
      ("恒生科技", "开{{HSTECH_OPEN_LO}}~{{HSTECH_OPEN_HI}}·{{HSTECH_OPEN_DIR}}", {{HSTECH_CLOSE_LO}}, {{HSTECH_CLOSE_HI}}, {{HSTECH_DAY_LO}}, {{HSTECH_DAY_HI}}, {{HSTECH_PREV_CLOSE}}, "{{HSTECH_SUP}}", "{{HSTECH_PRESS}}"),
    ],
    "sec2": "个股（观察 / 谨慎）",
    # (市场, 色, 关注, 回避)
    "stk": [
      ("港股", "#f5c542", '{{HK_FOCUS}}', '{{HK_AVOID}}'),
      ("上证", "#f6465d", '{{SH_FOCUS}}', '{{SH_AVOID}}'),
      ("创业板", "#0ecb81", '{{GEM_FOCUS}}', '{{GEM_AVOID}}'),
    ],
  },
}

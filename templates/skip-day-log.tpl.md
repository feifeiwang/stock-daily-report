### {DATE} 休市日（{WEEKDAY}）— SKIP，未生成任何报告

> 本条目由 `scripts/skip_day.py --log-out` 按本模板生成；只需核对数字、补「本轮增量」一段即可，
> 不用重写骨架。**改数字文字即可复用**（A45）。

- **交易日判定**：`python3 scripts/skip_day.py --repo <仓库> --date {DATE}` →
  `{HOLIDAY_OUT}` → `VERDICT=SKIP`
  → 下一开盘日 **{NEXT_OPEN}（{NEXT_WEEKDAY}，A股+港股同开）**；月份目录 `{MONTH_DIR}` **{MONTH_EXISTS}**（存在即复用，A10）。
- **幂等判定（A45）**：`PREV_MARKET_DAY={PREV_MARKET_DAY}`，总表末行 `LAST_ROW={LAST_ROW}` / `LAST_DATE={LAST_DATE}` /
  `LAST_M={LAST_M}` → `FINALIZE_STATE={FINALIZE_STATE}` → **`ACTION={ACTION}`**。
  - `SKIP_ONLY`：连续休市日 / 已定稿，**不采集、不回填、不新建行、不建日期文件、不调 build_charts/append_row/finalize_prev_day**。
  - `FINALIZE_THEN_LOG`：预取上一交易日数据 → `cp templates/prev-day-verify.tpl.py` 改值 → `finalize_prev_day.py` 定稿回填。
- **本次不产出**：不写 MD、不出三图、不新建总表行、不改动 `股票预测/股票预测总表.xlsx` 任何单元格、
  不建 `{MONTH_DIR}/` 下任何文件。
- **总表状态（只读核对）**：末行 G 列 `LAST_G={LAST_G}`；N 列 `N_COL={N_COL}`。
- **下一开盘日提示**：
  - 新行 `XLSX_PREV_RESULT = "{XLSX_PREV_RESULT}"`；末行已非「待验证」时 `--prev-result` 不触发（A34/A42）。
  - **A36 定锚**：以上一交易日**实际收盘**重新定锚，不沿用 N 列「收盘前预测」的预估收盘。
  - **月份目录**按日期自动计算（`DATE[:7].replace("-","")`），跨月无需手工新建（A10）。
- **本轮增量（每次手填这一段）**：<!-- 例如：预取周末消息面 / 新增脚本 / 无 -->
- **推送**：`references/runbook.md` 本条日志 + 本次改动的 `SKILL.md`/`scripts/*`/`templates/*`；总表零改动。
- **收尾**：`send_automation_result` 回报「今日休市未生成报告 + 下一开盘日 {NEXT_OPEN}」。

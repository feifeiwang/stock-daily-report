---
name: stock-daily-report
description: 每个交易日早晨自动预测上证/创业板/恒生/恒生科技的当日开盘走势（含收盘与日内区间），产出 1 份 MD + 3 张 1080×1920 竖版 JPG，并把当日小结写进「股票预测总表.xlsx」，全部提交到 GitHub 仓库的 股票预测/YYYYMM/ 目录。两地（A股与港股）同日均休市时跳过、不产生任何文件。当用户提到"今日股市预测/开盘预测/每日行情汇报/复盘昨天预测/更新股票预测总表"时使用。
---

# 每日股市开盘预测（stock-daily-report）

## 一句话流程

```
交易日检查 → 拉取仓库最新（gh_sync pull）→ 读总表最近几行（含上期结论）
→ 采集核实 → 写 MD → 改 templates/day_template.json → build_charts 出 3 张 JPG
→ append_row 写总表（顺带回填上一日结果）→ gh_sync push + 回验 → present_files
```

## 产出与归档（结构固定，勿改）

```text
feifeiwang/stock-daily-report
├── 股票预测/
│   ├── 股票预测总表.xlsx          # 每日一行的小结表（累计）
│   └── 202610/                    # 六位月份目录，存在即复用
│       ├── 2026-10-27.md
│       ├── 2026-10-27_1.jpg       # 图1：上一开盘日预测复盘
│       ├── 2026-10-27_2.jpg       # 图2：盘前要闻
│       └── 2026-10-27_3.jpg       # 图3：今日开盘与日内预测
├── scripts/                       # 可执行工具（build_charts / append_row / gh_sync / holidays …）
├── templates/                     # day_template.json + DATA-SCHEMA.md + 总表母版
└── references/                    # md-template / excel-spec / pitfalls / runbook（经验台账）
```

- 每期**只归档 1 MD + 3 JPG**，不归档 PNG/HTML/长图。
- 工作目录用 `/workspace/stock-daily-report-tool/work/{日期}/`（仓库外），仓库目录只放要提交的东西。

## 无人值守规则

1. **先判交易日**：`python3 scripts/holidays.py`。输出含 `SKIP:` 才结束（两地同休），否则继续；单市场休市时在 MD 里注明，另一市场照常预测。
2. **沙箱每次可能是新的**：技能目录可能不存在，**仓库就是技能的活体备份**。开工第一步永远 `git clone`，从仓库取脚本/模板/本 runbook（A23）。
3. 已存在的日期不重做：`gh_sync.py pull` 后检查 `股票预测/YYYYMM/{日期}.md` 与总表 B 列。
4. 不提问、不中断；缺数据就用保守区间并在 MD「数据来源/假设」里写明。
5. 任一步失败：记录原因，继续能独立完成的步骤，最终总结如实报告，**不静默跳过**。

## 每日执行清单

| # | 步骤 | 命令 / 要点 |
|---|---|---|
| 0 | 建工作区 | **先 `git clone` 仓库到 `/tmp/sdr`**（技能本体未持久化，仓库才是活体备份，见 runbook A23）；再从**仓库** `cp -r scripts templates` 到 `work/{日期}/`。**不要依赖 `/root/.codebuddy/skills/` 下的旧副本** |
| 1 | 拉最新 | `git clone https://github.com/feifeiwang/stock-daily-report.git /tmp/sdr`（秒级）；失败则回退 `GH_TOKEN=... python3 scripts/gh_sync.py pull --repo-dir <仓库目录>` |
| 2 | 读历史 | 读 `股票预测/股票预测总表.xlsx` 最后 5 行（含第14列「收盘前预测下一交易日」）+ `references/runbook.md`，确定"本期调整要点" |
| 3 | 采集 | **优先搜"当日早报"**（金十/东财/同花顺财经早餐），一篇拿到前一日收盘+隔夜美股+当日要闻；点位用精确数字反查复核；≥2 源交叉，禁杜撰。详见 runbook A16 |
| 3b | 拿开盘价 | **不用逐个反查**：搜《A股三大指数集体高开》类快讯，一篇同时给 A股 + 港股的高开涨跌幅，用 `昨收×(1+涨跌幅)` 反推（误差 <0.01）。见 runbook 2026-10-29 日志 |
| 4 | 写 MD | 按 `references/md-template.md`，一次 Write 到 `work/{日期}/{日期}.md`；**开盘区间是第一等公民**，收盘/日内作辅助 |
| 5 | 填数据 | `cp templates/day_template.json work/{日期}/day.json`，**只改值、不加键**（`XLSX_*` 绝不进 day.json，见 runbook A15）。**出图前跑引号自检**（A21）：值里可含任意引号，但 `NEWS*_D` 历史上是双引号包裹，已修 |
| 5b | 复盘判定 | `{p}_TAG`（决定颜色）与 `{p}_TAG_TXT`（显示文案）**必须成对改**，否则出现"文案=部分、颜色=准确"。四项全准才 `tag-ok`（A22） |
| 6 | 出三图 | `python3 work/{日期}/scripts/build_charts.py --data work/{日期}/day.json --out work/{日期}/` → 3 张 1080×1920 JPG（含区间硬校验 + 测高）；出图后**抽查图1配色，疑点先裁剪放大再改模板**（runbook A18）。**测高失败看行数不看字数**：brief 4 条总行数 ≈7 行是图1 的硬预算（A19）；区间排序按"收盘→开盘→全天"（开盘区间也有 ≤1% 隐性校验，A20） |
| 7 | 写总表 | `python3 scripts/append_row.py --repo <仓库> --data work/{日期}/day.json --prev-result "上一日：开盘x/4；收盘y/4；综合n/6"`；再补写第14列「收盘前预测下一交易日」占位（`vertical='top'` 字符串，别用未导入的常量） |
| 8 | 归档 | 把 MD + 3 JPG 复制到 `<仓库>/股票预测/{YYYYMM}/` |
| 9 | 推送 | `gh_sync.py push --msg "report: {日期}" <5 个相对路径> ...`（自带 md5 回验） |
| 10 | 展示 | present_files 三张 JPG；文字给四指数开盘/收盘区间结论 + 落点 + 失败项 |

## 预测口径（用户定稿，违反即返工）

1. **开盘优先**：四指数（上证、创业板、恒指、恒生科技）必报，每项给「开盘方向 + 开盘区间 + 置信度 + 首要变量」。
2. 收盘区间宽度 ≤ 昨收 ×1.0%；全天波动宽度 ≤1.5pct 且必须完整包含开盘与收盘区间。宽区间=无意义，脚本会直接拒绝渲染。
3. 恒生科技每次必报；美股只作背景，**不给美股操作建议**（建议只覆盖港股/上证/创业板）。
4. 涨跌幅一律由数值实时计算（`_p()`），禁手填百分比字符串。
5. **开盘与收盘分开验证**，不能用开盘命中替代全天命中；总表状态写"开盘 x/4、收盘 y/4、综合 n/6"。
6. 三图/HTML 副标题一律中性（只写"上一开盘日 · 日期 星期"），休市/节后首开等措辞只进 MD 正文。
7. 关键数字用白 `#e9edf6` 或金 `#f5c542`，禁暗灰；涨 `#f6465d`、跌 `#0ecb81`；每张图底部固定"AI预测，仅供参考，不构成投资建议"。
8. 已生成日期不重做；所有数字可溯源；图片一律 JPG。

## 模板固化边界（"改数字就能出图"）

- **只改 `templates/day_template.json`**（或它的副本）：119 个字段，按 图1/图2/图3 分组并带中文注释。
- **禁改**：`scripts/templates/gen3_images.tpl.py`（CSS/track/donut/main）、`scripts/build_charts.py` 的校验与测高逻辑、图卡结构。
- 图1 的涨跌颜色与 ▲▼ **不要手写**：脚本由 `{指数}_PCT` 正负自动决定（历史坑：写死 up 会让跌的指数标红）。
- 文案超长会溢出页脚：长度红线见 `templates/DATA-SCHEMA.md` 第 10 节，改了长文案就重跑 build_charts（它自带测高门禁）。
- **`day.json` 的键集是封闭的**：多一个键（尤其 `XLSX_*`）脚本立刻拒绝渲染。总表相关的三个字段不属于 day.json，用命令行参数或事后补写 xlsx。
- **模板里的引号**：`scripts/templates/gen3_images.data.py` 的占位符外层已统一为单引号，`build_charts.py` 对含引号/反斜杠的值自动做 `repr()` 转义——所以文案里**可以放心写 `<span class="hl">`**。若哪天又出现 `SyntaxError`，先查是否有人把模板改回了双引号（A21）。
- **总表第 14 列「收盘前预测下一交易日」**：当日早晨只写占位（列出今晨已锁定的四指数区间），真正的收盘前预判需在 14:30 前后另有流程填写。

## 脚本清单

| 脚本 | 用途 |
|---|---|
| `scripts/gh_sync.py` | 拉取/推送/回验仓库（HTTPS API，不依赖 git，中文路径已编码） |
| `scripts/holidays.py` | A股/港股交易日判定（动态 + 静态兜底），打印 `SKIP:` 表示两地同休 |
| `scripts/build_charts.py` | day.json → 三张 JPG（区间校验 → 渲染 → 测高 → 转 JPG） |
| `scripts/append_row.py` | 总表追加当日行 + 回填上一日结果 + 查重 |
| `scripts/templates/gen3_images.tpl.py` | 三图骨架（禁改） |
| `scripts/templates/gen3_images.data.py` | 三图数据区模板（`{{占位符}}`） |
| `scripts/measure_heights.py` | 屏高实测（build_charts 内部调用） |
| `scripts/to_jpg.py` | 单独把 PNG 转 JPG（备用） |
| `templates/build_master_xlsx.py` | 总表结构母版（总表损坏时重建） |

## 参考文件

- `references/runbook.md` — **经验台账：固化坑清单 + 模板脚本清单 + 每次运行日志（运行前必读、运行后必写）**
- `references/md-template.md` — MD 日报结构
- `references/excel-spec.md` — 总表字段口径
- `references/pitfalls.md` — 历史踩坑全量（含配色/尺寸/措辞红线）
- `references/github-push.md` — 推送协议（现以 `scripts/gh_sync.py` 为准）

## 每次运行结束必做（自迭代）

1. 把本次遇到的问题写进 `references/runbook.md` 的「运行日志」（日期 + 现象 + 根因 + 已落地修正）。
2. 可复用的修正固化成模板/脚本（放进 `scripts/`、`templates/`），并把 `SKILL.md` 对应条目更新。
3. 这些 Skill 文件改动一并 `gh_sync.py push`（`SKILL.md`、`references/*`、`scripts/*`、`templates/*`）。

---
name: stock-daily-report
description: 每个交易日早晨自动预测上证/创业板/恒生/恒生科技的当日开盘走势（含收盘与日内区间），产出 1 份 MD + 3 张 1080×1920 竖版 JPG，并把当日小结写进「股票预测总表.xlsx」，全部提交到 GitHub 仓库的 股票预测/YYYYMM/ 目录。两地（A股与港股）同日均休市时跳过、不产生任何文件。当用户提到"今日股市预测/开盘预测/每日行情汇报/复盘昨天预测/更新股票预测总表"时使用。
---

# 每日股市开盘预测（stock-daily-report）

## 一句话流程

```
交易日检查 → 拉取仓库最新（git clone / gh_sync pull）→ 读总表最近几行（含上期结论）
→ 采集核实并落盘 market-data.md → 写 MD → 改 day_values.py（纯值表）→ make_day_json 生成 day.json
→ build_charts 出 3 张 JPG → append_row 写总表（顺带回填上一日结果）→ gh_sync push + 回验 → present_files
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

1. **先判交易日**：`python3 scripts/holidays.py --next 3`。输出含 `SKIP:` 才结束（两地同休，走下面「休市日标准动作」），否则继续；单市场休市时在 MD 里注明，另一市场照常预测。
2. **沙箱每次可能是新的**：技能目录可能不存在，**仓库就是技能的活体备份**。开工第一步永远 `git clone`，从仓库取脚本/模板/本 runbook（A23）。
3. 已存在的日期不重做：`gh_sync.py pull` 后检查 `股票预测/YYYYMM/{日期}.md` 与总表 B 列。
4. 不提问、不中断；缺数据就用保守区间并在 MD「数据来源/假设」里写明。
5. 任一步失败：记录原因，继续能独立完成的步骤，最终总结如实报告，**不静默跳过**。
6. **长会话可能被上下文压缩（A37）**：步骤 3 采集完立刻把行情数据落盘到 `work/{日期}/market-data.md`（按 `templates/market-data-notes.md`）；若发现上下文被压缩、具体数字丢失，先 Read 该快照恢复，不要重新联网搜一遍。

## 休市日标准动作（周末 / 两地同休，必走）

判定为 `SKIP:` 后**不生成任何预测产物**，但仍要跑完下面 5 步，否则下一次开盘会丢上下文（A26）：

1. **记下一开盘日**：`holidays.py --next 3` 已打印（如 `2026-11-02 星期一 A股+港股同开`），写进本次运行日志。跨月时一并确认新月份目录（如 `202611`）会被自动创建。
2. **预取上一交易日实际数据**（A27）：搜「次日早报 + 新华社港股通稿 + 行情表」≥2 源交叉（A30），把四指数实际开/收、板块/个股表现填进 `work/{日期}/prev_day_verify.py`（从 `templates/prev-day-verify.tpl.py` cp 来，A44）；表格骨架也可参照 `templates/prev-day-snapshot.md`，贴进 `references/runbook.md` 的运行日志。**隔了一两天再搜，搜索引擎更容易返回旧年份数据（A16）**，所以休市日顺手取最稳。**采集完立刻落盘 `work/{日期}/market-data.md`（A37）**，防止会话压缩丢失数字。
3. **核对并一次定稿**（A29）：把**板块与个股也核完**，直接给出综合分，**不要留"待下一交易日核对"**——下一交易日 07:30 要出报告，时间最紧、核对质量最差。个股核对走 A31 的两条捷径。**用 `scripts/finalize_prev_day.py` 一键算分 + 回填 + 出快照**（A44）：`cp templates/prev-day-verify.tpl.py work/{日期}/prev_day_verify.py` → **只改这一个文件的数字/文字** → `python3 scripts/finalize_prev_day.py --repo <仓库绝对路径> --values work/{日期}/prev_day_verify.py --snapshot-out work/{日期}/runbook-snapshot.md`（可先加 `--dry-run` 试算）。脚本会机械算分（A41）、校验总表末行日期与「待验证」状态、**只写 M 列 + 置绿底 `FFE2F0D9`、G 列绝对不动**（A34/A42），并生成可直接贴进 runbook 的定稿快照 + 打印下一交易日 `XLSX_PREV_RESULT` 摘要串。
   > **G 列语义红线（A42，2026-11-07 修正）**：G 列是「该行自己的上一交易日结果」，休市日回填**只改 M 列**；本节旧版写的「G 列写 `MM-DD：…`」是 A34 之前的过时口径，照做会把 G 列覆写成该行自身结果，正是 11-04 踩过的坑（A34）。
   > 回填后提示下一交易日：**`--prev-result` 不再生效**（上一行已非「待验证」），改用 `day.json` 的 `XLSX_PREV_RESULT` 写摘要串（脚本已打印，照抄即可）。
4. **写运行日志 + 推送**：runbook 追加当日 `SKIP` 条目（日期 + 判定输出 + 下一开盘日 + 定稿快照），把 `SKILL.md`/`references/*`/`scripts/*`/`templates/*` 与总表的改动一并 `gh_sync.py push`。
5. **收尾**：不新建总表行、不建 `股票预测/YYYYMM/` 下任何文件、不调 `build_charts`/`append_row`；用 `send_automation_result` 回报"今日休市未生成报告 + 下一开盘日"。
   > 判定红线：**两地均休市才跳过**。只有港股休（如香港公众假期）或只有 A 股休（如内地法定假日）时照常产出，只在 MD 正文注明。
   >
   > **数据红线（A30）**：收盘数据一律以**次日早报 / 新华社通稿**为准。财经快讯站点的"XX指数跌X%报XXXX点"标题里的"收盘"二字常与时间戳不符（见过 09:31 发的"收盘"稿，与真实收盘方向相反），拿到先看时间戳是否 ≥15:00，且必须与第二个源交叉。

> 判定红线：**两地均休市才跳过**。只有港股休（如香港公众假期）或只有 A 股休（如内地法定假日）时照常产出，只在 MD 正文注明。

### 跨月首日提醒

- 月份目录由 `append_row.py` 按**日期**自动算（`DATE[:7].replace("-","")`，见 A10），**跨月不需要手工新建目录**：11 月首个交易日产物自动落 `股票预测/202611/`。
- 总表始终是同一个 `股票预测/股票预测总表.xlsx`，跨月不新建、不拆分。
- 跨月首日要回填的是**休市前最后一个交易日**那行（仍是最后一行，`append_row.py` 能正常回填）。

## 每日执行清单

| # | 步骤 | 命令 / 要点 |
|---|---|---|
| 0 | 建工作区 | **先 `git clone` 仓库到 `/tmp/sdr`**（技能本体不保证持久化，仓库才是活体备份，见 runbook A23）；再从**仓库** `cp -r scripts templates` 到 `work/{日期}/`。**不要依赖 `/root/.codebuddy/skills/` 下的旧副本**。clone 完成后顺手 `cp -r SKILL.md references scripts templates /root/.codebuddy/skills/stock-daily-forecast/` 让本轮会话能按名加载（A32）。**无人值守注意（A35）：自动化多次工具调用之间工作目录会重置，跨调用一律写绝对路径（脚本/--data/--repo/--out 全部写全），`cd` 只在同一条命令内有效** |
| 1 | 拉最新 | 公开仓库先匿名执行 `git clone https://github.com/feifeiwang/stock-daily-report.git /tmp/sdr`（秒级，不依赖 OAuth）；若 GitHub 连接器取 token 返回 404，**不要阻塞拉取**，继续匿名 clone。仅推送阶段加载授权 token 到环境变量；失败则按 A25 记录并如实报告 |
| 2 | 读历史 | 读 `股票预测/股票预测总表.xlsx` 最后 5 行（含第14列「收盘前预测下一交易日」）+ `references/runbook.md`，确定"本期调整要点" |
| 3 | 采集 | **优先搜"当日早报"**（金十/东财/同花顺财经早餐），一篇拿到前一日收盘+隔夜美股+当日要闻；点位用精确数字反查复核；≥2 源交叉，禁杜撰。详见 runbook A16。**收盘价只认次日早报/新华社通稿，快讯先看时间戳（A30）**；复盘个股时用 A31 的两条捷径（新华社港股通稿 + 每经沪深A股成交额榜），别逐条搜；**采集完立刻落盘 `work/{日期}/market-data.md`（A37，压缩后可恢复）** |
| 3b | 拿开盘价 | **不用逐个反查**：搜《A股三大指数集体高开》类快讯，一篇同时给 A股 + 港股的高开涨跌幅，用 `昨收×(1+涨跌幅)` 反推（误差 <0.01）。见 runbook 2026-10-29 日志 |
| 4 | 写 MD | 按 `references/md-template.md`，一次 Write 到 `work/{日期}/{日期}.md`；**开盘区间是第一等公民**，收盘/日内作辅助 |
| 5 | 填数据 | **A40 新口径**：`cp templates/day_values.tpl.py work/{日期}/day_values.py`，**每天只改这一个文件的数字/文字**（`VALS` 图用 + `XLSX_VALS` 总表用，内含上一日真实值样例）；`python3 scripts/make_day_json.py --template <仓库>/templates/day_template.json --values work/{日期}/day_values.py --out work/{日期}/day.json --stage chart` 生成图用 day.json。**键集封闭**（121 键 = 9 个 `_` 注释键 + 112 有效值键，脚本自动拦截未知键）；`XLSX_*` 绝不进图阶段（A15/A33）。**出图成功后**再跑同一脚本 `--stage xlsx` 注入三字段供步骤 7 的 `append_row`（append_row 不校验键集，build_charts 才校验）。**出图前跑引号自检**（A21）：`NEWS*_D` 内禁半角双引号，高亮 `<span class="hl">` 只写 `NEWS*_T` |
| 5b | 复盘判定 | `{p}_TAG`（决定颜色）与 `{p}_TAG_TXT`（显示文案）**必须成对改**，否则出现"文案=部分、颜色=准确"。四项全准才 `tag-ok`（A22） |
| 6 | 出三图 | `python3 work/{日期}/scripts/build_charts.py --data work/{日期}/day.json --out work/{日期}/` → 3 张 1080×1920 JPG（含区间硬校验 + 测高）；出图后**抽查图1配色，疑点先裁剪放大再改模板**（runbook A18）。**测高失败看行数不看字数**：brief 4 条总行数 ≈7 行是图1 的硬预算（A19）；区间排序按"收盘→开盘→全天"（开盘区间也有 ≤1% 隐性校验，A20） |
| 7 | 写总表 | day.json 注入 `XLSX_*` 后：`python3 scripts/append_row.py --repo <仓库> --data work/{日期}/day.json --prev-result "上一日：开盘x/4；收盘y/4；综合n/6"`（**2026-11-04 起 `--prev-result` 只回填上一行 M 列状态、不再覆写上一行 G 列**——G 列语义是"该行自己的上一交易日结果"，新行 G 列由 `XLSX_PREV_RESULT` 提供，见 A34）；再补写第14列「收盘前预测下一交易日」占位（`vertical='top'` 字符串，别用未导入的常量） |
| 8 | 归档 | 把 MD + 3 JPG 复制到 `<仓库>/股票预测/{YYYYMM}/` |
| 9 | 推送 | `gh_sync.py push --msg "report: {日期}" <当日 5 个路径> <本次改动的 SKILL/references/scripts/templates>`（自带 md5 回验；token 走 `GH_TOKEN` 或 `--token-file`，**绝不写进仓库/命令参数/日志**） |
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
9. **A股与港股可以反向（A28）**：恒指由内银/保险/石油等高股息权重主导，定价的是低估值与现金流；A股创业板/恒科定价的是成长与海外映射。**不能把"A股科技链杀跌"直接映射成"恒指低开"**。出现 A/H 背离时（如 2026-10-30：上证 -1.44%、创业板 -4.13%，恒指却 +1.46% 收红），四个指数必须分别定价：恒指看内银/保险/石油与南向资金，恒科与创业板才看纳指与美股 AI 链。
10. **政策救市组合拳可独立逆转低开基准（A34）**：当盘前出现国内千亿级增量工具落地（如 SFISF 互换便利、回购增持再贷款转长期并降息）或重大稳预期会议时，**gap 方向须上修、不可单看海外隔夜**。2026-11-02 前一晚按"美股半导体/纳指走弱"给四指数低开，但三部门稳市会议+千亿回购贷+逆回购换锚+美伊谈判（地缘缓和）构成政策救市组合拳，四指数集体高开、方向性误判——凡国内有强政策托底，低开基准须打折甚至翻多。
11. **收盘前预测（总表 N 列）不作次日点位基准（A36）**：N 列在 14:15 生成时 A股 15:00 / 港股 16:00 尚未收盘，用的是「预估收盘」锚；次日早报必须取**上一交易日实际收盘**重新定锚，只把 N 列当方向参考。政策落地日偏差可达数十点（11-04 预估 3675 / 3895 → 实际 3686.17 / 3936.02）。
12. **A/H 完全脱钩：同一隔夜变量在两地符号可以相反（A39）**：A28 的「可反向」要再进一层。2026-11-05 美股 AI 硬件（监管/反垄断/数据中心审批）风险令资金从美股高估值 AI 硬件切向**港股互联网估值洼地**，A股低开高走仅微涨（上证 +0.10%、创业板 +0.87%），港股科网却独立暴涨（恒指 +3.67%、恒科 +5.55%），早报给恒指/恒科的窄幅高开区间分别破上沿 **287 / 199 点**。执行三条：①恒指/恒科**绝不由 A股方向或 A股科技链反推**，四指数各自列「隔夜变量 → 本地符号」再定价；②「费半/纳指大跌」对 A股科技链是开盘压制、对港股科网**可能反而是资金分流利好**，禁止用一个方向套四指数；③港股单日 ≥+4% 后拥挤度骤升（南向净流出、成交放大），次日不可线性外推，方向给「回吐/分化」而非继续追高。
13. **极端外盘冲击下跳空幅度不可打折（A43）**：A34 的「政策托底打折」只适用于常规隔夜波动。当隔夜出现「主要股指跌幅创多年纪录 + 亚太熔断」的系统性冲击（2026-11-06 前夜：费半 -12.25%、纳指 -5.52%、韩股 -6.02% 触发年内第 11 次熔断、日经 -5.96% 进入技术性熊市、A50 夜盘 -1.85%），政策托底只改变**日内修复斜率**，压缩不了**开盘跳空**；11-06 早报按 A34 把低开压到 -0.9%~-2.0%，四指数实际开 -1.58%~-4.99%，区间下沿全被击穿 42~175 点（方向 4/4 全对、点位 0/4 命中）。执行：开盘区间下沿以 **A50 夜盘跌幅为下限再留 0.5~1pct 缓冲**，且在 MD 风险提示里写明「极端跳空下区间有失效可能」；不要为保住窄幅区间而人为抬高下沿。
14. **避险 ≠ 买黄金（A43 附）**：在「加息预期升温 + 美元偏强 + 投行下调金价预期」组合下，黄金/贵金属股与高股息防御资产**反向**。11-06 早报自己已列出「高盛下调 2026 年底金价至 4150 美元、英国央行加息 25bp、戴利称仍需加息」，仍把贵金属列为首要占优，而当日有色 -3.00%、黄金股集体重挫，真正承接避险资金的是银行/电力/农业/公用事业/电信。**盘前列出的宏观利空必须传导到板块结论**，否则属可避免的内部矛盾。

## 模板固化边界（"改数字就能出图"）

四件套各管一摊，**每日只需改 `work/{日期}/day_values.py` 一个文件**（从 `templates/day_values.tpl.py` cp 来，见 runbook A40）：

| 模板 | 管什么 | 改法 |
|---|---|---|
| `templates/day_values.tpl.py` | **每日唯一要改**：三图全部数字与文案（`VALS`）+ 总表三字段（`XLSX_VALS`），带分组注释与 11-06 真实值样例（A40） | cp 成 `day_values.py` → 只改数字文字 → 交给 `make_day_json.py` 两阶段 |
| `templates/day_template.json` | 键集母版（121 键 = 9 个 `_` 注释键 + 112 有效值键） | **不改**，由生成器读取 |
| `references/md-template.md` | 当日 MD 的骨架（六节） | 按 `{}` 占位符填 |
| `templates/prev-day-snapshot.md` | 休市日上一交易日的开/收快照 + 机械判定 + 回填命令 | 复制内容块 → 填数字 → 贴进 runbook |
| `templates/prev-day-verify.tpl.py` | **休市日/次日定稿唯一要改的纯值表**（A44）：四指数预测区间 vs 实际开收、方向符号、板块/个股得分与文字、累计分、来源 | cp 成 `work/{日期}/prev_day_verify.py` → 只改数字文字 → 交给 `finalize_prev_day.py` |
| `templates/market-data-notes.md` | **行情采集快照**（A37）：四指数开/收、板块个股、隔夜外围、来源链接、复盘素材 | 步骤 3 采集完复制到 `work/{日期}/market-data.md` 填数；会话压缩后 Read 它恢复 |
| `templates/DATA-SCHEMA.md` | 上面 112 个有效值字段的含义、红线、文案长度上限 | 只读，改值表前先查 |

> **休市日/定稿口径（A41，2026-11-07 固化）**：评分一律由 `finalize_prev_day.py` 机械判定——区间命中 = 1、**方向对但出区间 = 0.5**、方向反 = 0；综合 /6 = 开盘÷2 + 收盘÷2 + 板块 + 个股。历史上「方向对但出区间」有时记 0、有时记 0.5（口径漂移），此后统一按 `references/excel-spec.md` 4.1/4.3 执行，不再手工给分。方向由值表里的 `*_pred_sign(-1/0/1)` 与 `sign(实际值 − 昨收)` 比较，不做主观幅度判断。

- **只改 `work/{日期}/day_values.py`**：`VALS` 覆盖三图全部值，`XLSX_VALS` 供总表；**键名一律不许新增**，键集由 `scripts/make_day_json.py` 对照 `day_template.json` 自动校验（A40）。模板里少写某个键 = 沿用旧值，写错键名会直接被脚本拒绝。
- **禁改**：`scripts/templates/gen3_images.tpl.py` 的布局/组件/track/donut/main、`scripts/build_charts.py` 的校验与测高逻辑、图卡结构。**例外**：确属缺陷的修复（如 A38 补 `.rev-act.up/.down` 红涨绿跌配色）可改 CSS，但须同步写进 runbook，且不许为改当日内容动骨架。
- 图1 的涨跌颜色与 ▲▼ **不要手写**：脚本由 `{指数}_PCT` 正负自动决定（历史坑：写死 up 会让跌的指数标红）。**A38 补充**：`derive()` 只输出 `class="rev-act up/down"`，颜色须由 CSS 规则提供；验收时用像素取色或检查 `/tmp/img1.html` 是否含 `.rev-act.up{color:#f6465d}`，别只看 class 名。
- 文案超长会溢出页脚：长度红线见 `templates/DATA-SCHEMA.md` 第 10 节，改了长文案就重跑 build_charts（它自带测高门禁）。
- **`day.json` 的键集是封闭的**：多一个键（尤其 `XLSX_*`）`build_charts.py` 立刻拒绝渲染，`make_day_json.py --stage chart` 会提前拦截。总表三字段**只在出图成功后**用 `--stage xlsx` 注入同一 day.json（A33/A40）。
- **模板里的引号**：`scripts/templates/gen3_images.data.py` 的占位符外层已统一为单引号，`build_charts.py` 对含引号/反斜杠的值自动做 `repr()` 转义——所以文案里**可以放心写 `<span class="hl">`**。若哪天又出现 `SyntaxError`，先查是否有人把模板改回了双引号（A21）。
- **总表第 14 列「收盘前预测下一交易日」**：当日早晨只写占位（列出今晨已锁定的四指数区间），真正的收盘前预判需在 14:30 前后另有流程填写。

## 脚本清单

| 脚本 | 用途 |
|---|---|
| `scripts/gh_sync.py` | 拉取/推送/回验仓库（HTTPS API，不依赖 git，中文路径已编码） |
| `scripts/holidays.py` | A股/港股交易日判定（动态 + 静态兜底），打印 `SKIP:` 表示两地同休；`--next N` 列出之后 N 个开盘日 |
| `scripts/make_day_json.py` | **值表 → day.json**（键集封闭校验 + `--stage chart` / `--stage xlsx` 两阶段，A40） |
| `scripts/build_charts.py` | day.json → 三张 JPG（区间校验 → 渲染 → 测高 → 转 JPG） |
| `scripts/append_row.py` | 总表追加当日行 + 回填上一日结果 + 查重 |
| `scripts/finalize_prev_day.py` | **休市日/次日定稿一条龙**（A44）：纯值表 → 机械算分（A41）→ 只回填 M 列 + 绿底（G 列不动，A42）→ 生成可贴 runbook 的快照 md → 打印下一交易日 `XLSX_PREV_RESULT`；自带日期/状态校验与 `--dry-run` |
| `scripts/templates/gen3_images.tpl.py` | 三图骨架（禁改） |
| `scripts/templates/gen3_images.data.py` | 三图数据区模板（`{{占位符}}`） |
| `scripts/measure_heights.py` | 屏高实测（build_charts 内部调用） |
| `scripts/to_jpg.py` | 单独把 PNG 转 JPG（备用） |
| `templates/build_master_xlsx.py` | 总表结构母版（总表损坏时重建） |
| `templates/prev-day-snapshot.md` | **休市日专用**：上一交易日实际开/收数据 + 机械判定快照表格骨架（贴 runbook 用）；算分/回填改由 `finalize_prev_day.py` 自动完成 |
| `templates/prev-day-verify.tpl.py` | **休市日定稿纯值表**（A44）：与 `finalize_prev_day.py` 配套，内含真实值样例与字段红线 |

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

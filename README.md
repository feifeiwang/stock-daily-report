# stock-daily-report · 每日股市行情汇报 Skill

每个交易日自动生成一整套行情汇报：**MD 日报 + 3 张 1080×1920 竖版图（JPG）+ 经验 Excel 跟踪**，并按 `{年}/{月}/` 归档到本 GitHub 仓库。

本仓库既是一个 [Agent Skill](#作为-agent-skill-使用)（`SKILL.md` + `references/`），也可以把 `scripts/` 当独立工具用（只生成 HTML / 图片部分）。

## 产出物

归档到仓库 `YYYY/MM/` 目录，每期 4 个文件：

| 文件 | 内容 |
|---|---|
| `{日期}.md` | 前一交易日中美港三国股市总结 + 近日要闻 + 今日预测与操作建议 + 风险提示 + 预测复盘表 |
| `{日期}_1.jpg` | 图1：上一开盘日预测复盘 + 累计准确率圆环 |
| `{日期}_2.jpg` | 图2：昨日要闻精选 |
| `{日期}_3.jpg` | 图3：今日预测（大盘区间卡 + 板块 + 个股关注/回避） |

仓库根：

| 文件 | 内容 |
|---|---|
| `预测经验跟踪.xlsx` | **精简经验库（每次预测前必读）**：每日预测 + 上一日成败判定 + 失败原因（10 列，6 项制评分） |

本地另有 `每日行情预测准确率跟踪.xlsx`（全量留档，含四项指数实际收盘与逐项兑现详述），不归档到仓库。

## 目录结构

```
├── SKILL.md                  # Skill 定义：每日 10 步流程、14 条硬性规则、脚本固化边界
├── references/
│   ├── md-template.md        # MD 日报完整模板
│   ├── excel-spec.md         # 两份 Excel 规范 + 6 项制判定口径
│   ├── github-push.md        # 归档目录结构 + Contents API 串行推送协议
│   └── pitfalls.md           # 25 条避坑（归档路径/截图管线/尺寸联动/配色/预测质量）
├── scripts/
│   ├── gen_html.py           # 生成 8 屏竖屏 HTML（内联 SVG，无外部依赖）
│   ├── shot_long.py          # HTML 逐屏截图 + PIL 拼接长图
│   ├── gen3_images.py        # 生成三张 1080×1920 竖图（D 字典驱动）
│   ├── measure_heights.py    # 屏高实测把关（溢出退出码 1）
│   └── to_jpg.py             # PNG → JPG 转换（归档统一用 JPG）
├── 2026/                     # 按年份
│   └── 10/                   # 按月份
│       ├── 2026-10-21.md
│       └── 2026-10-21_1~3.jpg
└── README.md
```

## 每日流程（10 步，详见 SKILL.md）

```
0 防重复+定位  → 确认当天 md 未生成、GitHub YYYY/MM/ 无同名文件、经验库无当天行
1 读经验库     → 读 预测经验跟踪.xlsx（尤其 J 列失败原因），形成本期调整要点
2 采集核实     → WebSearch/WebFetch 采集前一交易日收盘/要闻，多源交叉，禁杜撰
3 MD 日报      → 按 md-template.md 一次写成 {工作区}/{日期}.md
4 Excel        → 经验库追加当天行 + 回填上一日判定；本地全量表写当天预测行
5 竖屏 HTML    → 复制昨日 gen_html 脚本改数据 → 运行
6 测高把关     → measure_heights.py，溢出先压缩再往下
7 长图         → shot_long.py 逐屏截图拼接（本地，不归档）
8 三张图       → 复制昨日 gen3_images 脚本只改顶部 D 字典 → 运行 → 测高
9 转 JPG + 推 GitHub → to_jpg.py 转换 → 串行 PUT 到 YYYY/MM/ + 经验 xlsx → 远程回验
10 展示        → present_files 三张 JPG + 当日结论
```

## 环境依赖

```bash
pip install playwright pillow openpyxl requests
playwright install chromium          # 或使用系统 Chrome
# 中文字体：Noto Sans CJK SC（图表渲染依赖，符号 ▲▼✓★⚠ 等已被该字体覆盖）
```

## 作为 Agent Skill 使用

`SKILL.md` 头部带标准 frontmatter（`name` / `description`），可被支持 Agent Skill 格式的运行时直接加载。归档走 GitHub Contents API（`scripts` 无 token，token 由环境变量 `GH_TOKEN` 注入）。

## 硬性规则（预测质量，来自实际使用反馈）

1. 大盘预测必须含**收盘价区间 + 全天波动范围**，且区间收窄：**收盘区间宽度（最高−最低）≤ 昨收 1%**，全天波动宽度 ≤ 1.5pct 且含收盘区，必须给方向倾向
2. 恒生科技每次必报
3. 操作建议只覆盖港股 / 上证 / 创业板，不谈美股操作
4. 分大盘、板块、个股三方面
5. 所有数字可溯源，禁止凭空杜撰
6. 关键数字不用暗灰色；三张图与 HTML 头部副标题一律中性（禁休市/假期等市场状态措辞上图）
7. 预测收盘必须配对"实际收盘 待定"显示位，实际值由图 1 次日复盘呈现
8. 涨跌幅百分比一律由数值实时算出，禁手填字符串
9. 图3 轨道刻度四卡统一昨收 ±2%，金条宽度即涨幅百分比
10. 产出归档到 GitHub `{年}/{月}/`，图片一律 JPG；每次预测前必读经验 Excel

## 免责声明

本项目生成的所有内容为 AI 自动生成的市场信息汇总与观点记录，数据整理自公开渠道，**不构成投资建议**。市场有风险，决策需独立判断。

## License

MIT

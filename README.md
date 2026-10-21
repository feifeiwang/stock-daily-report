# stock-daily-report · 每日股市行情汇报 Skill

每个交易日自动生成一整套行情汇报：**MD 日报 + Excel 准确率跟踪 + 竖屏 HTML 长图 + 三张 1080×1920 竖版图**，并可上传到网盘归档。

本仓库既是一个 [Agent Skill](#作为-agent-skill-使用)（`SKILL.md` + `references/`），也可以把 `scripts/` 当独立工具用（只生成 HTML / 图片部分）。

## 产出物（按当天日期命名）

| 文件 | 内容 |
|---|---|
| `{日期}.md` | 前一交易日中美港三国股市总结 + 近日要闻 + 今日预测与操作建议 + 风险提示 + 预测复盘表 |
| `每日行情预测准确率跟踪.xlsx` | 一行一天：四项大盘预测 + 板块 + 个股，次日回填实际值与判定 |
| `{日期}.html` | 8 屏手机竖屏（抖音可刷格式）行情速览 |
| `{日期}.png` | HTML 逐屏截图拼接的长图（1080×15360） |
| `{日期}_1.png` | 图1：上一开盘日预测复盘 + 累计准确率圆环 |
| `{日期}_2.png` | 图2：昨日要闻精选 |
| `{日期}_3.png` | 图3：今日预测（大盘区间卡 + 板块 + 个股关注/回避） |

## 目录结构

```
├── SKILL.md                  # Skill 定义：每日 10 步流程、硬性规则、脚本固化边界
├── references/
│   ├── md-template.md        # MD 日报完整模板
│   ├── excel-spec.md         # Excel 字段规范与防重流程
│   └── pitfalls.md           # 22 条避坑（网盘签名/截图管线/尺寸联动/配色/预测质量）
├── scripts/
│   ├── gen_html.py           # 生成 8 屏竖屏 HTML（内联 SVG，无外部依赖）
│   ├── shot_long.py          # HTML 逐屏截图 + PIL 拼接长图
│   ├── gen3_images.py        # 生成三张 1080×1920 竖图（D 字典驱动）
│   └── measure_heights.py    # 屏高实测把关（溢出退出码 1）
└── README.md
```

## 每日流程（10 步，详见 SKILL.md）

```
0 防重复检查  → 确认当天 md 与 Excel 行都不存在（已生成的日期不重做）
1 采集核实    → WebSearch/WebFetch 采集前一交易日收盘/要闻，多源交叉，禁杜撰
2 MD 日报     → 按 md-template.md 一次写成 {日期}.md
3 Excel       → 写当天预测行（openpyxl，一行一天）
4 竖屏 HTML   → 复制昨日 gen_html 脚本改数据 → 运行
5 测高把关    → measure_heights.py，溢出先压缩再往下
6 长图        → shot_long.py 逐屏截图拼接
7 三张图      → 复制昨日 gen3_images 脚本只改顶部 D 字典 → 运行 → 测高
8 上传网盘    → 逐个串行：开票 → PUT → complete（禁止并行开票）
9 展示        → present_files 三张图 + 当日结论
```

## 环境依赖

```bash
pip install playwright pillow openpyxl
playwright install chromium          # 或使用系统 Chrome
# 中文字体：Noto Sans CJK SC（图表渲染依赖，符号 ▲▼✓★⚠ 等已被该字体覆盖）
```

## 作为 Agent Skill 使用

`SKILL.md` 头部带标准 frontmatter（`name` / `description`），可被支持 Agent Skill 格式的运行时直接加载。工作流中的"网盘"步骤以 tdrive 类 MCP 工具为例（`dir_list` / `file_upload` / `file_upload_complete`），换成任意文件存储均可，目录 ID 在 SKILL.md 里占位，填你自己的即可。

## 硬性规则（预测质量，来自实际使用反馈）

1. 大盘预测必须含**收盘价区间 + 全天波动范围**，且区间收窄：收盘区间 ≤ 昨收 ±1.0%，波动范围 ≤1.5pct，必须给方向倾向
2. 恒生科技每次必报
3. 操作建议只覆盖港股 / 上证 / 创业板，不谈美股操作（美股仅背景）
4. 分大盘、板块、个股三方面
5. 所有数字可溯源，禁止凭空杜撰
6. 关键数字不用暗灰色；三张图与 HTML 头部副标题一律中性（禁休市/假期等市场状态措辞上图）
7. 预测收盘必须配对"实际收盘 待定"显示位，实际值由图 1 次日复盘呈现

## 免责声明

本项目生成的所有内容为 AI 自动生成的市场信息汇总与观点记录，数据整理自公开渠道，**不构成投资建议**。市场有风险，决策需独立判断。

## License

MIT

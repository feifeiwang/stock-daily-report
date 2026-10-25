# stock-daily-report · 每日股市开盘预测 Skill

每天早晨自动检查上证与中国香港股市交易日；只要任一市场开市，就生成：**1份MD日报 + 3张1080×1920竖版JPG + 1行累计Excel记录**。两地同日均休市时跳过。

本仓库既是一个 Agent Skill（`SKILL.md` + `references/`），也可以把 `scripts/` 当独立的图片生成工具使用。

## 产出物

累计总表固定为：

- `股票预测/股票预测总表.xlsx`

每日产物按六位月份目录归档，例如 `股票预测/202610/`：

| 文件 | 内容 |
|---|---|
| `{日期}.md` | 交易日检查、上一交易日复盘、盘前要闻、四指数开盘预测、收盘/日内区间、板块个股与风险提示 |
| `{日期}_1.jpg` | 图1：上一开盘日开盘/收盘预测复盘 + 累计准确率 |
| `{日期}_2.jpg` | 图2：盘前关键要闻 |
| `{日期}_3.jpg` | 图3：今日开盘区间优先的预测卡 + 个股观察 |

旧版 `YYYY/MM/` 与根目录 `预测经验跟踪.xlsx` 作为历史兼容数据保留，不再新增。

## 目录结构

```text
├── SKILL.md                     # Skill 说明（无人值守流程 + 预测口径 + 固化边界）
├── README.md
├── references/
│   ├── runbook.md               # ★经验台账：固化坑清单 + 每次运行日志（运行前必读）
│   ├── md-template.md           # MD 日报结构
│   ├── excel-spec.md            # 总表字段口径
│   ├── github-push.md           # 推送协议（以 gh_sync.py 为准）
│   └── pitfalls.md              # 历史踩坑全量
├── templates/                   # ★每天只改这里
│   ├── day_template.json        # 每日数据模板（119 字段，分组注释）
│   ├── DATA-SCHEMA.md           # 字段含义 + 文案长度红线
│   └── build_master_xlsx.py     # 总表结构母版（损坏时重建）
├── scripts/
│   ├── gh_sync.py               # 拉取/推送/回验（HTTPS API，不依赖 git）
│   ├── holidays.py              # A股/港股交易日判定
│   ├── build_charts.py          # day.json → 3 张 JPG（区间校验 + 测高 + 转码）
│   ├── append_row.py            # 总表追加当日行 + 回填上一日结果
│   ├── templates/
│   │   ├── gen3_images.tpl.py   # 三图骨架（CSS/组件/main，禁改）
│   │   └── gen3_images.data.py  # 三图数据区（{{占位符}}）
│   ├── measure_heights.py       # 屏高门禁（build_charts 内部调用）
│   ├── to_jpg.py                # PNG→JPG（备用）
│   └── gen_html.py / shot_long.py  # 旧版长图管线（仅本地调试，不归档）
├── 股票预测/
│   ├── 股票预测总表.xlsx
│   └── 202610/
│       ├── 2026-10-26.md
│       └── 2026-10-26_1~3.jpg
└── 2026/10/                     # 旧版历史归档，只读保留
```

## 每日流程（"改数字就能出图"）

```text
0 交易日检查   → python3 scripts/holidays.py（两地同休才跳过）
1 拉最新       → python3 scripts/gh_sync.py pull --repo-dir <仓库目录>
2 读历史       → 总表最后 5 行 + references/runbook.md
3 采集核实     → 多源核验前一交易日收盘、隔夜期指/商品、资金与要闻
4 写 MD        → 按 references/md-template.md
5 填数据       → cp templates/day_template.json day.json，只改值
6 出三图       → python3 scripts/build_charts.py --data day.json --out out/
                 （自动做区间硬校验 / 测高 / PNG→JPG）
7 写总表       → python3 scripts/append_row.py --repo <仓库> --data day.json --prev-result "..."
8 归档         → 股票预测/YYYYMM/ 放 1 MD + 3 JPG
9 推送         → python3 scripts/gh_sync.py push --msg "report: {日期}" <路径...>
10 展示        → 三张 JPG + 四指数结论
```

## 预测硬规则

1. 必报上证指数、创业板指、恒生指数、恒生科技指数。
2. 每项先给开盘方向、开盘数值区间、相对昨收百分比与置信度。
3. 收盘区间宽度不超过昨收1%；日内区间宽度不超过1.5个百分点且包含收盘区间（`build_charts.py` 会拒绝违规数据）。
4. 图3轨道统一为昨收±2%，百分比由数值实时计算，禁止手填。
5. 美股只作背景，不给美股操作建议；板块与个股覆盖中国香港、上证和创业板。
6. 开盘与收盘分开验证，不能用开盘命中替代全天命中。
7. 图片一律JPG；涨红、跌绿；关键数字用白色或金色。
8. 每张图底部固定“AI预测，仅供参考，不构成投资建议”。

## 模板与经验沉淀

- **每天只改 `templates/day_template.json`**；图卡结构、CSS、轨道、圆环均在 `scripts/templates/gen3_images.tpl.py` 固化，禁改。
- 图1 的涨跌颜色与 ▲▼ 由 `{指数}_PCT` 正负自动派生，禁止手写（历史坑：写死会红涨绿跌反色）。
- 遇到问题按"现象—根因—已落地修正"写进 `references/runbook.md`，能复用的固化成 `scripts/`/`templates/` 里的模板。

## 凭据安全

GitHub Token只通过环境变量使用，禁止写入仓库、脚本、日志、MD、Excel或远程URL。推送完成后删除仓库外的临时凭据文件。

## 环境依赖

```bash
pip install playwright pillow openpyxl requests
playwright install chromium
```

中文字体使用 `Noto Sans CJK SC`。

## 免责声明

本项目生成的所有内容为AI自动生成的市场信息汇总与观点记录，数据整理自公开渠道，**不构成投资建议**。市场有风险，决策需独立判断。

## License

MIT

# 运行经验与踩坑台账（每次运行后追加，运行前先读）

> 规则：**每次运行后把新踩的坑写进"运行日志"段**（日期 + 现象 + 根因 + 已落地的修正），
> 并把可复用的修正固化成模板/脚本（scripts/、templates/），避免下次重踩。

## 一、固化下来的坑（改代码/改流程前必看）

| # | 现象 | 根因 | 已固化修正 |
|---|---|---|---|
| A1 | `git clone/fetch/push` 卡 2 分钟失败：`Failed to connect to github.com port 443` | 沙箱出网只放通 api.github.com / codeload，git 协议不通 | 一律用 `scripts/gh_sync.py`（HTTPS Contents API 串行 PUT + md5 回验），不要 git |
| A2 | `push_gh.py put "a=b"` 报 `unrecognized arguments` | 位置参数被 `--files nargs=*` 吞掉 | 用 `gh_sync.py push --msg ... "路径" "路径"`；位置参数必须放在 `--msg` 之后 |
| A3 | Contents API 返回 404 以为"仓库为空" | 中文路径 `股票预测` 未做 `quote(..., safe="")` | `gh_sync.py` 内已统一 `contents_url()` 编码 |
| A4 | 图1 里跌的指数显示"▼-0.19%"却标红、带▲ | 模板把 `rev-act up` 与 `▲` 写死，只换数字 | `build_charts.py` 由 `{指数}_ACTUAL`/`_PCT` 自动派生 up/down + ▲▼ |
| A5 | 把带引号的 HTML 塞进模板报 `invalid character '▲'` | 直接字符串替换破坏了 Python 字面量 | `build_charts.py` 对 `*_ACT_SPAN` 做 `repr()` 转义（只取内层，外层引号由模板提供） |
| A6 | 改了 CSS 后三图溢出但不报错 | `.ft` 是绝对定位页脚，内容被盖住不抛异常 | `build_charts.py` 渲染后自动跑 `measure_heights.py`，间隙 <2px 直接退出码 3 |
| A7 | PNG 上传后仓库暴涨 | 三图 PNG 每张 0.6~2.8MB | `build_charts.py` 直接输出 JPG(quality 90)，PNG 只留在 /tmp |
| A8 | 预测区间写宽了被判"无意义" | 收盘区间 > 昨收 1%、全天 > 1.5pct | `build_charts.py` 在渲染前硬校验，违规退出码 2 并列明哪一项超限 |
| A9 | 同一天跑两次，总表出现重复行 | 无查重 | `append_row.py` 检测到同日期直接退出码 4；`gh_sync.py pull` 先同步远端 |
| A10 | 月末跨月，产物写错目录 | 按运行日而非自然月拼路径 | 月份目录 = `DATE[:7].replace("-","")`，脚本自动生成，勿手写 |
| A11 | 节假日误判导致白跑或漏跑 | 只看单一第三方日历 | `holidays.py` 动态（holiday-cn）+ 静态兜底；跳过条件严格为"两地均休市" |
| A12 | 图3 出现"预测收盘价"却没有实际收盘位（用户投诉） | 只显示预测 | 模板卡面固定"预测收盘 X~Y"+"实际收盘 待定"双位，实际值次日由图1 呈现 |
| A13 | 图上一旦写"休市后首开"就被用户投诉 | 措辞非中性 | 副标题只用"上一开盘日 · 日期 星期"；市场状态只写 MD 正文 |
| A14 | 经验库里越写越长，读不完 | 把整篇分析塞进单元格 | 总表每格短句；详细过程进 MD，不进 Excel |

## 二、模板与脚本清单（"改数字就能出图"）

| 文件 | 作用 | 每日怎么用 |
|---|---|---|
| `templates/day_template.json` | **每日唯一要改的数据文件**（119 个字段，按 图1/图2/图3 分组注释） | cp 一份 → 只改值 → 交给 build_charts |
| `scripts/build_charts.py` | JSON → 三张 JPG（校验区间规则 + 测高 + 转 JPG 一条龙） | `python3 scripts/build_charts.py --data day.json --out out/` |
| `scripts/append_row.py` | 总表追加当日行 + 回填上一日结果 | `python3 scripts/append_row.py --repo <仓库根> --data day.json --prev-result "..."` |
| `scripts/gh_sync.py` | 拉取/推送/回验（不依赖 git） | `pull` → 生成 → `push` |
| `scripts/templates/gen3_images.tpl.py` | 三图骨架（CSS/组件/main，禁改） | 由 build_charts 自动拼装，不手改 |
| `scripts/templates/gen3_images.data.py` | 三图数据区模板（{{占位符}}） | 同上，占位符含义见 `templates/DATA-SCHEMA.md` |
| `templates/build_master_xlsx.py` | 总表结构母版（表头+说明） | 总表损坏时重建：`python3 templates/build_master_xlsx.py <输出>` |

## 三、运行日志（倒序）

### 2026-10-26 首次按月归档运行

- **场景**：Skill 改为"每日 07:30 预测当日开盘 + 归档到 `股票预测/YYYYMM/`"后的首次执行；上一轮已产出 10-26 的 MD/三图/总表，但只落在本地产物目录，**未推到 GitHub**。
- **踩坑 1**：`git fetch origin` 卡住 135 秒后报 443 连接失败 → 改用 Contents API（见 A1）。
- **踩坑 2**：`push_gh.py put "SKILL.md=SKILL.md" ...` 被 `--files nargs="*"` 吞参 → 改放到 `--msg` 之后成功（见 A2）。后续固定改用新脚本 `gh_sync.py`。
- **踩坑 3**：直接克隆远端 `feifeiwang/stock-daily-report` 到本地校验时，中文目录在 Contents API 下返回 404 → 需 `quote(..., safe="")`（见 A3）。
- **踩坑 4**：把三图模板里的"涨跌颜色/箭头"写死，做跌的指数会红涨箭头 → 改为由数据派生（A4/A5）。
- **结果**：10-26 的 1 份 MD + 3 张 JPG + 总表已入库到 `股票预测/202610/` 与 `股票预测/股票预测总表.xlsx`，md5 全部回验一致。
- **给下次的提醒**：先 `gh_sync.py pull` 把远端最新总表拉下来再 `append_row`，否则会覆盖掉别处新增的行。

### 2026-10-26 补记（同日第二次运行）

- **踩坑 5**：新写的 `gh_sync.py` 首次全量推送全部 FAIL，`get_file` 返回 None（看似 404）。根因：`call()` 拼 URL 时漏了 `/repos/{owner}/{repo}` 前缀，请求打到了 `api.github.com/contents/...`。已修：`call()` 统一补前缀 + HTTP 非 404 时打印状态码与响应体（不再静默返回 None）。**教训：任何"看起来是 404"的问题先打印完整 URL。**
- **踩坑 6**：`print` 在 python heredoc 里不可靠（管道被吞），调试改脚本时要用文件写入或返回值断言，不要靠 print 观察。
- **踩坑 7**：build_charts 里 `{{X}}` 占位符如果外层用单引号包住含双引号的 HTML，会出现 `''<span class="...">''` 双引号叠加 → 已统一：模板外层一律单引号，注入值用 `repr()[1:-1]` 转义。
- **结果**：SKILL.md、references/runbook.md、scripts/*（含 templates 子目录）、templates/* 全部入库，md5 回验通过。

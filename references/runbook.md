# 运行经验与踩坑台账（每次运行后追加，运行前先读）

> 规则：**每次运行后把新踩的坑写进"运行日志"段**（日期 + 现象 + 根因 + 已落地的修正），
> 并把可复用的修正固化成模板/脚本（scripts/、templates/），避免下次重踩。

## 一、固化下来的坑（改代码/改流程前必看）

| # | 现象 | 根因 | 已固化修正 |
|---|---|---|---|
| A1 | `git clone/fetch/push` 卡 2 分钟失败：`Failed to connect to github.com port 443` | 沙箱出网只放通 api.github.com / codeload，git 协议不通 | 一律用 `scripts/gh_sync.py`（HTTPS Contents API 串行 PUT + md5 回验），不要 git。**2026-10-27 复核：git clone 已可通（2秒完成），属网络抖动。现口径：拉取可先试 git、失败回退 `gh_sync pull`；推送固定用 `gh_sync push`** |
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
| A15 | `build_charts.py` 报"多余键（模板里没有）：XLSX_PREV_RESULT, XLSX_BASIS, XLSX_STATUS" | 把 `DATA-SCHEMA.md` 第9节的"总表专用"字段写进了 `day.json`，但脚本按键集严格校验，只认模板里的 119 个键 | **总表字段不要放进 day.json**；`append_row.py` 的上一日结果用 `--prev-result` 传，依据/状态直接改 xlsx 或在 append_row 后补写。day.json 只放图用的键 |
| A16 | `WebSearch` 搜"2026年10月26日 A股收盘"返回大量 2020/2022 年同日期的旧新闻，数字完全对不上 | 搜索引擎按月日匹配，跨年份污染严重；指数点位（2999/3251点）与真实值（3697点）差一个数量级 | ①**优先搜"次日早报"**（如"金十数据全球财经早餐 2026年10月2X日""东方财富财经早餐""同花顺A股早报"），早报会完整复盘前一日并给当日要闻，一篇文章拿到 80% 素材；②拿到点位后用 `"点位数字" + 指数名` 定向反查（如搜 `恒生指数 23211 开盘价`）能直接命中行情快照；③**看到点位与近期量级明显不符（如上证 2999 点）立即判定为旧年份数据并弃用** |
| A17 | 核对上一日实际开盘价时，只有昨收/涨跌幅、缺开盘价 | 早报通常只写收盘 | 用 `涨跌幅反推`：开盘价 = 昨收 ×(1+开盘涨跌幅)，或搜行情快照字段（"今开盘"）。MD 复盘表必须写"实际开盘 + 涨跌幅"，否则无法判断开盘是否命中 |
| A18 | 打开 JPG 预览时误以为"上证卡片是绿色边框=误标为准确" | 缩略预览下深蓝边框 `#1e2a45` 与绿色标签在低分辨率下易混淆 | 怀疑配色错误时，**先用 PIL 裁剪该区域放大 2 倍再看**（`im.crop(box).resize((w*2,h*2))`），并同时检查生成的 HTML 里 `class` 是否真的是 `tag-ok`。HTML/CSS 正确就不要改模板——避免"修一个不存在的问题" |

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

### 2026-10-27 常规日运行（本次）

- **交易日判定**：`holidays.py` → `2026-10-27 A股=开市 港股=开市`，正常执行。
- **踩坑 1（新，记 A15）**：习惯性把 `XLSX_PREV_RESULT / XLSX_BASIS / XLSX_STATUS` 三个"总表专用"键塞进 `day.json`，`build_charts.py` 直接以"多余键"拒绝渲染（退出码非0）。**day.json 只允许模板 119 个键**，总表字段走 `--prev-result` 参数或事后补写。
- **踩坑 2（新，记 A16）**：首轮 `WebSearch "2026年10月26日 A股收盘"` 返回的全是 2020/2022 年同日期的旧闻（沪指 2999 点 / 3251 点），差点误用。改搜"金十数据全球财经早餐 2026年10月2X日""东方财富财经早餐 10月27日""同花顺A股早报"，一次拿到前一日完整收盘 + 隔夜美股 + 当日要闻；再用 `"23211.81"` 这类精确点位反查确认开盘价。
- **踩坑 3（新，记 A18）**：看图1缩略图时以为上证卡片被误标为绿色（"开错收准"却是绿的），放大 2 倍后确认边框是中性深蓝 `#1e2a45`，HTML 里 class 是正确的 `tag-half`。**结论：不要凭缩略图改模板，先裁剪放大验证。**
- **流程改进**：本次 `git clone https://github.com/feifeiwang/stock-daily-report.git` **在 2 秒内成功**（10-26 曾失败，属网络抖动），所以"拉取"环节可以用 git（快且能一次拿到全量历史）；**"推送"仍固定走 `gh_sync.py push`**（带 md5 回验，且不需要在沙箱里配置凭证持久化）。原则：**拉取可 git（失败则回退 gh_sync pull），推送只用 gh_sync**。
- **结果**：`股票预测/202610/2026-10-27.{md,_1,_2,_3.jpg}` 共 4 个文件 + 总表（追加第4行、回填第3行验证结果、N列写入 10-28 收盘前预测占位）。

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

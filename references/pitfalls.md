# 避坑清单（都是实际踩过的坑）

## tdrive 网盘操作

1. **下载**：`file_download` 返回签名 URL 后，把 URL 写进文件（如 /tmp/dl_url.txt）再用 Python requests 读取下载——长 URL 严禁 shell 内联（引号/编码必坏）。若返回 `InvalidAccessKeyId` 403，重新签发一次 URL 再试（2026-10-20 实测：首签失败、重签即成功）。
2. **上传**：`file_upload` 拿票据（domain/path/headers/confirm_key/task_id）→ `curl -T` 或 requests PUT → `file_upload_complete` 落库。
3. **上传票据不要并行申请**：并行开多个票后逐个 PUT，会出现 403 SignatureDoesNotMatch（票据互相干扰）。**必须逐个：申请一个 → PUT → complete，再下一个**。
4. **长 token 严禁手工转录**：把票据 JSON 落盘（/tmp/ticket.json），用 Python 脚本读取后 PUT。手工复制 2000 字符的 security-token 必错（InvalidAccessKeyId）。
5. 覆盖上传同名文件用 `conflict_strategy: "overwrite"`；或先删后传。

## Playwright 截图管线

6. 视口 405×720 + `device_scale_factor=2.6666667` → 每屏 1080×1920（9:16 竖屏，抖音格式）。
7. 截图前 `page.add_style_tag(content="*{animation:none!important;transition:none!important}")` 停动画。
8. 多屏 HTML：对每个 `.screen` 元素单独 `element.screenshot()`，再用 PIL 纵向拼接到色底 (7,10,20) 画布。
9. **屏幕内容高度必须实测**（用 `scripts/measure_heights.py`，两种屏型自动识别）：
   - **gen3 单屏页脚模式**：`.ft` 是 absolute 底页脚，内容超高会被盖住且不报错。实测"最后一个非页脚子元素 bottom vs 页脚 top"间隙，**≥2px** 才算安全。
   - **HTML reel 安全线模式**：`.screen` 固定 720px + overflow:hidden，`scrollHeight` 恒为 720 不可用。实测最深叶子 bottom vs 安全线 **698**（=720-22 底padding）；**bottom==698 是 `margin-top:auto` 的设计吸附位（note/end-src 等吸底元素），不算溢出；>698 才是溢出**。
   - **mk-meta flex 折行陷阱**：flex 子 span 被压缩后文本内部换行，高度 14→28px，但"children 宽度差"检查仍显示非负——必须直接量 `.mk-meta` 高度==14（四卡全单行）。
   - **压缩菜单**（按序尝试）：① 缩文案（个股括注 ≤3 字、chips 每行 ≤6 项、note ≤3 行）；② CSS 微调（已验证安全值：`.rcard` padding 10/14/8+margin-bottom 8、`.stk` padding 3px 7px 且 i 8.5px、`.gcard` margin-bottom 6、`.ncard` padding 12px 14px+`.news-list` gap 9、`.rc-hd` gap 6、`.sb-row` 加 `flex-wrap:wrap` 整 span 换行不碎行）；③ 仍超 → 拆屏。
10. 中文字体用 `"Noto Sans CJK SC"`；已验证 ▲▼✓★⚠↑↓◆×●·— 等符号被该字体覆盖；无 emoji 字体，不要用 emoji。

## Python 代码

11. 大段 CSS/JS 用普通字符串拼接，屏幕模板用 f-string——CSS 花括号进 f-string 需双倍转义，极易错。
12. 内容含字面 `%`（如 ▼1.59%）时不要用 `%` 字符串格式化，用 f-string。

## 配色规范（用户认可的深色竖屏风格）

13. 涨红 `#f6465d`、跌绿 `#0ecb81`、金 `#f5c542`、深底 `#070a14`、卡片 `rgba(19,27,49,.72)`、边框 `#22304f`。
14. 小字不要用纯灰 `#8a94ac` 承载关键数字——用户反馈"看不清"。关键数字用 `#e9edf6`（白）或金色；区间轨的"昨收"标签要加深色底 pill 并避开昨收标线。

## 预测质量（用户明确反馈）

15. 大盘预测必须含**收盘价区间 + 波动范围**，且区间要收窄：收盘区间宽度 ≤ 昨收 ±1%，波动范围宽度 ≤ 1.5pct；必须给方向倾向。宽区间 = 无意义预测。
16. 恒生科技每次必报；操作建议只覆盖港股/上证/创业板，不谈美股操作。
17. 已生成的日期不重做（先检查文件夹和 Excel）。
18. **区间轨端点标签（gen3_images.py `track()` 的 label_lo/label_hi）必须完整落在金色区内**：黑字 `#1a1405` 若用 `text-anchor="middle"` 贴在金色带边缘，会一半掉进深色轨道底呈"黑字黑底"——用户 2026-10-17 实际反馈"很难看"。正解：lo 用 `start` 锚在 `xl+PAD`、hi 用 `end` 锚在 `xh-PAD`（PAD≈5）；带宽不足两标签防叠字时合并为 `"lo~hi"` 居中。HTML 版 `range_card` 的标签在轨道下方且为浅色字，无此问题。

## 措辞红线（用户 2026-10-20 反馈）

19. **三图与 HTML 的头部副标题一律中性**：只写"上一开盘日 · {日期} {星期}"式事实模板。休市/假期/节后首开/恢复交易等**市场状态措辞禁止上图**（只写 MD 正文）。用户原话："今天是星期二，你图上却写着休盘日后首开，这显然是不对的。"注意排查所有变体（"今日恢复交易""10-20开市"都算）。
20. **预测收盘必须配对实际收盘显示位**：大盘卡同时给"预测收盘 XXXX~XXXX"（金）+ "实际收盘 待定"（金占位）。用户原话："你第三张图上还写着预测收盘价，但是收盘价在哪显示没有。"实际值由图1 次日复盘呈现，禁在图3 编造。HTML `range_card` 已固化该双标签（`.rc-close` + `.rc-ft .act`）。

## 尺寸联动与验证纪律

21. **全宽 SVG 的宽度常量 `W` 必须 = 屏宽 − 屏padding − 卡padding**（当前 405−26−44−28=**307**）。改 `.screen` 或 `.card` 任一 padding 必须同步 W，否则 SVG 溢出卡片（2026-10-20 发现 W=357 过期：屏1 分歧图超出卡右缘 37px、range_card 轨道超 22px，肉眼易漏、截图里图表骑在卡片边框上）。
22. **验证不污染工作区**：两个生成脚本输出路径都支持 argv 覆盖（`python3 gen_html.py /tmp/x.html`）；验证性生成一律写 /tmp。已发布产物若被误覆盖，从网盘 `file_download` 下载原版恢复（见 #1）。用户说"今天不更新"时，工作区 HTML/PNG 也不重生成。

# GitHub 归档规范（2026-10-21 用户定稿）

> 变更：产出**不再**入网盘/WorkBuddy 项目文件夹，统一归档到 GitHub 仓库。网盘文件保留不删，但不再作为归档路径。

## 仓库与目录结构

仓库：`feifeiwang/stock-daily-report`

```
<仓库根>/
├── SKILL.md / README.md / references/ / scripts/   # skill 本体
├── 预测经验跟踪.xlsx                                 # 经验库（每次预测前必读，见 excel-spec.md）
└── 2026/                                            # 按年份
    └── 10/                                          # 按月份（两位数，含前导 0）
        ├── 2026-10-21.md                            # 当日日报（1 个 MD）
        ├── 2026-10-21_1.jpg                         # 图1 预测复盘 + 准确率
        ├── 2026-10-21_2.jpg                         # 图2 昨日要闻
        └── 2026-10-21_3.jpg                         # 图3 今日预测
```

规则：
- 目录名 `YYYY/MM`，MM 必须是两位数（`04` 不是 `4`）。
- 每期**只归档 4 个文件**：1 个 MD + 3 张图（长图 `{日期}.png` 与 HTML **不归档**）。
- 图片**一律 JPG**（PNG 占空间大，用户明确要求）。用 `scripts/to_jpg.py` 从 PNG 转换，不要直接把 PNG 推上去。
- 历史日期回填：把已生成的 MD/PNG 转成 JPG 后按同一结构上传；没有文件的日期跳过，不补造。

## 推送方式：Contents API 逐文件 PUT（不用 git push）

本地 git 仓库与远程历史**无共同祖先**（曾多次 force/re-init），`git push` 会失败。统一走 GitHub Contents API：

```
GET  https://api.github.com/repos/{owner}/{repo}/contents/{path}      -> 取 sha
PUT  https://api.github.com/repos/{owner}/{repo}/contents/{path}      -> body: {message, content(base64), sha}
```

- 鉴权 header：`Authorization: token {TOKEN}`、`Accept: application/vnd.github+json`、`X-GitHub-Api-Version: 2022-11-28`
- 文本文件：读 bytes → base64 → 放 `content`
- 二进制（xlsx/jpg）：同样 base64（GitHub Contents API 支持二进制 base64）
- **新建目录不需要单独建**：PUT 文件到 `2026/10/xxx.jpg` 时路径会自动创建；目录里已有同名文件必须带 `sha` 覆盖，否则 422。
- **必须串行**：一个文件 PUT 完再下一个，并行会撞 API 限流/冲突。

参考脚本：`/tmp/api_update.py`（仓库内不落 token，token 走环境变量 `GH_TOKEN`）。

## 每期推送清单（Step 8）

| 序 | 路径 | 类型 | 备注 |
|---|---|---|---|
| 1 | `SKILL.md` | 文本 | skill 变更时 |
| 2 | `README.md` | 文本 | skill 变更时 |
| 3 | `references/*.md` | 文本 | 变更的才推 |
| 4 | `scripts/*.py` | 文本 | 变更的才推 |
| 5 | `预测经验跟踪.xlsx` | 二进制 | 每期都更新（追加一行 + 回填上一日判定） |
| 6 | `YYYY/MM/{日期}.md` | 文本 | 每期 |
| 7 | `YYYY/MM/{日期}_1.jpg` | 二进制 | 每期 |
| 8 | `YYYY/MM/{日期}_2.jpg` | 二进制 | 每期 |
| 9 | `YYYY/MM/{日期}_3.jpg` | 二进制 | 每期 |

推完**必须远程回验**：对每个路径再 GET 一次，核对 `size` 与本地一致（JPG 可另下载比对 MD5）。

## 归档前置检查

1. 经验 Excel 已读（Step 1 之前）——不允许不读就预测。
2. 三张图已转 JPG 且体积正常（单张通常 150~400KB；>800KB 说明 quality 需要下调或图太花）。
3. MD 中的区间已符合新规（宽度 ≤ 昨收 1%），且图3 百分比由数值实时算出。

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
经验编号核查（A60）—— 固化新 A 编号前必跑，杜绝「同号异物」。

背景：A49 的编号纪律只覆盖「同一次运行里出现多条新经验」，未覆盖
「上一流程（如 14:15 收盘前预测）已在运行日志里预留了 A 编号」。
11-12 14:15 日志预留 A57/A58，11-13 早报初稿未核查就把另一条经验
也记作 A57，险些造成两条不同经验共用同一编号。

用法（A35：跨调用一律绝对路径）：
  python3 scripts/next_exp_id.py --repo <仓库绝对路径>
  python3 scripts/next_exp_id.py --repo <仓库绝对路径> --json

扫描范围：
  references/runbook.md（坑表 + 运行日志）、references/pitfalls.md、SKILL.md
  + 股票预测/股票预测总表.xlsx 第 14 列（收盘前预测常含「建议编号 Axx」预留）
输出：
  已固化编号（坑表 solid）、已预留编号（含预留措辞且坑表未固化）、
  下一个可用新编号、冲突告警。

注意（2026-11-14 A60 补充）：ceiling 用「所有被提及编号(mentioned)的最大值 +1」，
  是刻意的保守设计——宁可跳号也不冒同号异物的风险。因此**文档里出现「不另起某号」
  「弃用某号」「曾误标某号」这类否定式引用时，那个具体编号仍会被计入 mentioned、
  使下次可用号跳过它**（11-14 日志初稿写「刻意不起 A62」即把 ceiling 推到 62）。
  写运行日志 / 坑表时，否定式编号引用一律**不写具体号**，只写「下一个可用号」。
"""

import argparse
import json
import os
import re
import sys

# 负向后顾避免把 "A2026" 误切成 A20；「A51附」作为 A51 的附注不另占号
PAT = re.compile(r'(?<![A-Za-z0-9])A(\d{1,2})(附)?(?!\d)')
# 坑表里「| A57 | ... |」视为已正式固化
SOLID = re.compile(r'^\|\s*A(\d{1,2})(附)?\s*\|')
# 预留措辞：出现这些词的上下文里的编号视为「已被别的流程占号」
RESERVE_HINTS = ('建议编号', '预留', '待下期', '待下一', '供次日', '供下次',
                 '供下期', '拟固化', '候选编号', '预留为', '建议固化')


def scan(repo):
    files = [
        os.path.join(repo, 'references', 'runbook.md'),
        os.path.join(repo, 'references', 'pitfalls.md'),
        os.path.join(repo, 'SKILL.md'),
    ]
    solid, reserved, mentioned = set(), {}, set()
    for f in files:
        if not os.path.exists(f):
            continue
        with open(f, encoding='utf-8') as fh:
            for i, line in enumerate(fh, 1):
                sm = SOLID.match(line)
                if sm and os.path.basename(f) == 'runbook.md':
                    solid.add(int(sm.group(1)))
                for m in PAT.finditer(line):
                    key = int(m.group(1))
                    mentioned.add(key)
                    # 只看该编号附近的窗口，避免整行里其它编号被连带判为预留
                    win = line[max(0, m.start() - 45): m.end() + 45]
                    if any(h in win for h in RESERVE_HINTS):
                        rec = (os.path.basename(f), i, line.strip()[:130])
                        reserved.setdefault(key, []).append(rec)

    xlsx = os.path.join(repo, '股票预测', '股票预测总表.xlsx')
    if os.path.exists(xlsx):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
            ws = wb['每日总览']
            for r in range(2, ws.max_row + 1):
                v = ws.cell(r, 14).value
                if not v:
                    continue
                for line in str(v).split('\n'):
                    for m in PAT.finditer(line):
                        key = int(m.group(1))
                        mentioned.add(key)
                        win = line[max(0, m.start() - 45): m.end() + 45]
                        if any(h in win for h in RESERVE_HINTS):
                            rec = ('总表N%d' % r, r, line.strip()[:130])
                            reserved.setdefault(key, []).append(rec)
            wb.close()
        except Exception as e:
            print('[warn] 总表 N 列扫描失败：%s' % e, file=sys.stderr)

    # 已在坑表固化的编号不再算「待认领的预留」
    reserved = {k: v for k, v in reserved.items() if k not in solid}
    return solid, reserved, mentioned


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True, help='仓库根目录（绝对路径）')
    ap.add_argument('--json', action='store_true', help='输出 JSON 供脚本消费')
    a = ap.parse_args()

    solid, reserved, mentioned = scan(a.repo)
    ceiling = max(set(solid) | set(reserved) | mentioned) if (solid or reserved or mentioned) else 0
    nxt = ceiling + 1
    # 同一编号既出现在预留上下文、又是最近刚固化的，提示人工复核
    conflicts = sorted(k for k in reserved if k >= ceiling - 2)

    if a.json:
        print(json.dumps({
            'solid': sorted(solid),
            'reserved': sorted(reserved),
            'mentioned': sorted(mentioned),
            'next': nxt,
            'ceiling': ceiling,
            'conflicts': conflicts,
        }, ensure_ascii=False))
        return

    print('=' * 72)
    print('经验编号核查 A60　仓库：%s' % a.repo)
    print('-' * 72)
    print('已固化（坑表）：', ', '.join('A%d' % k for k in sorted(solid)) or '无')
    print('已预留（坑表未固化，**不可另作他用**）：',
          ', '.join('A%d' % k for k in sorted(reserved)) or '无')
    for k in sorted(reserved):
        src = reserved[k][0]
        print('  A%d 预留出处：%s:%s  %s' % (k, src[0], src[1], src[2][:96]))
    print('-' * 72)
    print('下一个可用新编号：A%02d' % nxt)
    if conflicts:
        print('[冲突告警] 以下编号同时出现在预留与近期固化上下文，须人工复核：',
              ', '.join('A%d' % k for k in conflicts))
    print('=' * 72)


if __name__ == '__main__':
    main()

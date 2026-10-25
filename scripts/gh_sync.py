#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测 · GitHub 同步（下载 / 推送 / 回验），只依赖标准库
------------------------------------------------------------
为什么不用 git clone：本沙箱 git 走 443 端口直连常被墙（实测卡 2 分钟报
"Failed to connect to github.com port 443"），而 api.github.com 与
codeload.github.com 正常。所以统一走 HTTPS API（Contents API 串行 PUT）。

用法：
  # 下载整个仓库到目录（浅表：只取需要的文件，默认取 Skill 文件 + 股票预测/）
  python3 scripts/gh_sync.py pull --repo-dir /workspace/xx/stock-daily-report

  # 推送（串行 PUT；自动带 sha；推完回验 md5）
  python3 scripts/gh_sync.py push --repo-dir /workspace/xx/stock-daily-report \
      --msg "report: 2026-10-27" \
      "股票预测/股票预测总表.xlsx" "股票预测/202610/2026-10-27.md" \
      "股票预测/202610/2026-10-27_1.jpg" "..._2.jpg" "..._3.jpg"

  python3 scripts/gh_sync.py verify --repo-dir ... "路径1" "路径2"

Token：环境变量 GH_TOKEN > --token-file（默认 仓库外 ../.gh_token）。
遵守硬规则：token 绝不写进仓库文件；打印时自动打码。
"""
import argparse
import base64
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
REPO = "feifeiwang/stock-daily-report"
BRANCH = "main"


def token_of(args):
    t = os.environ.get("GH_TOKEN", "").strip()
    if not t and args.token_file and os.path.exists(args.token_file):
        t = open(args.token_file, encoding="utf-8").read().strip()
    if not t:
        print("错误：未找到 GH_TOKEN（环境变量或 --token-file），写操作无法继续", file=sys.stderr)
        sys.exit(2)
    return t


def call(method, path, token, body=None, retries=3):
    if path.startswith("http"):
        url = path
    else:
        url = f"{API}/repos/{REPO}" + (path if path.startswith("/") else "/" + path)
    data = json.dumps(body).encode() if body is not None else None
    for i in range(retries):
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "stock-daily-report-bot",
        })
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            if e.code in (409, 429, 500, 502, 503, 504) and i + 1 < retries:
                time.sleep(3 * (i + 1))
                continue
            body_txt = e.read().decode("utf-8", "ignore")[:300]
            if e.code == 404:
                return None
            print(f"  [HTTP {e.code}] {method} {url} -> {body_txt}", file=sys.stderr)
            raise
    return None


def contents_url(path):
    """Contents API 路径；中文路径必须逐段 quote。"""
    return "/contents/" + urllib.parse.quote(path.encode("utf-8"), safe="") + f"?ref={BRANCH}"


def get_file(path, token):
    return call("GET", contents_url(path), token)


def pull(args):
    token = token_of(args)
    root = args.repo_dir
    wanted = args.paths or ["SKILL.md", "README.md", ".gitignore",
                            "references", "scripts", "templates", "股票预测"]
    todo = []
    for w in wanted:
        w = w.rstrip("/")
        info = get_file(w, token)
        if info is None:
            print(f"  [skip] 远端无 {w}")
            continue
        if isinstance(info, list):
            todo += [(e["path"], e["type"]) for e in info if e["type"] == "file"]
            # 二级目录（股票预测/YYYYMM）一次展开
            for e in [e for e in info if e["type"] == "dir"]:
                sub = get_file(e["path"], token) or []
                todo += [(x["path"], x["type"]) for x in sub if x["type"] == "file"]
        else:
            todo.append((info["path"], "file"))

    for path, _ in todo:
        info = get_file(path, token)
        if info is None:
            print(f"  [skip] {path}")
            continue
        dst = os.path.join(root, path)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst) and os.path.getsize(dst) == info["size"]:
            print(f"  [keep] {path}")
            continue
        blob = base64.b64decode(info["content"])
        with open(dst, "wb") as f:
            f.write(blob)
        print(f"  [pull] {path} ({len(blob)} bytes)")
    print(f"下载完成：{len(todo)} 个文件 → {root}")


def put_one(path, token, msg, root):
    local = os.path.join(root, path)
    if not os.path.exists(local):
        print(f"  [SKIP] 本地不存在 {path}")
        return False
    raw = open(local, "rb").read()
    cur = get_file(path, token)
    body = {"message": msg, "content": base64.b64encode(raw).decode(),
            "branch": BRANCH, "committer": {"name": "stock-bot", "email": "stock-bot@users.noreply.github.com"}}
    if cur and "sha" in cur:
        if cur["size"] == len(raw):
            print(f"  [same] {path} 未变化，跳过")
            return True
        body["sha"] = cur["sha"]
    r = call("PUT", contents_url(path), token, body)
    ok = bool(r and r.get("content"))
    print(f"  [{'PUT' if ok else 'FAIL'}] {path} ({len(raw)} bytes)")
    return ok


def push(args):
    token = token_of(args)
    bad = []
    for p in args.paths:
        if not put_one(p, token, args.msg, args.repo_dir):
            bad.append(p)
    if bad:
        print("推送失败：" + ", ".join(bad), file=sys.stderr)
        return 1
    return verify(args)


def verify(args):
    token = token_of(args)
    bad = 0
    for p in args.paths:
        local = os.path.join(args.repo_dir, p)
        if not os.path.exists(local):
            continue
        info = get_file(p, token)
        if not info or "content" not in info:
            print(f"  [FAIL] {p} 远端不存在")
            bad += 1
            continue
        remote = base64.b64decode(info["content"])
        lm = hashlib.md5(open(local, "rb").read()).hexdigest()
        rm = hashlib.md5(remote).hexdigest()
        if lm == rm:
            print(f"  [OK] {p} ({len(remote)} bytes, md5 match)")
        else:
            print(f"  [FAIL] {p} md5 不一致（远端 {len(remote)}B / 本地 {os.path.getsize(local)}B）")
            bad += 1
    return 0 if bad == 0 else 1


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("pull", "push", "verify"):
        s = sub.add_parser(name)
        s.add_argument("--repo-dir", required=True)
        s.add_argument("--token-file", default=None)
        s.add_argument("paths", nargs="*")
        if name == "push":
            s.add_argument("--msg", default="chore: update")
        if name == "pull":
            s.add_argument("--paths", nargs="*", dest="paths_opt", default=None,
                           help="只拉这些顶层路径（默认 Skill 文件 + 股票预测/）")
    a = ap.parse_args()
    if a.cmd == "pull":
        a.paths = a.paths_opt or a.paths
        pull(a)
    elif a.cmd == "push":
        sys.exit(push(a))
    else:
        a.paths = a.paths
        sys.exit(verify(a))


if __name__ == "__main__":
    main()

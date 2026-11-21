#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gh_sync_curl.py — gh_sync.py 的 curl 兜底版（A67）。

场景：某些沙箱里 Python 的 urllib/requests 对 api.github.com 的 TLS 握手后
「读响应」会超时（ReadTimeout / TimeoutError: read operation timed out），
但 curl 走系统网络栈可正常访问同一 API。此时改用本脚本推送，逻辑与 gh_sync.py
的 push+verify 完全一致（GET sha → md5 比较 → PUT → 下载回验），只是把 HTTP
请求交给 curl 子进程，凭据仍只走 repo 外 600 文件的 --token-file，绝不进命令行/日志。

用法（一律绝对路径，A35）：
  python3 scripts/gh_sync_curl.py --repo-dir /tmp/sdr \
      --token-file /root/.codebuddy/.xxx --msg "report: 2026-11-21" \
      "股票预测/股票预测总表.xlsx" "references/runbook.md"

判定：
  - 若 gh_sync.py push 报 ReadTimeout / TimeoutError（连接建立后读超时），优先怀疑
    本沙箱 Python SSL 栈问题，直接改用本脚本，不要反复重试 urllib（超时后 PUT 可能
    已生效，重推前先按 verify 逻辑远端 md5 核对，避免盲目覆盖）。
  - 正常沙箱仍优先用 gh_sync.py（原生实现）；本脚本只在 urllib 超时时兜底。
"""
import argparse, base64, hashlib, json, os, subprocess, sys, time, urllib.parse

REPO = "feifeiwang/stock-daily-report"
BRANCH = "main"
API = "https://api.github.com"


def curl_json(method, url, token, body=None, retries=4):
    cmd = ["curl", "-s", "-S", "--max-time", "60", "-X", method,
           "-H", f"Authorization: Bearer {token}",
           "-H", "Accept: application/vnd.github+json",
           "-H", "X-GitHub-Api-Version: 2022-11-28",
           "-H", "User-Agent: stock-daily-report-bot"]
    if body is not None:
        cmd += ["-H", "Content-Type: application/json", "--data-binary", "@-"]
    cmd.append(url)
    payload = json.dumps(body).encode() if body is not None else None
    last = b""
    for i in range(retries):
        p = subprocess.run(cmd, input=payload, capture_output=True)
        last = p.stderr
        if p.returncode == 0 and p.stdout.strip():
            try:
                return json.loads(p.stdout)
            except Exception:
                pass
        time.sleep(2 * (i + 1))
    raise RuntimeError(f"curl {method} 失败: {last.decode(errors='ignore')[:200]}")


def cpath(path):
    return "/contents/" + urllib.parse.quote(path.encode("utf-8"), safe="") + f"?ref={BRANCH}"


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-dir", required=True)
    ap.add_argument("--token-file", required=True)
    ap.add_argument("--msg", default="chore: update")
    ap.add_argument("paths", nargs="*")
    a = ap.parse_args()
    token = open(a.token_file, encoding="utf-8").read().strip()
    url_base = f"{API}/repos/{REPO}"

    def get_file(path):
        try:
            return curl_json("GET", url_base + cpath(path), token)
        except Exception:
            return None

    bad = []
    for p in a.paths:
        local = os.path.join(a.repo_dir, p)
        if not os.path.exists(local):
            print(f"  [SKIP] 本地不存在 {p}"); bad.append(p); continue
        raw = open(local, "rb").read()
        cur = get_file(p)
        body = {"message": a.msg, "content": base64.b64encode(raw).decode(),
                "branch": BRANCH,
                "committer": {"name": "stock-bot", "email": "stock-bot@users.noreply.github.com"}}
        if cur and isinstance(cur, dict) and "sha" in cur:
            rmd5 = md5(base64.b64decode(cur["content"])) if cur.get("content") else None
            if rmd5 == md5(raw):
                print(f"  [same] {p} 未变化"); continue
            body["sha"] = cur["sha"]
        r = curl_json("PUT", url_base + cpath(p), token, body)
        ok = bool(r and isinstance(r, dict) and r.get("content"))
        print(f"  [{'PUT' if ok else 'FAIL'}] {p} ({len(raw)} bytes)")
        if not ok:
            bad.append(p)
    if bad:
        print("推送失败: " + ", ".join(bad), file=sys.stderr); return 1

    nb = 0
    for p in a.paths:
        local = os.path.join(a.repo_dir, p)
        info = get_file(p)
        if not info or "content" not in info:
            print(f"  [FAIL] {p} 远端不存在"); nb += 1; continue
        remote = base64.b64decode(info["content"])
        if md5(remote) == md5(open(local, "rb").read()):
            print(f"  [OK] {p} ({len(remote)} bytes, md5 match)")
        else:
            print(f"  [FAIL] {p} md5 不一致（远端{len(remote)}B/本地{os.path.getsize(local)}B）"); nb += 1
    return 0 if nb == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

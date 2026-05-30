"""gov.scan_secrets — 融合密鑰掃描（preflight 的 blocking check 之一）。

快照日期：2026-05-31（複製自 skills-governance/gov/scan_secrets.py，非 live 引用）。
策略：(a) .env 真實值明文比對（抓「我的金鑰外洩」）+ (b) secret_patterns 特徵掃描（抓「任何金鑰」）。
【絕不回傳/列印金鑰值】，只報「哪個金鑰名/特徵出現在哪些檔」。
含 'allowlist-secret' 的行刻意豁免。非 git repo → SKIP（視為安全）。
密鑰 pattern 取 Hermes 7 類 + AOV .secrets.baseline 聯集（於 governance_config.yaml 宣告）。

CLI：py -m gov.scan_secrets   （exit 0=clean / 1=leak）
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from gov.utils import find_repo_root, load_config


def _load_patterns(cfg: dict) -> list:
    pats = []
    for p in cfg.get("secret_patterns", []) or []:
        try:
            pats.append((p["name"], re.compile(p["regex"])))
        except (KeyError, re.error):
            continue
    return pats


def is_key_ascii_valid(v: str) -> bool:
    """真金鑰判定：純 ASCII 且非佔位符（排除 your_ / _here / 中文殘留）。"""
    if not v:
        return False
    try:
        v.encode("ascii")
    except UnicodeEncodeError:
        return False
    low = v.lower()
    return not any(k in low for k in ("your_", "_here", "xxxx", "placeholder", "您的"))


def _find_secret_leaks(secret_values: dict, file_contents: dict) -> dict:
    """比對 .env 真實值是否出現在追蹤檔中。絕不回傳值本身。"""
    leaks = {}
    for name, value in secret_values.items():
        if not value:
            continue
        hits = [p for p, c in file_contents.items() if c and value in c]
        if hits:
            leaks[name] = hits
    return leaks


def _find_pattern_secrets(file_contents: dict, patterns: list) -> list:
    """特徵掃描：只回傳檔名與行號，不回傳匹配值。"""
    hits = []
    for path, content in file_contents.items():
        if not content:
            continue
        for i, line in enumerate(content.splitlines(), 1):
            if "allowlist-secret" in line:
                continue
            for name, rx in patterns:
                if rx.search(line):
                    hits.append({"type": name, "file": path, "line": i})
                    break
    return hits


def scan(root: Path | None = None) -> dict:
    root = root or find_repo_root()
    cfg = load_config(root)
    patterns = _load_patterns(cfg)
    report = {"status": "PASS", "leaks": {}, "scanned_files": 0, "secret_count": 0, "summary": ""}

    # 1. 蒐集 .env 真實金鑰值（不外傳）
    secret_values = {}
    env_path = root / ".env"
    if env_path.exists():
        for raw in env_path.read_text("utf-8", errors="ignore").splitlines():
            s = raw.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if not re.search(r"KEY|TOKEN|SECRET|PASSWORD|WEBHOOK", k, re.I):
                continue
            if len(v) < 12 or not is_key_ascii_valid(v):
                continue
            secret_values[k] = v
    report["secret_count"] = len(secret_values)

    # 2. git 追蹤檔列表
    try:
        r = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True,
                           encoding="utf-8", errors="ignore", timeout=20)
        if r.returncode != 0:
            report["status"] = "SKIP"
            report["summary"] = "非 git repo 或 git 不可用，略過掃描（視為安全）。"
            return report
        tracked = [p for p in r.stdout.splitlines() if p.strip()]
    except Exception as e:
        report["status"] = "SKIP"
        report["summary"] = f"git 不可用：{e}"
        return report

    # 3. 讀追蹤檔內容
    file_contents = {}
    for rel in tracked:
        p = root / rel
        try:
            file_contents[rel] = p.read_bytes().decode("utf-8", "ignore")
        except Exception:
            continue
    report["scanned_files"] = len(file_contents)

    # 4. 比對：.env 明文 + 特徵掃描（均不輸出真值）
    leaks = dict(_find_secret_leaks(secret_values, file_contents))
    for h in _find_pattern_secrets(file_contents, patterns):
        leaks.setdefault("特徵:" + h["type"], []).append(f"{h['file']}:{h['line']}")
    report["leaks"] = leaks

    if leaks:
        report["status"] = "FAIL"
        report["summary"] = (f"🔴 偵測到 {len(leaks)} 類金鑰外洩於追蹤檔"
                             f"（掃 {report['scanned_files']} 檔 / {report['secret_count']} 真金鑰）。")
    else:
        report["summary"] = (f"✅ 無金鑰外洩"
                             f"（掃 {report['scanned_files']} 檔 / {report['secret_count']} 真金鑰）。")
    return report


def main() -> int:
    rep = scan()
    print(rep["summary"])
    for name, files in rep.get("leaks", {}).items():
        # 只印金鑰名稱與檔案位置，絕不印真實值
        print(f"  - {name}: {', '.join(files)}")
    return 1 if rep["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())

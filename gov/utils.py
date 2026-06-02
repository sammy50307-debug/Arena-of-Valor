"""gov.utils — 共享工具函式。

快照日期：2026-05-31（複製自 skills-governance/gov/utils.py，非 live 引用）。
功能：repo 根定位 + governance_config.yaml 載入（graceful 降級，pyyaml 未裝不卡死）。
"""
from __future__ import annotations

from pathlib import Path

CONFIG_NAME = "governance_config.yaml"


def find_repo_root(start: Path | None = None) -> Path:
    """從 start（預設本檔）往上找含 governance_config.yaml 的目錄；找不到回最近的父目錄。"""
    cur = (start or Path(__file__)).resolve()
    for parent in [cur, *cur.parents]:
        if (parent / CONFIG_NAME).exists():
            return parent
    return cur.parent


def load_config(root: Path | None = None) -> dict:
    """載入 governance_config.yaml。

    韌性：pyyaml 未安裝時回 {"_yaml_missing": True} 而非拋例外，
    讓各引擎在環境缺套件時能降級運作。
    """
    root = root or find_repo_root()
    cfg_path = root / CONFIG_NAME
    if not cfg_path.exists():
        return {"schema_version": 0.1, "status": "pilot", "_config_missing": True}
    try:
        import yaml  # type: ignore
    except ImportError:
        return {"_yaml_missing": True, "_config_path": str(cfg_path)}
    return yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
